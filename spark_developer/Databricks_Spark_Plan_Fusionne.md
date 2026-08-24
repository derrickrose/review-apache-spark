# Databricks Certified Associate Developer for Apache Spark — Plan fusionné (5 jours)

## OBJECTIF

Préparer l'examen en 5 jours de manière ultra-intensive et pragmatique.

Temps recommandé : 9–10 h/jour.

Principe :
- 40 % apprentissage
- 30 % pratique PySpark
- 30 % questions / mocks
- priorité aux sujets les plus susceptibles de faire gagner des points
- pas de lecture passive pendant des heures
- chaque concept doit être compris puis testé avec des questions

> ⚠️ Databricks ne publie pas de pondération officielle en % (ni en heures) par domaine. Les priorités et temps ci-dessous sont donc une stratégie de préparation, pas une pondération officielle.

## FORMAT DE L'EXAMEN

- 45 questions notées
- 90 minutes
- environ 2 minutes par question
- questions à choix multiples
- documentation/API non disponible pendant l'examen
- certification valable 2 ans

## PRIORITÉS (avec estimation de temps)

| # | Domaine                              | Priorité | Temps indicatif |
| - | ------------------------------------- | -------: | ---------------: |
| 1 | DataFrame / PySpark API               |    ⭐⭐⭐⭐⭐ |             10 h |
| 2 | Spark Architecture                    |    ⭐⭐⭐⭐⭐ |              7 h |
| 3 | Joins / Aggregations / Spark SQL / I/O |    ⭐⭐⭐⭐⭐ |              8 h |
| 4 | Troubleshooting / Performance / Tuning |    ⭐⭐⭐⭐⭐ |              7 h |
| 5 | Structured Streaming                  |     ⭐⭐⭐⭐ |              5 h |
| 6 | Questions / Mocks                     |    ⭐⭐⭐⭐⭐ |              7 h |
| 7 | UDF / State / Broadcast / Accumulators |    ⭐⭐⭐   |              — |
| 8 | Spark Connect                         |      ⭐⭐⭐ |              1 h |
| 9 | Pandas API on Spark                   |      ⭐⭐⭐ |              1 h |

---

# DOMAINE 1 — SPARK ARCHITECTURE & COMPONENTS

## Architecture

Connaître parfaitement :

```text
Spark Application
       ↓
     Driver
       ↓
      Job
       ↓
     Stages
       ↓
     Tasks
       ↓
   Executors
```

Connaître :
- Spark Application
- SparkSession
- Driver
- Worker
- Executor
- CPU cores
- Memory
- Cluster
- DataFrame
- Dataset

## Execution model

Comprendre :
- transformations
- actions
- lazy evaluation
- plan d'exécution
- jobs, stages, tasks
- partitions

Transformations importantes : select, filter, map, withColumn, groupBy, join, distinct, orderBy, repartition

Actions importantes : count, collect, show, take, first, write

## Lazy evaluation

Transformation → plan logique → Action → exécution.

## Partitions

Comprendre : partition, nombre de partitions, parallélisme, distribution des données, shuffle, partitionnement, `spark.sql.shuffle.partitions`.

## Cache

Connaître : `cache()`, `persist()`, `unpersist()`, storage levels. Comprendre quand le cache est utile et quand il gaspille la mémoire.

## Garbage Collection

Comprendre : JVM, heap, garbage collection, pression mémoire, executor OOM.

## Modules Spark

Reconnaître : Spark Core, Spark SQL, DataFrame, Structured Streaming, Pandas API on Spark, MLlib.

---

# DOMAINE 2 — SPARK SQL

## Read / Write

```python
spark.read
df.write
```

Formats : CSV, JSON, ORC, Text, Delta, JDBC

## Options

schema, inferSchema, header, delimiter, mode

## Save modes

append, overwrite, error/errorIfExists, ignore

## Partitioning

```python
df.write.partitionBy("country")
```

Comprendre : partitionnement, partition pruning, choix d'une bonne colonne, problème des trop nombreuses partitions, problème des petites partitions.

## Persistent tables

Comprendre : tables persistantes, partitionnement, organisation, récupération des données.

## Temporary views

```python
df.createOrReplaceTempView("employees")
spark.sql("SELECT * FROM employees")
```

## SQL

SELECT, WHERE, GROUP BY, HAVING, ORDER BY, JOIN, UNION

