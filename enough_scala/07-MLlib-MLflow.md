# 07 — MLlib & MLflow (Spark 4.0) — Scala + PySpark — FR

**Objectif :** Construire un **pipeline ML complet** sur **Spark 4.0** (Scala), avec **feature engineering**, **entraînement**, **tuning**, **évaluation**, **tracking MLflow**, **sauvegarde/reload du modèle**, et **scoring batch + streaming**. En bonus, une **implémentation PySpark** équivalente.

---

## 1) Architecture MLlib + MLflow (vue d’ensemble)

```
Data (bronze) → Prep (silver) → Features (VectorAssembler/Encoders/Scaler) →
→ Model (Regression/Classification) → Cross-Validation → Metrics →
→ MLflow (params, metrics, artifacts, model) → Batch/Streaming Scoring
```

- **API MLlib** basée **DataFrame** (fit/transform).  
- **MLflow** suit : paramètres, métriques, artefacts (plots), et **modèle** (registry possible).

---

## 2) Données d’exemple (Miaradia Rides)

### 2.1 Schéma & jeu synthétique
```scala
case class Ride(rideId: Long, city: String, distanceKm: Double, hour: Int, price: Double)
import spark.implicits._

val rides = Seq(
  Ride(1,"FR", 7.5,  9,  10.8),
  Ride(2,"US",12.0, 18, 18.4),
  Ride(3,"DE", 3.0, 23,  6.2),
  Ride(4,"FR",16.2,  8, 21.7),
  Ride(5,"MG", 9.5, 12, 13.1)
).toDF
```

### 2.2 Objectif modèle
- **Régression** : prédire `price` à partir de `distanceKm`, `city`, `hour`.

---

## 3) Feature Engineering (Scala)

```scala
import org.apache.spark.ml.feature._
import org.apache.spark.ml.Pipeline
import org.apache.spark.sql.functions._

// Encodage de la ville (StringIndexer + OneHotEncoder)
val indexer = new StringIndexer().setInputCol("city").setOutputCol("cityIdx").setHandleInvalid("keep")
val ohe     = new OneHotEncoder().setInputCols(Array("cityIdx")).setOutputCols(Array("cityOhe"))

// Optionnel : bucketiser l'heure (heures creuses/pleines)
val bucketizer = new Bucketizer()
  .setInputCol("hour").setOutputCol("hourBucket")
  .setSplits(Array(Double.NegativeInfinity, 7.0, 10.0, 16.0, 20.0, Double.PositiveInfinity))

// Assemblage des features
val assembler = new VectorAssembler()
  .setInputCols(Array("distanceKm", "hour", "cityOhe"))
  .setOutputCol("featuresRaw")

// Mise à l'échelle (StandardScaler)
val scaler = new StandardScaler().setInputCol("featuresRaw").setOutputCol("features").setWithMean(true).setWithStd(true)
```

---

## 4) Modèles + Pipeline + Tuning (Scala)

```scala
import org.apache.spark.ml.regression.{LinearRegression, GBTRegressor, RandomForestRegressor}
import org.apache.spark.ml.{Pipeline, PipelineModel}
import org.apache.spark.ml.evaluation.RegressionEvaluator
import org.apache.spark.ml.tuning.{CrossValidator, ParamGridBuilder}

// Modèle principal : Régression Linéaire
val lr = new LinearRegression().setFeaturesCol("features").setLabelCol("price")

// Pipeline complet
val pipeline = new Pipeline().setStages(Array(indexer, ohe, assembler, scaler, lr))

// Grid de paramètres
val paramGrid = new ParamGridBuilder()
  .addGrid(lr.regParam, Array(0.0, 0.01, 0.1))
  .addGrid(lr.elasticNetParam, Array(0.0, 0.5, 1.0))
  .build()

val evaluator = new RegressionEvaluator().setLabelCol("price").setPredictionCol("prediction").setMetricName("rmse")

val cv = new CrossValidator()
  .setEstimator(pipeline)
  .setEvaluator(evaluator)
  .setEstimatorParamMaps(paramGrid)
  .setNumFolds(3)

val Array(train, test) = rides.randomSplit(Array(0.8, 0.2), seed = 42L)
val cvModel = cv.fit(train)

val preds = cvModel.transform(test)
val rmse  = evaluator.evaluate(preds)
println(s"RMSE = $rmse")
```

> Alternatives : `RandomForestRegressor`, `GBTRegressor` — juste remplacer `lr` dans le pipeline et adapter la grille.

---

## 5) Tracking MLflow (Scala)

### 5.1 Setup & run
```scala
// libraryDependencies += "org.mlflow" % "mlflow-client" % "2.16.0" (ou via API pyfunc coté driver Python)
// En Scala pur, on peut logger via REST ou wrapper; ici, on montre l'approche la plus simple :
// 1) Utiliser mlflow server externe et logger métriques via REST ou via PySpark (cf. section PySpark).

// Exemple simple : écrire metrics/params dans un dossier "artifacts" (puis les attacher au run via API REST MLflow).
import java.nio.file.{Files, Paths}
import java.nio.charset.StandardCharsets

Files.createDirectories(Paths.get("/tmp/mlflow_artifacts"))
Files.write(Paths.get("/tmp/mlflow_artifacts/metrics.txt"), s"rmse=$rmse
".getBytes(StandardCharsets.UTF_8))
```

> 💡 En environnement mixte, nombre d’équipes utilisent **PySpark** pour l’orchestration MLflow (plus naturel), tout en conservant le **modèle SparkML**. Voir la section **PySpark** ci-dessous pour un **tracking MLflow complet** (start_run, log_param, log_metric, log_model).

---

## 6) Sauvegarde & reload du modèle (Scala)

