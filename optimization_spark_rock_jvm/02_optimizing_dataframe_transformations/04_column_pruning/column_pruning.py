from pyspark.sql import SparkSession
from pyspark.sql.functions import array_contains, upper

spark = SparkSession.builder.appName("Column Pruning").master("local[2]").getOrCreate()

sc = spark.sparkContext

guitars_df = spark.read.json("../data/guitars/guitars.json")
guitar_players_df = spark.read.json("../data/guitarPlayers/guitarPlayers.json")
bands_df = spark.read.json("../data/bands/bands.json")

join_condition = guitar_players_df["band"] == bands_df["id"]
guitarists_bands_df = guitar_players_df.join(bands_df, join_condition, "inner")
guitarists_bands_df.explain()

# Column pruning is a Catalyst optimizer rule that removes columns the query does not need.
# Spark reads, shuffles and processes only the columns that are actually referenced downstream.
# In this example, the query only needs the "name" column from the "bands" DataFrame, so Spark will only read and process that column.
"""
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- BroadcastHashJoin [band#24L], [id#41L], Inner, BuildLeft, false
   :- BroadcastExchange HashedRelationBroadcastMode(List(input[0, bigint, false]),false), [plan_id=30]
   :  +- Filter isnotnull(band#24L)
   :     +- FileScan json [band#24L,guitars#25,id#26L,name#27] Batched: false, DataFilters: [isnotnull(band#24L)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(band)], ReadSchema: struct<band:bigint,guitars:array<bigint>,id:bigint,name:string>
   +- Filter isnotnull(id#41L)
      +- FileScan json [hometown#40,id#41L,name#42,year#43L] Batched: false, DataFilters: [isnotnull(id#41L)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<hometown:string,id:bigint,name:string,year:bigint>
"""

guitarists_without_bands_df = guitar_players_df.join(
    bands_df, join_condition, "left_anti"
)
guitarists_without_bands_df.explain()

"""
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- BroadcastHashJoin [band#24L], [id#41L], LeftAnti, BuildRight, false
   :- FileScan json [band#24L,guitars#25,id#26L,name#27] Batched: false, DataFilters: [], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [], ReadSchema: struct<band:bigint,guitars:array<bigint>,id:bigint,name:string>
   +- BroadcastExchange HashedRelationBroadcastMode(List(input[0, bigint, false]),false), [plan_id=49]
      +- Filter isnotnull(id#41L)
         +- FileScan json [id#41L] Batched: false, DataFilters: [isnotnull(id#41L)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:bigint>


Column pruning = cut off columns that are not relevant
= shrinks DF
* useful for joins and groups
"""
print("hola----------------------------------")
# project and filter pushdown
names_df = guitarists_bands_df.select(guitar_players_df["name"], bands_df["name"])
names_df.explain()

"""
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [name#27, name#42]
   +- BroadcastHashJoin [band#24L], [id#41L], Inner, BuildRight, false
      :- Filter isnotnull(band#24L)
      :  +- FileScan json [band#24L,name#27] Batched: false, DataFilters: [isnotnull(band#24L)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(band)], ReadSchema: struct<band:bigint,name:string>
      +- BroadcastExchange HashedRelationBroadcastMode(List(input[0, bigint, false]),false), [plan_id=77]
         +- Filter isnotnull(id#41L)
            +- FileScan json [id#41L,name#42] Batched: false, DataFilters: [isnotnull(id#41L)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:bigint,name:string>


Spark tends to drop columns as early as possible.
Should be YOUR goal as well.
"""

rock_df = guitar_players_df.join(bands_df, join_condition).join(
    guitars_df, array_contains(guitar_players_df["guitars"], guitars_df["id"])
)

print("here---------------------")

essentials_df = rock_df.select(
    guitar_players_df["name"],
    bands_df["name"],
    upper(guitars_df["make"]),
)
essentials_df.explain()

"""
here---------------------
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [name#27, name#42, upper(make#10) AS upper(make)#117]
   +- BroadcastNestedLoopJoin BuildRight, Inner, array_contains(guitars#25, id#9L)
      :- Project [guitars#25, name#27, name#42]
      :  +- BroadcastHashJoin [band#24L], [id#41L], Inner, BuildRight, false
      :     :- Filter (isnotnull(band#24L) AND isnotnull(guitars#25))
      :     :  +- FileScan json [band#24L,guitars#25,name#27] Batched: false, DataFilters: [isnotnull(band#24L), isnotnull(guitars#25)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(band), IsNotNull(guitars)], ReadSchema: struct<band:bigint,guitars:array<bigint>,name:string>
      :     +- BroadcastExchange HashedRelationBroadcastMode(List(input[0, bigint, false]),false), [plan_id=124]
      :        +- Filter isnotnull(id#41L)
      :           +- FileScan json [id#41L,name#42] Batched: false, DataFilters: [isnotnull(id#41L)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:bigint,name:string>
      +- BroadcastExchange IdentityBroadcastMode, [plan_id=128]
         +- Filter isnotnull(id#9L)
            +- FileScan json [id#9L,make#10] Batched: false, DataFilters: [isnotnull(id#9L)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/rock_the_jvm_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:bigint,make:string>


"""

"""
LESSON: if you anticipate that the joined table is much larger than the table on whose column you are applying the
map-side operation, e.g. " * 5", or "upper", do this operation on the small table FIRST.

Particularly useful for outer joins.
"""

import time

time.sleep(10000)
