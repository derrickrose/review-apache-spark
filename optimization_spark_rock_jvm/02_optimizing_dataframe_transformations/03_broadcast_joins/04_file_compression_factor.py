import os
import tempfile
from pyspark.sql import SparkSession

# Doc : 00_broadcast_joins.md, section 4 (fichiers compressés et fileCompressionFactor)

spark = (
    SparkSession.builder.appName("File Compression Factor")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)


def size_in_bytes(df):
    return int(
        df._jdf.queryExecution().optimizedPlan().stats().sizeInBytes().toString()
    )


# données très compressibles : peu de valeurs distinctes répétées
path = os.path.join(tempfile.mkdtemp(), "lookup.parquet")
(
    spark.range(1, 2_000_000)
    .selectExpr(
        "id", "CAST(id % 10 AS STRING) AS category", "'constant value' AS label"
    )
    .write.parquet(path)
)

disk = sum(
    os.path.getsize(os.path.join(d, f))
    for d, _, fs in os.walk(path)
    for f in fs
    if f.endswith(".parquet")
)
lookup = spark.read.parquet(path)
estimate = size_in_bytes(lookup)

cached = spark.read.parquet(path)
cached.cache().count()
in_memory = size_in_bytes(cached)
cached.unpersist()

print(f"disque : {disk}, estimation : {estimate}, en mémoire (cache) : {in_memory}")
print(f"ratio mémoire / disque : {in_memory / disk:.1f}")
# attendu : estimation ≈ disque. Le ratio réel dépend des données : le cache est lui aussi compressé
# (spark.sql.inMemoryColumnarStorage.compressed=true), donc il peut être proche de 1.
# C'est ce ratio qu'il faut utiliser comme facteur en vrai.

big = spark.range(1, 50_000_000)

# seuil placé juste au-dessus de la taille disque : Spark broadcast
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(int(estimate * 1.5)))
# attendu : BroadcastHashJoin
big.join(spark.read.parquet(path), "id").explain()

# facteur 5 (fixe, pour que la démo bascule quel que soit le ratio réel) : 5 × disque > 1.5 × disque
spark.conf.set("spark.sql.sources.fileCompressionFactor", "5")
print("estimation avec facteur :", size_in_bytes(spark.read.parquet(path)))
# attendu : SortMergeJoin
big.join(spark.read.parquet(path), "id").explain()
