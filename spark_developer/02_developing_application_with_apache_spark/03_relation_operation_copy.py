from pyspark.sql import SparkSession

spark = (SparkSession.builder.appName("rel")
         .config("spark.sql.ansi.enabled", True)
         .getOrCreate())

from pyspark.sql import types as T

# required if number of columns are different
schema = T.StructType(
    [
        T.StructField("name", T.StringType(), nullable=True),
        T.StructField("age", T.DoubleType(), nullable=True),
        T.StructField("salary", T.IntegerType(), nullable=True),
        T.StructField("address", T.StringType(), nullable=True)
    ]
)

l1 = [
    {"name": "john", "age": 25.5, "salary": 5000},
    {"name": "emma", "age": 31.0, "salary": 6200},
    {"name": "carlos", "age": 28.0, "salary": 4800},
    {"name": "aisha", "age": 45.1, "salary": 8300},
    {"name": "yuki", "age": 22., "salary": 3900},
    {"name": "pierre", "age": 38.5, "salary": 7100}
]

l2 = [
    {"name": "john", "age": "20", "salary": 5000, "address": "12 rue de Paris"},
    {"name": "emma", "age": "31", "salary": 6200, "address": "45 avenue Victor Hugo"},
    {"name": "carlos", "age": "28", "salary": 4800, "address": "8 boulevard Saint-Michel"},
    {"name": "nadia", "age": "34", "salary": 5600, "address": "19 rue de Rivoli"},
    {"name": "yuki", "age": "22", "salary": 3900, "address": "27 rue Lafayette"}
]

from pyspark.sql import functions as F

df1 = spark.createDataFrame(l1).withColumn("t", F.lit(None)).select("name", "age", "salary", "t")
df2 = spark.createDataFrame(l2).select("name", "age", "salary", "address")
df3 = df1.union(df2)

df3.show()
df3.printSchema()
