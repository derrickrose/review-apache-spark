"""Core lab 24 — Driver pressure: collect / toPandas (plan §7, M24).

Benchmarked (safe sizes): toPandas of 5M rows with and without Arrow.
Manual failure step (expected OOM / maxResultSize error, capture it):
    spark.conf.set("spark.driver.maxResultSize", "512m"); C.trips(spark).collect()
"""
import common as C

N = 5_000_000
VARIANTS = {"baseline": {"spark.sql.execution.arrow.pyspark.enabled": "false"},
            "arrow": {"spark.sql.execution.arrow.pyspark.enabled": "true"}}
CHECK_CORRECTNESS = False
EXPECT = {"arrow": {"runtime_median_s": ("<", 0.5, "x_baseline")}}


def run(spark, variant):
    pdf = C.trips(spark, ["PULocationID", "tpep_pickup_datetime", "fare_amount"]).limit(N).toPandas()
    return {"rows_on_driver": len(pdf), "driver_mb": int(pdf.memory_usage(deep=True).sum() // 2**20)}
