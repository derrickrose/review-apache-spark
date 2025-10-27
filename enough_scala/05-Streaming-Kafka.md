# 05 — Streaming Kafka (Spark 4.0) + Delta/S3 — FR

**Objectif :** Pipeline **temps réel** complet sur **Apache Spark 4.0** avec **Kafka** → **Delta/S3**, incluant : lecture sécurisée, parsing JSON, **watermark + fenêtres**, **checkpointing**, **exactly-once (idempotence)**, **déploiement** (local/EMR/K8s), **monitoring**, et **producteur Kafka** (simulateur).

---

## 1) Architecture (vue d’ensemble)
```
[Producers] → Kafka(topic=rides) → Spark Structured Streaming (parse→clean→aggregate) →
→ Sink Delta/S3 (bronze/silver/gold) → Analytics/BI/ML + Monitoring (Prometheus/Grafana)
```

- **Garantie** : au moins une fois (Kafka) + **idempotence** côté sink (Delta/partitionnement) ⇒ *effectivement exactly-once*.
- **Tolérance pannes** : `checkpointLocation` (offsets + state).

---

## 2) Kafka — Topics & sécurité

### 2.1 Création topic
```bash
kafka-topics.sh --bootstrap-server kafka:9092 --create --topic rides --partitions 6 --replication-factor 3
```

### 2.2 Connexion sécurisée (SASL_SSL)
Variables d’env attendues : `KAFKA_USER`, `KAFKA_PASS` (cf. 03b Secrets).

Client properties (côté Spark) :
```properties
kafka.security.protocol=SASL_SSL
kafka.sasl.mechanism=SCRAM-SHA-512
kafka.ssl.truststore.location=/opt/certs/truststore.jks
kafka.sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required   username="${KAFKA_USER}" password="${KAFKA_PASS}";
```

---

## 3) Lecture Kafka + parsing JSON (Spark 4.0)

### 3.1 Schéma d’événement
```scala
import org.apache.spark.sql.types._
val rideSchema = new StructType()
  .add("rideId", LongType, false)
  .add("userId", LongType, false)
  .add("city", StringType, false)
  .add("distanceKm", DoubleType, false)
  .add("price", DoubleType, false)
  .add("ts", StringType, false) // ISO-8601
```

### 3.2 Lecture & parsing
```scala
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

val spark = SparkSession.builder()
  .appName("Streaming-Kafka-Rides")
  .config("spark.sql.adaptive.enabled","true")
  .getOrCreate()

val bootstrap = sys.env.getOrElse("KAFKA_BOOTSTRAP", "kafka:9092")
val checkpoint= sys.env.getOrElse("CHECKPOINT", "s3a://miaradia-ckpt/rides/")
val outDelta  = sys.env.getOrElse("OUT_DELTA",  "s3a://miaradia-lake/silver/rides_agg")

val raw = spark.readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", bootstrap)
  .option("subscribe", "rides")
  .option("startingOffsets", "latest")
  .option("failOnDataLoss", "false")
  .load()

val rides = raw
  .selectExpr("CAST(value AS STRING) as json")
  .select(from_json(col("json"), rideSchema).as("r"))
  .select(
    col("r.rideId"), col("r.userId"),
    upper(col("r.city")).as("city"),
    col("r.distanceKm"), col("r.price"),
    to_timestamp(col("r.ts")).as("ts")
  )
  .withWatermark("ts", "10 minutes")
```

---

## 4) Transformations : fenêtres + agrégations

Fenêtre **tumbling** 5 min :
```scala
val agg = rides
  .groupBy(
    window(col("ts"), "5 minutes"),
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
```

---

## 5) Sink Delta + Checkpointing

```scala
val q = agg.writeStream
  .format("delta")
  .outputMode("append")
  .option("checkpointLocation", checkpoint)
  .option("path", outDelta)
  .trigger(processingTime = "5 seconds")
  .start()

q.awaitTermination()
```

> **Idempotence** : Delta ACID + partitionnement temporel (ajouter une colonne `date` si besoin) ⇒ pas de doublons à la relecture/retry.

---

## 6) Déploiement — Local, EMR, Kubernetes

### 6.1 Local (dev)
```bash
spark-submit   --class StreamingKafkaApp   --conf spark.sql.adaptive.enabled=true   target/scala-3.4/miaradia-stream-assembly.jar
```

