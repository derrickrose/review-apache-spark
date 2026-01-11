# Spark Join Strategy Selection

## Overview

When you write a join, Spark doesn't just execute it blindly - it **automatically chooses the most efficient strategy** to perform that join based on your data.

Spark's **Catalyst Optimizer** analyzes your data and picks the best join algorithm automatically!

---

## Table Size Categories

Understanding table sizes is crucial for knowing which join strategy Spark will use:

| Category | Size Range | Typical Row Count | Strategy Used |
|----------|------------|-------------------|---------------|
| **Small** | < 10MB (default) | ~10K - 100K rows | Broadcast Hash Join |
| **Medium** | 10MB - 1GB | ~100K - 10M rows | Shuffle Hash Join |
| **Large** | > 1GB | > 10M rows | Sort Merge Join |
| **Very Large** | > 10GB | > 100M rows | Sort Merge Join |

**Note:** These are approximate guidelines. Actual behavior depends on:
- Cluster memory
- Number of worker nodes
- Data characteristics (columns, data types)
- Configuration settings

### Example Size Estimates:
```python
# Small table: 10,000 rows × 10 columns ≈ 1-2 MB → Broadcast
# Medium table: 1 million rows × 10 columns ≈ 100 MB → Shuffle Hash
# Large table: 100 million rows × 10 columns ≈ 10 GB → Sort Merge
```

---

## Join Strategies in Spark

### 1. Broadcast Hash Join (BHJ) ⚡⚡⚡

**When Used:** One table is small enough to fit in memory (< 10MB by default)

**How It Works:**
- Small table is copied (broadcasted) to ALL worker nodes
- Each node joins its partition of the large table with the complete small table
- **No shuffle needed!** (Very fast)

**Example:**
```python
# If df2 is small (< 10MB by default)
df1.join(df2, "id")  # Spark automatically uses broadcast join
```

**Diagram:**
```
Small Table → [Broadcast to all nodes]
Large Table → [Partitioned across nodes]
Each node has: Full small table + its partition of large table
```

**Advantages:**
- ✅ Fastest join strategy
- ✅ No shuffle required
- ✅ Minimal network I/O

**Disadvantages:**
- ❌ Small table must fit in memory on each executor
- ❌ Not suitable if both tables are large

---

### 2. Shuffle Hash Join

**When Used:** Both tables are medium-sized (10MB - 1GB range)

**How It Works:**
- Both tables are shuffled (redistributed) by join key
- Rows with same key end up on same node
- Hash table built for smaller side
- Probe the hash table with the larger side

**Advantages:**
- ✅ Good for medium-sized tables
- ✅ Faster than Sort Merge Join

**Disadvantages:**
- ❌ Requires shuffle (network I/O)
- ❌ Hash table must fit in memory

---

### 3. Sort Merge Join (SMJ)

**When Used:** Both tables are large (> 1GB)

**How It Works:**
- Both tables are shuffled by join key
- Both sides are sorted
- Sorted data is merged together
- Default for large-large joins

**Diagram:**
```
Table 1: Shuffle → Sort → ┐
                          ├→ Merge
Table 2: Shuffle → Sort → ┘
```

**Advantages:**
- ✅ Can handle very large datasets
- ✅ Doesn't require entire table in memory
- ✅ Scalable for big data

**Disadvantages:**
- ❌ Requires shuffle and sort (expensive)
- ❌ Slower than Broadcast or Shuffle Hash

---

### 4. Cartesian Join (Cross Join)

**When Used:** No join condition (CROSS JOIN)

**How It Works:**
- Every row from table 1 matched with every row from table 2
- Produces M × N rows (where M and N are row counts)
- Very expensive! ⚠️

**Example:**
```python
# This creates 1000 × 1000 = 1,000,000 rows!
df1.crossJoin(df2)
```

**Warning:** Use with extreme caution. Can easily create billions of rows!

---

## Configuration Settings

### Key Configuration Parameters

#### 1. Auto Broadcast Join Threshold

**Default:** 10MB (10485760 bytes)

