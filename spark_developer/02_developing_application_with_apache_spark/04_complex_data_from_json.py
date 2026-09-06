import json

l = [
    {
        "id": 1,
        "movie": json.dumps(
            {
                "title": "Inception",
                "info": {"release_date": "2025-07-16", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 1,
        "movie": json.dumps(
            {
                "title": "Inception",
                "info": {"release_date": "2025-07-16", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 1,
        "movie": json.dumps(
            {
                "title": "Inception",
                "info": {"release_date": "2024-01-10", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 1,
        "movie": json.dumps(
            {
                "title": "Inception",
                "info": {"release_date": "2023-05-20", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 2,
        "movie": json.dumps(
            {
                "title": "The Dark Knight",
                "info": {"release_date": "2025-08-01", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 2,
        "movie": json.dumps(
            {
                "title": "The Dark Knight",
                "info": {"release_date": "2025-08-01", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 2,
        "movie": json.dumps(
            {
                "title": "The Dark Knight",
                "info": {"release_date": "2024-06-10", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 3,
        "movie": json.dumps(
            {
                "title": "Interstellar",
                "info": {"release_date": "2026-01-01", "director": "Christopher Nolan"},
            }
        ),
    },
    {
        "id": 3,
        "movie": json.dumps(
            {
                "title": "Interstellar",
                "info": {"release_date": "2025-01-01", "director": "Christopher Nolan"},
            }
        ),
    },
]

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StringType, StructType, StructField

spark = SparkSession.builder.appName("from_json").getOrCreate()

df = spark.createDataFrame(l)
df.printSchema()

schema = StructType(
    [
        StructField("title", StringType()),
        StructField(
            "info",
            StructType(
                [
                    StructField("release_date", StringType()),
                    StructField("director", StringType()),
                ]
            ),
        ),
    ]
)

df2 = (
    df.withColumn("movie_", from_json(col("movie"), schema))
    .drop("movie")
    .withColumnRenamed("movie_", "movie")
)
df2.printSchema()

# note to select nested values we can use dot .
# json.dumps() realy necessary otherwise it will set the schema to map
# getField() is an alternative way to reference column when nested , like the dot
# select("movie.info.release_date") <=> select(col("movie").getField("info").getField("release_date"))
df2.select(col("movie").getField("info").getField("release_date")).show()
