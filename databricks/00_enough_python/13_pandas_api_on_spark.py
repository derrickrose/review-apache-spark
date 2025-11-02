# pandas api on spark
## pandas is actually industry standard for data analysis but it only works on a single machine
## we cannot use it if our dataset is so large which not fit on a single machine
## fortunately there is pandas api on spark which allow to use the same pandas code in a setting of distributed computation
## spark
## limitation pandas => all data must fit in memory of single machine
## spark addresses this limitation => scaling across many machines
## spark api is different from pandas api
## allow us to use pandas-like syntax on spark DataFrame
## certain edge functionality of pandas might not work on spark but most of them will
## 31 giga pyspark.pandas is faster than pandas
## 95 giga pandas is not working anymore => ConnectExceptionError
## we going to use pandas dataframe, spark and pyspark.pandas

# read csv with spark
from pyspark.sql import SparkSession

spark_session = SparkSession.builder.appName("pandas_api_on_spark").getOrCreate()
spark_df = spark_session.read.csv("listings.csv", header="true", inferSchema="true", multiLine="true", escape='"')
## default of show is 20
spark_df.show()
## display(spark_df) only on databricks environment
## argument inferSchema (without it, spark will read everything as string)
## inferSchema, spark will try to guess the datatype
## primitive StringType, BooleanType, ByteType, ShortType, IntegerType, LongType, FloatType, DoubleType, DecimalType
## date and time DateType, TimestampType
## complex (collection) ArrayType, MapType, StructType
## BinaryType, NullType
## Type hierarchy in spark
"""
DataType
├── AtomicType
│   ├── NumericType
│   │   ├── IntegralType
│   │   │   ├── ByteType
│   │   │   ├── ShortType
│   │   │   ├── IntegerType
│   │   │   └── LongType
│   │   └── FractionalType
│   │       ├── FloatType
│   │       └── DoubleType
│   ├── DecimalType
│   ├── StringType
│   ├── BooleanType
│   ├── BinaryType
│   ├── DateType
│   └── TimestampType
├── ArrayType
├── MapType
└── StructType
"""
import pandas as pd

pandas_df = pd.read_csv("listings.csv", header=0)
## default of head is 5
print(pandas_df.head(3).to_string())

import pyspark.pandas as ps

pypandas_df = ps.read_csv("listings.csv", inferSchema="true", header=0, multiLine="true", escape='"')
print(pypandas_df.head(3).to_string())

# pandas api on spark Index (list column name, each of the rows)
## different from pandas api standard and spark
## pandas use index for each or the rows
## spark is a distributed system so data is distributed into different segments and then distributed across the cluster
## this means it would be difficult to provide same Index, it will result too expensive computational overhead
## to solve this, the pandas api in spark offers few options:
## but we can configure by setting to compute.default_index_type the values distributed-sequence or distributed

## sequence as default works fine in moderately sized data
### implements sequence that increases one by one (0,1,2,3,...)
### uses pyspark window function without specifying partition
### can end up with whole partition on single node
### avoid when data is large

## distributed sequence : implements sequence that increases one by one
### uses group-by and group-map in distributed manner
### recommended if the index must be sequential for a large dataset and increasing one by one
### e.g. partition 1 0-> 99, partition 2 100 -> 199 ...

## distributed
### implements monotonically increasing sequence
### uses PySpark's monotonically_increasing_id in distributed manner
### recommended if the index does not have to be a sequence increasing one by one
### e.g. 1 2 33334545444 784544544545 ...

ps.set_option("compute.default_index_type", "distributed")
pypandas_df = ps.read_csv("listings.csv", inferSchema="true", header=0, multiLine="true", escape='"')
print(pypandas_df.head(100).to_string())

# converting from pypandas df to spark df
spark_df = pypandas_df.to_spark()

# converting from spark df to pandas on spark df
pypandas_df = ps.DataFrame(spark_df)  # pyspark.pandas
pypandas_df = spark_df.to_pandas_on_spark()  ## pyspark.pandas modern, preferred and safer

# converting from spark to pandas
pandas_df = spark_df.toPandas()  ## mode data to driver memory (only on small data)

# practical exercice
## let say we want to have the count of "property_type"
## spark dataframe > 100GB
print("-------------------------------------------- spark dataframe property count --------------")
spark_df.groupby("property_type").count().orderBy("count", ascending=False).show(100)
## pypandas dataframe (1-100 GB)
print(pypandas_df["property_type"].value_counts().head().to_string())

# data visualization
## we can create data visualization with pandas on spark with same familiar pandas api code syntax
## hist, kde, boxplot,
## pie, bar, barh, scatter
## area, line
import matplotlib.pyplot as plt

# ps.set_option("plotting.backend", "matplotlib")  # default is plotly

fig = pypandas_df["beds"].hist(bins=5)
fig.show()

# finally both spark and pandas on spark provide sql unlikely to traditional pandas
## pypandas_df
## have to register first
pypandas_df = pypandas_df.reset_index()
result = ps.sql("SELECT DISTINCT(property_type) FROM {pypandas_df}", pypandas_df=pypandas_df)
print(type(result)) # pyspark.pandas.frame.DataFrame
print(result.to_string())

## spark_df
