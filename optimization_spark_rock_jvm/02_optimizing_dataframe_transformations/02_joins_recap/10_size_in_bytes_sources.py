import os
import tempfile
from pyspark.sql import SparkSession, Row

# Doc : 00_joins_and_size_estimation.md, section 10 (d'où vient sizeInBytes)

spark = (
    SparkSession.builder.appName("sizeInBytes Sources").master("local[2]").getOrCreate()
)
sc = spark.sparkContext


def stats(df):
    s = df._jdf.queryExecution().optimizedPlan().stats()
    row_count = s.rowCount()
    return int(s.sizeInBytes().toString()), (
        row_count.get().toString() if row_count.isDefined() else None
    )


# Range : calcul arithmétique
print("range(1, 10)      :", stats(spark.range(1, 10)))  # attendu : (72, '9')

# RDD : taille inconnue → spark.sql.defaultSizeInBytes = Long.MaxValue, pas de rowCount
rdd_df = spark.createDataFrame(sc.parallelize([Row(id=1), Row(id=2)]))
print("RDD               :", stats(rdd_df))  # attendu : (9223372036854775807, None)

# createDataFrame(list) en PySpark : même chose que le RDD
print(
    "createDataFrame() :", stats(spark.createDataFrame([(1,), (2,)], ["id"]))
)  # attendu : Long.MaxValue

# Fichiers : taille sur disque
path = os.path.join(tempfile.mkdtemp(), "data.parquet")
spark.range(1, 1_000_000).selectExpr("id", "'abc' AS s").write.parquet(path)
disk = sum(
    os.path.getsize(os.path.join(d, f))
    for d, _, fs in os.walk(path)
    for f in fs
    if f.endswith(".parquet")
)
parquet_df = spark.read.parquet(path)
print("taille disque     :", disk)
print(
    "parquet           :", stats(parquet_df)
)  # attendu : ≈ taille disque, rowCount None

# fileCompressionFactor multiplie la taille disque
spark.conf.set("spark.sql.sources.fileCompressionFactor", "5")
print(
    "parquet × 5       :", stats(spark.read.parquet(path))
)  # attendu : ≈ 5 × taille disque
spark.conf.unset("spark.sql.sources.fileCompressionFactor")

# Cache : taille réelle en mémoire, une fois matérialisé
parquet_df.cache().count()
print(
    "parquet en cache  :", stats(parquet_df)
)  # attendu : taille du cache colonnaire (≠ disque)
