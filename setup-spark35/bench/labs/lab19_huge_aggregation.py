"""Core lab 19 — Huge aggregation (plan §7, M10). Scan → partial agg → Exchange → final agg → range Exchange → Sort.

    baseline   : AQE off, 8 shuffle partitions      → few huge reducers, aggregation spill risk
    aqe        : AQE on, 200 partitions coalesced   → balanced reducers
    partitions : AQE off, 400 partitions            → one variable (partition count) changed
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {
    "baseline": {"spark.sql.adaptive.enabled": "false", "spark.sql.shuffle.partitions": "8"},
    "aqe": {"spark.sql.adaptive.enabled": "true", "spark.sql.shuffle.partitions": "200"},
    "partitions": {"spark.sql.adaptive.enabled": "false", "spark.sql.shuffle.partitions": "400"},
}
EXPECT = {"aqe": {"max_task_ms": ("<", 0.6, "x_baseline")}}


def build(spark, variant):
    cc = C.common_crawl(spark)
    return (cc.groupBy("url_host_registered_domain")
              .agg(F.count("*").alias("pages"), F.avg("warc_record_length").cast("decimal(20,2)").alias("avg_len"))
              .orderBy(F.desc("pages")))
