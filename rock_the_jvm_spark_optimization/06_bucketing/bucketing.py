from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = (
    SparkSession.builder
    .appName("Bucketing")
    .master("local")
    .getOrCreate()
)

# deactivate broadcasting
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)

large = spark.range(1000000).selectExpr("id * 5 as id").repartition(10)
small = spark.range(10000).selectExpr("id * 3 as id").repartition(3)

joined = large.join(small, "id")
joined.explain()

# TODO: add query plan

# bucketing
(
    large.write
    .bucketBy(4, "id")
    .sortBy("id")
    .mode("overwrite")
    .saveAsTable("bucketed_large")
)

(
    small.write
    .bucketBy(4, "id")
    .sortBy("id")
    .mode("overwrite")
    .saveAsTable("bucketed_small")  # bucketing and saving almost as expensive as a regular shuffle
)

spark.sql("use default")
bucketed_large = spark.table("bucketed_large")
bucketed_small = spark.table("bucketed_small")
bucketed_join = bucketed_large.join(bucketed_small, "id")
bucketed_join.explain()

# TODO: add query plan

# bucketing for groups
flights_df = (
    spark.read
    .json("../data/flights/flights.json")
    .repartition(2)
)

most_delayed = (
    flights_df
    .filter("origin = 'DEN' and arrdelay > 1")
    .groupBy("origin", "dest", "carrier")
    .avg("arrdelay")
    .orderBy(col("avg(arrdelay)").desc_nulls_last())
)
most_delayed.explain()

# TODO: add query plan

# (
#     flights_df.write
#     .partitionBy("origin")
#     .bucketBy(4, "dest", "carrier")
#     .saveAsTable("flights_bucketed")  # just as long as a shuffle
# )
#
# flights_bucketed = spark.table("flights_bucketed")
# most_delayed2 = (
#     flights_bucketed
#     .filter("origin = 'DEN' and arrdelay > 1")
#     .groupBy("origin", "dest", "carrier")
#     .avg("arrdelay")
#     .orderBy(col("avg(arrdelay)").desc_nulls_last())
# )
# most_delayed2.explain()

# TODO: add query plan

"""
Bucket pruning
"""
the10 = bucketed_large.filter(col("id") == 10)
the10.show()
the10.explain()

# TODO: add query plan

# joined.count()         # 4-5s
# bucketed_join.count()  # 4s for bucketing + 0.5s for counting
# most_delayed.show()    # ~1s
# most_delayed2.show()   # ~0.2s = 5x perf!