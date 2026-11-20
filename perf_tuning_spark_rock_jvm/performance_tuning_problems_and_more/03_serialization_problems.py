"""
Serialization Problems (PySpark adaptation of part5boost/SerializationProblems.scala + slides)

Objective (slides)
- Fix the "task not serializable" problems
- Understand how Spark serializes transformations for executors

Applicable to lambdas only
- Scala: RDDs and Datasets.  PySpark: RDDs and Python UDFs (no Datasets in Python).
- DataFrame code using built-in functions (F.col, F.avg...) is NOT affected: no Python code is shipped.

Task serialization needed
- the driver sends the lambdas to the executors
- every reference a lambda makes is serialized with it
- if the reference is a field of an object (`self.factor`), the WHOLE object (`self`) is serialized
- not everything is serializable

Scala vs PySpark
- Scala: Java serialization. A class that isn't `Serializable` -> "Task not serializable".
- PySpark: cloudpickle. Almost every Python object is picklable, there is no `Serializable` marker,
  so that exact error does not exist. What DOES fail: shipping an object that holds a
  SparkContext / SparkSession / RDD / DataFrame (SPARK-5063, RDD_TRANSFORM_ONLY_VALID_ON_DRIVER),
  or an OS resource (DB connection, socket, lock, open file).
  And even when it works, capturing a big `self` ships it with every task (overhead).

That's why the classes below hold `self.rdd`: it's the PySpark way to reproduce the Scala failure.
"""
import os
import sys
import threading
from typing import Callable, List, NamedTuple

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Python workers must use the same interpreter as the driver, or unpickling fails in the workers
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)

spark = (
    SparkSession.builder
    .appName("Serialization Problems")
    .master("local[*]")
    .getOrCreate()
)

sc = spark.sparkContext

rdd = sc.parallelize(range(1, 101))


# ---------------------------------------------------------------------------
# The lambda doesn't reference the object -> only the lambda is shipped
# ---------------------------------------------------------------------------
class RDDMultiplier:
    def __init__(self, rdd):
        self.rdd = rdd

    def multiply_rdd(self) -> List[int]:
        return self.rdd.map(lambda x: x * 2).collect()


rdd_multiplier = RDDMultiplier(rdd)
# rdd_multiplier.multiply_rdd()  # works


# ---------------------------------------------------------------------------
# The problem: the lambda references a field -> `self` is shipped -> self.rdd can't be pickled
# ---------------------------------------------------------------------------
class MoreGeneralRDDMultiplier:
    def __init__(self, rdd):
        self.rdd = rdd
        self.factor = 2

    def multiply_rdd(self) -> List[int]:
        return self.rdd.map(lambda x: x * self.factor).collect()


more_general_rdd_multiplier = MoreGeneralRDDMultiplier(rdd)
# more_general_rdd_multiplier.multiply_rdd()
# FAILS: PicklingError ... RDD_TRANSFORM_ONLY_VALID_ON_DRIVER


# ---------------------------------------------------------------------------
# Technique 1: make the object serializable
# Scala: `extends Serializable`. Python objects already are; what we control is WHAT gets pickled
# (__getstate__). Easy, but large overhead: the whole object is still shipped with every task.
# ---------------------------------------------------------------------------
class SerializableRDDMultiplier:
    def __init__(self, rdd):
        self.rdd = rdd
        self.factor = 2

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("rdd", None)  # never ship the RDD to executors
        return state

    def multiply_rdd(self) -> List[int]:
        return self.rdd.map(lambda x: x * self.factor).collect()


serializable_rdd_multiplier = SerializableRDDMultiplier(rdd)
# serializable_rdd_multiplier.multiply_rdd()  # works


# ---------------------------------------------------------------------------
# Technique 2: capture local values (optimal, works the same in Scala and Python)
# ---------------------------------------------------------------------------
class MoreGeneralRDDMultiplierEnclosure:
    def __init__(self, rdd):
        self.rdd = rdd
        self.factor = 2

    def multiply_rdd(self) -> List[int]:
        enclosed_factor = self.factor  # only this int is captured
        return self.rdd.map(lambda x: x * enclosed_factor).collect()


more_general_rdd_multiplier2 = MoreGeneralRDDMultiplierEnclosure(rdd)
# more_general_rdd_multiplier2.multiply_rdd()  # works


# ---------------------------------------------------------------------------
# Same trap with Python UDFs (the case you actually meet in PySpark)
# ---------------------------------------------------------------------------
class PriceAdjuster:
    def __init__(self, spark_session: SparkSession, rate: float):
        self.spark = spark_session  # not picklable
        self.rate = rate

    def adjust_bad(self, df):
        adjust = F.udf(lambda p: p * self.rate, "double")  # captures self -> self.spark -> FAILS
        return df.withColumn("adjusted", adjust("price"))

    def adjust_good(self, df):
        rate = self.rate  # technique 2
        adjust = F.udf(lambda p: p * rate, "double")
        return df.withColumn("adjusted", adjust("price"))

    def adjust_best(self, df):
        # no Python lambda at all -> nothing to serialize, and no JVM<->Python round trip
        return df.withColumn("adjusted", F.col("price") * F.lit(self.rate))