Controls when Spark will automatically broadcast a table.

```python
# Check current threshold
current_threshold = spark.conf.get("spark.sql.autoBroadcastJoinThreshold")
print(f"Current threshold: {current_threshold} bytes")

# Set to 50MB
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 50 * 1024 * 1024)

# Set to 100MB
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 100 * 1024 * 1024)

# Disable auto broadcast (set to -1)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
```

**When to adjust:**
- Increase if you have lots of memory and want to broadcast larger tables
- Decrease if you have limited memory
- Disable (-1) if broadcasts are causing OOM errors

---

#### 2. Prefer Sort Merge Join

**Default:** True

Controls whether Spark prefers Sort Merge Join over Shuffle Hash Join.

```python
# Check current setting
spark.conf.get("spark.sql.join.preferSortMergeJoin")

# Disable (prefer Shuffle Hash Join instead)
spark.conf.set("spark.sql.join.preferSortMergeJoin", "false")

# Enable (default)
spark.conf.set("spark.sql.join.preferSortMergeJoin", "true")
```

---

#### 3. Adaptive Query Execution (AQE)

**Default:** True (in Spark 3.0+)

Allows Spark to dynamically optimize join strategies during execution.

```python
# Enable AQE
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Configure adaptive broadcast threshold
spark.conf.set("spark.sql.adaptive.autoBroadcastJoinThreshold", 30 * 1024 * 1024)  # 30MB
```

---

#### 4. Broadcast Timeout

**Default:** 300 seconds (5 minutes)

Maximum time to wait for a broadcast to complete.

```python
# Set to 10 minutes
spark.conf.set("spark.sql.broadcastTimeout", 600)
```

---

### Complete Configuration Example

```python
from pyspark.sql import SparkSession

# Create Spark session with custom join configurations
spark = SparkSession.builder \
    .appName("Join Optimization") \
    .config("spark.sql.autoBroadcastJoinThreshold", 50 * 1024 * 1024) \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.autoBroadcastJoinThreshold", 50 * 1024 * 1024) \
    .config("spark.sql.broadcastTimeout", 600) \
    .getOrCreate()

# Or update existing session
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 50 * 1024 * 1024)
```

---

## How Spark Chooses the Strategy

Spark's **Catalyst Optimizer** analyzes:

### 1. Table Statistics
```python
# Spark automatically collects statistics during operations
# You can manually analyze tables for better optimization
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS")

# Check table statistics
spark.sql("DESCRIBE EXTENDED my_table").show(100, False)
```

### 2. Table Sizes
```python
# Check DataFrame size
df.cache()  # Cache to trigger computation
df.count()  # Force evaluation

# Estimate size
from pyspark.sql.functions import *
size_bytes = df.rdd.map(lambda x: len(str(x))).sum()
print(f"Estimated size: {size_bytes / (1024*1024):.2f} MB")
```

### 3. Join Type
Different join types favor different strategies:
- **Inner join:** All strategies applicable
- **Left/Right join:** Broadcast preferred for small right/left table
- **Full outer join:** Usually Sort Merge Join
- **Cross join:** Cartesian product (slow!)

### 4. Available Memory
```python
# Check executor memory
spark.conf.get("spark.executor.memory")
```

---

## Decision Flow

```
START: Performing join between Table A and Table B
│
├─ Is either table < autoBroadcastJoinThreshold (10MB)?
│  ├─ YES → Use Broadcast Hash Join ⚡⚡⚡
│  └─ NO → Continue
│
├─ Is preferSortMergeJoin enabled (default: true)?
│  ├─ YES → Are both tables large (> 1GB)?
│  │  ├─ YES → Use Sort Merge Join ⚡
│  │  └─ NO → Use Shuffle Hash Join ⚡⚡
│  └─ NO → Use Shuffle Hash Join ⚡⚡
│
└─ Special case: No join condition?
   └─ Use Cartesian Join 🐌 (WARNING: SLOW!)
```

---

## Manual Control

### Force a Broadcast Join

