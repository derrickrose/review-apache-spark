# 🧠 Scala Expert — Partie 6B‑2 : Lineage, Benchmarking, Comparatif & Audit (FR)

**Objectif** : Traçabilité data (lineage), mesure de performance, choix technos batch/stream, et audit final avant prod.

---

## 1) Data Lineage & Gouvernance

### 1.1 OpenLineage (concept)
- Standard ouvert pour tracer **jobs, datasets, runs**.  
- Connecteurs pour Airflow, Spark, dbt…

### 1.2 Atlas / Glue Catalog (exemples)
Spark avec Hive/Glue :
```scala
spark.conf.set("spark.sql.catalogImplementation","hive")
spark.sql("CREATE TABLE IF NOT EXISTS bronze.rides (rideId BIGINT, userId BIGINT, city STRING, price DOUBLE) STORED AS PARQUET")
spark.sql("MSCK REPAIR TABLE bronze.rides")
```

Airflow → OpenLineage :
```python
# airflow.cfg: openlineage backend + connection URL vers Marquez
# Chaque tâche envoie automatiquement les métadonnées (run, inputs/outputs)
```

Tags business (AWS Glue) :
```bash
aws glue create-tags --resource-arn arn:aws:glue:... --tags dept=finance,pii=false
```

---

## 2) Benchmarking & Profiling

### 2.1 Micro-benchmark Scala (RDD vs DF vs DS)
```scala
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

object Bench {
  def time[A](name: String)(f: => A): A = {
    val t0 = System.nanoTime(); val r = f; val dt = (System.nanoTime()-t0)/1e9
    println(s"[$name] ${dt}s"); r
  }
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder().master("local[*]").getOrCreate()
    import spark.implicits._
    val N = 5_000_000
    val rdd = spark.sparkContext.parallelize(1 to N)
    val df  = rdd.toDF("x")
    val ds  = df.as[Int]

    time("RDD sum"){ rdd.reduce(_+_) }
    time("DF sum"){ df.agg(sum($"x")).collect() }
    time("DS sum"){ ds.reduce(_+_) }
  }
}
```

### 2.2 `sparkMeasure` (collecte métriques)
```scala
// build.sbt
libraryDependencies += "ch.cern.sparkmeasure" %% "spark-measure" % "0.23"
```
```scala
import ch.cern.sparkmeasure.StageMetrics
val sm = StageMetrics(spark)
sm.begin()
val res = spark.read.parquet("/path").groupBy("city").count().collect()
sm.end()
sm.createStageMetricsDF().show(false) // CPU time, bytes read, shuffle spill...
```

### 2.3 SparkListener custom (profiling maison)
```scala
import org.apache.spark.scheduler.{SparkListener, SparkListenerStageCompleted}
spark.sparkContext.addSparkListener(new SparkListener {
  override def onStageCompleted(s: SparkListenerStageCompleted): Unit = {
    val st = s.stageInfo
    println(s"[Stage ${st.stageId}] time=${st.duration.getOrElse(0)}ms tasks=${st.numTasks}")
  }
})
```

---

## 3) Comparatif Spark vs Flink vs Beam

| Critère | Spark | Flink | Beam |
|--------|------|------|-----|
| Batch | ✅ Excellent | ✅ Bon | ✅ via runners |
| Streaming | ✅ Très bon (latence sec) | ✅ **Top** (sub‑sec) | ⚠️ dépend du runner |
| Stateful | ✅ Bon | ✅ **Avancé** | ✅ via runner |
| Exactly-once | ✅ avec checkpoints | ✅ **natif** | ⚠️ dépend du runner |
| Écosystème | Très large | Grandissant | Standard d’API |
| Quand ? | ETL, ML, batch+stream | Stream temps réel critique | Portabilité multi‑engins |

**Règle simple** :  
- Temps réel **sous‑seconde** / stateful très complexe → **Flink**.  
- ETL/BI/ML batch + stream unifiés → **Spark**.  
- Portabilité multi‑runners (Dataflow…) → **Beam**.

---

## 4) Audit final (15 points)

1. Dimensionnement validé (5A)  
2. Plans `explain(true)` sans shuffle inutile  
3. AQE ON + skew join ON (si besoin)  
4. Data Quality (Deequ/GE) pass ✅  
5. Logs JSON + rétention définie  
6. Metrics Prometheus + dashboards Grafana  
7. Sécurité IAM/Kerberos/SA OK  
8. Secrets managés (KMS/SM/Secrets)  
9. CI/CD : tests, build, package, déploiement automatique  
10. Rollback possible (N-1 JAR/image)  
11. Backups/checkpoints HDFS/S3  
12. Lineage (Catalog/Atlas/OpenLineage) opérant  
13. Coût & débit I/O validés (S3/HDFS)  
14. Alertes SLA (latence/erreurs) en place  
15. Documentation/diagrammes à jour (README + dataflow)

---

## 5) Annexes utiles

- **scalafmt** : `.scalafmt.conf` partagé, build fail si non formaté.  
- **scalastyle** : règles basiques (import non utilisés, ligne > 120).  
- **Modèles de diagrammes** : C4, DAG Airflow, flux Kafka → Spark → Parquet.

**Fin — 6B‑2 (Lineage, Benchmarking, Comparatif & Audit).**
