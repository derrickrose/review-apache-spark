# Spark with Delta Lake Demo write
# default for delta is COW (copy on write)
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, IntegerType, StructField
from pyspark.sql.functions import col

INPUT = "input"
OUTPUT = "output_partition"

spark = (
    SparkSession.builder.appName("spark_with_delta_lake_demo")
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0")  # .config(
    #     "spark.sql.extensions",
    #     "io.delta.sql.DeltaSparkSessionExtension"
    # )
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )
    .config("spark.sql.parquet.compression.codec", "zstd")
    .getOrCreate()
)
schema = StructType(
    [
        StructField("id", IntegerType()),
        StructField("name", StringType()),
        StructField("age", IntegerType()),
        StructField("gender", StringType()),
    ]
)
df = spark.read.format("json").schema(schema).load(INPUT).orderBy("id").repartition(20).filter(col("gender") == "male")
print(df.rdd.getNumPartitions())
df.write.format("delta").mode("overwrite").partitionBy("gender").save(OUTPUT)