```python
from pyspark.sql.functions import broadcast

# Force df2 to be broadcasted
result = df1.join(broadcast(df2), "id")

# Force df1 to be broadcasted (BuildLeft)
result = broadcast(df1).join(df2, "id")
```

**When to force broadcast:**
- You know a table is small but Spark doesn't have statistics
- You want to override Spark's decision
- Testing performance with different strategies

---

### Disable Broadcast Join

```python
# Disable auto broadcast for this session
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)

# Or use a join hint (Spark 3.0+)
df1.hint("SHUFFLE_MERGE").join(df2, "id")
df1.hint("SHUFFLE_HASH").join(df2, "id")
```

---

### View the Chosen Strategy

```python
# Simple explain
df1.join(df2, "id").explain()

# Extended explain (more details)
df1.join(df2, "id").explain(True)

# Format explain for better readability
df1.join(df2, "id").explain("formatted")
```

**Example Output:**
```
== Physical Plan ==
*(2) BroadcastHashJoin [id#0], [id#5], Inner, BuildRight
:- *(2) LocalTableScan [id#0, name#1]
+- BroadcastExchange HashedRelationBroadcastMode
   +- *(1) LocalTableScan [id#5, value#6]
```

**What to look for:**
- `BroadcastHashJoin` → Broadcast strategy
- `SortMergeJoin` → Sort merge strategy
- `ShuffledHashJoin` → Shuffle hash strategy
- `BuildRight` or `BuildLeft` → Which table is being broadcasted/built

---

## Performance Comparison

| Strategy | Speed | Memory Usage | Network I/O | Best For |
|----------|-------|--------------|-------------|----------|
| **Broadcast Hash** | ⚡⚡⚡ Fastest | High (on executors) | Low | Small × Large tables |
| **Shuffle Hash** | ⚡⚡ Fast | Medium | High | Medium × Medium tables |
| **Sort Merge** | ⚡ Moderate | Low | High | Large × Large tables |
| **Cartesian** | 🐌 Slowest | Very High | Very High | Avoid! |

---

## Optimization Tips

### 1. Enable Statistics Collection
```python
# Analyze table to help Spark make better decisions
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS")
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS FOR COLUMNS col1, col2")
```

### 2. Adjust Broadcast Threshold Based on Cluster
```python
# If you have 16GB executor memory, you can safely broadcast larger tables
# Rule of thumb: Broadcast threshold should be 2-5% of executor memory
executor_memory_gb = 16
executor_memory_mb = executor_memory_gb * 1024  # 16384 MB

# Conservative approach: 5% is a good balance
safe_broadcast_mb = executor_memory_mb * 0.05  # 5% = 819 MB
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", int(safe_broadcast_mb * 1024 * 1024))

# More conservative: 2% for shared clusters
# safe_broadcast_mb = executor_memory_mb * 0.02  # 2% = 327 MB

# More aggressive: 10% only if you have dedicated resources
# safe_broadcast_mb = executor_memory_mb * 0.10  # 10% = 1638 MB
```

### 3. Cache Frequently Joined Tables
```python
# If a small table is joined multiple times, cache it
dim_table.cache()
fact_table.join(dim_table, "id")  # Will use cached version
```

### 4. Partition Data Properly
```python
# Partition by join key for better Sort Merge Join performance
df.repartition("join_key").write.parquet("path")
```

### 5. Use Bucketing for Repeated Joins
```python
# Bucket tables by join key (one-time cost, repeated benefit)
df.write.bucketBy(50, "join_key").sortBy("join_key").saveAsTable("bucketed_table")
```

---

## Monitoring Join Performance

### Check Query Execution
```python
# View the execution plan
df1.join(df2, "id").explain("cost")

# Get query execution time
import time
start = time.time()
result = df1.join(df2, "id").count()
print(f"Execution time: {time.time() - start:.2f} seconds")
```

### Spark UI
1. Open Spark UI (usually at `http://localhost:4040`)
2. Go to "SQL" tab
3. Click on your query
4. Examine:
   - DAG Visualization
   - Duration of each stage
   - Shuffle read/write sizes
   - Task distribution

