from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
FLIGHTS_PATH = DATA_DIR / "flights"
FLIGHTS_PARQUET_PATH = DATA_DIR / "flights_parquet"

spark = SparkSession.builder.appName("Catalyst Demo").master("local").getOrCreate()
spark.sparkContext.setLogLevel("DEBUG")

flights = spark.read.option("inferSchema", "true").json(str(FLIGHTS_PATH))

# Catalyst plays nice with chained filters
not_from_here = (
    flights.where(col("origin") != "LGA")
    .where(col("origin") != "ORD")
    .where(col("origin") != "SFO")
    .where(col("origin") != "DEN")
    .where(col("origin") != "BOS")
    .where(col("origin") != "EWR")
)

not_from_here.explain(True)

"""
== Parsed Logical Plan ==
'Filter '`!`('`=`('origin, EWR))
+- Filter NOT (origin#17 = BOS)
   +- Filter NOT (origin#17 = DEN)
      +- Filter NOT (origin#17 = SFO)
         +- Filter NOT (origin#17 = ORD)
            +- Filter NOT (origin#17 = LGA)
               +- Relation [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] json

== Analyzed Logical Plan ==
_id: string, arrdelay: double, carrier: string, crsarrtime: bigint, crsdephour: bigint, crsdeptime: bigint, crselapsedtime: double, depdelay: double, dest: string, dist: double, dofW: bigint, origin: string
Filter NOT (origin#17 = EWR)
+- Filter NOT (origin#17 = BOS)
   +- Filter NOT (origin#17 = DEN)
      +- Filter NOT (origin#17 = SFO)
         +- Filter NOT (origin#17 = ORD)
            +- Filter NOT (origin#17 = LGA)
               +- Relation [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] json

== Optimized Logical Plan ==
Filter (isnotnull(origin#17) AND ((NOT (origin#17 = LGA) AND NOT (origin#17 = ORD)) AND (((NOT (origin#17 = SFO) AND NOT (origin#17 = DEN)) AND NOT (origin#17 = BOS)) AND NOT (origin#17 = EWR))))
+- Relation [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] json

== Physical Plan ==
*(1) Filter ((((((isnotnull(origin#17) AND NOT (origin#17 = LGA)) AND NOT (origin#17 = ORD)) AND NOT (origin#17 = SFO)) AND NOT (origin#17 = DEN)) AND NOT (origin#17 = BOS)) AND NOT (origin#17 = EWR))
+- FileScan json [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] Batched: false, DataFilters: [isnotnull(origin#17), NOT (origin#17 = LGA), NOT (origin#17 = ORD), NOT (origin#17 = SFO), NOT (..., Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/flights], PartitionFilters: [], PushedFilters: [IsNotNull(origin), Not(EqualTo(origin,LGA)), Not(EqualTo(origin,ORD)), Not(EqualTo(origin,SFO)),..., ReadSchema: struct<_id:string,arrdelay:double,carrier:string,crsarrtime:bigint,crsdephour:bigint,crsdeptime:b...


"""


# sometimes we do something redundant, out of ignorance or lack of communication with the rest of our team
def filter_team1(flights: DataFrame) -> DataFrame:
    return flights.where(col("origin") != "LGA").where(col("dest") == "DEN")


def filter_team2(flights: DataFrame) -> DataFrame:
    return flights.where(col("origin") != "EWR").where(col("dest") == "DEN")


filter_both = filter_team1(filter_team2(flights))
filter_both.explain(True)

"""
== Parsed Logical Plan ==
'Filter '`=`('dest, DEN)
+- Filter NOT (origin#17 = LGA)
   +- Filter (dest#14 = DEN)
      +- Filter NOT (origin#17 = EWR)
         +- Relation [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] json

== Analyzed Logical Plan ==
_id: string, arrdelay: double, carrier: string, crsarrtime: bigint, crsdephour: bigint, crsdeptime: bigint, crselapsedtime: double, depdelay: double, dest: string, dist: double, dofW: bigint, origin: string
Filter (dest#14 = DEN)
+- Filter NOT (origin#17 = LGA)
   +- Filter (dest#14 = DEN)
      +- Filter NOT (origin#17 = EWR)
         +- Relation [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] json

== Optimized Logical Plan ==
Filter ((isnotnull(origin#17) AND isnotnull(dest#14)) AND ((NOT (origin#17 = EWR) AND (dest#14 = DEN)) AND NOT (origin#17 = LGA)))
+- Relation [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] json

== Physical Plan ==
*(1) Filter ((((isnotnull(origin#17) AND isnotnull(dest#14)) AND NOT (origin#17 = EWR)) AND (dest#14 = DEN)) AND NOT (origin#17 = LGA))
+- FileScan json [_id#6,arrdelay#7,carrier#8,crsarrtime#9L,crsdephour#10L,crsdeptime#11L,crselapsedtime#12,depdelay#13,dest#14,dist#15,dofW#16L,origin#17] Batched: false, DataFilters: [isnotnull(origin#17), isnotnull(dest#14), NOT (origin#17 = EWR), (dest#14 = DEN), NOT (origin#17..., Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/flights], PartitionFilters: [], PushedFilters: [IsNotNull(origin), IsNotNull(dest), Not(EqualTo(origin,EWR)), EqualTo(dest,DEN), Not(EqualTo(ori..., ReadSchema: struct<_id:string,arrdelay:double,carrier:string,crsarrtime:bigint,crsdephour:bigint,crsdeptime:b...


"""

# UPDATE - Spark 4 Catalyst has improved multi-key dynamic partition pruning (DPP)
# and multi-layer runtime filters. More filters are pushed down at multiple query plan layers.
# duplication on filters will be appearing only once thanks to catalyst
# pushing down filters all the way to the data source - do not read records in the first place
flights.write.format("parquet").mode("overwrite").save("catalyst/")

not_from_lga = (
    spark.read.format("parquet").load("catalyst/").where(col("origin") != "LGA")
)

not_from_lga.explain()
"""
== Physical Plan ==
*(1) Filter (isnotnull(origin#42) AND NOT (origin#42 = LGA))
+- *(1) ColumnarToRow
   +- FileScan parquet [_id#31,arrdelay#32,carrier#33,crsarrtime#34L,crsdephour#35L,crsdeptime#36L,crselapsedtime#37,depdelay#38,dest#39,dist#40,dofW#41L,origin#42] Batched: true, DataFilters: [isnotnull(origin#42), NOT (origin#42 = LGA)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/perf_tuning_spa..., PartitionFilters: [], PushedFilters: [IsNotNull(origin), Not(EqualTo(origin,LGA))], ReadSchema: struct<_id:string,arrdelay:double,carrier:string,crsarrtime:bigint,crsdephour:bigint,crsdeptime:b...

=>> pushed filters PushedFilters: [IsNotNull(origin), Not(EqualTo(origin,LGA))] 
==> also found on the debug mode 
"""
