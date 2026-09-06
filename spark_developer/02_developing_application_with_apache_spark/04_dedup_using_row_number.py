l = [
    # id = 1
    {"id": 1, "title": "Inception", "date": "2025-07-16"},
    {"id": 1, "title": "Inception", "date": "2025-07-16"},
    {"id": 1, "title": "Inception", "date": "2025-07-16"},
    {"id": 1, "title": "Inception", "date": "2024-01-10"},
    {"id": 1, "title": "Inception", "date": "2023-05-20"},
    {"id": 1, "title": "Inception", "date": "2023-05-20"},
    {"id": 1, "title": "Inception", "date": "2022-03-15"},
    # id = 2
    {"id": 2, "title": "The Dark Knight", "date": "2025-08-01"},
    {"id": 2, "title": "The Dark Knight", "date": "2025-08-01"},
    {"id": 2, "title": "The Dark Knight", "date": "2025-08-01"},
    {"id": 2, "title": "The Dark Knight", "date": "2025-08-01"},
    {"id": 2, "title": "The Dark Knight", "date": "2024-06-10"},
    {"id": 2, "title": "The Dark Knight", "date": "2023-04-05"},
    # id = 3
    {"id": 3, "title": "Interstellar", "date": "2026-01-01"},
    {"id": 3, "title": "Interstellar", "date": "2026-01-01"},
    {"id": 3, "title": "Interstellar", "date": "2025-01-01"},
    {"id": 3, "title": "Interstellar", "date": "2025-01-01"},
    {"id": 3, "title": "Interstellar", "date": "2025-01-01"},
    {"id": 3, "title": "Interstellar", "date": "2024-01-01"},
    # id = 4
    {"id": 4, "title": "The Matrix", "date": "2025-12-01"},
    {"id": 4, "title": "The Matrix", "date": "2025-12-01"},
    {"id": 4, "title": "The Matrix", "date": "2024-12-01"},
    {"id": 4, "title": "The Matrix", "date": "2024-12-01"},
    {"id": 4, "title": "The Matrix", "date": "2024-12-01"},
    {"id": 4, "title": "The Matrix", "date": "2023-12-01"},
]

from pyspark.sql import SparkSession

from pyspark.sql.window import Window

from pyspark.sql.functions import row_number, col

spark = SparkSession.builder.appName("complex").getOrCreate()

window_spec = Window().partitionBy("id").orderBy(col("date").desc())

dim = (
    spark.createDataFrame(l)
    .withColumn("row_number", row_number().over(window_spec))
    .filter(col("row_number") == 1)
    .select("id", "title", "date")
)

dim.show()
