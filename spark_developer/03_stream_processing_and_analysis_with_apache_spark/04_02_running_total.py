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

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    FloatType,
    TimestampType,
)

# {"event_type":"ORDER_CREATED","order_id":"order_7","user_id":"u7","amount":129.00,"event_time":"2025-01-10T10:30:00Z"}
# {"event_type":"ORDER_STATUS","order_id":"order_10","status":"SHIPPED","event_time":"2025-01-10T12:50:00Z"}
spark = SparkSession.builder.appName(
    "advanced_stream_processing_running_total"
).getOrCreate()
order_schema = StructType(
    [
        StructField("event_type", StringType()),
        StructField("order_id", StringType()),
        StructField("status", StringType()),
        StructField("event_time", TimestampType()),
    ]
)
order_stream_df = (
    spark.readStream.schema(order_schema)
    .format("json")
    .load("input_advanced_order_status")
)

order_stream_df.printSchema()
print(order_stream_df.isStreaming)

# running_total_stream_df = order_stream_df.groupBy("status").count().withColumnRenamed("count", "running_total").orderBy(col("running_total").desc())
running_total_stream_df = (
    order_stream_df.groupBy("status")
    .agg(count("*").alias("running_total"))
    .orderBy(col("running_total").desc())
)

order_queries = (
    order_stream_df.writeStream.format("console")
    .outputMode("append")
    .queryName("order_queries")
    .start()
)

running_total_queries = (
    running_total_stream_df.writeStream.format("memory")
    .outputMode("complete")
    .queryName("running_total_queries")
    .start()
)


while spark.streams.active:
    import time

    time.sleep(5)
    print("--------------------------------------")
    spark.sql("SELECT * FROM running_total_queries").show()
