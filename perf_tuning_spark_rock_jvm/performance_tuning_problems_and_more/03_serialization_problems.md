# 03 - Serialization problems : Scala vs PySpark

Sources : `03_serialization_problems.pdf`, `scala/part5boost/SerializationProblems.scala`,
code PySpark : [03_serialization_problems.py](03_serialization_problems.py)

## Le problème (commun aux deux)

- Le driver envoie les **lambdas** aux executors.
- Tout ce que la lambda référence est sérialisé avec elle.
- Si la lambda référence un **champ** (`factor` / `self.factor`), c'est **l'objet entier** qui part.
- Tout n'est pas sérialisable.

Ne concerne **que le code utilisateur dans des lambdas** :

| | Scala | PySpark |
|---|---|---|
| Concerné | RDD, Dataset (`map`, `filter`...) | RDD, UDF Python (`F.udf`, `pandas_udf`) |
| Pas concerné | DataFrame avec fonctions built-in | DataFrame avec fonctions built-in (`F.col`, `F.avg`...) |

## La différence de fond

| | Scala (JVM) | PySpark |
|---|---|---|
| Sérialiseur des closures | Java serialization | **cloudpickle** |
| Marqueur requis | `extends Serializable` | aucun : presque tout est picklable |
| Erreur typique | `Task not serializable` / `NotSerializableException` | `PicklingError` : `RDD_TRANSFORM_ONLY_VALID_ON_DRIVER`, `CONTEXT_ONLY_VALID_ON_DRIVER`, `cannot pickle '_thread.lock'` |
| Ce qui casse | toute classe non `Serializable` capturée | un objet qui contient un SparkContext / SparkSession / RDD / DataFrame, ou une ressource OS (connexion, lock, socket, fichier) |
| Lien caché vers l'objet englobant | oui : une classe/objet interne référence son `outer` | non : une classe imbriquée Python n'a pas de lien implicite |
| Méthode vs fonction | une méthode traîne `this` ; une `FunctionX` (val) non | une méthode liée (`obj.check`) traîne `obj` ; une fonction/closure non |

Conséquence : en PySpark, l'erreur Scala « classe pas Serializable » **n'existe pas**. Pour reproduire
la leçon, les classes Python du `.py` gardent volontairement une référence `self.rdd`.

## Les deux techniques du slide

| Technique | Scala | PySpark | Verdict (slide) |
|---|---|---|---|
| 1. Rendre l'objet sérialisable | `class X extends Serializable` | rien à faire en général ; pour exclure un champ non picklable : `__getstate__` | facile, **gros overhead** (tout l'objet est envoyé) |
| 2. Capturer des valeurs locales | `val enclosedFactor = factor` | `enclosed_factor = self.factor` | plus dur, **optimal** |

```scala
// Scala
def multiplyRDD() = {
  val enclosedFactor = factor
  rdd.map(_ * enclosedFactor).collect().toList
}
```
```python
# PySpark
def multiply_rdd(self):
    enclosed_factor = self.factor
    return self.rdd.map(lambda x: x * enclosed_factor).collect()
```

## Les cas du cours, côté PySpark

| Cas Scala | En PySpark | Résultat testé |
|---|---|---|
| `RDDMultiplier` (lambda sans champ) | idem | OK |
| `MoreGeneralRDDMultiplier` (sans `Serializable`) | échoue seulement parce que `self` contient l'RDD | `PicklingError` (voulu) |
| `extends Serializable` | `__getstate__` qui exclut `rdd` | OK |
| capture locale | idem | OK |
| Exercice 1 : objet imbriqué | pertinent seulement si on stocke `self.outer` explicitement | OK après capture locale |
| Exercice 2 : argument du constructeur | idem (technique 2) | OK |
| Exercice 3 : `FunctionX` sans `Serializable` | attribut fonction au lieu de méthode + capture locale | OK |

## Ce qui compte en plus en PySpark (absent du cours Scala)

| Sujet | Mauvais | Bon |
|---|---|---|
| UDF qui capture `self` | `F.udf(lambda p: p * self.rate)` → échoue si `self` contient la session | variable locale, ou mieux : **fonction built-in** sans UDF |
| Gros objet capturé (dict, modèle) | capturé dans la closure → envoyé avec **chaque tâche** | `sc.broadcast(obj)` → une fois par executor (DataFrame : `F.broadcast` join) |
| Connexion / client | créé sur le driver → `cannot pickle` | créé dans `mapPartitions` / `foreachPartition`, une fois par partition |
| Classes définies dans `__main__` vs module | — | `__main__` : copiées par valeur ; module : par nom → le module doit être installé sur les executors (`--py-files`) |
| Version de Python | driver ≠ workers → unpickling cassé (vu en pratique : `No module named 'pandas'`) | `PYSPARK_PYTHON` = même interpréteur que le driver |

## À retenir

- **Commun** : une lambda qui lit un champ embarque tout l'objet → capturer des valeurs locales.
- **Scala** : le piège, c'est la classe non `Serializable`.
- **PySpark** : le piège, c'est un objet qui contient Spark (session, contexte, RDD) ou une ressource OS ;
  et le vrai coût, ce sont les gros objets capturés et les UDF Python.
