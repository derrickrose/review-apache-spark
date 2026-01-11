# what is a DataFrame?
## Structured data processing in Apache Spark
## DataFrames are distributed collections of records, all with the same pre-defined structure (schema)
## Build on Spark's core concepts but with structure, optimization and familiar SQL-like operations for data manipulations.
## DataFrames track their schema and provide native support for many of the common SQL functions and relation operators (JOINs etc).
## DataFrames are evaluated as DAGs, using "lazy evaluation" (evaluating DataFrames only when required) and providing lineage
## and tolerance.

# creating DataFrames
## DataFrames can be created ...
## JSON, CSV, Parquet, ORC, Text or Binary Files
## Delta Lake or other Table Storage format directories
## A table or view in a catalog (like Unity Catalog)
## An external database
## An existing RDD
## example a csv file can be read using spar.read.csv()

# DataFrame API optimizations
## Adaptive Query Execution - Dynamic plan adjustments (cost-based optimization) during runtime based on actual data characteristics
### and execution patterns.
## In-Memory Columnar Storage - In-memory columnar format for all DataFrames enabling efficient analytical query performance and
### reduced memory footprint. ==> Thanks to Tungsten
## Built-in statistics - Automatic statistics collection while saving to optimized formats (Parquet, Delta)
### enables smarter query planning and execution
## Catalyst Optimizer and Photon

# What is Tungsten
## Tungsten is Spark's columnar in memory execution engine, providing a consistent columnar representation for
## DataFrames regardless of the data source.
## While DataFrames always use Tungsten's columnar format in memory, statistics are only collected when saving to
## optimized file formats
## Tungsten provides several performance benefits, including off-heap memory management, cache-aware computation,
## code generation for faster execution, and whole-stage code generation.
## It is important to distinguish between the in-memory representation, which is always columnar via Tungsten,
## and the on-disk storage formats, which may be row-based (e.g. CSV) or columnar (e.g. Parquet).
## Tungsten's columnar format is a key enabler of many of Spark's query optimizations.

# DataFrame (or Query planning)
## When a DataFrame is evaluated, the Driver creates an optimized execution plan through a series of transformation.
## converting the logical plan into an efficient physical execution plan that minimizes resource usage and execution time
## Unresolved Logical Plan ==> Analyzed Logical Plan ==> Optimized Logical Plan ==> Physical plan
## Analysis  ================> Logical Optimizations ==> Physical Optimizations ==> Code Generation

# Catalyst Optimizer and Photon
## Query optimization, code generation and efficient memory management
## Catalyst optimizer
###### Query Optimization that convert DataFrame Operations into an optimized execution plan
###### Applies rule-based and cost-based optimizations to improve query performance
## Photon engine
###### DataBricks-native vectorized query engine that accelerates query execution
###### Processes data in batches rather than row-by-row for better performance
###### Runs by default on Databricks SQL warehouses and serverless compute
###### Can be enabled on All-Purpose and Job Clusters in Databricks

# More on columnar storage
## Organizes data by column rather than row, enabling efficient scanning and analysis
## Particularly efficient for analytics workloads
## Implemented in DataFrame internal Storage and physical file encoding formats such as Parquet and ORC

# DataFrameReader and DataFrameWriter
## DataFrameReader (spark.read)
#### Supports multiple formats
#### Provides schema inference
"""
spark.read.format("format").option("key", "value").load("path")
spark.read.csv("path")
spark.read.json("path")
spark.read.parquet("path")
spark.read.orc("path")
spark.read.table("catalog.table")
spark.read.format("format").load("path")
"""
## DataFrameWriter (dataframe.write)
#### Flexible output format and partitioning
#### Supports various save modes (overwrite, append)
"""
df.write.format("format").mode("mode").option("key", "value").save("path")
df.write.csv("path")
df.write.json("path")
df.write.parquet("path")
df.write.orc("path")
df.write.saveAsTable("catalog.table")
df.write.format("format").save("path")
"""

# DataFrame Schema
## Structure, type, and data guarantee
#### Every DataFrame has a defined schema, structure and data types of all columns
#### Can be inferred from data or explicitly specified (more efficient)
#### Self definning formats like Parquet include schema information
#### Use printSchema() method to print out the DataFrame schema
"""
from pyspark.sql.types import *
schema = StructType([StructField("name", StringType(), True), StructField("age", IntegerType(), True)])
df = spark.createDataFrame([("John", 21), ("Jane", 22)], schema)
df.printSchema()
"""

# DDL Schemas
## An alternative to StructType definitions
## Instead of defining schemas using StructType objects, you can use DDL (Data Definition Language) strings for more readable
##### schema definitions
## You can do this :
"""
ddl_schema = "name STRING NOT NULL, age INT, city STRING"
df = spark.read.csv("path", schema=ddl_schema)
df.printSchema()
"""

# DataFrame Data Types
# primitive data types
"""
pyspark.sql.types.DataTypes                 SQL               Python base equivalents
----------------------------------------------------------------------------------------
ByteType                                  TINYINT             int
ShortType                                  SMALLINT           int
IntegerType                                INT                int
LongType                                   BIGINT             int (long before python3 ????)
FloatType                                  FLOAT              float
DoubleType                                 DOUBLE             float
DecimalType                                DECIMAL            decimal.Decimal (not float or double, better precision)
BooleanType                                BOOLEAN            bool
StringType                                 STRING             str
BinaryType                                 BINARY             bytes (more accurate than bytearray since spark return bytes objects)
DateType                                   DATE               datetime.date
TimestampType                              TIMESTAMP          datetime.datetime
NullType                                   NULL               None
StructType                                STRUCT             Row or dict or tuple or namedtuple (in DataFrames, returned as pyspark.sql.Row, but conceptually a dict)
ArrayType                                 ARRAY              list or tuple  
MapType                                   MAP                dict 
"""

# Transformations and actions
# DataFrames programming Operations
## DataFrames are immutable, once created, their data cannot be modified instead
## Transformations creates new DataFrames from existing ones (can be categorized as coarse Grain Transformations)
## Actions like showing or saving output trigger actual computation and produce final results
#### Multiple transformations can be called, the job is only created when an action is requested, a process called lazy evaluation

# Common DataFrame API Methods
## Transformations
#### select()
#### filter()
#### withColumn()
#### groupBy()
#### agg()
## Actions
#### count()
#### show()
#### take(n)
#### first()
#### write()

# SparkSQL
# SQL interface for Spark DataFrames
## DataFrame Registration :
#### Temporary views
###### createOrReplaceTempView()
#### Global Temp view
###### createGlobalTempView()
## SQL query execution
#### Use spark.sql() for SQL statements
#### Seamless integration with DataFrame API
#### Full SQL support
#### Complex types and expressions
#### Built-in function library
#### Seamless metastore integration

# Primer on SQL Metastores
# Metadata Management for Spark SQL
## A metastore is responsible for
#### defining table schemas and locations
#### defining table partitions
#### storing properties and information for objects including tables, views, functions
## Unity Catalog is the centralized metadata service provided for Databricks accounts and assigned to Databricks workspaces
#### that enables fine-grained security and governance across all data assets
