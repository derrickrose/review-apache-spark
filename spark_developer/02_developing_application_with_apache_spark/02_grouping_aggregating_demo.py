from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, round, count, desc, sum

spark = SparkSession.builder.appName("02_grouping_aggregating_demo").getOrCreate()
trips_df = spark.read.format("parquet").load("nyc_yellow_tripdata_2025_01.parquet")
trips_df.show(10)
## which vendor's taxi had the most trip
#### version courte
# total_trips_df = trips_df.groupBy("VendorID").count().orderBy(desc("count"))
# total_trips_df.show(10)

#### version longue
total_trips_df = (
    trips_df.groupBy("VendorID")
    .agg(
        count("*").alias("total_trip"),
        round(avg("fare_amount"), 2).alias("avg_fare"),
        round(avg("trip_distance"), 2).alias("avg_distance"),
        round(sum("fare_amount"), 2).alias("total_fare"),
    )
    .withColumnRenamed("VendorID", "vendor_id")
    .orderBy(desc("total_trip"))
)

total_trips_df.show(10)

## window functions
## using groupBy, we loose the details, but with window functions we can keep them
from pyspark.sql.window import Window
from pyspark.sql.functions import rank

# partitionBy will isolate by vendor_id, but the vendor_id appear once so the rank will be 1 for all
# window_spec = Window.partitionBy("vendor_id").orderBy("total_trip")
# made_trips_ranking_df = total_trips_df.withColumn(
#     "rank", rank().over(window_spec)
# ).orderBy(desc("rank"))
# made_trips_ranking_df.show(10)

# to fix that, not partition but global ranking using just orderBy
from pyspark.sql.window import Window
from pyspark.sql.functions import asc, desc, rank

total_trip_window = Window.orderBy(desc("total_trip"))
average_distance_window = Window.orderBy(desc("avg_distance"))
total_fare_window = Window.orderBy(desc("total_fare"))
ranking_df = total_trips_df.withColumns(
    {
        "total_fare_ranking": rank().over(total_fare_window),
        "avg_distance_ranking": rank().over(average_distance_window),
        "total_trip_ranking": rank().over(total_trip_window),
    }
).orderBy(asc("avg_distance_ranking"))
ranking_df.show(10)

# TODO to check method ntile() with window functions groups of n (5) for example
## TODO group, agg then rank in one line ?? is it possible ???
## TODO in python str + int => TypeError, in pyspark ?????? to check
