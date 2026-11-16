import time

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Tungsten Demo").master("local").getOrCreate()

sc = spark.sparkContext

numbers_rdd = sc.parallelize(range(1, 10000001)).cache()
numbers_rdd.count()
numbers_rdd.count()  # much faster

# Python RDD rows must be tuples to become DataFrame rows
numbers_df = (
    numbers_rdd.map(lambda x: (x,)).toDF(["value"]).cache()
)  # cached with Tungsten
numbers_df.count()
numbers_df.count()  # much faster

# Tungsten is active in WholeStageCodegen

# AQE (on by default since Spark 3.2) wraps plans in AdaptiveSparkPlan isFinalPlan=false,
# which hides the *(n) codegen markers in explain() - disable it so the difference is visible
spark.conf.set("spark.sql.adaptive.enabled", "false")

spark.conf.set("spark.sql.codegen.wholeStage", "false")
no_whole_stage_sum = spark.range(1000000).selectExpr("sum(id)")
no_whole_stage_sum.explain()
"""
== Physical Plan ==
HashAggregate(keys=[], functions=[sum(id#66L)])
+- HashAggregate(keys=[], functions=[partial_sum(id#66L)])
   +- Range (0, 1000000, step=1, splits=1)

"""
no_whole_stage_sum.show()

spark.conf.set("spark.sql.codegen.wholeStage", "true")
whole_stage_sum = spark.range(1000000).selectExpr("sum(id)")
whole_stage_sum.explain()
"""
== Physical Plan ==
*(1) HashAggregate(keys=[], functions=[sum(id#75L)])
+- *(1) HashAggregate(keys=[], functions=[partial_sum(id#75L)])
   +- *(1) Range (0, 1000000, step=1, splits=1)


===> the stars  * means that Tungsten is present!
"""
whole_stage_sum.show()

"""
Spark UI -> Storage tab (same 10M numbers, cached twice):

ID  RDD Name                         Storage Level                            Size in Memory
1   PythonRDD                        Memory Serialized 1x Replicated          38.2 MiB
11  *(1) Scan ExistingRDD[value#0L]  Disk Memory Deserialized 1x Replicated    9.8 MiB

The cached DataFrame is NOT the same thing as the cached RDD:

- Cached RDD (PythonRDD): stored as pickled Python objects, row by row.
  Spark knows nothing about what is inside - it is just opaque bytes.
  Default level for RDD.cache() is MEMORY_ONLY.

- Cached DataFrame (*(1) Scan ExistingRDD...): stored by Tungsten in a columnar,
  compressed binary format. Spark knows the schema (value: long), so it packs
  the column tightly and compresses it (consecutive numbers compress very well).
  The "*(1)" in the name is the whole-stage codegen marker - the cache is built
  from a Tungsten plan. Default level for DataFrame.cache() is MEMORY_AND_DISK.

=> same data, ~4x less memory (9.8 MiB vs 38.2 MiB) for the DataFrame cache.
"""

# keep the app alive so the Spark UI (http://localhost:4040) can be inspected
time.sleep(1000000)
