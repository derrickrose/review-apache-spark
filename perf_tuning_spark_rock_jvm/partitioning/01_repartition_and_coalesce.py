import time

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("Repartition and Coalesce")
    .master("local[*]")
    .getOrCreate()
)

sc = spark.sparkContext

numbers = sc.parallelize(range(1, 10_000_001))
print(numbers.getNumPartitions())  # number of virtual cores

# repartition
repartitioned_numbers = numbers.repartition(2)
repartitioned_numbers.count()

# coalesce - fundamentally different
coalesced_numbers = numbers.coalesce(2)  # for a smaller number of partitions
coalesced_numbers.count()

# force coalesce to be a shuffle
forced_shuffled_numbers = numbers.coalesce(2, shuffle=True)  # force a shuffle

if __name__ == "__main__":
    # keep the app alive to inspect the Spark UI at http://localhost:4040
    time.sleep(10_000_000)
