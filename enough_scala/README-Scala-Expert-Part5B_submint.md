# 🧱 Scala Expert — Partie 5B : Mise en production Spark (FR)

**Objectif** : Déployer, surveiller et tuner des jobs **Apache Spark** en production, avec exemples `spark-submit`, zoom **shuffle/AQE**, templates **YAML/JSON**, et **check‑list** finale. (Inclut une section **troubleshooting**).

---

## 1) Architecture & déploiement (rappel express)

- **Driver** : planifie, envoie les tâches, collecte les résultats.  
- **Executors** : exécutent les tasks; mémoire + CPU.  
- **Cluster manager** : **YARN**, **Kubernetes**, **Standalone**, **EMR/Dataproc**.  
- **Packaging** : `sbt assembly` → JAR **fat/uber** (avec dépendances nécessaires).

```bash
# Assembly typique
sbt clean test assembly
# Jar en target/scala-3.x/mon-app-assembly-<version>.jar
```

> En prod, le `--master` est fourni par le cluster; en local, utilisez `local[*]` pour les tests.

---

## 2) `spark-submit` — recettes prêtes à l’emploi

### 2.1 AWS EMR (YARN)
```bash
spark-submit \
  --deploy-mode cluster \
  --class com.miaradia.spark.MiaradiaSparkApp \
  --conf spark.executor.cores=5 \
  --conf spark.executor.memory=24g \
  --conf spark.executor.memoryOverhead=3g \
  --conf spark.sql.shuffle.partitions=600 \
  --conf spark.sql.adaptive.enabled=true \
  --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
  s3://miaradia-artifacts/jars/miaradia-etl-assembly.jar \
  s3://miaradia-data/rides.csv \
  s3://miaradia-data/cities.csv \
  s3://miaradia-out
```
**Notes** :  
- Sur EMR, les rôles IAM gèrent l’accès S3; vérifiez les **bucket policies**.  
- Ajoutez `--jars` pour libs externes (connecteurs JDBC, etc.).

### 2.2 Kubernetes (Spark-on-K8s)
```bash
spark-submit \
  --master k8s://https://<API_SERVER> \
  --deploy-mode cluster \
  --name miaradia-spark-job \
  --class com.miaradia.spark.MiaradiaSparkApp \
  --conf spark.kubernetes.container.image=ghcr.io/miaradia/spark:3.5.1 \
  --conf spark.executor.instances=40 \
  --conf spark.executor.cores=5 \
  --conf spark.executor.memory=24g \
  --conf spark.executor.memoryOverhead=3g \
  --conf spark.sql.adaptive.enabled=true \
  --conf spark.sql.shuffle.partitions=600 \
  --conf spark.kubernetes.namespace=data \
  --conf spark.kubernetes.executor.request.cores=5 \
  --conf spark.kubernetes.driverEnv.LOG_LEVEL=INFO \
  local:///opt/spark/jars/miaradia-etl-assembly.jar \
  s3a://miaradia-data/rides.csv s3a://miaradia-data/cities.csv s3a://miaradia-out
```
**Notes** :  
- Image Docker doit inclure le JAR; sinon utilisez `--jars` + `spark.kubernetes.file.upload.path`.  
- Pour S3 : configurez `fs.s3a.*` via `core-site.xml` ou `--conf` (clé/secret ou IAM rôle via IRSA).

---

## 3) Zoom technique : Shuffle & AQE (approfondi)

### 3.1 Quand le shuffle apparaît ?
- `groupBy`, `join`, `distinct`, `orderBy`, `repartition`, certaines `window`.  
- **Effet** : répartition des lignes par clé → écritures **shuffle write** (disque) puis **shuffle read**.

### 3.2 Où sont les fichiers ?
- Sur disque local des executors (`spark.local.dir`) + tampons mémoire (off-heap / overhead).

### 3.3 Comment *limiter/contourner* un shuffle ?
- **Réduire tôt** : `select` minimal + `filter` en amont.  
- **Broadcast** des petites dimensions : `join(broadcast(dim), ...)`.  
- **Bucketing** + **sorted** par clé sur tables récurrentes.  
- **Map-side combine** / pré‑agrégations locales.  
- **AQE** : active `spark.sql.adaptive.enabled=true` pour fusion partitions, `skewJoin`.

### 3.4 Lire un plan d’exécution
```scala
df.explain("extended") // Exchange = shuffle, BroadcastHashJoin = pas de shuffle côté petite table
```

### 3.5 AQE — réglages utiles
```bash
--conf spark.sql.adaptive.enabled=true
--conf spark.sql.adaptive.coalescePartitions.enabled=true
--conf spark.sql.adaptive.skewJoin.enabled=true
```

---

## 4) Templates prod — YAML / JSON / spark-defaults

