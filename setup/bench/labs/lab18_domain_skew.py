"""Core lab 18 — Domain / key skew (plan §7, M09). Common Crawl domains are naturally Zipf-distributed.

    baseline : repartition(url_host_registered_domain)  → top domains overload their partitions
    rebalance: REBALANCE(domain) hint                    → AQE splits skewed partitions
Also run once: .groupBy("url_host_registered_domain").count().orderBy(F.desc("count")).show(20)
to name the exact hot keys (plan M09 method).
"""
import common as C

VARIANTS = {"baseline": {}, "rebalance": {}}
EXPECT = {"baseline": {"max_over_median": (">", 2)}, "rebalance": {"max_over_median": ("<", 0.7, "x_baseline")}}


def build(spark, variant):
    cc = C.common_crawl(spark).select("url", "url_host_registered_domain", "warc_record_length")
    k = "url_host_registered_domain"
    return cc.repartition(k) if variant == "baseline" else cc.hint("rebalance", k)
