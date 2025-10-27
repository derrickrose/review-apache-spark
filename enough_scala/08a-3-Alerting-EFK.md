# 08a-3 — Alerting & EFK (Elasticsearch/FluentBit/Kibana) — Spark 4.0 — FR

**Objectif :** Mettre en place des **alertes pro** (Prometheus → Alertmanager → Slack/Email/Webhook) et une **centralisation des logs** (FluentBit → Elasticsearch → Kibana) pour vos jobs **Apache Spark 4.0**. Inclus : **exemples concrets Miaradia** (streaming bloqué, executor mort).

---

## 1) Architecture (vue d’ensemble)

```
Prometheus (rules) ──> Alertmanager ──> Slack / Email / Webhook
Spark Logs (JSON Log4j2) ──> FluentBit ──> Elasticsearch ──> Kibana
```

- Les **règles Prometheus** tirent sur les métriques Spark (Driver/Executors/Streaming).
- **Alertmanager** route vers Slack/Email selon la sévérité.
- Les **logs Spark** (JSON) sont collectés par **FluentBit** vers **Elasticsearch** puis visualisés dans **Kibana** (filtrage par `appId`, `jobId`, `traceId`).

---

## 2) Alertmanager — Configuration

`alertmanager.yml` (exemple prod minimal) :
```yaml
global:
  resolve_timeout: 5m

route:
  receiver: team-slack
  group_by: ['alertname', 'app_id', 'namespace']
  group_wait: 30s
  group_interval: 2m
  repeat_interval: 2h
  routes:
  - matchers: [ severity = "critical" ]
    receiver: team-slack-critical

receivers:
- name: team-slack
  slack_configs:
  - api_url: https://hooks.slack.com/services/T000/B000/XXXXX
    channel: '#spark-alerts'
    icon_emoji: ':rotating_light:'
    send_resolved: true
    title: '[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
    text: |
      *App:* {{ .CommonLabels.app_id }}
      *Namespace:* {{ .CommonLabels.namespace }}
      *Summary:* {{ .CommonAnnotations.summary }}
      *Desc:* {{ .CommonAnnotations.description }}

- name: team-slack-critical
  slack_configs:
  - api_url: https://hooks.slack.com/services/T000/B000/YYYYY
    channel: '#spark-critical'
    send_resolved: true

- name: team-email
  email_configs:
  - to: ops@miaradia.com
    from: noreply@miaradia.com
    smarthost: smtp.miaradia.com:587
    auth_username: noreply@miaradia.com
    auth_password: ${SMTP_PASS}
```

> Ajoutez des **webhooks** (PagerDuty/ServiceNow) si nécessaire.

---

## 3) Règles Prometheus — Spark (YAML)

`rules-spark.yml` :
```yaml
groups:
- name: spark-core
  rules:
  - alert: SparkJobFailuresHigh
    expr: sum(rate(spark_driver_job_failed_total[5m])) by (app_id, namespace) > 0
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Échecs de jobs Spark"
      description: "Des jobs échouent pour app={{ $labels.app_id }} (namespace={{ $labels.namespace }})."

  - alert: ExecutorsLost
    expr: sum(rate(spark_executor_lost_total[5m])) by (app_id, namespace) > 0
    for: 5m
    labels: { severity: critical }
    annotations:
      summary: "Executors perdus"
      description: "Perte d'executors détectée pour {{ $labels.app_id }}."

  - alert: GCTooHigh
    expr: avg_over_time(spark_executor_jvm_gc_time_ms[5m]) by (app_id, executor_id) > 20000
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Temps GC élevé"
      description: "GC > 20s sur 5m ({{ $labels.app_id }}/executor={{ $labels.executor_id }})."

- name: spark-streaming
  rules:
  - alert: StreamingNoInput
    expr: avg(rate(spark_streaming_input_rows_total[5m])) by (query) == 0
    for: 5m
    labels: { severity: warning }
    annotations:
      summary: "Streaming: pas d'input"
      description: "La query {{ $labels.query }} ne reçoit plus de données (≥ 5m)."

  - alert: StreamingBatchLatencyHigh
    expr: avg_over_time(spark_streaming_batch_duration_ms[5m]) by (query) > 30000
    for: 10m
    labels: { severity: warning }
    annotations:
      summary: "Streaming: latence batch élevée"
      description: "Durée > 30s pour {{ $labels.query }}."

  - alert: StreamingWatermarkLagCritical
    expr: max by (query) (spark_streaming_event_time_watermark_seconds) > 900
    for: 10m
    labels: { severity: critical }
    annotations:
      summary: "Streaming: retard watermark critique"
      description: "Retard > 15 minutes pour {{ $labels.query }}."
```

