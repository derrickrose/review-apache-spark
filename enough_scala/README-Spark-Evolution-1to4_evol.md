# 🧭 Évolution d’Apache Spark — de 1.x à 4.x (FR)

Ce document récapitule **les grandes évolutions** d’Apache Spark, avec **compatibilités (Java/Scala/Hadoop)**, **features clés**, **changements d’API**, et **impacts architecturaux**. Il inclut une **section détaillée sur l’unification Spark 2** (*SparkSession = SparkContext + SQLContext/HiveContext + Streaming*) et un **chapitre “Nouveautés Spark 4.0.0”**.

---

## 🗺️ Vue d’ensemble (tableau synthèse)

| Version Spark | Période | Java | Scala | Hadoop/YARN | Points clés | Impact architectural |
|---|---:|---:|---:|---:|---|---|
| **1.0–1.6** | 2014–2016 | 7/8 | 2.10/2.11 | 2.2–2.7 | RDD, DStream, SQL (naissant), MLlib, GraphX | 1ʳᵉ gen. : batch in‑memory, alternative à MapReduce |
| **2.0–2.4** | 2016–2019 | 8 | 2.11/2.12 | 2.7+ | **DataFrame/Dataset**, **SparkSession**, **Structured Streaming**, Tungsten 1.0, Catalyst | Unification SQL/Streaming, moteur vectorisé |
| **3.0–3.2** | 2020–2022 | 11 | 2.12/2.13 | 3.2+ | **AQE**, Dynamic Partition Pruning, K8s stable (3.1), ANSI | Cloud‑native, exécution adaptative |
| **3.3–3.5** | 2023–2025 | 17/21 | 3.3/3.4 | 3.3.6 | Shuffle Merge, Broadcast amélioré, **Pandas API on Spark**, Iceberg/Delta/Hudi | Industrialisation & connecteurs modernes |
| **4.0.x** | 2025+ | 17/21 | 3.4+ | 3.3+ | **Spark Connect**, **VARIANT**, Tungsten 2.0, Catalyst v2, **OpenTelemetry**, ANSI par défaut | Plate‑forme analytique unifiée, observabilité native |

> NB : Les valeurs “Java/Scala/Hadoop” indiquent les versions **minimales/mises en avant** par la communauté/éditeurs au moment de sortie.

---

## 🔵 Spark 1.x (2014–2016) — RDD & DStream

### Compatibilité
- **Java** : 7 → 8 • **Scala** : 2.10 → 2.11 • **Hadoop** : 2.2 → 2.7 • Managers : Standalone, **YARN**, Mesos

### Features majeures
- **RDD** immuables (transformations `map`, `flatMap`, `reduceByKey`…) • **Cache/persist()**
- **Spark SQL** initial (SchemaRDD/DataFrame via HiveContext)
- **Spark Streaming (DStream)** micro‑batch
- **MLlib** (pipelines de ML) • **GraphX** (graphes)

### Architecture interne
- **DAG Scheduler** + Task Scheduler • Shuffle par fichiers temporaires
- Sérialisation Java/Kryo • Pas d’optimisation dynamique

### Impact
- Remplacement de MapReduce pour l’analytique batch en mémoire (×10–100 plus rapide).

---

## 🟣 Spark 2.x (2016–2019) — SQL unifié & gestion mémoire

### Compatibilité
- **Java** : 8 • **Scala** : 2.11/2.12 • **Hadoop** : 2.7+ • Managers : YARN, Mesos, Standalone

### Features majeures
- **API DataFrame/Dataset unifiée** (typage + optimisations)
- **SparkSession** (remplace `SQLContext`/`HiveContext`, coordonne tout)
- **Structured Streaming** (2.3+) avec exactly‑once et intégration Kafka
- **Catalyst** (plan logique → physique) + **Tungsten 1.0** (mémoire off‑heap, vectorisation)
- Lecteurs **Parquet/ORC** vectorisés, **Whole‑Stage CodeGen**

### 🧩 **Unification des contextes (très important)**
**Avant Spark 2** :  
- `SparkContext` pour RDD, `SQLContext/HiveContext` pour SQL/Hive, `StreamingContext` pour DStreams → **3 contextes distincts**.

**Avec Spark 2** : **`SparkSession` regroupe tout** :

```scala
val spark = SparkSession.builder()
  .appName("UnifiedContext")
  .master("yarn")
  .getOrCreate()

// Accès aux anciens contextes via la même session
spark.sparkContext      // équivalent ancien SparkContext
spark.sql("SELECT 1")   // SQL direct
// Structured Streaming sur la même session
val streamDf = spark.readStream.format("kafka").option("subscribe","rides").load()
```

