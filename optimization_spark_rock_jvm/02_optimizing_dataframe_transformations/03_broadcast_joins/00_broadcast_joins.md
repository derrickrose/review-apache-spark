# Spark 3.5 — Broadcast joins

Ce fichier ne couvre que le broadcast. Les bases (stratégies de jointure, côté build vs streamé, hints, estimation de `sizeInBytes`, CBO, AQE, liste complète des confs) sont dans `02_joins_recap/joins_and_size_estimation.md`, noté **« G »** ci-dessous.

**Légende de vérification** (la même que G) :

- **(vérifié)** : testé en local sur PySpark 3.5.
- **(script : `NN_….py`)** : un script de ce dossier le reproduit, avec le résultat attendu en commentaire. À lancer pour confirmer.
- **(source)** : confirmé dans la doc officielle ou le code de la branche 3.5 (liste des sources : G, section 17).
- **(non vérifié)** : écrit de mémoire, ni testé ni trouvé dans les sources.

## Sommaire

1. [L'idée en bref](#1-lidée-en-bref)
2. [Le seuil de broadcast automatique](#2-le-seuil-de-broadcast-automatique)
3. [Contraintes du broadcast](#3-contraintes-du-broadcast)
4. [Piège : table plus grosse que son estimation](#4-piège--table-plus-grosse-que-son-estimation)
5. [Forcer ou contourner](#5-forcer-ou-contourner)
6. [AQE : conversion en broadcast à l'exécution](#6-aqe--conversion-en-broadcast-à-lexécution)
7. [Scripts](#7-scripts)

## 1. L'idée en bref

> **En bref :** Spark broadcast une table s'il **sait** qu'elle est petite. S'il ne sait pas, il la suppose gigantesque. (script : `01_max_long.py`)

Spark veut savoir **combien pèse** une table, pour décider s'il peut l'envoyer à tous les executors (broadcast).

**Cas 1 : il sait calculer.** `spark.range(1, 10)` = 9 lignes × 8 octets = 72 octets. C'est petit, il fait le broadcast.

**Cas 2 : il ne sait pas.** Avec un RDD (`sc.parallelize(...)`), Spark ne regarde pas dedans : il ne connaît ni le nombre de lignes, ni le poids. Par prudence, il suppose que c'est **gigantesque** et prend le plus grand nombre possible, `Long.MaxValue`, comme **poids** de la table (≈ 8 exaoctets). Il ne fait pas le broadcast.

`Long.MaxValue` remplace **le poids en octets**, pas le nombre de lignes. Spark ne pense pas « il y a 9 milliards de milliards de lignes », il pense « cette table pèse 8 exaoctets, je n'en sais pas plus ».

Comment Spark calcule ce poids selon la source (`Range`, `LogicalRDD`, fichiers, cache) et comment l'inspecter : G, sections 8 et 10.

## 2. Le seuil de broadcast automatique

> **En bref :** broadcast automatique si `sizeInBytes` estimé < `spark.sql.autoBroadcastJoinThreshold` (10 Mo par défaut). (script : `01_max_long.py`)

| Source | Estimation | Résultat |
|---|---|---|
| `spark.range(1, 10)` | 9 lignes × 8 = 72 octets | broadcast |
| `spark.range(1, 100000000)` | 99 999 999 × 8 ≈ 800 Mo | pas de broadcast |
| `createDataFrame(rdd)` / `createDataFrame(list)` (PySpark) | `Long.MaxValue` = 9 223 372 036 854 775 807 (taille inconnue ; `createDataFrame(list)` passe par `parallelize`, source : `session.py`) | pas de broadcast → SortMergeJoin |

Le seuil compare toujours l'**estimation**, jamais la taille réelle : pour un fichier, c'est en pratique la taille sur disque (section 4).

`spark.sql.autoBroadcastJoinThreshold=-1` désactive le broadcast automatique ; les hints restent actifs (section 5.1).

## 3. Contraintes du broadcast

### 3.1 Côté broadcastable

Seul le côté dont on ne garde pas les lignes sans match peut être broadcasté : à droite pour un left outer / semi / anti, à gauche pour un right outer, aucun pour un full outer, les deux pour un inner.

Tableau complet et explication (côté build vs streamé, exemples `id=3` et `id=7`) : G, section 3. Où placer `broadcast()` : G, section 5.2.

Un hint `broadcast()` sur le mauvais côté est ignoré : rien dans `explain()`, seulement un WARN dans les logs du driver (G, section 5.3). Règle confirmée dans le code : `canBuildBroadcastLeft` = inner / right outer, `canBuildBroadcastRight` = inner / left outer / left semi / left anti (source).

### 3.2 Le broadcast passe par le driver

Le petit côté est collecté sur le driver puis envoyé aux executors. Limites :

- `spark.driver.memory` (1g par défaut) ;
- `spark.driver.maxResultSize` (1g par défaut) ;
- `spark.sql.broadcastTimeout` (300 s par défaut) ;
- 8 Go max par table broadcastée (source : `BroadcastExchangeExec.MAX_BROADCAST_TABLE_BYTES = 8L << 30`).

Un broadcast trop gros se manifeste par un OOM du driver, un dépassement de `maxResultSize` ou un timeout.

## 4. Piège : table plus grosse que son estimation

> **En bref :** une table compressée sur disque, ou avec des arrays, peut passer sous le seuil alors qu'elle est bien plus grosse en mémoire. `fileCompressionFactor` corrige l'estimation des fichiers. (script : `04_file_compression_factor.py`)

### 4.1 Fichiers compressés

Pour du Parquet, `sizeInBytes` = taille des fichiers compressés (G, section 10.2). Une table de 8 Mo en Parquet peut faire beaucoup plus une fois décompressée en mémoire, et être broadcastée quand même (risque d'OOM). `spark.sql.autoBroadcastJoinThreshold` (10 Mo par défaut) s'applique donc en pratique à la taille disque. Correctif possible : `spark.sql.sources.fileCompressionFactor` (1.0 par défaut) multiplie la taille disque.

**Quand utiliser `fileCompressionFactor` ?** Quand la taille disque sous-estime la taille en mémoire (fichiers compressés). Exemple : un Parquet de 8 Mo pèse 40 Mo une fois décompressé. 8 Mo < 10 Mo, donc Spark broadcast, et envoie en réalité 40 Mo au driver puis à chaque executor (risque d'OOM, broadcast lent). En indiquant un ratio de compression de 5 :

```python
spark.conf.set("spark.sql.sources.fileCompressionFactor", "5")
```

L'estimation devient 8 Mo × 5 = 40 Mo > 10 Mo, donc pas de broadcast automatique → SortMergeJoin.

- S'applique uniquement aux sources fichiers lues directement (`spark.read.parquet(...)`…), pas aux RDD, `range` ou tables en cache (G, section 10.1).
- Facteur global unique : le choisir d'après le ratio réel (taille des fichiers vs taille du DataFrame en cache, onglet **Storage** de la Spark UI). Le script `04_file_compression_factor.py` calcule ce ratio. Attention : le cache est lui aussi compressé (`spark.sql.inMemoryColumnarStorage.compressed`, `true` par défaut, source), donc ce ratio peut être plus faible qu'on ne le pense.
- Alternative : garder le facteur à 1 et baisser `spark.sql.autoBroadcastJoinThreshold`.

### 4.2 Arrays et maps

Même piège avec les colonnes `array` / `map`, estimées à **1 seul élément** : une colonne `array<int>` de 1 000 entiers par ligne compte 4 octets au lieu de ~4 000 (G, section 8.2).

## 5. Forcer ou contourner

> **En bref :** `broadcast()` force le broadcast ; `cache()` + action donne à Spark la vraie taille d'un RDD. (script : `05_force_or_cache.py`)

### 5.1 Forcer le broadcast

```python
from pyspark.sql.functions import broadcast
joined = table.join(broadcast(lookup_table), "id")
```

- Le hint fonctionne même avec `spark.sql.autoBroadcastJoinThreshold=-1`.
- Syntaxe SQL des hints, alias et vérification dans `explain()` (`BuildRight` / `BuildLeft`) : G, sections 5 et 6.

### 5.2 Contourner l'estimation inconnue d'un RDD : `cache()` + action

Une fois matérialisé, le cache donne la taille réelle, et le broadcast se décide dès la planification (vérifié) :

```python
lookup_table.cache(); lookup_table.count()
table.join(lookup_table, "id")   # → BroadcastHashJoin
```

## 6. AQE : conversion en broadcast à l'exécution

> **En bref :** AQE peut transformer un SortMergeJoin en BroadcastHashJoin une fois les vraies tailles connues, mais le shuffle est déjà payé, et il refuse si trop de partitions sont vides. (script : `06_aqe_conversion.py`)

Ce qu'est AQE et `isFinalPlan` : G, section 12.

- `explain()` montre le plan avant exécution (`isFinalPlan=false`). AQE peut convertir le SortMergeJoin en BroadcastHashJoin à l'exécution, mais seulement après avoir matérialisé le shuffle des deux côtés (shuffle write payé, puis lecture locale via `AQEShuffleRead local`).
- Dans ce cas précis, AQE **ne convertit pas** : le petit côté n'a que 4 partitions non vides sur 200 (`spark.sql.shuffle.partitions`, 200 par défaut) (2 %), sous le seuil `spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin` (0.2 par défaut). Spark rétrograde alors le broadcast et garde le SortMergeJoin.

Le seuil AQE (`spark.sql.adaptive.autoBroadcastJoinThreshold`, par défaut même valeur que `spark.sql.autoBroadcastJoinThreshold`) n'utilise ni l'estimation sans CBO ni celle avec CBO : il compare la taille réelle des données de shuffle écrites, à l'exécution (source : `canBroadcastBySize` utilise ce seuil quand les stats sont « runtime »).

La doc officielle résume l'intérêt : c'est moins efficace qu'un broadcast décidé dès la planification, mais mieux que de continuer le SortMergeJoin, car on évite le tri des deux côtés et on lit les fichiers de shuffle en local si `spark.sql.adaptive.localShuffleReader.enabled` est `true` (source : doc *Performance Tuning*).

Le script montre aussi les deux façons de débloquer la conversion : baisser `nonEmptyPartitionRatioForBroadcastJoin`, ou réduire `spark.sql.shuffle.partitions` (4 / 8 = 50 % > 0.2).

Toutes les confs et leurs valeurs par défaut : G, section 14.

## 7. Scripts

| Script | Sections |
|---|---|
| `01_innocent_join.py` | 1, 2, 6 (exemple du cours : RDD de 4 lignes non broadcasté) |
| `01_max_long.py` | 1 (`Long.MaxValue`, `rowCount` vide), 2 (tableau du seuil) |
| `04_file_compression_factor.py` | 4 (taille disque vs mémoire, effet du facteur) |
| `05_force_or_cache.py` | 5 (`broadcast()`, seuil à `-1`, `cache()` + action) |
| `06_aqe_conversion.py` | 6 (conversion refusée puis acceptée) |
