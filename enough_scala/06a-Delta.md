# 06a — Delta Lake (Spark 4.0) — Scala + SQL — FR

**Objectif :** Mettre en place un **Lakehouse ACID** avec **Delta Lake** sur **Spark 4.0** : CRUD, **MERGE/UPSERT**, **Time Travel**, **Schema Evolution**, **Maintenance (OPTIMIZE/VACUUM)**, **Streaming**, **S3 + Glue**. Chaque section inclut **Scala & SQL** + un **exercice pratique**.

---

## 0) Prérequis (sbt & conf Spark)

```scala
ThisBuild / scalaVersion := "3.4.2"
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "4.0.0",
  "io.delta" %% "delta-spark" % "3.2.0"
)
```
`spark-submit` / `SparkSession` :
```scala
val spark = SparkSession.builder()
  .appName("Delta-4.0")
  .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
  .config("spark.sql.catalog.spark_catalog","org.apache.spark.sql.delta.catalog.DeltaCatalog")
  .getOrCreate()
```

---

## 1) CREATE / READ (Scala & SQL)

### Scala
```scala
import org.apache.spark.sql.functions._

val base = Seq(
  (1L,"FR",12.5,20.0,"2025-10-22T12:00:00Z"),
  (2L,"US", 8.0, 9.0,"2025-10-22T12:02:00Z")
).toDF("rideId","city","distanceKm","price","ts")

val path = "s3a://miaradia-lake/bronze/rides_delta"
base.write.format("delta").mode("overwrite").save(path)

val df = spark.read.format("delta").load(path)
df.createOrReplaceTempView("rides_delta")
```

### SQL
```sql
CREATE TABLE delta.`s3a://miaradia-lake/bronze/rides_delta`
( rideId BIGINT, city STRING, distanceKm DOUBLE, price DOUBLE, ts TIMESTAMP );

SELECT city, SUM(price) AS revenue FROM delta.`s3a://miaradia-lake/bronze/rides_delta` GROUP BY city;
```

### 🎯 Exercice
1) Crée la table Delta ci-dessus. 2) Lis-la et affiche les 5 premières lignes. 3) Compte les rides par `city`.

---

## 2) UPDATE & DELETE

### Scala
```scala
import io.delta.tables._
val delta = DeltaTable.forPath(spark, path)

delta.updateExpr("city = 'FR'", Map("price" -> "price * 1.02"))
delta.delete("price = 0 OR distanceKm IS NULL")
```

### SQL
```sql
UPDATE delta.`s3a://miaradia-lake/bronze/rides_delta` SET price = price * 1.02 WHERE city = 'FR';
DELETE FROM delta.`s3a://miaradia-lake/bronze/rides_delta` WHERE price = 0 OR distanceKm IS NULL;
```

### 🎯 Exercice
Met à jour tous les rides en `US` en augmentant `price` de 5 %, supprime ceux < 1€.

---

## 3) MERGE INTO (UPSERT) — incrémental

### Scala
```scala
val updates = Seq(
  (1L,"FR",15.0,23.0,"2025-10-22T12:10:00Z"), // UPDATE (rideId=1)
  (3L,"MG",10.0,12.0,"2025-10-22T12:12:00Z")  // INSERT (rideId=3)
).toDF("rideId","city","distanceKm","price","ts")

delta.as("t")
  .merge(
    updates.as("u"),
    "t.rideId = u.rideId"
  )
  .whenMatched().updateExpr(Map(
    "city" -> "u.city",
    "distanceKm" -> "u.distanceKm",
    "price" -> "u.price",
    "ts" -> "u.ts"
  ))
  .whenNotMatched().insertExpr(Map(
    "rideId" -> "u.rideId","city"->"u.city","distanceKm"->"u.distanceKm","price"->"u.price","ts"->"u.ts"
  ))
  .execute()
```

### SQL
```sql
MERGE INTO delta.`s3a://miaradia-lake/bronze/rides_delta` t
USING (SELECT 1 AS rideId,'FR' AS city,15.0 AS distanceKm,23.0 AS price, TIMESTAMP '2025-10-22 12:10:00' AS ts
       UNION ALL SELECT 3,'MG',10.0,12.0, TIMESTAMP '2025-10-22 12:12:00') u
ON t.rideId = u.rideId
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

### 🎯 Exercice
Ajoute un 4e ride (insert) et modifie le 2e (update). Vérifie les résultats.

---

## 4) Time Travel & History

### Scala
```scala
spark.sql(s"DESCRIBE HISTORY delta.`$path`").show(truncate=false)
val v1  = spark.read.format("delta").option("versionAsOf", 1).load(path)
val tAs = spark.read.format("delta").option("timestampAsOf","2025-10-22T12:05:00Z").load(path)
```

