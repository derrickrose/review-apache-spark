# 📙 Scala Expert — Partie 3 : Exceptions, Logging, Dates/Temps & Concurrence (FR)

**Contenu**
- Exceptions : `try/catch/finally`, `throw`, **exceptions personnalisées**, bonnes pratiques
- Approche fonctionnelle : `Try`, `Either`, `Option`, `Using`, `NonFatal`
- Logging pro : **SLF4J + Logback**, niveaux, logger par classe, formats
- Dates & temps : `java.time` (`LocalDate`, `LocalDateTime`, `Instant`, `ZonedDateTime`), `DateTimeFormatter`, `Duration`
- Concurrence : `Future`, `Promise`, `ExecutionContext`, composition (`map/flatMap/recover`), parallélisme (`sequence/traverse`), timeouts
- Exercices complets + solutions

---

## 1) Exceptions (impératif) — Scala 3 + équivalents Scala 2

### 1.1 `try/catch/finally` + `throw`
Scala 3 :
```scala
def div(a: Int, b: Int): Int =
  if b == 0 then throw new IllegalArgumentException("b ne doit pas être 0")
  a / b

def run(): Unit =
  try
    println(div(10, 2))
    println(div(1, 0))
  catch
    case e: IllegalArgumentException => println(s"Erreur: ${e.getMessage}")
    case t: Throwable => println(s"Autre erreur: $t")
  finally
    println("Toujours exécuté")
```
Scala 2 :
```scala
def div(a: Int, b: Int): Int = {
  if (b == 0) throw new IllegalArgumentException("b ne doit pas être 0")
  a / b
}

def run(): Unit = {
  try {
    println(div(10, 2))
    println(div(1, 0))
  } catch {
    case e: IllegalArgumentException => println(s"Erreur: ${e.getMessage}")
    case t: Throwable => println(s"Autre erreur: $t")
  } finally {
    println("Toujours exécuté")
  }
}
```

### 1.2 Exceptions personnalisées
Scala 3 :
```scala
class BusinessException(msg: String) extends Exception(msg)
class NotFoundException(id: Long) extends BusinessException(s"Ressource $id introuvable")
```
Bonne pratique : **messages clairs** + ajoute des **champs** (id, code) si besoin.

### 1.3 Bonnes pratiques (impératif)
- Ne pas masquer les exceptions : loggue + propage quand pertinent.
- `finally` pour **libérer** des ressources (flux, fichiers) si pas de `Using`.
- Exception **métier** ≠ exception **technique** : types distincts.

---

## 2) Gestion fonctionnelle des erreurs

### 2.1 `Try` / `Either` / `Option`
```scala
import scala.util.{Try, Success, Failure}

def parseInt(s: String): Try[Int] = Try(s.toInt)

def loadUserEither(id: Long): Either[String, String] =
  if id == 1 then Right("admin") else Left("not_found")

def findEmail(name: String): Option[String] =
  if name.nonEmpty then Some(s"$name@example.com") else None
```

### 2.2 `Using` (fermer automatiquement les ressources)
```scala
import scala.util.Using
import scala.io.Source

def readAll(path: String): Try[String] =
  Using(Source.fromFile(path)) { src => src.getLines().mkString("\n") }
```

### 2.3 `NonFatal` pour capturer les exceptions non fatales
```scala
import scala.util.control.NonFatal

def safe[A](thunk: => A): Either[String, A] =
  try Right(thunk)
  catch
    case NonFatal(e) => Left(e.getMessage)
```

---

## 3) Logging professionnel (SLF4J + Logback)

### 3.1 Dépendance & config
`build.sbt` :
```scala
libraryDependencies += "ch.qos.logback" % "logback-classic" % "1.5.6"
```
`src/main/resources/logback.xml` :
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

### 3.2 Logger par classe + niveaux
Scala 3 :
```scala
import org.slf4j.LoggerFactory

class UserService:
  private val log = LoggerFactory.getLogger(getClass)

  def find(id: Long): Option[String] =
    log.debug(s"find($id)")
    if id == 1 then
      log.info("User admin trouvé")
      Some("admin")
    else
      log.warn(s"User $id absent")
      None
```

Bonnes pratiques :
- Choisir le **niveau approprié** (`debug` pour dev, `info` pour succès, `warn` pour anomalies non bloquantes, `error` pour erreurs).
- Log **structuré et utile** (id, contexte, durée).

---

## 4) Dates & temps (API `java.time`)

### 4.1 Types essentiels
```scala
import java.time._
import java.time.format.DateTimeFormatter

val d = LocalDate.of(2025, 10, 21)
val dt = LocalDateTime.of(2025, 10, 21, 14, 30)
val zdt = ZonedDateTime.now(ZoneId.of("Europe/Paris"))
val inst = Instant.now()
```

### 4.2 Formatage / parsing
```scala
val fmt = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm")
val s  = dt.format(fmt)                // "21/10/2025 14:30"
val dt2 = LocalDateTime.parse("21/10/2025 14:30", fmt)
```

### 4.3 Durées & intervalles
```scala
val start = LocalDateTime.of(2025,10,1,12,0)
val end   = LocalDateTime.of(2025,10,21,15,30)
val dur   = java.time.Duration.between(start, end)
val minutes = dur.toMinutes
```

