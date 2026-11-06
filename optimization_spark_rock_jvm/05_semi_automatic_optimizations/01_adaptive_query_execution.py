from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = (
    SparkSession.builder.appName("AQE")
    .master("local[*]")
    .config(
        "spark.local.dir",
        "/media/frils/disk_local_d/spark-tmp,/media/frils/disk_local_e/spark-tmp,/tmp/spark-tmp",
    )
    .config("spark.io.compression.codec", "zstd")
    .config("spark.sql.adaptive.enabled", "false")
    .config("spark.sql.autoBroadcastJoinThreshold", "-1")
    .config("spark.driver.memory", "40g")
    .getOrCreate()
)


## how is spark doing the partitioning, default is 200
## hash the key, modulo 200 (the number of partition) and then we have the partitions where the data with that particular key is sent
## if some of the partition is too small, spark will combine some of the partitions in order to maximize the parallelism


def demo_coalescing_partitions():
    numbers_df = spark.range(1000000)
    grouped_df = (
        numbers_df.selectExpr("id % 20 as key", "id as value")
        .groupBy("key")
        .agg(F.sum("value").alias("total"))
    )
    print("partition count", grouped_df.rdd.getNumPartitions())
    grouped_df.show()

    grouped_df.explain(True)

    """
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=true
+- == Final Plan ==
   *(2) HashAggregate(keys=[key#2L], functions=[sum(value#3L)], output=[key#2L, total#9L])
   +- AQEShuffleRead coalesced
      +- ShuffleQueryStage 0
         +- Exchange hashpartitioning(key#2L, 200), ENSURE_REQUIREMENTS, [plan_id=25]
            +- *(1) HashAggregate(keys=[key#2L], functions=[partial_sum(value#3L)], output=[key#2L, sum#13L])
               +- *(1) Project [(id#0L % 20) AS key#2L, id#0L AS value#3L]
                  +- *(1) Range (0, 1000000, step=1, splits=8)
+- == Initial Plan ==
   HashAggregate(keys=[key#2L], functions=[sum(value#3L)], output=[key#2L, total#9L])
   +- Exchange hashpartitioning(key#2L, 200), ENSURE_REQUIREMENTS, [plan_id=15]
      +- HashAggregate(keys=[key#2L], functions=[partial_sum(value#3L)], output=[key#2L, sum#13L])
         +- Project [(id#0L % 20) AS key#2L, id#0L AS value#3L]
            +- Range (0, 1000000, step=1, splits=8)


here we see the marker AdaptiveSparkPlan this marks that spark will try to perform optimization during runtime
here we have number of partition after the shuffle is not 200 but 1, given the data is small, spark combined the partitions
thanks to the AQE

now disabled the AQE, spark will use the default partition count which is 200

    """


