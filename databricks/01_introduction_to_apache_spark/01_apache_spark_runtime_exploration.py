# notebooks
## collaborative and interactive development and analysis environment
## collection of what called cells
## cells can execute code, render markdown or render visualization
## default language in Databricks is python
## unless you use the magic command `%scala`, `%md`, ...
## sc is the short for SparkContext in Databricks environment

# entry point SparkSession for a spark application
## encapsulate all the different contexts, sql context, spark context, streaming context (from spark 2.0)
## before that the contexts are separate
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("apache_spark_runtime").master("local").getOrCreate()
application_id = spark.sparkContext.applicationId
print(application_id)

# create a new SparkSession from the existing session
## can be same application id
spark2 = spark.newSession()
application_id2 = spark2.sparkContext.applicationId
print(application_id2)
assert application_id == application_id2
assert spark.sparkContext == spark2.sparkContext

# dummy calculation using spark
import time
from pyspark.sql.functions import col, sum

# this will create a dataframe with column id and values from 0 to 999
df = spark.range(0, 1_000)
# df.show()
"""
+---+
| id|
+---+
|  0|
|  1|
|  2|
"""
## add new column in spark df with values the multiplication between existing column by itself
df = df.withColumn("square", col("id") * col("id"))  # time.sleep(10)

## beware it is with shuffle operation
grouped_data = df.groupBy((col("id") % 10).alias("id_modulo_1O"))  ## pyspark.sql.GroupedData
result = grouped_data.agg(sum("square").alias("sum_square"))
"""
+------------+----------+
|id_modulo_1O|sum_square|
+------------+----------+
|           0|  32835000|
|           1|  32934100|
|           2|  33033400|

without using the alias on the grouping key 

+------------+----------+
|(id % 10)|sum_square|
+------------+----------+
|           0|  32835000|
|           1|  32934100|
|           2|  33033400|
"""

## cache the result to see it on webui
## https://localhost:4040 pour accéder au web-ui
## note in local you have to pause it then able to see it
result.cache()
result.show()
print("------------------------ iddle for 15 minutes before collect ----------------------------")
time.sleep(60 * 15)
result.collect()
print("------------------------ iddle for 15 minutes before unpersist ----------------------------")
result.unpersist()

# some theory about spark

# lazy evaluation
## spark executes the transformation lazily
## nothing actually runs until the call of result.show()
## spark builds a logical plan -> physical plan -> DAG and executes it in stages separated by shuffle boundaries

# step by step of what spark does in this example
## step1 : map stage (narrow transformation)
## combine Operations that do not require shuffling
### range(0, 1000) -> creates an RDD of numbers 0 - 999 (parallelized locally)
### withColumn("square", col("id") * col("id")) -> map-like operation, applied per partition
## these are narrow transformations, so Spark can pipeline them together into one stage

## step2  reduce stage (shuffle boundary)
### grouped_data = df.groupBy((col("id") % 10).alias("id_modulo_10")
### groupBy() introduces a shuffle, spark must redistribute rows so all records with the same id % 10 end up on the same partition
### result = grouped_data.agg(spark_sum("square"))
### the aggregation (sum("square")) happens after the shuffle i.e. in a separate reduce stage
### this is a wide transformation (requires data movement)

## step3 result materialization (optional)
### when calling cache() followed by show(), Spark might split the DAG slightly further depending on caching and lineage persistence
#### cache registers a storage dependency but doesnt trigger execution yet
#### show() triggers the job, causing two possible jobs :
##### Job1 : compute and cache the result
##### Job2 : display cached data

## in practice from the webui
### Job 0 has 2 stages
#### Stage 0 : map (range, withColumn)
#### Stage 1 : reduce (groupBy, agg)
### Job 1 has 0 or 1 stage
#### only reads from cache
