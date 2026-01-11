# nested and semi-structured data

# complex data types are common in modern data pipelines, especially when working with JSON data,
## nested analytics results, or feature engineering
## types include :
#### Arrays (pyspark.sql.types.ArrayType) (ordered collection of elements e.g. [1,2,3])
#### Structs (pyspark.sql.types.StructType) (Nested structures with predefined named fileds)
#### Maps (pyspark.sql.types.MapType) (Key-value pairs with keys are not predefined)

# JSON Strings vs Structs
## JSON Strings require parsing overhead and memory waste
## Structs give type safety and better performance
## Convert early using from_json with schema

# """

from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("04_complex_data").getOrCreate()

js = {"name": "frils", "age": 38, "features": {"note": 10.5}}
df0 = spark.createDataFrame([(1, js)], ["id", "json_data"])
print("--------------------------------------------------------------")
df0.printSchema()
df0.show()
"""
root
 |-- id: long (nullable = true)
 |-- json_data: map (nullable = true)
 |    |-- key: string
 |    |-- value: string (valueContainsNull = true)

+---+--------------------+
| id|           json_data|
+---+--------------------+
|  1|{name -> frils, f...|
+---+--------------------+
"""

## TODO the parsing only works on json strings not like map
df = spark.createDataFrame([(1, str(js))]).toDF("id", "json_data")
print("--------------------------------------------------------------")
df.printSchema()
df.show()

"""
root
 |-- id: long (nullable = true)
 |-- json_data: string (nullable = true)

+---+--------------------+
| id|           json_data|
+---+--------------------+
|  1|{'name': 'frils',...|
+---+--------------------+

"""

schema = StructType(
    [
        StructField("name", StringType(), True),
        StructField("age", IntegerType(), True),
        StructField("features", MapType(StringType(), DoubleType()), True),
    ]
)

df2 = df.withColumn("json", from_json(col("json_data"), schema)).drop("json_data")
print("--------------------------------------------------------------")
df2.printSchema()
df2.show()
print(df2.head(1)[0].json.name)  ## frils
"""
# this actually from the schema we defined earlier

root
 |-- id: long (nullable = true)
 |-- json: struct (nullable = true)
 |    |-- name: string (nullable = true)
 |    |-- age: integer (nullable = true)
 |    |-- features: map (nullable = true)
 |    |    |-- key: string
 |    |    |-- value: double (valueContainsNull = true)

+---+--------------------+
| id|                json|
+---+--------------------+
|  1|{frils, 38, {note...|
+---+--------------------+

frils

"""

# working with StructType
## StructTypes maintain a logical grouping of related fields, like a table
## Struct Fields can be accessed and operated on using dot notation or using the getField() column function
"""
Input data with struct column user 
user : struct<name:string,age:int,scores:array<double>>

df.select(
col("user.name"), # direct field access
col("user").getField("age"), # alternative field access
col("user.scores")[0].alias("first_score") # nested field access
)
"""

# the explode function
# Unnesting nested data in arrays while preserving other columns
"""
Input: DataFrame with array column
id  items
0   [1,2,3]
1   [4,5,6]

# define schema matching json structure 
df.select("id", explode(col("items")).alias("item"))

# output
id  item
0   1
0   2
0   3
1   4
1   5
1   6
==> one row per element in the array 

"""

# common array column operations
"""
function                                            example                              purpose
array_contains(col, var)                array_contains(items, "a")            test if array contains a value
size(col)                               size(items)                           returns number of elements 
element_at(col, index)                  element_at(items, 1)                  returns nth element at index 
array_distinct(col)                     array_distinct(items)                 remove duplicates from array

note: collection in Spark Sql are 1-based indexing meaning starts from 1 not 0
"""

# aggregating to collections
# grouping items into arrays
## collect_list() is an aggregate function that gathers all values from a column into an array
#### commonly used with groupBy to build arrays of related values within each group
## collect_set() works similarly but removes duplicates, producing arrays of unique values
"""
df.groupBy("region").agg(collect_list(col("name")).alias("users")).show()
"""

# best practice for complex data types
## explode on large array can cause data explosion, 1 row becomes N rows which can overwhelm memory and processing
## collect_list/collect_set can be memory-intensive when groups are large as they hold all values per group in memory
## consider collect_set when duplicates are not needed and order does not matter
#### uses less memory, because it removes duplicates
#### less shuffle overhead as duplicate values dont need to be collected
