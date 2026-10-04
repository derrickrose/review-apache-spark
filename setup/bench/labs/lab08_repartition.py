"""Core lab 08 — Repartition / shuffle (plan §7, M05/M06).

~265 location keys hashed into 200 shuffle partitions → collisions, empty and oversized partitions.
Compare the Exchange variants with explain("formatted"):
    baseline  : repartition("PULocationID")       hashpartitioning(PULocationID, 200)
    roundrobin: repartition(200)                  RoundRobinPartitioning(200)
    rebalance : REBALANCE hint                    AQE splits/coalesces to the advisory size
"""
import common as C

VARIANTS = {"baseline": {}, "roundrobin": {}, "rebalance": {}}
EXPECT = {
    "baseline": {"max_over_median": (">", 3)},
    "roundrobin": {"max_over_median": ("<", 2)},
    "rebalance": {"max_over_median": ("<", 2.5)},
}


def build(spark, variant):
    t = C.trips(spark, ["PULocationID", "tpep_pickup_datetime", "fare_amount", "trip_distance"])
    if variant == "baseline":
        return t.repartition("PULocationID")
    if variant == "roundrobin":
        return t.repartition(200)
    return t.hint("rebalance")
