# 03a — IAM, Kerberos & RBAC Kubernetes (Spark Prod) — FR

**Objectif :** Sécuriser **l’authentification et l’autorisation** de vos jobs **Apache Spark 4.0** sur **AWS EMR/S3/Glue** et **Kubernetes** (Spark Operator), plus **Kerberos** pour HDFS/YARN.

> Scope volontairement ciblé : **AWS + K8s + Kerberos**, sans Vault/Secrets Manager (cf. 03b pour encryption & secrets).

---

## 1) IAM AWS — Rôles & Politiques (EMR / S3 / Glue)

### 1.1 Politique IAM minimale — rôle d’exécution Spark (Driver/Executor)
`policy-spark-exec.json` :
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadWriteLake",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": ["arn:aws:s3:::miaradia-lake","arn:aws:s3:::miaradia-artifacts"]
    },
    {
      "Sid": "S3RWObjects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject","s3:PutObject","s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::miaradia-lake/*",
        "arn:aws:s3:::miaradia-artifacts/*"
      ]
    },
    {
      "Sid": "GlueCatalogRead",
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase","glue:GetDatabases",
        "glue:GetTable","glue:GetTables","glue:GetPartition","glue:GetPartitions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

> 🔒 **Least privilege** : limiter aux buckets nécessaires et préfixes (`s3:prefix`). Ajouter `kms:Decrypt/Encrypt` si SSE‑KMS (voir 03b).

### 1.2 Trust policy (assume role) — EMR ou Pod IRSA (K8s)
`trust-spark.json` (EMR) :
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "elasticmapreduce.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

`trust-irsa.json` (K8s IRSA) :
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/<OIDC_PROVIDER>" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "<OIDC_PROVIDER>:sub": "system:serviceaccount:miaradia:spark-sa"
        }
      }
    }
  ]
}
```

### 1.3 Attachement du rôle côté Spark
- **EMR** : rôle instance + `spark.executorEnv.AWS_ROLE_ARN` si besoin.  
- **K8s (IRSA)** : annoter le `ServiceAccount` avec l’ARN du rôle (cf. §3).

---

## 2) Kerberos — HDFS/YARN sécurisé

### 2.1 `krb5.conf` (exemple)
```conf
[libdefaults]
  default_realm = EXAMPLE.COM
  dns_lookup_kdc = false
  ticket_lifetime = 24h
  renew_lifetime = 7d
  rdns = false
  forwardable = true

[realms]
  EXAMPLE.COM = {
    kdc = kdc1.example.com
    admin_server = kadmin.example.com
  }

[domain_realm]
  .example.com = EXAMPLE.COM
  example.com = EXAMPLE.COM
```

### 2.2 `spark-defaults.conf` (Kerberos)
```properties
spark.yarn.principal=miaradia@EXAMPLE.COM
spark.yarn.keytab=/etc/security/keytabs/miaradia.keytab
spark.hadoop.security.authentication=kerberos
spark.hadoop.security.authorization=true
spark.hadoop.fs.defaultFS=hdfs://namenode:8020
```

### 2.3 `spark-submit` avec keytab
```bash
spark-submit   --principal miaradia@EXAMPLE.COM   --keytab /etc/security/keytabs/miaradia.keytab   --deploy-mode cluster   --class com.miaradia.spark.App   s3://miaradia-artifacts/jars/miaradia-spark-app-assembly.jar
```

> 🔁 **Renouvellement** : Spark/YARN gère la recopie du ticket aux executors. S’assurer de la **durée** du ticket pour les jobs longs.

---

## 3) RBAC Kubernetes — Spark Operator

### 3.1 ServiceAccount + Role + RoleBinding
`rbac-spark.yaml` :
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark-sa
  namespace: miaradia
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::<ACCOUNT_ID>:role/miaradia-spark-role   # IRSA
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: spark-role
  namespace: miaradia
rules:
- apiGroups: [""]
  resources: ["pods","pods/log","services","configmaps"]
  verbs: ["get","list","watch","create","delete","patch"]
- apiGroups: ["sparkoperator.k8s.io"]
  resources: ["sparkapplications","scheduledsparkapplications"]
  verbs: ["get","list","watch","create","delete","patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: spark-rb
  namespace: miaradia
subjects:
- kind: ServiceAccount
  name: spark-sa
  namespace: miaradia
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: spark-role
```

### 3.2 SparkApplication (extrait) — usage du SA
```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: miaradia-spark-app
  namespace: miaradia
spec:
  type: Scala
  mode: cluster
  image: <REGISTRY>/miaradia-spark-app:4.0.0
  mainClass: com.miaradia.spark.App
  mainApplicationFile: "local:///opt/spark/jars/miaradia-spark-app-assembly.jar"
  sparkVersion: "4.0.0"
  driver:
    serviceAccount: spark-sa
    cores: 1
    memory: "2g"
  executor:
    instances: 4
    cores: 2
    memory: "4g"
```

> 🔐 **Namespace isolation** : créer un **namespace** dédié par équipe/projet ; limiter les `verbs` au strict nécessaire ; activer **NetworkPolicy**.

---

## 4) Bonnes pratiques — AuthZ/AuthN

- **IAM least privilege** : restreindre S3 par **préfixe** (`arn:aws:s3:::bucket/path/*`).  
- **Séparer** rôles **driver** et **executor** si nécessaire (accès différents).  
- **Kerberos** : gérer **rotation** des keytabs, limiter accès aux fichiers keytabs.  
- **K8s RBAC** : éviter `ClusterRole` global, préférez `Role` par **namespace**.  
- **Audit** : activer les **event logs** Spark & l’audit K8s (API server).  
- **CI/CD** : pas de credentials en clair, utiliser OIDC/IRSA.

---

## 5) Commandes utiles

```bash
# IAM — attacher la policy au rôle
aws iam create-policy --policy-name miaradia-spark-exec --policy-document file://policy-spark-exec.json
aws iam attach-role-policy --role-name miaradia-spark-role --policy-arn arn:aws:iam::<ACCOUNT_ID>:policy/miaradia-spark-exec

# K8s — créer namespace + RBAC
kubectl create namespace miaradia
kubectl apply -f rbac-spark.yaml

# Spark Operator — déployer l'app
kubectl apply -f spark-application.yaml
```

---

**Fin — 03a IAM/RBAC.**  
Le fichier **03b** couvrira **Secrets, Encryption (TLS, SSE‑KMS), Spark ACL, Audit**.
