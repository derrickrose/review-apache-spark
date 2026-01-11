# reading data with pyspark
## from csv
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("reading_data_with_dataframes").getOrCreate()
# df = spark.read.csv("listings.csv.gz", header="true", inferSchema="true", multiLine="true", escape='"')
df = (
    spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .load("listings.csv.gz", header="true", inferSchema="true", escape='"')
)

# print schema of the dataframe
## note, if no header so no schema then default _C0, _C1, ...
df.printSchema()
"""
root
 |-- id: long (nullable = true)
 |-- listing_url: string (nullable = true)
 |-- scrape_id: long (nullable = true)
 |-- last_scraped: date (nullable = true)
 |-- source: string (nullable = true)
 |-- name: string (nullable = true)
 |-- description: string (nullable = true)
 |-- neighborhood_overview: string (nullable = true)
 |-- picture_url: string (nullable = true)
 |-- host_id: integer (nullable = true)
 |-- host_url: string (nullable = true)
 |-- host_name: string (nullable = true)
 |-- host_since: date (nullable = true)
 |-- host_location: string (nullable = true)
 |-- host_about: string (nullable = true)
 |-- host_response_time: string (nullable = true)
 |-- host_response_rate: string (nullable = true)
 |-- host_acceptance_rate: string (nullable = true)
 |-- host_is_superhost: string (nullable = true)
 |-- host_thumbnail_url: string (nullable = true)
 |-- host_picture_url: string (nullable = true)
 |-- host_neighbourhood: string (nullable = true)
 |-- host_listings_count: integer (nullable = true)
 |-- host_total_listings_count: integer (nullable = true)
 |-- host_verifications: string (nullable = true)
 |-- host_has_profile_pic: string (nullable = true)
 |-- host_identity_verified: string (nullable = true)
 |-- neighbourhood: string (nullable = true)
 |-- neighbourhood_cleansed: string (nullable = true)
 |-- neighbourhood_group_cleansed: string (nullable = true)
 |-- latitude: double (nullable = true)
 |-- longitude: double (nullable = true)
 |-- property_type: string (nullable = true)
 |-- room_type: string (nullable = true)
 |-- accommodates: integer (nullable = true)
 |-- bathrooms: double (nullable = true)
 |-- bathrooms_text: string (nullable = true)
 |-- bedrooms: integer (nullable = true)
 |-- beds: integer (nullable = true)
 |-- amenities: string (nullable = true)
 |-- price: string (nullable = true)
 |-- minimum_nights: integer (nullable = true)
 |-- maximum_nights: integer (nullable = true)
 |-- minimum_minimum_nights: integer (nullable = true)
 |-- maximum_minimum_nights: integer (nullable = true)
 |-- minimum_maximum_nights: integer (nullable = true)
 |-- maximum_maximum_nights: integer (nullable = true)
 |-- minimum_nights_avg_ntm: double (nullable = true)
 |-- maximum_nights_avg_ntm: double (nullable = true)
 |-- calendar_updated: string (nullable = true)
 |-- has_availability: string (nullable = true)
 |-- availability_30: integer (nullable = true)
 |-- availability_60: integer (nullable = true)
 |-- availability_90: integer (nullable = true)
 |-- availability_365: integer (nullable = true)
 |-- calendar_last_scraped: date (nullable = true)
 |-- number_of_reviews: integer (nullable = true)
 |-- number_of_reviews_ltm: integer (nullable = true)
 |-- number_of_reviews_l30d: integer (nullable = true)
 |-- availability_eoy: integer (nullable = true)
 |-- number_of_reviews_ly: integer (nullable = true)
 |-- estimated_occupancy_l365d: integer (nullable = true)
 |-- estimated_revenue_l365d: integer (nullable = true)
 |-- first_review: date (nullable = true)
 |-- last_review: date (nullable = true)
 |-- review_scores_rating: double (nullable = true)
 |-- review_scores_accuracy: double (nullable = true)
 |-- review_scores_cleanliness: double (nullable = true)
 |-- review_scores_checkin: double (nullable = true)
 |-- review_scores_communication: double (nullable = true)
 |-- review_scores_location: double (nullable = true)
 |-- review_scores_value: double (nullable = true)
 |-- license: string (nullable = true)
 |-- instant_bookable: string (nullable = true)
 |-- calculated_host_listings_count: integer (nullable = true)
 |-- calculated_host_listings_count_entire_homes: integer (nullable = true)
 |-- calculated_host_listings_count_private_rooms: integer (nullable = true)
 |-- calculated_host_listings_count_shared_rooms: integer (nullable = true)
 |-- reviews_per_month: double (nullable = true)

"""

