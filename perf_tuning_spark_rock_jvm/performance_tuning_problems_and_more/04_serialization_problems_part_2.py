"""
Serialization part 2 - "Kryo Me a River", PySpark equivalent
(PySpark adaptation of part5boost/KryoSerializer.scala + 04_kryo_serialization.pdf)

Scala lesson: swap Java serialization for Kryo (fast, memory efficient, can't serialize
everything, needs class registration) -> with caching & shuffles: 10-20% faster, 20-30% less memory.

In PySpark, Python objects are NEVER serialized by Java or Kryo: they are serialized on the
Python side (pickle by default, or marshal) and the JVM only sees opaque bytes. The equivalent knobs are:

1. The Python serializer of the SparkContext (the real "Kryo switch" of PySpark)
     CPickleSerializer (default)  -> serializes almost anything          (~ Java serialization)
     MarshalSerializer            -> limited types only                  (~ Kryo: "can't serialize
                                     everything"; instead of registering classes you restrict
                                     yourself to built-in types: int, float, str, tuple, list, dict)
2. Python RDD caching is ALWAYS serialized (there's no MEMORY_ONLY_SER: Python RDD blocks are
   serialized bytes), AND PySpark sets spark.rdd.compress=true by default (Scala: false).
   So the cache is already compact.
   Measured (1M persons, warm JVM): marshal is NOT faster in a measurable way and NOT smaller
   (Python 3.12 pickle protocol 5 is very compact: raw 18 MB vs 20 MB for marshal).
   Measure on a warm JVM: the first job of a session pays the warm-up and biases comparisons.
3. The best "serializer" is not to have Python objects at all: DataFrames use Spark's binary
   row format (Tungsten) + columnar compressed cache. Kryo isn't involved there (in Scala either).
4. Moving data between the JVM and Python: Arrow (pandas_udf, toPandas) >> pickle (plain udf).

spark.serializer=KryoSerializer can still be set in PySpark: it is accepted, but only affects
the JVM-side objects (which are byte arrays for Python RDDs) -> no measurable effect.
"""
import json
import os
import sys
import time
import urllib.request

import pandas as pd
from pyspark import SparkConf, SparkContext, StorageLevel
from pyspark.serializers import CPickleSerializer, MarshalSerializer
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Python workers must use the same interpreter (and packages) as the driver,
# otherwise unpickling fails in the workers (e.g. "No module named 'pandas'").
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)

N_PERSONS = 1_000_000  # Scala lesson uses 10M; Python objects are much heavier, start smaller


def make_spark(serializer=None, app_name="Serialization part 2") -> SparkSession:
    """The serializer is fixed when the SparkContext is created (same as Kryo in Scala:
    it must be in the SparkConf before the session exists)."""
    conf = SparkConf().setAppName(app_name).setMaster("local[*]")
    sc = SparkContext(conf=conf, serializer=serializer or CPickleSerializer())
    return SparkSession(sc)


# Scala: case class Person(name: String, age: Int)
# Plain tuples (name, age): both pickle and marshal can serialize them.
# (A NamedTuple / custom class would work with pickle but NOT with marshal -
#  the PySpark version of "Kryo can't serialize everything".)
def generate_people(n: int):
    return ((f"Person{i}", i % 100) for i in range(1, n + 1))


# ---------------------------------------------------------------------------
# Metrics helpers (what you'd read in the Spark UI: Storage tab / Stages tab)
# ---------------------------------------------------------------------------
def cached_size_mb(sc: SparkContext) -> float:
    infos = sc._jsc.sc().getRDDStorageInfo()
    return sum(i.memSize() for i in infos) / 1024 / 1024


def shuffle_write_mb(sc: SparkContext) -> float:
    url = f"{sc.uiWebUrl}/api/v1/applications/{sc.applicationId}/stages"
    with urllib.request.urlopen(url) as r:
        stages = json.load(r)
    return sum(s.get("shuffleWriteBytes", 0) for s in stages) / 1024 / 1024


