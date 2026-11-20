# 04 - Serialization part 2 (Kryo) : Scala vs PySpark

Sources : `04_kryo_serialization.pdf`, `scala/part5boost/KryoSerializer.scala`,
code PySpark : [04_serialization_problems_part_2.py](04_serialization_problems_part_2.py)

## Le cours Scala

Remplacer la Java serialization par **Kryo** :
- rapide et économe en mémoire ;
- ne sait pas tout sérialiser ;
- demande d'enregistrer les classes (`spark.kryo.registrationRequired=true`, penser aux `Array[...]`).

```scala
val sparkConf = new SparkConf()
  .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
  .set("spark.kryo.registrationRequired", "true")
  .registerKryoClasses(Array(classOf[Person], classOf[Array[Person]]))
```

Annoncé : avec cache et shuffle, **10-20 % plus rapide, 20-30 % de mémoire en moins**
(mesuré dans le cours : cache 254 → 164 Mo, shuffle 72 → 43 Mo, 10M `Person`).

## Pourquoi Kryo ne s'applique pas à PySpark

Kryo sérialise des **objets JVM**. En PySpark :

- les objets Python sont **toujours sérialisés côté Python** (pickle par défaut, ou marshal) ; la JVM ne voit que des tableaux d'octets ;
- les DataFrames (Scala comme Python) utilisent le format binaire de Spark SQL (**Tungsten**),
  sans Java ni Kryo.

`spark.serializer=KryoSerializer` est accepté en PySpark mais n'a pas d'effet mesurable
(testé : cache 4.14 Mo et shuffle 4.02 Mo, avec ou sans Kryo ; temps dans le bruit).

| Situation | Kryo utilisé ? |
|---|---|
| RDD Scala/Java d'objets (`RDD[Person]`) | **oui**, c'est le cas du cours |
| DataFrame / Dataset (tous langages) | non (Tungsten) |
| RDD PySpark | quasi pas : octets opaques |
| DataFrame PySpark | non |

## Les équivalents PySpark

| Levier Scala | Équivalent PySpark |
|---|---|
| `spark.serializer` = Java (défaut) | `SparkContext(serializer=CPickleSerializer())` (défaut) |
| `spark.serializer` = Kryo | `SparkContext(serializer=MarshalSerializer())` |
| Kryo « ne sait pas tout sérialiser » | marshal n'accepte que les types built-in (`int`, `float`, `str`, `tuple`, `list`, `dict`) → `ValueError: unmarshallable object` sur une classe |
| Enregistrement des classes | pas d'équivalent : on se limite à des tuples / types built-in |
| À fixer dans le `SparkConf` avant la session | à fixer à la création du `SparkContext` |
| `persist(MEMORY_ONLY_SER)` | `persist(MEMORY_ONLY)` : un RDD Python en cache est **toujours** sérialisé |
| `spark.rdd.compress` = false par défaut | PySpark le met à **true** par défaut → cache déjà compressé |
| Meilleur encore : Dataset/DataFrame (encoders) | **DataFrame** : plus d'objets Python du tout |
| — | transfert JVM ↔ Python : **Arrow** (`pandas_udf`, `toPandas`) plutôt que pickle (`udf`) |

## Résultats mesurés (PySpark 3.5, local[*], 1M personnes)

Chiffres de `04_serialization_problems_part_2.py`, JVM chauffée (le script fait un passage de chauffe jeté avant de mesurer). Les tailles sont
reproductibles ; les temps varient d'un passage et d'une machine à l'autre :

| | Cache | Temps cache | Shuffle (`groupByKey`) | Temps shuffle |
|---|---|---|---|---|
| pickle (défaut) | 4.1 Mo | 1.6 s | 4.0 Mo | 2.4 s |
| marshal | 5.4 Mo | 1.6 s | 4.9 Mo | 2.2 s |
| DataFrame | 4.0 Mo | 2.2-2.5 s | 0.04 Mo (`groupBy().count()`, agrégation partielle) | 1.3 s |

| JVM ↔ Python (5M lignes) | Temps |
|---|---|
| fonction built-in | 0.3 s |
| `pandas_udf` (Arrow) | 3.4-3.5 s |
| `udf` (pickle) | 3.8-5.3 s (selon le passage) |

Lecture :
- **marshal n'apporte quasiment rien** : temps équivalents une fois la JVM chauffée (au 1er passage,
  il semblait 30-40 % plus rapide, mais c'était l'effet de chauffe : pickle tournait en premier),
  et il est **plus gros** : le pickle protocol 5 de Python 3.12 est déjà compact (18 Mo bruts contre
  20 Mo pour marshal), et le cache est compressé par défaut. Ni le gain de vitesse ni le gain mémoire
  de Kryo ne se retrouvent ici.
- Le vrai gain en PySpark vient d'abord du fait de **ne pas avoir d'objets Python** :
  DataFrame + fonctions built-in. Le shuffle quasi nul vient de l'agrégation partielle (avant
  shuffle) que `groupByKey` sur RDD ne fait pas. C'est un gain de plan d'exécution, pas de sérialiseur.
- Les UDF : la fonction built-in est ~10× plus rapide. Arrow aide face à pickle, et l'écart grandit
  avec des types plus lourds (chaînes, plusieurs colonnes) et des opérations vectorisées.

## À retenir

| | Scala | PySpark |
|---|---|---|
| Action principale | activer Kryo et enregistrer les classes | utiliser des DataFrames et des fonctions built-in |
| Si on reste en RDD | Kryo : +10-20 % de vitesse, -20-30 % de mémoire | garder pickle (défaut) : `MarshalSerializer` n'apporte rien de mesurable ici ; réduire plutôt les objets (tuples plutôt que classes) |
| Si on a besoin de code Python | — | `pandas_udf` (Arrow) plutôt que `udf` |
| Kryo | utile pour les RDD d'objets | inutile (accepté, sans effet) |
