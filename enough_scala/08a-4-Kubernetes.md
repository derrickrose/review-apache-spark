# 08a-4 — Kubernetes Monitoring (Prometheus Operator + ServiceMonitor) — FR

**Objectif :** Déployer une stack **Prometheus Operator** sur Kubernetes et **scraper automatiquement** les métriques **Spark 4.0** (Driver/Executors) via **ServiceMonitor/PodMonitor**, avec RBAC, annotations, NetworkPolicy et dashboards Grafana.

---

## 1) Pré‑requis & installation (Helm)

```bash
# Namespaces
kubectl create namespace monitoring || true

# Prometheus Operator + kube-state-metrics + node-exporter
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack   --namespace monitoring   --set grafana.enabled=true   --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false   --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

> Le chart **kube-prometheus-stack** installe : Prometheus Operator, Prometheus, Alertmanager, Grafana, exporters de base.

---

## 2) Stratégie de scrape Spark sur K8s

Deux options (souvent combinées) :
1. **ServiceMonitor** pour le **Driver** (Service stable, label `app: spark-driver`).  
2. **PodMonitor** pour les **Executors** (découverts dynamiquement via labels `spark-role=executor`).

> Spark 4.0 expose les métriques via le **PrometheusServlet** (cf. `metrics.properties`) sur le port **UI (4040/4041/...)**.

---

## 3) Annotations & Services côté Spark

### 3.1 Service pour le Driver
```yaml
apiVersion: v1
kind: Service
metadata:
  name: miaradia-spark-driver
  namespace: miaradia
  labels: { app: spark-driver }
spec:
  type: ClusterIP
  selector:
    spark-role: driver
  ports:
  - name: http
    port: 4040
    targetPort: 4040
```

### 3.2 Labels sur pods Spark
Assurez-vous que vos pods **Driver/Executor** ont les labels :
```yaml
metadata:
  labels:
    spark-role: driver   # ou executor
    app.kubernetes.io/part-of: spark
```

> Avec le **Spark Operator**, vous pouvez ajouter des labels via `driver.labels` / `executor.labels` dans `SparkApplication`.

---

## 4) ServiceMonitor (Driver) & PodMonitor (Executors)

### 4.1 ServiceMonitor (Driver)
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: spark-driver-sm
  namespace: monitoring
spec:
  selector:
    matchLabels: { app: spark-driver }
  namespaceSelector:
    any: true
  endpoints:
  - port: http
    path: /metrics/driver
    interval: 15s
    scheme: http
```

### 4.2 PodMonitor (Executors)
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: spark-executor-pm
  namespace: monitoring
spec:
  selector:
    matchLabels:
      spark-role: executor
  namespaceSelector:
    any: true
  podMetricsEndpoints:
  - port: http
    path: /metrics/executor
    interval: 15s
    relabelings:
    - sourceLabels: [__meta_kubernetes_pod_ip]
      targetLabel: instance
```

> Adaptez `port` si vos images n’exposent pas 4040 sous le nom `http`. Sinon utilisez `targetPort` numérique (ex: 4040).

---

## 5) Exemple complet — SparkApplication (Spark Operator)

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: miaradia-spark-app
  namespace: miaradia
spec:
  type: Scala
  mode: cluster
  image: <REGISTRY>/miaradia-spark-app:4.0.0
  imagePullPolicy: IfNotPresent
  mainClass: com.miaradia.spark.App
  mainApplicationFile: "local:///opt/spark/jars/miaradia-spark-app-assembly.jar"
  sparkVersion: "4.0.0"

  timeToLiveSeconds: 3600
  driver:
    serviceAccount: spark-sa
    cores: 1
    memory: "2g"
    labels:
      spark-role: driver
      app: spark-driver
    env:
      - name: SPARK_CONF_DIR
        value: /opt/spark/conf
    volumeMounts:
      - name: spark-conf
        mountPath: /opt/spark/conf
  executor:
    instances: 3
    cores: 2
    memory: "4g"
    labels:
      spark-role: executor
    env:
      - name: SPARK_CONF_DIR
        value: /opt/spark/conf
    volumeMounts:
      - name: spark-conf
        mountPath: /opt/spark/conf
  volumes:
    - name: spark-conf
      configMap:
        name: spark-metrics-conf
```

> Le **ConfigMap** ci‑dessous fournit `metrics.properties` (PrometheusServlet).

---

## 6) ConfigMap `metrics.properties` (PrometheusServlet)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spark-metrics-conf
  namespace: miaradia
data:
  metrics.properties: |
    *.sink.prometheusServlet.class=org.apache.spark.metrics.sink.PrometheusServlet
    *.sink.prometheusServlet.path=/metrics/prometheus
    *.sink.prometheusServlet.period=10
    *.source.jvm.class=org.apache.spark.metrics.source.JvmSource

    driver.sink.prometheusServlet.path=/metrics/driver
    driver.namespace=driver
    executor.sink.prometheusServlet.path=/metrics/executor
    executor.namespace=executor
```

> Montez ce **ConfigMap** sur `/opt/spark/conf/metrics.properties` via `SPARK_CONF_DIR`.

---

## 7) Grafana — Dashboards & Datasources

Après installation de **kube-prometheus-stack**, vous avez Grafana exposé.  
Ajoutez un **dashboard Spark** (cf. `08a-1` & `08a-2`) :  
- Importer **Grafana JSON** (panels: jobs, executors, shuffle, streaming).  
- Variables suggérées : `namespace`, `app_id`, `query` (streaming).

---

## 8) NetworkPolicy (sécurisation scrape)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-prometheus-to-spark
  namespace: miaradia
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/part-of: spark
  ingress:
  - from:
    - namespaceSelector:
        matchLabels: { name: monitoring }
    ports:
    - protocol: TCP
      port: 4040
  policyTypes: ["Ingress"]
```

> Autorise uniquement le **namespace monitoring** (Prometheus) à atteindre le port UI/metrics Spark.

---

## 9) RBAC minimal pour Operator & Monitoring

### 9.1 Prometheus RBAC (créé par Helm)  
Géré par `kube-prometheus-stack`. Vérifiez que Prometheus a accès aux **namespaces** ciblés.

### 9.2 Spark Operator RBAC
Lors de l’installation, le chart crée les permissions nécessaires sur `SparkApplication`.  
Limiter la portée au **namespace** `miaradia` pour isoler les équipes.

---

## 10) Checklist déploiement

- [ ] **kube-prometheus-stack** installé (Prometheus, Grafana, Alertmanager).  
- [ ] **Service** Driver et **labels** pods (`spark-role=driver|executor`).  
- [ ] **ServiceMonitor** (Driver) et **PodMonitor** (Executors).  
- [ ] **metrics.properties** monté (PrometheusServlet).  
- [ ] **NetworkPolicy** : autoriser uniquement Prometheus.  
- [ ] **Dashboards Grafana** importés.  
- [ ] **Alertes** chargées (cf. `08a-2` & `08a-3`).

---

**Fin — 08a-4 Kubernetes Monitoring.**  
Prochaine étape : **08b-Tracing.md** (OpenTelemetry + Jaeger, corrélation logs/metrics/traces).