> Chargez ces règles via `rule_files` dans `prometheus.yml`.

---

## 4) EFK — Centralisation des logs

### 4.1 Log4j2 côté Spark (JSON)
Voir `08a-1-Metrics-Core.md` pour `log4j2.xml` (layout JSON et rotation).

### 4.2 FluentBit — DaemonSet (Kubernetes)
`fluent-bit-ds.yaml` (extrait minimal) :
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels: { app: fluent-bit }
  template:
    metadata:
      labels: { app: fluent-bit }
    spec:
      serviceAccountName: fluent-bit
      containers:
      - name: fluent-bit
        image: cr.fluentbit.io/fluent/fluent-bit:2.2
        volumeMounts:
        - { name: varlog, mountPath: /var/log }
        - { name: config, mountPath: /fluent-bit/etc/ }
      volumes:
      - { name: varlog, hostPath: { path: /var/log } }
      - { name: config, configMap: { name: fluent-bit-config } }
```

### 4.3 ConfigMap FluentBit — parser JSON + output Elasticsearch
`fluent-bit-config.yaml` :
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  parsers.conf: |
    [PARSER]
        Name   json
        Format json
  fluent-bit.conf: |
    [SERVICE]
        Parsers_File parsers.conf
    [INPUT]
        Name tail
        Path /var/log/spark/*.json
        Parser json
        Tag spark
    [FILTER]
        Name record_modifier
        Match spark
        Record cluster miaradia-prod
    [OUTPUT]
        Name es
        Match spark
        Host elasticsearch.logging.svc
        Port 9200
        Index spark-logs
        Logstash_Format On
```

> Adaptez le **chemin** des logs selon votre image Spark/volume.

### 4.4 Elasticsearch & Kibana (helm charts recommandés)
- `helm repo add elastic https://helm.elastic.co`  
- `helm install elasticsearch elastic/elasticsearch`  
- `helm install kibana elastic/kibana`

---

## 5) Kibana — Recherche & visualisations

**Index pattern** : `spark-logs-*` (ou `spark-logs` selon output).  
**Champs clés** (si Log4j2 JSON + MDC) : `level`, `logger`, `message`, `appId`, `jobId`, `stageId`, `executorId`, `traceId`.

**Recherches utiles :**
- Erreurs d’app : `appId:"application_12345" AND level:ERROR`
- Executor crash : `message:*Lost executor* OR message:*Container killed*`
- Corrélation trace : `traceId:"<uuid>"` (si OTel/Jaeger relié)

**Visualisations** : histogramme erreurs par `logger`, top apps par `ERROR`, heatmap `stageId` vs `executorId`.

---

## 6) Exemples Miaradia — Alertes & logs

### 6.1 Alerte : *Streaming batch bloqué*
- Règle : `StreamingBatchLatencyHigh` (ci‑dessus) + annotation `summary/description`.
- Action : Alertmanager → Slack `#spark-alerts` (warning), inclut `query` et lien Grafana.

### 6.2 Alerte : *Executor mort*
- Règle : `ExecutorsLost` (critical).
- Action : route Alertmanager vers `#spark-critical` + email **on-call**.

### 6.3 Corrélation logs
- En cas de `ExecutorsLost`, rechercher dans Kibana :  
  `appId:"application_X" AND (message:*Lost executor* OR message:*Exited with*)`  
  et parcourir `traceId` si tracing activé (module 08b).

---

## 7) Bonnes pratiques (prod)

- **Séparation** des canaux : Slack (warning), Slack+Email (critical), PagerDuty (sev‑1).  
- **Rétention** : logs 30–90j, traces 7–14j, metrics ≥ 15–30j (selon coûts).  
- **Cardinalité** : éviter labels haute cardinalité côté Prometheus (ex. `stageAttemptId`).  
- **SLA** : définir des seuils par **query** (streaming) et **appId** (batch).  
- **Sécurité** : pas de PII dans les logs ; contrôles RBAC sur Kibana.

---

**Fin — 08a-3 Alerting & EFK.**  
Étape suivante : **08a-4-Kubernetes.md** (Prometheus Operator + ServiceMonitor) puis **08b-Tracing.md**.
