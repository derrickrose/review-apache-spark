"""Core lab 11 — Excessive read parallelism (plan §7, M17). Reuses the lab 10 small-file layout.

Spark packs files into splits up to maxPartitionBytes, charging openCostInBytes per file. Small
maxPartitionBytes → many tasks and many concurrent object-store requests; large → fewer, bigger tasks.
"""
from pyspark.sql import functions as F
import common as C
import lab10_small_files as L10

VARIANTS = {
    "baseline": {"spark.sql.files.maxPartitionBytes": "1MB", "spark.sql.files.openCostInBytes": "0"},
    "mpb128m": {"spark.sql.files.maxPartitionBytes": "128MB"},
    "mpb512m": {"spark.sql.files.maxPartitionBytes": "512MB"},
}
EXPECT = {"mpb128m": {"tasks": ("<", 0.3, "x_baseline")}, "mpb512m": {"tasks": ("<", 0.3, "x_baseline")}}


def setup(spark):
    L10.setup(spark)


def build(spark, variant):
    return (spark.read.parquet(L10.SMALL).groupBy("PULocationID")
            .agg(F.sum("fare_amount").cast("decimal(20,2)").alias("s")))
