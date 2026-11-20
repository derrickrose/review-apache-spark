"""
Fixing Data Skews (PySpark port of part5boost/FixingDataSkews.scala)
"""
import random as random_module
import string
import time
from typing import List, Sequence, Tuple, TypeVar

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

T = TypeVar("T")

spark = (
    SparkSession.builder
    .appName("Fixing Data Skews")
    .master("local[*]")
    .getOrCreate()
)

# deactivate broadcast joins
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
spark.conf.set("spark.sql.adaptive.enabled", False)


# ---------------------------------------------------------------------------
# Data generation (port of common.DataGenerator)
# ---------------------------------------------------------------------------
class DataGenerator:
    random = random_module.Random()

    # -------------------------------------------------------------------
    # General data generation
    # -------------------------------------------------------------------
    @classmethod
    def random_double(cls, limit: float) -> float:
        assert limit >= 0
        return cls.random.random() * limit

    @classmethod
    def random_long(cls, limit: int = 2**63 - 1) -> int:
        assert limit >= 0
        return cls.random.randrange(limit)

    @classmethod
    def random_int(cls, limit: int = 2**31 - 1) -> int:
        assert limit >= 0
        return cls.random.randrange(limit)

    @classmethod
    def random_int_between(cls, low: int, high: int) -> int:
        assert low <= high
        return cls.random.randrange(high - low) + low

    @classmethod
    def random_string(cls, n: int) -> str:
        return "".join(cls.random.choices(string.ascii_letters + string.digits, k=n))

    @classmethod
    def pick_from(cls, seq: Sequence[T]) -> T:
        assert len(seq) > 0
        return seq[cls.random_int(len(seq))]

    # -------------------------------------------------------------------
    # Guitars generation - fixing skewed data lecture
    # -------------------------------------------------------------------
    guitar_model_set: List[Tuple[str, str]] = [
        ("Taylor", "914"),
        ("Martin", "D-18"),
        ("Takamine", "P7D"),
        ("Gibson", "L-00"),
        ("Tanglewood", "TW45"),
        ("Fender", "CD-280S"),
        ("Yamaha", "LJ16BC"),
    ]

    @classmethod
    def random_guitar_model(cls, uniform: bool = False) -> Tuple[str, str]:
        """
        Generates a tuple of (make, model) from the available set.
        If 'uniform' is False, it has a 50% chance of picking one pair, and 50% chance for all the others.
        """
        if not uniform and cls.random.random() < 0.5:
            idx = 0
        else:
            idx = cls.random.randrange(len(cls.guitar_model_set))
        return cls.guitar_model_set[idx]

    @classmethod
    def random_sound_quality(cls) -> float:
        return float(f"4.{cls.random.randrange(9)}")

    @classmethod
    def random_guitar_registration(cls) -> str:
        return cls.random_string(8)

    @classmethod
    def random_guitar_model_type(cls) -> str:
        return f"{cls.random_string(4)}-{cls.random_string(4)}"

    @classmethod
    def random_guitar_price(cls) -> int:
        return 500 + cls.random.randrange(1500)

    @classmethod
    def random_guitar(cls, uniform_dist: bool = False) -> Tuple[str, str, str, float]:
        """Row matching GUITAR_SCHEMA: (configurationId, make, model, soundScore)"""
        make, model = cls.random_guitar_model(uniform_dist)
        return (cls.random_guitar_model_type(), make, model, cls.random_sound_quality())

    @classmethod
    def random_guitar_sale(cls, uniform_dist: bool = False) -> Tuple[str, str, str, float, float]:
        """Row matching GUITAR_SALE_SCHEMA: (registration, make, model, soundScore, salePrice)"""
        make, model = cls.random_guitar_model(uniform_dist)
        return (
            cls.random_guitar_registration(), make, model,
            cls.random_sound_quality(), float(cls.random_guitar_price()),
        )


# Scenario: a factory of handmade guitars (Taylor, Martin, Tanglewood...).
# A guitar row is a reference description with an "objective" sound score from 0 to 5 (factory / "new" score).
GUITAR_SCHEMA = StructType([
    StructField("configurationId", StringType()),
    StructField("make", StringType()),
    StructField("model", StringType()),
    StructField("soundScore", DoubleType()),
])

# A guitar sale row describes a specific guitar (by registration) with its sound score
# (can be higher or lower than the "new" score) and the sale price on the store.
GUITAR_SALE_SCHEMA = StructType([
    StructField("registration", StringType()),
    StructField("make", StringType()),
    StructField("model", StringType()),
    StructField("soundScore", DoubleType()),
    StructField("salePrice", DoubleType()),
])

guitars: DataFrame = spark.createDataFrame([DataGenerator.random_guitar() for _ in range(40000)], GUITAR_SCHEMA)
guitar_sales: DataFrame = spark.createDataFrame([DataGenerator.random_guitar_sale() for _ in range(200000)], GUITAR_SALE_SCHEMA)

"""
  A Guitar is similar to a GuitarSale if
  - same make and model
  - abs(guitar.soundScore - guitarSale.soundScore) <= 0.1

  Problem:
  - for every Guitar, avg(sale prices of ALL SIMILAR GuitarSales)
  - Gibson L-00, config "sadfhja", sound 4.3,
    compute avg(sale prices of ALL GuitarSales of Gibson L-00 with sound quality between 4.2 and 4.4
"""

# UPDATE - Spark 4 AQE (Adaptive Query Execution) handles many skew cases automatically via
# spark.sql.adaptive.skewJoin.enabled (default true). AQE detects skewed partitions at runtime
# and splits them into smaller sub-partitions. Manual salting (shown below) is still needed when:
#   - AQE can't detect the skew (e.g. skew emerges after a non-equi join condition)
#   - the skew is in a non-join operation (aggregations, window functions)
#   - you need deterministic partition control


def naive_solution():
    g = guitars.alias("g")
    s = guitar_sales.alias("s")
    joined = (
        g.join(s, ["make", "model"])
        .where(F.abs(F.col("s.soundScore") - F.col("g.soundScore")) <= 0.1)
        .groupBy("configurationId")
        .agg(F.avg("salePrice").alias("averagePrice"))
    )

    joined.explain()
    return joined.count()

SALT = 100

def no_skew_solution():
    # salting interval 0-99
    exploded_guitars = guitars.withColumn(
        "salt", F.explode(F.array(*[F.lit(i) for i in range(SALT)]))
    ).alias("g")  # multiplying the guitars DF xSALT
    salted_guitar_sales = guitar_sales.withColumn(
        "salt", (F.monotonically_increasing_id() % SALT).cast("int")
    ).alias("s")

    non_skewed_join = (
        exploded_guitars.join(salted_guitar_sales, ["make", "model", "salt"])
        .where(F.abs(F.col("s.soundScore") - F.col("g.soundScore")) <= 0.1)
        .groupBy("configurationId")
        .agg(F.avg("salePrice").alias("averagePrice"))
    )

    non_skewed_join.explain()
    return non_skewed_join.count()


if __name__ == "__main__":
    naive_solution() #almos 2 minutes
    # no_skew_solution() #28 seconds
    time.sleep(1000000)  # keep the Spark UI (http://localhost:4040) alive