prices = spark.createDataFrame([(10.0,), (20.0,)], "price double")
price_adjuster = PriceAdjuster(spark, 1.2)
# price_adjuster.adjust_bad(prices).show()   # fails
# price_adjuster.adjust_good(prices).show()  # works
# price_adjuster.adjust_best(prices).show()  # works, preferred


# ---------------------------------------------------------------------------
# Scala exercises - only partially relevant in Python
# ---------------------------------------------------------------------------

"""
Exercise 1 (nested object)
Scala: a nested `object` holds a hidden reference to its outer instance -> outer must be serializable.
Python: a nested class has NO implicit link to the outer instance. The trap only exists if you
store the outer object explicitly (self.outer), as below. Fix: capture locals.
"""
class MoreGeneralRDDMultiplierNestedClass:
    def __init__(self, rdd):
        self.rdd = rdd
        self.factor = 2
        self.nested_multiplier = self.NestedMultiplier(self)

    class NestedMultiplier:
        def __init__(self, outer: "MoreGeneralRDDMultiplierNestedClass"):
            self.outer = outer  # explicit reference -> holds the RDD
            self.extra_term = 10
            self.local_factor = outer.factor

        def multiply_rdd(self) -> List[int]:
            local_factor = self.local_factor
            extra_term = self.extra_term
            return self.outer.rdd.map(lambda x: x * local_factor + extra_term).collect()


nested_multiplier = MoreGeneralRDDMultiplierNestedClass(rdd)
# nested_multiplier.nested_multiplier.multiply_rdd()  # [12, 14, ...]


"""
Exercise 2: capture the constructor argument (relevant: technique 2)
"""
class Person(NamedTuple):
    name: str
    age: int


people = sc.parallelize([
    Person("Alice", 43),
    Person("Bob", 12),
    Person("Charlie", 23),
    Person("Diana", 67),
])


class LegalDrinkingAgeChecker:
    def __init__(self, legal_age: int, people_rdd):
        self.legal_age = legal_age
        self.people = people_rdd

    def process_people(self) -> List[bool]:
        age_threshold = self.legal_age  # capture in a local value
        return self.people.map(lambda p: p.age >= age_threshold).collect()


people_checker = LegalDrinkingAgeChecker(21, people)
# people_checker.process_people()  # [True, False, True, True]


"""
Exercise 3: make it work without Serializable
Scala hint: FunctionX values are serializable, methods drag `this` along.
Python: same idea - a bound method (obj.check) carries `obj`; a plain function/closure doesn't.
"""
class PersonProcessor:
    def __init__(self, people_rdd):
        self.people = people_rdd  # must never be shipped

    class DrinkingAgeChecker:
        def __init__(self, legal_age: int):
            captured_legal_age = legal_age  # 3: capture the constructor argument
            # 1: a function value instead of a method
            self.check: Callable[[int], bool] = lambda age: age >= captured_legal_age

    class DrinkingAgeFlagger:
        def __init__(self, checker: Callable[[int], bool], people_rdd):
            self.checker = checker
            self.people = people_rdd

        def flag(self) -> List[bool]:
            captured_checker = self.checker  # 2: capture the lambda
            return self.people.map(lambda p: captured_checker(p.age)).collect()

    def process_people(self) -> List[bool]:
        us_checker = self.DrinkingAgeChecker(21)
        flagger = self.DrinkingAgeFlagger(us_checker.check, self.people)
        return flagger.flag()


person_processor = PersonProcessor(people)

# ---------------------------------------------------------------------------
# PySpark extras: what the lambdas capture
# ---------------------------------------------------------------------------

"""
Big objects: a captured object is pickled into EVERY task.
Broadcast it: sent once per executor and cached there.
(DataFrames: prefer a broadcast join, df.join(F.broadcast(small_df), "key"))
"""
lookup = {i: f"category_{i % 50}" for i in range(500_000)}


def closure_capture():
    return rdd.map(lambda x: lookup.get(x)).collect()  # `lookup` shipped with each task


def broadcast_capture():
    lookup_bc = sc.broadcast(lookup)  # shipped once per executor
    try:
        return rdd.map(lambda x: lookup_bc.value.get(x)).collect()
    finally:
        lookup_bc.unpersist()


"""
Non-picklable resources (DB/HTTP clients, locks, sockets): never create them on the driver.
Create them on the executor, once per partition.
"""
class FakeConnection:
    def __init__(self):
        self._lock = threading.Lock()  # not picklable, like a real client

    def lookup(self, x):
        return x * 10

    def close(self):
        pass


def connection_bad():
    conn = FakeConnection()  # driver side
    return rdd.map(lambda x: conn.lookup(x)).take(3)  # FAILS: cannot pickle '_thread.lock'


def connection_good():
    def per_partition(rows):
        conn = FakeConnection()  # executor side, once per partition
        try:
            for x in rows:
                yield conn.lookup(x)
        finally:
            conn.close()

    return rdd.mapPartitions(per_partition).take(3)
    # DataFrame equivalents: df.foreachPartition(...) for writes, mapInPandas(...) for transforms


if __name__ == "__main__":
    print(person_processor.process_people())
