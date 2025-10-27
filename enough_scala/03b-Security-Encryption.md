# 03b — Security, Secrets, Encryption, Spark ACL & Audit (Spark Prod) — FR

**Objectif :** Sécuriser vos **jobs Apache Spark 4.0** de bout en bout : **secrets**, **chiffrement (TLS/SSE‑KMS)**, **Spark ACL/UI**, **audit & logs JSON**.  
Compatible **EMR/YARN**, **Kubernetes**, **S3/HDFS**.

> Pour IAM/Kerberos/RBAC, voir `03a-IAM-RBAC.md`.

---

## 1) Gestion des Secrets (AWS / Kubernetes / Jenkins)

### 1.1 Kubernetes — `Secret` + environnement
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: spark-secrets
  namespace: miaradia
type: Opaque
data:
  DB_USER: bWlhcmFkaWE=          # echo -n 'miaradia' | base64
  DB_PASS: c3VwZXJfc2VjcmV0       # echo -n 'super_secret' | base64
---
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
    envSecretKeyRefs:
      - name: DB_USER
        valueFrom:
          secretKeyRef:
            name: spark-secrets
            key: DB_USER
      - name: DB_PASS
        valueFrom:
          secretKeyRef:
            name: spark-secrets
            key: DB_PASS
  executor:
    envSecretKeyRefs:
      - name: DB_USER
        valueFrom:
          secretKeyRef:
            name: spark-secrets
            key: DB_USER
      - name: DB_PASS
        valueFrom:
          secretKeyRef:
            name: spark-secrets
            key: DB_PASS
```

**Bonnes pratiques** :  
- Ne **jamais** commiter de secrets en clair.  
- Utiliser des **namespaces** dédiés, RBAC minimal, et rotation des secrets.  
- Préférer **IRSA/OIDC** pour AWS plutôt que des clés statiques.

### 1.2 Jenkins — Credentials → env
```groovy
withCredentials([usernamePassword(credentialsId: 'db-creds', usernameVariable: 'DB_USER', passwordVariable: 'DB_PASS')]) {
  sh 'echo "$DB_USER" | wc -c'
}
```

---

## 2) Encryption des données (in-transit & at-rest)

### 2.1 TLS côté Spark (UI & REST)
`spark-defaults.conf` :
```properties
spark.ui.enabled=true
spark.ssl.enabled=true
spark.ssl.keyStore=/opt/certs/keystore.jks
spark.ssl.keyStorePassword=${keystore_pass}
spark.ssl.protocol=TLSv1.2
spark.authenticate=true
spark.authenticate.enableSaslEncryption=true
```

### 2.2 TLS Kafka / JDBC (exemples)
```properties
# Kafka TLS/SASL
kafka.security.protocol=SASL_SSL
kafka.sasl.mechanism=SCRAM-SHA-512
kafka.ssl.truststore.location=/opt/certs/truststore.jks
kafka.sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required   username="${KAFKA_USER}" password="${KAFKA_PASS}";
```
```properties
# JDBC SSL
spark.datasource.jdbc.sslmode=require
spark.datasource.jdbc.trustStore=/opt/certs/truststore.jks
```

### 2.3 S3 — SSE‑S3 vs **SSE‑KMS** (recommandé)
```properties
# HADOOP CORE-SITE
fs.s3a.server-side-encryption-algorithm=SSE-KMS
fs.s3a.server-side-encryption.key=arn:aws:kms:eu-west-1:123456789012:key/abcd-efgh-....
```
**IAM** (cf. 03a) : ajouter `kms:Encrypt`, `kms:Decrypt`, `kms:GenerateDataKey` sur la clé KMS.

### 2.4 HDFS — Encryption Zones (si on‑prem/Hadoop)
- Créer une **EZ (Encryption Zone)** pour les dossiers sensibles.  
- Chiffrer au niveau **HDFS Transparent Encryption** (KMS Hadoop).

---

## 3) Spark ACL & UI (restriction d’accès)

`spark-defaults.conf` :
```properties
spark.ui.enabled=true
spark.acls.enable=true
spark.ui.view.acls=admin_user,alice,bob
spark.ui.view.acls.groups=data-admins
spark.modify.acls=admin_user
spark.admin.acls=admin_user
spark.history.ui.acls.enable=true
spark.history.ui.admin.acls=admin_user
```

**Idée** : limiter **qui** peut voir la **Spark UI** (jobs, DAG, logs) et qui peut **modifier** l’appli.  
Sur K8s, restreindre l’accès via **Ingress** + **Auth** (OIDC/SSO).

---

## 4) Audit & Logs JSON sécurisés

### 4.1 Event Log Spark (obligatoire prod)
`spark-submit` :
```bash
spark-submit   --conf spark.eventLog.enabled=true   --conf spark.eventLog.dir=s3a://miaradia-logs/spark-events   ...
```

### 4.2 Logback JSON (MDC enrichi)
`logback.xml` :
```xml
<configuration>
  <appender name="JSON" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>/var/log/spark/app.json</file>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <fileNamePattern>/var/log/spark/app.%d{yyyy-MM-dd}.json</fileNamePattern>
      <maxHistory>30</maxHistory>
    </rollingPolicy>
    <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
      <providers>
        <timestamp/>
        <pattern><pattern>
          {"level":"%level","logger":"%logger","message":"%msg",
           "mdc":%mdc,"thread":"%thread","appId":"%X{appId}","user":"%X{user}",
           "stageId":"%X{stageId}","taskId":"%X{taskId}","traceId":"%X{traceId}","clientIp":"%X{clientIp}"}
        </pattern></pattern>
      </providers>
    </encoder>
  </appender>
  <root level="INFO"><appender-ref ref="JSON"/></root>
