# 04 — Lineage & Gouvernance : OpenLineage, Marquez, Apache Atlas, AWS Glue — FR

**Objectif :** Mettre en place un **lineage bout‑en‑bout** pour vos jobs **Apache Spark 4.0** : capture automatique (OpenLineage agent) + persistance (Marquez) + gouvernance (Atlas / Glue Data Catalog).

---

## 1) Concepts rapides

- **Lineage** = provenance & impact des datasets (inputs → outputs), avec détails d’exécution.
- **OpenLineage** = spec **ouverte** d’événements de lineage (jobs, runs, datasets).
- **Marquez** = service OSS de stockage/visualisation OpenLineage.
- **Atlas / Glue** = gouvernance & catalog : schémas, tags, classifications, policies.

---

## 2) OpenLineage pour Spark — Agent Java (recommandé)

L’agent **instrumente Spark** sans modifier le code et **envoie les événements** vers un **endpoint OpenLineage** (Marquez, proxy, etc.).

### 2.1 Dépendances & conf (Spark 4.0)

**spark-submit** (Driver & Executors) :

```bash
SPARK_VER=4.0.0
OL_VER=1.13.0

/opt/spark/bin/spark-submit   --conf spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener   --conf spark.openlineage.transport.type=http   --conf spark.openlineage.transport.url=http://marquez:5000   --conf spark.openlineage.namespace=miaradia-prod   --conf spark.openlineage.facets.spark_version=true   --conf spark.openlineage.facets.column_lineage.enabled=true   --packages io.openlineage:openlineage-spark_${SPARK_VER}:${OL_VER}   --class com.miaradia.spark.App local:///opt/spark/jars/app.jar
```

> Notes :  
> - `spark.extraListeners` ajoute le listener OpenLineage.  
> - `transport.url` pointe vers Marquez (ou proxy).  
> - Activation du **column lineage** si supporté.  
> - Utiliser la coordonnée `_spark_${SPARK_VER}`/scala binaire selon la distribution de l’agent (adapter si besoin).

### 2.2 Configuration avancée
```properties
spark.openlineage.parentJob.namespace=miaradia-prod
spark.openlineage.parentJob.name=nightly-etl
spark.openlineage.jobName=rides-etl
spark.openlineage.run.facets.git.ref=${GIT_SHA}
spark.openlineage.transport.timeout=10s
spark.openlineage.disable.transport.retry=false
```

---

## 3) Déploiement Marquez (Docker Compose)

`docker-compose.yml` (dev / test local) :

```yaml
version: '3.7'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: marquez
      POSTGRES_PASSWORD: marquez
      POSTGRES_DB: marquez
    ports: ["5432:5432"]
  api:
    image: marquezproject/marquez:latest
    depends_on: [db]
    environment:
      MARQUEZ_DB_HOST: db
      MARQUEZ_DB_PORT: 5432
      MARQUEZ_DB_NAME: marquez
      MARQUEZ_DB_USER: marquez
      MARQUEZ_DB_PASSWORD: marquez
    ports: ["5000:5000"]
  web:
    image: marquezproject/marquez-web:latest
    depends_on: [api]
    ports: ["3000:3000"]
```

Accès :  
- API OpenLineage : `http://localhost:5000`  
- UI Marquez : `http://localhost:3000`

---

## 4) Exemples d’événements générés (automatique)

L’agent Spark capture automatiquement les **datasets** (ex: `s3://bucket/path/*.parquet`), les **jobs** (class main), et les **runs** (applicationId), y compris :
- **Inputs** : sources `read` (Parquet/CSV/Delta/Iceberg/Kafka).  
- **Outputs** : sinks `write` (Parquet/Delta/Iceberg/Kafka).  
- **Facets** : schéma, statistics, error, column-lineage (si activé).

Aucun changement de code n’est nécessaire ; cependant vous pouvez **enrichir** via la config (cf. §2.2).

---

## 5) Atlas — Intégration Lineage & Catalog

### 5.1 Ingestion Spark vers Atlas
- Utiliser le **bridge Spark ↔ Atlas** (Atlas Hook) ou un **ingestor OpenLineage → Atlas**.
- Alternatives : exporter OpenLineage (Marquez API) puis **mapper** vers Atlas types (`hive_table`, `fs_path`, `process`).

