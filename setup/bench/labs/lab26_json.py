"""Core lab 26 — JSON parsing (plan §7, M15). Landsat STAC items (real or same-shape synthetic).

All variants extract (id, datetime, cloud_cover) for items with eo:cloud_cover < 10.
    baseline : spark.read.json → schema INFERENCE pass over all the data, then query
    explicit : from_json with an explicit DDL schema (one pass, only needed fields)
    variant  : parse_json → VARIANT + variant_get (Spark 4)
"""
from pyspark.sql import functions as F
import common as C

SCHEMA = "id string, properties struct<datetime:string, `eo:cloud_cover`:double>"
VARIANTS = {"baseline": {}, "explicit": {}, "variant": {}}
EXPECT = {"explicit": {"runtime_median_s": ("<", 0.8, "x_baseline")}}


def build(spark, variant):
    raw = C.stac(spark)
    if variant == "baseline":
        path = C.REAL["stac"] if C.SOURCE == "real" else C.SYN["stac"]
        j = spark.read.json(path)
        out = j.select("id", F.col("properties.datetime").alias("dt"), F.col("properties.`eo:cloud_cover`").alias("cc"))
    elif variant == "explicit":
        j = raw.select(F.from_json("value", SCHEMA).alias("j"))
        out = j.select("j.id", F.col("j.properties.datetime").alias("dt"), F.col("j.properties.`eo:cloud_cover`").alias("cc"))
    else:
        v = raw.select(F.parse_json("value").alias("v"))
        out = v.select(F.variant_get("v", "$.id", "string").alias("id"),
                       F.variant_get("v", "$.properties.datetime", "string").alias("dt"),
                       F.variant_get("v", "$.properties['eo:cloud_cover']", "double").alias("cc"))
    return out.where(F.col("cc") < 10)