---

# DOMAINE 3 — DATAFRAME / DATASET API

**PRIORITÉ MAXIMALE.**

## DataFrame basics

```python
df.select()
df.selectExpr()
df.filter()
df.where()
df.withColumn()
df.withColumnRenamed()
df.drop()
df.alias()
df.distinct()
df.limit()
df.orderBy()
df.sort()
```

Objectif : être capable de lire un code PySpark et prédire le résultat.

## Columns

```python
col()
lit()
when()
otherwise()
cast()
coalesce()
isNull()
isNotNull()
```

## String functions

```python
concat()
concat_ws()
split()
regexp_replace()
lower()
upper()
trim()
substring()
length()
```

## Arrays

```python
array()
array_contains()
size()
explode()
explode_outer()
posexplode()
```

Comprendre parfaitement `explode()`. Faire au moins 15 exercices.

## Structs

```python
df.select("address.city")
```

Comprendre : StructType, StructField, nested fields.

## Null / Missing Data

```python
df.na.drop()
df.na.fill()
df.na.replace()
```

Comprendre la différence entre NULL, NaN, chaîne vide, colonne manquante.

## Deduplication

```python
dropDuplicates()
dropDuplicates(["id"])
```

## Aggregations

```python
groupBy()
agg()
count()
countDistinct()
approx_count_distinct()
sum()
avg()
mean()
min()
max()
```

Comprendre la différence entre `count("*")`, `count("column")`, `countDistinct("column")`.

## Summary

```python
df.summary()
```

## Dates / timestamps

Concepts : Unix epoch, date, timestamp, conversion epoch → date, conversion date → string.

```text
year()
month()
dayofmonth()
hour()
date_add()
date_sub()
datediff()
months_between()
to_date()
to_timestamp()
date_format()
unix_timestamp()
```

## Sorting

`orderBy()`, `sort()`, ascending, descending

## Schema

`df.printSchema()`, `df.schema`, StructType, StructField, data types, nullable

## Collect / Rows

`collect()`, `take()`, `first()`

⚠️ `collect()` ramène les données au Driver → risque d'OOM si volume important.

---

# JOINS

`inner`, `left`, `right`, `full`, `cross`, `left_semi`, `left_anti`

- **Inner** : retourne les correspondances des deux côtés.
- **Left** : garde toutes les lignes de gauche.
- **Right** : garde toutes les lignes de droite.
- **Full** : garde les lignes des deux côtés.
- **Cross** : produit cartésien.
- **Left Semi** : lignes de gauche qui ont une correspondance à droite.
- **Left Anti** : lignes de gauche qui n'ont pas de correspondance à droite.

Astuce mémo :
```text
Je veux les lignes qui existent dans l'autre table → LEFT SEMI
Je veux les lignes qui n'existent pas → LEFT ANTI
```

## Multiple keys / colonnes dupliquées

Pratiquer : plusieurs clés, aliases, colonnes dupliquées, nulls, mêmes noms de colonnes.

## Broadcast join

Comprendre : petit dataset, broadcast vers les executors, réduction potentielle du shuffle, limite liée à la mémoire.

```python
from pyspark.sql.functions import broadcast
df1.join(broadcast(df2), "id")
```

---

# UNION

```python
union()
unionByName()
```

`union()` → correspondance par position.
`unionByName()` → correspondance par nom.

Comprendre également le principe de UNION ALL.

---

# UDF / STATE / VARIABLES

- **UDF** : définition, création, invocation, coût potentiel, pourquoi les fonctions natives Spark sont généralement préférables.
- **Stateful operators** : comprendre le principe du state.
- **StateStore** : son rôle dans les opérations stateful.
- **Broadcast variables** : petite donnée distribuée aux executors, accès local par les tasks, différence entre broadcast variable et broadcast join.
- **Accumulators** : rôle, utilisation, limitations, différence avec une variable normale.

---

# DOMAINE 4 — TROUBLESHOOTING & TUNING

## repartition() vs coalesce()

```text
repartition() → redistribution complète → shuffle
coalesce()    → principalement réduction → moins de shuffle
```

## Shuffle

```text
Partition → redistribution → réseau → disque → nouvelles partitions
```

Opérations pouvant provoquer du shuffle : `groupBy()`, `join()`, `distinct()`, `orderBy()`, `repartition()`

