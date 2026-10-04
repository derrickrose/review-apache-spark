"""Core lab 03 — JOIN skew (plan §7, M09).

The skewed copy (90% of rows on key 1) is materialized once by setup(): rand() is non-deterministic.
Variants change ONE variable each vs baseline (plan §1.2):
    baseline : broadcast off, AQE skew join off  → one giant SortMergeJoin reducer
    aqe_skew : + spark.sql.adaptive.skewJoin.enabled=true (splits the skewed partition)
    salted   : baseline conf, query rewritten with salting (N=32, small side replicated ×32)
"""
from pyspark.sql import functions as F
import common as C

SKEWED = f"{C.BASE}/tlc/yellow_skewed"
SALT = 32
_off = {"spark.sql.autoBroadcastJoinThreshold": "-1", "spark.sql.adaptive.autoBroadcastJoinThreshold": "-1"}
VARIANTS = {
    "baseline": {**_off, "spark.sql.adaptive.skewJoin.enabled": "false"},
    "aqe_skew": {**_off, "spark.sql.adaptive.skewJoin.enabled": "true"},
    "salted": {**_off, "spark.sql.adaptive.skewJoin.enabled": "false"},
}
EXPECT = {
    "baseline": {"max_over_median": (">", 4)},                   # the symptom must reproduce
    "aqe_skew": {"max_over_median": ("<", 2.5), "runtime_median_s": ("<", 0.8, "x_baseline")},
    "salted": {"max_over_median": ("<", 3), "runtime_median_s": ("<", 0.9, "x_baseline")},
}


def setup(spark):
    C.materialize_skew(spark, SKEWED)


def build(spark, variant):
    trips = spark.read.parquet(SKEWED).select("k", "fare_amount", "tpep_pickup_datetime")
    zones = C.zones(spark)
    if variant != "salted":
        return trips.join(zones, trips.k == zones.LocationID)
    t = trips.withColumn("salt", (F.rand(7) * SALT).cast("int"))
    z = zones.crossJoin(spark.range(SALT).select(F.col("id").cast("int").alias("salt")))
    return t.join(z, (t.k == z.LocationID) & (t.salt == z.salt)).drop("salt")
