d = [
    {"name": "jean", "age": 20, "birth": "1999-01-01"},
    {"name": "marie", "age": 25, "birth": "1994-03-12"},
    {"name": "paul", "age": 32, "birth": "1987-11-05"},
    {"name": "thomas", "age": 32, "birth": "1987-11-05"},
    {"name": "sophie", "age": 28, "birth": "1991-07-19"},
    {"name": "lucas", "age": 22, "birth": "1997-09-30"},
    {"name": "toto", "age": 22, "birth": "1997-09-30"}
]

from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = SparkSession.builder.appName("test").getOrCreate()
df = spark.createDataFrame(d)
ages = df.select("age")
total = ages.count()
print(total)
sum_age = ages.agg(
    F.sum("age").alias("sum_age")
)
sum_age.show()

avg = sum_age.select("sum_age").withColumn(
    "avg_age", F.try_divide(
        F.col("sum_age"), F.lit(total)
    )
).drop("sum_age")



avg.show()

avg_ = avg.select("avg_age").take(1)[0]
print(avg_)



d = [
    {"name": "jean", "age": 20, "birth": "1999-01-01"},
    {"name": "marie", "age": 25, "birth": "1994-03-12"},
    {"name": "paul", "age": 32, "birth": "1987-11-05"},
    {"name": "thomas", "age": 32, "birth": "1987-11-05"},
    {"name": "sophie", "age": 28, "birth": "1991-07-19"},
    {"name": "lucas", "age": 22, "birth": "1997-09-30"},
    {"name": "toto", "age": 22, "birth": "1997-09-30"}
]

from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = SparkSession.builder.appName("test").getOrCreate()
df = spark.createDataFrame(d)
df.show()

births = df.select("birth").withColumn("year", F.year("birth")).drop("birth")
count = births.groupBy("year").agg(
    F.count("year").alias("count")
)
count.show()