## Data Skew

Exemple conceptuel :
```text
Partition 1 → 10 000 000 lignes
Partition 2 → 10 000 lignes
Partition 3 → 15 000 lignes
Partition 4 → 8 000 lignes
```

Conséquences : task très lente, stage ralenti, mauvaise utilisation des ressources, temps d'exécution élevé.

Stratégies : broadcast, meilleur partitionnement, salting, réduire les données avant le join, AQE, éviter les opérations inutiles.

## AQE — Adaptive Query Execution

Optimisation dynamique, adaptation du plan, optimisation des partitions, optimisation des joins, gestion du skew.

## Spark UI / Monitoring

Connaître : Jobs, Stages, Tasks, Executors, SQL, Storage, logs.

Savoir diagnostiquer :
- **OOM** → trop de données en mémoire, `collect()` excessif, cache excessif, partition trop grosse
- **Task beaucoup plus lente** → data skew, mauvais partitionnement, mauvaise distribution des données
- **Shuffle énorme** → join, groupBy, orderBy, distinct, repartition
- **Performance mauvaise** → analyser Spark UI, Driver logs, Executor logs, partitions, shuffle, skew, mémoire

---

# DOMAINE 5 — STRUCTURED STREAMING

## Architecture

```text
Source
 ↓
Streaming DataFrame
 ↓
Transformations
 ↓
Sink
```

## Streaming DataFrame

`spark.readStream`, `df.writeStream`, trigger, output mode, checkpoint, sink

## Output modes

- **Append** : ajoute les nouvelles lignes au résultat.
- **Update** : met à jour les résultats qui ont changé.
- **Complete** : réécrit l'ensemble du résultat.

## Watermark

```text
Données en retard → Spark conserve du state → watermark → nettoyage de l'ancien state
```

Comprendre : event time, late data, watermark, state, state cleanup.

## Windows

Fenêtres temporelles, event time, aggregation, watermark.

## Streaming deduplication

Comprendre la différence entre déduplication **sans** watermark et déduplication **avec** watermark, et l'impact sur la conservation du state.

## Checkpoint / Recovery / Exactly-once

Comprendre : checkpoint, state, recovery, fault tolerance.

Connaître la différence entre at-most-once, at-least-once, exactly-once.

---

# DOMAINE 6 — SPARK CONNECT

Petit domaine — ne pas y passer plusieurs heures.

Comprendre : architecture client/server, séparation client/serveur, communication avec Spark.

Deployment modes : Client, Cluster, Local.

Objectif : comprendre les concepts et répondre aux questions théoriques.

---

# DOMAINE 7 — PANDAS API ON SPARK

Petit domaine.

Comprendre : différence avec Pandas classique, exécution distribuée, avantages, limites, cas d'utilisation.

**Pandas UDF** : définition, création, invocation, pourquoi l'utiliser.

Ne pas chercher à devenir expert Pandas en 5 jours.

---

# 📅 JOUR 1 — ARCHITECTURE + DATAFRAME API

## 08:00–08:30 — Architecture minimale

À connaître : Spark Application, SparkSession, Driver, Executor, Worker, Job, Stage, Task, Partition, DataFrame, Dataset.

## 08:30–10:00 — DataFrame basics

```python
df.select()
df.selectExpr()
df.filter()
df.where()
df.withColumn()
df.withColumnRenamed()
df.drop()
df.alias()
df.distinct()
df.limit()
df.orderBy()
df.sort()
```

Objectif : être capable de lire un code PySpark et prédire le résultat.

## 10:15–11:45 — Column expressions

```python
col()
lit()
when()
otherwise()
cast()
isNull()
isNotNull()
coalesce()
```

Strings :
```python
concat()
concat_ws()
split()
regexp_replace()
lower()
upper()
trim()
substring()
length()
```

## 11:45–12:30 — Null / Missing Data

```python
df.na.drop()
df.na.fill()
df.na.replace()
```

Comprendre : NULL, NaN, empty string, missing column.

## 13:30–15:00 — Arrays / Structs / Explode

```python
explode()
explode_outer()
posexplode()
array()
array_contains()
size()
```

Structs : `col("address.city")`

Faire au moins 15 exercices.

## 15:15–16:45 — Aggregations

