# 06b — Apache Iceberg (Spark 4.0) + Comparatif Delta vs Iceberg vs Hudi — FR

**Objectif :** Maîtriser **Apache Iceberg** sur **Spark 4.0** (catalog Glue/Hive, S3) : **CRUD**, **MERGE**, **snapshots/branches/tags**, **time travel/rollback**, **compaction/rewrite**, **streaming**, + **comparatif Delta vs Iceberg vs Hudi** et **checklist Lakehouse**.

---

## 0) Setup & prérequis (Spark 4.0)

### Dépendances (sbt)
```scala
ThisBuild / scalaVersion := "3.4.2"
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "4.0.0",
  "org.apache.iceberg" %% "iceberg-spark-runtime-3.5" % "1.6.1"   // adapter à spark 4 si binaire 3.5
)
```

### SparkSession (Glue catalog)
```scala
val spark = org.apache.spark.sql.SparkSession.builder()
  .appName("Iceberg-4.0")
  .config("spark.sql.catalog.glue", "org.apache.iceberg.spark.SparkCatalog")
  .config("spark.sql.catalog.glue.warehouse", "s3a://miaradia-warehouse/")
  .config("spark.sql.catalog.glue.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
  .config("spark.sql.catalog.glue.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
  .config("spark.sql.catalog.glue.client.factory", "org.apache.iceberg.aws.glue.GlueClientFactories$Default")
  .getOrCreate()
```

> 💡 *Alternative :* `spark.sql.catalog.local` avec `org.apache.iceberg.spark.SparkCatalog` + `hadoop` catalog (warehouse HDFS/S3).

---

## 1) CREATE / APPEND / READ (Scala + SQL)

### Scala (create & append)
```scala
import org.apache.spark.sql.functions._

import spark.implicits._
val df = Seq(
  (1L, "FR", 12.5, 20.0, "2025-10-22T12:00:00Z"),
  (2L, "US",  8.0,  9.0, "2025-10-22T12:02:00Z")
).toDF("rideId","city","distanceKm","price","ts").withColumn("ts", to_timestamp($"ts"))

df.writeTo("glue.bronze.rides_iceberg")
  .tableProperty("format-version","2")              // Iceberg v2 pour row-level ops
  .partitionedBy(years($"ts"), months($"ts"), bucket(16, $"city"))
  .createOrReplace()                                // crée si absent sinon remplace

val read = spark.table("glue.bronze.rides_iceberg")
read.show(false)
```

### SQL
```sql
CREATE TABLE glue.bronze.rides_iceberg (
  rideId BIGINT, city STRING, distanceKm DOUBLE, price DOUBLE, ts TIMESTAMP
)
USING iceberg
PARTITIONED BY (years(ts), months(ts), bucket(16, city))
TBLPROPERTIES ('format-version'='2');

SELECT city, SUM(price) revenue FROM glue.bronze.rides_iceberg GROUP BY city;
```

---

## 2) UPDATE / DELETE / MERGE (row-level ops)

### Scala
```scala
// UPDATE
spark.sql("UPDATE glue.bronze.rides_iceberg SET price = price * 1.02 WHERE city = 'FR'")

// DELETE
spark.sql("DELETE FROM glue.bronze.rides_iceberg WHERE price < 1 OR distanceKm IS NULL")

// MERGE (UPSERT)
val updates = Seq(
  (1L,"FR",15.0,23.0,"2025-10-22T12:10:00Z"),
  (3L,"MG",10.0,12.0,"2025-10-22T12:12:00Z")
).toDF("rideId","city","distanceKm","price","ts").withColumn("ts", to_timestamp($"ts"))

updates.createOrReplaceTempView("updates_v")
spark.sql("""
MERGE INTO glue.bronze.rides_iceberg t
USING updates_v u
ON t.rideId = u.rideId
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")
```

> ℹ️ Les **row-level operations** (UPDATE/DELETE/MERGE) nécessitent **Iceberg v2** et un moteur compatible (Spark 3.2+, OK pour Spark 4).

---

## 3) Snapshots, Time Travel, Branches/Tags

### Historique & time travel
```sql
-- Liste des snapshots
CALL glue.system.snapshots(table => 'bronze.rides_iceberg');

-- Lire une version spécifique
SELECT * FROM glue.bronze.rides_iceberg VERSION AS OF 1234567890123;

-- Ou par timestamp
SELECT * FROM glue.bronze.rides_iceberg TIMESTAMP AS OF '2025-10-22 12:05:00';
```

### Branches & tags (feature avancée)
```sql
-- Créer une branche depuis le snapshot courant
CALL glue.system.create_branch('bronze.rides_iceberg', branch => 'dev');

-- Tagger un snapshot
CALL glue.system.create_tag('bronze.rides_iceberg', tag => 'preprod', snapshot_id => 1234567890123);

-- Lire depuis une branche
SELECT * FROM glue.bronze.rides_iceberg VERSION AS OF BRANCH 'dev';

-- Rollback
CALL glue.system.rollback_to_snapshot('bronze.rides_iceberg', snapshot_id => 1234567890123);
```

> 🧭 Branches/Tags = **contrôle de versions** de table (tests, A/B, rollback).

---

## 4) Maintenance & optimisation