---

## Common Issues & Solutions

### Issue 1: Broadcast Timeout
**Error:** `org.apache.spark.sql.execution.BroadcastTimeout`

**Solutions:**
```python
# Increase timeout
spark.conf.set("spark.sql.broadcastTimeout", 600)  # 10 minutes

# Or disable auto broadcast
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
```

---

### Issue 2: Out of Memory During Broadcast
**Error:** `java.lang.OutOfMemoryError`

**Solutions:**
```python
# Decrease broadcast threshold
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 5 * 1024 * 1024)  # 5MB

# Or increase executor memory
spark = SparkSession.builder \
    .config("spark.executor.memory", "8g") \
    .getOrCreate()
```

---

### Issue 3: Slow Sort Merge Join
**Solutions:**
```python
# 1. Increase parallelism
spark.conf.set("spark.sql.shuffle.partitions", 200)  # Default

# 2. Check for data skew
df.groupBy("join_key").count().orderBy(desc("count")).show()

# 3. Use salting for skewed keys
from pyspark.sql.functions import rand, concat, lit
df_salted = df.withColumn("join_key_salted", concat(col("join_key"), lit("_"), (rand() * 10).cast("int")))
```

---

## Key Takeaways

✅ **Spark automatically picks the best join strategy** based on table sizes and configuration

✅ **Broadcast Hash Join is fastest** (no shuffle!) - optimize for this when possible

✅ **Default broadcast threshold is 10MB** - adjust based on your cluster memory

✅ **Use `.explain()` to see what Spark chose** and verify it matches your expectations

✅ **Enable Adaptive Query Execution (AQE)** for dynamic optimization

✅ **Collect statistics** to help Spark make better decisions

✅ **Monitor joins in Spark UI** to identify bottlenecks

✅ **Force broadcast** when you know better than Spark (but use sparingly)

---

## Quick Reference Commands

```python
# Check configuration
spark.conf.get("spark.sql.autoBroadcastJoinThreshold")

# Set broadcast threshold to 50MB
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 50 * 1024 * 1024)

# Force broadcast
from pyspark.sql.functions import broadcast
df1.join(broadcast(df2), "id")

# View execution plan
df1.join(df2, "id").explain()

# Analyze table
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS")

# Enable AQE
spark.conf.set("spark.sql.adaptive.enabled", "true")
```

---

## Why Spark Doesn't Have Statistics

You might wonder: "If statistics are so important, why doesn't Spark always have them?"

### Reasons Spark Might Not Have Statistics

#### 1. Statistics Aren't Collected Automatically for All Sources

Spark doesn't automatically collect detailed statistics for every DataFrame or table. It depends on how the data was loaded:

```python
# Reading from files - NO automatic statistics
df = spark.read.parquet("data.parquet")  # Spark doesn't know size yet

# Reading from CSV - NO automatic statistics  
df = spark.read.csv("data.csv")  # Spark doesn't scan entire file

# Creating DataFrame from code - NO statistics
df = spark.range(1000000)  # Spark hasn't evaluated it yet
```

**Why?** Collecting statistics requires scanning the entire dataset, which is expensive. Spark uses **lazy evaluation** - it doesn't execute operations until you trigger an action.

---

#### 2. Statistics Are Only Collected for Managed Tables

```python
# Unmanaged table (external data) - NO auto statistics
spark.read.parquet("/path/to/data").createOrReplaceTempView("my_view")

# Managed table - CAN have statistics (but must run ANALYZE)
df.write.saveAsTable("managed_table")
spark.sql("ANALYZE TABLE managed_table COMPUTE STATISTICS")
```

For external data sources (files, S3, HDFS), Spark doesn't automatically know:
- How many rows exist
- Data distribution
- Column statistics

---

#### 3. Data Sources Don't Provide Metadata

Different sources provide different levels of metadata:

