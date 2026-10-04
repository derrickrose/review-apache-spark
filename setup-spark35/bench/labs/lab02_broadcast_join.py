"""Core lab 02 — Broadcast JOIN (plan §7, M08): threshold, hint, lifecycle, failure.

Manual failure step (not benchmarked, it is expected to fail):
    spark.conf.set("spark.sql.broadcastTimeout", "5")
    C.trips(spark).join(F.broadcast(C.trips(spark).limit(30_000_000)), "VendorID").count()
Capture the error (timeout or driver OOM) and locate the broadcast build in the SQL tab.
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {
    "baseline": {"spark.sql.autoBroadcastJoinThreshold": "-1",
                 "spark.sql.adaptive.autoBroadcastJoinThreshold": "-1"},   # forced SMJ against a 265-row table
    "auto": {},                                                            # default 10MB threshold → BHJ
    "hint": {"spark.sql.autoBroadcastJoinThreshold": "-1",
             "spark.sql.adaptive.autoBroadcastJoinThreshold": "-1"},       # threshold off, explicit hint wins
}
EXPECT = {
    "auto": {"shuffle_r": ("<", 0.2, "x_baseline")},
    "hint": {"shuffle_r": ("<", 0.2, "x_baseline")},
}


def build(spark, variant):
    t = C.trips(spark, ["PULocationID", "fare_amount"])
    z = C.zones(spark)
    z = F.broadcast(z) if variant == "hint" else z
    return t.join(z, t.PULocationID == z.LocationID)
