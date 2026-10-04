"""Core lab 09 — Partition explosion at write (plan §7, M05/M17).

Files written = Σ over tasks of (distinct partition values in that task). With a high-cardinality
partition column and data spread across all tasks, this is ~tasks × values.
    baseline   : partitionBy(pickup_hour) directly (336 hours × 32 tasks ≈ 10.7k files)
    clustered  : repartition("pickup_hour") first → each value in one task → 1 file per value
    lower_card : partitionBy(pickup_date) after repartition (14 values) — a design change
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "clustered": {}, "lower_card": {}}
EXPECT = {
    "clustered": {"files": ("<", 0.2, "x_baseline")},
    "lower_card": {"files": ("<", 50)},
}


def _df(spark):
    return (C.trips(spark, ["tpep_pickup_datetime", "PULocationID", "fare_amount"])
            .withColumn("pickup_hour", F.date_format("tpep_pickup_datetime", "yyyy-MM-dd-HH"))
            .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
            .where(F.col("pickup_date").between("2024-03-01", "2024-03-14"))
            .repartition(32))                                   # upstream shuffle: data spread over 32 tasks


def _path(variant):
    return f"{C.OUT}/lab09/{variant}"


def run(spark, variant):
    df = _df(spark)
    if variant == "baseline":
        w = df.write.partitionBy("pickup_hour")
    elif variant == "clustered":
        w = df.repartition("pickup_hour").write.partitionBy("pickup_hour")
    else:
        w = df.repartition("pickup_date").write.partitionBy("pickup_date")
    w.mode("overwrite").parquet(_path(variant))
    n, size = C.file_stats(spark, _path(variant))
    return {"files": n, "avg_file_kb": round(size / max(n, 1) / 1024, 1)}


def result(spark, variant):
    return spark.read.parquet(_path(variant)).select("tpep_pickup_datetime", "PULocationID", "fare_amount")