def demo_switching_to_broadcast_join():
    large_table = spark.range(1000000).selectExpr("id as large_id", "id % 100 as key")
    small_table = spark.range(100).selectExpr("id as small_id", "id as key")

    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
    ## only uncomment for the second run
    spark.conf.set("spark.sql.adaptive.enabled", True)
    spark.conf.set("spark.sql.adaptive.autoBroadcastJoinThreshold", 10 * 1024 * 1024)
    joined = large_table.join(small_table, "key")
    joined.explain()

    """
    == Physical Plan ==
*(5) Project [key#3L, large_id#2L, small_id#8L]
+- *(5) SortMergeJoin [key#3L], [key#9L], Inner
   :- *(2) Sort [key#3L ASC NULLS FIRST], false, 0
   :  +- Exchange hashpartitioning(key#3L, 200), ENSURE_REQUIREMENTS, [plan_id=35]
   :     +- *(1) Project [id#0L AS large_id#2L, (id#0L % 100) AS key#3L]
   :        +- *(1) Filter isnotnull((id#0L % 100))
   :           +- *(1) Range (0, 1000000, step=1, splits=8)
   +- *(4) Sort [key#9L ASC NULLS FIRST], false, 0
      +- Exchange hashpartitioning(key#9L, 200), ENSURE_REQUIREMENTS, [plan_id=41]
         +- *(3) Project [id#6L AS small_id#8L, id#6L AS key#9L]
            +- *(3) Range (0, 100, step=1, splits=8)
            
we can see on the UI that there is optimization done, on the plan still same sort merge join
but actually on the UI, sql/dataframe tab, we have now some BroadcasHashJoin


== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [key#3L, large_id#2L, small_id#8L]
   +- SortMergeJoin [key#3L], [key#9L], Inner
      :- Sort [key#3L ASC NULLS FIRST], false, 0
      :  +- Exchange hashpartitioning(key#3L, 200), ENSURE_REQUIREMENTS, [plan_id=29]
      :     +- Project [id#0L AS large_id#2L, (id#0L % 100) AS key#3L]
      :        +- Filter isnotnull((id#0L % 100))
      :           +- Range (0, 1000000, step=1, splits=8)
      +- Sort [key#9L ASC NULLS FIRST], false, 0
         +- Exchange hashpartitioning(key#9L, 200), ENSURE_REQUIREMENTS, [plan_id=30]
            +- Project [id#6L AS small_id#8L, id#6L AS key#9L]
               +- Range (0, 100, step=1, splits=8)

    
also the final query plan on the UI changed the join strategy 

== Physical Plan ==
AdaptiveSparkPlan (29)
+- == Final Plan ==
   * HashAggregate (19)
   +- ShuffleQueryStage (18), Statistics(sizeInBytes=16.0 B, rowCount=1)
      +- Exchange (17)
         +- * HashAggregate (16)
            +- * Project (15)
               +- * BroadcastHashJoin Inner BuildRight (14)
                  :- AQEShuffleRead (6)
                  :  +- ShuffleQueryStage (5), Statistics(sizeInBytes=15.3 MiB, rowCount=1.00E+6)
                  :     +- Exchange (4)
                  :        +- * Project (3)
                  :           +- * Filter (2)
                  :              +- * Range (1)
                  +- BroadcastQueryStage (13), Statistics(sizeInBytes=1024.8 KiB, rowCount=100)
                     +- BroadcastExchange (12)
                        +- AQEShuffleRead (11)
                           +- ShuffleQueryStage (10), Statistics(sizeInBytes=1600.0 B, rowCount=100)
                              +- Exchange (9)
                                 +- * Project (8)
                                    +- * Range (7)
    
    
    """

    print(joined.count())


