"""
PySpark port of scala/part5rddtransformations/ByKeyFunctions.scala
Notes: 02_by_key_functions_to_read.md

Scenario: a dataset of (word, occurrences) scraped from a big document.
We want the total per word, in a single map on the driver.
Compare the "Shuffle Write" of each job in the Spark UI.
"""

import random
import sys
from operator import add
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.rdd_data_generator import WORDS_FILE  # noqa: E402
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

spark = get_spark("By Key Functions", master="local[2]")
sc = spark.sparkContext

words = WORDS_FILE.read_text().split()
# 2M pairs built on the driver, then parallelized (same as Seq.fill in Scala)
word_counts = sc.parallelize(
    [(random.choice(words), random.randrange(1000)) for _ in range(2_000_000)]
).cache()
word_counts.count()  # materialize once so every job below starts from the same data

# the most intuitive solution can be the most dangerous:
#  - shuffles EVERY value so all data for a key lands on one machine
#  - a skewed key may not fit in an executor's memory -> OOM
group_by_key = (
    lambda: word_counts.groupByKey().mapValues(sum).collectAsMap()
)  # noqa: E731

# map-side partial aggregation, shuffles much less data
reduce_by_key = lambda: word_counts.reduceByKey(add).collectAsMap()  # noqa: E731

# like reduceByKey with a zero value
fold_by_key = lambda: word_counts.foldByKey(0, add).collectAsMap()  # noqa: E731

# zero + (agg, record) -> agg + (agg, agg) -> agg ; output type can differ (int -> float)
aggregate_by_key = lambda: word_counts.aggregateByKey(
    0.0, add, add
).collectAsMap()  # noqa: E731

# the most general one; also lets you choose the output partitioning
combine_by_key = lambda: word_counts.combineByKey(  # noqa: E731
    lambda count: count,  # createCombiner: value -> aggregate
    lambda total, v: total + v,  # mergeValue: inside a partition
    lambda t1, t2: t1 + t2,  # mergeCombiners: across partitions
    numPartitions=10,
).collectAsMap()

if __name__ == "__main__":
    results = [
        timed("groupByKey", group_by_key),
        timed("reduceByKey", reduce_by_key),
        timed("foldByKey", fold_by_key),
        timed("aggregateByKey", aggregate_by_key),
        timed("combineByKey", combine_by_key),
    ]
    print("all equal:", all(r == results[0] for r in results))
    keep_ui_open()
