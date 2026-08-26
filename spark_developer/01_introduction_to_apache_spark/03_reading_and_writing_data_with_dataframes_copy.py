# reading data with pyspark
## from csv
# https://github.com/MangoTheCat/Modelling-Airbnb-Prices/blob/master/listings.csv.gz
from pyspark.sql import SparkSession

# spark = SparkSession.builder.appName("reading_data_with_dataframes").getOrCreate()
# df = spark.read.csv("listings.csv.gz", header="true", inferSchema="true", multiLine="true", escape='"')

spark = (
    SparkSession.builder.appName("reading_data_with_dataframes")
    # .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.0")
    # .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    # .config("spark.sql.catalog.spark_catalog",
    #         "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.sql.shuffle.partitions","10")
    .getOrCreate()
)

listings_df = (
    spark.read.format("csv")
    .option("header", "true")
    # .option("inferSchema", "true")
    # .option("multiLine", "true")
    .option("escape", '"')
    .option("quote", '"')
    .option("delimiter", ",")
    .load("../data/")
    # .load("../data/listings.csv.gz", header="true", inferSchema="true", escape='"')
)

# print schema of the dataframe
## note, if no header so no schema then default _C0, _C1, ...
listings_df.printSchema()
print(listings_df.rdd.getNumPartitions())
listings_df.write.format("parquet").mode("overwrite").save("write_data/listings_parquet")
# listings_df2 = listings_df.repartition(10)
# listings_df2 = listings_df
# print(listings_df2.rdd.getNumPartitions())

import time

time.sleep(15 * 60)
