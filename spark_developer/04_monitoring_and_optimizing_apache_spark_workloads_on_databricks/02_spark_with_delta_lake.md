# Spark with Delta Lake

## Introduction to Tabular Storage

Evolution of open table formats for cloud data lakes

- Traditional data lake challenges
    - no transactional guarantees
    - no schema enforcement
    - performance issues with many small files
    - no built-in data quality controls
    - difficult metadata management
- evolution of storage formats:
    - basic data representation (csv, json) => efficient encoding (parquet, orc) => tabular transactional storage (delta
      lake, apache iceberg)

Early data lakes used raw file formats like json and csv on storage like HDFS or S3, with no transactional guarantees,
schema enforcement, or proper metadata management making data unreliable and hard to catalog.

Small files also hurt performance. Columnar formats like parquet and orc brought better compression and faster reads but
still lacked transaction support.

Modern formats like delta lake and apache iceberg now add ACID transactions, schema checks, and time travel features to
the data lake, making data reliable, consistent, and easy to manage.

## Introduction to Delta Lake

An open format bringing ACID transactions to the data lake.

What is Delta Lake?

- Open-source storage framework
- created by Databricks
- built on top of parquet
- brings reliability to data lakes
- native integration with apache spark
  Why Delta Lake?
- eliminates data inconsistency
- concurrent reads and writes (e.g. full refresh operations)

Delta Lake features:

- ACID transactions at scale
- schema enforcement
- schema evolution
- time travel (data versioning)
- unified batch and streaming
- scalable metadata handling
- enfoces data quality
- simplifies data pipelines
- reduces data lake management complexity

Delta Lake is an open-source storage format from Databricks that brings ACID transactions to data lakes.
Built on Parquet, it allows fine-grained data updates, maintains a history of all changes (making time travel and
rollback possible), and ensures data consistency and reliability even with failed jobs.
Delta Lake enforces schema, tracks schema changes, and supports both batch and streaming.
It lets one manage cloud-scala data lakes more easily by adding transactional reliability and structure, making
pipelines simpler and more robust.

## How Delta Lake works

Understanding the transaction log and versioning

- Each INSERT, UPDATE, DELETE operation
    - computes a "Delta" from the current version
        - as files added or removed
    - create new data files (if necessary)
    - commits a new "version" to the _delta_log
        - becomes the latest or current version
- Each SELECT operation
    - gets the manifest of data files from the version in the _delta_log (latest by default)
    - returns the data from the amalgam of files in the version

```text
tablex/
| Delta Lake Directory 
|____delta_log/
|   | Transaction Log 
|   |----- version0.json
|   |      includes data file A
|   |
|   |----- version1.json
|   |      includes data file A & B
|
|----data_file_A.parquet
|----data_file_B.parquet
| 
```

Delta Lake tracks changes through a _delta_log folder in each table's directory.
Every data update (insert, update, delete) creates a new log version, recording only the files added or removed.
The latest version lists the current files that make up the table, so Delta Lake always read the right data.
This Log acts like a manifest, enabling fast updates, time travel, and reliable data consistency without rewriting all
data.

## Delta Lake Operations

Advanced operations enabled by Delta Lake's transaction log

- Fine grained DELETE and UPDATE operations
- row-level modifications (including condition-based opartions)
- MERGE operations
    - true upserts (update+insert, can do delete as well)
    - support for complex merge conditions
- Schema evolution
    - including the CREZATE OR REPLACE TABLE operation
- Time Travel
    - Ability to select previous versions of data (view or RESTORE)

The Delta Lake transaction log allow you to make row-level updates and deletes without rewriting the full dataset.
You can use merge operations (upserts) to insert, update, or delete based on conditions.
Schema evolution is supported -- "create or replace table" updates the schema, and you can still access earlier schemas
through previous versions.
The Log also enables time travel, letting you view or restore data from a specific version or timestamp for easy
recovery or auditing.

## Apache Spark and Delta Lake

Integration between Databricks, Apache Spark and Delta Lake

- reads from delta lake tables

  ```python
  spark.read.format("delta").load("table_path")
  ```
- writes to delta lake tables
  ```python
  df.write.format("delta").save("table_path")
  ```
- Delta Lake is the default for Databricks
  ```python
  spark.read("table_path")
  df.write.mode("append").save("table_path")
  ```
- Delta specific spark SQL commands for inspection :
    - DESCRIBE HISTORY and DESCRIBE DETAIL
    - maintenance and performance commands OPTIMIZE and VACUUM (discussed later)

[For more information ](https://docs.databricks.com/aws/en/sql/language-manual#delta-statements) : https://docs.databricks.com/aws/en/sql/language-manual#delta-statements

## Delta Lake Performance and Maintenance

Optimizing and maintaining Delta tables for production workloads

- Table Optimizations :
  ```python
  # compact small files and index columns
  spark.sql("OPTIMIZE my_delta_table ZORDER BY (date)")
  ```
- Log Cleaning Operations :
  ```python
  # remove files no longer referenced
  spark.sql("VACUUM my_delta_table RETAIN 168 HOURS")
  ```

- Best practices:
    - Use table ("Hive") partitioning for large eventful datasets (e.g. transactions, events)
    - Monitor file sizes (watch for excessive small files)
    - Auto-optimize and auto-compact enabled by default on Databricks

Example to mention in demo:

- ALTER TABLE my_table SET TBLPROPERTIES ( 'delta.autoOptimize.optimizeWrite" = 'true', '
  delta.autoOptimize.autoCompact' = 'true') This config ensures that files are written and compacted efficiently without
  needing to run OPTIMIZE manually.

## Introduction to Apache Iceberg

An alternative open table format for cloud data lakes

- What is Apache Iceberg?
    - Open table format created by Neflix
    - Similar goals to Delta Lake
- Key Features:
    - ACID transactions
    - schema evolution
    - hidden partitioning and partition evolution
    - branch/tag support
- Spark integration
- Log Cleaning Operations :
  ```python
  # read iceberg table (addtl libraries required)
  spark.read.format("iceberg").load("table_path")
  # write to iceberg
  df.writeTo("my_table").append()
  ```

- Hidden partitioning :
    - unlike traditional partitioning where partition columns are visible in the data (like delta lake)
    - iceberg abstracts partition details from users
    - partition transforms (like dates into months) happen behind the scenes
    - users query natural columns, iceberg handles partition prunning autamatically
    - can change partition scheme without changing queries
- Partition evolution:
    - can change how a table is partitioned without rewriting data
    - example : change from daily to monthly partitoins seamlessly
    - old and new partition schemes can coexist
    - queryies automatically use the most efficient partition scheme
    - enables gradual migration of partitioning strategy
- Branch/Tag Support
    - similar to git branching concept
    - branches : named references to table states that can evolve
    - example: 'prod' and 'dev' branches of same table
    - can test changes in isolation
    - merge changes between branches
    - tags: named references to specific snapshots
    - example: tag a specific version as 'EOY2023'
    - immutable pointers to specific table states
    - useful for audit/compliance
