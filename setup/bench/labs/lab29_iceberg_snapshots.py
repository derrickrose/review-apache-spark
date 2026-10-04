"""Core lab 29 — Iceberg snapshot / append explosion (plan §7, M20).

    baseline   : one append per day of Q1 (91 commits) → snapshots, manifests and metadata grow
    maintained : same appends + rewrite_manifests + expire_snapshots → planning cost falls back
Measured: commits, manifests, and the planning+read time of a point query after the writes.
"""
import time
from pyspark.sql import functions as F
import common as C

TBL = {"baseline": "lab.db.l29_appends", "maintained": "lab.db.l29_maintained"}
VARIANTS = {"baseline": {}, "maintained": {}}
EXPECT = {"maintained": {"manifests": ("<", 0.2, "x_baseline")}}


def setup(spark):
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lab.db")


def run(spark, variant):
    t = C.trips(spark).where(F.col("pickup_date").between("2024-01-01", "2024-03-31"))
    name = TBL[variant]
    t.limit(0).drop("pickup_date").writeTo(name).using("iceberg").createOrReplace()
    days = [r[0] for r in t.select("pickup_date").distinct().orderBy("pickup_date").collect()]
    for d in days:
        t.where(F.col("pickup_date") == d).drop("pickup_date").writeTo(name).append()
    if variant == "maintained":
        db_t = name.split(".", 1)[1]
        spark.sql(f"CALL lab.system.rewrite_manifests('{db_t}')")
        spark.sql(f"CALL lab.system.expire_snapshots(table => '{db_t}', older_than => TIMESTAMP '2999-01-01', retain_last => 1)")
    t0 = time.time()
    spark.table(name).where("PULocationID = 132").count()
    q = time.time() - t0
    return {"commits": len(days), "snapshots": spark.table(name + ".snapshots").count(),
            "manifests": spark.table(name + ".manifests").count(), "point_query_s": round(q, 2)}


def result(spark, variant):
    return spark.table(TBL[variant])