# ---------------------------------------------------------------------------
# 1 + 2. Caching and shuffling with pickle vs marshal (= Java vs Kryo in Scala)
# ---------------------------------------------------------------------------
def test_caching(sc: SparkContext):
    people = sc.parallelize(generate_people(N_PERSONS), 16)
    start = time.time()
    # MEMORY_ONLY for a Python RDD = serialized bytes (the Scala MEMORY_ONLY_SER equivalent)
    people.persist(StorageLevel.MEMORY_ONLY).count()
    elapsed = time.time() - start
    size = cached_size_mb(sc)
    people.unpersist()
    return size, elapsed


def test_shuffling(sc: SparkContext):
    people = sc.parallelize(generate_people(N_PERSONS), 16)
    start = time.time()
    people.map(lambda p: (p[1], p)).groupByKey().mapValues(len).count()
    return shuffle_write_mb(sc), time.time() - start


def compare_serializers():
    # Warm-up pass, results discarded: the JVM (py4j gateway) lives across sessions,
    # so whichever serializer runs first would otherwise look slower.
    spark = make_spark(app_name="warm-up")
    test_caching(spark.sparkContext)
    test_shuffling(spark.sparkContext)
    spark.stop()

    for name, ser in [("pickle (default)", CPickleSerializer()), ("marshal", MarshalSerializer())]:
        spark = make_spark(ser, f"serializer-{name}")
        cache_mb, cache_s = test_caching(spark.sparkContext)
        shuffle_mb, shuffle_s = test_shuffling(spark.sparkContext)
        print(f"{name:<18} cache {cache_mb:7.1f} MB {cache_s:5.1f}s | "
              f"shuffle {shuffle_mb:7.2f} MB {shuffle_s:5.1f}s")
        spark.stop()


def marshal_limits():
    """Kryo needs class registration; marshal simply refuses non built-in types."""
    from typing import NamedTuple

    class Person(NamedTuple):
        name: str
        age: int

    spark = make_spark(MarshalSerializer(), "marshal-limits")
    try:
        spark.sparkContext.parallelize([Person("Alice", 43)]).map(lambda p: p.age).collect()
    except Exception as e:
        print("marshal + custom class ->", type(e).__name__, str(e).splitlines()[0][:80])
    finally:
        spark.stop()


# ---------------------------------------------------------------------------
# 3. Get rid of Python objects: DataFrame (Tungsten binary rows, columnar cache)
# ---------------------------------------------------------------------------
def test_dataframe():
    spark = make_spark(app_name="dataframe")
    sc = spark.sparkContext
    people_df = (
        spark.range(1, N_PERSONS + 1)
        .select(F.concat(F.lit("Person"), F.col("id")).alias("name"),
                (F.col("id") % 100).cast("int").alias("age"))
    )
    start = time.time()
    people_df.persist(StorageLevel.MEMORY_ONLY).count()
    cache_mb, cache_s = cached_size_mb(sc), time.time() - start
    people_df.unpersist()

    start = time.time()
    people_df.groupBy("age").count().collect()
    shuffle_mb, shuffle_s = shuffle_write_mb(sc), time.time() - start
    print(f"{'DataFrame':<18} cache {cache_mb:7.1f} MB {cache_s:5.1f}s | "
          f"shuffle {shuffle_mb:7.2f} MB {shuffle_s:5.1f}s  (partial aggregation before shuffle)")
    spark.stop()


# ---------------------------------------------------------------------------
# 4. JVM <-> Python transfer: built-in vs Arrow (pandas_udf) vs pickle (udf)
# ---------------------------------------------------------------------------
def test_jvm_python_boundary():
    spark = make_spark(app_name="arrow")
    df = spark.range(5_000_000).withColumn("price", (F.col("id") % 1000).cast("double"))

    @F.udf("double")
    def add_tax_udf(p):  # row by row, pickled
        return p * 1.2

    @F.pandas_udf("double")
    def add_tax_pandas(p: pd.Series) -> pd.Series:  # batches, Arrow columnar
        return p * 1.2

    for label, col in [("built-in", F.col("price") * 1.2),
                       ("pandas_udf (Arrow)", add_tax_pandas("price")),
                       ("python udf (pickle)", add_tax_udf("price"))]:
        start = time.time()
        df.select(F.sum(col)).first()
        print(f"{label:<20} {time.time() - start:5.2f}s")
    spark.stop()


if __name__ == "__main__":
    compare_serializers()
    marshal_limits()
    test_dataframe()
    test_jvm_python_boundary()
