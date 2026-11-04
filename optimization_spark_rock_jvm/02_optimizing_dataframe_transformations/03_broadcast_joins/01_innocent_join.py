import time
from pyspark.sql import SparkSession, Row
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

spark = (
    SparkSession.builder.appName("Innocent Join")
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

# the innocent join
# no auto broadcast even though the table is small, because Spark doesn't know the size of an RDD
# it assumes sizeInBytes = spark.sql.defaultSizeInBytes, which is Long.MaxValue bytes, roughly 8 exabytes
# (this is a size in bytes, not a row count, see 00_broadcast_joins.md section 1)


joined = table.join(lookup_table, "id")
joined.explain()
"""
== Physical Plan ==
*(5) Project [id#4L, order#1]
+- *(5) SortMergeJoin [id#4L], [cast(id#0 as bigint)], Inner
   :- *(2) Sort [id#4L ASC NULLS FIRST], false, 0
   :  +- Exchange hashpartitioning(id#4L, 200), ENSURE_REQUIREMENTS, [plan_id=27]
   :     +- *(1) Range (1, 100000000, step=1, splits=2)
   +- *(4) Sort [cast(id#0 as bigint) ASC NULLS FIRST], false, 0
      +- Exchange hashpartitioning(cast(id#0 as bigint), 200), ENSURE_REQUIREMENTS, [plan_id=33]
         +- *(3) Filter isnotnull(id#0)
            +- *(3) Scan ExistingRDD[id#0,order#1]
"""
# SortMergeJoin: both sides are shuffled (Exchange hashpartitioning, 200 partitions) then sorted
# the 100M-row table is moved across the network just to match 4 rows -> very slow

joined.show()

if __name__ == "__main__":
    time.sleep(1000)
