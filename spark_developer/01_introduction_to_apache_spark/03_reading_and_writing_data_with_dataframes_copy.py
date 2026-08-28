## from csv
# https://github.com/MangoTheCat/Modelling-Airbnb-Prices/blob/master/listings.csv.gz
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("reading_data_with_dataframes")
    # .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.0")
    # .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    # .config("spark.sql.catalog.spark_catalog",
    #         "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.sql.shuffle.partitions", "10").getOrCreate()
)

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    LongType,
    DateType,
    DoubleType,
)

schema = StructType(
    [
        StructField("id", IntegerType(), True),
        StructField("listing_url", StringType(), True),
        StructField("scrape_id", LongType(), True),
        StructField("last_scraped", DateType(), True),
        StructField("name", StringType(), True),
        StructField("summary", StringType(), True),
        StructField("space", StringType(), True),
        StructField("description", StringType(), True),
        StructField("experiences_offered", StringType(), True),
        StructField("neighborhood_overview", StringType(), True),
        StructField("notes", StringType(), True),
        StructField("transit", StringType(), True),
        StructField("access", StringType(), True),
        StructField("interaction", StringType(), True),
        StructField("house_rules", StringType(), True),
        StructField("thumbnail_url", StringType(), True),
        StructField("medium_url", StringType(), True),
        StructField("picture_url", StringType(), True),
        StructField("xl_picture_url", StringType(), True),
        StructField("host_id", IntegerType(), True),
        StructField("host_url", StringType(), True),
        StructField("host_name", StringType(), True),
        StructField("host_since", DateType(), True),
        StructField("host_location", StringType(), True),
        StructField("host_about", StringType(), True),
        StructField("host_response_time", StringType(), True),
        StructField("host_response_rate", StringType(), True),
        StructField("host_acceptance_rate", StringType(), True),
        StructField("host_is_superhost", StringType(), True),
        StructField("host_thumbnail_url", StringType(), True),
        StructField("host_picture_url", StringType(), True),
        StructField("host_neighbourhood", StringType(), True),
        StructField("host_listings_count", IntegerType(), True),
        StructField("host_total_listings_count", IntegerType(), True),
        StructField("host_verifications", StringType(), True),
        StructField("host_has_profile_pic", StringType(), True),
        StructField("host_identity_verified", StringType(), True),
        StructField("street", StringType(), True),
        StructField("neighbourhood", StringType(), True),
        StructField("neighbourhood_cleansed", StringType(), True),
        StructField("neighbourhood_group_cleansed", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("zipcode", StringType(), True),
        StructField("market", StringType(), True),
        StructField("smart_location", StringType(), True),
        StructField("country_code", StringType(), True),
        StructField("country", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("is_location_exact", StringType(), True),
        StructField("property_type", StringType(), True),
        StructField("room_type", StringType(), True),
        StructField("accommodates", IntegerType(), True),
        StructField("bathrooms", DoubleType(), True),
        StructField("bedrooms", IntegerType(), True),
        StructField("beds", IntegerType(), True),
        StructField("bed_type", StringType(), True),
        StructField("amenities", StringType(), True),
        StructField("square_feet", IntegerType(), True),
        StructField("price", StringType(), True),
        StructField("weekly_price", StringType(), True),
        StructField("monthly_price", StringType(), True),
        StructField("security_deposit", StringType(), True),
        StructField("cleaning_fee", StringType(), True),
        StructField("guests_included", IntegerType(), True),
        StructField("extra_people", StringType(), True),
        StructField("minimum_nights", IntegerType(), True),
        StructField("maximum_nights", IntegerType(), True),
        StructField("calendar_updated", StringType(), True),
        StructField("has_availability", StringType(), True),
        StructField("availability_30", IntegerType(), True),
        StructField("availability_60", IntegerType(), True),
        StructField("availability_90", IntegerType(), True),
        StructField("availability_365", IntegerType(), True),
        StructField("calendar_last_scraped", DateType(), True),
        StructField("number_of_reviews", IntegerType(), True),
        StructField("first_review", DateType(), True),
        StructField("last_review", DateType(), True),
        StructField("review_scores_rating", IntegerType(), True),
        StructField("review_scores_accuracy", IntegerType(), True),
        StructField("review_scores_cleanliness", IntegerType(), True),
        StructField("review_scores_checkin", IntegerType(), True),
        StructField("review_scores_communication", IntegerType(), True),
        StructField("review_scores_location", IntegerType(), True),
        StructField("review_scores_value", IntegerType(), True),
        StructField("requires_license", StringType(), True),
        StructField("license", StringType(), True),
        StructField("jurisdiction_names", StringType(), True),
        StructField("instant_bookable", StringType(), True),
        StructField("cancellation_policy", StringType(), True),
        StructField("require_guest_profile_picture", StringType(), True),
        StructField("require_guest_phone_verification", StringType(), True),
        StructField("calculated_host_listings_count", IntegerType(), True),
        StructField("reviews_per_month", DoubleType(), True),
    ]
)

listings_df = (
    spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .option("multiLine", "true")
    .option("escape", '"')
    .option("quote", '"')
    .option("delimiter", ",")
    .option("mode", "PERMISSIVE")
    .schema(schema)
    .load("../data/")
    # .load("../data/listings.csv.gz", header="true", inferSchema="true", escape='"')
)
from pyspark.sql.functions import col

listings_df.createOrReplaceGlobalTempView("listings_global_temp")
listings_df.createOrReplaceTempView("listings_temp")


spark.sql("select * from listings_temp limit 10").show()
spark.sql("select * from global_temp.listings_global_temp limit 10").show()


import time

time.sleep(10 * 60)
