"""Core lab 01 — Shuffle JOIN (plan §7, M08). Large × large join; compare SMJ, SHJ and BHJ.

The 265-row zone table would be broadcast automatically, so the large side here is trips ⋈ daily
location stats (~100k rows), and broadcast is disabled except in the `bhj` variant.
Read in the plan: two `Exchange hashpartitioning(PULocationID, pickup_date)` under SortMergeJoin.
"""
from pyspark.sql import functions as F
import common as C

_off = {"spark.sql.autoBroadcastJoinThreshold": "-1", "spark.sql.adaptive.autoBroadcastJoinThreshold": "-1"}
VARIANTS = {
    "baseline": {**_off},                                                   # SortMergeJoin
    "shj": {**_off, "spark.sql.join.preferSortMergeJoin": "false"},         # ShuffledHashJoin (no sort)
    "bhj": {"spark.sql.autoBroadcastJoinThreshold": "64MB"},                # BroadcastHashJoin (one Exchange less)
}
EXPECT = {
    "bhj": {"shuffle_r": ("<", 0.5, "x_baseline")},
}


def build(spark, variant):
    t = C.trips(spark, ["PULocationID", "pickup_date", "fare_amount", "trip_distance"])
    stats = t.groupBy("PULocationID", "pickup_date").agg(F.avg("fare_amount").alias("loc_day_avg_fare"))
    return t.join(stats, ["PULocationID", "pickup_date"])
