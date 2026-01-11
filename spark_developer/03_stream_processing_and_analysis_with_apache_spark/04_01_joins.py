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
from pyspark.sql.functions import sum, round
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    FloatType,
    TimestampType,
)

# {"event_type":"ORDER_CREATED","order_id":"order_7","user_id":"u7","amount":129.00,"event_time":"2025-01-10T10:30:00Z"}
# {"event_type":"ORDER_STATUS","order_id":"order_4","status":"SHIPPED","event_time":"2025-01-10T11:40:00Z"}
# {"user_id":"u1","first_name":"Jean","last_name":"Dupont","phone":"+33 6 12 34 56 01","street_address":"12 rue de Rivoli","zip_code":"75001","city":"Paris","country":"FR"}

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    FloatType,
    TimestampType,
)
from pyspark.sql.functions import col

spark = SparkSession.builder.appName("advanced_streaming_joins").getOrCreate()

order_schema = StructType(
    [
        StructField("event_type", StringType()),
        StructField("order_id", StringType()),
        StructField("user_id", StringType()),
        StructField("amount", FloatType()),
        StructField("event_time", TimestampType()),
    ]
)

status_schema = StructType(
    [
        StructField("event_type", StringType()),
        StructField("order_id", StringType()),
        StructField("status", StringType()),
        StructField("event_time", TimestampType()),
    ]
)

user_schema = StructType(
    [
        StructField("user_id", StringType()),
        StructField("first_name", StringType()),
        StructField("last_name", StringType()),
        StructField("phone", StringType()),
        StructField("street_address", StringType()),
        StructField("zip_code", StringType()),
        StructField("city", StringType()),
        StructField("country", StringType()),
    ]
)

order_stream_df = (
    spark.readStream.schema(order_schema)
    .format("json")
    .option("path", "input_advanced_order")
    .load()
    .select("user_id", "amount", col("event_time").alias("order_time"), "order_id")
)
print("order_stream_df.isStreaming", order_stream_df.isStreaming)
order_stream_df.printSchema()

status_stream_df = (
    spark.readStream.schema(status_schema)
    .format("json")
    .option("path", "input_advanced_order_status")
    .load()
    .select("order_id", "status", col("event_time").alias("status_time"))
)
print("status_stream_df.isStreaming", status_stream_df.isStreaming)
status_stream_df.printSchema()

user_df = (
    spark.read.schema(user_schema)
    .json("user_details.json")
    .select("first_name", "last_name", "zip_code", "city", "country", "user_id")
)
print("user_df.isStreaming", user_df.isStreaming)
user_df.printSchema()

joined_df = order_stream_df.join(status_stream_df, "order_id").join(user_df, "user_id")
print("joined_df.isStreaming", joined_df.isStreaming)
joined_df.printSchema()

order_query = (
    order_stream_df.writeStream.format("memory").queryName("order_query").start()
)
status_query = (
    status_stream_df.writeStream.format("memory").queryName("status_query").start()
)

joined_query = (
    joined_df.writeStream.format("memory")
    .outputMode("append")
    .queryName("joined_query")
    .start()
)

# joined_query.awaitTermination()
while True:
    # while spark.streams.active:
    import time

    time.sleep(5)
    print("================== order ==============================")
    spark.sql("SELECT * FROM order_query").show()
    print("------------------ status ------------------------------")
    spark.sql("SELECT * FROM status_query").show()
    print("------------------ joined ------------------------------")
    spark.sql("SELECT * FROM joined_query").show()
