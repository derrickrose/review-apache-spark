# 🤖 Scala Expert — Partie 7C : MLlib & Feature Engineering (Spark 4.0, Scala) — FR

**Objectif :** Construire des **pipelines ML** robustes avec **Spark 4.0** (Scala 3), du **feature engineering** au **tuning** et au **déploiement (batch + streaming)**, en s’appuyant sur un **Lakehouse Delta**.

---

## 0) Prérequis & dépendances (sbt)

```scala
ThisBuild / scalaVersion := "3.4.2"
libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % "4.0.0",
  "org.apache.spark" %% "spark-mllib" % "4.0.0",
  "io.delta" %% "delta-spark" % "3.2.0",
  "ch.qos.logback" % "logback-classic" % "1.5.6"
)
```

---

## 1) Données & objectif ML

On repart de la table Delta `rides_delta` vue en 7B :
- Variables : `rideId`, `city`, `distanceKm`, `price`, `ts`
- **Objectif** (exemple) : classifier si un ride est **“premium”** (`label = price >= 20.0`), ou **régression** pour prédire `price`.

---

## 2) Feature engineering (Indexers, Encoders, Assembler, Scaler)

```scala
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.ml.Pipeline
import org.apache.spark.ml.feature._

val spark = SparkSession.builder()
  .appName("MLlib-Features")
  .config("spark.sql.extensions","io.delta.sql.DeltaSparkSessionExtension")
  .config("spark.sql.catalog.spark_catalog","org.apache.spark.sql.delta.catalog.DeltaCatalog")
  .getOrCreate()

// Lecture Delta
val deltaPath = "s3a://miaradia-lake/bronze/rides_delta"
val raw = spark.read.format("delta").load(deltaPath)
  .withColumn("label", (col("price") >= 20.0).cast("double"))
  .na.drop(Seq("city","distanceKm","price"))

// Pipeline de features
val cityIndexer = new StringIndexer().setInputCol("city").setOutputCol("city_idx").setHandleInvalid("keep")
val oneHot      = new OneHotEncoder().setInputCol("city_idx").setOutputCol("city_oh")
val scaler      = new StandardScaler().setInputCol("distanceKm").setOutputCol("distance_scaled").setWithStd(true).setWithMean(false)

val assembler = new VectorAssembler()
  .setInputCols(Array("city_oh","distance_scaled"))
  .setOutputCol("features")
```

> Note : on crée une **étiquette** binaire à partir de `price`. Pour une **régression**, on utilisera `label = price`.

---

## 3) Modèle & Pipeline (classification)

```scala
import org.apache.spark.ml.classification.LogisticRegression
import org.apache.spark.ml.PipelineModel
import org.apache.spark.ml.evaluation.MulticlassClassificationEvaluator

val lr = new LogisticRegression()
  .setFeaturesCol("features")
  .setLabelCol("label")
  .setMaxIter(50)
  .setRegParam(0.01)

val pipeline = new Pipeline().setStages(Array(cityIndexer, oneHot, scaler, assembler, lr))

val Array(train, test) = raw.randomSplit(Array(0.8, 0.2), seed = 42L)
val model = pipeline.fit(train)

val pred = model.transform(test)
pred.select("city","distanceKm","price","label","probability","prediction").show(10, truncate=false)

// Évaluation
val evaluator = new MulticlassClassificationEvaluator()
  .setLabelCol("label")
  .setPredictionCol("prediction")
  .setMetricName("f1")

val f1 = evaluator.evaluate(pred)
println(s"F1-score = $f1")
```

---

## 4) Sauvegarde & rechargement du PipelineModel

```scala
// Sauvegarder le modèle (Lakehouse)
model.write.overwrite().save("s3a://miaradia-models/rides-classifier-pipeline")

// Recharger
val reloaded = PipelineModel.load("s3a://miaradia-models/rides-classifier-pipeline")
```

---

## 5) Tuning : Cross-validation & Grid Search

