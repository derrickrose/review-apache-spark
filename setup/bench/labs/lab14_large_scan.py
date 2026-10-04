"""Core lab 14 — Large table scan: predicate pushdown and layout (plan §7, M16).

Pushdown only saves I/O if row-group min/max statistics can exclude row groups, i.e. if the data is
clustered on the filter column. setup() writes a copy sorted by fare_amount.
    baseline        : unsorted layout, pushable filter       (pushed, but almost nothing skipped)
    sorted          : sorted layout, same pushable filter    (row groups skipped)
    not_pushable    : sorted layout, `fare_amount + 0 > X`  (not pushed → full scan)
Read `PushedFilters` in the plan and "size of files read" in the SQL tab.
"""
from pyspark.sql import functions as F
import common as C

SORTED = f"{C.OUT}/lab14/sorted_by_fare"
X = 150.0
VARIANTS = {"baseline": {}, "sorted": {}, "not_pushable": {}}
EXPECT = {"sorted": {"input": ("<", 0.3, "x_baseline")}, "not_pushable": {"input": (">", 0.7, "x_baseline")}}


def setup(spark):
    if not C.exists(spark, SORTED):
        C.trips(spark).drop("pickup_date").orderBy("fare_amount").write.mode("overwrite").parquet(SORTED)


def build(spark, variant):
    cols = ["VendorID", "tpep_pickup_datetime", "PULocationID", "fare_amount", "tip_amount"]
    if variant == "baseline":
        return C.trips(spark, cols).where(F.col("fare_amount") > X)
    df = spark.read.parquet(SORTED).select(*cols)
    return df.where(F.col("fare_amount") > X) if variant == "sorted" else df.where(F.col("fare_amount") + 0 > X)
