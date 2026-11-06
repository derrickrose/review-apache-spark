"""
PySpark port of scala/part4rddjoins/SimpleRDDJoins.scala
Notes: 01_optimizing_rdd_joins_to_read.md

Goal: the number of students who passed the exam (= at least one attempt > 9.0).
Run `python -m common.rdd_data_generator` (from optimization_spark_rock_jvm/) first (writes generated_data/examData).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.rdd_data_generator import GENERATED  # noqa: E402
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

spark = get_spark("RDD joins")
sc = spark.sparkContext
ROOT = GENERATED / "examData"


def read_ids():
    # candidates are hash-partitioned up front (Scala: .partitionBy(new HashPartitioner(10)))
    return (
        sc.textFile(str(ROOT / "examIds.txt"))
        .map(lambda line: line.split(" "))
        .map(lambda t: (int(t[0]), t[1]))
        .partitionBy(10)
    )


def read_exam_scores():
    return (
        sc.textFile(str(ROOT / "examScores.txt"))
        .map(lambda line: line.split(" "))
        .map(lambda t: (int(t[0]), float(t[1])))
    )


def best(pair1, pair2):
    return pair1 if pair1[0] > pair2[0] else pair2


def plain_join():
    candidates, scores = read_ids(), read_exam_scores()
    joined = scores.join(candidates)  # (id, (score, name)) - every attempt is joined
    final = joined.reduceByKey(best).filter(lambda kv: kv[1][0] > 9.0)
    return final.count()


def pre_aggregate():
    candidates, scores = read_ids(), read_exam_scores()
    max_scores = scores.reduceByKey(max)  # 1 row per student before the join
    return max_scores.join(candidates).filter(lambda kv: kv[1][0] > 9.0).count()


def pre_filtering():
    candidates, scores = read_ids(), read_exam_scores()
    max_scores = scores.reduceByKey(max).filter(lambda kv: kv[1] > 9.0)
    return max_scores.join(candidates).count()


def co_partitioning():
    candidates, scores = read_ids(), read_exam_scores()
    # reuse the candidates' partitioning for the scores
    # (PySpark: same numPartitions + same partitionFunc (portable_hash) = same partitioner)
    n = candidates.getNumPartitions()
    repartitioned_scores = scores.partitionBy(n)
    joined = repartitioned_scores.join(candidates)
    final = joined.reduceByKey(best).filter(lambda kv: kv[1][0] > 9.0)
    return final.count()


def combined():
    candidates, scores = read_ids(), read_exam_scores()
    repartitioned_scores = scores.partitionBy(candidates.getNumPartitions())
    max_scores = repartitioned_scores.reduceByKey(max).filter(lambda kv: kv[1] > 9.0)
    return max_scores.join(candidates).count()


if __name__ == "__main__":
    print("candidates partitioner:", read_ids().partitioner)
    for fn in (plain_join, pre_aggregate, pre_filtering, co_partitioning, combined):
        timed(fn.__name__, fn)
    # compare the DAGs / shuffle read+write of the 5 jobs in the Spark UI
    keep_ui_open()
