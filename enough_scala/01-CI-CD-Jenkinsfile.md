# 01 — CI/CD Jenkinsfile (Spark Scala/SBT) — FR

**Objectif :** Pipeline **Jenkins** prêt à l’emploi pour **build**, **tester**, **packager** (fat JAR) et **déployer** un job **Apache Spark 4.0 / Scala 3.4** sur **EMR (YARN)** ou **Kubernetes**.  
Inclut : cache dépendances SBT, rapports JUnit, artefacts, *optional* Docker image push (ECR), et variables d’environnement standardisées.

---

## 1) Arborescence projet (exemple)
```
.
├─ Jenkinsfile
├─ build.sbt
├─ project/
│  ├─ plugins.sbt
│  └─ build.properties
├─ src/
│  ├─ main/scala/com/miaradia/spark/App.scala
│  └─ test/scala/com/miaradia/spark/AppSpec.scala
├─ infra/
│  ├─ k8s/         # manifests optionnels
│  └─ scripts/     # scripts spark-submit, utils
```

---

## 2) Prérequis Jenkins (nœud/agent)
- **Java 21** (ou 17) installé
- **SBT** (1.10+)
- **Docker** (si build image)
- **AWS CLI** (si S3/ECR/EMR)
- **kubectl** & **spark-submit** (si K8s)
- Credentials Jenkins : `AWS_DEFAULT_REGION`, `AWS_ACCOUNT_ID`, `K8S_API`, `REGISTRY`, etc.

> Conseillé : *Jenkins Shared Library* pour réutiliser steps (cache SBT, login ECR, etc.).

---

## 3) Jenkinsfile — pipeline complet

```groovy
pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 60, unit: 'MINUTES')
  }

  environment {
    JAVA_HOME    = '/usr/lib/jvm/java-21-openjdk'     // adapter à l'agent
    SBT_OPTS     = '-Dsbt.log.noformat=true'
    APP_NAME     = 'miaradia-spark-app'
    SCALA_BIN    = '3.4.2'
    SPARK_VER    = '4.0.0'
    FAT_JAR      = "target/scala-3.4/${APP_NAME}-assembly.jar"
    S3_BUCKET_AR = 's3://miaradia-artifacts/jars/'
    DOCKER_REG   = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_DEFAULT_REGION}.amazonaws.com"
    IMAGE_NAME   = "${DOCKER_REG}/${APP_NAME}:${SPARK_VER}"
    K8S_MASTER   = "k8s://${env.K8S_API}"             // ex: https://api.k8s:6443
  }

  stages {

    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Setup (SBT cache)') {
      steps {
        sh '''
          echo "Cache sbt/ivy/coursier"
          mkdir -p ~/.ivy2/cache ~/.sbt ~/.cache/coursier
        '''
      }
    }

    stage('Lint & Format') {
      steps {
        sh '''
          sbt scalafmtAll
          sbt scalastyle
        '''
      }
    }

    stage('Test') {
      steps {
        sh 'sbt -v test'
      }
      post {
        always {
          junit testResults: 'target/test-reports/**/*.xml', allowEmptyResults: true
        }
      }
    }

    stage('Package (fat JAR)') {
      steps {
        sh 'sbt clean assembly'
        sh 'ls -lh target/scala-*/'
      }
      post {
        success {
          archiveArtifacts artifacts: 'target/scala-*/**/*.jar', fingerprint: true
        }
      }
    }

    stage('Upload artifact (S3)') {
      when { expression { return env.AWS_DEFAULT_REGION } }
      steps {
        sh '''
          aws s3 cp "${FAT_JAR}" "${S3_BUCKET_AR}"
          echo "Uploaded to ${S3_BUCKET_AR}"
        '''
      }
    }

    stage('Build & Push Docker (optional)') {
      when { expression { return env.AWS_ACCOUNT_ID } }
      steps {
        sh '''
          aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin ${DOCKER_REG}
          docker build -t ${IMAGE_NAME} --build-arg SPARK_VER=${SPARK_VER} .
          docker push ${IMAGE_NAME}
        '''
      }
    }

    stage('Deploy EMR (spark-submit)') {
      when { allOf { branch 'main'; expression { return env.DEPLOY_EMR == 'true' } } }
      steps {
        sh '''
          spark-submit             --deploy-mode cluster             --class com.miaradia.spark.App             --conf spark.sql.adaptive.enabled=true             --conf spark.serializer=org.apache.spark.serializer.KryoSerializer             ${S3_BUCKET_AR}${APP_NAME}-assembly.jar             s3a://miaradia-data/in.csv s3a://miaradia-out/
        '''
      }
    }

    stage('Deploy K8s (spark-submit)') {
      when { allOf { branch 'main'; expression { return env.DEPLOY_K8S == 'true' } } }
      steps {
        sh '''
          /opt/spark/bin/spark-submit             --master ${K8S_MASTER}             --deploy-mode cluster             --name ${APP_NAME}             --class com.miaradia.spark.App             --conf spark.kubernetes.container.image=${IMAGE_NAME}             --conf spark.sql.adaptive.enabled=true             local:///opt/spark/jars/${APP_NAME}-assembly.jar             s3a://miaradia-data/in.csv s3a://miaradia-out/
        '''
      }
    }
  }

  post {
    success {
      echo 'Pipeline OK ✅'
    }
    failure {
      echo 'Pipeline KO ❌ — vérifier logs des stages.'
    }
    always {
      cleanWs(deleteDirs: true, notFailBuild: true)
    }
  }
}
```

