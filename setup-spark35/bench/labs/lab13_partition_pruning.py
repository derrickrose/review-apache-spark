"""Core lab 13 — Partition pruning, pruning failure and DPP (plan §7, M16).

The prepared TLC table is partitioned by pickup_date (data/prepare_tlc.py). All variants return the
same rows; only how much is scanned changes. Check `PartitionFilters` in explain("formatted").
    baseline : filter on an expression of the data column → no pruning (full scan)
    pruned   : filter on the partition column              → one partition read
    dpp      : join with a filtered date dimension         → dynamic partition pruning at runtime
"""
from pyspark.sql import functions as F
import common as C

DAY = "2024-03-15"
VARIANTS = {"baseline": {}, "pruned": {}, "dpp": {"spark.sql.optimizer.dynamicPartitionPruning.enabled": "true"}}
EXPECT = {"pruned": {"input": ("<", 0.05, "x_baseline")}, "dpp": {"input": ("<", 0.05, "x_baseline")}}


def build(spark, variant):
    t = C.trips(spark, ["pickup_date", "tpep_pickup_datetime", "PULocationID", "fare_amount"])
    if variant == "baseline":
        return t.where(F.to_date("tpep_pickup_datetime") == F.lit(DAY).cast("date")).where(F.col("pickup_date") == F.to_date("tpep_pickup_datetime"))
    if variant == "pruned":
        return t.where(F.col("pickup_date") == F.lit(DAY).cast("date")).where(F.col("pickup_date") == F.to_date("tpep_pickup_datetime"))
    dates = spark.range(1).select(F.lit(DAY).cast("date").alias("pickup_date"))
    return t.join(F.broadcast(dates), "pickup_date").where(F.col("pickup_date") == F.to_date("tpep_pickup_datetime")).select(t.columns)
