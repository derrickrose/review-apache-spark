"""Core lab 12 — Massive file discovery / listing (plan §7, M17/M24).

Lists objects through binaryFile selecting only metadata columns (content is pruned, no bytes read).
With LAB_SOURCE=real this lists one day of s3://unidata-nexrad-level2/ (tens of thousands of objects).
    baseline : recursive listing of the whole prefix (driver-side discovery of every object)
    pruned   : pathGlobFilter + a narrower prefix → fewer objects listed (different, intended result)
Look at the gap between job start and the first task: that is planning/listing time on the driver.
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "pruned": {}}
CHECK_CORRECTNESS = False
EXPECT = {"pruned": {"listing_s": ("<", 0.5, "x_baseline")}}


def run(spark, variant):
    import time
    df = C.nexrad_listing(spark)
    if variant == "pruned":
        root = C.REAL["nexrad"] if C.SOURCE == "real" else C.SYN["nexrad"]
        sub = root.rstrip("/") + ("/KTLX/" if C.SOURCE == "real" else "/station=KAMX/")
        df = (spark.read.format("binaryFile").option("recursiveFileLookup", "true").load(sub)
              .select("path", "length", "modificationTime"))
    t0 = time.time()
    plan_rows = df.select(F.count("*"), F.sum("length")).first()
    return {"objects": plan_rows[0], "bytes": plan_rows[1], "listing_s": round(time.time() - t0, 2)}
