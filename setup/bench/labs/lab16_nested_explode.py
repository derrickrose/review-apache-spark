"""Core lab 16 — Nested data / explode (plan §7, M15).

`tags` is MAP<string,string>: explode yields (key, value) — one row per tag.
    baseline : explode every tag, then keep key = 'highway'   (amplify, then filter)
    direct   : read tags['highway'] without exploding           (same result, no amplification)
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "direct": {}}
EXPECT = {"direct": {"runtime_median_s": ("<", 0.8, "x_baseline")}}


def build(spark, variant):
    o = C.osm(spark).select("id", "tags")
    if variant == "baseline":
        return o.select("id", F.explode("tags").alias("key", "value")).where("key = 'highway'").select("id", "value")
    return o.select("id", F.element_at("tags", F.lit("highway")).alias("value")).where(F.col("value").isNotNull())


def run(spark, variant):
    o = C.osm(spark)
    exploded = o.select(F.explode("tags")).count()
    build(spark, variant).write.format("noop").mode("overwrite").save()
    return {"input_rows": o.count(), "exploded_rows": exploded}
