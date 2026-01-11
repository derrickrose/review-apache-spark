# relation operations
# joins, set operations, and key performance considerations for efficient relational queries

# DataFrame Join Operations
# Understanding how to combine data from multiple DataFrames
## Joins combine two DataFrames based on a matching key column(s)
## Multiple join types supported: inner, outer, left, right, cross
## Join condition can use single or multiple columns
## Column naming conflicts handled with DataFrame aliases
## refresher  on join types :
#### inner join keeps only matching rows
#### left join keeps all rows from the left DataFrame along with matching rows from the right DataFrame
#### right join keeps all rows from the right DataFrame along with matching rows from the left DataFrame
#### outer join keeps all rows from both DataFrames, filling in nulls where no match exists
#### cross join performs a cartesian product, combining all rows from both DataFrames (use with care) (no joining key).
## column naming conflicts can occur if both DataFrames have a column with the same name, sucha as id; in such cases,
#### use disambiguated column referencing methods (e.g. df1["id"].alias("id_df1", df1.id == df2.id)

# join example
"""
# Basic join
## Performs an inner join by default on the user_id column
df1.join(df2, "user_id") # Inner join by default

# Specifying join type
## Performs a left join that keeps all rows from df1, matching where user_id equals
df1.join(df2, on=df1.user_id == df2.user_id, how="left")

# Multiple conditions with DataFrame aliases
## Performs an inner join with multiple conditions using DataFrame aliases to clearly resolve column names such as id and region
from pyspark.sql.functions import col
users.alias("u").join(
    orders.alias("o"),
    [col("u.id") == col("o.user_id"), col("u.region") == col("o.region")],
    "inner"
)
"""

# set operations A [1,2,3]  B [2,3,4]
# Understand relationships within datasets
## Union: includes all unique elements from both sets (no duplicates)
#### A U B -> [1,2,3,4]
## Intersection: includes elements in both sets (no duplicates)
#### A ∩ B -> [2,3]
## Substraction: includes elements in A only
#### A - B -> [1]
#### There are functions which allow a union to retain duplicates found in both sets

# DataFrame Set Operations
# Finding common records or differences between datasets
# All set operations require matching DataFrames schemas
"""
Operation        Example                         Description
union()          df1.union(df2)                  Combines all rows from both DataFrames by position (first column by first column, same for the rest)
intersect()      df1.intersect(df2)              Returns only rows present in both DataFrames
subtract()      df1.subtract(df2)               Returns only rows in first DataFrame but not in second
unionByName()    df1.unionByName(df2)            Combines DataFrames matching by column names


"union() preserves duplicates by default. 
Other set operations like intersect() and subtract() remove duplicates by default. 
Use xxxAll() variants to preserve duplicates for those operations."
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("03_relation_operation").getOrCreate()

df1 = spark.createDataFrame([(1,), (1,), (2,)], ["id"])
df2 = spark.createDataFrame([(2,), (3,)], ["id"])

df1.union(
    df2
).show()  # If it shows 1,1,2,2,3 → union() KEEPS duplicates (I'm right), this is correct  # If it shows 1,2,3 → union() REMOVES duplicates (text is right, I'm wrong)

df1 = spark.createDataFrame([(1,), (1,), (2,)], ["id"])
df2 = spark.createDataFrame([(1,), (2,)], ["id"])

df1.intersect(df2).show()  # Does this remove duplicates?

# Join Performance Considerations
# Optimizing relational operations in a distributed environment
## Join strategy selection
#### Spark automatically chooses the join strategy
#### smaller DataFrame should be referenced first
"""
good 
small_df.join(large_df, "key")

bad
large_df.join(small_df, "key")
"""
## use the broadcast() hint
#### Spark can optimize join performance by broadcasting small tables using the broadcast hint
"""
from pyspark.sql.functions import broadcast
large_df.join(broadcast(small_df,"key"))

It avoids costly shuffle by sending the small DataFrame to all worker nodes
"""

# More join performance considerations
# optimizing relational operations in a distributed environment
## data skew handling
#### uneven distribution of join keys can impact performance
#### consider repartitioning in some cases
## memory management
#### monitor shuffle spill metrics for joins
#### consider caching frequently joined DataFrames
## Tip: Use the Spark UI to monitor join performance and identify bottlenecks
## Tip: use projection to only select needed columns
