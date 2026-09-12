l = [{"name": "john", "sexe": "male", "note": 18},
     {"name": "adriana", "sexe": "female", "note": 12},
     {"name": "toto", "sexe": "male", "note": 10},
     {"name": "tati", "sexe": "male", "note": 10},
     {"name": "tatiana", "sexe": "female", "note": 19}]

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("test").getOrCreate()

from pyspark.sql.types import StructType, StructField, StringType, IntegerType

schema = StructType([
    StructField("name", StringType(), nullable=True),
    StructField("sexe", StringType(), nullable=True),
    StructField("note", IntegerType(), nullable=True)
])

from pyspark.sql.window import Window

from pyspark.sql.functions import col, rank, dense_rank, row_number

window_spec = Window.partitionBy(col("sexe")).orderBy(col("note").asc())

df = spark.createDataFrame(l, schema)

ranked = df.withColumn("rank",
                       rank().over(window_spec)).withColumn("dense_rank", dense_rank().over(window_spec)).withColumn(
    "row_number", row_number().over(window_spec)).orderBy(col("sexe").desc())

ranked.show()

######" check all notes by sex

from pyspark.sql.functions import collect_set

list_of_notes = df.groupBy(col("sexe")).agg(

    collect_set(col("note")).alias("notes")


)


list_of_notes.show()