```scala
val modelPath = "s3a://miaradia-models/lr-price"
cvModel.bestModel.write.overwrite().save(modelPath)

// Reload pour scoring batch
val loaded = PipelineModel.load(modelPath)
val scored = loaded.transform(test)
scored.select("city","distanceKm","hour","prediction").show(false)
```

---

## 7) Scoring Streaming (Scala)

```scala
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._
import org.apache.spark.ml.PipelineModel

val streamSchema = new StructType()
  .add("rideId", LongType).add("city", StringType).add("distanceKm", DoubleType).add("hour", IntegerType)

val incoming = spark.readStream.format("kafka")
  .option("kafka.bootstrap.servers", sys.env.getOrElse("KAFKA_BOOTSTRAP","kafka:9092"))
  .option("subscribe","rides_features")
  .load()
  .selectExpr("CAST(value AS STRING) as json")
  .select(from_json(col("json"), streamSchema).as("r")).select("r.*")

val prodModel = PipelineModel.load(modelPath)
val predictions = prodModel.transform(incoming)

val query = predictions
  .select(to_json(struct(col("rideId"), col("prediction").alias("price_pred"))).alias("value"))
  .writeStream.format("kafka")
  .option("kafka.bootstrap.servers", sys.env.getOrElse("KAFKA_BOOTSTRAP","kafka:9092"))
  .option("topic","rides_predictions")
  .option("checkpointLocation","s3a://miaradia-ckpt/rides_predictions")
  .start()
query.awaitTermination()
```

---

## 8) Bonnes pratiques (Scala)

- **Reproductibilité** : fixer random seed, versionner le **pipeline** et le **jeu de features**.  
- **Drift** : monitorer la dérive des features vs training (moyennes/variances).  
- **Registry** : promouvoir les **meilleurs runs** vers **Production** (via MLflow Model Registry).  
- **Sécurité** : chiffrer les modèles sur S3 (**SSE-KMS**), **IAM least privilege**.  
- **Coûts** : batch scoring pour volumétrie, streaming pour near-real-time.

---

# 🐍 Bonus — PySpark + MLflow (tracking complet)

> Même logique que la version Scala, mais avec **MLflow intégré nativement** (API Python).

```python
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler, StandardScaler
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import mlflow, mlflow.spark

spark = SparkSession.builder.appName("MLlib-MLflow-Py").getOrCreate()

# Données
data = spark.createDataFrame([
    (1,"FR",7.5,9,10.8),
    (2,"US",12.0,18,18.4),
    (3,"DE",3.0,23,6.2),
    (4,"FR",16.2,8,21.7),
    (5,"MG",9.5,12,13.1)
], ["rideId","city","distanceKm","hour","price"])

indexer = StringIndexer(inputCol="city", outputCol="cityIdx", handleInvalid="keep")
ohe     = OneHotEncoder(inputCols=["cityIdx"], outputCols=["cityOhe"])
assembler = VectorAssembler(inputCols=["distanceKm","hour","cityOhe"], outputCol="featuresRaw")
scaler = StandardScaler(inputCol="featuresRaw", outputCol="features", withMean=True, withStd=True)
lr = LinearRegression(featuresCol="features", labelCol="price")
pipe = Pipeline(stages=[indexer, ohe, assembler, scaler, lr])

grid = ParamGridBuilder()     .addGrid(lr.regParam, [0.0, 0.01, 0.1])     .addGrid(lr.elasticNetParam, [0.0, 0.5, 1.0])     .build()

evaluator = RegressionEvaluator(labelCol="price", predictionCol="prediction", metricName="rmse")
train, test = data.randomSplit([0.8, 0.2], seed=42)

with mlflow.start_run(run_name="miaradia-price-regression"):
    cv = CrossValidator(estimator=pipe, estimatorParamMaps=grid, evaluator=evaluator, numFolds=3)
    model = cv.fit(train)
    preds = model.transform(test)
    rmse = evaluator.evaluate(preds)
    mlflow.log_param("algorithm", "LinearRegression")
    mlflow.log_metric("rmse", rmse)
    mlflow.spark.log_model(model.bestModel, "model")
    print("RMSE:", rmse)
```

### Reload + Scoring (PySpark)
```python
import mlflow
from pyspark.ml import PipelineModel

loaded = mlflow.spark.load_model("runs:/<RUN_ID>/model")
scored = loaded.transform(test)
scored.select("city","distanceKm","hour","prediction").show(truncate=False)
```

> Remplace `<RUN_ID>` par l’identifiant du run (vu dans l’UI MLflow).  
> Configure `MLFLOW_TRACKING_URI` vers ton serveur (local ou remote).

---

## 9) Exercices pratiques

1) Ajouter une **feature** `isPeakHour` (0/1) et mesurer l’impact sur le **RMSE**.  
2) Tester un **RandomForestRegressor** et comparer (RMSE/R²).  
3) Activer **MLflow Model Registry** et **promouvoir** la meilleure version en *Production*.  
4) Déployer le modèle en **scoring streaming** (Kafka `rides_features` → `rides_predictions`).

---

## 10) Checklist ML en production

- **Datasets versionnés** (Delta/Iceberg) + lineage (OpenLineage).  
- **Features stables** (feature store, hashing des catégories).  
- **Tuning** validé (k-fold, grid raisonnable).  
- **Tracking** (MLflow) : params/metrics/model/artifacts, **Model Registry**.  
- **Observabilité** : latence scoring, dérive des features, erreurs d’inférence.  
- **Sécurité** : S3 SSE‑KMS + IAM ; data minimization.  
- **SLA** : batch vs streaming (coûts et temps de réponse).

---

**Fin — 07 MLlib & MLflow (Spark 4.0)**.  
Lien naturel avec : **05 Streaming Kafka**, **06a/06b Lakehouse**, **7D Observabilité**.
