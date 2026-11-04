import time
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    IntegerType,
    StringType,
    ArrayType,
)

spark = (
    SparkSession.builder.appName("Colum Joins")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

DATA: Path = Path(__file__).resolve().parents[3] / "data"

guitars_schema = StructType(
    [
        StructField("id", IntegerType(), True),
        StructField("model", StringType(), True),
        StructField("make", StringType(), True),
        StructField("guitarType", StringType(), True),
    ]
)

guitar_player_schema = StructType(
    [
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("guitars", ArrayType(IntegerType()), True),
        StructField("band", StringType(), True),
    ]
)

bands_schema = StructType(
    [
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("hometown", StringType(), True),
        StructField("year", IntegerType(), True),
    ]
)

guitars_df = spark.read.json(
    str(DATA / "guitars" / "guitars.json"), schema=guitars_schema
)
guitar_players_df = spark.read.json(
    str(DATA / "guitarPlayers" / "guitarPlayers.json"), schema=guitar_player_schema
)
bands_df = spark.read.json(str(DATA / "bands" / "bands.json"), schema=bands_schema)

join_condition = guitar_players_df["band"] == bands_df["id"]

guitarist_df = guitar_players_df.join(bands_df, join_condition, "inner")

guitarist_df.explain()

"""
== Physical Plan ==
*(2) BroadcastHashJoin [cast(band#11 as int)], [id#16], Inner, BuildLeft, false
:- BroadcastExchange HashedRelationBroadcastMode(List(cast(cast(input[3, string, false] as int) as bigint)),false), [plan_id=25]
:  +- *(1) Filter isnotnull(band#11)
:     +- FileScan json [id#8,name#9,guitars#10,band#11] Batched: false, DataFilters: [isnotnull(band#11)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/guitarPlay..., PartitionFilters: [], PushedFilters: [IsNotNull(band)], ReadSchema: struct<id:int,name:string,guitars:array<string>,band:string>
+- *(2) Filter isnotnull(id#16)
   +- FileScan json [id#16,name#17,hometown#18,year#19] Batched: false, DataFilters: [isnotnull(id#16)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/bands/band..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:int,name:string,hometown:string,year:int>

"""

### guitarists with no band
guitarist_no_band = guitar_players_df.join(bands_df, join_condition, "left_anti")

guitarist_no_band.explain()
"""
== Physical Plan ==
*(2) BroadcastHashJoin [cast(band#11 as int)], [id#16], LeftAnti, BuildRight, false
:- FileScan json [id#8,name#9,guitars#10,band#11] Batched: false, DataFilters: [], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/guitarPlay..., PartitionFilters: [], PushedFilters: [], ReadSchema: struct<id:int,name:string,guitars:array<string>,band:string>
+- BroadcastExchange HashedRelationBroadcastMode(List(cast(input[0, int, false] as bigint)),false), [plan_id=59]
   +- *(1) Filter isnotnull(id#16)
      +- FileScan json [id#16] Batched: false, DataFilters: [isnotnull(id#16)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/bands/band..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:int>
====>>>> see the FileScan json only id here the previous one is FileScan json id, name, hometown, yean ...
====>>>> usefull for join and groups for large df
"""

## project and filter pushdown
names_df = guitarist_df.select(guitar_players_df["name"], bands_df["name"])
names_df.explain()
names_df.show()

"""
== Physical Plan ==
*(2) Project [name#9, name#17]
+- *(2) BroadcastHashJoin [cast(band#11 as int)], [id#16], Inner, BuildRight, false
   :- *(2) Filter isnotnull(band#11)
   :  +- FileScan json [name#9,band#11] Batched: false, DataFilters: [isnotnull(band#11)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/guitarPlay..., PartitionFilters: [], PushedFilters: [IsNotNull(band)], ReadSchema: struct<name:string,band:string>
   +- BroadcastExchange HashedRelationBroadcastMode(List(cast(input[0, int, false] as bigint)),false), [plan_id=102]
      +- *(1) Filter isnotnull(id#16)
         +- FileScan json [id#16,name#17] Batched: false, DataFilters: [isnotnull(id#16)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/bands/band..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:int,name:string>

=====>>>>> sparks tends to drop columns as early as possible
should be your goal as well 
"""
from pyspark.sql.functions import array_contains

##
rock_df = guitar_players_df.join(bands_df, join_condition).join(
    guitars_df,
    array_contains(
        guitar_players_df["guitars"],
        guitars_df["id"],
    ),
)
rock_df.explain()
"""
== Physical Plan ==
*(3) BroadcastNestedLoopJoin BuildRight, Inner, array_contains(guitars#10, id#0)
:- *(3) BroadcastHashJoin [cast(band#11 as int)], [id#16], Inner, BuildLeft, false
:  :- BroadcastExchange HashedRelationBroadcastMode(List(cast(cast(input[3, string, false] as int) as bigint)),false), [plan_id=204]
:  :  +- *(1) Filter (isnotnull(band#11) AND isnotnull(guitars#10))
:  :     +- FileScan json [id#8,name#9,guitars#10,band#11] Batched: false, DataFilters: [isnotnull(band#11), isnotnull(guitars#10)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/guitarPlay..., PartitionFilters: [], PushedFilters: [IsNotNull(band), IsNotNull(guitars)], ReadSchema: struct<id:int,name:string,guitars:array<int>,band:string>
:  +- *(3) Filter isnotnull(id#16)
:     +- FileScan json [id#16,name#17,hometown#18,year#19] Batched: false, DataFilters: [isnotnull(id#16)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/bands/band..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:int,name:string,hometown:string,year:int>
+- BroadcastExchange IdentityBroadcastMode, [plan_id=212]
   +- *(2) Filter isnotnull(id#0)
      +- FileScan json [id#0,model#1,make#2,guitarType#3] Batched: false, DataFilters: [isnotnull(id#0)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/guitars/gu..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:int,model:string,make:string,guitarType:string>

"""

from pyspark.sql.functions import upper

essentials_df = rock_df.select(
    guitar_players_df["name"],
    bands_df["name"],
    upper(guitars_df["make"]),
)
essentials_df.explain()
"""
== Physical Plan ==
*(3) Project [name#9, name#17, upper(make#2) AS upper(make)#106]
+- *(3) BroadcastNestedLoopJoin BuildRight, Inner, array_contains(guitars#10, id#0)
   :- *(3) Project [name#9, guitars#10, name#17]
   :  +- *(3) BroadcastHashJoin [cast(band#11 as int)], [id#16], Inner, BuildRight, false
   :     :- *(3) Filter (isnotnull(band#11) AND isnotnull(guitars#10))
   :     :  +- FileScan json [name#9,guitars#10,band#11] Batched: false, DataFilters: [isnotnull(band#11), isnotnull(guitars#10)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/guitarPlay..., PartitionFilters: [], PushedFilters: [IsNotNull(band), IsNotNull(guitars)], ReadSchema: struct<name:string,guitars:array<int>,band:string>
   :     +- BroadcastExchange HashedRelationBroadcastMode(List(cast(input[0, int, false] as bigint)),false), [plan_id=283]
   :        +- *(1) Filter isnotnull(id#16)
   :           +- FileScan json [id#16,name#17] Batched: false, DataFilters: [isnotnull(id#16)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/bands/band..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:int,name:string>
   +- BroadcastExchange IdentityBroadcastMode, [plan_id=290]
      +- *(2) Filter isnotnull(id#0)
         +- FileScan json [id#0,make#2] Batched: false, DataFilters: [isnotnull(id#0)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/guitars/gu..., PartitionFilters: [], PushedFilters: [IsNotNull(id)], ReadSchema: struct<id:int,make:string>

"""
## spark is doing column pruning
## upper function is done last by spark
## but we can optimize it in the way that if we know that the guitars dataframe is smaller, so we can perform the upper function before the join
## in contrary if the result is smaller, it is ok to do it at the end, final goal is to minimize the amount of data that is processed


## if you do a select after a join, the project operation is pushed as down as possible to the joined dataframes (refer to the physical plan at the bottom, spark already selects only the required columns)

if __name__ == "__main__":
    time.sleep(1000)