---

## 4) `build.sbt` (exemple minimal pro)

```scala
ThisBuild / scalaVersion := "3.4.2"

lazy val root = (project in file("."))
  .settings(
    name := "miaradia-spark-app",
    version := "1.0.0",
    libraryDependencies ++= Seq(
      "org.apache.spark" %% "spark-sql" % "4.0.0" % "provided",
      "org.scalatest" %% "scalatest" % "3.2.19" % Test
    ),
    assembly / test := {},
    assembly / assemblyMergeStrategy := {
      case PathList("META-INF", xs @ _*) => MergeStrategy.discard
      case _ => MergeStrategy.first
    }
  )
```

`project/plugins.sbt` :
```scala
addSbtPlugin("com.eed3si9n" % "sbt-assembly" % "2.2.0")
addSbtPlugin("org.scalameta" % "sbt-scalafmt" % "2.5.2")
addSbtPlugin("org.scalastyle" %% "scalastyle-sbt-plugin" % "1.0.0")
```

---

## 5) Dockerfile (optionnel, Spark on K8s)

```dockerfile
FROM bitnami/spark:4.0.0
ARG SPARK_VER=4.0.0
USER root
COPY target/scala-3.4/miaradia-spark-app-assembly.jar /opt/spark/jars/
USER 1001
```

---

## 6) Conseils & bonnes pratiques

- **Branches** : déployer seulement depuis `main`/`release/*`.
- **Secrets** : Jenkins Credentials + variables d’env. jamais en clair dans le Jenkinsfile.
- **Tests** : **toujours** publier JUnit + archiver le fat JAR.
- **Artefacts** : nommer avec version/tag (`app-1.0.0+gitsha.jar`).
- **EMR** : utiliser **Managed Scaling** (EMR 6/7) et roles IAM stricts (S3 read/write).
- **K8s** : utiliser **ServiceAccount + RBAC**, `spark.dynamicAllocation.enabled=true`.

---

## 7) Variables d’environnement utiles (Jenkins)

- `AWS_DEFAULT_REGION=eu-west-1`
- `AWS_ACCOUNT_ID=123456789012`
- `DEPLOY_EMR=true|false`
- `DEPLOY_K8S=true|false`
- `K8S_API=https://api.mycluster:6443`
- `REGISTRY=<optionnel-si-non-ECR>`

---

## 8) Script helper (facultatif)

`scripts/run-spark-submit-emr.sh` :
```bash
#!/usr/bin/env bash
set -euo pipefail
APP_JAR="$1"; IN="$2"; OUT="$3"
spark-submit --deploy-mode cluster   --class com.miaradia.spark.App   --conf spark.sql.adaptive.enabled=true   --conf spark.serializer=org.apache.spark.serializer.KryoSerializer   "$APP_JAR" "$IN" "$OUT"
```
(Ensuite appeler ce script depuis Jenkins)

---

**Fin — 01 CI/CD Jenkinsfile.**  
Prochain fichier : **02-GitHub-Actions.md** (workflow équivalent CI/CD sur GitHub).