```python
groupBy()
agg()
count()
countDistinct()
approx_count_distinct()
sum()
avg()
mean()
min()
max()
```

Comprendre les différences entre `count("*")`, `count("column")`, `countDistinct("column")`.

## 16:45–17:30 — Dates / timestamps

```text
year, month, day, hour
date_add, date_sub, datediff, months_between
to_date, to_timestamp, date_format, unix_timestamp
```

## 17:30–18:00 — Fiche de révision

Créer une fiche : *toutes les fonctions PySpark que je dois connaître par cœur.*

## 19:00–21:00 — Questions

**40 questions chronométrées.**

🎯 Objectif : **70 %+**

---

# 📅 JOUR 2 — JOINS + SPARK SQL + I/O

## 08:00–09:30 — Joins

`inner`, `left`, `right`, `full`, `cross`, `left_semi`, `left_anti` — comprendre exactement le résultat de chaque type.

## 09:30–10:30 — Join conditions

Pratiquer : plusieurs clés, aliases, colonnes dupliquées, nulls, mêmes noms de colonnes.

## 10:45–11:45 — Semi / Anti joins

```text
Je veux les lignes qui existent dans l'autre table → LEFT SEMI
Je veux les lignes qui n'existent pas → LEFT ANTI
```

## 11:45–12:30 — Broadcast join

Principe, intérêt, fonctionnement, quand l'utiliser.

## 13:30–14:15 — Union

```python
union()
unionByName()
```

Comprendre les différences de comportement avec l'ordre des colonnes.

## 14:15–15:30 — Spark SQL

```python
createOrReplaceTempView()
spark.sql()
```

SQL : SELECT, WHERE, GROUP BY, HAVING, ORDER BY, JOIN, UNION

Être capable de résoudre le même problème en PySpark et en SQL.

## 15:45–17:00 — Read / Write

Formats : CSV, JSON, ORC, Text, Delta, JDBC

```python
spark.read
spark.write
```

Options : schema, inferSchema, header, delimiter, mode

## 17:00–18:00 — Save modes + partitioning

`append`, `overwrite`, `error/errorIfExists`, `ignore`

```python
partitionBy()
```

Avantages et limites du partitioning.

## 19:00–21:00 — Questions

**50 questions.**

🎯 Objectif : **75 %+**

---

# 📅 JOUR 3 — SPARK ARCHITECTURE + PERFORMANCE

## 08:00–09:00 — Execution model

```text
Application → Job → Stage → Task
Driver → Executors → Tasks
```

## 09:00–10:00 — Transformations / Actions

Transformations : select, filter, withColumn, join, groupBy
Actions : count, collect, show, take, first, write

Comprendre la **lazy evaluation**.

## 10:15–11:30 — Narrow vs Wide

Narrow : filter, map, select
Wide : groupBy, join, distinct, orderBy, repartition

Comprendre pourquoi les wide transformations peuvent provoquer un **shuffle**.

## 11:30–12:30 — Partitions

```python
repartition()
coalesce()
```

Augmentation/diminution des partitions, shuffle, coût relatif, cas d'utilisation.

## 13:30–14:30 — Shuffle

Network I/O, disk I/O, serialization, coût, data movement, skew.

## 14:30–15:30 — Cache / Persist

```python
df.cache()
df.persist()
df.unpersist()
```

Storage levels et quand le cache est utile.

## 15:45–16:45 — Data Skew

Reconnaître des partitions déséquilibrées ; comprendre broadcast, salting, AQE.

## 16:45–17:30 — AQE

Adaptation du plan, optimisation, gestion des partitions et du skew.

## 17:30–18:30 — Spark UI

Jobs, Stages, Tasks, Executors, SQL, Storage, logs.

Diagnostiquer : OOM, shuffle excessif, skew, task lente, cluster sous-utilisé.

## 19:30–21:30 — Questions

**50 questions.**

🎯 Objectif : **75–80 %+**

---

# 📅 JOUR 4 — STRUCTURED STREAMING + SPARK CONNECT + PANDAS API

## 08:00–09:00 — Structured Streaming

```text
Source → Streaming DataFrame → Transformations → Sink
```

## 09:00–10:00 — Streaming DataFrames

`readStream`, `writeStream`, trigger, output mode, checkpoint, sink

## 10:15–11:15 — Output modes

`append`, `complete`, `update` — quand chaque mode est utilisé.

