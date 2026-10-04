"""Core lab 20 — String processing at scale (plan §7, M12/M13). Same logic, three execution paths.

    baseline : row-at-a-time Python UDF (BatchEvalPython in the plan, pickle serialization)
    arrow    : Arrow-optimized Python UDF (useArrow=True → ArrowEvalPython)
    native   : built-in functions (whole-stage codegen, no Python worker)
"""
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "arrow": {}, "native": {}}
EXPECT = {"native": {"runtime_median_s": ("<", 0.3, "x_baseline")}, "arrow": {"runtime_median_s": ("<", 1.0, "x_baseline")}}


def _py(url):
    if url is None:
        return None
    u = url.lower()
    host = u.split("/")[2] if u.count("/") >= 2 else ""
    camp = u.split("?ref=")[1] if "?ref=" in u else None
    return f"{host}|{len(u)}|{camp}"


def build(spark, variant):
    cc = C.common_crawl(spark).select("url")
    if variant == "native":
        u = F.lower("url")
        camp = F.when(F.instr(u, "?ref=") > 0, F.regexp_extract(u, r"\?ref=(.*)$", 1))
        out = F.concat_ws("|", F.split(u, "/").getItem(2), F.length(u).cast("string"), F.coalesce(camp, F.lit("None")))
    else:
        udf = F.udf(_py, "string", useArrow=(variant == "arrow"))
        out = udf("url")
    return cc.select(out.alias("parsed"))
