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

# count order by processing time 1 minute window and group by window

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    FloatType,
    TimestampType,
)
from pyspark.sql.functions import window, count, current_timestamp


spark = SparkSession.builder.appName("tumbling_window").getOrCreate()

order_schema = StructType(
    [
        StructField("event_type", StringType()),
        StructField("order_id", StringType()),
        StructField("user_id", StringType()),
        StructField("amount", FloatType()),
        StructField("event_time", TimestampType()),
    ]
)

order_streaming_df = (
    spark.readStream.format("json").schema(order_schema).load("input_advanced_order")
)

one_minute_windowed_order_count = order_streaming_df.groupBy(
    window(current_timestamp(), windowDuration="1 minute")
).agg(count("*").alias("orders_per_window"))

one_minute_windowed_order_count_query = (
    one_minute_windowed_order_count.writeStream.format("console")
    .outputMode("update")
    .start()
)

one_minute_windowed_order_count_query.awaitTermination()