### SQL
```sql
DESCRIBE HISTORY delta.`s3a://miaradia-lake/bronze/rides_delta`;
SELECT * FROM delta.`s3a://miaradia-lake/bronze/rides_delta@v1`;
```

### 🎯 Exercice
Restaure la version **avant** le MERGE et compare les counts par `city`.

---

## 5) Schema Evolution & Constraints

### Scala
```scala
val withCurrency = base.withColumn("currency", lit("EUR"))
withCurrency.write.format("delta").mode("append").option("mergeSchema","true").save(path)
spark.sql(s"ALTER TABLE delta.`$path` ADD CONSTRAINT nonneg CHECK (price >= 0)")
```

### SQL
```sql
ALTER TABLE delta.`s3a://miaradia-lake/bronze/rides_delta`
SET TBLPROPERTIES ('delta.minReaderVersion'='2','delta.minWriterVersion'='7');
ALTER TABLE delta.`s3a://miaradia-lake/bronze/rides_delta`
ADD CONSTRAINT nonneg CHECK (price >= 0);
```

### 🎯 Exercice
Ajoute une colonne `payment` (STRING) via `mergeSchema`, puis crée une contrainte `distanceKm > 0`.

---

## 6) Maintenance : OPTIMIZE / Z-ORDER / VACUUM

> Objectif : réduire **small files**, améliorer le **pruning** et la **localité** des données.

### SQL (Databricks/Delta OSS selon dist.)
```sql
OPTIMIZE delta.`s3a://miaradia-lake/bronze/rides_delta` ZORDER BY (city, ts);
VACUUM  delta.`s3a://miaradia-lake/bronze/rides_delta` RETAIN 168 HOURS;
```

### Scala (compaction simple alternative)
```scala
val compacted = spark.read.format("delta").load(path).coalesce(32)
compacted.write.format("delta").mode("overwrite").option("overwriteSchema","true").save(path)
```

### 🎯 Exercice
Mesure le temps d’un `count()` avant/après OPTIMIZE. Observe `DESCRIBE HISTORY`.

---

## 7) Intégration S3 + Glue Catalog

### Spark conf (Glue metastore)
```properties
spark.sql.catalogImplementation=hive
hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory
```

### SQL — Table managée par Glue
```sql
CREATE TABLE glue.bronze.rides_delta
USING DELTA
LOCATION 's3a://miaradia-lake/bronze/rides_delta';
```

### 🎯 Exercice
Enregistre la table dans **Glue**, puis requête-la via `spark.sql("SELECT ... FROM glue.bronze.rides_delta")`.

---

## 8) Structured Streaming (read → write Delta)

### Scala
```scala
val stream = spark.readStream.format("delta").load(path)
val out    = "s3a://miaradia-lake/silver/rides_streamed"

val query = stream
  .withWatermark("ts","10 minutes")
  .groupBy(window(col("ts"),"5 minutes"), col("city"))
  .agg(sum("price").as("revenue"))
  .writeStream
  .format("delta")
  .option("checkpointLocation","s3a://miaradia-ckpt/rides_streamed")
  .option("path", out)
  .outputMode("append")
  .start()
query.awaitTermination()
```

### 🎯 Exercice
Change la fenêtre (10 min), ajoute `avg(distanceKm)`, vérifie l’idempotence après restart (`checkpointLocation`).

---

## 9) Bonnes pratiques (prod)

- **Partitionnement** par **date/heure** + colonnes de filtre fréquentes.  
- **Small files** : planifie **OPTIMIZE** / compaction régulière.  
- **Z-Order** sur colonnes de prédicats (`city`, `ts`).  
- **ACID** : préférer **MERGE** pour l’incrémental.  
- **Gouvernance** : tables dans **Glue** pour noms stables + permissions IAM.  
- **Coût/perf** : compression Snappy/ZSTD, `maxRecordsPerFile`, `spark.sql.shuffle.partitions` adapté.  
- **Sécurité** : **SSE-KMS** S3, IAM least privilege, audit (event logs).

---

## 🔬 Mini-projet guidé (récap)

1) **Créer** la table Delta (1).  
2) **Faire** un **MERGE** incrémental (3).  
3) **Explorer** l’historique & **time travel** (4).  
4) **Évoluer** le schéma + **contraintes** (5).  
5) **Optimiser** (OPTIMIZE/VACUUM) (6).  
6) **Cataloguer** dans **Glue** (7).  
7) **Streamer** vers une table agrégée Delta (8).

---

**Fin — 06a Delta Lake (Spark 4.0).**  
Prochain : **06b-Iceberg.md** (+ comparatif Delta vs Iceberg vs Hudi).