**Conséquences architecturales :**
- Un seul point d’entrée/configuration (`spark.conf`)  
- Caches & catalogues partagés • UDFs centralisées  
- Coexistence naturelle **batch + SQL + streaming** dans **une même session**  
- Migration facilitée des apps 1.x → 2.x (via `SparkSession`)

### Impact
- Spark devient **SQL‑first** et **pipeline‑ready** ; 3–5× plus rapide sur workloads anal. courants.

---

## 🟢 Spark 3.x (2020–2025) — Cloud‑native & adaptatif

### Compatibilité
- **Java** : 11 / 17 / 21 • **Scala** : 2.12 / 2.13 / 3.x • **Hadoop** : 3.2+ • **K8s** : stable (3.1+)

### Features majeures
- **AQE (Adaptive Query Execution)** : fusion partitions, gestion **skew join**, plan de join modifié **à l’exécution**
- **Dynamic Partition Pruning** • **ANSI** mode • **UI SQL** améliorée
- **Support Kubernetes** first‑class (Spark Operator) • **Pandas API on Spark** (Koalas)
- **Shuffle merge**, broadcast amélioré • Connecteurs **Iceberg/Hudi/Delta**

### Architecture interne
- Catalyst enrichi de statistiques runtime • Tungsten “1.5” (gestion mémoire & vectorisation stabilisées)
- Cloud storage natif (S3A/GCS/ADLS), history server amélioré

### Impact
- Spark devient **cloud‑ready** et **auto‑adaptatif**, idéal pour ETL/BI/ML unifiés.

---

## 🟠 Spark 4.0.0 (2025+) — Connect & Observabilité

### Compatibilité
- **Java** : 17/21 • **Scala** : 3.4+ • **Hadoop** : 3.3+ • **K8s** : 1.25+ • **Python** : 3.9+

### Nouveautés clés
1) **Spark Connect** (gRPC) — client/serveur distant (Python/Scala/Java/Go/Rust/Swift) :
```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.remote("sc://cluster:15002").getOrCreate()
df = spark.read.csv("s3a://data/rides.csv", header=True)
```
2) **Type `VARIANT`** — stockage JSON semi‑structuré natif :
```sql
CREATE TABLE t(id BIGINT, meta VARIANT);
INSERT INTO t VALUES (1, '{"price":12,"city":"Paris"}');
SELECT meta.price FROM t;
```
3) **Tungsten 2.0** & **Catalyst v2** — exécution vectorielle et planification coût revues  
4) **OpenTelemetry & Audit events JSON** — observabilité standardisée  
5) **ANSI SQL par défaut** — erreurs strictes si conversions risquées

### Impact
- Plate‑forme analytique **unifiée et observable** • **Multi‑langage** complet • Meilleur support des **lakehouses** (Delta/Iceberg/Hudi).

---

## 🧪 Matrice de compatibilité (référence rapide)

| Spark | Java | Scala | Hadoop | Managers |
|---:|---:|---:|---:|---|
| 1.6 | 7/8 | 2.10/2.11 | 2.2–2.7 | YARN, Mesos, Standalone |
| 2.4 | 8 | 2.11/2.12 | 2.7+ | YARN, Mesos, Standalone |
| 3.2 | 11 | 2.12/2.13 | 3.2+ | **YARN, K8s**, Standalone |
| 3.5 | 17/21 | **3.3/3.4** | 3.3.6 | YARN, **K8s** |
| 4.0 | 17/21 | **3.4+** | 3.3+ | YARN, **K8s** |

> Pour Python : PySpark 4 requiert Python **3.9+**.

---

## 📌 Implications de design par version (guidelines)

- **1.x** : Éviter les nouveaux projets en RDD/DStream pur. Migrer vers DataFrame/Structured Streaming.  
- **2.x** : Standardiser `SparkSession`, DataFrames/Datasets. Centraliser config & UDFs.  
- **3.x** : Activer **AQE**, utiliser **K8s** ou EMR 6/7, préférer **Iceberg/Delta**.  
- **4.x** : Envisager **Spark Connect**, adopter `VARIANT` pour semi‑structuré, activer **OpenTelemetry**.

---

## 📚 Références de migration
- 1.x → 2.x : remplacer `SQLContext/HiveContext/StreamingContext` par **`SparkSession`** + **Structured Streaming**.  
- 2.x → 3.x : activer **AQE**, corriger comportements **ANSI** et revoir les UDFs.  
- 3.x → 4.x : tester **Spark Connect**, valider compat matrices (Java/Scala/Hadoop), migrer monitorings vers **OpenTelemetry**.

---

**Fin.** Ce document est prêt à être versionné aux côtés de tes parties 5A/5B/6A/6B pour donner la **vision d’ensemble** à l’équipe (ops, data eng, architectes).

