# 02 — GitHub Actions (CI/CD Spark Scala) — FR

**Objectif :** Workflow **GitHub Actions** prêt à l’emploi pour **build**, **tester**, **packager** (fat JAR SBT), **publier artefacts**, **push Docker ECR** (optionnel) et **déployer** un job **Apache Spark 4.0 / Scala 3.4** sur **Kubernetes** et/ou **EMR**.

---

## 1) Prérequis
- **Repo GitHub** avec code Scala/Spark (SBT).
- **Secrets GitHub** configurés :
  - `AWS_ACCOUNT_ID`, `AWS_REGION` (ex: eu-west-1)
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (ou rôle OIDC, cf. plus bas)
  - `K8S_API`, `K8S_NAMESPACE` (si K8s), `ECR_REPO` (ex: miaradia-spark)
- **Java 21** (ou 17), **SBT 1.10+**.

---

## 2) Workflow CI/CD — `/.github/workflows/ci-cd-spark.yml`

```yaml
name: CI-CD Spark

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-test-package:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    env:
      APP_NAME: miaradia-spark-app
      SCALA_BIN: 3.4.2
      SPARK_VER: 4.0.0
      AWS_REGION: ${{ secrets.AWS_REGION }}
      AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
      ECR_REPO: ${{ secrets.ECR_REPO }}
      REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ secrets.AWS_REGION }}.amazonaws.com
    steps:
      - uses: actions/checkout@v4

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '21'

      - name: Cache SBT
        uses: actions/cache@v4
        with:
          path: |
            ~/.ivy2/cache
            ~/.sbt
            ~/.cache/coursier
          key: ${{ runner.os }}-sbt-${{ hashFiles('**/build.sbt') }}-${{ hashFiles('**/project/plugins.sbt') }}
          restore-keys: |
            ${{ runner.os }}-sbt-

      - name: Lint & Test
        run: |
          sbt scalafmtAll
          sbt scalastyle
          sbt -v test

      - name: Package fat JAR
        run: |
          sbt clean assembly
          ls -lh target/scala-*/

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: fat-jar
          path: target/scala-*/**/*.jar
          retention-days: 7

      - name: Configure AWS creds (ECR / S3 / EMR)
        if: ${{ secrets.AWS_ACCESS_KEY_ID != '' }}
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Login to ECR
        if: ${{ secrets.AWS_ACCOUNT_ID != '' && secrets.ECR_REPO != '' }}
        run: |
          aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $REGISTRY

      - name: Build & Push Docker image (optional)
        if: ${{ secrets.AWS_ACCOUNT_ID != '' && secrets.ECR_REPO != '' }}
        run: |
          TAG=${{ github.sha }}
          IMG=$REGISTRY/$ECR_REPO:$TAG
          docker build -t $IMG --build-arg SPARK_VER=$SPARK_VER .
          docker push $IMG
          echo "IMAGE=$IMG" >> $GITHUB_ENV

      - name: Upload fat JAR to S3 (optional)
        if: ${{ secrets.AWS_ACCOUNT_ID != '' }}
        run: |
          JAR=$(ls target/scala-*/${{ env.APP_NAME }}-assembly.jar | head -n1)
          aws s3 cp "$JAR" s3://miaradia-artifacts/jars/
```

---

## 3) Déploiement Kubernetes (Spark on K8s)

### 3.1 Avec `spark-submit` (cluster mode)
```yaml
  deploy-k8s:
    needs: build-test-package
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Setup kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'v1.29.0'
      - name: Kubeconfig
        run: |
          echo "${{ secrets.KUBECONFIG_CONTENT }}" > kubeconfig
          export KUBECONFIG=$PWD/kubeconfig
          kubectl config set-context --current --namespace=${{ secrets.K8S_NAMESPACE }}
      - name: Submit Spark job
        env:
          IMAGE: ${{ env.IMAGE }}
          K8S_API: ${{ secrets.K8S_API }}
        run: |
          /opt/spark/bin/spark-submit             --master k8s://$K8S_API             --deploy-mode cluster             --class com.miaradia.spark.App             --conf spark.kubernetes.container.image=$IMAGE             --conf spark.sql.adaptive.enabled=true             local:///opt/spark/jars/miaradia-spark-app-assembly.jar             s3a://miaradia-data/in.csv s3a://miaradia-out/
```

### 3.2 Avec Spark Operator (CRD `SparkApplication`)
Publie un manifest YAML et laisse l’opérateur gérer le job.

```yaml
  deploy-operator:
    needs: build-test-package
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Setup kubectl
        uses: azure/setup-kubectl@v4
      - name: Apply SparkApplication
        run: |
          envsubst < infra/k8s/spark-application.yaml | kubectl apply -f -
```

`infra/k8s/spark-application.yaml` (extrait) :
```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: miaradia-spark-app
  namespace: ${K8S_NAMESPACE}
spec:
  type: Scala
  mode: cluster
  image: ${IMAGE}
  mainClass: com.miaradia.spark.App
  mainApplicationFile: "local:///opt/spark/jars/miaradia-spark-app-assembly.jar"
  sparkVersion: "4.0.0"
  restartPolicy:
    type: Never
```

---

## 4) Déploiement EMR (optionnel)

### 4.1 Step via AWS CLI
```yaml
  deploy-emr:
    needs: build-test-package
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Configure AWS creds
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
      - name: Submit EMR step
        run: |
          aws emr add-steps --cluster-id j-XXXX             --steps Type=Spark,Name="miaradia-spark",ActionOnFailure=CONTINUE,Args="--deploy-mode,cluster,--class,com.miaradia.spark.App,s3://miaradia-artifacts/jars/miaradia-spark-app-assembly.jar,s3a://miaradia-data/in.csv,s3a://miaradia-out/"
```

---

## 5) OIDC AWS (recommandé) au lieu d’Access Keys

```yaml
permissions:
  id-token: write
  contents: read

- name: Configure AWS creds via OIDC
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::<account>:role/GHA-OIDC-Role
    role-session-name: gha-spark
    aws-region: ${{ secrets.AWS_REGION }}
```

---

## 6) Conseils & bonnes pratiques

- **Artifacts** : publier le **fat JAR** et l’image Docker (tag = `github.sha`).
- **Conditions de déploiement** : uniquement sur `main` ou release tags.
- **Sécurité** : utiliser **OIDC** (assume-role) plutôt que des clés statiques.
- **Performances** : activer caches SBT, limiter les jobs concurrents (`concurrency`).
- **Qualité** : `scalafmt` + `scalastyle` obligatoires avant build.
- **Observabilité** : ajouter un job “post-deploy” qui vérifie Spark UI / Prometheus.

---

## 7) Variables utiles
- `IMAGE` (exportée après push)  
- `REGISTRY`, `ECR_REPO`  
- `K8S_NAMESPACE`, `K8S_API`  
- `AWS_REGION`, `AWS_ACCOUNT_ID`

---

**Fin — 02 GitHub Actions.**  
Prochain fichier : **03-Spark-Security.md** (IAM, Kerberos, RBAC, secrets, chiffrement).
