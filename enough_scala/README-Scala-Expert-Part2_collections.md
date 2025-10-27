# 📗 Scala Expert — Partie 2 : Collections, FP & POO complète (FR)

**Contenu de la partie 2**
- Collections immuables & muables : `List`, `Seq`, `Vector`, `Set`, `Map`, `Array`, `ListBuffer`, `ArrayBuffer`
- Opérations FP : `map`, `flatMap`, `filter`, `collect`, `foldLeft`, `foldRight`, `reduce`, `groupBy`, `partition`
- Options & erreurs : `Option`, `Either`, `Try` (aperçu)
- Pattern matching avancé (sur valeurs, tuples, collections, case classes)
- POO complète : `class`, `case class`, `object` compagnon, `trait`, héritage, polymorphisme, visibilité, `sealed`, `final`
- Enums Scala 3 (avec méthodes), équivalents Scala 2
- Exemples **Scala 3** + équivalents **Scala 2**
- Exercices avancés + solutions

---

## 1) Collections (immuables / muables)

### Collections immuables (Scala 3)
```scala
val xs  = List(1,2,3,4)
val evn = xs.filter(_ % 2 == 0)           // List(2,4)
val dbl = xs.map(_ * 2)                    // List(2,4,6,8)
val sum = xs.foldLeft(0)(_ + _)            // 10

val s   = Set(1,2,2,3)                     // Set(1,2,3)
val m   = Map("FR" -> "France", "MG" -> "Madagascar")
val m2  = m + ("US" -> "United States")
val m3  = m2 - "MG"
val joinedKeys = m.keySet union m3.keySet
```

### Collections muables (Scala 3)
```scala
import scala.collection.mutable.{ListBuffer, ArrayBuffer, Map => MMap, Set => MSet}

val lb  = ListBuffer(1,2,3); lb += 4; lb.append(5); val listFinal = lb.toList
val ab  = ArrayBuffer(1,2); ab += 3; ab(0) = 9
val mm  = MMap("a" -> 1); mm.update("b", 2); mm.remove("a")
val ms  = MSet(1,2); ms += 3; ms -= 2
```

### Équivalents Scala 2
```scala
val xs  = List(1,2,3,4)
val evn = xs.filter(_ % 2 == 0)
val dbl = xs.map(_ * 2)
val sum = xs.foldLeft(0)(_ + _)

import scala.collection.mutable.{ListBuffer, ArrayBuffer, Map => MMap, Set => MSet}
val lb  = ListBuffer(1,2,3); lb += 4; lb.append(5); val listFinal = lb.toList
val ab  = ArrayBuffer(1,2); ab += 3; ab(0) = 9
val mm  = MMap("a" -> 1); mm.update("b", 2); mm.remove("a")
val ms  = MSet(1,2); ms += 3; ms -= 2
```

---

## 2) Opérations fonctionnelles clés

### map / flatMap / filter / collect
```scala
val words = List("alpha beta", "gamma", "delta eps")
val tokens = words.flatMap(_.split("\\s+").toList)  // List(alpha,beta,gamma,delta,eps)
val onlyLong = tokens.filter(_.length >= 5)         // List(alpha,gamma,delta)

// collect = filtrer + transformer en même temps (via pattern matching partiel)
val nums = List("10", "x", "20", "oops", "7")
val parsed = nums.collect { case s if s.forall(_.isDigit) => s.toInt }  // List(10,20,7)
```

### foldLeft / foldRight / reduce / groupBy / partition
```scala
val xs = List(1,2,3,4)

val sum   = xs.foldLeft(0)(_ + _)               // 10 (assoc à gauche)
val prod  = xs.foldLeft(1)(_ * _)               // 24
val right = xs.foldRight("Z")((n, acc) => s"($n->$acc)")  // (1->(2->(3->(4->Z))))

val grouped = List("FR", "MG", "FR").groupBy(identity)    // Map(FR->List(FR,FR), MG->List(MG))
val (small, big) = xs.partition(_ <= 2)                   // (List(1,2), List(3,4))
```

---

## 3) Option / Either / Try (aperçu)

```scala
def normalizeEmail(s: String): Option[String] =
  val t = s.trim.toLowerCase
  if t.contains("@") then Some(t) else None

def parsePrice(s: String): Either[String, Double] =
  try Right(s.trim.toDouble)
  catch case _: NumberFormatException => Left(s"Prix invalide: $s")

import scala.util.{Try, Success, Failure}
def toIntTry(s: String): Try[Int] = Try(s.toInt)
```

Équivalents Scala 2 identiques (syntaxe catch/case avec accolades).

---

## 4) Pattern matching avancé

### Sur tuples et case classes
```scala
case class User(id: Long, name: String, age: Int)

def describe(u: User): String = u match
  case User(_, n, a) if a >= 18 => s"$n (adulte)"
  case User(_, n, _)            => s"$n (mineur)"

val pair = (200, "OK")
val msg  = pair match
  case (200, body) => s"HTTP OK: $body"
  case (code, _)   => s"HTTP code $code"
```

