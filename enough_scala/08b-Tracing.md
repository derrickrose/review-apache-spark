# 08b — Tracing Distribué Spark 4.0 (OpenTelemetry + Jaeger) — FR

**Objectif :** Instrumenter **Apache Spark 4.0** pour le **tracing distribué** avec **OpenTelemetry (OTel)**, collecter via **OTel Collector**, visualiser dans **Jaeger**, et **corréler** *traces ↔ logs ↔ metrics* (MDC + Prometheus).

---

## 1) Architecture & principes

```
Spark Driver/Executors ─(OTel Java Agent)─> OTel Collector ─> Jaeger (traces)
                                         └> Logs (Log4j2 JSON) → EFK (Kibana)
                                         └> Metrics (PrometheusServlet) → Grafana
```

- **OTel Java Agent** = instrumentation **sans code** (bytecode) des librairies JVM (HTTP, JDBC, gRPC…).
- **Ressources OTel** : `service.name`, `service.version`, `deployment.environment`, tags Spark (`spark.app.id`, `jobId`, `stageId`).

---

## 2) Démarrage rapide — spark-submit

### 2.1 Variables d'env conseillées
```bash
export OTEL_SERVICE_NAME="spark4"
export OTEL_RESOURCE_ATTRIBUTES="service.version=4.0.0,deployment.environment=prod"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector.monitoring:4317"
# Sampling (head) : always_on | parentbased_always_on | traceidratio e.g. 0.1
export OTEL_TRACES_SAMPLER="parentbased_traceidratio"
export OTEL_TRACES_SAMPLER_ARG="0.1"
```

### 2.2 Commande
```bash
/opt/spark/bin/spark-submit   --conf "spark.driver.extraJavaOptions=-javaagent:/opt/otel/opentelemetry-javaagent.jar"   --conf "spark.executor.extraJavaOptions=-javaagent:/opt/otel/opentelemetry-javaagent.jar"   --conf spark.driverEnv.OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME}   --conf spark.driverEnv.OTEL_RESOURCE_ATTRIBUTES=${OTEL_RESOURCE_ATTRIBUTES}   --conf spark.driverEnv.OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}   --conf spark.executorEnv.OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME}   --conf spark.executorEnv.OTEL_RESOURCE_ATTRIBUTES=${OTEL_RESOURCE_ATTRIBUTES}   --conf spark.executorEnv.OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}   --class com.miaradia.spark.App   local:///opt/spark/jars/app.jar
```

> L’agent colle automatiquement les spans aux opérations réseau/JDBC/etc. Pour Spark internes, on ajoute des **attributs** (appId, job/stage) via MDC ou hooks côté driver (cf. §5).

---

## 3) OpenTelemetry Collector — pipeline traces

`otel-collector.yaml` (minimal prod) :
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http: {}

processors:
  memory_limiter:
    limit_mib: 2048
    check_interval: 5s
  batch:
    send_batch_max_size: 8192
    timeout: 5s
  attributes:
    actions:
    - key: app.namespace
      action: insert
      value: miaradia-prod

exporters:
  jaeger:
    endpoint: jaeger-collector.monitoring.svc:14250
    tls: { insecure: true }
  logging:
    loglevel: warn

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, attributes, batch]
      exporters: [jaeger, logging]
```

Déploiement : `kubectl -n monitoring apply -f otel-collector.yaml` (Deployment/Service).

---

## 4) Jaeger — usage rapide

- UI (port-forward si besoin) : `kubectl -n monitoring port-forward svc/jaeger-query 16686:16686` → http://localhost:16686  
- Filtrer par `Service = spark4`, `operation`, et rechercher par **`spark.app.id`** si ajouté dans les attributs.

---

## 5) Corrélation Traces ↔ Logs (MDC) & attributs Spark

### 5.1 Enrichir les logs Spark avec traceId/spanId (Scala)
```scala
import org.slf4j.MDC
import org.apache.spark.scheduler._