### 5.2 Schémas & tags
- Créer des **types Atlas** personnalisés pour vos domaines (ex : `rides_table`).
- **Classifications** : `PII`, `GDPR`, `FINANCE`.  
- Propager les **classifications** aux colonnes (PII → `user_id`, `email`).

### 5.3 Requêtes lineage
- Atlas UI fournit : **Lineage Graph** (upstream/downstream), **Impact Analysis**.
- Exemples d’APIs : `/api/atlas/v2/lineage/<guid>`.

> En pratique : Marquez pour **tracking d’exécution runtime**, Atlas pour **gouvernance** et **politiques**.

---

## 6) AWS Glue Data Catalog (référentiel de schéma)

### 6.1 Spark ↔ Glue
```properties
spark.sql.catalogImplementation=hive
hive.metastore.client.factory.class=com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory
```
- Les **tables** (Delta/Iceberg/Parquet) sont enregistrées dans **Glue Catalog** (bases, tables, partitions).

### 6.2 Lineage dans Glue
- Glue capture du lineage **ETL Glue Jobs** nativement ; pour Spark, préférer **OpenLineage** + **Marquez** puis **export** vers un SI gouvernance (Atlas/Collibra).

---

## 7) Airflow / Orchestrateurs (bonus)

- **OpenLineage Airflow** : installer `openlineage-airflow` pour capter le lineage **DAG/Task**.  
- **Marquez** : déclarer `OPENLINEAGE_URL` & `OPENLINEAGE_NAMESPACE` dans la conf Airflow.  
- Avantage : **chaîne complète** Orchestrateur → Spark → Datasets dans un graphe unifié.

---

## 8) Exemples SQL & Delta/Iceberg — visibilité lineage

Même sans agent, vous pouvez **déclarer** explicitement inputs/outputs via métadonnées.

### 8.1 Spark SQL — tags lineage (simple)
```scala
spark.conf.set("spark.openlineage.jobName","rides-df-agg")
spark.sql("SET miaradia.lineage.inputs=s3a://miaradia-lake/bronze/rides_delta")
spark.sql("SET miaradia.lineage.outputs=s3a://miaradia-lake/silver/rides_agg")
spark.sql("""
  INSERT OVERWRITE DIRECTORY 's3a://miaradia-lake/silver/rides_agg'
  SELECT city, SUM(price) AS revenue FROM delta.`s3a://miaradia-lake/bronze/rides_delta` GROUP BY city
""")
```

### 8.2 Delta & Iceberg — catalog / history
- **Delta** : `DESCRIBE HISTORY delta.\`path\`` expose les versions (peut être ingéré dans un **facet custom**).  
- **Iceberg** : `CALL system.snapshots('db.table')` (voir 7B) ; utilisez le **catalog Glue** pour noms stables.

---

## 9) Bonnes pratiques Lineage

- **Standardiser** les noms de **jobs** (`spark.openlineage.jobName`) et **namespace** (env/projet).  
- **Activer** l’agent sur **TOUS** les jobs (prod & pre‑prod).  
- **Stabiliser** les **paths** S3/HDFS et les **catalogs** (Delta/Iceberg) pour des noms de datasets constants.  
- **Ségréguer** les environnements (namespace `dev`, `staging`, `prod`).  
- **Relier** l’orchestrateur (Airflow) pour la vision bout‑en‑bout.  
- **Conserver** Marquez DB (Postgres) avec **rétention** ≥ 90 jours et **sauvegardes** planifiées.

---

## 10) Commandes utiles

```bash
# Lancer Marquez local
docker compose up -d

# Vérifier l’endpoint OpenLineage
curl -s http://localhost:5000/api/v1/namespaces | jq

# Spark submit avec agent OpenLineage
/opt/spark/bin/spark-submit   --conf spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener   --conf spark.openlineage.transport.type=http   --conf spark.openlineage.transport.url=http://localhost:5000   --conf spark.openlineage.namespace=miaradia-dev   --packages io.openlineage:openlineage-spark_4.0.0:1.13.0   --class com.miaradia.spark.App local:///opt/spark/jars/app.jar
```

---

**Fin — 04 Lineage & Gouvernance (OpenLineage / Marquez / Atlas / Glue).**  
Prochain fichier : **05-Streaming-Kafka.md** (pipeline temps réel complet).

