from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when

# Doc : 00_joins_and_size_estimation.md, section 12 (AQE : isFinalPlan, coalescing, skew)

spark = SparkSession.builder.appName("AQE").master("local[2]").getOrCreate()


def plan(df):
    return df._jdf.queryExecution().executedPlan().toString()


# 12.2 isFinalPlan
df = spark.range(1, 1_000_000).groupBy((col("id") % 10).alias("k")).count()
print("avant action   :", "isFinalPlan=true" in plan(df))  # attendu : False
df.show()
print("après show()   :", "isFinalPlan=true" in plan(df))  # attendu : False
df.collect()
print("après collect():", "isFinalPlan=true" in plan(df))  # attendu : True

# 12.3 coalescing : 200 partitions de shuffle presque vides regroupées
# attendu dans le Final Plan : AQEShuffleRead coalesced
df.explain()

# 12.4 skew join : une clé concentre la majorité des lignes
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "1MB")
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "1MB")
skewed = spark.range(1, 1_000_000).withColumn(
    "k", when(col("id") % 10 < 9, 0).otherwise(col("id"))
)
other = spark.range(0, 1_000_000).withColumnRenamed("id", "k")
joined = skewed.join(other, "k")
# collect() et pas count() : count() exécute un autre plan, joined.explain() resterait à isFinalPlan=false (12.2)
joined.collect()
# attendu dans le Final Plan : SortMergeJoin(skew=true) / AQEShuffleRead ... skewed
joined.explain()
