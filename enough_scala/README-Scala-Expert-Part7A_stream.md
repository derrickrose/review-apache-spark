# ⚡ Scala Expert — Partie 7A : Structured Streaming + Kafka (Spark 4.0) — FR

**Objectif** : Construire un pipeline **temps réel** robuste sur **Apache Spark 4.0.0** avec **Kafka**, incluant : lecture/écriture, schémas JSON, **watermarks**, **window aggregations**, **checkpointing**, **exactly-once (idempotent)**, et **déploiement EMR/K8s**.

---

## 0) Prérequis & dépendances (sbt)

```scala
ThisBuild / scalaVersion := "3.4.2"
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "4.0.0",
  "org.apache.spark" %% "spark-sql-kafka-0-10" % "4.0.0",    // source/sink Kafka
  "ch.qos.logback"   %  "logback-classic" % "1.5.6"          // logs propres
)
```

> **Kafka côté cluster** : configure `bootstrap.servers`, topics, ACL/SSL si besoin.  
> **Spark 4** : Java 17/21, Scala 3.4+, Hadoop 3.3+ (cf. doc 5A/5B).

---

## 1) Modèle d’événement & schéma
Supposons un topic `rides` avec des messages JSON comme :
```json
{"rideId":123,"userId":45,"city":"FR","distanceKm":12.5,"price":20.0,"ts":"2025-10-22T12:03:45Z"}
```

Schéma Spark (StructType) :
```scala
import org.apache.spark.sql.types._

val rideSchema = new StructType()
  .add("rideId", LongType, false)
  .add("userId", LongType, false)
  .add("city", StringType, false)
  .add("distanceKm", DoubleType, false)
  .add("price", DoubleType, false)
  .add("ts", StringType, false) // on cast en Timestamp ensuite
```

---

## 2) Lecture Kafka (source) + parsing JSON

```scala
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

object KafkaStreamingApp:

  def main(args: Array[String]): Unit =
    val bootstrap = sys.env.getOrElse("KAFKA_BOOTSTRAP", "localhost:9092")
    val topic     = sys.env.getOrElse("KAFKA_TOPIC", "rides")
    val checkpoint= sys.env.getOrElse("CHECKPOINT", "s3a://miaradia-checkpoints/rides-stream/")
    val outDir    = sys.env.getOrElse("OUT_DIR", "s3a://miaradia-out/rides-agg/")

    val spark = SparkSession.builder()
      .appName("Miaradia-Rides-Streaming")
      .config("spark.sql.adaptive.enabled", "true")
      .getOrCreate()

    import spark.implicits._

    // 1) Lecture Kafka : key/value en binaire
    val raw = spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", bootstrap)
      .option("subscribe", topic)
      .option("startingOffsets", "latest") // "earliest" pour relecture
      .load()

    // 2) Parsing JSON → colonnes typées
    val rideSchema = new StructType()
      .add("rideId", LongType, false)
      .add("userId", LongType, false)
      .add("city", StringType, false)
      .add("distanceKm", DoubleType, false)
      .add("price", DoubleType, false)
      .add("ts", StringType, false)

    val rides = raw
      .selectExpr("CAST(value AS STRING) as json")
      .select(from_json(col("json"), rideSchema).as("r"))
      .select(
        col("r.rideId"), col("r.userId"),
        upper(col("r.city")).as("city"),
        col("r.distanceKm"), col("r.price"),
        to_timestamp(col("r.ts")).as("ts")
      )
      .withWatermark("ts", "10 minutes") // pour late data handling

    // 3) Aggrégation fenêtrée (revenue & distance moyenne par city, fenêtre 5 min)
    val agg = rides
      .groupBy(
        window(col("ts"), "5 minutes", "5 minutes"),
        col("city")
      )
      .agg(
        sum(col("price")).as("revenue"),
        avg(col("distanceKm")).as("avg_distance"),
        count(lit(1)).as("cnt")
      )
      .select(
        col("city"),
        date_format(col("window.start"), "yyyy-MM-dd HH:mm:ss").as("win_start"),
        date_format(col("window.end"), "yyyy-MM-dd HH:mm:ss").as("win_end"),
        col("revenue"), col("avg_distance"), col("cnt")
      )

    // 4) Écriture "append" en Parquet avec checkpointing (exactly-once côté sink Parquet si idempotent)
    val query = agg.writeStream
      .format("parquet")
      .outputMode("append")
      .option("path", outDir)
      .option("checkpointLocation", checkpoint)
      .trigger(processingTime = "5 seconds")
      .start()

    query.awaitTermination()
```

