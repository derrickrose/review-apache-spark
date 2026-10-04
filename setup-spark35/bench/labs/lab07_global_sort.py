"""Core lab 07 — Global sort (plan §7, M11).

orderBy = sampling job + range Exchange + Sort (total order across partitions).
sortWithinPartitions = Sort only, no shuffle — NOT equivalent: order holds only inside each partition.
Correctness: both keep the same rows (checksum is order-independent), the ordering guarantee differs.
"""
import common as C

VARIANTS = {"baseline": {}, "within": {}}
EXPECT = {"within": {"shuffle_w": ("<", 0.05, "x_baseline"), "runtime_median_s": ("<", 1.0, "x_baseline")}}


def build(spark, variant):
    t = C.trips(spark, ["tpep_pickup_datetime", "PULocationID", "fare_amount"])
    return t.orderBy("tpep_pickup_datetime") if variant == "baseline" else t.sortWithinPartitions("tpep_pickup_datetime")
