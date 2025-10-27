# 08a-2 — Observabilité Structured Streaming (Spark 4.0) — FR

**Objectif :** Surveiller un pipeline **Kafka → Spark Structured Streaming → Delta/S3** en **production**, avec métriques clés, **dashboard Grafana étendu**, **alertes Prometheus**, code **Scala & PySpark**, et **bonnes pratiques**.

---

## 1) Architecture (vue d’ensemble)
```
Kafka (topic=rides) → Spark Structured Streaming (parse → agg) → Delta/S3
                                            ├─ UI /metrics (Prometheus)
                                            └─ Logs (Log4j2 JSON → EFK)
Grafana (dashboards) + Alertmanager (alertes)
```

---

## 2) Métriques clés Structured Streaming

| Indicateur | Ce que ça mesure | Source Prometheus (indicatif) |
|------------|------------------|-------------------------------|
| `inputRowsPerSecond` | Débit d’entrée | `spark_streaming_input_rows_total` (rate) |
| `processedRowsPerSecond` | Débit traité | `spark_streaming_processed_rows_total` (rate) |
| `batchDuration` | Latence par micro-batch | `spark_streaming_batch_duration_ms` |
| `eventTimeWatermark` | Retard max des events | `spark_streaming_event_time_watermark_seconds` |
| `stateOperators` | Taille de l’état (agg/join) | `spark_streaming_state_operators_*` |

PromQL utiles :  
```promql
# Débit entrant / traité (rows/s) par query
avg(rate(spark_streaming_input_rows_total[1m])) by (query)
avg(rate(spark_streaming_processed_rows_total[1m])) by (query)

# Latence moyenne batch (ms)
avg_over_time(spark_streaming_batch_duration_ms[5m]) by (query)

# Retard watermark (s) max observé
max by (query) (spark_streaming_event_time_watermark_seconds)
```

---

## 3) Configuration Spark (rappel essentiel)
Dans `metrics.properties` (cf. 08a-1), activer l’exposer **PrometheusServlet**.  
Conseils streaming :
```properties
spark.sql.shuffle.partitions=200            # adapter au débit
spark.sql.streaming.minBatchesToRetain=100 # debug
spark.sql.streaming.stateStore.providerClass=org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider
spark.sql.streaming.stopGracefullyOnShutdown=true
```

---

## 4) Dashboard Grafana — JSON étendu (extraits)

Panels recommandés :  
- Throughput Input/Processed, Batch Duration (p50/p95 si dispo), Watermark lag, Active Queries, State Rows, Failed Batches, Output Rows.  

Exemple (extraits JSON minimalistes) :
```json
{
  "title": "Spark Streaming — Miaradia",
  "panels": [
    { "type": "graph", "title": "Input Rows/s",
      "targets": [{ "expr": "avg(rate(spark_streaming_input_rows_total[1m])) by (query)" }] },
    { "type": "graph", "title": "Processed Rows/s",
      "targets": [{ "expr": "avg(rate(spark_streaming_processed_rows_total[1m])) by (query)" }] },
    { "type": "graph", "title": "Batch Duration (ms)",
      "targets": [{ "expr": "avg_over_time(spark_streaming_batch_duration_ms[5m]) by (query)" }] },
    { "type": "graph", "title": "Event Time Watermark (s)",
      "targets": [{ "expr": "max by (query) (spark_streaming_event_time_watermark_seconds)" }] }
  ]
}
```

---

## 5) Règles Prometheus & Alertes (YAML)

`rules-streaming.yml` :
```yaml
groups:
- name: spark-streaming
  rules:
  - alert: NoInputData
    expr: avg(rate(spark_streaming_input_rows_total[5m])) by (query) == 0
    for: 5m
    labels: { severity: warning }
    annotations:
      summary: "Streaming: plus d'input (5m)"
      description: "Query {{ $labels.query }} ne reçoit plus de données."

  - alert: HighBatchDuration
    expr: avg_over_time(spark_streaming_batch_duration_ms[5m]) by (query) > 30000
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Latence batch élevée"
      description: "Durée > 30s pour {{ $labels.query }}."

  - alert: WatermarkLagHigh
    expr: max by (query) (spark_streaming_event_time_watermark_seconds) > 900
    for: 10m
    labels: { severity: critical }
    annotations:
      summary: "Retard watermark"
      description: "Retard > 15 minutes sur {{ $labels.query }}."
```

