"""Core lab 23 — Oversized cache / memory pressure (plan §7, M13/M14). Watch the Storage tab and GC.

    baseline  : cache the full wide table deserialized in memory (MEMORY_ONLY) → eviction + recomputation
    projected : cache only the 3 columns the downstream needs
    disk      : MEMORY_AND_DISK (serialized spill of what does not fit)
Downstream is identical: two aggregations.
"""
from pyspark import StorageLevel
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "projected": {}, "disk": {}}
CHECK_CORRECTNESS = False
EXPECT = {"projected": {"gc_ms": ("<", 0.7, "x_baseline")}}


def run(spark, variant):
    t = C.trips(spark).withColumn("copy", F.explode(F.sequence(F.lit(1), F.lit(3))))   # 3× to exceed storage memory
    if variant == "projected":
        t = t.select("PULocationID", "DOLocationID", "fare_amount")
    t = t.persist(StorageLevel.MEMORY_AND_DISK if variant == "disk" else StorageLevel.MEMORY_ONLY)
    t.count()
    t.groupBy("PULocationID").agg(F.sum("fare_amount")).write.format("noop").mode("overwrite").save()
    t.groupBy("DOLocationID").agg(F.avg("fare_amount")).write.format("noop").mode("overwrite").save()
    rdd_info = spark.sparkContext._jsc.sc().getRDDStorageInfo()
    mem = sum(i.memSize() for i in rdd_info); disk = sum(i.diskSize() for i in rdd_info)
    cached = max([i.numCachedPartitions() / max(i.numPartitions(), 1) for i in rdd_info] or [0])
    t.unpersist()
    return {"cached_mem_mb": mem // 2**20, "cached_disk_mb": disk // 2**20, "fraction_cached": round(cached, 2)}
