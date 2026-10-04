"""Core lab 27 — Small files + skew combined (plan §7, M17/M09).

repartition(N, hot_key) sends ALL hot rows to ONE partition: you get one giant file plus many tiny or
empty partitions — not N balanced files. Diagnose both symptoms (task skew AND file-size spread).
    baseline : repartition(2000, k) then write
    rebalance: REBALANCE(k) hint then write (AQE splits the hot partition, merges the tiny ones)
"""
import common as C

SKEWED = f"{C.BASE}/tlc/yellow_skewed"
VARIANTS = {"baseline": {}, "rebalance": {}}
EXPECT = {"baseline": {"max_over_median": (">", 4)}, "rebalance": {"max_file_mb": ("<", 0.5, "x_baseline")}}


def setup(spark):
    C.materialize_skew(spark, SKEWED)


def _path(v):
    return f"{C.OUT}/lab27/{v}"


def run(spark, variant):
    t = spark.read.parquet(SKEWED).drop("pickup_date")
    (t.repartition(2000, "k") if variant == "baseline" else t.hint("rebalance", "k")).write.mode("overwrite").parquet(_path(variant))
    files = spark.read.format("binaryFile").load(_path(variant) + "/*.parquet").select("length").toPandas()["length"]
    return {"files": len(files), "max_file_mb": round(files.max() / 2**20, 1), "median_file_kb": round(files.median() / 1024, 1)}


def result(spark, variant):
    return spark.read.parquet(_path(variant))
