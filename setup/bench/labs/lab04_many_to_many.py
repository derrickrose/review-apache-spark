"""Core lab 04 — Many-to-many JOIN / join explosion (plan §7, M08/M15).

Rule: compute the expected output cardinality BEFORE running: Σ_k count_left(k) × count_right(k).
On the full year this self-join is ~10^13 rows, so the lab is bounded to ONE day.
    baseline : self-join on PULocationID only (duplicate keys on both sides)
    fixed    : add the real grain to the key (PULocationID + pickup hour + VendorID) — a different,
               intended result, so correctness is not compared (CHECK_CORRECTNESS = False)
"""
from pyspark.sql import functions as F
import common as C

DAY = "2024-03-15"
VARIANTS = {"baseline": {}, "fixed": {}}
CHECK_CORRECTNESS = False
EXPECT = {"fixed": {"output_rows": ("<", 0.05, "x_baseline")}}


def _sides(spark):
    t = C.trips(spark).where(F.col("pickup_date") == DAY)
    t = t.withColumn("h", F.hour("tpep_pickup_datetime"))
    left = t.select("PULocationID", "h", "VendorID", "tpep_pickup_datetime")
    right = t.select("PULocationID", "h", "VendorID", "tpep_dropoff_datetime")
    return left, right


def run(spark, variant):
    left, right = _sides(spark)
    keys = ["PULocationID"] if variant == "baseline" else ["PULocationID", "h", "VendorID"]
    cl = left.groupBy(*keys).count().withColumnRenamed("count", "cl")
    cr = right.groupBy(*keys).count().withColumnRenamed("count", "cr")
    expected = cl.join(cr, keys).select(F.sum(F.col("cl") * F.col("cr"))).first()[0]
    out = left.join(right, keys).count()
    assert out == expected, f"cardinality estimate {expected} != actual {out}"
    return {"input_rows": left.count(), "output_rows": out, "expansion": round(out / max(left.count(), 1), 1)}
