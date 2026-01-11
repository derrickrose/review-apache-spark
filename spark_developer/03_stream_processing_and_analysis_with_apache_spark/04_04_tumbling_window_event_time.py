# timestamp from unix convert to normal timestamp spark ???
# running total when we didnt perform any windowing not that useful
# there comes the windowing, we define a window off the timestamp inside the data
## useful for aggregation and analysis over time intervals, e.g. count
## number of orders placed within a one minute interval window
## in memory sink then we query the memory, note it is in complete outputmode
## counting number of orders placed within a one minute interval window in a complete outputmode

## sliding window
## is used for fraud detection for example

## streaming joins
## correlation of events
## enrichment

## stream stream processing join

## late arriving data

## ce quon va faire c'est lire le stream et perform running total achat

# data comming on the directories input_advanced_order and input_advanced_order_status

# {"event_type":"ORDER_STATUS","order_id":"order_10","status":"DELIVERED","event_time":"2025-01-10T15:00:00Z"}
# {"event_type":"ORDER_CREATED","order_id":"order_9","user_id":"u9","amount":75.25,"event_time":"2025-01-10T10:40:00Z"}

# count order by event time 1 minute window and group by window


from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    FloatType,
    TimestampType,
)
from pyspark.sql.functions import window, col, count

spark = SparkSession.builder.appName("tumbling_one_minute_window").getOrCreate()

order_schema = StructType(
    [
        StructField("event_type", StringType()),
        StructField("order_id", StringType()),
        StructField("user_id", StringType()),
        StructField("amount", FloatType()),
        StructField("event_time", TimestampType()),
    ]
)

order_stream_df = (
    spark.readStream.format("json").schema(order_schema).load("input_advanced_order")
)

order_per_minute_df = order_stream_df.groupBy(
    window(timeColumn=col("event_time"), windowDuration="1 minute")
).agg(count("*").alias("orders_per_minute"))

order_per_minute_updated = (
    order_per_minute_df.withColumn("start", col("window.start"))
    .withColumn("end", col("window.end"))
    .drop(col("window"))
)

order_per_minute = (
    order_per_minute_updated.writeStream.format("memory")
    .outputMode("complete")
    .queryName("order_per_minute")
    .start()
)

index = 0
while True:
    import time
    time.sleep(30)
    print(f"==============={index}=================")
    spark.sql("SELECT * from order_per_minute").show()
    index += 1