**Notes importantes :**
- Le **checkpoint** est **obligatoire** pour assurer la **tolérance aux pannes** et la gestion des offsets Kafka.  
- `withWatermark("ts","10 minutes")` permet d’évacuer l’état et d’ignorer les événements trop en retard (> 10 min).  
- `outputMode("append")` : standard pour fenêtres **tumbling** (5 min). Pour **sliding**, utilisez `update`/`complete` selon besoin.

---

## 3) Écriture vers Kafka (sink) — optionnel

```scala
val toKafka = rides
  .select(to_json(struct($"rideId",$"userId",$"city",$"distanceKm",$"price",$"ts")).as("value"))

val kafkaSinkQuery = toKafka.writeStream
  .format("kafka")
  .option("kafka.bootstrap.servers", bootstrap)
  .option("topic", "rides_enriched")
  .option("checkpointLocation", checkpoint + "/to-kafka")
  .start()
```

> **Astuce** : active **l’idempotence Kafka** côté broker/producer si tu cibles une **sémantique exactly-once** de bout en bout.

---

## 4) Validation & nettoyage (qualité en stream)

```scala
val cleaned = rides.filter($"price" >= 0.0 && $"distanceKm" >= 0.0 && $"city".isNotNull)
val anomalies = rides.except(cleaned) // lignes invalides
val anomaliesWrite = anomalies.writeStream
  .format("parquet")
  .option("path", s"$outDir/anomalies")
  .option("checkpointLocation", s"$checkpoint/anomalies")
  .outputMode("append")
  .start()
```

---

## 5) Déploiement — `spark-submit` (EMR & Kubernetes)

### 5.1 EMR (YARN)
```bash
spark-submit \
  --deploy-mode cluster \
  --class KafkaStreamingApp \
  --conf spark.sql.adaptive.enabled=true \
  --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
  s3://miaradia-artifacts/jars/miaradia-stream-assembly.jar
```

### 5.2 Kubernetes (Spark-on-K8s)
```bash
spark-submit \
  --master k8s://https://$K8S_API \
  --deploy-mode cluster \
  --name miaradia-streaming \
  --class KafkaStreamingApp \
  --conf spark.kubernetes.container.image=$REG/miaradia-spark:4.0.0 \
  --conf spark.sql.adaptive.enabled=true \
  local:///opt/spark/jars/miaradia-stream-assembly.jar
```

> **Sécurité** : pour Kafka TLS/SASL, ajoute `kafka.security.protocol`, `ssl.*` ou `sasl.*` via `.option(...)` sur la source Kafka.

---

## 6) Triggers & latence

- `trigger(processingTime = "5 seconds")` : micro-batch fixe.  
- `trigger(Trigger.Once())` : batch unique sur offsets courants (utile pour rattrapage).  
- **Continous processing** (faible latence) : options limitées, tests recommandés.

---

## 7) Bonnes pratiques (prod)

- **Checkpoint unique et durable** (HDFS/S3) par pipeline.  
- **Watermarks** pour bornes d’état, sinon fuite mémoire.  
- **Idempotence en sortie** : écriture partitionnée par temps (`date/hour`), ou clé naturelle pour éviter doublons.  
- **Surveiller** : StateStore size, inputRowsPerSecond, processedRowsPerSecond.  
- **AQE ON** + **coalesce en sortie** pour limiter les petits fichiers.  
- **Logs** : JSON + corrélation `queryId`, `batchId`.

---

## 8) Tests locaux & docker-compose (facultatif)

**docker-compose.yaml** (Kafka minimal) :
```yaml
version: '3.7'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.1
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
  kafka:
    image: confluentinc/cp-kafka:7.5.1
    depends_on: [zookeeper]
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports: ["9092:9092"]
```

**Générer des messages** (kafkacat) :
```bash
seq 1 10 | jq -c '{rideId:., userId:(.+100), city:"FR", distanceKm:12.3, price:20.0, ts:(now|todate)}' \
 | kcat -b localhost:9092 -t rides -P
```

---

## 9) Troubleshooting rapide

- **`StateStore memory leak / OOM`** : watermark absent ou trop grand → réduire la fenêtre, activer watermark.  
- **`Task killed / executor lost`** : partitions surdimensionnées → augmenter parallélisme ou réduire batch interval.  
- **`Too many small files`** : `coalesce` avant écriture, partitionner par date/heure.  
- **`Late data dropped`** : ajuster watermark selon SLA métier.

---

## 10) Extension (7B/7C/7D)

- **7B (Delta/Iceberg)** : remplacer l’écriture Parquet par **Delta** (`format("delta")`), ajouter `merge`, time travel.  
- **7C (MLlib)** : brancher un modèle de scoring en streaming (`foreachBatch`).  
- **7D (Observabilité)** : exporter métriques via Prometheus & OpenTelemetry.

**Fin — 7A.** Pipeline Kafka → Spark 4 → Parquet (fenêtres + watermark) prêt pour la prod.