## 11:15–12:15 — Watermark

Event time, late data, watermark, state, state cleanup.

## 12:15–13:00 — Streaming aggregations

Windows, aggregations, watermark, deduplication.

## 14:00–15:00 — Streaming deduplication

Différence entre déduplication sans watermark et avec watermark.

## 15:15–16:00 — Exactly-once / Fault tolerance

Checkpoint, state, recovery, fault tolerance, exactly-once.

## 16:00–16:30 — UDF + State + Broadcast + Accumulators

UDF, StateStore, broadcast variables, accumulators.

## 16:30–17:15 — Spark Connect

Architecture client/server, différence avec Spark traditionnel, local, cluster, client deployment.

## 17:15–18:00 — Pandas API on Spark

Pandas classique vs Pandas API on Spark, avantages, limites, Pandas UDF.

## 18:00–18:15 — Fiche finale

```text
Streaming
Watermark
Output modes
Checkpoint
Exactly-once
Spark Connect
Pandas API
Pandas UDF
```

## 19:00–20:30 — Questions

**45 questions mixtes.**

## 20:30–21:30 — Correction

Classer les erreurs :
```text
🔴 Je ne connais pas
🟠 Je connais mais j'hésite
🟢 Erreur d'inattention
```

---

# 🔥 JOUR 5 — MODE EXAMEN

## 08:00–08:45 — Révision

Priorité : DataFrame API, Joins, Aggregations, Partitions, Shuffle, Cache, Broadcast, Streaming.

## 08:45–10:15 — MOCK #1

**45 questions / 90 minutes.** Conditions réelles : pas de documentation, chronomètre, aucune aide.

## 10:15–11:30 — Correction

Pour chaque erreur :
```text
Question → Ma réponse → Pourquoi c'était faux → Bonne réponse → Concept à retenir
```

## 11:30–12:30 — Weak points

Travailler uniquement les domaines où le score est faible.

## 13:30–15:00 — MOCK #2

**45 questions / 90 minutes.** 🎯 Objectif : **80 %+**

## 15:00–16:00 — Correction

## 16:00–17:00 — Révision des pièges

Focus : joins, partitions, shuffle, UDF, aggregations, streaming, Spark Connect.

## 17:00–18:30 — MOCK #3

**45 questions / 90 minutes.** 🎯 Objectif : **85 %+**

## 18:30–19:15 — Correction

## 19:15–20:00 — Dernière fiche mentale

Être capable d'expliquer sans notes :

1. Pourquoi Spark est lazy ?
2. Différence `repartition()` / `coalesce()` ?
3. Qu'est-ce qu'un shuffle ?
4. Quand utiliser broadcast join ?
5. Pourquoi une task peut être beaucoup plus lente ?
6. Quand utiliser cache/persist ?
7. Qu'est-ce qu'un watermark ?
8. Différence append/update/complete ?
9. Driver vs Executor ?
10. Job vs Stage vs Task ?

## 20:00 — STOP

Dormir correctement. Pas de nuit blanche.

---

# LES 20 CONCEPTS À SAVOIR SANS HÉSITER

1. Driver vs Executor
2. Worker vs Executor
3. Application vs Job
4. Job vs Stage
5. Stage vs Task
6. Transformation vs Action
7. Lazy evaluation
8. Narrow vs Wide transformation
9. Shuffle
10. repartition vs coalesce
11. cache vs persist
12. Data skew
13. AQE
14. Broadcast join
15. Inner vs Left join
16. Left Semi vs Left Anti
17. Append vs Update vs Complete
18. Watermark
19. Checkpoint
20. Spark Connect

---

# 🎯 CHECKLIST FINALE

## Architecture
- [ ] Driver
- [ ] Executor
- [ ] Worker
- [ ] Application
- [ ] Job
- [ ] Stage
- [ ] Task
- [ ] Partition
- [ ] SparkSession
- [ ] Lazy evaluation
- [ ] Transformations
- [ ] Actions
- [ ] Cache / Persist
- [ ] Garbage Collection

## Spark SQL
- [ ] CSV / JSON / ORC / Text / Delta / JDBC
- [ ] Schema / inferSchema
- [ ] Save modes
- [ ] partitionBy
- [ ] Temporary views
- [ ] Spark SQL (SELECT/WHERE/GROUP BY/HAVING/ORDER BY/JOIN/UNION)

