from pyspark.sql import SparkSession
from pyspark.sql.functions import col

### bucketing is intelligent way of splitting data before a join or group
### bucket pruning

## bucketing is a technique used in spark to split data into smaller chunks
## bucketing is avalaible in dataframe writer

import os

# Persistent catalog stored NEXT TO THIS SCRIPT:
#   metastore_db/     -> the catalog (table names, schema, bucketing info)
#   spark-warehouse/  -> the table data
# Because the catalog survives between runs, mode("overwrite") recognizes
# the existing tables and replaces them.
HERE = os.path.dirname(os.path.abspath(__file__))

spark = (
    SparkSession.builder.appName("Bucketing")
    .master("local[2]")
    .config("spark.sql.warehouse.dir", os.path.join(HERE, "spark-warehouse"))
    .config("spark.sql.sources.bucketing.autoBucketedScan.enabled", "false")
    .config(
        "spark.hadoop.javax.jdo.option.ConnectionURL",
        f"jdbc:derby:;databaseName={os.path.join(HERE, 'metastore_db')};create=true",
    )
    .enableHiveSupport()
    .getOrCreate()
)

# deactivate broadcasting and aqe
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
spark.conf.set("spark.sql.adaptive.enabled", "false")

large_df = spark.range(1000000).selectExpr("id * 5 AS id").repartition(10)
small_df = spark.range(10000).selectExpr("id * 3 AS id").repartition(3)

joined = large_df.join(small_df, "id")
joined.explain()
"""
== Physical Plan ==
*(5) Project [id#2L]
+- *(5) SortMergeJoin [id#2L], [id#6L], Inner
   :- *(2) Sort [id#2L ASC NULLS FIRST], false, 0
   :  +- Exchange hashpartitioning(id#2L, 200), ENSURE_REQUIREMENTS, [plan_id=40]
   :     +- Exchange RoundRobinPartitioning(10), REPARTITION_BY_NUM, [plan_id=39]
   :        +- *(1) Project [(id#0L * 5) AS id#2L]
   :           +- *(1) Range (0, 1000000, step=1, splits=2)
   +- *(4) Sort [id#6L ASC NULLS FIRST], false, 0
      +- Exchange hashpartitioning(id#6L, 200), ENSURE_REQUIREMENTS, [plan_id=47]
         +- Exchange RoundRobinPartitioning(3), REPARTITION_BY_NUM, [plan_id=46]
            +- *(3) Project [(id#4L * 3) AS id#6L]
               +- *(3) Range (0, 10000, step=1, splits=2)
"""

# bucketing
# mode("overwrite") works across runs thanks to the persistent catalog above.
large_df.write.bucketBy(4, "id").sortBy("id").mode("overwrite").saveAsTable(
    "large_bucketed"
)
small_df.write.bucketBy(4, "id").sortBy("id").mode("overwrite").saveAsTable(
    "small_bucketed"
)  ## bucketing and saving is almost as expensive as a regular shuffle
## no shuffle, almost as expensive as shuffle

# reading from bucketed data
bucketed_small = spark.table("small_bucketed")
bucketed_large = spark.table("large_bucketed")
bucketed_join = bucketed_large.join(bucketed_small, "id")
bucketed_join.explain()
"""
== Physical Plan ==
*(3) Project [id#17L]
+- *(3) SortMergeJoin [id#17L], [id#15L], Inner
   :- *(1) Sort [id#17L ASC NULLS FIRST], false, 0
   :  +- *(1) Filter isnotnull(id#17L)
   :     +- *(1) ColumnarToRow
   :        +- FileScan parquet spark_catalog.default.large_bucketed[id#17L] Batched: true, Bucketed: true, DataFilters: [isnotnull(id#17L)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:bigint>, SelectedBucketsCount: 4 out of 4
   +- *(2) Sort [id#15L ASC NULLS FIRST], false, 0
      +- *(2) Filter isnotnull(id#15L)
         +- *(2) ColumnarToRow
            +- FileScan parquet spark_catalog.default.small_bucketed[id#15L] Batched: true, Bucketed: true, DataFilters: [isnotnull(id#15L)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:bigint>, SelectedBucketsCount: 4 out of 4

joining bucketed data is so much faster it is almost the same as hashpartitioning on key
"""

## bucketing for groups
## average delay of flights group by origin, destination and the carrier (airline)
import time

from pathlib import Path

DATA: Path = Path(__file__).parents[3] / "data"

flights_df = (
    spark.read.option("inferSchema", "true")
    .json(str(DATA / "flights" / "flights.json"))
    .repartition(2)
)

