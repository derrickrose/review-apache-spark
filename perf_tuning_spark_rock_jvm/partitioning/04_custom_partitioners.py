import bisect
import random
import string
import time

from pyspark.core.rdd import (
    portable_hash,
)  # Spark 4.x; on Spark 3.x: from pyspark.rdd import portable_hash
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Partitioners").master("local").getOrCreate()

sc = spark.sparkContext

numbers = sc.parallelize(range(1, 10001))
print(numbers.partitioner)  # None: a plain (non key-value) RDD has no partitioner

# A partitioner is the logic that decides which record goes to which partition.
# Only pair RDDs (key, value) can carry a partitioner.
# DataFrames can also control partitioning (repartition(n, "col"),
# repartitionByRange, write.partitionBy, bucketBy), but a CUSTOM
# partitioning function is only possible on RDDs.
numbers3 = numbers.repartition(3)  # round-robin/random redistribution (full shuffle)
print(numbers3.partitioner)  # None: repartition does not set a partitioner

# Keeping track of the partitioner matters: a known partitioner lets Spark
# skip shuffles in later key-based operations (reduceByKey, join...).
keyed_numbers = numbers.map(lambda n: (n % 10, n))  # RDD[(int, int)], keys 0..9
print(keyed_numbers.partitioner)  # None: map() drops the partitioner (keys may change)
# use mapValues() to keep an existing partitioner

# ---------------------------------------------------------------------------
# HASH PARTITIONING
# partition = hash(key) % numPartitions
# PySpark has no HashPartitioner class: partitionBy(n) hashes keys with
# portable_hash (same behaviour as new HashPartitioner(3) in Scala,
# different hash function)
# ---------------------------------------------------------------------------
hashed_numbers = keyed_numbers.partitionBy(3, portable_hash)
print(hashed_numbers.partitioner)  # <pyspark.rdd.Partitioner ...>
"""
  - Equal keys always land in the same partition
  - No order between partitions (keys 1, 2, 3 can go to 3, 0, 2)
  - Cheap: no sampling step
  - Weakness: a very frequent key -> skewed partition
    (here: 10 distinct keys on 3 partitions -> partitions of unequal size)

  Use cases:
    combineByKey, groupByKey, aggregateByKey, foldByKey and reduceByKey
    hash-partition internally (shuffle). If the RDD is already partitioned
    with a matching partitioner, they skip the shuffle.

    Joins: if neither RDD has a partitioner, both are hash-partitioned (shuffled).
    If both are pre-partitioned with the same partitioner, the shuffle is avoided.

  Example, keys 1-8, 2 partitions (k % 2):
    P0: 2, 4, 6, 8   P1: 1, 3, 5, 7

  DataFrame equivalent: df.repartition(n, "col")
  
"""

# ---------------------------------------------------------------------------
# RANGE PARTITIONING
# Sample keys -> compute boundaries -> key goes to the partition whose range
# contains it
# PySpark has no RangePartitioner class either. sortByKey samples the keys,
# computes range boundaries and range-partitions the data internally,
# then sorts each partition (≈ new RangePartitioner(5) + sort)
# ---------------------------------------------------------------------------
ranged_numbers = keyed_numbers.sortByKey(numPartitions=5)
"""
  - Partitions are ordered: all keys in P0 < all keys in P1 < ...
  - Costs an extra pass over the data to sample keys; keys must be sortable
  - Balanced only as well as the sample is; a single very frequent key
    still can't be split across partitions

  Use cases: sorting (sortByKey, orderBy), range queries,
             balancing partitions when the key distribution is uneven

  Example, keys 1-8, 2 partitions (boundary 4):
    P0: 1, 2, 3, 4   P1: 5, 6, 7, 8

  DataFrame equivalent: df.repartitionByRange(n, "col") / df.orderBy("col")

  Keys within the same range end up in the same partition.
  Example: keys spread over 0-1000, 5 partitions, boundaries [200, 400, 600, 800]
    key <= 200        => partition 0
    200 < key <= 400  => partition 1
    400 < key <= 600  => partition 2
    600 < key <= 800  => partition 3
    key > 800         => partition 4
  (Spark computes the boundaries from a sample, so they follow the data
   distribution and are not necessarily evenly spaced.)
  Here keys are 0..9 on 5 partitions -> roughly 2 keys per partition.

  Range partitioning is how Spark does a global sort: range-partition, then
  sort each partition -> reading P0, P1, ... in order gives sorted data.
  sortByKey / orderBy do this internally; you don't partition beforehand.

  The resulting RDD does have a partitioner (ranged_numbers.partitioner is set),
  but PySpark compares partitioners by function object, and every sortByKey()
  builds a new boundary function -> a later sortByKey() shuffles again.
  
  
  => note that RangePartitioner is a prerequisite for a SORT.
  so that means in scala after repartitioning using RangePartitioner, if you perform a sortByKey(), Spark will not shuffle again.
"""
print(ranged_numbers.partitioner)  # <pyspark.rdd.Partitioner ...>

# Range partitioning WITHOUT the sort: give your own boundaries
# (boundaries must match the key domain: keys here are 0..9)
bounds = [2, 5, 7]  # gives 4 partitions: <=2 | 3-5 | 6-7 | >7
ranged_no_sort = keyed_numbers.partitionBy(4, lambda k: bisect.bisect_left(bounds, k))


# ---------------------------------------------------------------------------
# CUSTOM PARTITIONER
# ---------------------------------------------------------------------------
def generate_random_words(n_words, max_length):
    r = random.Random()
    alphabet = string.ascii_letters + string.digits
    return [
        # randrange(max_length) -> length 0..max_length-1 (empty words possible)
        "".join(r.choice(alphabet) for _ in range(r.randrange(max_length)))
        for _ in range(n_words)
    ]


random_words_rdd = sc.parallelize(generate_random_words(1000, 100))
# Goal: repartition this RDD by word length -> two words of the same length
# end up in the same partition.
# Custom computation = counting the occurrences of 'z' in every word
z_words_rdd = random_words_rdd.map(
    lambda word: (word, word.count("z"))
)  # RDD[(str, int)]


# In PySpark a custom partitioner is just a function key -> int;
# Spark applies `% numPartitions` to its result.
# (Scala equivalent: extend Partitioner, override numPartitions and getPartition)
def by_length_partitioner(key):
    return len(key)


# lengths are 0..99 and we use 100 partitions -> exactly one length per partition
by_length_z_words = z_words_rdd.partitionBy(100, by_length_partitioner)

if __name__ == "__main__":
    # Check which keys ended up in each partition
    # print(hashed_numbers.glom().map(lambda p: sorted({k for k, _ in p})).collect())
    # print(ranged_numbers.glom().map(lambda p: sorted({k for k, _ in p})).collect())
    # print(ranged_no_sort.glom().map(lambda p: sorted({k for k, _ in p})).collect())

    # foreachPartition runs on executors; in local mode output goes to the console
    def print_partition(it):
        for x in it:
            print(x)

    by_length_z_words.foreachPartition(print_partition)

    # Keep the app alive to inspect the Spark UI (http://localhost:4040)
    # BEFORE stopping it: after spark.stop() the UI is gone.
    time.sleep(10000)
    spark.stop()
