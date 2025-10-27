# 📈 Scala Expert — Partie 7D : Observabilité & Monitoring avancé (Spark 4.0) — FR

**Objectif** : Mettre en place une **observabilité de niveau production** pour Apache **Spark 4.0** : Spark UI/History, metrics Prometheus, dashboards Grafana, **OpenTelemetry**, **audit logging**, **correlation IDs**, alerting et autoscaling (EMR/K8s).

---

## 1) Spark UI & History Server (bases solides)

### 1.1 Démarrer avec les bonnes options
```bash
spark-submit   --conf spark.eventLog.enabled=true   --conf spark.eventLog.dir=s3a://miaradia-logs/spark-events   --conf spark.history.fs.logDirectory=s3a://miaradia-logs/spark-events   --conf spark.history.custom.executor.log.enabled=true   ...
```

**Bonnes pratiques**
- **Activer l’event log** pour toutes les applis (obligatoire pour History Server).
- Conserver **90 jours** minimum en prod (conformité interne).
- Sur K8s : monter un **PVC** ou pointer vers **S3/ADLS/GCS**.

### 1.2 Lire les bons écrans
- **Jobs/Stages** : temps, skew (tâches très longues), *shuffle read/write*, *spill*.  
- **SQL** : opérateurs **Exchange** (shuffle), **BroadcastHashJoin/SortMergeJoin**.  
- **Storage** : cache/persist (taille, niveau).  
- **Executors** : GC time, mémoire, *task time*, *input bytes*.

---

## 2) Structured Streaming UI (temps réel)
- **Input Rate** (`inputRowsPerSecond`) & **Process Rate** (`processedRowsPerSecond`).  
- **State Operators** : taille des stores, nombre de clés, latence.  
- **Watermark** : borne d’éviction, événements en retard.  
- **Batch Duration** : dérive si surcharge CPU/I/O.

```scala
spark.conf.set("spark.sql.streaming.ui.enabled", "true")
```

---

## 3) Metrics System → Prometheus

### 3.1 Activer les metrics
`metrics.properties` (packagé dans l’image/driver) :
```properties
*.sink.prometheusServlet.class=org.apache.spark.metrics.sink.PrometheusServlet
*.sink.prometheusServlet.path=/metrics
*.source.jvm.class=org.apache.spark.metrics.source.JvmSource

master.sink.prometheusServlet.path=/metrics/master
worker.sink.prometheusServlet.path=/metrics/worker
applications.sink.prometheusServlet.path=/metrics/applications
executor.sink.prometheusServlet.path=/metrics/executor
driver.sink.prometheusServlet.path=/metrics/driver
```

Spark submit :
```bash
--conf spark.metrics.conf=metrics.properties
--conf spark.ui.prometheus.enabled=true
```

### 3.2 Scrape Prometheus (exemple K8s)
`scrape-config` Prometheus :
```yaml
- job_name: 'spark'
  kubernetes_sd_configs:
    - role: pod
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: "true"
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      target_label: __meta_kubernetes_pod_container_port_number
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
```

Annoter les pods Spark :
```yaml
prometheus.io/scrape: "true"
prometheus.io/port: "4040"
prometheus.io/path: "/metrics"
```

### 3.3 Métriques clés à suivre
- **Executors** : `executorRunTime`, `jvmHeapUsed`, `executorCpuTime`.  
- **Shuffle** : `shuffleReadBytes`, `shuffleWriteBytes`, `diskBytesSpilled`.  
- **Streaming** : `inputRowsPerSecond`, `processedRowsPerSecond`, `stateOnCurrentVersionSizeBytes`.  
- **SQL** : `numRows`, `duration`, `scanTime`, `broadcastTime`.

---

## 4) Dashboards Grafana (exemples rapides)

### 4.1 Panneau — Throughput streaming
Expr Prometheus :
```
rate(spark_streaming_inputRate_total[1m])
```
Affiche les lignes/s entrantes.

### 4.2 Panneau — Latence batch
```
histogram_quantile(0.95, sum(rate(spark_streaming_batchDuration_milliseconds_bucket[5m])) by (le))
```

### 4.3 Panneau — GC time executor
```
rate(spark_executor_gcTime_seconds_total[5m])
```

### 4.4 Panneau — Shuffle spill
```
rate(spark_shuffle_diskBytesSpilled_total[5m])
```

**Conseils** : panels séparés pour **Executors**, **SQL**, **Streaming**, **Shuffle**. Variables de dashboard : `appId`, `jobId`, `stageId`.

---

## 5) OpenTelemetry (OTel) — traces & métriques unifiées

### 5.1 Export OTLP (driver/executor)
`spark-submit` :
```bash
--conf spark.executor.extraJavaOptions="-javaagent:/otel/opentelemetry-javaagent.jar   -Dotel.exporter.otlp.endpoint=http://otel-collector:4317   -Dotel.resource.attributes=service.name=spark-executor,service.namespace=miaradia"
--conf spark.driver.extraJavaOptions="-javaagent:/otel/opentelemetry-javaagent.jar   -Dotel.exporter.otlp.endpoint=http://otel-collector:4317   -Dotel.resource.attributes=service.name=spark-driver,service.namespace=miaradia"
```

