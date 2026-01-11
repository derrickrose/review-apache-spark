# IBM Data architect on coursera

https://www.coursera.org/professional-certificates/ibm-data-architect#courses

# Data eng

https://www.coursera.org/professional-certificates/data-engineering#courses
https://www.coursera.org/professional-certificates/ibm-data-engineer
https://www.coursera.org/specializations/aws-data-engineer-certification#courses

# snowflake

https://www.coursera.org/professional-certificates/snowflake-data-engineering#courses

# Fundamentals

https://www.coursera.org/specializations/python-bash-sql-data-engineering-duke#courses

# Python developer

https://www.coursera.org/professional-certificates/microsoft-python-developer?recommenderId=related-roles#courses

# Path

Cloud Data Engineering - The 5-Level Path

(Each level: what you do → cloud services you learn)

## Basic foundations:

→ Programming: Python for ETL + automation, SQL for querying and modeling.
→ Data Systems: Relational (PostgreSQL/MySQL) + NoSQL basics (MongoDB, DynamoDB).
→ Processing Concepts: Batch vs streaming, Spark fundamentals, Kafka fundamentals.
→ Cloud & Storage Basics: S3 / ADLS / GCS, object storage concepts, VPC/network basics.
→ Orchestration & Automation: Airflow/Luigi, Git, Docker, CI/CD basics.
→ Data Modeling: Normalization, denormalization, OLTP vs OLAP, partitioning principles.

## Level 1 — Ingest & Land Raw Data

Bring data from applications, databases, logs, and events into the cloud in its raw form.
→ Batch ingestion:
AWS (DMS) • Azure (Data Factory) • GCP (Datastream) • OCI (GoldenGate)
→ Streaming ingestion:
AWS (Kinesis) • Azure (Event Hubs) • GCP (Pub/Sub) • OCI (GoldenGate Streams)
→ Raw storage layer:
AWS (S3) • Azure (ADLS Gen2) • GCP (Cloud Storage) • OCI (Object Storage)
→ Schema + metadata:
AWS (Glue Data Catalog) • Azure (Purview) • GCP (Data Catalog) • OCI (Data Catalog)
→ Access & security:
AWS (IAM) • Azure (RBAC) • GCP (IAM) • OCI (IAM + Vault)

## Level 2 — Clean, Transform & Structure Data

Make raw data usable through transformations, enrichment, and modeling.

→ Batch transformations (Spark/ETL):
AWS (Glue ETL / EMR Spark) • Azure (Databricks / Synapse Spark) • GCP (Dataflow / Dataproc) • OCI (Data Flow)
→ Event-driven enrichment:
AWS (Lambda) • Azure (Functions) • GCP (Cloud Functions) • OCI (Functions)
→ SQL on data lakes:
AWS (Athena) • Azure (Synapse Serverless SQL) • GCP (BigQuery external tables) • OCI (ADW external)
→ Analytical warehouse:
AWS (Redshift) • Azure (Synapse Dedicated SQL) • GCP (BigQuery) • OCI (Autonomous Data Warehouse)

## Level 3 — Build the Data Platform (Lakehouse Layer)

Design the scalable structure behind your pipelines — open table formats, orchestration, and storage patterns.

→ Lakehouse table formats:
AWS (Iceberg on S3) • Azure (Delta Lake on ADLS) • GCP (BigLake tables) • OCI (Parquet + ADW)
→ Pipeline orchestration:
AWS (Glue Workflows / Step Functions) • Azure (ADF / Synapse Pipelines) • GCP (Cloud Composer) • OCI (Data Integration
Flows)\
→ Optimization & layout:
AWS (Parquet + S3 partitioning) • Azure (Delta Z-order) • GCP (BQ partitioning + clustering) • OCI (Partitioned Parquet)
→ Lifecycle management:
AWS (S3 Lifecycle Rules) • Azure (ADLS Tiering) • GCP (Storage Classes) • OCI (Lifecycle Policies)

## Level 4 — Scale, Observe & Govern

Make pipelines enterprise-grade: more reliability, less cost, tighter security.

→ High-scale compute:
AWS (EMR) • Azure (Synapse Spark) • GCP (Dataflow Autoscaling) • OCI (Data Flow autoscaling)
→ Data quality & validation:
AWS (Deequ / Glue Data Quality) • Azure (Purview Quality) • GCP (Dataplex Quality) • OCI (Data Integration Checks)
→ Monitoring & observability:
AWS (CloudWatch) • Azure (Monitor + Log Analytics) • GCP (Cloud Monitoring) • OCI (OCI Monitoring)
→ Governance & permissions:
AWS (Lake Formation) • Azure (Purview) • GCP (VPC Service Controls + IAM) • OCI (IAM Policies + Vault)
→ Cost controls:
AWS (S3 tiers, Redshift RA3) • Azure (Reserved capacity, tiering) • GCP (BQ slot management) • OCI (Autoscaling +
lifecycle rules)

## Level 5 — Deliver Data Products & Pipeline

Expose high-quality data to ML teams, BI tools, and real-time applications.

→ Analytics datasets:
AWS (Redshift / Athena) • Azure (Synapse SQL) • GCP (BigQuery) • OCI (ADW)
→ BI dashboards:
AWS (QuickSight) • Azure (Power BI) • GCP (Looker) • OCI (Oracle Analytics Cloud)
→ ML pipelines / Feature stores:
AWS (SageMaker Feature Store) • Azure (Azure ML) • GCP (Vertex AI + BQ ML) • OCI (Oracle Data Science)
→ Low-latency serving:
AWS (Kinesis Analytics) • Azure (Stream Analytics) • GCP (Bigtable / Firestore) • OCI (GoldenGate Real-Time)

## Certification Guide ~ Multi-Cloud Data Engineer Path

AWS

→ AWS Cloud Practitioner (optional)
→ AWS Solutions Architect Associate
→ AWS Data Engineer Associate
→ AWS Machine Learning Specialty (optional)

Azure

→ AZ-900 Azure Fundamentals
→ Azure Data Engineer Associate
→ AZ-104 or AZ-305 (optional platform track)

GCP

→ Associate Cloud Engineer
→ Professional Data Engineer
→ Professional Cloud Architect (optional)

OCI

→ OCI Foundations Associate
→ OCI Data Science Professional
→ Autonomous Database Specialist (optional)

## Projects You Can Build:

DataCamp Projects – Beginner-friendly guided projects
Coursera Projects – Guided projects
Kaggle Datasets & Notebooks
Alex The Analyst (YouTube) – Project walkthroughs