# 📚 Scala & Spark Core Expert — Volume 1 (FR)

**Objectif :** maîtriser **Scala** (langage) et **Apache Spark (Core)** du niveau avancé à expert : bases solides, API RDD/DataFrame/Dataset, SQL, internals (Catalyst/Tungsten), **shuffle & partitionnement**, et **dimensionnement/tuning** pour Spark **3.5/4.0**.

> Ce Volume 1 couvre les parties **1 → 5**. Le Volume 2 (CI/CD, sécurité, lineage, streaming, lakehouse, ML, observabilité) est séparé.

---

## 1) Introduction & Vision

- **Pourquoi Scala + Spark ?** Performance, expressivité, typage fort, écosystème Big Data.
- **Cas d’usage** : ETL massifs, BI/SQL, machine learning distribué, streaming (temps réel).
- **Version cible** : Spark **3.5.1 / 4.0.0**, Java **17/21**, Scala **3.4.x** (compat 2.13 ok).

**Mantra** : *DataFrame/Dataset d’abord, RDD seulement si nécessaire.*

---

## 2) Scala — Récapitulatif Expert

### 2.1 Syntaxe essentielle
```scala
// Variables & types
val x: Int = 42            // immuable
var y: Double = 3.14       // mutable (éviter en FP)

// Fonctions
def inc(a: Int): Int = a + 1
val add = (a: Int, b: Int) => a + b

// Option / Either
def safeDiv(a: Int, b: Int): Option[Double] =
  if (b == 0) None else Some(a.toDouble / b)

def validatePrice(p: Double): Either[String, Double] =
  if (p >= 0) Right(p) else Left("price < 0")
```

### 2.2 POO & Traits
```scala
trait Priceable { def price: Double }
case class Ride(rideId: Long, city: String, distanceKm: Double, price: Double) extends Priceable

def promo(p: Priceable): Double = p.price * 0.9
```

### 2.3 Collections & implicites utiles
```scala
val amounts = List(10.0, 5.0, 7.5)
val total = amounts.foldLeft(0.0)(_ + _)
val by2 = amounts.map(_ * 2).filter(_ > 10)

// Implicite simple (scala 3: given)
given Ordering[Ride] = Ordering.by(_.price)
val top = List(Ride(1,"FR",12.5,20), Ride(2,"US",8,9)).max // par price
```

### 2.4 Erreurs & exceptions
```scala
import scala.util.{Try, Success, Failure}

def parse(s: String): Try[Int] = Try(s.toInt)
parse("42")    // Success(42)
parse("oops")  // Failure(java.lang.NumberFormatException)
```

### 2.5 Concurrence (futures rapide)
```scala
import scala.concurrent.{Future, Await}
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent.duration._

val f = Future { Thread.sleep(50); 1 + 1 }
val r = Await.result(f, 2.seconds)
```

> Pour la prod scala 3 : préférer **ZIO/Cats Effect** si vous faites beaucoup d’IO asynchrones.

---

## 3) Spark Fondamentaux — RDD, DataFrame, Dataset, SQL

### 3.1 Démarrage SparkSession
```scala
import org.apache.spark.sql.SparkSession

val spark = SparkSession.builder()
  .appName("CoreBasics")
  .master("local[*]") // en prod: yarn/k8s
  .getOrCreate()
import spark.implicits._
```

### 3.2 RDD (à connaître, à limiter)
```scala
val rdd = spark.sparkContext.parallelize(1 to 10)
val sum = rdd.map(_ * 2).filter(_ > 10).reduce(_ + _)
```

### 3.3 DataFrame (non typé au compile‑time)
```scala
val df = Seq((1,"FR",12.5,20.0),(2,"US",8.0,9.0)).toDF("rideId","city","distanceKm","price")
df.select("city","price").where($"price" > 10).show()
```

### 3.4 Dataset (typé)
```scala
case class Ride(rideId: Long, city: String, distanceKm: Double, price: Double)
val ds = df.as[Ride]
val premium = ds.filter(_.price >= 20.0)
```

### 3.5 Spark SQL
```scala
df.createOrReplaceTempView("rides")
spark.sql("SELECT city, COUNT(*) cnt, SUM(price) revenue FROM rides GROUP BY city").show()
```

**Recommandation** : DataFrame/Dataset + SQL pour 95 % des cas.

---

## 4) Spark Avancé — Internals & Optimisations

### 4.1 Catalyst & Tungsten (rappel)
- **Catalyst** : plan **logique → optimisé → physique** (réécritures, pushdown, join reorder).
- **Tungsten** : exécution vectorisée + gestion mémoire **off‑heap** (réduit GC).

```scala
df.explain("extended") // repérer Exchange (shuffle), BroadcastHashJoin, SortMergeJoin
```

### 4.2 Shuffle — quand et comment l’éviter
- Shuffle survient sur `groupBy`, `join`, `distinct`, `repartition`, `orderBy`…
- **Réduire tôt** (select minimal, filter en amont).  
- **Broadcast** petite table (`broadcast(dim)`), **bucketing**, **pré‑agrégations locales**.  
- Activer **AQE** (Spark 3.x/4.x) pour fusion de partitions, skew join.

