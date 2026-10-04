"""Core lab 15 — Geographic / key skew (plan §7, M09), natural skew first.

OSM nodes bucketed on a 1° lat/lon grid: dense cities make a few cells dominate.
    baseline : repartition(200, cell)    → overloaded partitions for the dense cells
    fine     : 0.1° grid                 → finer key, more balanced
    rebalance: REBALANCE(cell) hint      → AQE splits oversized partitions
Rows are unchanged by every variant (only placement changes), so checksums must match.
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "fine": {}, "rebalance": {}}
EXPECT = {
    "baseline": {"max_over_median": (">", 3)},
    "fine": {"max_over_median": ("<", 0.5, "x_baseline")},
    "rebalance": {"max_over_median": ("<", 0.5, "x_baseline")},
}


def build(spark, variant):
    n = C.osm(spark).where("type = 'node'").select("id", "lat", "lon")
    if variant == "fine":
        return n.withColumn("cell", F.concat_ws(":", F.floor(n.lat * 10), F.floor(n.lon * 10))).repartition(200, "cell").drop("cell")
    n = n.withColumn("cell", F.concat_ws(":", F.floor("lat"), F.floor("lon")))
    return (n.repartition(200, "cell") if variant == "baseline" else n.hint("rebalance", "cell")).drop("cell")
