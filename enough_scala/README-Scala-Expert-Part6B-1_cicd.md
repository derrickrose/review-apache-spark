# 🔧 Scala Expert — Partie 6B‑1 : CI/CD & Sécurité (FR)

**Objectif** : Automatiser le build/test/deploy des jobs Spark (CI/CD) et sécuriser l’exécution (IAM/Kerberos/K8s SA, chiffrement, audit).

---

## 1) CI/CD — Pipelines réels

### 1.1 Jenkinsfile (de la PR au déploiement)

```groovy
pipeline {
  agent any
  environment {
    SBT_OPTS = "-Dsbt.log.noformat=true"
    AWS_REGION = "eu-west-1"
    JAR = "target/scala-3.4/miaradia-etl-assembly.jar"
    S3_JARS = "s3://miaradia-artifacts/jars/"
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Lint & Format') { steps { sh 'sbt scalafmtAll && sbt scalastyle' } }
    stage('Test') { steps { sh 'sbt -v test' } }
    stage('Package') { steps { sh 'sbt clean assembly' } }
    stage('Upload JAR') { steps { sh 'aws s3 cp ${JAR} ${S3_JARS}' } }
    stage('Deploy (EMR spark-submit)') {
      when { branch 'main' }
      steps {
        sh '''
          spark-submit \
            --deploy-mode cluster \
            --class com.miaradia.spark.MiaradiaSparkApp \
            --conf spark.executor.cores=5 \
            --conf spark.executor.memory=24g \
            --conf spark.sql.shuffle.partitions=600 \
            ${S3_JARS}miaradia-etl-assembly.jar \
            s3://miaradia-data/rides.csv s3://miaradia-data/cities.csv s3://miaradia-out
        '''
      }
    }
  }
  post { always { junit 'target/test-reports/**/*.xml' } }
}
```

### 1.2 GitHub Actions (build + test + push image ECR + spark-submit K8s)

```yaml
name: ci-cd-spark
on:
  push:
    branches: [ main ]
  pull_request:
jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Java
        uses: actions/setup-java@v4
        with: { distribution: 'temurin', java-version: '21' }
      - name: Cache sbt
        uses: actions/cache@v4
        with:
          path: |
            ~/.ivy2/cache
            ~/.sbt
            ~/.cache/coursier
          key: ${{ runner.os }}-sbt-${{ hashFiles('**/build.sbt') }}
      - name: Lint & Test
        run: |
          sbt scalafmtAll
          sbt scalastyle
          sbt test
      - name: Package fat JAR
        run: sbt assembly
      - name: Build & push Docker
        env:
          REG: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.eu-west-1.amazonaws.com
        run: |
          docker build -t $REG/miaradia-spark:latest .
          aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin $REG
          docker push $REG/miaradia-spark:latest
      - name: spark-submit on K8s
        run: |
          /opt/spark/bin/spark-submit \
            --master k8s://https://$K8S_API \
            --deploy-mode cluster \
            --class com.miaradia.spark.MiaradiaSparkApp \
            --conf spark.kubernetes.container.image=$REG/miaradia-spark:latest \
            local:///opt/spark/jars/miaradia-etl-assembly.jar \
            s3a://miaradia-data/rides.csv s3a://miaradia-data/cities.csv s3a://miaradia-out
```

---

## 2) Tests Spark & qualité de code

### 2.1 ScalaTest (exemple ciblé)

```scala
import org.scalatest.funsuite.AnyFunSuite
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

class KpiSpec extends AnyFunSuite {
  val spark = SparkSession.builder().master("local[2]").appName("test").getOrCreate()
  import spark.implicits._

  test("revenue by city computes correctly") {
    val df = Seq(("Paris", 10.0), ("Paris", 5.0), ("Lyon", 3.0)).toDF("city", "price")
    val res = df.groupBy($"city").agg(sum($"price").as("rev")).as[(String,Double)].collect().toMap
    assert(res("Paris") == 15.0 && res("Lyon") == 3.0)
  }
}
```

### 2.2 Lint & Format

`project/plugins.sbt` :
```scala
addSbtPlugin("org.scalameta" % "sbt-scalafmt" % "2.5.2")
addSbtPlugin("org.scalastyle" %% "scalastyle-sbt-plugin" % "1.0.0")
```

`build.sbt` :
```scala
scalafmtOnCompile := true
```

---

## 3) Sécurité — IAM / Kerberos / K8s

### 3.1 AWS IAM (EMR/S3) — principes
- Rôles IAM pour EMR (EMR_EC2_DefaultRole / EMR_DefaultRole).  
- Politiques S3 minimales : accès **lecture** aux inputs, **écriture** aux outputs.  
- Chiffrement : SSE‑S3 ou SSE‑KMS sur buckets sensibles.

### 3.2 Kerberos (Hadoop/YARN)
- Config realm & keytabs pour HDFS/YARN; spark-submit avec délégation :  
```bash
spark-submit --principal user@REALM --keytab /path/user.keytab ...
```

### 3.3 Kubernetes — ServiceAccount & RBAC
YAML minimal :
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark-sa
  namespace: data
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: spark-role
  namespace: data
rules:
  - apiGroups: [""] 
    resources: ["pods","services","configmaps"]
    verbs: ["create","get","list","watch","delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: spark-rb
  namespace: data
subjects:
  - kind: ServiceAccount
    name: spark-sa
    namespace: data
roleRef:
  kind: Role
  name: spark-role
  apiGroup: rbac.authorization.k8s.io
```

### 3.4 Chiffrement & Réseau
- **In‑transit** : TLS (ingress, s3a SSL).  
- **At‑rest** : Parquet chiffré (KMS), S3 SSE‑KMS.  
- **Secret management** : K8s Secrets / AWS Secrets Manager.

---

## 4) Audit & conformité (logs + accès)

- **Logs structurés** (JSON) via Logback → ELK/Opensearch.  
- Traçabilité : corroler `appId`, `stageId`, `jobId`.  
- ACL Spark : `spark.acls.enable=true` + `spark.ui.view.acls`.

**Fin — 6B‑1 (CI/CD & Sécurité).** Prochaine : **6B‑2 (Lineage, Benchmarking, Comparatif & Audit final)**.
