l = [
    # ==================== SCI-FI ====================
    {"id": 1, "title": "Inception", "date": "2025-07-16", "category": "Sci-Fi"},
    {"id": 1, "title": "Inception", "date": "2025-07-16", "category": "Sci-Fi"},

    {"id": 2, "title": "Interstellar", "date": "2026-01-01", "category": "Sci-Fi"},
    {"id": 2, "title": "Interstellar", "date": "2026-01-01", "category": "Sci-Fi"},

    {"id": 3, "title": "The Matrix", "date": "2025-03-10", "category": "Sci-Fi"},
    {"id": 3, "title": "The Matrix", "date": "2025-03-10", "category": "Sci-Fi"},

    {"id": 4, "title": "Blade Runner 2049", "date": "2024-11-20", "category": "Sci-Fi"},
    {"id": 4, "title": "Blade Runner 2049", "date": "2024-11-20", "category": "Sci-Fi"},

    # ==================== ACTION ====================
    {"id": 5, "title": "The Dark Knight", "date": "2025-08-01", "category": "Action"},
    {"id": 5, "title": "The Dark Knight", "date": "2025-08-01", "category": "Action"},

    {"id": 6, "title": "Mad Max: Fury Road", "date": "2025-06-15", "category": "Action"},
    {"id": 6, "title": "Mad Max: Fury Road", "date": "2025-06-15", "category": "Action"},

    {"id": 7, "title": "John Wick", "date": "2024-09-10", "category": "Action"},
    {"id": 7, "title": "John Wick", "date": "2024-09-10", "category": "Action"},

    {"id": 8, "title": "Gladiator", "date": "2023-05-20", "category": "Action"},
    {"id": 8, "title": "Gladiator", "date": "2023-05-20", "category": "Action"},

    # ==================== CRIME ====================
    {"id": 9, "title": "The Godfather", "date": "2024-03-15", "category": "Crime"},
    {"id": 9, "title": "The Godfather", "date": "2024-03-15", "category": "Crime"},

    {"id": 10, "title": "Pulp Fiction", "date": "2025-02-10", "category": "Crime"},
    {"id": 10, "title": "Pulp Fiction", "date": "2025-02-10", "category": "Crime"},

    {"id": 11, "title": "Goodfellas", "date": "2024-07-01", "category": "Crime"},
    {"id": 11, "title": "Goodfellas", "date": "2024-07-01", "category": "Crime"},

    {"id": 12, "title": "The Departed", "date": "2023-10-12", "category": "Crime"},
    {"id": 12, "title": "The Departed", "date": "2023-10-12", "category": "Crime"},

    # ==================== DRAMA ====================
    {"id": 13, "title": "Forrest Gump", "date": "2025-04-20", "category": "Drama"},
    {"id": 13, "title": "Forrest Gump", "date": "2025-04-20", "category": "Drama"},

    {"id": 14, "title": "The Shawshank Redemption", "date": "2024-12-01", "category": "Drama"},
    {"id": 14, "title": "The Shawshank Redemption", "date": "2024-12-01", "category": "Drama"},

    {"id": 15, "title": "Fight Club", "date": "2025-01-15", "category": "Drama"},
    {"id": 15, "title": "Fight Club", "date": "2025-01-15", "category": "Drama"},

    {"id": 16, "title": "The Green Mile", "date": "2023-08-10", "category": "Drama"},
    {"id": 16, "title": "The Green Mile", "date": "2023-08-10", "category": "Drama"},
]

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("complex_data_collect_list").getOrCreate()

df = spark.createDataFrame(l)
from pyspark.sql.functions import collect_list, collect_set, col

df.groupBy("category").agg(
    collect_list(col("title"))
).show()

# now if I want a list of json, I need the struct

from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from pyspark.sql.functions import struct

grou = df.groupBy("category").agg(

    collect_list(
        struct(
            "id",
            "title",
            "date"

        )

    ).alias("movies")

)

deduped = df.groupBy("category").agg(
    collect_set(struct(
        "id",
        "title",
        "date"
    )).alias("movies")
)

from pyspark.sql.functions import size

grou.withColumn("size", size("movies")).show()
deduped.withColumn("size", size("movies")).show()
