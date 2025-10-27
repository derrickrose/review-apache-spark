# 📘 Scala Expert — Partie 1 : Bases, syntaxe, chaînes, boucles, fonctions (FR)

**Contenu**
- Variables, expressions, types, inférence
- Chaînes (`String`) + interpolations `s`, `f`, `raw`
- Boucles `for`, `while`, plages `Range`
- Récursion + optimisation `@tailrec`
- Fonctions (params par défaut, curryfication), équivalents Scala 2
- Exercices avec pistes de solutions

---

## 1) Variables, expressions, types

### Scala 3
```scala
val nom: String = "Miaradia"   // immuable
var compteur = 0               // mutable (éviter si possible)
compteur += 1

def add(a: Int, b: Int): Int = a + b

val total = add(2, 3)          // 5
val expr = if total > 3 then "ok" else "ko"  // if est une expression
```

### Scala 2 (équivalent)
```scala
val nom: String = "Miaradia"
var compteur = 0
compteur += 1

def add(a: Int, b: Int): Int = a + b

val total = add(2, 3)
val expr = if (total > 3) "ok" else "ko"
```

---

## 2) Chaînes (`String`) et interpolations

### Scala 3
```scala
val user = "Alice"
val age  = 27
val s1   = s"Salut $user, tu as $age ans."          // s-interpolation
val prix = 12.3456
val s2   = f"Total: $prix%1.2f €"                   // f-interpolation (format)
val s3   = raw"C:\\new\\path\\tab"                     // raw: pas d'échappement
val multi =
  """|Ligne 1
     |Ligne 2
     |Ligne 3""".stripMargin
```

### Scala 2
```scala
val user = "Alice"
val age  = 27
val s1   = s"Salut $user, tu as $age ans."
val prix = 12.3456
val s2   = f"Total: $prix%1.2f €"
val s3   = raw"C:\\new\\path\\tab"
val multi =
  """|Ligne 1
     |Ligne 2
     |Ligne 3""".stripMargin
```

---

## 3) Boucles et plages (`Range`)

### Scala 3
```scala
for i <- 1 to 5 do println(i)     // 1,2,3,4,5
for i <- 1 until 5 do println(i)  // 1,2,3,4
for i <- 0 to 10 by 2 do println(i)  // 0,2,4,6,8,10

var i = 0
while i < 3 do
  println(i)
  i += 1
```

### Scala 2
```scala
for (i <- 1 to 5) println(i)
for (i <- 1 until 5) println(i)
for (i <- 0 to 10 by 2) println(i)

var i = 0
while (i < 3) { println(i); i += 1 }
```

---

## 4) Récursion, `@tailrec`, paramètres by-name et `lazy`

### Scala 3
```scala
import scala.annotation.tailrec

def fact(n: Int): Int =
  @tailrec def go(k: Int, acc: Int): Int =
    if k <= 1 then acc else go(k - 1, acc * k)
  go(n, 1)

def debug(msg: => String)(block: => Unit): Unit = // msg évalué si besoin
  println(s"[DEBUG] $msg")
  block

lazy val lourd = (1 to 5_000_000).sum  // calcul différé à la 1re utilisation
```

### Scala 2
```scala
import scala.annotation.tailrec

def fact(n: Int): Int = {
  @tailrec def go(k: Int, acc: Int): Int =
    if (k <= 1) acc else go(k - 1, acc * k)
  go(n, 1)
}

def debug(msg: => String)(block: => Unit): Unit = {
  println(s"[DEBUG] $msg")
  block
}

lazy val lourd = (1 to 5000000).sum
```

---

## 5) Fonctions (params par défaut, curryfication, fonctions anonymes)

### Scala 3
```scala
def greet(name: String = "monde"): String = s"Bonjour, $name !"

def mul(a: Int)(b: Int): Int = a * b        // curryfication
val fois2 = mul(2) _                        // partiel
val r = fois2(10)                           // 20

val inc = (x: Int) => x + 1                 // lambda
val xs  = List(1,2,3).map(inc)              // List(2,3,4)
```

### Scala 2
```scala
def greet(name: String = "monde"): String = s"Bonjour, $name !"

def mul(a: Int)(b: Int): Int = a * b
val fois2 = mul(2) _
val r = fois2(10)

val inc = (x: Int) => x + 1
val xs  = List(1,2,3).map(inc)
```

---

## 6) Exercices (avec pistes)

1) **Chaînes** : `normalizeName(s: String): String` → trim, minuscule, capitalize.  
*Piste* : `s.trim.toLowerCase.capitalize`.

2) **Boucles** : multiples de 3 entre 1 et 30.  
*Piste* : `for i <- 1 to 30 if i % 3 == 0 do println(i)`.

3) **Récursion** : somme 1..n en tail-rec.  
*Piste* : accumuler `acc + k` jusqu’à `k==0`.

4) **Fonctions** : `compose(f,g)` → `x => f(g(x))`.  
*Piste* : `(x: A) => f(g(x))`.

5) **By-name** : `time(block: => A): (A, Long)` mesure le temps.  
*Piste* : `val t0 = System.nanoTime` …

---

### Solutions succinctes (Scala 3)
```scala
def normalizeName(s: String) = s.trim.toLowerCase.capitalize

for i <- 1 to 30 if i % 3 == 0 do println(i)

import scala.annotation.tailrec
def sumTo(n: Int): Int =
  @tailrec def go(k: Int, acc: Int): Int =
    if k <= 0 then acc else go(k - 1, acc + k)
  go(n, 0)

def compose[A,B,C](f: B => C, g: A => B): A => C = (x: A) => f(g(x))

def time[A](block: => A): (A, Long) =
  val t0 = System.nanoTime()
  val res = block
  val dt = System.nanoTime() - t0
  (res, dt)
```

---

## 7) Prochaines parties
- **Partie 2** : Collections (List, Map, Set, Vector…), FP (map/flatMap/fold), POO complète.
- **Partie 3** : Exceptions (standard & personnalisées), logging, dates/temps, concurrence.
- **Partie 4** : Mini‑projet ETL + Préparation Spark + Exercices experts.
