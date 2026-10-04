"""Core lab 10 — Small files (plan §7, M17).

setup() writes the same data twice: 20,000 tiny files and ~16 well-sized files (use 100k+ files on
a cluster). The benchmark reads each layout with the same aggregation.
Chain to observe: files → file splits (input partitions) → tasks → scheduling/listing overhead.
"""
from pyspark.sql import functions as F
import common as C

SMALL = f"{C.OUT}/lab10/small"
COMPACT = f"{C.OUT}/lab10/compact"
N_SMALL = 20_000
VARIANTS = {"baseline": {}, "compact": {}}
EXPECT = {"compact": {"tasks": ("<", 0.5, "x_baseline"), "runtime_median_s": ("<", 0.8, "x_baseline")}}


def setup(spark):
    t = C.trips(spark, ["PULocationID", "DOLocationID", "fare_amount", "tpep_pickup_datetime"])
    if not C.exists(spark, SMALL):
        t.repartition(N_SMALL).write.mode("overwrite").parquet(SMALL)
    if not C.exists(spark, COMPACT):
        t.repartition(16).write.mode("overwrite").parquet(COMPACT)


def build(spark, variant):
    df = spark.read.parquet(SMALL if variant == "baseline" else COMPACT)
    return df.groupBy("PULocationID").agg(F.sum("fare_amount").cast("decimal(20,2)").alias("s"), F.count("*").alias("n"))


def run(spark, variant):
    build(spark, variant).write.format("noop").mode("overwrite").save()
    n, size = C.file_stats(spark, SMALL if variant == "baseline" else COMPACT)
    return {"files": n, "avg_file_kb": round(size / n / 1024, 1)}