def demo_skew_join():  # 23 mins with skew
    spark.conf.set("spark.sql.adaptive.enabled", False)
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)

    skewed_df = spark.range(10000000000).selectExpr(
        "CASE WHEN id < 800000000 THEN 0 ELSE id % 100 END as key", "id as value1"
    )

    uniform_df = spark.range(100).selectExpr("id as key", "id as value2")

    joined = skewed_df.join(uniform_df, "key")
    joined.explain()
    """
    == Physical Plan ==
*(5) Project [key#2L, value1#3L, value2#9L]
+- *(5) SortMergeJoin [key#2L], [key#8L], Inner
   :- *(2) Sort [key#2L ASC NULLS FIRST], false, 0
   :  +- Exchange hashpartitioning(key#2L, 200), ENSURE_REQUIREMENTS, [plan_id=35]
   :     +- *(1) Project [CASE WHEN (id#0L < 800000000) THEN 0 ELSE (id#0L % 100) END AS key#2L, id#0L AS value1#3L]
   :        +- *(1) Filter CASE WHEN (id#0L < 800000000) THEN true ELSE isnotnull((id#0L % 100)) END
   :           +- *(1) Range (0, 10000000000, step=1, splits=8)
   +- *(4) Sort [key#8L ASC NULLS FIRST], false, 0
      +- Exchange hashpartitioning(key#8L, 200), ENSURE_REQUIREMENTS, [plan_id=41]
         +- *(3) Project [id#6L AS key#8L, id#6L AS value2#9L]
            +- *(3) Range (0, 100, step=1, splits=8)

    Spark UI metrics (AQE off, 10B rows, 200 shuffle partitions, zstd):

    1. Distribution across the 200 tasks
    | Metric             | Min   | 25th % | Median | 75th %  | Max      | Max / 75th |
    |--------------------|-------|--------|--------|---------|----------|------------|
    | Duration           | 3 ms  | 7 ms   | 11 ms  | 1.1 min | 13 min   | ~12x       |
    | Rows read (shuffle)| 0     | 0      | 0      | 92 M    | 892 M    | ~10x       |
    | Spill (memory)     | 0 B   | 0 B    | 0 B    | 1.4 GiB | 17.9 GiB | ~13x       |
    | Spill (disk)       | 0 B   | 0 B    | 0 B    | 185 KiB | 2.2 MiB  | ~12x       |
    | GC time            | 0 ms  | 0 ms   | 0 ms   | 27 ms   | 0.4 s    | ~15x       |

    2. Slowest tasks: rows per task = number of keys landing in the partition
    | Task index | Duration | Rows read   | Keys in partition       | Spill (memory) |
    |------------|----------|-------------|-------------------------|----------------|
    | 5          | 13 min   | 892,000,001 | key 0 (800 M + 92 M)    | 17.9 GiB       |
    | 64, 168    | ~4 min   | 276,000,003 | 3 keys x 92 M           | 5.5 GiB        |
    | 0, 4, 11.. | ~2.8 min | 184,000,002 | 2 keys x 92 M           | 3.4 GiB        |
    | ~100 others| 3-11 ms  | 0           | none (empty partitions) | 0              |

    3. Totals
    | Total task time    | 2.2 h          |
    | Rows shuffled      | 10,000,000,100 |
    | Shuffle read size  | 32.8 MiB       |
    | Spill (memory)     | 170.2 GiB      |
    | Spill (disk)       | 22.2 MiB       |

    Takeaways:
    - Skew on key 0: one task reads 892 M rows (~10x a normal key) and takes 13 min;
      the whole stage waits on that single task.
    - Median task reads 0 rows: only 100 distinct keys hashed into 200 partitions,
      so many partitions are empty and some get 2-3 keys (hash collisions).
    - Disk use stayed tiny (32.8 MiB shuffle, 22 MiB disk spill) thanks to zstd on very
      regular data; "Spill (memory)" is the in-memory size, not disk usage.


    """

    joined.count()


def demo_skew_join_aqe_optimized():
    spark.conf.set("spark.sql.adaptive.enabled", True)
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
    spark.conf.set(
        "spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5
    )  # skewed is 5x median
    spark.conf.set(
        "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "200m"
    )  # skewed <=> bigger than 200MB and size is 5 times bigger than median

    skewed_df = spark.range(10000000000).selectExpr(
        "CASE WHEN id < 800000000 THEN 0 ELSE id % 100 END as key", "id as value1"
    )

    uniform_df = spark.range(100).selectExpr("id as key", "id as value2")

    joined = skewed_df.join(uniform_df, "key")
    joined.explain()
    """
    == Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [key#2L, value1#3L, value2#9L]
   +- SortMergeJoin [key#2L], [key#8L], Inner
      :- Sort [key#2L ASC NULLS FIRST], false, 0
      :  +- Exchange hashpartitioning(key#2L, 200), ENSURE_REQUIREMENTS, [plan_id=29]
      :     +- Project [CASE WHEN (id#0L < 800000000) THEN 0 ELSE (id#0L % 100) END AS key#2L, id#0L AS value1#3L]
      :        +- Filter CASE WHEN (id#0L < 800000000) THEN true ELSE isnotnull((id#0L % 100)) END
      :           +- Range (0, 10000000000, step=1, splits=8)
      +- Sort [key#8L ASC NULLS FIRST], false, 0
         +- Exchange hashpartitioning(key#8L, 200), ENSURE_REQUIREMENTS, [plan_id=30]
            +- Project [id#6L AS key#8L, id#6L AS value2#9L]
               +- Range (0, 100, step=1, splits=8)

note the AdaptiveSparkPlan isFinalPlan=false

    """
    joined.count()


if __name__ == "__main__":
    # demo_coalescing_partitions()
    # demo_switching_to_broadcast_join()
    # demo_skew_join() # 23 min ???? bizarre
    demo_skew_join_aqe_optimized() # 30 min
    import time

    time.sleep(10000)
