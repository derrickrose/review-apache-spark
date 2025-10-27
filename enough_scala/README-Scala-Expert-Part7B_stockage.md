
# 🧊 Scala Expert — Partie 7B : Lakehouse avec Delta Lake & Apache Iceberg (Spark 4.0) — FR

**Objectif :** Passer d’un pipeline Parquet classique à un **Lakehouse ACID** avec **Delta Lake** et **Apache Iceberg** sous **Spark 4.0** : `MERGE/UPSERT`, `TIME TRAVEL`, **schema evolution**, maintenance (OPTIMIZE/VACUUM), et bonnes pratiques (partitionnement, Z-Ordering, layout).

---

## 0) Prérequis & dépendances (sbt)

```scala
ThisBuild / scalaVersion := "3.4.2"
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "4.0.0",
  // Delta Lake (OSS)
  "io.delta" %% "delta-spark" % "3.2.0",
  // Iceberg (Spark runtime)
  "org.apache.iceberg" %% "iceberg-spark-runtime-3.5_2.13" % "1.6.1",
  "ch.qos.logback" % "logback-classic" % "1.5.6"
)
```

**Spark 4.0** : Java 17/21, Scala 3.4+, Hadoop 3.3+ (cf. matrices 5A/5B/Evolution).  
**Catalogues** : Delta/Parquet peuvent vivre sur S3/HDFS ; Iceberg recommande un **catalogue** (Glue/Hive/REST).

---

## 1) Delta Lake — bases et création

### 1.1 Créer une table Delta à partir d’un DataFrame
```scala
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

val spark = SparkSession.builder()
  .appName("Lakehouse-Delta")
  .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
  .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
  .getOrCreate()

val df = Seq(
  (1L, "FR", 12.5, 20.0, "2025-10-22T12:00:00Z"),
  (2L, "US",  8.0,  9.0, "2025-10-22T12:02:0Z")
).toDF("rideId","city","distanceKm","price","ts")

// Ecriture initiale Delta
df.write.format("delta").mode("overwrite").save("s3a://miaradia-lake/bronze/rides_delta")
```

### 1.2 Lecture & SQL
```scala
val deltaPath = "s3a://miaradia-lake/bronze/rides_delta"
val d = spark.read.format("delta").load(deltaPath)
d.createOrReplaceTempView("rides_delta")
spark.sql("SELECT city, SUM(price) revenue FROM rides_delta GROUP BY city").show()
```

---

## 2) Delta Lake — MERGE (UPSERT) et DELETE

### 2.1 Upserts (MERGE INTO)
```scala
// Nouvelles données (incrément)
val updates = Seq(
  (1L, "FR", 15.0, 23.0, "2025-10-22T12:10:00Z"), // mise à jour
  (3L, "MG", 10.0, 12.0, "2025-10-22T12:12:00Z")  // insertion
).toDF("rideId","city","distanceKm","price","ts")

import io.delta.tables._
val deltaTbl = DeltaTable.forPath(spark, deltaPath)

deltaTbl.as("t")
  .merge(
    updates.as("u"),
    "t.rideId = u.rideId"
  )
  .whenMatched()
    .updateExpr(Map("city" -> "u.city", "distanceKm" -> "u.distanceKm", "price" -> "u.price", "ts" -> "u.ts"))
  .whenNotMatched()
    .insertExpr(Map("rideId" -> "u.rideId", "city" -> "u.city", "distanceKm" -> "u.distanceKm", "price" -> "u.price", "ts" -> "u.ts"))
  .execute()
```

### 2.2 Deletes & updates ciblés
```scala
// Supprimer rides gratuits anciens
deltaTbl.delete("price = 0 AND ts < '2025-10-22T00:00:00Z'")

// Update ciblé
deltaTbl.updateExpr("city = 'FR'", Map("price" -> "price * 1.02"))
```

---

## 3) Delta Lake — Time Travel & History

```scala
// Historique des versions
spark.sql(s"DESCRIBE HISTORY delta.`$deltaPath`").show(truncate=false)

// Time travel par version
val v1 = spark.read.format("delta").option("versionAsOf", 1).load(deltaPath)

// Time travel par timestamp
val t = spark.read.format("delta")
  .option("timestampAsOf", "2025-10-22T12:05:00Z").load(deltaPath)
```

**Use-cases** : audits, debugging, reproduction ML, rollback de partitions.

---

## 4) Delta Lake — Maintenance (OPTIMIZE / VACUUM / Z-Order)

```text
-- OPTIMIZE (compacte petits fichiers) — nécessite Delta OPTIMIZE (selon dist.)
OPTIMIZE delta.`s3a://miaradia-lake/bronze/rides_delta` ZORDER BY (city, ts);

-- VACUUM (nettoyage des fichiers obsolètes)
VACUUM delta.`s3a://miaradia-lake/bronze/rides_delta` RETAIN 168 HOURS;
```

**Bonnes pratiques** :  
- Planifier **OPTIMIZE** régulier (évite “small files problem”)  
- **Z-Order** sur colonnes de filtres fréquents (ex. `city`, `ts`)  
- **VACUUM** après rétention légale/audit (par défaut 7 jours)

---

## 5) Delta Lake — Schema Evolution & Constraints

```scala
// Evolution de schéma automatique côté écriture
df.withColumn("currency", lit("EUR"))
  .write
  .format("delta")
  .mode("append")
  .option("mergeSchema", "true")
  .save(deltaPath)