```scala
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

### 4.3 Partitionnement & parallélisme
- Règle d’or : **partitions ≈ 2–3× le nombre total de cœurs**.
- Parquet **128–256 Mo** par fichier en sortie.
- Éviter les **petits fichiers** → `coalesce` / `repartition` intelligent.

```scala
val out = df.repartition(200, $"city") // hash partition by city
out.write.mode("overwrite").parquet("s3a://bucket/silver/rides")
```

### 4.4 Joins — stratégies
- **BroadcastHashJoin** : dimension ≤ ~10–100 Mo (configurable).  
- **SortMergeJoin** : par défaut sur clés triées (coût élevé si gros shuffle).  
- **Bucketed Joins** : sur tables récurrentes avec même bucketing/tri.

```scala
import org.apache.spark.sql.functions.broadcast
val cities = Seq(("FR","Paris"),("US","NYC")).toDF("city","name")
val joined = df.join(broadcast(cities), Seq("city"), "left")
```

### 4.5 Cache & storage levels
```scala
val cached = df.select($"city",$"price").where($"price" > 0).cache()
cached.count()
// Storage tab dans Spark UI → vérifier taille et niveau (MEMORY, MEMORY_AND_DISK...)
```

---

## 5) Dimensionnement & Tuning (prod)

### 5.1 Mémoire / Cœurs / Executors
- **Executors** : 4–6 cœurs chacun (éviter “fat executors”).
- **Mémoire** : 16–32 Go heap / executor + **overhead** 7–10 %.
- **Parallelisme** : partitions adaptées au cluster (2–3× cœurs).

### 5.2 Serializer & GC
```properties
spark.serializer=org.apache.spark.serializer.KryoSerializer
spark.memory.fraction=0.6
spark.executor.memoryOverhead=3g
```
- Préférer **Kryo**. Surveiller **GC time** (Spark UI → Executors).

### 5.3 AQE & SQL conf recommandées
```properties
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
spark.sql.adaptive.skewJoin.enabled=true
spark.sql.shuffle.partitions=600   # exemple cluster large
```
- Ajuster `spark.sql.shuffle.partitions` (trop bas → saturation ; trop haut → overhead).

### 5.4 I/O & formats
- Source/sink **Parquet** (colonnaire, predicate pushdown).  
- **Compression** : Snappy/ZSTD.  
- **Layout** : partitionnement par **date/heure** si requêté.

### 5.5 Commandes utiles & explain
```scala
spark.conf.getAll.foreach(println)                         // voir la config effective
df.write.option("maxRecordsPerFile","2_000_000")...        // maîtriser la taille fichiers
spark.time { df.count() }                                  // mesure simple
df.explain(true)                                           // plan détaillé
```

### 5.6 Check‑list rapide pré‑prod
- [ ] Partitions & parallélisme validés (pas de small files).  
- [ ] AQE ON, broadcast pertinents.  
- [ ] Plans sans shuffles inutiles (`explain`).  
- [ ] Serializer **Kryo** + overhead mémoire configuré.  
- [ ] Formats & compression corrects.  
- [ ] Tests de charge + Spark UI vérifiée (stages/skew).

---

## 📎 Annexes — Exemples complets

### A. Job scala minimal (batch)
```scala
object BatchJob:
  def main(args: Array[String]): Unit =
    val spark = SparkSession.builder().appName("BatchJob").getOrCreate()
    import spark.implicits._
    val in  = spark.read.option("header","true").csv(args(0))
    val out = in.groupBy($"city").count()
    out.write.mode("overwrite").parquet(args(1))
```

**spark-submit (EMR/K8s générique) :**
```bash
spark-submit   --deploy-mode cluster   --class BatchJob   --conf spark.sql.adaptive.enabled=true   --conf spark.serializer=org.apache.spark.serializer.KryoSerializer   s3://bucket/jars/batch-assembly.jar s3://bucket/in.csv s3://bucket/out
```

### B. Tables Parquet → SQL
```scala
val silver = spark.read.parquet("s3a://bucket/silver/rides")
silver.createOrReplaceTempView("rides")
spark.sql("""
  SELECT city, COUNT(*) cnt, SUM(price) revenue
  FROM rides
  GROUP BY city
  ORDER BY revenue DESC
""").show(20, truncate=false)
```

---

## 🎯 Conclusion

Avec ce **Volume 1**, tu possèdes :
- La **maîtrise de Scala** pour écrire du code Spark propre et typé.
- La **connaissance profonde** des API Spark (RDD/DF/DS/SQL) et des **internals** (Catalyst/Tungsten).
- Les **réflexes de tuning** (shuffle, partitions, broadcast, AQE) et **dimensionnement** pro.

➡️ Passe au **Volume 2** pour la **production** : CI/CD, sécurité, lineage, streaming Kafka, Lakehouse (Delta/Iceberg), MLlib, observabilité (Prometheus/Grafana/OTel).
