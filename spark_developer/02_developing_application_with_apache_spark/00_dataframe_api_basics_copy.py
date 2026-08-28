# DataFrame Transformations Methods
# Core methods for distributed transformation

## DataFrame operations are distributed automatically across all partitions, enabling parallel processing of larege datasets
## All DataFrame transformations have equivalent SQL operations under the hood (e.g., select() maps to SELECT, filter() maps to WHERE)
## Methods return a new DataFrame rather than modifying the existing one, supporting immutable transformations
## Each operation builds upon the logical plan until an action triggers execution

# Basic DataFrame Transformation Methods
"""
DataFrame Method                            Equivalent SQL Operation                Description
select()                                SELECT                                      projection : choose specific columns
filter(), where()                       WHERE                                       selection : filter rows based on conditions
groupBy()                               GROUP BY                                   group rows by columns for aggregation
orderBy(), sort()                       ORDER BY                                   sort DataFrame by columns
join()                                  JOIN                                       combine two DataFrames by a key

"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StringType

spark = SparkSession.builder.appName("DataFrameBasics").getOrCreate()
from pyspark.sql.functions import regexp_count, col, lit
from pyspark.sql.types import ArrayType, StringType

from pyspark.sql.functions import udf, pandas_udf


@udf("string")
def upper_case(url):
    return url.upper()


import pandas as pd


@pandas_udf(returnType=StringType())
def upper_case_pandas_udf(values: pd.Series)-> pd.Series:
    return values.str.upper()


df = spark.read.csv("../data/", header=True, inferSchema=True, multiLine=True, quote='"', escape='"', sep=",",
                    mode="PERMISSIVE").select("id",
                                              "listing_url").filter(

    col("listing_url").isNotNull() & col("id").isNotNull() & (regexp_count("listing_url", lit("^https")) > 0)

).withColumn(
    "URL", upper_case(col("listing_url"))
)


import time

# générer un DataFrame avec beaucoup de lignes (ex: 1M+)
big_df = df.select(col("listing_url")).limit(1).crossJoin(spark.range(1_000_000))

t0 = time.time()
big_df.withColumn("URL", upper_case(col("listing_url"))).count()
print("UDF classique:", time.time() - t0)

t0 = time.time()
big_df.withColumn("URL", upper_case_pandas_udf(col("listing_url"))).count()
print("Pandas UDF:", time.time() - t0)




## links https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.html

# handling missing values in DataFrame
# common operations for dealing with null/NA values
## common functions for handling nulls:
#### isNull() / isNotNull() - checks if values are null
#### count(col) - counts non-null values in a specific column
#### df.fillna() / df.na.fill() - replace nulls with values
#### df.dropna() / df.na.drop() - remove rows with nulls
"""
df.dropna(subset=["my_column"])
df.na.drop(subset=["my_column"])
df.fillna("unknown")
df.na.fill("unknown")
"""

# referencing DataFrame columns
"""
Type                   Description                                                            Example 

Direct                 Simplest syntax, works for basic columns selection                     df.select("name")

By Attribute           Only works for column names that are valid Python identifiers,         df.select(df.first_name) OK
df.column_name         cal be referenced across DataFrames (e.g. in joins)                    df.select(df.first-name) KO
                       
Column expression      works with any column name, can be referenced across DataFrames        df.select(df["name"])
bracket notation       (e.g. in joins), note: using df.select(df["name"].alias("customer")) 
column with special     will work perfectly but it's not the most readable syntax
column with special     used for disambiguation in joins
characters too

Column object          required when building complex expressions or using column-specific    df.select(col("name")).alias("customer_name")
                       operations like alias(), cast(), asc(), desc()                         col("name").isNull() 
                       used when complex expressions are needed                       

"""

# common column object methods
## link https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.Column.html
"""
Method                    Description
alias()                   rename column, e.g.                       col("name").alias("customer_name")
cast() / astype()        change data type, e.g.                     col("age").cast(IntegerType())
isNull / isNotNull()     checks for nulls                           col("name").isNotNull()
contains()                string matching                           col("title").contains("Manager")
asc() / desc()            sort direction (used with sort/orderBy)   df.sort(col("age").desc(), col(name).asc())

"""

# Built-in Functions
## Functions operate on columns in DataFrames
## Functions can operate on scalar (strings, ints, etc) or complex data types (lists, structs, etc.)
## Function categories include Math, Datetime, Collection, BitWise, Aggregate, Window and more
## Can be used in both DataFrame operations and SQL queries using the equivalent SQL function names

# Common Built-in Functions
## https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html
## https://spark.apache.org/docs/latest/api/sql/index.html#built-in-functions
"""
Built-in Functions                              Equivalent SQL                        Description
round(col, scale)                               ROUND                                 round number to scale 
concat(col1, col2)                              CONCAT                                concatenate strings 
date_format(col, format)                        DATE_FORMAT                           format date string
regexp_replace(col, pattern, replacement)       REGEXP_REPLACE                        replace using regular expression
coalesce(col1, col2)                            COALESCE                              first non-null value

