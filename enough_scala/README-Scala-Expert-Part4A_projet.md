# 📘 Scala Expert — Partie 4A : Mini‑projet ETL complet (FR)

**Objectif** : Construire un pipeline **ETL** propre en Scala (pré‑Spark), prêt à être porté vers Spark (Partie 4B).  
**Livrables** : architecture modulaire (Extract / Transform / Load), code commenté, validation & logging, tests indicatifs.

---

## 0) Structure de projet (sbt)

```
etl-scala/
 ├── build.sbt
 ├── src/
 │   ├── main/
 │   │   ├── resources/
 │   │   │   └── logback.xml
 │   │   └── scala/com/miaradia/etl/
 │   │       ├── Extract.scala
 │   │       ├── Transform.scala
 │   │       ├── Load.scala
 │   │       └── MiaradiaETLApp.scala
 │   └── test/scala/com/miaradia/etl/
 │       └── TransformSpec.scala
 └── data/
     ├── rides.csv
     └── cities.csv
```

### `build.sbt`
```scala
ThisBuild / scalaVersion := "3.4.2"
ThisBuild / organization := "com.miaradia"
ThisBuild / version := "0.1.0"

libraryDependencies ++= Seq(
  "org.scalatest" %% "scalatest" % "3.2.19" % Test,
  "ch.qos.logback" % "logback-classic" % "1.5.6"
)

scalacOptions ++= Seq("-deprecation","-feature","-Wunused:all")
```

### `logback.xml`
```xml
<configuration>
  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
      <pattern>%d{HH:mm:ss.SSS} %-5level [%thread] %logger - %msg%n</pattern>
    </encoder>
  </appender>
  <root level="INFO">
    <appender-ref ref="STDOUT"/>
  </root>
</configuration>
```

---

## 1) Modélisation & Validation

### Domain
```scala
package com.miaradia.etl

import java.time.*

final case class Ride(
  rideId: Long,
  userId: Long,
  city: String,
  distanceKm: Double,
  price: Double,
  ts: LocalDateTime
)

final case class City(code: String, name: String)

/** Lignes invalides conservées pour traçabilité */
final case class InvalidRow(line: String, reason: String)
```

### Validation (règles simples)
```scala
package com.miaradia.etl

object Validate:
  def nonEmpty(s: String): Boolean = s != null && s.trim.nonEmpty
  def positiveOrZero(d: Double): Boolean = d >= 0.0

  def rideOk(r: Ride): Boolean =
    nonEmpty(r.city) && positiveOrZero(r.distanceKm) && positiveOrZero(r.price)
```

---

## 2) Extract — lecture des fichiers CSV

```scala
package com.miaradia.etl

import org.slf4j.LoggerFactory
import scala.io.Source
import scala.util.{Try, Using}
import java.time.*
import java.time.format.DateTimeFormatter

object Extract:
  private val log = LoggerFactory.getLogger(getClass)
  private val tsFmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

  /** Parse une ligne ride: rideId,userId,city,distanceKm,price,ts */
  def parseRide(line: String): Option[Ride] =
    val parts = line.split(",").map(_.trim)
    Try:
      Ride(
        rideId     = parts(0).toLong,
        userId     = parts(1).toLong,
        city       = parts(2),
        distanceKm = parts(3).toDouble,
        price      = parts(4).toDouble,
        ts         = LocalDateTime.parse(parts(5), tsFmt)
      )
    .toOption

  /** Parse une ligne city: code,name */
  def parseCity(line: String): Option[City] =
    line.split(",").map(_.trim) match
      case Array(code, name) if code.nonEmpty && name.nonEmpty => Some(City(code, name))
      case _ => None

  def readRides(path: String): (List[Ride], List[InvalidRow]) =
    Using(Source.fromFile(path)) { src =>
      src.getLines().drop(1).toList.map { l =>
        parseRide(l).toRight(InvalidRow(l, "parse_error"))
      }
    }.toOption.getOrElse(Nil)
     .partitionMap(identity) match
        case (valid, invalid) =>
          if invalid.nonEmpty then log.warn(s"${invalid.size} lignes rides invalides")
          (valid, invalid)

  def readCities(path: String): (List[City], List[InvalidRow]) =
    Using(Source.fromFile(path)) { src =>
      src.getLines().drop(1).toList.map { l =>
        parseCity(l).toRight(InvalidRow(l, "parse_error"))
      }
    }.toOption.getOrElse(Nil)
     .partitionMap(identity) match
        case (valid, invalid) =>
          if invalid.nonEmpty then log.warn(s"${invalid.size} lignes cities invalides")
          (valid, invalid)
```

---

## 3) Transform — nettoyage, enrichissement, agrégations

