# Introduction to groupBy() operations

## groupBy() operations in Spark partition data across nodes based on grouping columns
## aggregations execute in parallel across partitions for optimal performance
## similar to SQL GROUPBY syntax but with more flexible options
## supports multiple columns for complex grouping patterns
## groupBy() returns a GroupedData object that let you chain aggregation methods like count(), mean(), sum(), avg()
#### which are lazily evaluated until an action triggers execution

# examples
"""
df.groupBy("department").count() ## count the number of users in each department
df.groupBy("department", "location").avg("salary") ## average salary by department and location
df.groupBy(col("department"), year(col("hire_date")).sum("revenue") ## sum revenue by department and year

"""

# basic aggregation methods
## count() equivalent to count(*)
## sum() equivalent to SUM(col)
## avg() equivalent to AVG(col)
## min() equivalent to MIN(col)

# combining multiple aggregations
## multiple aggregation methods can be chained together on the same GroupedData object
## .groupBy().agg( avg(col("age")).alias("avg_age"), avg(col("salary")).alias("avg_salary"))
## can be used on pandas UDFs as well
## .agg() is also needed for aliasing a single aggregation function
#### i.e. .agg({"average":"avg"}


data = [
    {"age": 32, "name": "James", "ville": "tana", "salary": 50000},
    {"age": 25, "name": "Joseph", "ville": "tana", "salary": 10000},
    {"age": 44, "name": "James", "ville": "diego", "salary": 33000},
    {"age": 25, "name": "Joseph", "ville": "diego", "salary": 100000},
    {"age": 22, "name": "James", "ville": "tana", "salary": 5000},
    {"age": 12, "name": "Jao", "ville": "tana"},
    {"age": 50, "name": "Joseph", "ville": "diego"},
]
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, rank, dense_rank, row_number

spark = SparkSession.builder.appName(
    "02_introduction_to_DataFrames_and_SQL"
).getOrCreate()
df = spark.createDataFrame(data)
average1 = df.groupBy("ville").avg("age")
average = df.groupBy("ville").agg(avg("age").alias("age_average"))
average1.show()
average.show()
df.groupBy("ville").agg(
    avg(col("age")).alias("avg_age"), avg(col("salary")).alias("avg_salary")
)

# window functions introduction
# aggregation without losing row level details
## what are they
#### special functions that can be used to perform calculation across a set of rows related to current row
## when to use
#### calculating running totals/averages
#### ranking records within groups
#### accessing previous/next rows values
#### comparing row values to group aggregates

"""
example 
from pyspark.sql.window import Window, rank

window_spec = Window.partitionBy("ville").orderBy("salary")
df.withColumn("rank", rank().over(window_spec)).show()


"""
from pyspark.sql.window import Window

window_spec = Window.partitionBy("ville").orderBy("salary")
salary_rank_df = df.withColumn("rank", row_number().over(window_spec))
salary_rank_df.show()
cleand_df = salary_rank_df.na.drop()
cleand_df.show()