### 4.4 Fuseaux & conversions
```scala
val utc    = ZonedDateTime.now(ZoneId.of("UTC"))
val paris  = utc.withZoneSameInstant(ZoneId.of("Europe/Paris"))
```

---

## 5) Concurrence : `Future` / `Promise` / `ExecutionContext`

### 5.1 Basics
```scala
import scala.concurrent.{Future, Promise}
import scala.concurrent.ExecutionContext.Implicits.global

def fetch(i: Int): Future[Int] = Future { i * 2 }

val f: Future[Int] = fetch(21).map(_ + 1)         // 43
val g: Future[Int] = fetch(10).flatMap(a => fetch(a)) // composition
```

### 5.2 Parallélisme (sequence/traverse)
```scala
val futures: List[Future[Int]] = List(1,2,3,4).map(fetch)
val all: Future[List[Int]] = Future.sequence(futures)   // exécute en parallèle
```

### 5.3 Gestion d’erreurs & récupération
```scala
val okOrDefault: Future[Int] =
  fetch(0).map(_ / 0).recover { case _: ArithmeticException => 0 }
```

### 5.4 `Promise` (compléter manuellement)
```scala
val p = Promise[String]()
val fut = p.future
// ... plus tard
p.success("done")
```

### 5.5 Timeout simple (avec `Promise`)
```scala
import scala.concurrent.duration._
import java.util.Timer
import java.util.TimerTask

def timeoutAfter[A](millis: Long): Future[A] =
  val p = Promise[A]()
  val t = new Timer(true)
  t.schedule(new TimerTask { def run(): Unit = p.failure(new RuntimeException("timeout")) }, millis)
  p.future
```

> Pour un contrôle fin (annulation, délais), privilégier des libs comme **cats-effect** ou **ZIO** (hors périmètre ici).

---

## 6) Exercices (avec solutions)

### Exercice 1 — Exceptions & logging
**But** : écrire `readNumber(path)` qui lit un fichier, parse un `Int` et :
- loggue `info` si succès, `error` sinon
- remonte une exception métier `ParseException` en cas d’échec

*Solution (Scala 3)* :
```scala
import org.slf4j.LoggerFactory
import scala.util.{Try,Success,Failure}
import scala.io.Source

class ParseException(msg: String) extends Exception(msg)

object Reader:
  private val log = LoggerFactory.getLogger("Reader")
  def readNumber(path: String): Int =
    try
      val n = Source.fromFile(path).getLines().mkString.trim.toInt
      log.info(s"Lu: $n")
      n
    catch
      case e: NumberFormatException =>
        log.error("Parse", e); throw new ParseException("Nombre invalide")
      case t: Throwable =>
        log.error("Erreur", t); throw t
```

### Exercice 2 — Using + Either
**But** : `readAll(path): Either[String,String]` qui ferme la ressource et renvoie une erreur lisible.

*Solution (Scala 3)* :
```scala
import scala.util.Using
import scala.io.Source

def readAll(path: String): Either[String,String] =
  Using(Source.fromFile(path))(_.getLines().mkString("\n"))
    .toEither.left.map(_.getMessage)
```

### Exercice 3 — Dates & formatage
**But** : fonction `formatParis(ts: Long): String` qui prend un timestamp epoch millis et renvoie `dd/MM/yyyy HH:mm` en Europe/Paris.

*Solution (Scala 3)* :
```scala
import java.time._
import java.time.format.DateTimeFormatter

def formatParis(epochMillis: Long): String =
  val z = Instant.ofEpochMilli(epochMillis).atZone(ZoneId.of("Europe/Paris"))
  z.format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"))
```

### Exercice 4 — Parallélisme simple
**But** : lancer en parallèle `fetch(10)`, `fetch(20)`, `fetch(30)` et récupérer la somme.

*Solution (Scala 3)* :
```scala
import scala.concurrent.{Future}
import scala.concurrent.ExecutionContext.Implicits.global

def fetch(i: Int): Future[Int] = Future { i * 2 }

def sumAll(): Future[Int] =
  Future.sequence(List(10,20,30).map(fetch)).map(_.sum)
```

---

## 7) Bonus — Best practices / erreurs à éviter / mini‑quiz

- **Ne pas** tout catcher avec `Throwable` (sauf si tu **re‑lances** après log).
- Préfère `Using` pour gérer les ressources (au lieu de `finally` manuel).
- Log **utile** et **contextualisé** (pas de stacktrace en `info`).
- En concurrence, **pas de shared mutable state** sans synchronisation.
- Les **timeouts** explicites évitent les deadlocks silencieux.

**Mini‑quiz (réponses rapides)**
1. Quelle différence entre `Try` et `Either` ? → `Try` modèle exceptions ; `Either` modèle erreurs **typées** métiers.
2. Pourquoi `Using` ? → Gestion automatique de la fermeture de ressource.
3. `Future.sequence(List(f1,f2,f3))` fait quoi ? → Agrège en parallèle et donne `Future[List[A]]` quand tout est fini.

---

**Fin — Partie 3**  
Prochaine (Partie 4) : **Mini‑projet ETL complet + Préparation Spark + Exercices experts**.