## we can also use the schema attribute of the dataframe
print(df.schema)
"""
StructType([StructField('id', StringType(), True), StructField('listing_url', StringType(), True), StructField('scrape_id', StringType(), True), StructField('last_scraped', StringType(), True), StructField('source', StringType(), True), StructField('name', StringType(), True), StructField('description', StringType(), True), StructField('neighborhood_overview', StringType(), True), StructField('picture_url', StringType(), True), StructField('host_id', StringType(), True), StructField('host_url', StringType(), True), StructField('host_name', StringType(), True), StructField('host_since', StringType(), True), StructField('host_location', StringType(), True), StructField('host_about', StringType(), True), StructField('host_response_time', StringType(), True), StructField('host_response_rate', StringType(), True), StructField('host_acceptance_rate', StringType(), True), StructField('host_is_superhost', StringType(), True), StructField('host_thumbnail_url', StringType(), True), StructField('host_picture_url', StringType(), True), StructField('host_neighbourhood', StringType(), True), StructField('host_listings_count', StringType(), True), StructField('host_total_listings_count', StringType(), True), StructField('host_verifications', StringType(), True), StructField('host_has_profile_pic', StringType(), True), StructField('host_identity_verified', StringType(), True), StructField('neighbourhood', StringType(), True), StructField('neighbourhood_cleansed', StringType(), True), StructField('neighbourhood_group_cleansed', StringType(), True), StructField('latitude', StringType(), True), StructField('longitude', StringType(), True), StructField('property_type', StringType(), True), StructField('room_type', StringType(), True), StructField('accommodates', StringType(), True), StructField('bathrooms', StringType(), True), StructField('bathrooms_text', StringType(), True), StructField('bedrooms', StringType(), True), StructField('beds', StringType(), True), StructField('amenities', StringType(), True), StructField('price', StringType(), True), StructField('minimum_nights', StringType(), True), StructField('maximum_nights', StringType(), True), StructField('minimum_minimum_nights', StringType(), True), StructField('maximum_minimum_nights', StringType(), True), StructField('minimum_maximum_nights', StringType(), True), StructField('maximum_maximum_nights', StringType(), True), StructField('minimum_nights_avg_ntm', StringType(), True), StructField('maximum_nights_avg_ntm', DoubleType(), True), StructField('calendar_updated', StringType(), True), StructField('has_availability', StringType(), True), StructField('availability_30', StringType(), True), StructField('availability_60', StringType(), True), StructField('availability_90', StringType(), True), StructField('availability_365', StringType(), True), StructField('calendar_last_scraped', StringType(), True), StructField('number_of_reviews', DoubleType(), True), StructField('number_of_reviews_ltm', DoubleType(), True), StructField('number_of_reviews_l30d', DoubleType(), True), StructField('availability_eoy', StringType(), True), StructField('number_of_reviews_ly', StringType(), True), StructField('estimated_occupancy_l365d', StringType(), True), StructField('estimated_revenue_l365d', StringType(), True), StructField('first_review', StringType(), True), StructField('last_review', StringType(), True), StructField('review_scores_rating', DoubleType(), True), StructField('review_scores_accuracy', DoubleType(), True), StructField('review_scores_cleanliness', DoubleType(), True), StructField('review_scores_checkin', DoubleType(), True), StructField('review_scores_communication', StringType(), True), StructField('review_scores_location', DoubleType(), True), StructField('review_scores_value', DoubleType(), True), StructField('license', IntegerType(), True), StructField('instant_bookable', StringType(), True), StructField('calculated_host_listings_count', IntegerType(), True), StructField('calculated_host_listings_count_entire_homes', IntegerType(), True), StructField('calculated_host_listings_count_private_rooms', IntegerType(), True), StructField('calculated_host_listings_count_shared_rooms', StringType(), True), StructField('reviews_per_month', StringType(), True)])
"""

## deplay() function is feature of databricks
## and data profiling

# explicitly defining the schema
## no nead to define all the schema
## and no need to infer the schema
## only used for text based file format like CSV and JSON, self describing tables no need (delta table or parquet)
## best practice since change of data my generate errors
## it is also worth mentioning that schema inferring does trigger a job and in the opposite the other way does not
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
)

