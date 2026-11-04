import tempfile
from pyspark.sql import SparkSession

# Doc : 00_joins_and_size_estimation.md, sections 9 (CBO) et 11 (effet des opérations)

spark = (
    SparkSession.builder.appName("Operations and CBO")
    .master("local[2]")
    .config("spark.sql.warehouse.dir", tempfile.mkdtemp())
    .getOrCreate()
)


def stats(df):
    s = df._jdf.queryExecution().optimizedPlan().stats()
    row_count = s.rowCount()
    return int(s.sizeInBytes().toString()), (
        row_count.get().toString() if row_count.isDefined() else None
    )


r = spark.range(1, 1_000_000)

# Sans CBO
print("range              :", stats(r))  # attendu : ~8 Mo
print(
    "filter id < 10     :", stats(r.filter("id < 10"))
)  # attendu : ~8 Mo (aucune réduction)
print(
    "select + colonne   :", stats(r.selectExpr("id", "'x' AS s"))
)  # attendu : ratio (8 + 8 + 20) / (8 + 8)

# Table catalogue + ANALYZE
r.selectExpr("id", "CAST(id % 100 AS STRING) AS s").write.saveAsTable("t")
t = spark.table("t")
print("table sans ANALYZE :", stats(t))  # attendu : taille disque, rowCount None

spark.sql("ANALYZE TABLE t COMPUTE STATISTICS")
print("ANALYZE (table)    :", stats(spark.table("t")))  # attendu : rowCount = 999999

spark.sql("ANALYZE TABLE t COMPUTE STATISTICS FOR COLUMNS id, s")
# statistiques de colonne : min, max, num_nulls, distinct_count, avg_col_len, max_col_len, histogram
spark.sql("DESCRIBE EXTENDED t id").show(truncate=False)
spark.sql("DESCRIBE EXTENDED t s").show(truncate=False)

# Avec CBO : le filtre réduit l'estimation
spark.conf.set("spark.sql.cbo.enabled", "true")
print(
    "CBO filter id < 10 :", stats(spark.table("t").filter("id < 10"))
)  # attendu : rowCount ≈ 10
spark.conf.set("spark.sql.cbo.enabled", "false")
print(
    "sans CBO, même filtre :", stats(spark.table("t").filter("id < 10"))
)  # attendu : pas de réduction

# Les stats ne se mettent pas à jour seules
spark.range(1, 1_000_000).selectExpr("id", "CAST(id AS STRING) AS s").write.mode(
    "append"
).saveAsTable("t")
spark.conf.set("spark.sql.cbo.enabled", "true")
# attendu (non vérifié) : avec spark.sql.statistics.size.autoUpdate.enabled=false (défaut), Spark efface
# les stats de la table après une écriture faite par Spark → rowCount None, retour à totalSize.
# Les stats restent vraiment périmées si les fichiers sont modifiés hors de Spark.
print("après append       :", stats(spark.table("t")))
