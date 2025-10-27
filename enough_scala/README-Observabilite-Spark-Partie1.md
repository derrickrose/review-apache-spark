# README Observabilité Spark 4.0 — Partie 1/2
## Apache Spark + Prometheus + Grafana + EFK + Jaeger (OpenTelemetry)

---

## 1. Objectif

Ce document présente une **architecture complète d’observabilité pour Apache Spark 4.0**, intégrée dans un environnement **Kubernetes** avec les composants suivants :

- **Prometheus** pour la collecte des métriques Spark (Driver, Executors, Structured Streaming)  
- **Grafana** pour la visualisation et le suivi des performances  
- **Alertmanager** pour la gestion des alertes (Slack, Email, PagerDuty)  
- **FluentBit + Elasticsearch + Kibana (EFK)** pour la centralisation et l’analyse des logs  
- **OpenTelemetry + Jaeger** pour le tracing distribué et la corrélation avec les métriques et logs

Ce README consolide les modules :  
- `08a-1` → Metrics Core  
- `08a-2` → Observabilité Structured Streaming  
- `08a-3` → Alerting & EFK  
- `08a-4` → Monitoring Kubernetes (Prometheus Operator)  
- `08b` → Tracing Distribué (OpenTelemetry + Jaeger)

---

## 2. Architecture globale

### 2.1 Vue d’ensemble (ASCII)

```
                       ┌────────────────────────────┐
                       │        Kafka Topics        │
                       └────────────┬───────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │      Spark Structured Streaming   │
                    │  (Driver + Executors, Spark 4.0)  │
                    ├────────────────┬──────────────────┤
                    │                │                  │
         ┌──────────┘      ┌─────────┘          ┌───────┘
         ▼                 ▼                    ▼
 Prometheus (Metrics)   EFK Stack (Logs)     OTel Collector (Traces)
   │                        │                    │
   ▼                        ▼                    ▼
Grafana (Dashboards)   Kibana (Logs)         Jaeger (Traces)
   │                        │                    │
   └──────────────► Corrélation & Analyse unifiée ◄──────────────┘
```

Cette architecture permet :
- Le suivi en **temps réel** des jobs Spark batch et streaming
- La **corrélation automatique** entre logs, métriques et traces
- Une **analyse de performance** approfondie (latence, throughput, erreurs)
- Une **résolution rapide d’incidents** grâce à l’observabilité complète

---

## 3. Description des modules

| Module | Nom | Rôle principal | Technologies clés |
|---------|-----|----------------|-------------------|
| **08a-1** | Metrics Core | Collecte des métriques Spark (Prometheus) | `metrics.properties`, `prometheus.yml`, Grafana dashboards |
| **08a-2** | Structured Streaming | Suivi des flux Kafka → Delta + alertes latence | PromQL, alertes, dashboards |
| **08a-3** | Alerting & EFK | Alertmanager + FluentBit + Elasticsearch + Kibana | Slack/Email alerts, JSON logs |
| **08a-4** | Kubernetes Monitoring | Scraping automatique via Prometheus Operator | `ServiceMonitor`, `PodMonitor`, RBAC |
| **08b** | Tracing Distribué | Traces OpenTelemetry + Jaeger | OTel Java Agent, Collector, Jaeger UI |

---

## 4. Workflow complet — Miaradia Observability

### 4.1 Contexte

Le système **Miaradia** traite les courses en temps réel :  
> Kafka reçoit les trajets des utilisateurs (ville, distance, prix).  
> Spark Structured Streaming agrège les données par fenêtre de 5 min et stocke les résultats dans Delta Lake (S3).  
> L’infrastructure d’observabilité suit chaque étape pour détecter les anomalies et optimiser les performances.

### 4.2 Chaîne d’observation

```
Kafka → Spark Structured Streaming → Delta Lake (S3)
   │           │           │
   │           │           ├──> EFK (Logs JSON)
   │           ├──────────────> Prometheus (Metrics)
   │           └──────────────> OpenTelemetry (Traces)
   │
   ▼
 Grafana  ───►  Dashboards unifiés (Metrics + Traces)
 Kibana   ───►  Analyse log contextualisée
 Jaeger   ───►  Tracing des pipelines Spark
```

### 4.3 Exemples de surveillance en production

| Type | Exemple suivi | Indicateurs |
|------|----------------|-------------|
| **Batch** | Calcul quotidien du revenu total | `job_duration`, `shuffle_read`, `gc_time` |
| **Streaming** | Prix moyen par ville (Miaradia) | `inputRowsPerSecond`, `batchDuration`, `eventTimeWatermark` |
| **Alerting** | Aucune donnée reçue 5 min | Règle `StreamingNoInput` |
| **Logging** | Executor crash détecté | `message:*Lost executor*` |
| **Tracing** | Retard watermark anormal | Corrélation trace → log → métrique |

---

## 5. Intégration entre métriques, logs et traces

| Type | Collecte | Stockage | Visualisation |
|------|-----------|-----------|---------------|
| **Metrics** | Prometheus (scrape HTTP `/metrics`) | TSDB (Prometheus) | Grafana |
| **Logs** | FluentBit (tail JSON) → Elasticsearch | Index `spark-logs-*` | Kibana |
| **Traces** | OpenTelemetry Java Agent → Collector | Jaeger | Jaeger UI + liens Grafana |

- Chaque **Spark job** expose des métriques par Driver et Executor.  
- Les **logs JSON** incluent les champs `appId`, `stageId`, `traceId`.  
- Les **traces OTel** permettent de suivre un job complet à travers tous les composants.  
- Grafana intègre des **liens vers Jaeger et Kibana** pour un diagnostic complet.

---

**Suite → Partie 2 : Bonnes pratiques, dimensionnement, checklist production, et extensions futures.**