schema = StructType(
    [
        StructField("id", StringType(), True),
        StructField("listing_url", StringType(), True),
        StructField("scrape_id", StringType(), True),
        StructField("last_scraped", StringType(), True),
        StructField("source", StringType(), True),
        StructField("name", StringType(), True),
        StructField("description", StringType(), True),
        StructField("neighborhood_overview", StringType(), True),
        StructField("picture_url", StringType(), True),
        StructField("host_id", StringType(), True),
        StructField("host_url", StringType(), True),
        StructField("host_name", StringType(), True),
        StructField("host_since", StringType(), True),
        StructField("host_location", StringType(), True),
        StructField("host_about", StringType(), True),
        StructField("host_response_time", StringType(), True),
        StructField("host_response_rate", StringType(), True),
        StructField("host_acceptance_rate", StringType(), True),
        StructField("host_is_superhost", StringType(), True),
        StructField("host_thumbnail_url", StringType(), True),
        StructField("host_picture_url", StringType(), True),
        StructField("host_neighbourhood", StringType(), True),
        StructField("host_listings_count", StringType(), True),
        StructField("host_total_listings_count", StringType(), True),
        StructField("host_verifications", StringType(), True),
        StructField("host_has_profile_pic", StringType(), True),
        StructField("host_identity_verified", StringType(), True),
        StructField("neighbourhood", StringType(), True),
        StructField("neighbourhood_cleansed", StringType(), True),
        StructField("neighbourhood_group_cleansed", StringType(), True),
        StructField("latitude", StringType(), True),
        StructField("longitude", StringType(), True),
        StructField("property_type", StringType(), True),
        StructField("room_type", StringType(), True),
        StructField("accommodates", StringType(), True),
        StructField("bathrooms", StringType(), True),
        StructField("bathrooms_text", StringType(), True),
        StructField("bedrooms", StringType(), True),
        StructField("beds", StringType(), True),
        StructField("amenities", StringType(), True),
        StructField("price", StringType(), True),
        StructField("minimum_nights", StringType(), True),
        StructField("maximum_nights", StringType(), True),
        StructField("minimum_minimum_nights", StringType(), True),
        StructField("maximum_minimum_nights", StringType(), True),
        StructField("minimum_maximum_nights", StringType(), True),
        StructField("maximum_maximum_nights", StringType(), True),
        StructField("minimum_nights_avg_ntm", StringType(), True),
        StructField("maximum_nights_avg_ntm", DoubleType(), True),
        StructField("calendar_updated", StringType(), True),
        StructField("has_availability", StringType(), True),
        StructField("availability_30", StringType(), True),
        StructField("availability_60", StringType(), True),
        StructField("availability_90", StringType(), True),
        StructField("availability_365", StringType(), True),
        StructField("calendar_last_scraped", StringType(), True),
        StructField("number_of_reviews", DoubleType(), True),
        StructField("number_of_reviews_ltm", DoubleType(), True),
        StructField("number_of_reviews_l30d", DoubleType(), True),
        StructField("availability_eoy", StringType(), True),
        StructField("number_of_reviews_ly", StringType(), True),
        StructField("estimated_occupancy_l365d", StringType(), True),
        StructField("estimated_revenue_l365d", StringType(), True),
        StructField("first_review", StringType(), True),
        StructField("last_review", StringType(), True),
        StructField("review_scores_rating", DoubleType(), True),
        StructField("review_scores_accuracy", DoubleType(), True),
        StructField("review_scores_cleanliness", DoubleType(), True),
        StructField("review_scores_checkin", DoubleType(), True),
        StructField("review_scores_communication", StringType(), True),
        StructField("review_scores_location", DoubleType(), True),
        StructField("review_scores_value", DoubleType(), True),
        StructField("license", IntegerType(), True),
        StructField("instant_bookable", StringType(), True),
        StructField("calculated_host_listings_count", IntegerType(), True),
        StructField("calculated_host_listings_count_entire_homes", IntegerType(), True),
        StructField(
            "calculated_host_listings_count_private_rooms", IntegerType(), True
        ),
        StructField("calculated_host_listings_count_shared_rooms", StringType(), True),
        StructField("reviews_per_month", StringType(), True),
    ]
)

df1 = spark.read.csv(
    "listings.csv.gz", header="true", multiLine="true", escape='"', schema=schema
)
print(df.schema)
assert df.schema == df1.schema

# example of DDL schema (Data Definition Language) using sql
ddl_schema = """
id INTEGER NOT NULL,
listing_url BOOLEAN,
scrape_id INTEGER,
last_scraped DATE,
source STRING,
name STRING,
description STRING,
neighborhood_overview STRING,
picture_url STRING,
host_id INTEGER
"""
df3 = (
    spark.read.format("csv")
    .option("header", "true")
    .schema(ddl_schema)
    .load("listings.csv.gz")
)
df3.printSchema()

# writing to parquet file
df3.write.format("parquet").mode("overwrite").save("03_write_dir/listings.parquet")
import os

for path in os.listdir("03_write_dir"):
    if os.path.isdir(f"03_write_dir/{path}"):
        for file in os.listdir(f"03_write_dir/{path}"):
            print(f"03_write_dir/{path}/{file}")
    else:
        print(f"03_write_dir/{path}")

# writing to a table
## to new table
# df3.write.format("delta").mode("overwrite").saveAsTable("listings")
## another option is using writeTo invoking DataFrameWriterV2
DA_name = ""
## options are append, overwrite, partition table ...
## preferedApproach
# df3.writeTo(f"{DA_name}.listings").createOrReplace()
