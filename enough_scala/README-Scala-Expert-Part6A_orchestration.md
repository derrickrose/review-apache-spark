# 🧱 Scala Expert — Partie 6A : Orchestration, Data Quality & IaC (FR)

**Objectif** : Industrialiser vos jobs Spark avec **orchestration (Airflow)**, **qualité des données (Deequ / Great Expectations)**,
et **Infrastructure as Code** (Terraform EMR + Spark on Kubernetes).

---

## 1) Orchestration des jobs Spark (Airflow)

### 1.1 DAG Airflow avec `SparkSubmitOperator` (YARN/EMR)
```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

default_args = {
    'owner': 'miaradia',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'sla': timedelta(minutes=30),
}

with DAG(
    dag_id='etl_miaradia_batch',
    start_date=datetime(2025, 10, 22),
    schedule_interval='0 2 * * *',  # tous les jours à 02:00
    catchup=False,
    default_args=default_args,
) as dag:

    etl = SparkSubmitOperator(
        task_id='spark_etl',
        application='s3://miaradia-artifacts/jars/miaradia-etl-assembly.jar',
        java_class='com.miaradia.spark.MiaradiaSparkApp',
        conn_id='spark_default',  # Spark/YARN connection
        application_args=['s3://miaradia-data/rides.csv','s3://miaradia-data/cities.csv','s3://miaradia-out'],
        verbose=True,
        conf={
            'spark.executor.cores': '5',
            'spark.executor.memory': '24g',
            'spark.executor.memoryOverhead': '3g',
            'spark.sql.shuffle.partitions': '600',
            'spark.sql.adaptive.enabled': 'true',
            'spark.serializer': 'org.apache.spark.serializer.KryoSerializer',
        },
    )

    etl
```

### 1.2 Airflow avec Kubernetes (Spark-on-K8s)
```python
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime

with DAG('etl_miaradia_k8s', start_date=datetime(2025,10,22), schedule_interval=None, catchup=False) as dag:
    spark_job = KubernetesPodOperator(
        name='miaradia-spark',
        task_id='spark-submit',
        namespace='data',
        image='ghcr.io/miaradia/spark:3.5.1',
        cmds=['/opt/spark/bin/spark-submit'],
        arguments=[
            '--master','k8s://https://kubernetes.default.svc',
            '--deploy-mode','cluster',
            '--class','com.miaradia.spark.MiaradiaSparkApp',
            '--conf','spark.kubernetes.container.image=ghcr.io/miaradia/spark:3.5.1',
            '--conf','spark.executor.instances=40',
            '--conf','spark.executor.cores=5',
            '--conf','spark.executor.memory=24g',
            '--conf','spark.sql.adaptive.enabled=true',
            'local:///opt/spark/jars/miaradia-etl-assembly.jar',
            's3a://miaradia-data/rides.csv','s3a://miaradia-data/cities.csv','s3a://miaradia-out'
        ],
        get_logs=True,
    )
```

---

## 2) Data Quality & Validation

### 2.1 Deequ (Scala) — vérifications de règles qualité
```scala
// build.sbt
libraryDependencies += "com.amazon.deequ" %% "deequ" % "2.0.7-spark-3.5"
```
```scala
import com.amazon.deequ.VerificationSuite
import com.amazon.deequ.checks.{Check, CheckLevel}
import com.amazon.deequ.constraints.ConstrainableDataTypes
import org.apache.spark.sql.SparkSession

val spark = SparkSession.builder().appName("DQ").getOrCreate()
val df = spark.read.option("header","true").csv("s3://miaradia-data/rides.csv")

val check = Check(CheckLevel.Error, "Règles DQ rides")
  .isComplete("userId")
  .isNonNegative("price")
  .isNonNegative("distanceKm")
  .isContainedIn("city", Array("FR","MG","US"))

val result = VerificationSuite().onData(df).addCheck(check).run()
if (result.status.toString != "Success") sys.error("Data Quality failed")
```

### 2.2 Great Expectations (Python) — expectations & checkpoint
```python
import great_expectations as ge
from great_expectations.core.batch import BatchRequest
from great_expectations.checkpoint import SimpleCheckpoint

context = ge.get_context()
batch_request = BatchRequest(
    datasource_name='miaradia_datasource',
    data_connector_name='default_inferred_data_connector_name',
    data_asset_name='rides.csv',
)

validator = context.get_validator(batch_request=batch_request, expectation_suite_name='rides_suite')
validator.expect_column_values_to_not_be_null('userId')
validator.expect_column_values_to_be_between('price', min_value=0)
validator.expect_column_values_to_be_between('distanceKm', min_value=0)
validator.expect_column_values_to_be_in_set('city', [ 'FR','MG','US'])
context.save_expectation_suite(validator.expectation_suite)

checkpoint = SimpleCheckpoint(
    name='rides_checkpoint',
    data_context=context,
    validations=[{'batch_request': batch_request, 'expectation_suite_name': 'rides_suite'}]
)
res = checkpoint.run()
assert res['success'], 'Data Quality failed'
```

---

## 3) Infrastructure as Code (IaC)

### 3.1 Terraform — AWS EMR (extrait minimal)
```hcl
provider "aws" { region = "eu-west-1" }

resource "aws_emr_cluster" "spark" {
  name          = "miaradia-spark"
  release_label = "emr-7.1.0"
  applications  = ["Spark"]
  master_instance_type = "m5.xlarge"
  core_instance_type   = "m5.2xlarge"
  core_instance_count  = 3

  configurations_json = <<JSON
  [{
    "Classification": "spark-defaults",
    "Properties": {
      "spark.sql.adaptive.enabled": "true",
      "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
    }
  }]
  JSON
}
```

### 3.2 Spark on Kubernetes — SparkOperator (YAML complet minimal)
```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: miaradia-spark-job
  namespace: data
spec:
  type: Scala
  mode: cluster
  image: ghcr.io/miaradia/spark:3.5.1
  mainClass: com.miaradia.spark.MiaradiaSparkApp
  mainApplicationFile: local:///opt/spark/jars/miaradia-etl-assembly.jar
  sparkVersion: "3.5.1"
  driver:
    cores: 2
    memory: 4g
    serviceAccount: spark-sa
  executor:
    instances: 20
    cores: 4
    memory: 16g
  sparkConf:
    "spark.sql.adaptive.enabled": "true"
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
```

---

## 4) Bonnes pratiques (résumé opérationnel)
- **Orchestration** : un job = une responsabilité; retrys et SLA; alertes sur échecs.
- **DQ** : bloquer en cas d’échec critique (prix < 0, colonnes nulles…), logs des anomalies.
- **IaC** : versionner les configs (git), séparer dev/test/prod, variables pour secrets.
- **Observabilité** : Spark UI, métriques, logs JSON, corrélation par jobId/stageId.

**Fin — Partie 6A.** Prochaine : **6B — CI/CD, Sécurité, Lineage, Benchmarking, Comparatif & Audit.**