| Data Source | Statistics Available? | Notes |
|-------------|----------------------|-------|
| Parquet files | ✅ Partial | Row count in metadata (sometimes) |
| CSV files | ❌ No | No metadata at all |
| JSON files | ❌ No | No metadata at all |
| JDBC tables | ✅ Yes | Can get from source database |
| Hive tables | ✅ Yes | If ANALYZE was run |
| In-memory DataFrames | ❌ No | Must compute manually |

```python
# Parquet may have row count in footer
df = spark.read.parquet("data.parquet")
# But Spark might not read it until needed

# CSV has no metadata at all
df = spark.read.csv("data.csv")
# Spark has NO idea how many rows without scanning
```

---

#### 4. Statistics Become Stale After Transformations

```python
# Original table has statistics
spark.sql("ANALYZE TABLE users COMPUTE STATISTICS")

# After filtering/transformation - statistics are LOST
filtered_df = spark.table("users").filter(col("age") > 25)
# Spark doesn't know the size of filtered_df without running it!

# After join - statistics are UNKNOWN
joined_df = users.join(orders, "user_id")
# Spark has to estimate the result size
```

**Why?** Spark would need to execute the entire query to know exact statistics, defeating the purpose of lazy evaluation.

---

#### 5. ANALYZE TABLE Was Never Run

For managed tables, you must explicitly collect statistics:

```python
# Create table - NO statistics yet
df.write.saveAsTable("my_table")

# Must manually collect statistics
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS")

# For column-level statistics
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS FOR COLUMNS col1, col2")
```

**Many users forget this step!**

---

#### 6. Statistics Cost vs Benefit

Collecting statistics requires:
- Scanning the entire dataset
- Computing aggregations
- Storing metadata

```python
# This can be EXPENSIVE for large tables!
spark.sql("ANALYZE TABLE billion_row_table COMPUTE STATISTICS")
# Might take minutes or hours to complete
```

Spark doesn't do this automatically because:
- ❌ It's slow and resource-intensive
- ❌ Data might change frequently (statistics become stale)
- ❌ Not always needed for query optimization
- ❌ Would slow down every query startup

---

### How to Check if Statistics Exist

```python
# Method 1: Check table description
spark.sql("DESCRIBE EXTENDED my_table").show(100, False)
# Look for: Statistics: 1234567 bytes, 100000 rows

# Method 2: Check formatted description
spark.sql("DESCRIBE FORMATTED my_table").show(100, False)

# Method 3: Check query plan for statistics
df.explain("cost")
# Look for: Statistics(sizeInBytes=...)
```

---

### When Spark Might Have Some Statistics

#### 1. After Caching
```python
df.cache()
df.count()  # Triggers caching and computes statistics
# Now Spark knows the exact row count and size
```

#### 2. After Writing to Hive/Catalog
```python
df.write.saveAsTable("my_table")
# May have basic statistics if auto-stats is enabled
```

#### 3. Reading from JDBC
```python
# Can get statistics from source database
df = spark.read.jdbc(url, "table_name", properties)
```

#### 4. Parquet Files with Footer Metadata
```python
# Parquet stores row counts in file footer
df = spark.read.parquet("data.parquet")
# Spark CAN read this metadata (but might not use it immediately)
```

---

### Solutions: How to Provide Statistics to Spark

#### Option 1: Run ANALYZE TABLE
```python
# For managed tables - most reliable method
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS")

# With column statistics (more detailed)
spark.sql("ANALYZE TABLE my_table COMPUTE STATISTICS FOR COLUMNS col1, col2, col3")
```

#### Option 2: Force Broadcast (Override Spark's Decision)
```python
from pyspark.sql.functions import broadcast

# You know it's small, tell Spark explicitly
large_df.join(broadcast(small_lookup_df), "id")
```

#### Option 3: Use Join Hints
```python
# Spark 3.0+
df1.hint("broadcast").join(df2, "id")
df1.hint("SHUFFLE_MERGE").join(df2, "id")
df1.hint("SHUFFLE_HASH").join(df2, "id")
```

