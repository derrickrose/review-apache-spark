# 08a-1 — Metrics Core (Spark 4.0 + Prometheus + Grafana) — FR

**Objectif :** Activer les **métriques Spark 4.0** et les exposer pour **Prometheus** puis **Grafana**.  
Ce module couvre : `spark-defaults.conf`, `metrics.properties`, `prometheus.yml`, requêtes **PromQL** et un **dashboard Grafana (JSON)** minimal prêt à importer.

---

## 1) Configuration Spark

### 1.1 `spark-defaults.conf` (extraits)
```properties
# Event logs (Spark History Server)
spark.eventLog.enabled=true
spark.eventLog.dir=s3a://miaradia-logs/spark-events

# Chemin du fichier de métriques Dropwizard
spark.metrics.conf=/opt/spark/conf/metrics.properties

# Namespace pour tagger vos métriques
spark.metrics.namespace=miaradia-prod

# (Streaming) pour afficher l’onglet UI streaming
spark.sql.streaming.ui.enabled=true
```

### 1.2 `metrics.properties` (Dropwizard → PrometheusServlet)
> Enregistrez le contenu suivant dans `/opt/spark/conf/metrics.properties`.

```properties
*.sink.prometheusServlet.class=org.apache.spark.metrics.sink.PrometheusServlet
*.sink.prometheusServlet.path=/metrics/prometheus
*.sink.prometheusServlet.period=10
*.source.jvm.class=org.apache.spark.metrics.source.JvmSource

master.sink.prometheusServlet.path=/metrics/master
applications.sink.prometheusServlet.path=/metrics/applications

driver.sink.prometheusServlet.path=/metrics/driver
driver.namespace=driver

executor.sink.prometheusServlet.path=/metrics/executor
executor.namespace=executor
```

> Selon votre image Spark, l’endpoint HTTP (4040/4041/…) doit être exposé. Sur K8s, vérifiez les **ports** de votre Driver/Executors.

---

## 2) Prometheus — `prometheus.yml` (exemple)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Driver Spark (port UI)
  - job_name: 'spark-driver'
    metrics_path: /metrics/driver
    static_configs:
      - targets: ['driver-svc:4040']   # service K8s ou hostname:port

  # Executors Spark (découverte K8s)
  - job_name: 'spark-executors'
    metrics_path: /metrics/executor
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_spark_role]
        action: keep
        regex: executor
      - source_labels: [__meta_kubernetes_pod_ip]
        target_label: __address__
        replacement: '$1:4040'
```

> Sur VM/EMR sans K8s, remplacez par une **liste statique** de cibles (IPs/ports) ou utilisez un **exporter proxy**.

---

## 3) Requêtes PromQL utiles

```promql
# Durée moyenne des jobs (ms) par application
avg by (app_id) (spark_driver_job_duration_sum / spark_driver_job_duration_count)

# Taux d'échec de tâches (sur 5 min)
sum(rate(spark_executor_task_failed_total[5m]))
  / ignoring (status) sum(rate(spark_executor_task_started_total[5m]))

# Débit Shuffle (lecture/écriture)
rate(spark_executor_shuffle_read_bytes_total[5m])
rate(spark_executor_shuffle_write_bytes_total[5m])

# Streaming (débit d'entrée et de traitement)
avg(rate(spark_streaming_input_rows_total[1m])) by (query)
avg(rate(spark_streaming_processed_rows_total[1m])) by (query)

# Mémoire exécutors (si exposée)
max by (executor_id) (spark_executor_memory_used_bytes)
```

---

## 4) Dashboard Grafana (JSON minimal)

Importez ce **JSON** dans Grafana (Dashboards → Import). Il comporte 4 panels clefs.

```json
{
  "schemaVersion": 38,
  "title": "Spark 4.0 — Core Metrics (Minimal)",
  "panels": [
    {
      "type": "graph",
      "title": "Job Duration (avg ms)",
      "targets": [
        { "expr": "avg by (app_id) (spark_driver_job_duration_sum / spark_driver_job_duration_count)" }
      ]
    },
    {
      "type": "graph",
      "title": "Task Failure Rate",
      "targets": [
        { "expr": "sum(rate(spark_executor_task_failed_total[5m])) / sum(rate(spark_executor_task_started_total[5m]))" }
      ]
    },
    {
      "type": "graph",
      "title": "Shuffle Read/Write (bytes/s)",
      "targets": [
        { "expr": "rate(spark_executor_shuffle_read_bytes_total[5m])" },
        { "expr": "rate(spark_executor_shuffle_write_bytes_total[5m])" }
      ]
    },
    {
      "type": "graph",
      "title": "Streaming Throughput (rows/s)",
      "targets": [
        { "expr": "avg(rate(spark_streaming_input_rows_total[1m])) by (query)" },
        { "expr": "avg(rate(spark_streaming_processed_rows_total[1m])) by (query)" }
      ]
    }
  ]
}
```

> Pour un dashboard complet (executors, GC, CPU, watermark, batchDuration), utilisez le fichier étendu du module `08a-2-Streaming.md`.

---

## 5) Démarrage rapide (checklist)

- [ ] Copier `metrics.properties` sur **Driver & Executors**.  
- [ ] Exposer le port **UI Spark** (4040/4041/…).  
- [ ] Configurer **Prometheus** avec les jobs de scrape ci‑dessus.  
- [ ] Importer le **dashboard JSON** dans Grafana.  
- [ ] Vérifier les métriques en temps réel lors d’un job Spark.

---

**Fin — 08a-1 Metrics Core.**  
Étape suivante : **08a-2-Streaming.md** (observabilité Structured Streaming : latence, watermark, alertes & dashboard étendu).
