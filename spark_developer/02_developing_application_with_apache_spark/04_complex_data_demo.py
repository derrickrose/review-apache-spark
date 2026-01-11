## customers offers transactions

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    ArrayType,
)
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("04_complex_data_demo").getOrCreate()
customers_df = spark.read.format("json").load("customers.json")
customers_df.printSchema()  ## corrupt_record

## since spark is not able to read the correct schema, we need to define it manually as follow
raw = StructField("raw", StringType())
street = StructField("street", StringType())
city = StructField("city", StringType())
state = StructField("state", StringType())
zipcode = StructField("zip", StringType())
address = StructField("address", StructType([raw, street, city, state, zipcode]))
age = StructField("age", IntegerType())
name = StructField("name", StringType())
info = StructField("info", StructType([name, age, address]))
idcode = StructField("id", IntegerType())
people = StructField("people", ArrayType(StructType([idcode, info])))
schema = StructType([people])
from pyspark.sql.functions import explode

customers_df = spark.read.format("json").load("customers.json")
customers_df.printSchema()
customers_df.show(10)

# note that each line is a Row and we can reference by position as well by name
# finally I am wondering that a StructType is a Row
print(customers_df.limit(1).collect())
print(customers_df.limit(1).collect()[0])
print(customers_df.limit(1).collect()[0][0])
print(customers_df.limit(1).collect()[0][0][0])
print(customers_df.limit(1).collect()[0][0][0][0])
print(customers_df.limit(1).collect()[0][0][0]["id"])
print(customers_df.limit(1).collect()[0]["people"][0]["info"])

## todo check execution time with and without schema
