import time
from pyspark.sql import SparkSession, Row
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

spark = (
    SparkSession.builder.appName("Broadcast Joins")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

sc = spark.sparkContext

rows = sc.parallelize(
    [
        Row(0, "zero"),
        Row(1, "first"),
        Row(2, "second"),
        Row(3, "third"),
    ]
)

rows_schema = StructType(
    [
        StructField("id", IntegerType()),
        StructField("order", StringType()),
    ]
)

# small table
lookup_table = spark.createDataFrame(rows, rows_schema)

# large table
table = spark.range(1, 100000000)  # column is "id"

# a smarter join
# Spark can't estimate the RDD-based lookup_table size (see 01_innocent_join.py),
# so we tell it explicitly with the broadcast() hint
from pyspark.sql.functions import broadcast

joined = table.join(broadcast(lookup_table), "id")
joined.explain()
"""
== Physical Plan ==
*(2) Project [id#4L, order#1]
+- *(2) BroadcastHashJoin [id#4L], [cast(id#0 as bigint)], Inner, BuildRight, false
   :- *(2) Range (1, 100000000, step=1, splits=2)
   +- BroadcastExchange HashedRelationBroadcastMode(List(cast(input[0, int, false] as bigint)),false), [plan_id=74]
      +- *(1) Filter isnotnull(id#0)
         +- *(1) Scan ExistingRDD[id#0,order#1]
"""
# BroadcastHashJoin ... BuildRight: the small table (right side) is the one broadcast

joined.show()
##### VERY IMPORTANT
# why this is so fast
## because the broadcast copies the small dataframe entirely to every executor: no shuffle,
## the big table stays where it is and each partition is joined in memory against the copy
## use it when a big df is joined with a small df (the small one must fit in executor/driver memory)

if __name__ == "__main__":
    time.sleep(1000)
