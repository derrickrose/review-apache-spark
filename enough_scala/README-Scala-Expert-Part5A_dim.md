# 📊 Scala Expert — Partie 5A : Dimensionnement Spark (Sizing complet)

**But** : dimensionner correctement un job Spark (CPU, RAM, partitions, shuffle) pour tenir un **SLA** au **coût minimal**.

---

## 1) Variables à estimer avant tout
- **Taille d’entrée** (brut / compressé) et **format** (Parquet/CSV/JSON)
- **Facteur d’expansion mémoire** après décodage (≈ ×2 à ×6 selon colonnes)
- **Shuffle attendu** (joins, aggregations) → nombre d’étapes et taille
- **SLA** : ex. “finir en ≤ 30 min” (batch) ou “latence ≤ 60 s” (streaming)
- **Infra** : vCores/RAM par nœud, I/O (HDFS/S3), réseau, budget

---

## 2) Règles rapides (cheat‑sheet)
- **Cœurs/exécuteur** : **4 à 6** (sweet‑spot)
- **RAM Heap/exécuteur** : **16–32 Go** (éviter > 64 Go)
- **Overhead JVM** : **7–10 %** (`spark.executor.memoryOverhead`)
- **Parallelisme** : **2–3 partitions / cœur** disponible
- **Partitions d’entrée (Parquet)** : **128–256 Mo** par partition
- **Shuffle partitions** : **200–600** pour commencer (`spark.sql.shuffle.partitions`)
- **Broadcast join** si dimension ≤ **256–512 Mo** (`autoBroadcastJoinThreshold`)
- **Dynamic allocation** : ON si cluster partagé ; OFF si SLA strict & workload stable

---

## 3) Méthode “worksheet” (formules pratiques)
1) **Cœurs totaux**
```
total_cores = executors * cores_per_executor
parallelism_cible ≈ 2–3 × total_cores
```
2) **Partitions**
- Entrée Parquet : `nb_partitions_in = ceil(size_in_bytes / 256MB)`
- Après filtres/agg : **repartition** pour rester ≈ `2–3 × total_cores`
3) **Mémoire/exécuteur**
```
executor_heap   ≈ working_set_per_core × cores_per_executor
overhead        ≈ 7–10 % de executor_heap
executor_total  = executor_heap + overhead
```
4) **Nombre d’exécuteurs**
- Batch : à partir du **SLA** + débit I/O ; viser 70–80 % d’utilisation cluster
- Streaming : dimensionner sur le **débit crête** (events/s) × **coût/événement**

---

## 4) Exemples chiffrés
### 4.1 — Batch Parquet **1 To**, SLA **30 min**
- Entrée : 1 To Parquet (S3/HDFS), 2 aggregations + 1 join
- Expansion mémoire estimée ×3 → 3 To **répartis** sur le cluster

**Plan recommandé**
- `cores/executor = 5`, `executor_heap = 24g`, `overhead = 3g` → **~27g total**
- **40 exécuteurs** → **200 cœurs** totaux
- **Shuffle partitions = 600** (≈ 3 × cœurs)

**Params initiaux**
```
spark.executor.cores=5
spark.executor.memory=24g
spark.executor.memoryOverhead=3g
spark.dynamicAllocation.enabled=false
spark.sql.shuffle.partitions=600
spark.sql.autoBroadcastJoinThreshold=256MB
spark.sql.adaptive.enabled=true
spark.sql.parquet.filterPushdown=true
spark.sql.files.maxPartitionBytes=268435456  # ~256MB
```

### 4.2 — Streaming **50k events/s**, fenêtre **10 min**, SLA **60 s**
- Fenêtre 10 min → **30 M events** en vol max (ordre de grandeur)
- Pipeline : parse JSON + enrichissement + aggregate(key)

**Plan recommandé**
- `cores/executor = 4`, `executor_heap = 16g`, `overhead = 2g`
- **24 exécuteurs** → **96 cœurs** totaux ; trigger **5 s**

**Params initiaux**
```
spark.executor.cores=4
spark.executor.memory=16g
spark.executor.memoryOverhead=2g
spark.streaming.backpressure.enabled=true
spark.sql.shuffle.partitions=400
spark.sql.adaptive.enabled=true
spark.sql.streaming.stateStore.maintenanceInterval=60s
```
**Astuces** : surveiller **state size** (Spark UI), **watermarks** pour purge, backpressure ON.

---

## 5) Mémoire & stockage : ce qu’il faut compter
- **Heap** (RDD/DataFrame, encoders, objets)
- **Overhead/off‑heap** (buffers shuffle, sérialisation)
- **Shuffle files** (disque local/réseau)
- **Broadcast** (répliqué par exécuteur)

**Raccourcis**
```
executor_total ≈ executor_heap × 1.1
cluster_RAM    ≈ executor_total × executors
```

---

## 6) Partitions & Shuffle
- Entrée Parquet : **128–256 Mo**/partition
- Garder **2–3× cœurs** tout au long du pipeline (repartition/coalesce)
- **Skew** (clés chaudes) : **salting** + **AQE** (`spark.sql.adaptive.skewJoin.enabled=true`)
- **Broadcast join** si dim ≤ **256–512 Mo** ; sinon éviter le shuffle massif

---

## 7) I/O, formats & réseau
- **Parquet** ≫ CSV/JSON (colonnaire, compression, predicate pushdown)
- **S3** : latence, privilégier gros blocs, **coalesce** en sortie
- **HDFS** : vérifier réplication & throughput par datanode

---

## 8) Dynamic allocation & autoscaling
**ON** (cluster mutualisé, workloads variables)
```
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=2
spark.dynamicAllocation.maxExecutors=80
spark.dynamicAllocation.initialExecutors=10
```
**OFF** (SLA strict & stable) → prédictible, plus simple à profiler

---

## 9) Anti‑patterns & pièges (et comment les éviter)
- Exécuteurs **trop gros** → GC & contention : rester sur **4–6 cœurs**, **16–32 Go heap**
- Trop peu de partitions → CPU sous‑utilisés ; trop → overhead & shuffle gargantuesque
- **UDF** partout → préférer fonctions SQL natives (Catalyst)
- **Nulls** non gérés → `Option`/valeurs par défaut + schémas stricts
- Ignorer Spark UI → toujours profiler **stages**, **tasks**, **skew**, **spilled**

---

## 10) Tableaux de tuning (récap express)
| Élément | Recommandation de départ |
|---|---|
| Cœurs/exécuteur | 4–6 |
| Heap/exécuteur | 16–32 Go |
| Overhead | 7–10 % de la heap |
| Partitions/parallélisme | 2–3 × cœurs totaux |
| Parquet partition | 128–256 Mo |
| Shuffle partitions | 200–600 |
| Broadcast join | ≤ 256–512 Mo |
| Dynamic allocation | ON (mutualisé), OFF (SLA strict) |

---

**Fin — Partie 5A**. Prochaine : **Partie 5B — Mise en production Spark** (templates YAML/JSON, monitoring, check‑list).