## DataFrame API
- [ ] select / selectExpr / filter / where / withColumn / withColumnRenamed / drop / alias
- [ ] distinct / limit / orderBy / sort
- [ ] explode / arrays / structs
- [ ] null handling
- [ ] deduplication
- [ ] aggregations
- [ ] dates / timestamps
- [ ] schema
- [ ] collect / Rows

## Joins
- [ ] Inner / Left / Right / Full / Cross
- [ ] Left Semi / Left Anti
- [ ] Multiple keys
- [ ] Broadcast join
- [ ] Union / UnionByName

## UDF / State / Variables
- [ ] UDF
- [ ] Stateful operators
- [ ] StateStore
- [ ] Broadcast variables
- [ ] Accumulators

## Performance
- [ ] repartition / coalesce
- [ ] shuffle
- [ ] cache / persist / storage levels
- [ ] data skew
- [ ] AQE
- [ ] Spark UI
- [ ] Driver / Executor logs
- [ ] OOM

## Structured Streaming
- [ ] readStream / writeStream
- [ ] Source / Sink
- [ ] Output modes (append/update/complete)
- [ ] Watermark / event time / late data
- [ ] Windows / aggregation
- [ ] Deduplication / state
- [ ] Checkpoint / recovery / fault tolerance
- [ ] Exactly-once

## Spark Connect
- [ ] Client/server architecture
- [ ] Client / Cluster / Local mode

## Pandas API
- [ ] Pandas API on Spark
- [ ] Pandas UDF

---

# SI TU MANQUES DE TEMPS

Priorité :
1. DataFrame API
2. Joins
3. Aggregations
4. Spark Architecture
5. Partitions / Shuffle
6. Performance / Skew / AQE
7. Spark SQL / I/O
8. Structured Streaming
9. UDF / State / Broadcast / Accumulators
10. Spark Connect
11. Pandas API on Spark

Ne passe pas plusieurs heures sur Spark Connect ou Pandas API — utilise ce temps pour DataFrame, joins, performance ou streaming.

---

# MÉTHODE POUR CHAQUE SUJET

1. Comprendre le concept — 20 min
2. Coder / manipuler — 30 à 45 min
3. Faire des questions — 20 à 30 min
4. Corriger — 15 min
5. Noter les pièges

Règle : **Comprendre → pratiquer → questions → corriger → recommencer.**

---

# STRATÉGIE LE JOUR DE L'EXAMEN

**Première passe :**
- répondre immédiatement aux questions faciles
- marquer les questions difficiles
- avancer, ne pas perdre 5 minutes sur une question

**Deuxième passe :**
- revenir aux questions marquées
- éliminer les réponses manifestement fausses
- choisir la meilleure réponse

Toujours vérifier : type de join, ordre des colonnes, null, partition, shuffle, action vs transformation, output mode, watermark, checkpoint, Driver vs Executor.

---

# 📈 CRITÈRE POUR PASSER L'EXAMEN

| Score aux mocks         | Décision               |
| ----------------------- | ---------------------- |
| <65 %                   | ❌ Ne pas passer        |
| 65–70 %                 | ⚠️ Risqué              |
| 70–75 %                 | 🟠 Réviser             |
| 75–80 %                 | 🟢 Envisageable        |
| 80–85 %                 | 🟢 Bonne préparation   |
| **85 %+ sur 2–3 mocks** | 🟢 **Passer l'examen** |

## Critère final détaillé

Tu es prêt si :
- Mock #1 ≥ 80 %
- Mock #2 ≥ 80 %
- Mock #3 ≥ 85 %
- tu peux expliquer pourquoi la bonne réponse est correcte
- tu peux expliquer pourquoi les mauvaises réponses sont fausses
- tu comprends les principaux concepts sans documentation
- tu lis rapidement du code PySpark
- tu identifies immédiatement les problèmes de join, partition, shuffle, skew et memory
- tu réponds sans hésitation aux fondamentaux du Structured Streaming

## Règle principale

Ne cherche pas seulement à mémoriser les réponses. Pour chaque question, demande-toi :

> **Quel concept Spark cette question teste-t-elle ?**

Objectif final :

**Comprendre → Pratiquer → Questions → Correction → Mock → Weak points → Révision → Mock → 85 %+ → EXAMEN.**
