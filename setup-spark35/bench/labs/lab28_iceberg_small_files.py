"""Core lab 28 — Iceberg small files + compaction (plan §7, M19/M20).

Since Iceberg 1.2 the Spark writer requests write.distribution-mode=hash on partitioned tables, which
re-shuffles and UNDOES a user repartition(). On an unpartitioned table nothing redistributes, so
repartition(N) produces N files. (Spark ignores distribution mode in CTAS/RTAS before 3.5.)
    baseline    : unpartitioned, repartition(2000) → 2000 small files; read query
    partitioned : partitioned by VendorID, same repartition(2000) → hash distribution → few files
    compacted   : baseline layout + rewrite_data_files → read query on compacted table
"""
from pyspark.sql import functions as F
import common as C

T = {"baseline": "lab.db.l28_small", "partitioned": "lab.db.l28_part", "compacted": "lab.db.l28_compacted"}
VARIANTS = {"baseline": {}, "partitioned": {}, "compacted": {}}
EXPECT = {"partitioned": {"data_files": ("<", 0.1, "x_baseline")}, "compacted": {"data_files": ("<", 0.05, "x_baseline")}}


def setup(spark):
    spark.sql("CREATE NAMESPACE IF NOT EXISTS lab.db")


def run(spark, variant):
    t = C.trips(spark).drop("pickup_date").repartition(2000)
    w = t.writeTo(T[variant]).using("iceberg")
    (w.partitionedBy(F.col("VendorID")) if variant == "partitioned" else w).createOrReplace()
    if variant == "compacted":
        spark.sql(f"CALL lab.system.rewrite_data_files(table => '{T[variant].split('.', 1)[1]}')").show()
    spark.table(T[variant]).groupBy("PULocationID").agg(F.sum("fare_amount")).write.format("noop").mode("overwrite").save()
    f = spark.table(T[variant] + ".files").agg(F.count("*").alias("n"), F.avg("file_size_in_bytes").alias("avg")).first()
    return {"data_files": f["n"], "avg_file_kb": round(f["avg"] / 1024, 1)}


def result(spark, variant):
    return spark.table(T[variant])