from pyspark.sql import functions as F

avg_delay_df = (
    flights_df.filter("origin = 'DEN' AND arrdelay > 1")
    .groupBy("origin", "dest", "carrier")
    .agg(F.avg("arrdelay").alias("avg_delay"))
    .orderBy(col("avg_delay").desc_nulls_first())
)
avg_delay_df.explain()
"""
== Physical Plan ==
*(4) Sort [avg_delay#68 DESC NULLS FIRST], true, 0
+- Exchange rangepartitioning(avg_delay#68 DESC NULLS FIRST, 200), ENSURE_REQUIREMENTS, [plan_id=245]
   +- *(3) HashAggregate(keys=[origin#41, dest#38, carrier#32], functions=[avg(arrdelay#31)])
      +- Exchange hashpartitioning(origin#41, dest#38, carrier#32, 200), ENSURE_REQUIREMENTS, [plan_id=241]
         +- *(2) HashAggregate(keys=[origin#41, dest#38, carrier#32], functions=[partial_avg(arrdelay#31)])
            +- Exchange RoundRobinPartitioning(2), REPARTITION_BY_NUM, [plan_id=237]
               +- *(1) Filter (((isnotnull(origin#41) AND isnotnull(arrdelay#31)) AND (origin#41 = DEN)) AND (arrdelay#31 > 1.0))
                  +- FileScan json [arrdelay#31,carrier#32,dest#38,origin#41] Batched: false, DataFilters: [isnotnull(origin#41), isnotnull(arrdelay#31), (origin#41 = DEN), (arrdelay#31 > 1.0)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/flights/fl..., PartitionFilters: [], PushedFilters: [IsNotNull(origin), IsNotNull(arrdelay), EqualTo(origin,DEN), GreaterThan(arrdelay,1.0)], ReadSchema: struct<arrdelay:double,carrier:string,dest:string,origin:string>
2 shuffles for the grouping operation
"""

### let optimize this using bucketing

flights_df.write.partitionBy("origin").bucketBy(4, "dest", "carrier").mode(
    "overwrite"
).saveAsTable("flights_bucketed")

bucketed_avg_delay = (
    spark.table("flights_bucketed")
    .filter("origin = 'DEN' AND arrdelay > 1")
    .groupBy("origin", "dest", "carrier")
    .agg(F.avg("arrdelay").alias("avg_delay"))
    .orderBy(col("avg_delay").desc_nulls_first())
)
bucketed_avg_delay.explain()
"""
*(2) Sort [avg_delay#170 DESC NULLS FIRST], true, 0
+- Exchange rangepartitioning(avg_delay#170 DESC NULLS FIRST, 200), ENSURE_REQUIREMENTS, [plan_id=340]
   +- *(1) HashAggregate(keys=[origin#143, dest#140, carrier#134], functions=[avg(arrdelay#133)])
      +- *(1) HashAggregate(keys=[origin#143, dest#140, carrier#134], functions=[partial_avg(arrdelay#133)])
         +- *(1) Filter (isnotnull(arrdelay#133) AND (arrdelay#133 > 1.0))
            +- *(1) ColumnarToRow
               +- FileScan parquet spark_catalog.default.flights_bucketed[arrdelay#133,carrier#134,dest#140,origin#143] Batched: true, Bucketed: true, DataFilters: [isnotnull(arrdelay#133), (arrdelay#133 > 1.0)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [isnotnull(origin#143), (origin#143 = DEN)], PushedFilters: [IsNotNull(arrdelay), GreaterThan(arrdelay,1.0)], ReadSchema: struct<arrdelay:double,carrier:string,dest:string>, SelectedBucketsCount: 4 out of 4

note that there is just one shuffle 
"""

val_10 = bucketed_large.filter("id = 10")
val_10.show()
val_10.explain()
"""
== Physical Plan ==
*(1) Filter (isnotnull(id#17L) AND (id#17L = 10))
+- *(1) ColumnarToRow
   +- FileScan parquet spark_catalog.default.large_bucketed[id#17L] Batched: true, Bucketed: true, DataFilters: [isnotnull(id#17L), (id#17L = 10)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id), EqualTo(id,10)], ReadSchema: struct<id:bigint>, SelectedBucketsCount: 1 out of 4
   
you can see at the end of the plan that it says selected buckets count: 1 out of 4
which means that bucket prunning is working 
dont forget to disable auto bucketed scan in order to see it work, it is automatically enabled by default on spark starting from spark 3.1.0
"""

import time

time.sleep(10000)
