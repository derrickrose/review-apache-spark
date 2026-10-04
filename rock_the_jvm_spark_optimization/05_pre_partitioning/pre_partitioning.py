from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col

spark = (
    SparkSession.builder
    .appName("Pre-partitioning")
    .master("local")
    .getOrCreate()
)

# deactivate broadcast joins
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)


def add_columns(df: DataFrame, n: int) -> DataFrame:
    """add_columns(initial_table, 3) => DataFrame with columns "id", "newCol1", "newCol2", "newCol3" """
    new_columns = [f"id * {i} as newCol{i}" for i in range(1, n + 1)]
    return df.selectExpr("id", *new_columns)


# don't touch this
initial_table = spark.range(1, 10000000).repartition(10)  # RoundRobinPartitioning(10)
narrow_table = spark.range(1, 5000000).repartition(7)  # RoundRobinPartitioning(7)

# scenario 1
wide_table = add_columns(initial_table, 30)
join1 = wide_table.join(narrow_table, "id")
join1.explain()
# print(join1.count())  # around 20s

# TODO: add query plan

# scenario 2
alt_narrow = narrow_table.repartition(col("id"))  # use a HashPartitioner
alt_initial = initial_table.repartition(col("id"))
# join on co-partitioned DFs
join2 = alt_initial.join(alt_narrow, "id")
result2 = add_columns(join2, 30)
result2.explain()
# print(result2.count())  # 6s

# TODO: add query plan

"""
Lesson: partition early.
Partitioning late is AT BEST what Spark naturally does.
co-partitioned 
"""

# scenario 3
enhance_columns_first = add_columns(initial_table, 30)
repartitioned_narrow = narrow_table.repartition(col("id"))
repartitioned_enhanced = enhance_columns_first.repartition(col("id"))  # USELESS!
## even commenting the previous line, the query plan looks the same as it is not commented, why ??,
result3 = enhance_columns_first.join(repartitioned_enhanced, "id")
result3 = enhance_columns_first.join(repartitioned_narrow, "id")
# print(result3.count())  # around 19-20s
result3.explain()

# TODO: add query plan

"""
Exercise: what would happen if we just repartitioned the smaller table to 10 partitions?
TERRIBLE!
"""
initial_table.join(narrow_table.repartition(10), "id").explain()  # identical to scenario 1

# TODO: add query plan