Brancher ces règles dans Prometheus, avec Alertmanager (cf. 08a‑1 pour Slack/Email).

---

## 6) Exemple complet — Miaradia (Scala)

```scala
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._

val spark = SparkSession.builder().appName("Miaradia-Streaming").getOrCreate()

val schema = new StructType()
  .add("rideId", LongType).add("city", StringType)
  .add("distanceKm", DoubleType).add("price", DoubleType)
  .add("ts", StringType)

val input = spark.readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", sys.env.getOrElse("KAFKA_BOOTSTRAP", "kafka:9092"))
  .option("subscribe", "rides")
  .option("startingOffsets", "latest")
  .load()
  .selectExpr("CAST(value AS STRING) AS json")
  .select(from_json(col("json"), schema).as("r"))
  .select(col("r.*"))
  .withColumn("ts", to_timestamp(col("ts")))
  .withWatermark("ts", "10 minutes")

val agg = input
  .groupBy(window(col("ts"), "5 minutes"), col("city"))
  .agg(avg("price").as("avg_price"), sum("price").as("revenue"), count(lit(1)).as("cnt"))
  .select(col("city"),
          date_format(col("window.start"), "yyyy-MM-dd HH:mm:ss").as("win_start"),
          date_format(col("window.end"), "yyyy-MM-dd HH:mm:ss").as("win_end"),
          col("avg_price"), col("revenue"), col("cnt"))

val q = agg.writeStream
  .format("delta")
  .option("checkpointLocation", sys.env.getOrElse("CKPT", "s3a://miaradia-ckpt/streaming/rides"))
  .option("path", sys.env.getOrElse("OUT", "s3a://miaradia-lake/silver/rides_agg"))
  .outputMode("append")
  .trigger(processingTime = "10 seconds")
  .start()

q.awaitTermination()
```

---

## 7) Exemple équivalent — PySpark

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, window, avg, sum as ssum, count, date_format
from pyspark.sql.types import StructType, StructField, LongType, StringType, DoubleType

spark = SparkSession.builder.appName("Miaradia-Streaming-Py").getOrCreate()

schema = StructType([
    StructField("rideId", LongType()),
    StructField("city", StringType()),
    StructField("distanceKm", DoubleType()),
    StructField("price", DoubleType()),
    StructField("ts", StringType()),
])

inputDF = (spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "rides")
    .option("startingOffsets", "latest")
    .load()
    .selectExpr("CAST(value AS STRING) AS json")
    .select(from_json(col("json"), schema).alias("r"))
    .select("r.*")
    .withColumn("ts", to_timestamp(col("ts")))
    .withWatermark("ts", "10 minutes"))

agg = (inputDF.groupBy(window(col("ts"), "5 minutes"), col("city"))
       .agg(avg("price").alias("avg_price"), ssum("price").alias("revenue"), count("*").alias("cnt"))
       .select(col("city"),
               date_format(col("window.start"), "yyyy-MM-dd HH:mm:ss").alias("win_start"),
               date_format(col("window.end"), "yyyy-MM-dd HH:mm:ss").alias("win_end"),
               col("avg_price"), col("revenue"), col("cnt")))

q = (agg.writeStream
     .format("delta")
     .option("checkpointLocation", "s3a://miaradia-ckpt/streaming/rides")
     .option("path", "s3a://miaradia-lake/silver/rides_agg")
     .outputMode("append")
     .trigger(processingTime="10 seconds")
     .start())

q.awaitTermination()
```

---

## 8) Bonnes pratiques production

- **Checkpoint dédié** et persistant (S3/HDFS), **un par query**.  
- **Watermark** cohérent avec le **retard maximum** attendu.  
- **Tuning** `spark.sql.shuffle.partitions` vs débit et nombre de partitions Kafka.  
- **Backpressure** naturel avec triggers ; surveiller `processedRowsPerSecond`.  
- **Small files** : regrouper sorties (coalesce/OPTIMIZE Delta).  
- **Sécurité** : Kafka **SASL_SSL**, S3 **SSE‑KMS** ; limiter accès IAM.  
- **Observabilité** : panels Grafana + alertes ci‑dessus, logs JSON (EFK).

---

**Fin — 08a-2 Streaming Observability.**  
Étape suivante : **08a-3-Alerting-EFK.md** (Alertmanager + centralisation logs).