spark.sparkContext.addSparkListener(new SparkListener {
  override def onApplicationStart(e: SparkListenerApplicationStart): Unit = {
    MDC.put("appId", spark.sparkContext.applicationId)
  }
  override def onStageSubmitted(e: SparkListenerStageSubmitted): Unit = {
    MDC.put("stageId", e.stageInfo.stageId.toString)
  }
})
// Si l'agent OTel expose le traceId à la thread local, certains appenders peuvent l'injecter automatiquement.
// À défaut, créez un traceId fallback côté app :
MDC.put("traceId", java.util.UUID.randomUUID().toString)
```

### 5.2 `log4j2.xml` — layout JSON incluant MDC
```xml
<JsonLayout complete="false" compact="true" eventEol="true" properties="true"/>
```

> Avec **EFK** (08a‑3), on peut rechercher `traceId:"..."` et recouper avec la trace Jaeger.

### 5.3 Ajouter des attributs OTel custom
Vous pouvez enrichir les **resource attributes** via `OTEL_RESOURCE_ATTRIBUTES` :  
`deployment.environment=prod,cluster=emr,app=spark-pricer,spark.app.id=<id>`  
ou via un **processor** `attributes` au niveau du collector (cf. §3).

---

## 6) Sécurité & performances

- **Sampling** : 1–10 % recommandé en prod (`parentbased_traceidratio` + `OTEL_TRACES_SAMPLER_ARG=0.05`).  
- **Pii** : ne loggez pas de PII en attributs de trace ; privilégiez `appId`, `jobId`, `stageId`.  
- **Réseau** : limiter l’accès au collector via **NetworkPolicy** ; TLS/mtls si nécessaire.  
- **Overhead** : l’agent OTel ajoute une faible latence (quelques %). Tester en pré‑prod et exclure les endpoints bruyants si besoin.

---

## 7) Exemple complet (Kubernetes)

### 7.1 Montage de l’agent dans l’image
Dockerfile (extrait) :
```dockerfile
FROM bitnami/spark:4.0.0
ADD opentelemetry-javaagent.jar /opt/otel/opentelemetry-javaagent.jar
COPY conf/* /opt/spark/conf/
```

### 7.2 SparkApplication (extrait)
```yaml
spec:
  driver:
    env:
      - name: OTEL_SERVICE_NAME
        value: spark4
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: http://otel-collector.monitoring:4317
    javaOptions: "-javaagent:/opt/otel/opentelemetry-javaagent.jar"
  executor:
    env:
      - name: OTEL_SERVICE_NAME
        value: spark4
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: http://otel-collector.monitoring:4317
    javaOptions: "-javaagent:/opt/otel/opentelemetry-javaagent.jar"
```

---

## 8) Intégration Grafana — liens croisés

Dans votre dashboard Grafana, ajoutez un **lien externe** vers Jaeger :  
- URL type : `http://jaeger-query.monitoring.svc:16686/search?service=$service&tags={"spark.app.id":"$app_id"}`  
- Variables : `service` (OTel), `app_id` (Spark).  
Permet de passer d’un pic de **latence** metrics à la **trace** détaillée en 1 clic.

---

## 9) Checklist Tracing

- [ ] **OTel Java Agent** monté sur **Driver + Executors**.  
- [ ] **OTLP gRPC** vers **OTel Collector** OK (4317).  
- [ ] **Jaeger** up, service exposé en cluster/port-forward.  
- [ ] **Logs JSON** contiennent `traceId`, `appId`, `stageId`.  
- [ ] **Dashboards Grafana** avec liens vers Jaeger.  
- [ ] **Sampling** en place (ratio raisonnable), rétention 7–14j.

---

**Fin — 08b Tracing Distribué.**  
Relie‑le à **08a‑1/2/3/4** pour une observabilité Spark **complète**.