```scala
import org.apache.spark.ml.tuning.{ParamGridBuilder, CrossValidator}
import org.apache.spark.ml.evaluation.BinaryClassificationEvaluator

val binEval = new BinaryClassificationEvaluator().setLabelCol("label").setMetricName("areaUnderROC")

val paramGrid = new ParamGridBuilder()
  .addGrid(lr.regParam, Array(0.001, 0.01, 0.1))
  .addGrid(lr.maxIter, Array(50, 100))
  .build()

val cv = new CrossValidator()
  .setEstimator(pipeline)
  .setEvaluator(binEval)
  .setEstimatorParamMaps(paramGrid)
  .setNumFolds(3)
  .setParallelism(2) // paralléliser l’entrainement

val cvModel = cv.fit(train)
val cvPred  = cvModel.transform(test)
println(s"AUC = ${binEval.evaluate(cvPred)}")
```

---

## 6) Régression (alternative rapide)

```scala
import org.apache.spark.ml.regression.GBTRegressor
import org.apache.spark.ml.evaluation.RegressionEvaluator

val gbt = new GBTRegressor()
  .setLabelCol("price")
  .setFeaturesCol("features")
  .setMaxDepth(5)
  .setMaxIter(50)

// Pour régression, remplacez label binaire
val rawReg = raw.drop("label").withColumnRenamed("price","label")

val pipeReg = new Pipeline().setStages(Array(cityIndexer, oneHot, scaler, assembler, gbt))
val mReg = pipeReg.fit(rawReg)
val pReg = mReg.transform(rawReg)

val rmse = new RegressionEvaluator().setLabelCol("label").setPredictionCol("prediction").setMetricName("rmse").evaluate(pReg)
println(s"RMSE = $rmse")
```

---

## 7) Scoring batch (job quotidien) & stockage résultats

```scala
val newData = spark.read.format("delta").load("s3a://miaradia-lake/silver/rides_daily")
val scored  = reloaded.transform(newData)
scored.write.mode("overwrite").format("delta").save("s3a://miaradia-lake/gold/rides_scored")
```

---

## 8) Scoring en streaming (Structured Streaming)

```scala
import org.apache.spark.sql.functions._

val stream = spark.readStream
  .format("delta")
  .load("s3a://miaradia-lake/bronze/rides_delta_stream")  // dossier alimenté par 7A
  .withColumn("label", (col("price") >= 20.0).cast("double"))

val scoredStream = reloaded.transform(stream)

val q = scoredStream
  .writeStream
  .format("delta")
  .option("checkpointLocation", "s3a://miaradia-checkpoints/stream-scoring")
  .option("path", "s3a://miaradia-lake/gold/rides_scored_stream")
  .outputMode("append")
  .start()

q.awaitTermination()
```

---

## 9) ML avancé : autres algos utiles

- **Classification** : `RandomForestClassifier`, `GBTClassifier`, `LinearSVC`  
- **Régression** : `RandomForestRegressor`, `GBTRegressor`, `LinearRegression`  
- **Clustering** : `KMeans`, `BisectingKMeans`, `GaussianMixture`  
- **Recommandation** : `ALS` (collaborative filtering)  

Exemple `KMeans` :
```scala
import org.apache.spark.ml.clustering.KMeans

val kmeans = new KMeans().setK(4).setSeed(42L).setFeaturesCol("features")
val kmModel = kmeans.fit(assembler.transform(raw))
println(s"WSSSE: ${kmModel.summary.trainingCost}")
```

---

## 10) Bonnes pratiques ML en production

- **Versionner** les modèles (`modelPath/version`), garder les artefacts (`PipelineModel`, hyperparamètres, métriques).  
- **Reproductibilité** : seed fixée, splits stables, **Delta Time Travel** pour les données d’entrainement.  
- **Monitoring** : suivre *drift* (statistiques de features), qualité des labels, AUC/F1 au fil du temps.  
- **MLflow** (ou équivalent) pour tracking des expériences et du registry modèles.  
- **Explainability** : importance des features (`featureImportances` pour RF/GBT), SHAP (lib externe).  
- **Sécurité** : contrôler l’accès au dossier des modèles (IAM/KMS), logs audit.  
- **Coûts** : coalesce en écriture, compression (ZSTD), planifier l’entrainement hors pics.  

---

**Fin — 7C.** Tu as maintenant un **pipeline ML complet** (features → modèle → tuning → scoring batch/stream) sur **Spark 4.0**.
