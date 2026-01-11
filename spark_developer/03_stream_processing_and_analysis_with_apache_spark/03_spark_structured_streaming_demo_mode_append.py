# demo streaming
from typing import Optional

## stream reading from file check 02_spark_structured_streaming.py

## start a query

## basic transformations

## filter the stream

## using the stop method of the stream just to ensure that we dont have any queries running with this name (queryName)
## because we are going to create a new one with the same name but this time sink is in memory

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

schema = StructType(
    [
        StructField("id", IntegerType()),
        StructField("name", StringType()),
        StructField("age", IntegerType()),
        StructField("gender", StringType()),
        StructField("city", StringType()),
    ]
)

spark = SparkSession.builder.appName("structured_streaming").getOrCreate()

streaming_df = spark.readStream.schema(
    "name STRING, id int, age INT, city STRING, gender STRING"
).json("input")

print(streaming_df.isStreaming)

cleaned_df = streaming_df.select("id", "name", "age", "gender")

memory_query = (
    cleaned_df.writeStream.format("memory")
    .queryName("query")
    .outputMode("append")
    .start()
)

while spark.streams.active:
    import time

    time.sleep(5)
    ## this is showing duplicated rows
    spark.sql("select * from query where gender = 'male'").show()