### 4.1 Spark-on-K8s (YAML minimal)
```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: miaradia-spark-job
  namespace: data
spec:
  type: Scala
  mode: cluster
  image: ghcr.io/miaradia/spark:3.5.1
  mainClass: com.miaradia.spark.MiaradiaSparkApp
  mainApplicationFile: local:///opt/spark/jars/miaradia-etl-assembly.jar
  sparkVersion: "3.5.1"
  driver:
    cores: 2
    memory: 4g
    serviceAccount: spark-sa
  executor:
    instances: 40
    cores: 5
    memory: 24g
  deps:
    jars: []
  sparkConf:
    "spark.sql.adaptive.enabled": "true"
    "spark.sql.shuffle.partitions": "600"
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
```

### 4.2 EMR — configuration JSON (extrait)
```json
{
  "Classification": "spark-defaults",
  "Properties": {
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.shuffle.partitions": "600",
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
  }
}
```

### 4.3 `spark-defaults.conf` (commenté)
```properties
spark.sql.adaptive.enabled=true
spark.sql.shuffle.partitions=600
spark.serializer=org.apache.spark.serializer.KryoSerializer
spark.executor.cores=5
spark.executor.memory=24g
spark.executor.memoryOverhead=3g
```

---

## 5) Monitoring & observabilité

### 5.1 Spark UI
- **Stages** (temps, tasks, skew), **Storage** (cache), **SQL** (plans).  
- Repérer `Exchange`, `SortMergeJoin`, `BroadcastHashJoin`.

### 5.2 Prometheus + Grafana
- Activer métriques :  
  ```bash
  --conf spark.metrics.conf=metrics.properties
  ```
- Suivre : CPU par task, **GC time**, **shuffle spill**, mémoire, StateStore (streaming).

### 5.3 Logs structurés (ELK)
- Logback JSON → ingestion ELK/Opensearch; corrélation par `appId`, `stageId`, `jobId`.

---

## 6) Tuning en production (récap)

- **Mémoire** : 16–32 Go heap/executor + overhead 7–10 %.  
- **Cœurs** : 4–6 / executor (éviter “fat executors”).  
- **Partitions** : 2–3× cœurs totaux; Parquet 128–256 Mo.  
- **Serializer** : **Kryo** recommandé.  
- **Cache** ciblé (réutilisation multiple).  
- **Shuffle** : AQE on, broadcast si petite dimension, bucketing si réutilisé.  
- **I/O** : limiter petits fichiers (coalesce); préférer Parquet.

---

## 7) Check‑list pré‑production (go‑live)

- [ ] **Dimensionnement** validé (cf. Partie 5A)  
- [ ] **Plan sans shuffles inutiles** (`explain`)  
- [ ] **AQE activée** + skew join si besoin  
- [ ] **Logs** (niveau, format JSON si ELK)  
- [ ] **Metrics** (Prometheus/Grafana)  
- [ ] **Sécurité** (IAM/Kerberos/SA), accès S3/HDFS OK  
- [ ] **Data Quality** (échantillons, règles)  
- [ ] **CI/CD** basique (build + tests + déploiement)  
- [ ] **Rollback** prévu (version jar précédente)  
- [ ] **Alerte SLA** (latence, throughput, échecs)  

---

## 8) Troubleshooting (pannes courantes & correctifs)

### 8.1 `ExecutorLostFailure` / executors qui disparaissent
- **Causes** : OOM, node preempted (K8s), réseau.  
- **Fix** : réduire heap par JVM mais augmenter le **nombre** d’executors; vérifier GC; surveiller noeuds K8s.

### 8.2 `OutOfMemoryError: GC overhead limit exceeded`
- **Causes** : heap trop pleine, gros shuffles.  
- **Fix** : réduire taille partitions, **augmenter parallelisme**, `persist(MEMORY_AND_DISK)`, vérifier objets volumineux/UDF.

### 8.3 `Shuffle fetch failed`
- **Causes** : fichiers shuffle perdus/corrup, executors morts.  
- **Fix** : augmenter **retries**, stabiliser cluster, vérifier disque local, activer **AQE**.

### 8.4 `java.io.FileNotFoundException` (S3)
- **Causes** : permissions, chemins, éventuelle latence S3.  
- **Fix** : rôles IAM, chemins `s3a://`, réessais, consistency EMRFS si besoin.

### 8.5 Skew extrême (clé chaude)
- **Symptôme** : tâches très longues sur quelques partitions.  
- **Fix** : **salting**, **broadcast** petite table, **AQE skew** on, **bucketing** par clé.

---

## 9) Annexes — commandes utiles

```bash
# Voir config effective
spark-submit --version

# Debug niveau SQL plan
spark.sql.debug.maxToStringFields=200

# Exemple d’explain complet depuis spark-shell
spark.read.parquet("/path").where("price > 0").explain(true)
```

---

**Fin — Partie 5B.**  
Prochaine partie (6) : **Industrialisation & Architecture Spark** (Airflow, Deequ, Terraform, CI/CD, sécurité, lineage, comparatifs).
