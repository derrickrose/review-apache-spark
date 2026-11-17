import time

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("Partitioning Problems")
    .master("local[*]")  # for parallelism
    # default driver heap (1g) is too small to cache 400MB partitions -> OOM
    # must be set before the JVM starts, i.e. here, not via spark.conf.set
    .config("spark.driver.memory", "8g")
    .getOrCreate()
)

sc = spark.sparkContext


def process_numbers(n_partitions: int) -> None:
    numbers = spark.range(100_000_000)  # ~800MB
    repartitioned_numbers = numbers.repartition(n_partitions)
    repartitioned_numbers.cache()
    repartitioned_numbers.count()
    # the goal is to mesure how long does it take to count the aggregation depending on the number of parititons
    # the computation I care about
    # note that the act or repartitioning without the cache will be included in the show job
    # here is to isolate the computation of aggregation
    repartitioned_numbers.selectExpr("sum(id)").show()
    # free the cache so later runs don't compete for memory
    # repartitioned_numbers.unpersist()


# 1 - use size estimator
def df_size_estimator() -> None:
    numbers = spark.range(100_000)
    # SizeEstimator has no Python API: call the JVM class through py4j on the
    # underlying Java Dataset object (numbers._jdf).
    size_estimator = spark._jvm.org.apache.spark.util.SizeEstimator
    # usually works, not super accurate, within an order of magnitude - larger number
    # measures the memory footprint of the actual JVM object backing the dataset
    print(size_estimator.estimate(numbers._jdf))
    numbers.cache()
    numbers.count()


# 2 - use query plan
def estimate_with_query_plan() -> None:
    numbers = spark.range(100_000)
    # accurate size in bytes for the DATA (queryExecution is JVM-only, reached via py4j)
    print(numbers._jdf.queryExecution().optimizedPlan().stats().sizeInBytes())


def estimate_rdd() -> None:
    numbers = sc.parallelize(range(1, 100_001))
    # note: a PySpark RDD is cached as pickled Python objects, so the size shown
    # in the Storage tab differs from the Scala RDD[Int] version
    numbers.cache().count()


if __name__ == "__main__":
    # process_numbers(2)  # 400MB / partition
    # process_numbers(20)  # 40MB / partition
    # process_numbers(200)  # 4MB / partition
    # process_numbers(2000)  # 400KB / partition
    # process_numbers(20000)  # 40KB / partition

    # df_size_estimator()
    # estimate_with_query_plan()
    estimate_rdd()

    # 10-100MB rule for partition size for UNCOMPRESSED DATA

    # UPDATE - Spark 4 introduces spark.sql.maxSinglePartitionBytes (default 128MB)
    # This enforces a hard cap on partition size. Previously partitions could grow unbounded.
    # Jobs with very large partitions will now automatically get more partitions.
    # Override with: spark.conf.set("spark.sql.maxSinglePartitionBytes", "268435456")  # 256MB

    # keep the app alive to inspect the Spark UI at http://localhost:4040
    time.sleep(10_000_000)
