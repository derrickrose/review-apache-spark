"""Core lab 25 — Python UDF vs native Spark (plan §7, M12).

    baseline : @udf row-at-a-time (pickle)       BatchEvalPython
    arrow    : @udf(useArrow=True)               ArrowEvalPython
    pandas   : @pandas_udf vectorized            ArrowEvalPython (Series → Series)
    native   : fare_amount * 0.20                no Python at all
"""
import pandas as pd
from pyspark.sql import functions as F
import common as C

VARIANTS = {"baseline": {}, "arrow": {}, "pandas": {}, "native": {}}
EXPECT = {"native": {"runtime_median_s": ("<", 0.3, "x_baseline")}, "pandas": {"runtime_median_s": ("<", 0.7, "x_baseline")}}


def _tip(f):
    return None if f is None else round(f * 0.20, 4)


@F.pandas_udf("double")
def _tip_pd(s: pd.Series) -> pd.Series:
    return (s * 0.20).round(4)


def build(spark, variant):
    t = C.trips(spark, ["fare_amount"])
    if variant == "native":
        tip = F.round(F.col("fare_amount") * F.lit(0.20), 4)
    elif variant == "pandas":
        tip = _tip_pd("fare_amount")
    else:
        tip = F.udf(_tip, "double", useArrow=(variant == "arrow"))("fare_amount")
    return t.select(tip.alias("tip"))
