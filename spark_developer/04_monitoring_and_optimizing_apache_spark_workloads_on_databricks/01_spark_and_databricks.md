# Apache Spark and Databricks

## Databricks Background

A unified data and AI platform built by the creators of Apache Spark

- Founded in 2013 by the creators of Apache Spark, Databricks
    - is buit on open-source foundations: Apache Spark, Delta Lake and MLFlow
    - is available on all major cloud platforms (with a consistent exeprience)
    - pioneered the Lakehouse and Medallion architectures
- Databricks features:
    - enterprise-grade security and governance
    - collaborative notebooks and workspace environments
    - optimized performance through proprietary enhancements

## The Lakehouse

- A data warehouse is designed for structured data, optimized for BI and analytics, with strong schema enforcement and
  governance, but can be costly and inflexible
- A data lake, stores raw, diverse data types (structured, semi-structured, unstructured, offering low-cost storage and
  flexibility, but often lacks performance, and data management capabilities)
- The lakehouse architecture brings together the best of both worlds : A unified architecture combining the data
  warehouse and data lake
    - The srucuture of the Data Warehouse (and transactional capabilites) with the extensibility of the Data Lake
    - Scalability via separation of storage and compute
    - Support for all data types (structured, unstructured, ...)
    - Unified batch and stream processing support

## Medallion Architecture

A structured approach to data transformation and quality in the Lakehouse
Multi-layered data organization

- bronze tier : like for like source copy with history (the Delta Lake)
- silver tier : cleaned and conformed (but not aggregated) data
- gold tier : business-level features and aggregates

## Databricks Workspaces

Collaborative environments for data, analytics, and ML development

Isolated, collaborative environments for organizations, departments, teams, projects or analytics, including:

- compute resources (Spark clusters and serverless warehouses)
- directories and notebooks
- jobs (delta live table pipelines and workflow jobs)
- access to objects in Unity Catalog (tables, views, functions, models and more)
- simplified governance, security and access control

## Databricks Runtimes and Compute

Purpose-built environments optimized for different workloads

- What is Databricks Runtime (DBR)?
    - pre packaged and tested combination of Spark core and peripheral components
    - simplifies operations and boosts performance
    - runtime types include :
        - standard runtime: base Apache Spark with Databricks optimizations
        - machine learning runtime: pre-configured with popular ML libraries
        - photon enabled runtime: native vectorized engine for SQL performance
- Compute options :
    - All purpose clusters: interactive development and analysis
        - support for most underlying cloud provider instance types and sizes (incl GPUs)
    - Job Clusters: automated production workloads
    - SQL warehouses and serverless compute: no cluster management
- additional notes (mention verbally if time permits):
    - supports instance pools for faster startup and resource reuse
    - spot instances can be used to reduce costs on ephemeral workloads

## Unity Catalog

Unified data governance and security across your Databricks Lakehouse

- core functions :
    - single control plane for all data assets
    - fine-grained access control (tables, columns, rows)
    - automated data lineage tracking
    - centralized auditing and compliance
- why Unity Catalog?
    - manages data & AI assets across workspaces
    - simplifies security and governance
    - provides data discovery and sharing

A control plane is the centralized system responsible for managing and orchestrating configurations and policies.
In this context, unity catalog acts as a single control plane for :

- managing data permissions (table-, column-, row-level access)
- handling lineage, auditing, and compliance
- sharing data assets across multiple workspaces 