### Compaction / rewrite data files
```sql
-- Compacte les petits fichiers (bin-packing)
CALL glue.system.rewrite_data_files('bronze.rides_iceberg');

-- Réécrit les manifestes (améliore la découverte)
CALL glue.system.rewrite_manifests('bronze.rides_iceberg');

-- Expire snapshots anciens (libère stockage)
CALL glue.system.expire_snapshots('bronze.rides_iceberg', TIMESTAMP '2025-10-15 00:00:00');
```

### Partition & clustering
- Choisir **partitioning** d’abord par **temps** (année/mois/jour) + colonnes de filtre (ville).  
- Utiliser **bucket**/**truncate** pour la cardinalité élevée.  
- Ajuster **`write.distribution-mode`** (`hash`, `range`) si nécessaire.

---

## 5) Streaming (read/write)

### Write streaming vers Iceberg
```scala
val stream = spark.readStream
  .format("delta")
  .load("s3a://miaradia-lake/bronze/rides_delta_stream")

val query = stream
  .writeStream
  .format("iceberg")
  .option("checkpointLocation","s3a://miaradia-ckpt/iceberg_stream")
  .toTable("glue.silver.rides_iceberg_stream")
```

### Read streaming depuis Iceberg (micro-batch)
```scala
val readStreamIce = spark.readStream
  .format("iceberg")
  .load("glue.silver.rides_iceberg_stream")

val out = readStreamIce
  .writeStream
  .format("console")
  .start()
out.awaitTermination()
```

> ⚠️ Vérifier la version Iceberg/Spark pour les capacités exactes de **Structured Streaming** (sink/source) ; l’exemple ci‑dessus fonctionne en **micro‑batch** avec v1.4+.

---

## 6) Intégration S3 & Glue (prod)

- **IAM least privilege** (cf. 03a) : S3 + Glue + KMS.  
- **SSE‑KMS** pour les données (cf. 03b).  
- **Warehouse** unique (`s3a://.../warehouse/`) par environnement (dev/staging/prod).  
- **Rétention** : `expire_snapshots` planifié, `rewrite_data_files` périodique.  
- **Catalog strategy** : préférer **Glue** pour noms stables, IAM centralisé, intégration Athena.

---

## 7) Comparatif — Delta vs Iceberg vs Hudi

| Critère | **Delta Lake** | **Iceberg** | **Hudi** |
|---|---|---|---|
| ACID | Oui (Log + checkpoints) | Oui (snapshots) | Oui |
| Row-level ops (UPDATE/MERGE) | Oui | Oui (v2) | Oui (Copy-on-write/Merge-on-read) |
| Time Travel | Oui (version/timestamp) | Oui (snapshot/timestamp) | Oui (commit timeline) |
| Branches/Tags | Non (OSS), features Databricks | Oui (branches/tags) | Tags via timeline |
| Multi‑engine (Spark, Trino, Flink, Athena, Snowflake) | Très bon (mais certaines features spécifiques Databricks) | **Excellent** (standard de facto) | Bon (intégré Kafka connecteurs) |
| Streaming | Très bon (Delta + Spark) | Bon (micro‑batch, évolue vite) | **Fort** (ingestion rapide/upsert) |
| Optimisation fichiers | OPTIMIZE/Z‑Order | `rewrite_data_files`/`rewrite_manifests` | Compaction / clustering |
| Gouvernance/catalog | Hive/Unity Catalog/Glue | **Glue/Hive** (très fort multi‑engine) | Hive |
| Cas d’usage typiques | ETL/BI/ML Databricks, simplicité | **Data mesh**, multi‑engine, gouvernance | Ingestion **rapide** avec upsert (CDC) |

### Choisir selon ton contexte
- **Databricks centric / simplicité** → **Delta**.  
- **Multi‑engine (Trino/Athena/Snowflake) & data mesh** → **Iceberg**.  
- **Ingestion CDC/streaming upsert très volumétrique** → **Hudi**.  
- **Mix** possible (ex.: Bronze en Hudi → Silver/Gold en Iceberg/Delta).

---

## 8) Exercices pratiques

1) Créer `glue.bronze.rides_iceberg` (v2, partitions temps + bucket).  
2) Faire un **MERGE** (update/insert).  
3) Lister les **snapshots**, lire un **timestamp** antérieur.  
4) Créer une **branche** `dev`, y écrire, puis **rollback**.  
5) Lancer un **rewrite_data_files** et mesurer l’effet sur un `count()`.  
6) Écrire un **flux streaming** vers `glue.silver.rides_iceberg_stream` + lire en micro‑batch.

---

## 9) Checklist Lakehouse (Delta & Iceberg & Hudi)

- **Design bronze/silver/gold** (layout S3 + catalog Glue).  
- **Partitions temporelles** + colonnes de filtrage ; éviter sur‑partitionner.  
- **Compaction périodique** (OPTIMIZE / rewrite / clustering).  
- **Rétention snapshots** : politique claire (30–90j).  
- **Sécurité** : IAM least privilege, **SSE‑KMS**, audit logs.  
- **Governance** : tables **cataloguées** (Glue/Unity) + lineage (OpenLineage).  
- **Streaming** : checkpoints dédiés + idempotence (exactly‑once logique).

---

**Fin — 06b Iceberg (Spark 4.0) + Comparatif.**  
Tu peux lier ce module avec `05-Streaming-Kafka.md` (source) et `07-MLlib-MLflow.md` (scoring).