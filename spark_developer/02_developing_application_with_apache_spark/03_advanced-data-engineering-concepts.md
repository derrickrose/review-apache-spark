# Advanced Data Engineering Concepts

## Beyond the Basics: Complete Reference Guide

This guide covers advanced data engineering concepts that build on top of fundamentals like partitioning, bucketing, SCD patterns, and file-based vs database tables.

---

## Table of Contents

1. [File Formats Deep Dive](#file-formats-deep-dive)
2. [Advanced Partitioning Strategies](#advanced-partitioning-strategies)
3. [Data Compaction & File Sizing](#data-compaction--file-sizing)
4. [Schema Evolution](#schema-evolution)
5. [Data Skipping & Pruning](#data-skipping--pruning)
6. [Data Indexing Strategies](#data-indexing-strategies)
7. [Compression Techniques](#compression-techniques)
8. [Data Deduplication](#data-deduplication)
9. [Change Data Capture (CDC)](#change-data-capture-cdc)
10. [Data Quality & Validation](#data-quality--validation)
11. [Data Lineage & Metadata](#data-lineage--metadata)
12. [Data Cataloging](#data-cataloging)
13. [Performance Tuning](#performance-tuning)
14. [Caching Strategies](#caching-strategies)
15. [Data Governance & Security](#data-governance--security)
16. [Streaming Deep Dive](#streaming-deep-dive)
17. [Z-Ordering](#z-ordering)
18. [Cost Optimization](#cost-optimization)
19. [Essential Tools](#essential-tools)
20. [Learning Path](#learning-path)

---

## File Formats Deep Dive

### Overview of File Formats

| Format | Type | Best For | Compression | Schema Evolution |
|--------|------|----------|-------------|------------------|
| **Parquet** | Columnar | Analytics (OLAP) | Excellent | Good |
| **ORC** | Columnar | Hive/Presto workloads | Excellent | Good |
| **Avro** | Row-based | Streaming, Kafka | Good | Excellent |
| **JSON** | Text | APIs, debugging | Poor | Excellent |
| **CSV** | Text | Simple data exchange | Poor | None |

---

### Parquet (Columnar Storage)

```python
# Write Parquet
df.write \
    .format("parquet") \
    .option("compression", "snappy") \
    .save("s3://bucket/data")

# Read Parquet with column pruning
df = spark.read.parquet("s3://bucket/data") \
    .select("id", "name", "amount")  # Only reads these columns!

# Parquet structure:
# Row Group 1 (128MB)
#   Column Chunk: id [1, 2, 3, ..., 100000]
#   Column Chunk: name ["Alice", "Bob", ...]
#   Column Chunk: amount [100.50, 200.75, ...]
# Row Group 2 (128MB)
#   ...

# Benefits:
# ✅ Column pruning (read only needed columns)
# ✅ Predicate pushdown (skip row groups)
# ✅ Excellent compression
# ✅ Industry standard

# Use when:
# - Analytics workloads
# - Wide tables (many columns)
# - Need to read subsets of columns
```

---

### ORC (Optimized Row Columnar)

```python
# Write ORC
df.write \
    .format("orc") \
    .option("compression", "zlib") \
    .save("s3://bucket/data")

# ORC features:
# - Similar to Parquet (columnar)
# - Better for Hive ecosystem
# - Slightly better compression than Parquet
# - Built-in indexes (row group, bloom filters)

# Use when:
# - Hive/Presto heavy environment
# - Need built-in indexes
# - Maximum compression important
```

---

### Avro (Row-Based)

```python
# Write Avro
df.write \
    .format("avro") \
    .save("s3://bucket/data")

# Avro structure:
# - Schema stored in file header
# - Row-oriented (entire row together)
# - Compact binary format

# Schema example:
{
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id", "type": "long"},
        {"name": "name", "type": "string"},
        {"name": "email", "type": ["null", "string"], "default": null}
    ]
}

# Benefits:
# ✅ Schema evolution (add/remove fields easily)
# ✅ Self-describing (schema in file)
# ✅ Compact binary format
# ✅ Standard in streaming (Kafka)

# Use when:
# - Streaming applications
# - Kafka messages
# - Schema changes frequently
# - Need to read entire rows
```

---

### JSON (Text-Based)

```python
# Write JSON
df.write \
    .format("json") \
    .save("s3://bucket/data")

# JSON example:
{"id": 1, "name": "Alice", "age": 30}
{"id": 2, "name": "Bob", "age": 25}

# Benefits:
# ✅ Human-readable
# ✅ Flexible schema
# ✅ Easy to debug
# ✅ Universal format

# Drawbacks:
# ❌ Large file size
# ❌ Slow to parse
# ❌ No compression benefit
# ❌ Must read entire row

# Use when:
# - APIs
# - Configuration files
# - Debugging
# - Human inspection needed
```

---

### When to Use Which Format

```
Analytics/Data Warehouse:
└─ Parquet or ORC
   - Columnar storage
   - Excellent for aggregations
   - Read subset of columns

Streaming/Event-Driven:
└─ Avro
   - Schema evolution
   - Kafka standard
   - Compact binary

Data Exchange/APIs:
└─ JSON
   - Human-readable
   - Universal support
   - Easy integration

Archive/Cold Storage:
└─ Parquet with GZIP compression
   - Maximum compression
   - Infrequent access
   - Cost optimization
```

---

## Advanced Partitioning Strategies

### Multi-Level Partitioning

```python
# Hierarchical partitioning
df.write \
    .partitionBy("year", "month", "day", "hour") \
    .parquet("s3://bucket/events")

# Directory structure:
/events/
  year=2024/
    month=01/
      day=01/
        hour=00/
          data.parquet
        hour=01/
          data.parquet
      day=02/
        hour=00/
          ...

# Query with partition pruning:
spark.sql("""
    SELECT * FROM events
    WHERE year = 2024 
    AND month = 1 
    AND day = 1
    AND hour BETWEEN 0 AND 5
""")
# Only scans 6 directories (hours 0-5)
```

---

### The Small Files Problem

```python
# Problem: Hourly partitioning = 24 * 365 = 8,760 directories per year
# If each hour has 10 files = 87,600 files!
# Result: Slow queries (metadata overhead)

# Solution 1: Coarser partitioning
df.write \
    .partitionBy("year", "month", "day") \  # Daily, not hourly
    .parquet("s3://bucket/events")

# Solution 2: Dynamic partitioning with bucketing
df.write \
    .partitionBy("date") \
    .bucketBy(24, "hour") \  # 24 buckets representing hours
    .saveAsTable("events")

# Solution 3: Hidden partitioning (Iceberg)
spark.sql("""
    CREATE TABLE catalog.db.events (
        event_time TIMESTAMP,
        ...
    )
    USING iceberg
    PARTITIONED BY (hours(event_time))
""")
# Iceberg manages partitioning internally
# No partition columns in queries!
```

---

### Partition Evolution (Iceberg)

```python
# Start with daily partitioning
spark.sql("""
    CREATE TABLE catalog.db.events (...)
    USING iceberg
    PARTITIONED BY (days(event_time))
""")

# Later: Change to hourly (without rewriting data!)
spark.sql("""
    ALTER TABLE catalog.db.events
    SET PARTITION SPEC (hours(event_time))
""")

# Old data: Still partitioned by days
# New data: Partitioned by hours
# Queries work on both!

# This is IMPOSSIBLE with traditional Spark partitioning
# Would require rewriting all data
```

---

### Partition Transforms (Iceberg)

```python
# Date/Time transforms
PARTITIONED BY (
    years(timestamp_col),   # Partition by year
    months(timestamp_col),  # Partition by month
    days(timestamp_col),    # Partition by day
    hours(timestamp_col)    # Partition by hour
)

# Bucketing transform
PARTITIONED BY (
    bucket(N, column)  # Hash-based bucketing
)

# Truncate transform (for strings)
PARTITIONED BY (
    truncate(length, string_col)  # First N characters
)

# Identity transform (exact value)
PARTITIONED BY (
    identity(column)  # Partition by exact value
)

# Example: Multi-level with transforms
spark.sql("""
    CREATE TABLE catalog.db.events (
        event_time TIMESTAMP,
        user_id BIGINT,
        region STRING,
        ...
    )
    USING iceberg
    PARTITIONED BY (
        days(event_time),       -- Daily partitions
        bucket(16, user_id),    -- 16 buckets per day
        truncate(2, region)     -- First 2 chars of region
    )
""")
```

---

## Data Compaction & File Sizing

### The Small Files Problem

```
Problem:
/data/
  file-0001.parquet (100KB)  ← Too small!
  file-0002.parquet (200KB)
  file-0003.parquet (150KB)
  ... 10,000 files!

Issues:
- Slow metadata operations (listing files)
- Query overhead (opening many files)
- Scheduler overhead (too many tasks)
- Memory pressure (file handles)
```

---

### Optimal File Sizes

```
File Size Guidelines:

Too Small (< 1MB):
❌ Metadata overhead dominates
❌ Too many files to list
❌ Inefficient I/O

Sweet Spot (128MB - 1GB):
✅ Good parallelism
✅ Efficient I/O
✅ Reasonable metadata size
✅ Fits in memory buffers

Too Large (> 1GB):
❌ Less parallelism
❌ Memory pressure
❌ Slow to read entire file
❌ Hard to cache

Recommendations:
- OLTP/Streaming: 128MB - 256MB
- OLAP/Analytics: 512MB - 1GB
- Archive: 1GB+ (compression more important)
```

---

### Compaction Strategies

#### Iceberg Compaction

```python
# Identify small files
spark.sql("""
    SELECT 
        file_path, 
        file_size_in_bytes
    FROM catalog.db.table.files
    WHERE file_size_in_bytes < 1048576  -- < 1MB
    ORDER BY file_size_in_bytes
""")

# Compact small files
spark.sql("""
    CALL catalog.system.rewrite_data_files(
        table => 'db.events',
        options => map(
            'target-file-size-bytes', '536870912',  -- 512MB target
            'min-file-size-bytes', '1048576',       -- Rewrite files < 1MB
            'max-file-size-bytes', '1073741824'     -- Don't rewrite files > 1GB
        )
    )
""")

# What happens:
# 1. Reads many small files
# 2. Combines into larger files
# 3. Writes new files (512MB each)
# 4. Atomic metadata update
# 5. Old files marked for deletion
```

---

#### Delta Lake Compaction

```python
from delta.tables import DeltaTable

# Optimize (compact files)
deltaTable = DeltaTable.forPath(spark, "/delta/events")

deltaTable.optimize().executeCompaction()

# With Z-ordering
deltaTable.optimize() \
    .executeZOrderBy("customer_id", "event_date")

# Vacuum (delete old files)
deltaTable.vacuum(retentionHours=168)  # Keep 7 days of history
```

---

#### Spark Coalesce/Repartition

```python
# Coalesce (reduce partitions, no shuffle)
df.coalesce(10).write.parquet("output")

# Use when:
# - Want fewer, larger files
# - Acceptable to have uneven partition sizes
# - Want to avoid shuffle

# Repartition (hash-based, with shuffle)
df.repartition(100, "customer_id").write.parquet("output")

# Use when:
# - Want even partition sizes
# - Preparing for downstream processing
# - Can afford shuffle cost

# Example: Write optimal-sized files
data_size_mb = df.count() * avg_row_size_bytes / (1024 * 1024)
target_file_size_mb = 512
num_files = int(data_size_mb / target_file_size_mb)

df.repartition(num_files).write.parquet("output")
# Result: ~512MB files
```

---

## Schema Evolution

### Types of Schema Changes

#### 1. Add Column (Safe)

```python
# Iceberg
spark.sql("""
    ALTER TABLE catalog.db.users 
    ADD COLUMN phone STRING
""")

# Delta Lake
spark.sql("""
    ALTER TABLE delta.`/path/to/users` 
    ADD COLUMN phone STRING
""")

# Result:
# Old data: phone = null
# New data: phone = actual value
# Queries work seamlessly
```

---

#### 2. Rename Column (Iceberg Only)

```python
# Iceberg tracks field IDs, not names
spark.sql("""
    ALTER TABLE catalog.db.users 
    RENAME COLUMN first_name TO given_name
""")

# Old queries still work if using field ID
# New queries use new name
# Physical data unchanged!

# Delta Lake: Not supported (would break compatibility)
# Workaround: Add new column, drop old
```

---

#### 3. Drop Column (Lazy Deletion)

```python
# Drop column
spark.sql("""
    ALTER TABLE catalog.db.users 
    DROP COLUMN obsolete_field
""")

# What happens:
# - Metadata updated (column no longer visible)
# - Physical data still in files (not deleted)
# - Future compaction can remove it
# - Queries can't access it anymore

# Benefit: Fast (metadata-only operation)
# Drawback: Data still takes up space until compaction
```

---

#### 4. Change Data Type

```python
# Safe type changes (widening)
spark.sql("""
    ALTER TABLE catalog.db.users 
    ALTER COLUMN age TYPE BIGINT  -- was INT
""")

# Safe conversions:
# ✅ INT → BIGINT
# ✅ FLOAT → DOUBLE
# ✅ DATE → TIMESTAMP

# Unsafe conversions (data loss):
# ❌ BIGINT → INT (overflow risk)
# ❌ DOUBLE → FLOAT (precision loss)
# ❌ STRING → INT (parsing errors)

# For unsafe: Read, cast, rewrite
df = spark.table("catalog.db.users")
df_converted = df.withColumn("age", col("age").cast("int"))
df_converted.writeTo("catalog.db.users_v2").create()
```

---

#### 5. Nested Schema Changes

```python
# Schema with nested struct
spark.sql("""
    CREATE TABLE catalog.db.users (
        id BIGINT,
        name STRING,
        address STRUCT<
            street: STRING,
            city: STRING,
            state: STRING
        >
    )
""")

# Add field to nested struct
spark.sql("""
    ALTER TABLE catalog.db.users 
    ADD COLUMN address.zip_code STRING
""")

# Result schema:
# address STRUCT<
#     street: STRING,
#     city: STRING,
#     state: STRING,
#     zip_code: STRING  ← New field
# >
```

---

### Schema Evolution Best Practices

```python
# 1. Always specify schemas (don't rely on inference)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

schema = StructType([
    StructField("id", IntegerType(), False),
    StructField("name", StringType(), False),
    StructField("email", StringType(), True)
])

df = spark.read.schema(schema).json("data.json")

# 2. Use schema merge when needed
df.write \
    .option("mergeSchema", "true") \
    .mode("append") \
    .parquet("output")

# 3. Version your schemas
# schema_v1.json
# schema_v2.json (with new fields)
# schema_v3.json (field renamed)

# 4. Test schema changes before production
# Use development environment
# Verify backward compatibility
# Check query performance

# 5. Document schema changes
# Keep changelog
# Notify downstream consumers
```

---

## Data Skipping & Pruning

### Partition Pruning

```python
# Query with partition filter
spark.sql("""
    SELECT * FROM events
    WHERE event_date = '2024-01-15'
""")

# Spark skips all partitions except 2024-01-15
# If 365 partitions (daily for 1 year):
# Scans: 1 partition
# Skips: 364 partitions
# Speedup: 365x!
```

---

### File Pruning (Statistics)

```python
# Parquet/Iceberg stores min/max per file
file-001.parquet:
  customer_id: min=1, max=1000
  order_date: min='2024-01-01', max='2024-01-15'

# Query:
SELECT * FROM orders WHERE customer_id > 5000

# Spark checks file statistics:
# file-001: max=1000 < 5000 → Skip! ❌
# file-002: max=10000 > 5000 → Read ✅
# file-003: max=3000 < 5000 → Skip! ❌

# Only reads files that MIGHT contain matching data
```

---

### Bloom Filters (Advanced)

```python
# Probabilistic data structure for set membership
# "Is value X in this file?"

# Delta Lake Bloom Filter
spark.sql("""
    CREATE BLOOMFILTER INDEX ON delta.`/path/to/table` 
    FOR COLUMNS (email)
    OPTIONS (
        fpp = 0.01,          -- False positive probability (1%)
        numItems = 10000000  -- Expected number of items
    )
""")

# Query:
WHERE email = 'user@example.com'

# Bloom filter check:
# file-001: Bloom filter says "Maybe" → Read
# file-002: Bloom filter says "Definitely not" → Skip!
# file-003: Bloom filter says "Definitely not" → Skip!
# ...
# file-999: Bloom filter says "Definitely not" → Skip!

# Skips 998 out of 1000 files!

# Use cases:
# ✅ High-cardinality columns (email, UUID, phone)
# ✅ Point lookups (WHERE col = 'value')
# ✅ Can tolerate occasional false positives

# Don't use for:
# ❌ Range queries (WHERE col > 100)
# ❌ Low-cardinality columns (status, category)
# ❌ Columns used in aggregations
```

---

### Z-Order Clustering

```python
# (Covered in detail in Z-Ordering section)

# Multi-dimensional data layout
df.writeTo("catalog.db.orders") \
    .option("write.distribution-mode", "range") \
    .sortBy("customer_id", "order_date", "product_id") \
    .create()

# Enables file pruning on multiple columns simultaneously
```

---

## Data Indexing Strategies

### Column Statistics (Min/Max)

```python
# Automatically maintained by Parquet/Iceberg
# Per-column, per-file basis

# File metadata:
{
    "columns": [
        {
            "name": "customer_id",
            "min": 1,
            "max": 1000,
            "null_count": 0,
            "distinct_count": 1000
        },
        {
            "name": "amount",
            "min": 10.50,
            "max": 9999.99,
            "null_count": 5,
            "distinct_count": 950
        }
    ]
}

# Query optimizer uses these for pruning:
WHERE customer_id > 5000
# Skips files where max < 5000

WHERE amount BETWEEN 100 AND 500
# Only reads files where ranges overlap
```

---

### Bitmap Indexes

```python
# For low-cardinality columns
# Example: status column (pending, approved, cancelled)

# Conceptual structure:
# Row | status
# ----|----------
#  1  | pending
#  2  | approved
#  3  | pending
#  4  | cancelled
#  5  | pending

# Bitmap indexes:
# pending:   10101 (rows 1, 3, 5)
# approved:  01000 (row 2)
# cancelled: 00010 (row 4)

# Query: WHERE status = 'pending' OR status = 'cancelled'
# Result:    10111 (OR operation, very fast!)

# Not natively supported in Spark
# Available in traditional databases (Oracle, PostgreSQL)
```

---

### Secondary Indexes (Limited Support)

```python
# Traditional databases have secondary indexes
# Spark/Iceberg: Limited support, mainly via partitioning/Z-ordering

# Workaround: Manually create lookup tables
# Primary table:
users_df = spark.table("users")  # 100M users

# Secondary index table (email → user_id mapping):
email_index = users_df.select("email", "user_id") \
    .distinct() \
    .write \
    .bucketBy(100, "email") \
    .saveAsTable("users_email_index")

# Lookup by email (fast):
email_to_find = "user@example.com"
user_ids = spark.table("users_email_index") \
    .filter(col("email") == email_to_find) \
    .select("user_id")

# Join with main table:
result = user_ids.join(users_df, "user_id")  # Bucketed join!
```

---

## Compression Techniques

### Compression Algorithm Comparison

| Algorithm | Compression Ratio | Compression Speed | Decompression Speed | CPU Usage |
|-----------|-------------------|-------------------|---------------------|-----------|
| **Snappy** | 2-3x | ⚡⚡⚡ Very Fast | ⚡⚡⚡ Very Fast | Low |
| **LZ4** | 2-3x | ⚡⚡⚡ Very Fast | ⚡⚡⚡ Very Fast | Low |
| **ZSTD** | 3-5x | ⚡⚡ Fast | ⚡⚡ Fast | Medium |
| **GZIP** | 4-6x | ⚡ Slow | ⚡⚡ Moderate | High |
| **Bzip2** | 5-7x | 🐌 Very Slow | 🐌 Slow | Very High |

---

### Snappy (Default for Parquet)

```python
df.write \
    .option("compression", "snappy") \
    .parquet("output")

# Characteristics:
# ✅ Fast compression/decompression
# ✅ Low CPU usage
# ✅ Good for hot data (frequently accessed)
# ⚠️ Moderate compression ratio

# Use when:
# - Performance > storage cost
# - Interactive queries
# - Frequently accessed data
```

---

### GZIP (Maximum Compression)

```python
df.write \
    .option("compression", "gzip") \
    .parquet("output")

# Characteristics:
# ✅ Highest compression ratio
# ✅ Good for cold storage
# ❌ Slow compression
# ❌ Higher CPU usage

# Use when:
# - Storage cost > query performance
# - Archive/cold storage
# - Infrequently accessed data
# - Long-term retention
```

---

### ZSTD (Balanced)

```python
df.write \
    .option("compression", "zstd") \
    .parquet("output")

# Characteristics:
# ✅ Good compression ratio (better than Snappy)
# ✅ Reasonable speed (faster than GZIP)
# ✅ Tunable compression levels
# ⚠️ Newer format (compatibility)

# Use when:
# - Want balance of speed and compression
# - Modern data lakes
# - All engines support ZSTD
```

---

### LZ4 (Fastest)

```python
df.write \
    .option("compression", "lz4") \
    .parquet("output")

# Characteristics:
# ✅ Extremely fast decompression
# ✅ Very low CPU usage
# ⚠️ Lower compression than Snappy

# Use when:
# - Maximum read performance critical
# - CPU is bottleneck
# - Read-heavy workloads
```

---

### Compression Best Practices

```python
# 1. Hot data (frequently queried)
hot_data.write \
    .option("compression", "snappy") \  # Fast
    .parquet("hot/")

# 2. Warm data (occasionally queried)
warm_data.write \
    .option("compression", "zstd") \  # Balanced
    .parquet("warm/")

# 3. Cold data (rarely queried, archive)
cold_data.write \
    .option("compression", "gzip") \  # Maximum compression
    .parquet("cold/")

# 4. Different codecs for different columns (ORC)
df.write \
    .format("orc") \
    .option("orc.compress", "ZLIB") \  # Default
    .option("orc.bloom.filter.columns", "email") \
    .save("output")

# 5. Test compression on your data
# - Compression ratio varies by data type
# - Text compresses better than random numbers
# - Sorted data compresses better than random
```

---

## Data Deduplication

### Method 1: dropDuplicates (In-Memory)

```python
# Remove duplicates based on all columns
df_deduped = df.dropDuplicates()

# Remove duplicates based on specific columns
df_deduped = df.dropDuplicates(["user_id", "event_date"])

# Keep first occurrence
df_deduped = df.dropDuplicates(["user_id"])

# Characteristics:
# ✅ Simple API
# ✅ Fast for small-medium data
# ❌ Full shuffle required
# ❌ Memory-intensive for large data
```

---

### Method 2: Window Functions (More Control)

```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, desc

# Keep latest record per user
window = Window \
    .partitionBy("user_id") \
    .orderBy(desc("timestamp"))

df_deduped = df \
    .withColumn("rn", row_number().over(window)) \
    .filter("rn = 1") \
    .drop("rn")

# Benefits:
# ✅ Control which record to keep (first, last, max, etc.)
# ✅ Can add dedup metadata
# ✅ Flexible conditions

# Keep record with highest score:
window = Window \
    .partitionBy("user_id") \
    .orderBy(desc("score"), desc("timestamp"))

df_deduped = df \
    .withColumn("rn", row_number().over(window)) \
    .filter("rn = 1") \
    .drop("rn")
```

---

### Method 3: MERGE (Upsert)

```python
# Iceberg/Delta: Atomic upsert operation
spark.sql("""
    MERGE INTO catalog.db.users t
    USING (
        SELECT 
            user_id, 
            name, 
            email,
            updated_at
        FROM updates
        QUALIFY row_number() OVER (
            PARTITION BY user_id 
            ORDER BY updated_at DESC
        ) = 1
    ) s
    ON t.user_id = s.user_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

# What happens:
# 1. Deduplicates source (QUALIFY)
# 2. Updates existing records
# 3. Inserts new records
# 4. Atomic operation (all or nothing)

# Benefits:
# ✅ ACID guarantees
# ✅ Deduplication + upsert in one operation
# ✅ Production-ready
```

---

### Method 4: Row-Level DELETE

```python
# Delete all but the latest record per user
spark.sql("""
    DELETE FROM catalog.db.events e1
    WHERE EXISTS (
        SELECT 1 
        FROM catalog.db.events e2
        WHERE e1.user_id = e2.user_id
        AND e1.event_timestamp < e2.event_timestamp
    )
""")

# Warning: Can be expensive on large tables
# Better: Use MERGE or window functions
```

---

### Deduplication Strategies

```python
# Strategy 1: Dedupe at read time (Ad-hoc)
df = spark.table("raw_events")
df_clean = df.dropDuplicates(["event_id"])
# Use for: One-time analysis

# Strategy 2: Dedupe at write time (ETL)
raw_df = spark.read.parquet("source/")
clean_df = raw_df.dropDuplicates(["event_id"])
clean_df.write.parquet("cleaned/")
# Use for: Creating clean datasets

# Strategy 3: Dedupe with MERGE (Incremental)
# Daily job:
spark.sql("""
    MERGE INTO catalog.db.events t
    USING daily_events s
    ON t.event_id = s.event_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")
# Use for: Production incremental loads

# Strategy 4: Primary key constraint (Prevention)
spark.sql("""
    CREATE TABLE catalog.db.users (
        user_id BIGINT PRIMARY KEY,  -- Iceberg 1.4+
        name STRING,
        email STRING
    )
""")
# Prevents duplicates at write time
```

---

## Change Data Capture (CDC)

### CDC Architecture

```
┌──────────────────────────────────────────────────────┐
│              Source Database (OLTP)                  │
│                 PostgreSQL/MySQL                     │
│                                                      │
│  Tables: users, orders, products                    │
└────────────────┬─────────────────────────────────────┘
                 │
                 │ Debezium/Maxwell captures changes
                 │ (INSERT, UPDATE, DELETE)
                 ▼
┌──────────────────────────────────────────────────────┐
│                 Kafka (CDC Log)                      │
│                                                      │
│  Topics: db.users, db.orders, db.products          │
│  Retention: 7 days                                  │
└────────────────┬─────────────────────────────────────┘
                 │
                 │ Spark Streaming consumes
                 ▼
┌──────────────────────────────────────────────────────┐
│            Spark Streaming Processing                │
│                                                      │
│  - Parse CDC events                                 │
│  - Apply transformations                            │
│  - Maintain state                                   │
└────────────────┬─────────────────────────────────────┘
                 │
                 │ Writes to data lake
                 ▼
┌──────────────────────────────────────────────────────┐
│              Iceberg Data Lake (OLAP)                │
│                                                      │
│  Tables: dim_users, fact_orders (analytics-ready)  │
└──────────────────────────────────────────────────────┘
```

---

### CDC Event Structure

```json
// INSERT event
{
    "before": null,
    "after": {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "created_at": "2024-01-15T10:30:00Z"
    },
    "op": "c",  // create
    "ts_ms": 1705318200000,
    "source": {
        "db": "production",
        "table": "users"
    }
}

// UPDATE event
{
    "before": {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com"
    },
    "after": {
        "id": 1,
        "name": "Alice",
        "email": "alice.smith@example.com"  // Changed
    },
    "op": "u",  // update
    "ts_ms": 1705318300000
}

// DELETE event
{
    "before": {
        "id": 1,
        "name": "Alice",
        "email": "alice.smith@example.com"
    },
    "after": null,
    "op": "d",  // delete
    "ts_ms": 1705318400000
}
```

---

### Processing CDC in Spark

```python
# Read CDC stream from Kafka
cdc_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "postgres.public.users") \
    .option("startingOffsets", "earliest") \
    .load()

# Parse JSON events
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import *

cdc_schema = StructType([
    StructField("before", StructType([
        StructField("id", LongType()),
        StructField("name", StringType()),
        StructField("email", StringType())
    ])),
    StructField("after", StructType([
        StructField("id", LongType()),
        StructField("name", StringType()),
        StructField("email", StringType())
    ])),
    StructField("op", StringType()),
    StructField("ts_ms", LongType())
])

parsed_stream = cdc_stream \
    .selectExpr("CAST(value AS STRING) as json") \
    .select(from_json("json", cdc_schema).alias("data")) \
    .select("data.*")

# Apply CDC changes to Iceberg table
def apply_cdc_batch(batch_df, batch_id):
    batch_df.createOrReplaceTempView("cdc_batch")
    
    # Apply INSERTs and UPDATEs
    spark.sql("""
        MERGE INTO catalog.db.users t
        USING (
            SELECT after.* 
            FROM cdc_batch 
            WHERE op IN ('c', 'u')  -- Create or Update
        ) s
        ON t.id = s.id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)
    
    # Apply DELETEs
    spark.sql("""
        DELETE FROM catalog.db.users
        WHERE id IN (
            SELECT before.id 
            FROM cdc_batch 
            WHERE op = 'd'
        )
    """)
    
    print(f"Batch {batch_id}: Processed CDC events")

# Start streaming
query = parsed_stream.writeStream \
    .foreachBatch(apply_cdc_batch) \
    .option("checkpointLocation", "/checkpoints/cdc-users") \
    .trigger(processingTime="1 minute") \
    .start()

query.awaitTermination()
```

---

### CDC Best Practices

```python
# 1. Handle out-of-order events
# Events might arrive out of order
# Use timestamp to determine latest version

spark.sql("""
    MERGE INTO catalog.db.users t
    USING (
        SELECT *
        FROM (
            SELECT 
                after.*,
                ts_ms,
                row_number() OVER (
                    PARTITION BY after.id 
                    ORDER BY ts_ms DESC
                ) as rn
            FROM cdc_batch
            WHERE op IN ('c', 'u')
        )
        WHERE rn = 1
    ) s
    ON t.id = s.id AND s.ts_ms > t.updated_at
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

# 2. Handle schema evolution
# Add new columns from source database
# Iceberg handles this gracefully

# 3. Monitor lag
# Track time between event creation and processing
from pyspark.sql.functions import current_timestamp, from_unixtime

parsed_stream \
    .withColumn("event_time", from_unixtime(col("ts_ms") / 1000)) \
    .withColumn("processing_time", current_timestamp()) \
    .withColumn("lag_seconds", 
        unix_timestamp("processing_time") - unix_timestamp("event_time"))

# 4. Idempotency
# Replay same events → same result
# MERGE is idempotent (safe to replay)

# 5. Checkpointing
# Store processing state
# Resume from last processed offset on failure
.option("checkpointLocation", "/checkpoints/cdc")
```

---

## Data Quality & Validation

### Schema Validation

```python
from pyspark.sql.types import *

# Define expected schema
expected_schema = StructType([
    StructField("id", IntegerType(), nullable=False),
    StructField("name", StringType(), nullable=False),
    StructField("email", StringType(), nullable=True),
    StructField("age", IntegerType(), nullable=True),
    StructField("created_at", TimestampType(), nullable=False)
])

# Read with schema enforcement
df = spark.read \
    .schema(expected_schema) \
    .parquet("input/")

# This will FAIL if:
# - Column missing
# - Wrong data type
# - Non-nullable column has nulls
```

---

### Data Validation Checks

```python
def validate_data(df):
    """Comprehensive data quality checks"""
    
    # 1. Null checks
    null_counts = df.select([
        sum(col(c).isNull().cast("int")).alias(c)
        for c in df.columns
    ]).collect()[0].asDict()
    
    required_columns = ["id", "name", "created_at"]
    for col_name in required_columns:
        null_count = null_counts[col_name]
        assert null_count == 0, f"Column {col_name} has {null_count} nulls"
    
    # 2. Value range checks
    invalid_ages = df.filter("age < 0 OR age > 150").count()
    assert invalid_ages == 0, f"Found {invalid_ages} invalid ages"
    
    # 3. Format checks
    invalid_emails = df.filter("email IS NOT NULL AND email NOT LIKE '%@%'").count()
    assert invalid_emails == 0, f"Found {invalid_emails} invalid emails"
    
    # 4. Uniqueness checks
    total = df.count()
    unique_ids = df.select("id").distinct().count()
    assert total == unique_ids, f"Duplicate IDs found: {total - unique_ids}"
    
    # 5. Referential integrity
    # Check if all customer_ids exist in customers table
    customers = spark.table("customers").select("id")
    orphan_orders = df.join(customers, df.customer_id == customers.id, "left_anti")
    orphan_count = orphan_orders.count()
    assert orphan_count == 0, f"Found {orphan_count} orphan orders"
    
    # 6. Business logic checks
    negative_amounts = df.filter("amount < 0").count()
    assert negative_amounts == 0, f"Found {negative_amounts} negative amounts"
    
    future_dates = df.filter(f"order_date > current_date()").count()
    assert future_dates == 0, f"Found {future_dates} future dates"
    
    print("✅ All data quality checks passed!")
    return df

# Use in pipeline
validated_df = validate_data(raw_df)
validated_df.write.parquet("output/")
```

---

### Great Expectations Integration

```python
# Great Expectations: Popular data quality framework

import great_expectations as ge

# Convert Spark DataFrame to GE DataFrame
df_ge = ge.from_pandas(df.toPandas())

# Define expectations
df_ge.expect_column_values_to_not_be_null("id")
df_ge.expect_column_values_to_be_unique("id")
df_ge.expect_column_values_to_be_between("age", 0, 150)
df_ge.expect_column_values_to_match_regex(
    "email", 
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
df_ge.expect_column_values_to_be_in_set(
    "status", 
    ["pending", "approved", "cancelled"]
)

# Validate
results = df_ge.validate()

# Check results
if results["success"]:
    print("✅ All expectations met!")
else:
    print("❌ Some expectations failed:")
    for result in results["results"]:
        if not result["success"]:
            print(f"  - {result['expectation_config']['expectation_type']}")
            print(f"    {result['result']}")
```

---

### Constraints (Delta Lake)

```python
# Add constraints to Delta table
spark.sql("""
    ALTER TABLE delta.`/path/to/users`
    ADD CONSTRAINT valid_email CHECK (email LIKE '%@%')
""")

spark.sql("""
    ALTER TABLE delta.`/path/to/users`
    ADD CONSTRAINT valid_age CHECK (age >= 0 AND age <= 150)
""")

# Future writes that violate constraints will FAIL
# Ensures data quality at write time

# Drop constraint
spark.sql("""
    ALTER TABLE delta.`/path/to/users`
    DROP CONSTRAINT valid_email
""")
```

---

### Data Quality Metrics

```python
# Track data quality over time
def calculate_dq_metrics(df):
    total_rows = df.count()
    
    metrics = {
        "timestamp": current_timestamp(),
        "total_rows": total_rows,
        "null_rate": df.filter("email IS NULL").count() / total_rows,
        "duplicate_rate": (total_rows - df.dropDuplicates(["id"]).count()) / total_rows,
        "completeness": df.filter("name IS NOT NULL AND email IS NOT NULL").count() / total_rows,
        "validity": df.filter("age >= 0 AND age <= 150").count() / total_rows
    }
    
    return metrics

# Store metrics
metrics = calculate_dq_metrics(df)
metrics_df = spark.createDataFrame([metrics])
metrics_df.write.mode("append").parquet("dq_metrics/")

# Query metrics history
spark.read.parquet("dq_metrics/") \
    .orderBy("timestamp") \
    .show()

# Alert if quality drops
if metrics["completeness"] < 0.95:
    send_alert("Data completeness dropped below 95%!")
```

---

## Data Lineage & Metadata

### What is Data Lineage?

```
Data lineage tracks the flow of data through your pipeline:

Source → Transform → Destination

Example:
PostgreSQL (users table)
    │
    ├─ ETL Job 1: Extract & Load
    ▼
Bronze Layer (raw_users)
    │
    ├─ ETL Job 2: Clean & Transform
    ▼
Silver Layer (cleaned_users)
    │
    ├─ ETL Job 3: Aggregate & Join
    ▼
Gold Layer (user_analytics)
    │
    ├─ BI Tool: Dashboard
    ▼
Executive Report
```

---

### Why Lineage Matters

```
Questions lineage answers:

1. Impact Analysis
   "If I change this table, what breaks downstream?"

2. Root Cause Analysis
   "This report has wrong data. Where did it come from?"

3. Compliance
   "Show me all uses of PII data"

4. Trust
   "Is this data fresh? Who owns it?"

5. Optimization
   "Which tables are never used? (Can we delete?)"
```

---

### OpenLineage (Standard)

```python
# OpenLineage: Open standard for data lineage

from openlineage.spark import SparkOpenLineageListener

# Configure Spark to send lineage events
spark = SparkSession.builder \
    .appName("ETL Job") \
    .config(
        "spark.extraListeners",
        "io.openlineage.spark.agent.OpenLineageSparkListener"
    ) \
    .config("spark.openlineage.transport.type", "http") \
    .config("spark.openlineage.transport.url", "http://lineage-server:5000") \
    .config("spark.openlineage.namespace", "production") \
    .getOrCreate()

# Every Spark operation now automatically sends lineage events!

# Read (INPUT event)
df = spark.read.parquet("s3://bucket/raw_users")
# Event sent: Read from dataset "s3://bucket/raw_users"

# Transform (no event, part of job)
cleaned = df.filter("age >= 0")

# Write (OUTPUT event)
cleaned.write.parquet("s3://bucket/cleaned_users")
# Event sent: Wrote to dataset "s3://bucket/cleaned_users"

# Lineage graph automatically built:
# raw_users → [ETL Job] → cleaned_users
```

---

### Lineage Event Example

```json
{
    "eventType": "COMPLETE",
    "eventTime": "2024-01-15T10:30:00Z",
    "run": {
        "runId": "job-123-run-456"
    },
    "job": {
        "namespace": "production",
        "name": "users-etl",
        "facets": {
            "sql": {
                "query": "SELECT * FROM raw_users WHERE age >= 0"
            }
        }
    },
    "inputs": [
        {
            "namespace": "s3://bucket",
            "name": "raw_users",
            "facets": {
                "schema": {
                    "fields": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "name", "type": "STRING"},
                        {"name": "age", "type": "INTEGER"}
                    ]
                },
                "dataSource": {
                    "name": "s3",
                    "uri": "s3://bucket/raw_users"
                }
            }
        }
    ],
    "outputs": [
        {
            "namespace": "s3://bucket",
            "name": "cleaned_users",
            "facets": {
                "schema": {
                    "fields": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "name", "type": "STRING"},
                        {"name": "age", "type": "INTEGER"}
                    ]
                },
                "stats": {
                    "rowCount": 1000000,
                    "size": 52428800
                }
            }
        }
    ]
}
```

---

### Lineage Tools

#### 1. Apache Atlas

```python
# Atlas: Metadata management and lineage

# Automatic lineage capture for:
# - Hive
# - Spark
# - Kafka
# - HDFS

# Features:
# - Search metadata
# - Visualize lineage
# - Tag sensitive data
# - Audit trail
```

---

#### 2. DataHub (LinkedIn)

```python
# DataHub: Modern data catalog with lineage

# Features:
# - Real-time lineage
# - Impact analysis
# - Data discovery
# - Ownership tracking
# - Documentation

# Integration:
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.emitter.rest_emitter import DatahubRestEmitter

emitter = DatahubRestEmitter("http://datahub-server:8080")

# Emit lineage
dataset_urn = make_dataset_urn("hive", "users.cleaned_users")
# ... emit events
```

---

#### 3. Marquez (OpenLineage)

```python
# Marquez: OpenLineage-compatible lineage server

# Automatic capture from:
# - Spark
# - Airflow
# - dbt
# - Great Expectations

# View lineage in UI:
# http://marquez-ui:3000
```

---

## Data Cataloging

### What is a Data Catalog?

```
A data catalog is a metadata repository that helps users:

1. Discover data
   "What datasets exist?"
   "Where is customer data?"

2. Understand data
   "What does this column mean?"
   "Who owns this table?"

3. Trust data
   "Is this data quality-checked?"
   "When was it last updated?"

4. Access data
   "Do I have permissions?"
   "How do I query this?"
```

---

### Hive Metastore (Basic Catalog)

```python
# Hive Metastore: Metadata store for Spark tables

# Create database
spark.sql("CREATE DATABASE IF NOT EXISTS ecommerce")

# Create table
spark.sql("""
    CREATE TABLE ecommerce.orders (
        order_id BIGINT,
        customer_id BIGINT,
        amount DECIMAL(10,2),
        order_date DATE
    )
    USING iceberg
    LOCATION 's3://bucket/ecommerce/orders'
""")

# List databases
spark.sql("SHOW DATABASES").show()

# List tables in database
spark.sql("SHOW TABLES IN ecommerce").show()

# Describe table
spark.sql("DESCRIBE EXTENDED ecommerce.orders").show(truncate=False)

# Show table properties
spark.sql("SHOW TBLPROPERTIES ecommerce.orders").show()

# Show partitions
spark.sql("SHOW PARTITIONS ecommerce.orders").show()
```

---

### AWS Glue Catalog

```python
# Glue Catalog: Managed Hive Metastore in AWS

# Configure Spark to use Glue Catalog
spark = SparkSession.builder \
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog") \
    .config("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
    .config("spark.sql.catalog.glue_catalog.warehouse", "s3://my-bucket/warehouse") \
    .getOrCreate()

# Use Glue Catalog
spark.sql("CREATE DATABASE glue_catalog.ecommerce")
spark.sql("USE glue_catalog.ecommerce")

# Benefits:
# ✅ Managed service (no server to maintain)
# ✅ Integrated with AWS services (Athena, EMR, Glue ETL)
# ✅ Cross-account access
# ✅ Automatic backups
```

---

### Unity Catalog (Databricks)

```python
# Unity Catalog: Enterprise data catalog with governance

# Three-level namespace: catalog.schema.table
spark.sql("CREATE CATALOG production")
spark.sql("CREATE SCHEMA production.ecommerce")
spark.sql("""
    CREATE TABLE production.ecommerce.orders (...)
    USING iceberg
""")

# Fine-grained access control
spark.sql("""
    GRANT SELECT ON TABLE production.ecommerce.orders 
    TO `data-scientists@company.com`
""")

spark.sql("""
    GRANT ALL PRIVILEGES ON SCHEMA production.ecommerce 
    TO `data-engineers@company.com`
""")

# Audit logs
spark.sql("""
    SELECT * FROM system.access.audit
    WHERE table_name = 'production.ecommerce.orders'
    AND event_date >= current_date() - 7
""")

# Data lineage (automatic)
# Captured from notebooks, jobs, queries

# Benefits:
# ✅ Centralized governance
# ✅ Fine-grained access control
# ✅ Audit trail
# ✅ Cross-cloud (AWS, Azure, GCP)
# ✅ Lineage tracking
```

---

### Catalog Best Practices

```python
# 1. Organize with hierarchy
# catalog/database/schema/table structure

# Good:
production.ecommerce.orders
production.ecommerce.customers
production.analytics.sales_summary

# Bad (flat structure):
orders
customers
sales_summary_v2_final

# 2. Document tables
spark.sql("""
    COMMENT ON TABLE production.ecommerce.orders 
    IS 'Production order transactions. Updated daily at 2 AM UTC.'
""")

# 3. Document columns
spark.sql("""
    ALTER TABLE production.ecommerce.orders
    ALTER COLUMN amount COMMENT 'Order total in USD'
""")

# 4. Set ownership
spark.sql("""
    ALTER TABLE production.ecommerce.orders
    SET TBLPROPERTIES (
        'owner' = 'data-engineering@company.com',
        'created_by' = 'john.doe@company.com',
        'business_owner' = 'sales-team@company.com'
    )
""")

# 5. Tag sensitive data
spark.sql("""
    ALTER TABLE production.ecommerce.customers
    SET TAGS ('pii' = 'true', 'gdpr' = 'true')
""")

# 6. Track data quality
spark.sql("""
    ALTER TABLE production.ecommerce.orders
    SET TBLPROPERTIES (
        'data_quality_score' = '0.98',
        'last_quality_check' = '2024-01-15'
    )
""")
```

---

## Performance Tuning

### Shuffle Optimization

```python
# Shuffle happens in many operations:

# 1. Joins
df1.join(df2, "key")  # Shuffle both sides

# 2. GroupBy + Aggregations
df.groupBy("customer_id").agg(sum("amount"))  # Shuffle

# 3. Window functions
from pyspark.sql.window import Window
window = Window.partitionBy("customer_id").orderBy("date")
df.withColumn("rank", rank().over(window))  # Shuffle

# 4. Distinct
df.select("customer_id").distinct()  # Shuffle

# 5. Repartition
df.repartition(100, "customer_id")  # Shuffle

# 6. SortBy
df.sort("customer_id", "date")  # Shuffle
```

---

### Shuffle Tuning

```python
# Key parameter: spark.sql.shuffle.partitions (default: 200)

# Problem: Default might be wrong
# - Too few partitions → Large tasks (OOM risk)
# - Too many partitions → Small tasks (overhead)

# Calculate optimal partitions:
data_size_gb = 100
target_partition_size_gb = 0.5  # 512MB
optimal_partitions = int(data_size_gb / target_partition_size_gb)
# = 200 partitions

spark.conf.set("spark.sql.shuffle.partitions", optimal_partitions)

# Guidelines:
# Small data (< 10GB): 50-100 partitions
# Medium data (10-100GB): 200-500 partitions
# Large data (> 100GB): 1000+ partitions

# Rule of thumb: 128MB - 1GB per partition
```

---

### Adaptive Query Execution (AQE)

```python
# AQE: Dynamic query optimization during execution (Spark 3.0+)

# Enable AQE
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Feature 1: Coalesce partitions
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionSize", "1MB")

# What it does:
# - Detects small partitions after shuffle
# - Combines them into larger partitions
# - Reduces task overhead

# Feature 2: Dynamic join strategy
spark.conf.set("spark.sql.adaptive.autoBroadcastJoinThreshold", "10MB")

# What it does:
# - Starts with sort-merge join
# - If one side is small (< 10MB), switches to broadcast join
# - Mid-execution optimization!

# Feature 3: Skew join optimization
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# What it does:
# - Detects skewed partitions (5x larger than median)
# - Splits large partition into smaller ones
# - Distributes work evenly

# Example without AQE:
# Partition 0: 100MB (10 seconds)
# Partition 1: 100MB (10 seconds)
# Partition 2: 5GB (500 seconds) ← Straggler!
# Partition 3: 100MB (10 seconds)
# Total: 500 seconds (waiting for partition 2)

# With AQE:
# Partition 2 split into 50 × 100MB partitions
# All finish in ~10 seconds
# Total: 10 seconds (50x faster!)
```

---

### Broadcast Join Optimization

```python
# Force broadcast for known small tables
from pyspark.sql.functions import broadcast

# Small lookup table
lookup = spark.read.parquet("lookup")  # 1MB

# Large fact table
facts = spark.read.parquet("facts")  # 100GB

# Without broadcast (sort-merge join, slow)
result = facts.join(lookup, "key")  # Shuffles 100GB!

# With broadcast (fast!)
result = facts.join(broadcast(lookup), "key")  # Only broadcasts 1MB

# Configure automatic broadcast threshold
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10MB")

# Spark will automatically broadcast tables < 10MB
```

---

### Predicate Pushdown

```python
# Predicate pushdown: Filter data at source (before reading)

# Without pushdown (reads all data, then filters)
df = spark.read.parquet("large_table")  # Reads 100GB
filtered = df.filter("date = '2024-01-01'")  # Filters in memory

# With pushdown (filters at read time)
df = spark.read \
    .option("mergeSchema", "false") \
    .parquet("large_table") \
    .filter("date = '2024-01-01'")  # Only reads 1 day!

# Parquet automatically pushes down:
# ✅ Column filters (SELECT specific columns)
# ✅ Row filters (WHERE conditions)
# ✅ Uses Parquet statistics (min/max per row group)

# Example:
# File has 10 row groups
# Row group 1: date min='2024-01-01', max='2024-01-05'
# Row group 2: date min='2024-01-06', max='2024-01-10'
# ...
# Filter: date = '2024-01-01'
# Only reads row group 1! (90% data skipped)
```

---

### Partitioning for Performance

```python
# Read optimization
spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")  # 128MB

# What it does:
# - Splits large files into smaller partitions
# - Better parallelism

# Write optimization
df.repartition(100).write.parquet("output")

# vs

df.coalesce(10).write.parquet("output")

# repartition: Full shuffle, even distribution
# coalesce: No shuffle (or minimal), may have uneven sizes

# Use repartition when:
# - Need even partition sizes
# - Downstream processing benefits from distribution

# Use coalesce when:
# - Want to reduce partitions
# - Don't need perfect distribution
# - Want to avoid shuffle cost
```

---

## Caching Strategies

### Storage Levels

```python
from pyspark import StorageLevel

# 1. MEMORY_ONLY (default for .cache())
df.persist(StorageLevel.MEMORY_ONLY)
# ✅ Fastest access
# ❌ Lost if executor dies
# ❌ OOM if doesn't fit

# 2. MEMORY_AND_DISK (default for .persist())
df.persist(StorageLevel.MEMORY_AND_DISK)
# ✅ Spills to disk if needed
# ✅ More reliable
# ⚠️ Slower if reading from disk

# 3. DISK_ONLY
df.persist(StorageLevel.DISK_ONLY)
# ✅ No memory pressure
# ❌ Slower than memory
# ✅ Good for very large datasets

# 4. MEMORY_ONLY_SER (serialized)
df.persist(StorageLevel.MEMORY_ONLY_SER)
# ✅ Less memory usage (serialized)
# ❌ CPU cost to deserialize
# ✅ Good when memory-constrained

# 5. OFF_HEAP
df.persist(StorageLevel.OFF_HEAP)
# ✅ No GC pressure
# ✅ More stable memory
# ⚠️ Requires configuration
```

---

### When to Cache

```python
# ✅ Cache when:

# 1. DataFrame used multiple times
expensive_df = spark.read.parquet("large_table") \
    .join(lookup, "key") \
    .filter("amount > 1000") \
    .cache()  # Cache here!

result1 = expensive_df.groupBy("customer").sum("amount")
result2 = expensive_df.groupBy("product").count()
result3 = expensive_df.filter("date > '2024-01-01'")

# 2. Iterative algorithms (ML)
for i in range(10):
    # Without cache: Recomputes from source each iteration!
    df = df.withColumn("iter", lit(i))

df.cache()  # Cache before loop!
for i in range(10):
    df = df.withColumn("iter", lit(i))

# 3. Checkpoint in long chains
df.checkpoint()  # Breaks lineage, prevents stack overflow

# ❌ Don't cache when:

# 1. DataFrame used only once
df = spark.read.parquet("table")
df.filter("id > 100").write.parquet("output")  # No cache needed

# 2. Very large data that won't fit in memory
# 3. Data already optimized (Iceberg, Delta with statistics)
```

---

### Broadcast Variables

```python
from pyspark.sql.functions import broadcast

# Problem: Small lookup table joined with large fact table
lookup = spark.read.parquet("lookup")  # 10MB
facts = spark.read.parquet("facts")  # 100GB

# Without broadcast: Sort-merge join (shuffles 100GB)
result = facts.join(lookup, "key")

# With broadcast: Broadcast join (no shuffle)
result = facts.join(broadcast(lookup), "key")

# Broadcast automatically caches lookup on all executors
# No shuffle needed!

# Manual broadcast variable (for RDDs/UDFs)
lookup_dict = {"key1": "value1", "key2": "value2"}
broadcast_lookup = spark.sparkContext.broadcast(lookup_dict)

def lookup_udf(key):
    return broadcast_lookup.value.get(key)

# All executors have access to broadcast_lookup
```

---

### Unpersist

```python
# Always unpersist when done to free memory

# Cache
expensive_df.cache()

# Use
result1 = expensive_df.groupBy("customer").sum()
result2 = expensive_df.groupBy("product").count()

# Unpersist
expensive_df.unpersist()

# Memory freed for other operations

# Check what's cached
spark.catalog.listCachedTables()

# Clear all cache
spark.catalog.clearCache()
```

---

## Data Governance & Security

### Row-Level Security

```python
# Control which rows users can see

# Unity Catalog (Databricks)
spark.sql("""
    CREATE ROW ACCESS POLICY regional_access
    ON catalog.db.orders
    FOR ROWS WHERE region = current_user_region()
""")

spark.sql("""
    GRANT SELECT ON TABLE catalog.db.orders 
    TO `sales-team@company.com`
    USING POLICY regional_access
""")

# User in US-West region:
# SELECT * FROM catalog.db.orders
# Only sees rows where region = 'US-West'

# Implementation pattern:
# 1. Store user metadata (region, role, etc.)
# 2. Create row filter function
# 3. Apply filter automatically based on current user
```

---

### Column-Level Security

```python
# Hide or mask columns based on user permissions

# Unity Catalog column masking
spark.sql("""
    ALTER TABLE catalog.db.customers
    ALTER COLUMN ssn SET MASK mask_show_last_4(ssn)
""")

# Regular user sees: XXX-XX-1234
# Admin sees: 123-45-1234

# Available masks:
# - mask_show_first_4
# - mask_show_last_4
# - mask_hash (SHA-256)
# - mask (replace with XXXXX)
# - Custom functions

# Redaction (complete hiding)
spark.sql("""
    REVOKE SELECT (ssn, credit_card) 
    ON TABLE catalog.db.customers 
    FROM `data-analysts@company.com`
""")
# These columns appear as NULL to data analysts
```

---

### Encryption

```python
# 1. Encryption at rest (S3/ADLS/GCS)
# Configured at storage layer
# - S3: SSE-S3, SSE-KMS, SSE-C
# - ADLS: Storage Service Encryption
# - GCS: Google-managed keys

# 2. Encryption in transit
spark.conf.set("spark.ssl.enabled", "true")
spark.conf.set("spark.ssl.keyStore", "/path/to/keystore")
spark.conf.set("spark.ssl.keyStorePassword", "password")
spark.conf.set("spark.ssl.trustStore", "/path/to/truststore")

# 3. Column-level encryption (application-level)
from pyspark.sql.functions import expr
from cryptography.fernet import Fernet

# Encrypt
encryption_key = Fernet.generate_key()
df_encrypted = df.withColumn(
    "encrypted_ssn",
    expr(f"aes_encrypt(ssn, '{encryption_key.decode()}')")
)

# Decrypt (only by authorized users)
df_decrypted = df_encrypted.withColumn(
    "decrypted_ssn",
    expr(f"aes_decrypt(encrypted_ssn, '{encryption_key.decode()}')")
)
```

---

### Audit Logging

```python
# Track all data access

# Unity Catalog audit logs
spark.sql("""
    SELECT 
        event_time,
        user_identity,
        action_name,
        request_params.table_name,
        response.status_code
    FROM system.access.audit
    WHERE action_name IN ('READ', 'WRITE', 'DELETE')
    AND event_date >= current_date() - 30
    ORDER BY event_time DESC
""")

# CloudTrail (AWS)
# Logs all API calls to S3, Glue, EMR
# Enable for compliance/security

# Custom audit trail
def log_access(user, table, action):
    audit_record = {
        "timestamp": current_timestamp(),
        "user": user,
        "table": table,
        "action": action,
        "ip": request.remote_addr
    }
    spark.createDataFrame([audit_record]).write \
        .mode("append") \
        .parquet("audit_logs/")

# Log every table access
@log_table_access
def read_table(table_name):
    return spark.table(table_name)
```

---

## Streaming Deep Dive

### Structured Streaming Architecture

```
┌──────────────────────┐
│     Data Source      │ (Kafka, files, socket)
│  (Unbounded stream)  │
└──────────┬───────────┘
           │
           │ Micro-batches (default) or Continuous
           ▼
┌──────────────────────┐
│  Spark Streaming     │
│  Processing Engine   │
│                      │
│  - Stateful ops      │
│  - Windowing         │
│  - Deduplication     │
└──────────┬───────────┘
           │
           │ Write
           ▼
┌──────────────────────┐
│       Sink           │ (Iceberg, Delta, Kafka, console)
│  (Output destination)│
└──────────────────────┘
           │
           │ Checkpoint (fault tolerance)
           ▼
┌──────────────────────┐
│   Checkpoint         │
│   Location           │
│  (Processing state)  │
└──────────────────────┘
```

---

### Basic Streaming Example

```python
# Read from Kafka
kafka_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "events") \
    .option("startingOffsets", "earliest") \
    .load()

# Parse JSON
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import *

schema = StructType([
    StructField("event_id", StringType()),
    StructField("user_id", IntegerType()),
    StructField("event_type", StringType()),
    StructField("timestamp", TimestampType())
])

parsed = kafka_stream \
    .selectExpr("CAST(value AS STRING) as json") \
    .select(from_json("json", schema).alias("data")) \
    .select("data.*")

# Transform
transformed = parsed \
    .filter("event_type IN ('click', 'purchase')") \
    .withColumn("hour", hour("timestamp"))

# Write to Iceberg
query = transformed.writeStream \
    .format("iceberg") \
    .outputMode("append") \
    .option("checkpointLocation", "/checkpoints/events") \
    .trigger(processingTime="1 minute") \
    .toTable("catalog.db.events")

query.awaitTermination()
```

---

### Windowed Aggregations

```python
from pyspark.sql.functions import window, count, sum

# Tumbling window (non-overlapping)
windowed = parsed \
    .groupBy(
        window("timestamp", "10 minutes"),  # 10-minute windows
        "user_id"
    ) \
    .agg(
        count("*").alias("event_count"),
        sum("amount").alias("total_amount")
    )

# Sliding window (overlapping)
windowed = parsed \
    .groupBy(
        window("timestamp", "10 minutes", "5 minutes"),  # 10-min window, 5-min slide
        "user_id"
    ) \
    .agg(count("*").alias("event_count"))

# Session window (event-based)
windowed = parsed \
    .groupBy(
        session_window("timestamp", "30 minutes"),  # Gap of 30 minutes ends session
        "user_id"
    ) \
    .agg(count("*").alias("events_in_session"))

# Write aggregated data
windowed.writeStream \
    .format("iceberg") \
    .outputMode("append") \  # or "update" or "complete"
    .option("checkpointLocation", "/checkpoints/windowed") \
    .trigger(processingTime="1 minute") \
    .toTable("catalog.db.event_summary")
```

---

### Output Modes

```python
# 1. Append (default)
.outputMode("append")
# - Only new rows added
# - Use for: Streaming inserts, event logs
# - Cannot use with aggregations on non-windowed data

# 2. Update
.outputMode("update")
# - Only changed rows updated
# - Use for: Aggregations, updates
# - Supported by Iceberg/Delta

# 3. Complete
.outputMode("complete")
# - Entire result rewritten
# - Use for: Small aggregations, debugging
# - Not scalable for large data
```

---

### Checkpointing

```python
# Checkpoint: Stores processing state for fault tolerance

query = df.writeStream \
    .option("checkpointLocation", "s3://bucket/checkpoints/job1") \
    .start()

# What's stored in checkpoint:
# - Offset information (where we are in the stream)
# - State store (for stateful operations)
# - Metadata (query configuration)

# Benefits:
# ✅ Exactly-once processing
# ✅ Resume from failure
# ✅ Stateful operations work across restarts

# Important: Never delete checkpoint while query is running!
# Starting new query with fresh checkpoint = reprocessing all data
```

---

### Deduplication in Streaming

```python
# Remove duplicates based on key
deduplicated = parsed \
    .dropDuplicates(["event_id"])

# With watermark (limit state size)
from pyspark.sql.functions import expr

deduplicated = parsed \
    .withWatermark("timestamp", "1 hour") \
    .dropDuplicates(["event_id", "timestamp"])

# Keeps state for 1 hour
# After watermark passes, old state is dropped
# Prevents unbounded state growth
```

---

### Stateful Operations

```python
# Stateful: Maintains state across batches

# 1. Aggregations
parsed.groupBy("user_id").count()
# State: Running count per user

# 2. Deduplication
parsed.dropDuplicates(["event_id"])
# State: Set of seen event_ids

# 3. Joins (stream-stream or stream-static)
stream1.join(stream2, "key")
# State: Buffered events from both streams

# 4. FlatMapGroupsWithState (custom stateful logic)
def update_state(key, events, state):
    # Custom stateful processing
    # Return updated state and output
    pass

parsed.groupByKey(lambda x: x.user_id) \
    .flatMapGroupsWithState(...)
```

---

## Z-Ordering

(Already covered in detail earlier)

### Quick Reference

```python
# Z-ordering: Multi-dimensional data layout
# Optimizes for queries filtering on multiple columns

# Iceberg
spark.sql("""
    CALL catalog.system.rewrite_data_files(
        table => 'db.orders',
        strategy => 'sort',
        sort_order => 'zorder(customer_id, order_date, product_id)'
    )
""")

# Delta Lake
from delta.tables import DeltaTable
deltaTable = DeltaTable.forPath(spark, "/delta/orders")
deltaTable.optimize().executeZOrderBy("customer_id", "order_date", "product_id")

# Benefits:
# ✅ File pruning on multiple columns
# ✅ Better than sorting on single column
# ✅ Queries with any of these columns benefit

# Use when:
# ✅ Multiple filter columns in queries
# ✅ Query patterns vary
# ✅ Large tables (TB+)
```

---

## Cost Optimization

### 1. Right-Size Clusters

```python
# Monitor resource utilization
# - CPU usage: Should be 60-80%
# - Memory usage: Should be 60-80%
# - Network I/O: Should be moderate

# Too large: Wasting money on idle resources
# Too small: Jobs run slow, may fail

# Start small, scale up as needed
```

---

### 2. Use Spot/Preemptible Instances

```python
# AWS Spot Instances: 60-90% cheaper
# GCP Preemptible VMs: 60-90% cheaper
# Azure Spot VMs: Similar savings

# Tradeoff: Can be terminated anytime
# Solution: Use for non-critical, retryable workloads

# EMR example (AWS):
# - Core nodes: On-demand (persistent)
# - Task nodes: Spot (can lose, no data loss)

# Mix:
# - 20% on-demand (stability)
# - 80% spot (cost savings)
```

---

### 3. Autoscaling

```python
# Dynamic allocation: Add/remove executors based on workload

spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", 2)
spark.conf.set("spark.dynamicAllocation.maxExecutors", 100)
spark.conf.set("spark.dynamicAllocation.initialExecutors", 10)

# Benefits:
# ✅ Start small (save cost)
# ✅ Scale up when needed (performance)
# ✅ Scale down when idle (save cost)
```

---

### 4. Storage Tiering

```python
# Hot data (recent, frequently accessed)
# - S3 Standard / Azure Hot / GCS Standard
# - Fast access, higher cost

# Warm data (older, occasionally accessed)
# - S3 Intelligent-Tiering / Azure Cool
# - Moderate cost

# Cold data (archive, rarely accessed)
# - S3 Glacier / Azure Archive / GCS Nearline
# - Low cost, retrieval latency

# Lifecycle policies (S3 example):
{
    "Rules": [
        {
            "Id": "MoveToIA",
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}

# Automatic cost optimization!
```

---

### 5. Query Optimization

```python
# Partition pruning (covered)
WHERE date = '2024-01-01'  # Scans 1 day, not entire table

# Column pruning
SELECT id, name  # Only reads 2 columns, not all 50

# Predicate pushdown
# Filters applied at source (Parquet, database)

# File format & compression
# Parquet + Snappy: Good balance
# Parquet + GZIP: Maximum compression (cold storage)

# These optimizations reduce:
# - Data scanned (less I/O)
# - Processing time (faster)
# - Cost (pay for what you use)
```

---

### 6. Monitoring & Alerts

```python
# Track cost per job
# Set budgets and alerts

# AWS Cost Explorer: Track EMR/S3 costs
# Datadog/CloudWatch: Track job metrics
# Custom dashboards: Cost per pipeline/team

# Alert on anomalies:
# - Job taking 10x longer than usual
# - Sudden spike in S3 storage
# - Cluster running 24/7 (should be ephemeral)

# Example metric:
cost_per_row_processed = total_cost / rows_processed

# Track over time:
# - Optimization working? Cost per row decreasing?
# - New data? Cost per row stable despite volume growth?
```

---

### 7. Cluster Scheduling

```python
# Run non-urgent jobs during off-peak hours

# Peak hours (9 AM - 5 PM):
# - Interactive queries
# - Critical dashboards
# - High priority on-demand instances

# Off-peak hours (6 PM - 8 AM):
# - Batch ETL jobs
# - Data backfills
# - Model training
# - More spot instances available (cheaper)

# Example Airflow schedule:
dag = DAG(
    "nightly_etl",
    schedule_interval="0 2 * * *",  # 2 AM daily
    ...
)

# Benefits:
# ✅ Cheaper spot pricing off-peak
# ✅ Less contention for resources
# ✅ Critical jobs get priority during business hours
```

---

## Essential Tools

### Must Know

1. **Apache Spark**
   - Core processing engine
   - Master it!

2. **Table Formats**
   - Iceberg or Delta Lake
   - ACID, time travel, schema evolution

3. **File Formats**
   - Parquet (analytics)
   - Avro (streaming)

4. **Kafka**
   - Stream processing
   - Event streaming

5. **Airflow**
   - Workflow orchestration
   - DAG-based scheduling

6. **dbt**
   - SQL-based transformations
   - Data modeling
   - Testing & documentation

7. **Docker**
   - Containerization
   - Portable environments

8. **Kubernetes**
   - Container orchestration
   - Spark on K8s

9. **Terraform**
   - Infrastructure as code
   - Reproducible environments

10. **Git**
    - Version control
    - Collaboration

---

### Cloud Platforms

#### AWS
- **S3**: Object storage
- **Glue**: Managed metastore, ETL
- **EMR**: Managed Spark clusters
- **Athena**: Serverless SQL queries
- **Redshift**: Data warehouse
- **Kinesis**: Streaming

#### Azure
- **ADLS**: Data lake storage
- **Synapse**: Analytics platform
- **Databricks**: Managed Spark
- **Event Hubs**: Streaming

#### GCP
- **GCS**: Object storage
- **BigQuery**: Data warehouse
- **Dataproc**: Managed Spark
- **Pub/Sub**: Messaging

---

### Monitoring & Observability

- **Spark UI**: Job monitoring (built-in)
- **Grafana**: Dashboards
- **Prometheus**: Metrics collection
- **DataDog**: APM, metrics, logs
- **CloudWatch**: AWS monitoring
- **Application Insights**: Azure monitoring
- **Stackdriver**: GCP monitoring

---

## Learning Path

```
┌────────────────────────────────────────────────────────┐
│              FOUNDATION (You're here! ✅)              │
├────────────────────────────────────────────────────────┤
│  - SQL                                                 │
│  - Python                                              │
│  - Data structures                                     │
│  - Spark basics                                        │
│  - Partitioning, bucketing                            │
│  - SCD patterns                                        │
│  - File formats                                        │
└────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                   INTERMEDIATE                          │
├────────────────────────────────────────────────────────┤
│  - Iceberg/Delta Lake                                  │
│  - Performance tuning                                  │
│  - Schema design                                       │
│  - ETL patterns                                        │
│  - Data quality                                        │
│  - Z-ordering                                          │
└────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                    ADVANCED                             │
├────────────────────────────────────────────────────────┤
│  - Streaming (Kafka, Structured Streaming)            │
│  - Data governance                                     │
│  - Cost optimization                                   │
│  - Architecture design                                 │
│  - CDC implementation                                  │
│  - Multi-cloud strategies                              │
└────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│                     EXPERT                              │
├────────────────────────────────────────────────────────┤
│  - Custom query optimizations                          │
│  - Distributed systems internals                       │
│  - Query optimizer internals                           │
│  - Building data platforms                             │
│  - Team leadership                                     │
└────────────────────────────────────────────────────────┘
```

---

## What to Focus On Next

### 1. Hands-On Practice (Most Important!)

Build a real end-to-end project:

```
Project: E-commerce Analytics Platform

1. Data Sources
   - PostgreSQL (operational DB)
   - REST API (external enrichment)
   - CSV files (legacy data)

2. Bronze Layer (Raw)
   - Extract from sources
   - Load to S3 in raw format
   - Partition by ingestion_date

3. Silver Layer (Cleaned)
   - CDC from PostgreSQL
   - Data quality checks
   - Deduplication
   - Schema validation
   - Partition by date, bucket by customer_id

4. Gold Layer (Curated)
   - Business aggregations
   - Dimension tables (SCD Type 2)
   - Fact tables (transaction grain)
   - Z-ordered for query performance

5. Orchestration
   - Airflow DAGs
   - Monitoring & alerts
   - Data quality checks

6. Query Layer
   - SQL analytics
   - BI tool integration
   - Performance optimization

This project covers everything we discussed!
```

---

### 2. Learn Streaming

- Kafka fundamentals
- Spark Structured Streaming
- Real-time CDC
- Event-driven architectures

---

### 3. Master One Cloud Platform

Pick AWS, Azure, or GCP:
- Learn data services deeply
- Understand pricing models
- Get certified (optional but valuable)
- Build cloud-native pipelines

---

### 4. Workflow Orchestration

- Airflow or Dagster
- Schedule and monitor jobs
- Dependency management
- Retry logic
- Alerting

---

### 5. SQL Optimization

- Query execution plans
- Index strategies
- Join algorithms
- Statistics and histograms

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│                  DATA ORGANIZATION                       │
├─────────────────────────────────────────────────────────┤
│  Partitioning → Coarse (directories)                    │
│  Bucketing → Medium (hash distribution)                 │
│  Z-Ordering → Fine (multi-column layout)                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    FILE FORMATS                          │
├─────────────────────────────────────────────────────────┤
│  Analytics → Parquet/ORC                                │
│  Streaming → Avro                                       │
│  Data Lake with ACID → Iceberg/Delta                    │
│  APIs → JSON                                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    PERFORMANCE                           │
├─────────────────────────────────────────────────────────┤
│  Caching → Reuse expensive computations                 │
│  Broadcasting → Small table joins                       │
│  AQE → Dynamic optimization                             │
│  Shuffle tuning → Partition count                       │
│  Predicate pushdown → Filter at source                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   DATA QUALITY                           │
├─────────────────────────────────────────────────────────┤
│  Schema validation → Enforce types                      │
│  Constraints → Business rules                           │
│  Great Expectations → Comprehensive checks              │
│  Monitoring → Track health metrics                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 COST OPTIMIZATION                        │
├─────────────────────────────────────────────────────────┤
│  Right-size clusters                                    │
│  Spot instances (60-90% savings)                        │
│  Partition pruning (scan less data)                     │
│  Compression (reduce storage)                           │
│  Storage tiering (hot/warm/cold)                        │
│  Autoscaling (pay for what you use)                     │
└─────────────────────────────────────────────────────────┘
```

---

## Conclusion

You've now covered:

✅ **File formats** - When to use Parquet, Avro, ORC, JSON
✅ **Advanced partitioning** - Multi-level, hidden partitioning, transforms
✅ **Compaction** - Small files problem, optimal sizing
✅ **Schema evolution** - Add/rename/drop columns safely
✅ **Data skipping** - Partition/file pruning, bloom filters, Z-ordering
✅ **Indexing** - Statistics, bitmap indexes
✅ **Compression** - Snappy, GZIP, ZSTD, LZ4
✅ **Deduplication** - Multiple strategies
✅ **CDC** - Change data capture architecture
✅ **Data quality** - Validation, constraints, monitoring
✅ **Lineage** - Tracking data flow
✅ **Cataloging** - Hive Metastore, Glue, Unity Catalog
✅ **Performance tuning** - Shuffle, AQE, caching
✅ **Security** - Encryption, access control, audit logs
✅ **Streaming** - Windowing, checkpointing, state management
✅ **Z-ordering** - Multi-dimensional optimization
✅ **Cost optimization** - Spot instances, storage tiering

**Next steps:**
1. Build hands-on projects
2. Practice with real datasets
3. Learn one cloud platform deeply
4. Master workflow orchestration (Airflow)
5. Explore streaming (Kafka)

**You're well on your way to becoming a senior data engineer!** 🚀

---

*Keep learning, keep building, and remember: The best way to learn is by doing!*
