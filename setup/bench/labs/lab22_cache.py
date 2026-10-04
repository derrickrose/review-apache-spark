"""Core lab 22 — Cache / recomputation (plan §7, M14). One filtered base, three actions.

    baseline : no cache → the scan + filter runs three times (3 jobs re-reading the input)
    cache    : base.cache() + materialize once → later actions read InMemoryTableScan
    cache_bad: cache a base used only once → pure overhead (find when caching hurts)
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "cache": {}, "cache_bad": {}}
CHECK_CORRECTNESS = False
EXPECT = {"cache": {"input": ("<", 0.5, "x_baseline")}}


def run(spark, variant):
    base = C.trips(spark).where(F.col("fare_amount") > 10)
    if variant in ("cache", "cache_bad"):
        base = base.cache()
        base.count()
    if variant == "cache_bad":
        base.groupBy("PULocationID").count().write.format("noop").mode("overwrite").save()
    else:
        for col in ("PULocationID", "DOLocationID", "VendorID"):
            base.groupBy(col).count().write.format("noop").mode("overwrite").save()
    base.unpersist()