</configuration>
```

### 4.3 Enrichir MDC via Listener
```scala
import org.apache.spark.scheduler._
import org.slf4j.MDC

spark.sparkContext.addSparkListener(new SparkListener {
  override def onJobStart(jobStart: SparkListenerJobStart): Unit = {
    MDC.put("appId", spark.sparkContext.applicationId)
    MDC.put("user", sys.props.getOrElse("user.name", "unknown"))
  }
  override def onStageSubmitted(s: SparkListenerStageSubmitted): Unit = {
    MDC.put("stageId", s.stageInfo.stageId.toString)
  }
})
```

### 4.4 Audit SQL (QueryExecutionListener)
```scala
spark.listenerManager.register(new org.apache.spark.sql.util.QueryExecutionListener {
  override def onSuccess(funcName: String, qe: org.apache.spark.sql.execution.QueryExecution, durationNs: Long): Unit = {
    val q = qe.simpleString
    println("{\"event\":\"sql\",\"duration_ms\":" + (durationNs/1e6).toString + ",\"query\":\"" + q.take(500) + "\"}")
  }
  override def onFailure(funcName: String, qe: org.apache.spark.sql.execution.QueryExecution, exception: Exception): Unit = {}
})
```

**Rétention & centralisation** : exporter vers **S3**/**CloudWatch**/**ELK** ; conserver **≥ 90 jours** (compliance).

---

## 5) Bonnes pratiques sécurité (checklist)

- **Chiffrement** : activer **TLS** (UI/REST), **SSE‑KMS** (S3), encryption zones HDFS.  
- **Secrets** : stockés en **K8s Secrets / Jenkins Credentials** ; rotation & scopes minimaux.  
- **ACL Spark** : restreindre UI et modifications (`spark.acls.enable=true`).  
- **Réseau** : limiter les ingress via **NetworkPolicy** (K8s) ou Security Groups (EMR).  
- **Audit** : **event logs** ON + logs JSON, MDC enrichi, rétention 90j+.  
- **CI/CD** : pas de clés statiques ; préférer **OIDC/IRSA**.  
- **KMS** : définir policies précises `kms:Encrypt/Decrypt/GenerateDataKey`.

---

## 6) Commandes utiles

```bash
# K8s — créer secret
kubectl -n miaradia create secret generic spark-secrets   --from-literal=DB_USER=miaradia --from-literal=DB_PASS=super_secret

# S3 — vérifier la clé KMS
aws kms describe-key --key-id alias/miaradia-sse-kms

# Spark UI SSL — vérifier port
curl -vk https://driver-pod:4040
```

---

**Fin — 03b Security & Encryption.**  
Prochain fichier : **04-Lineage-Atlas-OpenLineage.md** (lineage bout‑en‑bout).
