# spark with delta lake demo read

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, IntegerType, StructField


spark = (
    SparkSession.builder.appName("spark_with_delta_lake_read_parquet_demo")
    # .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0")  # .config(
    #     "spark.sql.extensions",
    #     "io.delta.sql.DeltaSparkSessionExtension"
    # )
    # .config(
    #     "spark.sql.catalog.spark_catalog",
    #     "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    # )
    .getOrCreate()
)

# spark.sparkContext.setLogLevel("DEBUG")

schema = StructType(
    [
        StructField("id", IntegerType()),
        StructField("name", StringType()),
        StructField("age", IntegerType()),
        StructField("gender", StringType()),
    ]
)

df = spark.read.format("parquet").option("inferSchema", "true").load("output_partition")
print(df.rdd.getNumPartitions())
df.printSchema()

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
