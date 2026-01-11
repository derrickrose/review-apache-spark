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

# streaming_df = (
#     spark.readStream.schema("name STRING, id int, age INT, city STRING, gender STRING")
#     .option("maxFilesPerTrigger", 1)
#     .json("input")
# )

# same results as the previous
streaming_df = spark.readStream.schema(schema).json("input")

print(streaming_df.isStreaming)

cleaned_df = streaming_df.select("id", "name", "age", "gender")

from pyspark.sql.functions import col, current_timestamp

## this is a stream too since the input is a stream and there were no aggregation
is_adult_df = cleaned_df.withColumn("is_adult", col("age") > 18)

## filter is a stateless operation
## men are male > 18
men_df = is_adult_df.filter("gender = 'male' AND is_adult = true")

boys_df = is_adult_df.filter((col("gender") == "male") & (col("age") < 18))

male_df = men_df.union(boys_df)

# men_query = (
#     men_df.writeStream.format("memory")
#     .queryName("men_query")
#     .outputMode("append")
#     .start()
# )

# boys_query = (
#     boys_df.writeStream.format("memory")
#     .queryName("boys_query")
#     .outputMode("append")
#     .start()
# )

male_df = (
    male_df.withColumn("processing_time", current_timestamp())
    .writeStream.format("console")
    .trigger(processingTime="1 minutes")
    .queryName("male_query")
    .outputMode("append")
    .start()
)

# to stop all queries
## we can also filter by queryName so just the specific one will be stopped
## something like if q.name == 'men_query': =+> proceed to stopping it
# for q in spark.streams.active:
#     q.stop()

# while spark.streams.active:
#     import time
#
#     time.sleep(5)
#     ## this is showing duplicated rows
#     print("-------------------------men")
#     spark.sql("select * from men_query").show(1000)
#     print("-------------------------boys")
#     spark.sql("select * from boys_query").show(1000)

male_df.awaitTermination()