#### Option 4: Cache and Count
```python
# Force Spark to compute and store statistics
small_df.cache()
small_df.count()  # Now Spark knows the exact size

# Use in join
large_df.join(small_df, "id")  # Spark knows small_df size now
```

#### Option 5: Enable Auto Statistics Collection
```python
# For catalog tables
spark.conf.set("spark.sql.statistics.fallBackToHdfs", "true")

# Auto-gather statistics on write (Databricks-specific)
spark.conf.set("spark.databricks.optimizer.dynamicFilePruning", "true")
```

---

### Real-World Example: Impact of Missing Statistics

```python
# Scenario: Joining large fact table with small dimension table

# Small lookup table (actually 1MB, 1000 rows)
lookup_df = spark.read.csv("country_codes.csv")

# Large fact table (100GB, 1 billion rows)
sales_df = spark.read.parquet("sales_data.parquet")

# ❌ WITHOUT statistics - Spark doesn't know lookup_df is small
result = sales_df.join(lookup_df, "country_code")
# Spark might choose Sort Merge Join
# - Shuffles BOTH tables (including 100GB!)
# - Sorts both sides
# - Takes 10+ minutes

# ✅ WITH broadcast hint - Tell Spark it's small
result = sales_df.join(broadcast(lookup_df), "country_code")
# Spark uses Broadcast Join
# - Broadcasts 1MB to all nodes
# - No shuffle of 100GB table
# - Takes 30 seconds

# Speed improvement: 20x faster! 🚀
```

---

### Best Practices for Managing Statistics

#### 1. Analyze Frequently Queried Tables
```python
# Run after data loads or significant updates
spark.sql("ANALYZE TABLE sales_fact COMPUTE STATISTICS")
spark.sql("ANALYZE TABLE customer_dim COMPUTE STATISTICS")
```

#### 2. Cache Reference/Dimension Tables
```python
# Small tables used in multiple joins
country_codes.cache()
country_codes.count()  # Trigger caching

# Now all joins will know its size
sales.join(country_codes, "code")
orders.join(country_codes, "code")
```

#### 3. Use Broadcast for Known Small Tables
```python
# Dimension tables, lookup tables, configuration tables
fact_table.join(broadcast(dimension_table), "key")
```

#### 4. Schedule Regular ANALYZE Jobs
```python
# In production pipelines
def refresh_statistics(table_name):
    spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS")
    spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS FOR ALL COLUMNS")

# Run nightly or after ETL
refresh_statistics("sales_fact")
refresh_statistics("customer_dim")
```

#### 5. Monitor Query Plans
```python
# Check if statistics are being used
df.explain("cost")

# Look for:
# - Statistics(sizeInBytes=...) ✅ Good!
# - No statistics found ❌ Problem!
```

#### 6. Enable Adaptive Query Execution (AQE)
```python
# AQE can adjust joins mid-execution based on runtime statistics
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

---

### Summary: Statistics Checklist

When optimizing joins, ask yourself:

- [ ] Does Spark have statistics on my tables?
- [ ] Should I run `ANALYZE TABLE`?
- [ ] Are my dimension tables cached?
- [ ] Should I use `broadcast()` hint?
- [ ] Is AQE enabled for dynamic optimization?
- [ ] Am I monitoring query plans with `.explain()`?

**Remember:** Statistics are the key to Spark making intelligent join decisions. Without them, Spark is flying blind! 🎯

---

## Bottom Line

**Spark is smart** - it analyzes your data and picks the fastest join algorithm automatically! However, understanding these strategies helps you:
- Configure Spark optimally for your workload
- Debug performance issues
- Make informed decisions about data modeling
- Override Spark when you have domain knowledge it doesn't
- Provide statistics when Spark doesn't have them

**Key Insight:** Spark doesn't automatically have statistics because collecting them is expensive and would slow down lazy evaluation. You must either:
1. Explicitly collect statistics with `ANALYZE TABLE`
2. Tell Spark what you know with `broadcast()` hints
3. Enable features like AQE for runtime optimization

🚀 **Happy joining!**