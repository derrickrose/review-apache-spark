# 📙 Scala Expert — Partie 4B : Spark (DataFrame/Dataset), Optimisations & Exercices (FR)

**Objectif** : Porter le pipeline ETL (Partie 4A) vers **Apache Spark** et apprendre les bases pro :
- Création d’une **SparkSession**
- Lecture/écriture (**CSV/JSON/Parquet**)
- Transformations **DataFrame/Dataset** (select, filter, groupBy, agg)
- **Joins**, **UDF**, **fenêtrage (window)**
- **Optimisations** : cache, repartition/coalesce, **AQE**, broadcast join, explain
- **Exercices experts** + solutions

---

## 0) Démarrage Spark

### Dépendances (`build.sbt`)
```scala
ThisBuild / scalaVersion := "3.4.2"
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "3.5.1",
  "org.apache.spark" %% "spark-core" % "3.5.1",
  "ch.qos.logback" % "logback-classic" % "1.5.6"
)
```

### Création de `SparkSession`
```scala
import org.apache.spark.sql.SparkSession

object SparkBoot:
  def session(app: String): SparkSession =
    SparkSession.builder()
      .appName(app)
      .master("local[*]")      // en prod, laissé vide (fourni par le cluster)
      .config("spark.sql.adaptive.enabled", "true")
      .getOrCreate()
```

---

## 1) Lecture / Écriture

```scala
import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._

def readParquet(spark: SparkSession, path: String): DataFrame =
  spark.read.parquet(path)

def readCsv(spark: SparkSession, path: String, header: Boolean = true): DataFrame =
  spark.read.option("header", header.toString).option("inferSchema", "true").csv(path)

def writeParquet(df: DataFrame, path: String, mode: String = "overwrite"): Unit =
  df.write.mode(mode).parquet(path)

def writeJson(df: DataFrame, path: String, mode: String = "overwrite"): Unit =
  df.write.mode(mode).json(path)
```

---

## 2) Schémas, Dataset & case classes

```scala
import org.apache.spark.sql.Encoders
import java.time.LocalDateTime

case class Ride(rideId: Long, userId: Long, city: String, distanceKm: Double, price: Double, ts: String)
case class City(code: String, name: String)

// Dataset = DataFrame typé
def toRideDS(df: org.apache.spark.sql.DataFrame) =
  import df.sparkSession.implicits._
  df.as[Ride]
```

💡 Remarque : Spark ne gère pas nativement `LocalDateTime` en case class — utilisez `String`/`Timestamp`.

---

## 3) Transformations essentielles

```scala
import org.apache.spark.sql.functions._

def normalizeCityCol = (col("city").trim().lower).substr(1,1).upper.concat(col("city").trim().lower.substr(2, 100))
// alternative plus simple : initcap(lower(trim(city)))

def kpiByCity(df: org.apache.spark.sql.DataFrame) = {
  val cleaned = df.withColumn("city_norm", initcap(lower(trim(col("city")))))
  val rev = cleaned.groupBy(col("city_norm")).agg(sum(col("price")).as("revenue"))
  val avg = cleaned.groupBy(col("city_norm")).agg(avg(col("distanceKm")).as("avg_distance"))
  (rev, avg)
}
```

### Filtrer / sélectionner / trier
```scala
val rides = readCsv(spark, "data/rides.csv")
val fr = rides.filter(col("city") === "FR").select("rideId","userId","price").orderBy(desc("price"))
```

---

## 4) Joins, UDF & fenêtres (window)

```scala
import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions._

val rides = readCsv(spark, "data/rides.csv")
val cities = readCsv(spark, "data/cities.csv")

// Join
val joined = rides.join(cities, rides.col("city") === cities.col("code"), "left")

// UDF (éviter si possible; préférer fonctions natives)
val maskUdf = udf((s: String) => if (s==null) null else ("****" + s.takeRight(4)))
val masked = joined.withColumn("mask_user", maskUdf(col("userId").cast("string")))

// Fenêtre: classement des rides par prix par ville
val w = Window.partitionBy(col("name")).orderBy(desc("price"))
val ranked = masked.withColumn("rank_price", row_number().over(w))
```

---

## 5) Optimisations & diagnostics

