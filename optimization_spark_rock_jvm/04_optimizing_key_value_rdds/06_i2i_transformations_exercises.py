"""
PySpark port of scala/part5rddtransformations/I2ITransformations.scala (exercises)
Notes: 06_iterator_to_iterator_transformations_exercises_to_read.md

Two "almost right" top-10 implementations: better than sortBy, worse than the i2i version
in 05_i2i_transformations.py.
"""

import heapq
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.rdd_data_generator import GENERATED  # noqa: E402
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

# Self-contained on purpose: importing 05_i2i_transformations works on the driver, but
# its functions are pickled *by reference* to that module, which the Python workers
# can't import (name starts with a digit) -> tasks fail.
spark = get_spark("I2I Transformations - Exercises")
sc = spark.sparkContext

LIMIT = 10
METRICS_PATH = GENERATED / "metrics" / "metrics1m.txt"
value = lambda kv: kv[1]  # noqa: E731


def read_metrics():
    return (
        sc.textFile(str(METRICS_PATH))
        .map(lambda line: line.split(" "))
        .map(lambda t: (t[0], float(t[1])))
    )


def i2i_transformation(records):
    """Reference solution from 05_i2i_transformations.py: stream, bounded state."""
    return iter(heapq.nsmallest(LIMIT, records, key=value))


def top_metrics_i2i():
    return (
        read_metrics()
        .mapPartitions(i2i_transformation)
        .repartition(1)
        .mapPartitions(i2i_transformation)
        .take(LIMIT)
    )


def top_metrics_ex1():
    """
    Better than the "dummy" approach:
      - not sorting the entire RDD
    Bad (worse than optimal):
      - sorting the entire partition
      - forcing the iterator in memory (list) -> can OOM the executors
    """
    per_partition = lambda it: iter(sorted(list(it), key=value)[:LIMIT])  # noqa: E731
    return (
        read_metrics()
        .mapPartitions(per_partition)
        .repartition(1)
        .mapPartitions(per_partition)
        .take(LIMIT)
    )


def top_metrics_ex2():
    """
    Better than ex1:
      - extracting the top 10 per partition instead of sorting the entire partition
    Bad because:
      - list(records) can still OOM the executors
      - iterating twice (building the list, then looping over it)
      - allocating a list cell per record (GC on the JVM / memory in Python)
    """

    def per_partition(records):
        limited = []  # kept sorted, at most LIMIT items (TreeSet in Scala)
        for record in list(records):  # <- the problem: materializes the partition
            limited.append(record)
            limited.sort(key=value)
            if len(limited) > LIMIT:
                limited.pop()
        return iter(limited)

    return (
        read_metrics()
        .mapPartitions(per_partition)
        .repartition(1)
        .mapPartitions(per_partition)
        .take(LIMIT)
    )


# The fix: drop list(...) and stream the iterator -> i2i_transformation (above)


if __name__ == "__main__":
    e1 = timed("ex1 sort each partition", top_metrics_ex1)
    e2 = timed("ex2 bounded, after list()", top_metrics_ex2)
    best = timed("i2i (reference)", top_metrics_i2i)
    print(
        "same top 10:", [v for _, v in e1] == [v for _, v in e2] == [v for _, v in best]
    )
    keep_ui_open()
