# spark with delta lake demo read

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("spark_with_delta_lake_read_table_demo")
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0")  # .config(
    #     "spark.sql.extensions",
    #     "io.delta.sql.DeltaSparkSessionExtension"
    # )
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )
    .getOrCreate()
)

df = spark.read.format("delta").load("output")
print(df.rdd.getNumPartitions())
print(df.count())
import time

time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)

print(df.count())
time.sleep(5)
