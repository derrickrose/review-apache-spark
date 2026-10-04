"""Core lab 17 — Complex / graph-like JOIN (plan §7, M08). Ways → node refs → node coordinates.

There is no node_id column: ways carry nds ARRAY<STRUCT<ref>>, so explode first, then join on ref = id.
    baseline : join the full rows (all columns, tags maps included) and project at the end
    pruned   : project the join keys + needed columns BEFORE the join (less shuffle)
Rows are identical; compare Shuffle Write and intermediate cardinality (exploded refs per way).
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "pruned": {}}
EXPECT = {"pruned": {"shuffle_w": ("<", 0.8, "x_baseline")}}


def build(spark, variant):
    o = C.osm(spark)
    ways, nodes = o.where("type = 'way'"), o.where("type = 'node'")
    refs = ways.select(F.col("id").alias("way_id"), F.col("tags").alias("way_tags"),
                       F.posexplode("nds").alias("pos", "nd"))
    if variant == "baseline":
        j = refs.join(nodes, refs.nd.ref == nodes.id)
        return j.select("way_id", "pos", "lat", "lon")
    r = refs.select("way_id", "pos", F.col("nd.ref").alias("ref"))
    n = nodes.select(F.col("id").alias("ref"), "lat", "lon")
    return r.join(n, "ref").select("way_id", "pos", "lat", "lon")
