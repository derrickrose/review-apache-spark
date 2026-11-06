"""
PySpark port of scala/part5rddtransformations/I2ITransformations.scala (lesson part)
Notes: 05_iterator_to_iterator_transformations_to_read.md
Exercises: 06_i2i_transformations_exercises.py

Science project: each metric has an identifier and a value.
Return the smallest ("best") 10 metrics.

Run `python -m common.rdd_data_generator` (from optimization_spark_rock_jvm/) first (writes generated_data/metrics/metrics1m.txt).
"""

import heapq
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.rdd_data_generator import GENERATED  # noqa: E402
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

spark = get_spark("I2I Transformations")
sc = spark.sparkContext

LIMIT = 10
METRICS_PATH = GENERATED / "metrics" / "metrics1m.txt"  # course: metrics10m.txt


def read_metrics():
    return (
        sc.textFile(str(METRICS_PATH))
        .map(lambda line: line.split(" "))
        .map(lambda t: (t[0], float(t[1])))
    )


def top_metrics():
    # sorts the WHOLE RDD (range partitioning + shuffle of every record) to keep 10
    return read_metrics().sortBy(lambda kv: kv[1]).take(LIMIT)


def i2i_transformation(records):
    """
    Iterator -> iterator:
      - a NARROW transformation
      - consumes the iterator once, as a stream, keeping bounded state (10 items)
      - Spark can spill selectively because the partition is never held in memory
    Warning: don't traverse more than once or convert to a collection.

    Scala uses a mutable TreeSet trimmed to LIMIT; heapq.nsmallest does the same
    with a bounded heap (and keeps duplicate values, which a TreeSet ordered by
    value would silently merge).
    """
    return iter(heapq.nsmallest(LIMIT, records, key=lambda kv: kv[1]))


def top_metrics_i2i():
    return (
        read_metrics()
        .mapPartitions(i2i_transformation)  # top 10 per partition
        .repartition(1)  # tiny shuffle: 10 x numPartitions records
        .mapPartitions(i2i_transformation)  # global top 10
        .take(LIMIT)
    )


if __name__ == "__main__":
    a = timed("sortBy + take", top_metrics)
    b = timed("i2i", top_metrics_i2i)
    print("same top 10:", [v for _, v in a] == [v for _, v in b])
    for m in b:
        print(m)
    # built-in equivalent of the i2i version:
    # read_metrics().takeOrdered(LIMIT, key=lambda kv: kv[1])
    keep_ui_open()
