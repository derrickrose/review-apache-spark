"""Core lab 06 — Window skew (plan §7, M11).

AQE skew-join handling does NOT apply to windows: the whole window partition must be on one task.
    baseline   : row_number over the 90%-hot key           → one giant sort/window task
    natural    : same window on the natural PULocationID   → the realistic (milder) distribution
    aqe_off    : baseline with AQE disabled                → shows AQE does not fix window skew
A semantic-preserving fix does not exist: fixing it means changing the window key (business decision).
"""
from pyspark.sql import Window, functions as F
import common as C

SKEWED = f"{C.BASE}/tlc/yellow_skewed"
VARIANTS = {"baseline": {}, "natural": {}, "aqe_off": {"spark.sql.adaptive.enabled": "false"}}
CHECK_CORRECTNESS = False
EXPECT = {
    "baseline": {"max_over_median": (">", 4)},
    "aqe_off": {"max_over_median": (">", 4)},
    "natural": {"max_task_ms": ("<", 0.5, "x_baseline")},
}


def setup(spark):
    C.materialize_skew(spark, SKEWED)


def build(spark, variant):
    t = spark.read.parquet(SKEWED).select("k", "PULocationID", "tpep_pickup_datetime", "fare_amount")
    key = "PULocationID" if variant == "natural" else "k"
    w = Window.partitionBy(key).orderBy("tpep_pickup_datetime")
    return t.withColumn("rn", F.row_number().over(w)).withColumn("prev_fare", F.lag("fare_amount").over(w))
