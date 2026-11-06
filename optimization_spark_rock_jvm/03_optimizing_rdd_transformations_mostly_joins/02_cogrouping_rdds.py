"""
PySpark port of scala/part4rddjoins/CogroupingRDDs.scala
Notes: 02_cogrouping_to_read.md

Take all the student attempts:
  - if a student passed (best attempt >= 9.0), send them an email "PASSED"
  - else send them an email with "FAILED"
(Scala uses >= 9.0 here but > 9.0 in SimpleRDDJoins - kept as in the course.)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.rdd_data_generator import GENERATED  # noqa: E402
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

spark = get_spark("Cogrouping RDDs")
sc = spark.sparkContext
ROOT = GENERATED / "examData"


def _read(name, cast):
    return (
        sc.textFile(str(ROOT / name))
        .map(lambda line: line.split(" "))
        .map(lambda t: (int(t[0]), cast(t[1])))
    )


def read_ids():
    return _read("examIds.txt", str)


def read_exam_scores():
    return _read("examScores.txt", float)


def read_exam_emails():
    return _read("examEmails.txt", str)


def plain_join():
    scores = read_exam_scores().reduceByKey(max)
    candidates, emails = read_ids(), read_exam_emails()

    results = (
        candidates.join(scores)  # (id, (name, max_score))
        .join(emails)  # (id, ((name, max_score), email))  -> 2nd shuffle
        .mapValues(lambda v: (v[1], "PASSED") if v[0][1] >= 9.0 else (v[1], "FAILED"))
    )
    return results.count()


def cogrouped_join():
    scores = read_exam_scores().reduceByKey(max)
    candidates, emails = read_ids(), read_exam_emails()

    def decide(groups):
        # groups = (names, max_scores, emails), each a ResultIterable
        _names, max_scores, email_it = (list(g) for g in groups)
        if not email_it or not max_scores:  # Scala: for-comprehension over Options
            return None
        return email_it[0], "PASSED" if max_scores[0] >= 9.0 else "FAILED"

    # one shuffle stage co-partitioning the 3 RDDs
    # ⚠️ PySpark: cogroup(other, numPartitions) takes ONE other RDD (a 2nd RDD would be
    # taken as numPartitions). The N-way version of Scala's cogroup(a, b) is groupWith.
    result = candidates.groupWith(scores, emails).mapValues(decide)
    result.count()
    return (
        result.count()
    )  # 2nd count recomputes the lineage (nothing cached), as in the course


if __name__ == "__main__":
    timed("plain_join", plain_join)
    timed("cogrouped_join", cogrouped_join)
    keep_ui_open()
