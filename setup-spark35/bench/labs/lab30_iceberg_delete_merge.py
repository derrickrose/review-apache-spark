"""Core lab 30 — Iceberg DELETE / MERGE: copy-on-write vs merge-on-read (plan §7, M20).

The default for DELETE/UPDATE/MERGE is copy-on-write (rewrite affected data files). merge-on-read
writes delete files instead (cheaper write, more expensive read until compaction).
Both variants must end with identical table contents.
"""
from pyspark.sql import functions as F
import common as C

TBL = {"baseline": "lab.db.l30_cow", "mor": "lab.db.l30_mor"}
MODE = {"baseline": "copy-on-write", "mor": "merge-on-read"}
VARIANTS = {"baseline": {}, "mor": {}}
EXPECT = {"mor": {"write_s": ("<", 0.8, "x_baseline"), "delete_files": (">", 0)}}


def setup(spark):
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lab.db")


def run(spark, variant):
    import time
    name, mode = TBL[variant], MODE[variant]
    (C.trips(spark).where(F.month("pickup_date") <= 3).drop("pickup_date")
     .writeTo(name).using("iceberg").partitionedBy(F.days("tpep_pickup_datetime"))
     .tableProperty("write.delete.mode", mode).tableProperty("write.update.mode", mode)
     .tableProperty("write.merge.mode", mode).createOrReplace())
    C.trips(spark).where("pickup_date = '2024-02-10'").select("VendorID", "tpep_pickup_datetime", "PULocationID") \
        .dropDuplicates(["VendorID", "tpep_pickup_datetime", "PULocationID"]).createOrReplaceTempView("l30_src")
    t0 = time.time()
    spark.sql(f"DELETE FROM {name} WHERE PULocationID = 132")
    spark.sql(f"DELETE FROM {name} WHERE PULocationID = 138")
    spark.sql(f"""MERGE INTO {name} t USING l30_src s
                  ON t.VendorID = s.VendorID AND t.tpep_pickup_datetime = s.tpep_pickup_datetime AND t.PULocationID = s.PULocationID
                  WHEN MATCHED THEN UPDATE SET t.tip_amount = 0""")
    write_s = time.time() - t0
    t1 = time.time()
    spark.table(name).groupBy("PULocationID").agg(F.sum("tip_amount")).write.format("noop").mode("overwrite").save()
    read_s = time.time() - t1
    return {"write_s": round(write_s, 2), "read_s": round(read_s, 2),
            "data_files": spark.table(name + ".data_files").count(),
            "delete_files": spark.table(name + ".delete_files").count()}


def result(spark, variant):
    return spark.table(TBL[variant]).select("VendorID", "tpep_pickup_datetime", "PULocationID", "fare_amount", "tip_amount")