```scala
package com.miaradia.etl

import org.slf4j.LoggerFactory

object Transform:
  private val log = LoggerFactory.getLogger(getClass)

  /** Nettoie la ville (trim + capitale 1re lettre) */
  def normalizeCity(s: String): String =
    val t = s.trim.toLowerCase
    if t.isEmpty then t else t.head.toUpper + t.tail

  def clean(r: Ride): Ride =
    r.copy(city = normalizeCity(r.city))

  /** Filtre rides valides selon Validate */
  def filterValid(rs: List[Ride]): (List[Ride], List[Ride]) =
    rs.map(r => if Validate.rideOk(r) then Left(clean(r)) else Right(r))
      .partitionMap(identity)

  /** Enrichit avec libellé de ville via dictionnaire code->name */
  def enrich(rs: List[Ride], cities: List[City]): List[(Ride, String)] =
    val dict = cities.map(c => c.code -> c.name).toMap
    rs.map(r => r -> dict.getOrElse(r.city, r.city))

  /** KPI: total revenus par ville libellée */
  def revenueByCity(rs: List[(Ride, String)]): Map[String, Double] =
    rs.groupBy(_._2).view.mapValues(_.map(_._1.price).sum).toMap

  /** KPI: distance moyenne par ville */
  def avgDistanceByCity(rs: List[(Ride, String)]): Map[String, Double] =
    rs.groupBy(_._2).view.mapValues{ xs =>
      val d = xs.map(_._1.distanceKm)
      d.sum / math.max(1, d.size)
    }.toMap
```

---

## 4) Load — écriture des résultats

```scala
package com.miaradia.etl

import org.slf4j.LoggerFactory
import java.io.PrintWriter

object Load:
  private val log = LoggerFactory.getLogger(getClass)

  def writeJsonKpi(path: String, kpi: Map[String, Double]): Unit =
    val json = kpi.map{ case (k,v) => "{"city":"" + k + "","value":" + v + "}" }
                  .mkString("[",",","]")
    val w = new PrintWriter(path)
    try w.write(json)
    finally w.close()
    log.info(s"Écrit: " + path)

  def writeInvalid(path: String, invalids: List[InvalidRow]): Unit =
    val w = new PrintWriter(path)
    try
      w.println("line,reason")
      invalids.foreach(ir => w.println(""" + ir.line.replace(""","'") + ""," + ir.reason))
    finally w.close()
    log.warn(s"Invalids: " + invalids.size + " -> " + path)
```

---

## 5) App — orchestration du pipeline

```scala
package com.miaradia.etl

import org.slf4j.LoggerFactory

object MiaradiaETLApp:

  private val log = LoggerFactory.getLogger(getClass)

  @main def run(ridesPath: String, citiesPath: String, outDir: String): Unit =
    log.info("ETL start")

    val (rides, invalidRidesParse)   = Extract.readRides(ridesPath)
    val (cities, invalidCitiesParse) = Extract.readCities(citiesPath)

    val (validRides, invalidRidesRule) = Transform.filterValid(rides)
    val enriched = Transform.enrich(validRides, cities)

    val kpiRevenue = Transform.revenueByCity(enriched)
    val kpiAvgDist = Transform.avgDistanceByCity(enriched)

    Load.writeJsonKpi(outDir + "/kpi_revenue.json", kpiRevenue)
    Load.writeJsonKpi(outDir + "/kpi_avg_distance.json", kpiAvgDist)
    Load.writeInvalid(outDir + "/invalid_rides.csv", invalidRidesParse + invalidRidesRule)
    Load.writeInvalid(outDir + "/invalid_cities.csv", invalidCitiesParse)

    log.info("ETL done. valid=" + validRides.size + ", invalid=" + (invalidRidesParse.size + invalidRidesRule.size))
```

---

## 6) Données d’exemple

### `data/rides.csv`
```
rideId,userId,city,distanceKm,price,ts
1,10,FR,12.5,20.0,2025-10-20 12:00:00
2,11,MG,0.0,0.0,2025-10-20 13:00:00
3,10,FR,-5.0,9.0,2025-10-20 14:00:00
4,99,US,22.0,35.5,2025-10-20 15:10:00
```

### `data/cities.csv`
```
code,name
FR,France
MG,Madagascar
US,United States
```

---

## 7) Tests indicatifs (ScalaTest)

```scala
package com.miaradia.etl

import org.scalatest.funsuite.AnyFunSuite
import java.time.LocalDateTime

class TransformSpec extends AnyFunSuite:

  test("normalizeCity") {
    assert(Transform.normalizeCity("  paris ") == "Paris")
  }

  test("revenueByCity") {
    val r1 = Ride(1,10,"FR",10.0,20.0, LocalDateTime.now())
    val r2 = Ride(2,11,"FR",5.0, 15.0, LocalDateTime.now())
    val enr = List(r1 -> "France", r2 -> "France")
    val kpi = Transform.revenueByCity(enr)
    assert(kpi("France") == 35.0)
  }
```
Lance les tests : `sbt test`.

---

## 8) Exécution

Compilation & run :  
```bash
sbt compile
sbt "run data/rides.csv data/cities.csv out"
```

Résultats :  
- `out/kpi_revenue.json`  
- `out/kpi_avg_distance.json`  
- `out/invalid_rides.csv`  
- `out/invalid_cities.csv`

---

## 9) Pont vers Spark (preview Partie 4B)
- Les **case classes** `Ride`/`City` deviennent les **schémas de Dataset**.  
- Les **transformations** (groupBy, map, filter) migrent vers **Spark SQL** (`groupBy("city").agg(...)`).  
- Le **logging** reste identique (SLF4J).  
- La **validation** peut s’implémenter via **colonnes dérivées** et **filtres**.  

Dans la Partie **4B**, on traduira ce pipeline en **Spark (DataFrame/Dataset)** avec persistance Parquet, `SparkSession`, optimisations, et exercices avancés.
