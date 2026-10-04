"""Core lab 21 — Cardinality explosion (plan §7, M15). 1 row → 100 rows, then aggregate.

    baseline : explode(sequence(1,100)) then sum → 100× rows through the plan
    preagg   : algebraic rewrite: sum(fare) × 100 → same answer, no explosion
Always compute output_rows / input_rows before running at scale.
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "preagg": {}}
EXPECT = {"preagg": {"runtime_median_s": ("<", 0.2, "x_baseline")}}


def build(spark, variant):
    t = C.trips(spark, ["PULocationID", "fare_amount"]).withColumn("fare", F.col("fare_amount").cast("decimal(12,2)"))
    if variant == "baseline":
        e = t.withColumn("i", F.explode(F.sequence(F.lit(1), F.lit(100))))
        return e.groupBy("PULocationID").agg(F.sum("fare").alias("s"))
    return t.groupBy("PULocationID").agg((F.sum("fare") * 100).cast("decimal(22,2)").alias("s"))


def result(spark, variant):
    return build(spark, variant).select("PULocationID", F.col("s").cast("decimal(22,2)").alias("s"))