### Sur collections (déconstruction)
```scala
def headTail[A](xs: List[A]): String = xs match
  case h :: t => s"head=$h, tailSize=${t.size}"
  case Nil    => "vide"
```

Scala 2 : même logique avec match { case ... } et case h :: t =>.

---

## 5) POO complète (Scala 3 + Scala 2)

### Classes, héritage, polymorphisme, visibilité
```scala
trait Vehicle:
  def move(): String

abstract class Engine:
  protected def hp: Int
  def spec: String = s"${hp}hp"

class Diesel(private val _hp: Int) extends Engine:
  protected def hp: Int = _hp

class Bike(engine: Engine) extends Vehicle:
  def move() = s"bike(${engine.spec})"
```

Scala 2 équivalent :
```scala
trait Vehicle { def move(): String }

abstract class Engine {
  protected def hp: Int
  def spec: String = s"${hp}hp"
}

class Diesel(private val _hp: Int) extends Engine {
  protected def hp: Int = _hp
}

class Bike(engine: Engine) extends Vehicle {
  def move() = s"bike(${engine.spec})"
}
```

### Case classes & objets compagnons
```scala
case class Person(id: Long, name: String)
object Person:
  def fromCsv(line: String): Option[Person] =
    line.split(",") match
      case Array(id, n) if id.forall(_.isDigit) => Some(Person(id.toLong, n.trim))
      case _                                    => None
```

Scala 2 :
```scala
case class Person(id: Long, name: String)
object Person {
  def fromCsv(line: String): Option[Person] = line.split(",") match {
    case Array(id, n) if id.forall(_.isDigit) => Some(Person(id.toLong, n.trim))
    case _                                    => None
  }
}
```

### sealed / final / private / protected
- sealed trait : hiérarchie fermée, match exhaustif.
- final : empêche l’héritage/surcharges.
- private / protected : contrôlent la visibilité.

---

## 6) Enums Scala 3 (avec méthodes) + équivalents Scala 2

Scala 3 :
```scala
enum Role:
  case Admin, Editor, Reader
  def canWrite: Boolean = this match
    case Admin | Editor => true
    case Reader         => false
```

Scala 2 :
```scala
sealed trait Role { def canWrite: Boolean }
case object Admin  extends Role { val canWrite = true }
case object Editor extends Role { val canWrite = true }
case object Reader extends Role { val canWrite = false }
```

---

## 7) Exercices avancés (avec solutions)

### Exercice 1 — Nettoyage & agrégation (collections)
Entrée :
```scala
val emails = List(" Alice@EXAMPLE.com ", "bob@foo.io", "bad", "carol@foo.io")
```
Attendu : `Map("example.com" -> 1, "foo.io" -> 2)`

**Solution (Scala 3)**
```scala
def normalizeEmail(s: String): Option[String] =
  val t = s.trim.toLowerCase
  if t.contains("@") then Some(t) else None

val domains: List[String] =
  emails.flatMap(normalizeEmail).map(_.split("@").last)

val counts: Map[String, Int] =
  domains.groupBy(identity).view.mapValues(_.size).toMap
```

### Exercice 2 — Option + Either
Entrée : `val raw = List("12.3", "x", "7", "-1")`
Attendu : garder seulement les `Right` >= 0.

**Solution (Scala 3)**
```scala
def parsePrice(s: String): Either[String, Double] =
  try Right(s.toDouble) catch case _: NumberFormatException => Left(s"bad: $s")

val checked: List[Either[String, Double]] = raw.map(parsePrice)
val positives = checked.collect { case Right(v) if v >= 0 => v }
```

### Exercice 3 — POO & enums
**But** : Payment (Card(number), Cash, Transfer(iban)) + `mask()`.

**Solution (Scala 3)**
```scala
enum Payment:
  case Card(number: String)
  case Cash
  case Transfer(iban: String)

  def mask: String = this match
    case Card(n)      => "****" + n.takeRight(4)
    case Cash         => "cash"
    case Transfer(ib) => "****" + ib.takeRight(4)
```

### Exercice 4 — Pattern matching sur collections
**Solution (Scala 3)**
```scala
def firstTwo[A](xs: List[A]): String = xs match
  case Nil            => "empty"
  case a :: Nil       => s"one: $a"
  case a :: b :: _    => s"two: $a,$b"
```

---

## 8) Compétences acquises
- Choisir la bonne collection (perfs et immutabilité)
- Transformer et agréger avec les primitives FP
- Combiner Option/Either/Try pour des flows robustes
- Modéliser en POO idiomatique (traits, case classes, compagnons)
- Utiliser les Enums Scala 3 et alternatives Scala 2

**Prochaine étape :** Partie 3 (Exceptions avancées, logging, dates/temps, concurrence).