// Contraintes (CHECK) — via SQL
spark.sql(s"""
  ALTER TABLE delta.`${deltaPath}`
  ADD CONSTRAINT price_nonnegative CHECK (price >= 0)
""")
```

> **Attention** : `mergeSchema` ajoute/ajuste les colonnes, à utiliser avec gouvernance (catalog/DDL).

---

## 6) Iceberg — Catalogues & création de tables

### 6.1 Configuration Spark (exemple Glue catalog)
```scala
val spark = SparkSession.builder()
  .appName("Lakehouse-Iceberg")
  .config("spark.sql.catalog.glue", "org.apache.iceberg.spark.SparkCatalog")
  .config("spark.sql.catalog.glue.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
  .config("spark.sql.catalog.glue.warehouse", "s3://miaradia-warehouse")
  .config("spark.sql.catalog.glue.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
  .getOrCreate()
```

### 6.2 Créer une table Iceberg (SQL)
```sql
CREATE TABLE glue.bronze.rides (
  rideId BIGINT,
  city STRING,
  distanceKm DOUBLE,
  price DOUBLE,
  ts TIMESTAMP
) PARTITIONED BY (days(ts));
```

### 6.3 Insertion & lecture
```sql
INSERT INTO glue.bronze.rides VALUES (1,'FR',12.5,20.0, TIMESTAMP '2025-10-22 12:00:00');
SELECT city, SUM(price) FROM glue.bronze.rides GROUP BY city;
```

---

## 7) Iceberg — SNAPSHOTS, BRANCHES & TIME TRAVEL

```sql
-- Historique des snapshots
CALL glue.system.snapshots('bronze.rides');

-- Lire un snapshot précis
SELECT * FROM glue.bronze.rides VERSION AS OF 1234567890;

-- Branches (ex: "dev" pour tests, "main" pour prod) — selon version
CALL glue.system.create_branch('bronze.rides', 'dev');

-- Time travel par timestamp
SELECT * FROM glue.bronze.rides TIMESTAMP AS OF TIMESTAMP '2025-10-22 12:05:00';
```

**Intérêt** : CI/CD data, expérimentation, rollback ciblé, reproductibilité ML.

---

## 8) Iceberg — MERGE, UPDATE, DELETE (ACID)

```sql
-- UPSERT Iceberg (MERGE)
MERGE INTO glue.bronze.rides t
USING glue.staging.rides_updates u
ON t.rideId = u.rideId
WHEN MATCHED THEN UPDATE SET t.price = u.price, t.distanceKm = u.distanceKm, t.ts = u.ts
WHEN NOT MATCHED THEN INSERT (rideId, city, distanceKm, price, ts)
VALUES (u.rideId, u.city, u.distanceKm, u.price, u.ts);

-- DELETE ciblé
DELETE FROM glue.bronze.rides WHERE price = 0 AND ts < TIMESTAMP '2025-10-22 00:00:00';
```

---

## 9) Iceberg — Maintenance (Rewrite, Expire, Compaction)

```sql
-- Compaction / rewrite files (réécrit petits fichiers → gros blocs)
CALL glue.system.rewrite_data_files('bronze.rides');

-- Expirer snapshots anciens (garder historique raisonnable)
CALL glue.system.expire_snapshots('bronze.rides', TIMESTAMP '2025-10-15 00:00:00');

-- Réécrire manifests & clustering de partition
CALL glue.system.rewrite_manifests('bronze.rides');
```

---

## 10) Bonnes pratiques Lakehouse (Delta & Iceberg)

- **Partitionnement** par **temps** (jour/heure) et/ou **clé requêtée** (ville) ; éviter trop de partitions.  
- **Layout** : `/{layer}/{domain}/{table}/dt=YYYY-MM-DD/` pour requêtes time-based.  
- **Small files** : planifier **OPTIMIZE** (Delta) / **rewrite_data_files** (Iceberg).  
- **Z-Order (Delta)** : accélère les filtres multi-colonnes.  
- **Catalog** : utiliser **Glue/Hive/REST** (Iceberg) pour gouvernance & transactions isolées.  
- **ACID** : préférer **MERGE** plutôt que job custom.  
- **Data Quality** : règles DQ (Deequ/GE) avant merge.  
- **Sécurité** : SSE-KMS sur S3, IAM policies minimales, audit logs.  
- **Coût** : coalesce en sortie, compression (ZSTD, Snappy), pruning activé.  

---

## 11) Intégration avec Streaming (rappel de 7A)

- **Delta** en Sink Streaming : `.format("delta").option("checkpointLocation", "...")` pour **exactly-once**.  
- **Iceberg** supporte **Spark Structured Streaming** (append/upsert) avec commit ACID.  
- **Watermarks** + **partitions temporelles** = taille d’état maîtrisée & requêtes rapides.

---

## 12) Migration Parquet → Lakehouse (pattern concret)

1) Écrire **la même table** en Delta/Iceberg (shadow write).  
2) **Valider** (counts, checksums, DQ).  
3) Basculer les **lecteurs** (`spark.read.format("delta"/"iceberg")`).  
4) Activer **MERGE** et **time travel**.  
5) Mettre en place **maintenance périodique** (OPTIMIZE/VACUUM ou rewrite/expire).

---

**Fin — 7B.** Vous avez un **Lakehouse ACID** (Delta & Iceberg) prêt pour la prod, compatible Spark 4.0.
