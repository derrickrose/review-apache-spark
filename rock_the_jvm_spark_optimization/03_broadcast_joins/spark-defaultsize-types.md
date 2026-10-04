# Spark 3.5 — Taille par défaut des types (`defaultSize`)

Valeurs utilisées par l'optimiseur (Catalyst) pour **estimer** la taille d'un plan (`sizeInBytes`) quand le nombre de lignes est connu. Elles ne reflètent pas l'occupation mémoire réelle.

Vérifiées en local sur PySpark 3.5 via `DataType.defaultSize()`.

## Types simples

| Type Spark | Octets |
|---|---|
| `BooleanType` | 1 |
| `ByteType` | 1 |
| `ShortType` | 2 |
| `IntegerType` | 4 |
| `LongType` | 8 |
| `FloatType` | 4 |
| `DoubleType` | 8 |
| `DecimalType` (précision ≤ 18) | 8 |
| `DecimalType` (précision > 18) | 16 |
| `StringType` | 20 (valeur arbitraire) |
| `BinaryType` | 100 (valeur arbitraire) |
| `DateType` | 4 |
| `TimestampType` / `TimestampNTZType` | 8 |
| `NullType` | 1 |
| `DayTimeIntervalType` | 8 |
| `YearMonthIntervalType` | 4 |

## Types complexes

| Type | Règle | Exemple |
|---|---|---|
| `ArrayType` | taille d'un seul élément | `array<int>` = 4 |
| `MapType` | clé + valeur (une seule entrée) | `map<string,bigint>` = 20 + 8 = 28 |
| `StructType` | somme des champs | `struct<a:int,b:string>` = 4 + 20 = 24 |

## Application : broadcast automatique

Spark broadcast automatiquement un côté de la jointure si son `sizeInBytes` estimé est inférieur à `spark.sql.autoBroadcastJoinThreshold` (10 Mo par défaut).

| Source | Estimation | Résultat |
|---|---|---|
| `spark.range(1, 10)` | 9 lignes × 8 = 72 octets | broadcast |
| `spark.range(1, 100000000)` | 99 999 999 × 8 ≈ 800 Mo | pas de broadcast |
| `createDataFrame(rdd)` / `createDataFrame(list)` (PySpark) | `Long.MaxValue` = 9 223 372 036 854 775 807 (taille inconnue) | pas de broadcast → SortMergeJoin |

- `Range` : taille calculée par arithmétique (`(end - start) / step × 8`), sans lire les données.
- `LogicalRDD` : Spark ne peut pas connaître la taille sans exécuter le RDD, il utilise `spark.sql.defaultSizeInBytes` (`Long.MaxValue`) comme sentinelle « inconnue ». Ce n'est pas un nombre de lignes.
- `explain()` montre le plan avant exécution (`isFinalPlan=false`). AQE peut convertir le SortMergeJoin en BroadcastHashJoin à l'exécution, mais seulement après avoir matérialisé le shuffle des deux côtés (shuffle write payé, puis lecture locale via `AQEShuffleRead local`).
- Dans ce cas précis, AQE **ne convertit pas** : le petit côté n'a que 4 partitions non vides sur 200 (2 %), sous le seuil `spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin` (0.2). Spark rétrograde alors le broadcast et garde le SortMergeJoin.

Forcer le broadcast :

```python
from pyspark.sql.functions import broadcast
joined = table.join(broadcast(lookup_table), "id")
```

Inspecter l'estimation :

```python
df._jdf.queryExecution().optimizedPlan().stats().sizeInBytes()
```

## Points complémentaires

**1. Contourner l'estimation inconnue d'un RDD : `cache()` + action.** Une fois matérialisé, le cache donne la taille réelle, et le broadcast se décide dès la planification (vérifié) :

```python
lookup_table.cache(); lookup_table.count()
table.join(lookup_table, "id")   # → BroadcastHashJoin
```

**2. Un filtre ne réduit pas l'estimation (sans CBO).** `spark.range(1, 1000000).filter("id < 10")` reste estimé à ~8 Mo. Il faut `spark.sql.cbo.enabled=true` et `ANALYZE TABLE ... COMPUTE STATISTICS FOR COLUMNS` pour que Spark évalue la sélectivité.

**3. Sources fichiers : taille sur disque.** Pour du Parquet, `sizeInBytes` = taille des fichiers compressés. Une table de 8 Mo en Parquet peut faire beaucoup plus une fois décompressée en mémoire, et être broadcastée quand même (risque d'OOM).

**4. Le broadcast passe par le driver.** Le petit côté est collecté sur le driver puis envoyé aux executors. Limites : `spark.driver.memory`, `spark.driver.maxResultSize`, `spark.sql.broadcastTimeout` (300 s), 8 Go max par table broadcastée.

**5. Côté broadcastable selon le type de jointure.**

| Jointure | Côté broadcastable |
|---|---|
| inner | gauche ou droite |
| left outer / left semi / left anti | droite uniquement |
| right outer | gauche uniquement |
| full outer | aucun |

Un hint `broadcast()` sur le mauvais côté est ignoré silencieusement.

**6. Réglages utiles.**
- `spark.sql.autoBroadcastJoinThreshold=-1` : désactive le broadcast automatique (les hints restent actifs).
- `spark.sql.adaptive.autoBroadcastJoinThreshold` : seuil distinct pour les décisions d'AQE à l'exécution.
- `spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin` (0.2) : en dessous, AQE refuse de convertir en broadcast.
- Hints SQL : `BROADCAST`, `MERGE`, `SHUFFLE_HASH`, `SHUFFLE_REPLICATE_NL`.

## AQE : `isFinalPlan`

`isFinalPlan` est un drapeau d'état de l'`AdaptiveSparkPlanExec` (nœud racine posé par AQE). Il passe à `true` uniquement quand ce plan a été exécuté jusqu'au bout.

1. Avant action : le plan est découpé en *query stages* aux frontières de shuffle/broadcast → `isFinalPlan=false`.
2. Pendant l'exécution : à chaque stage terminé, AQE récupère les stats réelles (taille des partitions, octets écrits) et ré-optimise la suite (coalescing, conversion en broadcast, skew…).
3. Tous les stages matérialisés : AQE crée et exécute le stage final → `isFinalPlan=true`, `explain()` affiche `Final Plan` + `Initial Plan`.

Piège (vérifié) :

| Moment | `isFinalPlan` |
|---|---|
| avant action | `false` |
| après `df.show()` | `false` |
| après `df.collect()` | `true` |

`show()` exécute un nouveau plan (avec `limit`), pas celui du DataFrame : `df.explain()` reste à `false`. Pour voir le plan final : onglet **SQL** de la Spark UI, ou `explain()` après une action qui exécute le plan complet (`collect()`, `write`…).

## Sources

- Code source : `sql/api/src/main/scala/org/apache/spark/sql/types/` (chaque type redéfinit `defaultSize`, ex. `StringType.scala` : `override def defaultSize: Int = 20`).
- Scaladoc : `org.apache.spark.sql.types.DataType.defaultSize`.
- Doc officielle (config uniquement) : Spark SQL *Performance Tuning* — `spark.sql.autoBroadcastJoinThreshold`, hints de jointure.