### 6.2 EMR (YARN)
```bash
spark-submit   --deploy-mode cluster   --class StreamingKafkaApp   --conf spark.serializer=org.apache.spark.serializer.KryoSerializer   --conf spark.sql.adaptive.enabled=true   s3://miaradia-artifacts/jars/miaradia-stream-assembly.jar
```

### 6.3 Kubernetes (Spark-on-K8s)
```bash
spark-submit   --master k8s://$K8S_API   --deploy-mode cluster   --name streaming-kafka   --class StreamingKafkaApp   --conf spark.kubernetes.container.image=$REG/stream:4.0.0   --conf spark.sql.adaptive.enabled=true   local:///opt/spark/jars/miaradia-stream-assembly.jar
```

---

## 7) Monitoring & Observabilité

- **Streaming UI** : `inputRowsPerSecond`, `processedRowsPerSecond`, `stateOperators`.  
- **Prometheus** : activer `metrics.properties` + scrape Driver/Executors (cf. 7D).  
- **Alertes** : no data, GC time élevé, spill disque (cf. 7D/Alertmanager).

Listener simple :
```scala
import org.apache.spark.sql.streaming._
spark.streams.addListener(new StreamingQueryListener {
  override def onQueryStarted(e: StreamingQueryListener.QueryStartedEvent): Unit = println(s"Query ${e.name} started: ${e.id}")
  override def onQueryProgress(e: StreamingQueryListener.QueryProgressEvent): Unit = println(e.progress.prettyJson)
  override def onQueryTerminated(e: StreamingQueryListener.QueryTerminatedEvent): Unit = println(s"Query ${e.id} terminated")
})
```

---

## 8) Bonnes pratiques (prod)

- **Checkpoint dédié** par pipeline.  
- **Watermark** pour borner l’état (éviter OOM).  
- **Partitions Kafka** ≥ débit cible / `processedRowsPerSecond`.  
- **Failover** : `failOnDataLoss=false` si brokers tournent.  
- **Sortie** : coalesce/partitionnement raisonnable pour éviter **small files**.  
- **Sécurité** : SASL_SSL Kafka, SSE‑KMS S3 (cf. 03b).

---

## 9) Producteur Kafka (simulateur Scala)

```scala
// sbt: libraryDependencies += "org.apache.kafka" % "kafka-clients" % "3.7.0"
import java.util.Properties
import org.apache.kafka.clients.producer.{KafkaProducer, ProducerRecord}
import scala.util.Random
import java.time.Instant

object RidesProducer:
  def main(args: Array[String]): Unit =
    val props = new Properties()
    props.put("bootstrap.servers", sys.env.getOrElse("KAFKA_BOOTSTRAP","localhost:9092"))
    props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer")
    props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer")
    // TLS/SASL si besoin (voir 05 §2.2 / 03b)
    val producer = new KafkaProducer[String, String](props)

    val cities = Array("FR","US","DE","MG","UK")
    val rnd = new Random()

    while true do
      val rideId = rnd.nextInt(1_000_000)
      val userId = rnd.nextInt(100_000)
      val city   = cities(rnd.nextInt(cities.length))
      val dist   = 5 + rnd.nextDouble() * 20
      val price  = math.round((dist * (0.8 + rnd.nextDouble())) * 100) / 100.0
      val ts     = Instant.now().toString
      val json   = s"{\"rideId\":$rideId,\"userId\":$userId,\"city\":\"$city\",\"distanceKm\":$dist,\"price\":$price,\"ts\":\"$ts\"}"
      producer.send(new ProducerRecord[String, String]("rides", rideId.toString, json))
      Thread.sleep(100)
```
Run :
```bash
sbt "runMain RidesProducer"
```

---

## 10) Tests locaux (docker-compose)

```yaml
version: '3.7'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.1
    environment: { ZOOKEEPER_CLIENT_PORT: 2181 }
  kafka:
    image: confluentinc/cp-kafka:7.5.1
    depends_on: [zookeeper]
    ports: ["9092:9092"]
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

---

## 11) Checklist rapide

- [ ] `checkpointLocation` unique et persistant (S3/HDFS).  
- [ ] `withWatermark` configuré selon SLA (ex: 10 min).  
- [ ] Partitions Kafka suffisantes.  
- [ ] Coalesce/partitionnement sortie OK (pas de small files).  
- [ ] Sécurité : SASL_SSL Kafka, SSE‑KMS S3.  
- [ ] Monitoring/alertes branchés (Prometheus/Grafana).

---

**Fin — 05 Streaming Kafka.**  
Tu peux brancher directement 7B (Delta/Iceberg), 7C (ML), 7D (Observabilité).
