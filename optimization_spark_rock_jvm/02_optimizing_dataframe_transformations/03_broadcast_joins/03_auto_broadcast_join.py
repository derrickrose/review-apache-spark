import time
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("Broadcast Joins")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

small_table_df = spark.range(1, 10000)
big_table_df = spark.range(1, 100000000)
joined = small_table_df.join(big_table_df, "id")

joined.explain()

"""
== Physical Plan ==
*(2) Project [id#0L]
+- *(2) BroadcastHashJoin [id#0L], [id#2L], Inner, BuildLeft, false
   :- BroadcastExchange HashedRelationBroadcastMode(List(input[0, bigint, false]),false), [plan_id=19]
   :  +- *(1) Range (1, 10000, step=1, splits=2)
   +- *(2) Range (1, 100000000, step=1, splits=2)
"""

## VERY IMPORTANT:
# Spark knows the exact size of a range (here 9999 rows x 8 bytes ≈ 80 KB), so it broadcasts it automatically, no hint needed.
# This is unlike a DataFrame created from an RDD: Spark can't measure its size and assumes Long.MaxValue bytes (see 01_max_long.py).
# Spark only broadcasts automatically when the estimated size of the smaller table is below the threshold.
# Above the threshold, it falls back to a shuffle join (SortMergeJoin).
## spark.sql.autoBroadcastJoinThreshold: the maximum estimated size, in bytes, of a table that Spark broadcasts automatically to all executors in a join.
## default: 10485760 (10 MB). Set it to -1 to disable automatic broadcast joins.
if __name__ == "__main__":
    time.sleep(1000)