### Cache / persist
```scala
val df = readParquet(spark, "/path/to/parquet")
df.cache()            // ou .persist(StorageLevel.MEMORY_AND_DISK)
df.count()            // action pour matérialiser le cache
```

### Repartition / Coalesce
```scala
val repart = df.repartition(200)   // augmente/égalise le parallélisme (shuffle)
val smaller = df.coalesce(10)      // réduit sans shuffle (en sortie par ex.)
```

### Broadcast join (si petite dimension)
```scala
import org.apache.spark.sql.functions.broadcast
val smallDim = readParquet(spark, "dim_small")
val fact = readParquet(spark, "big_fact")
val bj = fact.join(broadcast(smallDim), Seq("key"), "left")
```

### AQE & Explain
```scala
spark.conf.set("spark.sql.adaptive.enabled", "true")
df.explain(true)  // plan logique + physique, utile pour diagnostiquer le shuffle
```

---

## 6) App Spark : traduction de la Partie 4A

```scala
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

object MiaradiaSparkApp:
  def main(args: Array[String]): Unit =
    val ridesPath  = args.lift(0).getOrElse("data/rides.csv")
    val citiesPath = args.lift(1).getOrElse("data/cities.csv")
    val outDir     = args.lift(2).getOrElse("out_spark")

    val spark = SparkBoot.session("Miaradia Spark ETL")
    import spark.implicits._

    val rides  = readCsv(spark, ridesPath)
      .withColumn("city_norm", initcap(lower(trim(col("city")))))
    val cities = readCsv(spark, citiesPath)

    val enr = rides.join(cities, rides.col("city") === cities.col("code"), "left")
    val rev = enr.groupBy(coalesce(col("name"), col("city_norm")).as("city"))
                 .agg(sum(col("price")).as("revenue"))
    val avg = enr.groupBy(coalesce(col("name"), col("city_norm")).as("city"))
                 .agg(avg(col("distanceKm")).as("avg_distance"))

    writeJson(rev, s"$outDir/kpi_revenue")
    writeJson(avg, s"$outDir/kpi_avg_distance")

    spark.stop()
```

---

## 7) Exercices experts (avec solutions)

### Ex 1 — Agrégations multi-mesures
**But** : pour chaque ville, calculer `revenue`, `avg_price`, `max_distance`, `count`.
```scala
val res = enr.groupBy(coalesce(col("name"), col("city_norm")).as("city"))
  .agg(
    sum("price").as("revenue"),
    avg("price").as("avg_price"),
    max("distanceKm").as("max_distance"),
    count(lit(1)).as("cnt")
  )
```

### Ex 2 — Détection d’anomalies
**But** : marquer les rides avec `price <= 0` ou `distanceKm < 0` et les écrire à part.
```scala
val bad = rides.filter((col("price") <= 0) || (col("distanceKm") < 0))
writeParquet(bad, s"$outDir/bad_records")
```

### Ex 3 — Top-N par ville (fenêtre)
**But** : garder les **3 rides** les plus chers par ville libellée.
```scala
import org.apache.spark.sql.expressions.Window
val city = coalesce(col("name"), col("city_norm")).as("city")
val w = Window.partitionBy(city).orderBy(desc("price"))
val top3 = enr.withColumn("rnk", row_number().over(w)).filter(col("rnk") <= 3)
```

### Ex 4 — Broadcast vs Shuffle Join (comparatif)
**But** : forcer un broadcast et comparer les plans (`explain`).
```scala
val bj = rides.join(broadcast(cities), rides("city") === cities("code"))
bj.explain(true)
```

---

## 8) Bonnes pratiques Spark (récap)

- **Éviter les UDF** quand une fonction SQL existe (meilleures perfs & catalyst)
- **Limiter les colonnes** tôt (`select`) et **filtrer** tôt (`where`) pour réduire le shuffle
- Ajuster **`spark.sql.shuffle.partitions`** (200–600 typiquement) selon le cluster
- Utiliser **`explain`**, Spark UI (stages/tasks), et **AQE** pour détecter le skew
- **Broadcast** les petites dimensions, sinon **salting** pour les clés chaudes
- En écriture, **coalesce** pour réduire le nombre de fichiers petits
- **Cache/persist** uniquement ce qui est réutilisé plusieurs fois

**Fin — Partie 4B.** Prochaine partie : **5 — Dimensionnement & mise en production Spark**.
