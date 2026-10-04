"""Core lab 05 — Aggregation skew (plan §7, M10).

Key insight: partial (map-side) aggregation collapses a hot key to ONE row per map task for
decomposable aggregates, so `count` on a 95% hot key shows NO reducer skew. A non-collapsing
aggregate (collect_list) carries all values through the shuffle and shows the skew.
All variants return (k, n) so results are comparable.
    baseline       : collect_list on the hot key        → one huge reducer
    count          : count() on the same key            → no skew (explain why from the plan)
    salted_2stage  : collect_list per (k, salt), then flatten per k
"""
from pyspark.sql import functions as F
import common as C

HOT = f"{C.BASE}/tlc/yellow_hot95"
SALT = 64
VARIANTS = {"baseline": {}, "count": {}, "salted_2stage": {}}
EXPECT = {
    "baseline": {"max_over_median": (">", 4)},
    "count": {"max_over_median": ("<", 3)},
    "salted_2stage": {"max_over_median": ("<", 3), "runtime_median_s": ("<", 1.0, "x_baseline")},
}


def setup(spark):
    C.materialize_skew(spark, HOT, frac=0.95, hot=-1)


def build(spark, variant):
    t = spark.read.parquet(HOT).select("k", "tpep_pickup_datetime")
    if variant == "count":
        return t.groupBy("k").agg(F.count("*").alias("n"))
    if variant == "baseline":
        return t.groupBy("k").agg(F.size(F.collect_list("tpep_pickup_datetime")).alias("n"))
    stage1 = (t.withColumn("salt", (F.rand(3) * SALT).cast("int"))
               .groupBy("k", "salt").agg(F.collect_list("tpep_pickup_datetime").alias("v")))
    return stage1.groupBy("k").agg(F.size(F.flatten(F.collect_list("v"))).alias("n"))