### 5.2 Context propagation
- Ajouter `traceId` dans les logs (driver & executors).  
- Corréler avec `appId`, `stageId`, `taskId`.

---

## 6) Audit logging & logs structurés

### 6.1 Logback JSON (extrait)
`logback.xml` :
```xml
<configuration>
  <appender name="JSON" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>/var/log/spark/app.json</file>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <fileNamePattern>/var/log/spark/app.%d{yyyy-MM-dd}.json</fileNamePattern>
      <maxHistory>30</maxHistory>
    </rollingPolicy>
    <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
      <providers>
        <timestamp/>
        <pattern><pattern>
          {"level":"%level","logger":"%logger","message":"%msg",
           "mdc":%mdc,"thread":"%thread","appId":"%X{appId}",
           "stageId":"%X{stageId}","taskId":"%X{taskId}","traceId":"%X{traceId}"}
        </pattern></pattern>
      </providers>
    </encoder>
  </appender>
  <root level="INFO"><appender-ref ref="JSON"/></root>
</configuration>
```

### 6.2 Enrichir les MDC (SparkListener léger)
```scala
import org.apache.spark.scheduler._
spark.sparkContext.addSparkListener(new SparkListener {
  override def onStageSubmitted(s: SparkListenerStageSubmitted): Unit = {
    org.slf4j.MDC.put("stageId", s.stageInfo.stageId.toString)
  }
})
```

### 6.3 Audit SQL (simple)
```scala
spark.listenerManager.register(new org.apache.spark.sql.util.QueryExecutionListener {
  override def onSuccess(funcName: String, qe: org.apache.spark.sql.execution.QueryExecution, durationNs: Long): Unit = {
    val q = qe.simpleString
    println("{"event":"sql","duration_ms":%s,"query":"%s"}".format((durationNs/1e6).toString, q.take(500)))
  }
  override def onFailure(funcName: String, qe: org.apache.spark.sql.execution.QueryExecution, exception: Exception): Unit = {}
})
```

---

## 7) Alerting (Prometheus Alertmanager)

Règles d’alerte (exemples) :
```yaml
groups:
- name: spark-rules
  rules:
  - alert: SparkStreamingNoData
    expr: rate(spark_streaming_inputRate_total[5m]) < 1
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Streaming à l'arrêt"
      description: "Aucun message consommé depuis 10 min"

  - alert: SparkHighGCTime
    expr: rate(spark_executor_gcTime_seconds_total[5m]) > 5
    for: 15m
    labels: { severity: critical }
    annotations:
      summary: "GC time anormalement élevé"
      description: "Vérifier dimensionnement executors et taille partitions"

  - alert: SparkShuffleSpill
    expr: rate(spark_shuffle_diskBytesSpilled_total[10m]) > 1e9
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Beaucoup de spill sur disque"
      description: "Réduire partitions/activer AQE/broadcast"
```

---

## 8) Autoscaling (EMR & Kubernetes)

### 8.1 EMR
- **Instance Fleets** + règles **Managed Scaling** (CPU/Memory/Throughput).  
- Jobs batch → **step concurrency** et priorités.  
- Pour streaming → cluster **long‑running** + auto-recovery.

### 8.2 Spark-on-Kubernetes
- **Dynamic Allocation** :
```properties
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.initialExecutors=5
spark.dynamicAllocation.minExecutors=2
spark.dynamicAllocation.maxExecutors=80
```
- **Cluster Autoscaler** K8s pour ajouter/retirer des nœuds.  
- Limiter par **requests/limits** CPU/Mémoire pour des coûts stables.

---

## 9) Bonnes pratiques Observabilité (récap)

- **Event log ON** partout, rétention ≥ 90 j.  
- **Prometheus** : exporter driver/executors, dashboards dédiés SQL/Shuffle/Streaming.  
- **OTel** : tracer driver & executors, corréler avec `traceId/appId`.  
- **Logs JSON** : parsables, MDC enrichi, rotation & rétention.  
- **Alertes SLA** : throughput, latence, GC, spill, failed stages.  
- **Runbooks** : consignes pour `Shuffle fetch failed`, OOM, skew.  
- **Tests de charge** : valider dashboards & seuils avant go‑live.

---

## 10) Snippets prêts à l’emploi (résumé)

### spark-submit (K8s) avec Prometheus + OTel
```bash
spark-submit   --master k8s://https://$K8S_API   --deploy-mode cluster   --class com.miaradia.spark.App   --conf spark.metrics.conf=metrics.properties   --conf spark.ui.prometheus.enabled=true   --conf spark.executor.extraJavaOptions="-javaagent:/otel/otel-agent.jar -Dotel.exporter.otlp.endpoint=http://otel-collector:4317"   --conf spark.driver.extraJavaOptions="-javaagent:/otel/otel-agent.jar -Dotel.exporter.otlp.endpoint=http://otel-collector:4317"   local:///opt/spark/jars/app.jar
```

### Grafana : variables utiles
- `appId`, `jobId`, `stageId`, `executorId`  
- `namespace`, `pod` (K8s)

---

**Fin — 7D.** Tu disposes d’une **observabilité complète** (UI, metrics, traces, logs, alertes, autoscaling) pour Spark 4.0 en prod.