"""

# User Defined Functions (UDF)
# Extending Spark with custom functions
## UDFs allow you to use Python functions on DataFrame columns
## argument of a DataFrame should be a column ??? have to check this
## Allows developers to create reusable custom functions
## Can adversely impact performance as they cannot be optimized by the Catalyst optimize and have additional serialization overhead

## what happens under the hood
#### Spark detects a regular UDF :
###### wraps the Python function (make_greeting in this case) inside a special Spark SQL UDF object
###### registers its return type (here string)
###### this object can be serialized and shipped to JVM executors

#### Logical plan phase :
###### when you call df.select(make_greeting(col("name")) spark doesnt execute python code yet
###### instead, adds UDF expression node to the Catalyst logical plan something like UDF(make_greeting, [Column(name)])
###### catalyst understands there is a python udf here but can't optimize inside it (black box)

#### execution phase (runtime), when Spark executes the plan:
###### data is from the JVM (Spark executors)
###### for each partition :
######## Spark serializes the data (column to -> Python objects) using Pickle
######## Sends that batch to the Python worker process
###### the python worker:
######## calls your function row by row (your make_greeting)
######## produces new values ("Hello Alice", "Hello Bob")
###### Spark serializes the results and send back to the JVM
###### JVM combines the output into a new DataFrame column
## this python <-> jvm round trip per row adds heavy serialization overhead


"""
from pyspark.sql.functions import udf
@udf("string")
def make_greeting(name):
    return "Hello " + name

df.select(make_greeting("name")) ???? may be col("name")

---------------------------------------

@udf(returnType=StringType())
def make_greeting(name):
    return "Hello " + name
"""

# pandas UDFs (vectorized UDFs) and Apache Arrow
# Improving UDF performance using vectorized operations (batches of row)
## Pandas UDFs allow you to write Python functions that operate on batches of rows instead of single rows,
#### leveraging Apache Arrow for more efficient Python-JVM serialization
###### Arrow provides zero-copy data sharing between JVM and Python memory (not the case for regular UDFs)
###### Catalyst still sees a UDF node, but it's marked as a Pandas (vectorized) UDF so it can push down some optimizations (e.g. partitioning, projection)

## what happens under the hood:
#### sparks detects a Pandas UDF:
###### wraps the python function (make_greeting for instance) inside a special Spark SQL PandasUDF object
###### register its return type (string)
###### marks it as vectorized (operations on batches, not row)
###### this object can be serialized and shipped to JVM executors, like regular UDF but this time annotated for Arrow-based execution

#### Logical plan phase :
###### when you call df.select(make_greeting(col("name")) spark doesnt execute python code yet
###### instead, adds UDF expression node to the Catalyst logical plan something like PandasUDF(make_greeting, [Column(name)], returnType= StringType)
###### catalyst understands there is a pandas udf here and can optimize surrounding operations (projection, filter pushdown)
###### the plan notes that this function will use Arrow columnar data transfer

#### execution phase (runtime), when Spark executes the plan:
###### data is from the JVM (Spark executors)
###### for each partition :
######## Spark converts column data into Arrow columnar format (in-memory, contiguous buffers)
######## Sends that Arrow batch to the Python worker process
###### the python worker:
######## uses Pyarrow to map the Arrow batch directly into a Pandas Series or DataFrame
######## calls your function once per batch not once per row (e.g., make_greeting(pd.Series(["Alice", "Bob", "Chuck"]))
######## your function runs vectorized Pandas/NumPy code at c speed
######## produces new values Pandas Series result (e.g., ["Hello Alice", "Hello Bob", "Hello Charli"])
###### Spark serializes the results back Arrow format and sends to the JVM
###### JVM deserializes the Arrow buffer back into Spark's internal columnar format (ColumnarBatch
###### Spark merges the new column into the DataFrame and proceeds with further stages

"""
Aspect	                                Regular UDF	                                Pandas UDF
Data transfer	                        Row-by-row (Pickle)	                        Batch (Arrow columnar)
Execution granularity	                Each row separately	                        Whole column batches
Serialization	                        Python object serialization (slow)	        Apache Arrow (zero-copy)
Python function calls	                Called once per row	                        Called once per batch
Optimization	                        None (black box)	                        Partial (Catalyst aware of Arrow batches)
Performance                             High overhead	                            10–100× faster

summary when using regular udf
1️⃣ JVM executor prepares row-based data (not Arrow)
2️⃣ Sends Pickled rows to the Python worker
3️⃣ Python worker unpickles rows into native Python objects
4️⃣ Executes the UDF row by row
5️⃣ Pickles the results back into bytes
6️⃣ Sends the Pickled result batch back to the JVM
7️⃣ JVM unpickles and converts data to Spark’s internal format
8️⃣ Spark merges the new column into the DataFrame

summary flow when using pandas udf
1️⃣ JVM executor prepares column batches (Arrow format)
2️⃣ Sends Arrow batch to Python worker
3️⃣ Python worker → Arrow → Pandas Series
4️⃣ Executes the Pandas UDF (vectorized on Series)
5️⃣ Converts result → Arrow format
6️⃣ Sends Arrow batch back to JVM
7️⃣ JVM converts Arrow → Spark internal column
8️⃣ DataFrame result combined and returned
"""

"""
from pyspark.sql.functions import pandas_udf
@pandas_udf("integer")
def add_one(s: pd.Series) -> pd.Series:
    return s + 1

df.select(add_one("age")) ???? should be column instead of string???? to be checked 


@pandas_udf("string")
def make_greeting(pandas_series: pd.Series) -> pd.Series:
    return pandas_series.apply(lambda name: "Hello " + name)

df.select(make_greeting("name"))
"""

## summary
#### Spark runs on the Java Virtual Machine (JVM);
#### Python (PySpark on the Driver and Executors) runs in a separate process on the CPython runtime which is implemented in C
#### Python and JVM don't natively share memory
#### Serialization = converting Python objects to a format that Spark (JVM) can process
#### Traditional UDFs serialize one row at a time -> slow and inefficient
#### Pandas UDFs use Arrow to pass entire batches of data efficiently
#### Apache Arrow provides a fast, columnar, in-memory data format


import time

time.sleep(10 * 60)
