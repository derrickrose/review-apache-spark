"""
PySpark port of scala/part4rddjoins/RDDBroadcastJoins.scala
Notes: 03_broadcast_joins_to_read.md

Scenario: assign prizes to a wide-scale competition (10M+ people). Who won what?
The RDD API has no automatic broadcast join -> do it by hand.
"""

import random
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

N = 2_000_000  # course: 10M (38s plain vs 2s broadcast on the JVM)

spark = get_spark("Broadcast Joins")
sc = spark.sparkContext

# small lookup table
prizes = sc.parallelize([(1, "gold"), (2, "silver"), (3, "bronze")])

# the leaderboard is known: (rank, name). Names are generated on the executors.
leaderboard = sc.range(1, N + 1).map(
    lambda i: (i, "".join(random.choices(string.ascii_letters + string.digits, k=8)))
)


def plain_join():
    # shuffles N rows to match 3 rows
    return leaderboard.join(prizes).collect()


# 1. collect the small RDD on the driver, 2. broadcast it
# Unlike the Scala code (which discards the Broadcast handle and captures the map in the
# closure), we use the handle: shipped once per executor instead of once per task.
medals_bc = sc.broadcast(prizes.collectAsMap())


def broadcast_join():
    def lookup(records):  # iterator over the partition, all local
        medals = medals_bc.value
        for index, name in records:
            medal = medals.get(index)
            if medal is not None:  # inner join: drop non-matching rows
                yield name, medal

    # 3. map-side lookup, no shuffle at all
    return leaderboard.mapPartitions(lookup).collect()


if __name__ == "__main__":
    print(timed("plain_join", plain_join))
    print(timed("broadcast_join", broadcast_join))
    keep_ui_open()
