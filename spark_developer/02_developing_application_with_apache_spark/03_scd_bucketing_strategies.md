# Data Warehouse Patterns + Spark Bucketing Strategies

## The Connection That's Rarely Taught

This guide makes **explicit** the connection between **data warehouse design patterns** (Slowly Changing Dimensions, Fact tables) and **Spark optimization strategies** (bucketing, partitioning).

Most tutorials teach these concepts separately. This guide connects them to help you make better architectural decisions.

---

## Table of Contents

1. [Quick Decision Guide](#quick-decision-guide)
2. [Understanding the Fundamentals](#understanding-the-fundamentals)
3. [SCD Types → Bucketing Strategies](#scd-types--bucketing-strategies)
4. [Fact Table Patterns → Bucketing Strategies](#fact-table-patterns--bucketing-strategies)
5. [Complete Data Warehouse Example](#complete-data-warehouse-example)
6. [Decision Trees](#decision-trees)
7. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
8. [Real-World Case Studies](#real-world-case-studies)

---

## Quick Decision Guide

**Use this flowchart to decide your bucketing strategy:**

```
Is this a Dimension or Fact table?
│
├─ DIMENSION TABLE
│  │
│  ├─ How often does it change?
│  │  ├─ Never/Rarely (years)        → Type 0 SCD → Bucket once, never re-bucket
│  │  ├─ Infrequently (weekly/monthly) → Type 1 SCD → Re-bucket periodically
│  │  └─ Track history (append-only)  → Type 2 SCD → Bucket once + append forever ✅ BEST!
│  │
│  └─ Bucketing config:
│      bucketBy(num_buckets, "dimension_key").saveAsTable()
│
└─ FACT TABLE
   │
   ├─ Data arrival pattern?
   │  ├─ High velocity (hourly/daily)  → Partition by time + Bucket by dimension
   │  ├─ Batch loads (weekly)          → Bucket by dimension
   │  └─ Real-time streaming           → Don't bucket (use broadcast joins)
   │
   └─ Bucketing config:
       partitionBy("date").bucketBy(num_buckets, "dimension_key").saveAsTable()
```

---

## Understanding the Fundamentals

### What is Slowly Changing Dimension (SCD)?

**Definition:** Dimension tables that change over time at different rates and in different ways.

**Example - Customer Dimension:**
- Customer moves to new address (change)
- Customer changes phone number (change)
- Customer's purchase history grows (append)

**The Key Question:** How do we handle these changes in our data warehouse?

---

### What is Bucketing in Spark?

**Definition:** Pre-organizing data by hash-partitioning based on specific columns and saving that organization to disk.

**Benefit:** When joining on the bucketed column, Spark can skip the shuffle phase (massive performance gain).

**Example:**
```python
# Without bucketing - requires shuffle (SLOW)
orders.join(customers, "customer_id")  # Shuffles 100GB + 10GB

# With bucketing - no shuffle (FAST)
orders_bucketed.join(customers_bucketed, "customer_id")  # Reads matching buckets directly
```

---

### The Connection

**The rate and pattern of data change determines the optimal bucketing strategy.**

| Data Change Pattern | Bucketing Feasibility | Strategy |
|---------------------|----------------------|----------|
| **Never changes** | ✅✅✅ Perfect | Bucket once, use forever |
| **Append-only** | ✅✅✅ Perfect | Bucket + append (never re-bucket) |
| **Infrequent overwrites** | ✅✅ Good | Re-bucket periodically |
| **Frequent updates** | ⚠️ Challenging | Partition + bucket or don't bucket |
| **Real-time streaming** | ❌ Not feasible | Don't bucket |

**SCD types ARE data change patterns!** Therefore, **SCD types determine bucketing strategies.**

---

## SCD Types → Bucketing Strategies

### SCD Type 0: Fixed Dimension (Immutable)

**Pattern:** Data never changes after initial load.

**Examples:**
- Date dimension
- Geography hierarchy (country, state, city)
- Product categories (stable taxonomy)

**Bucketing Strategy:**
```python
# ✅ BUCKET ONCE - NEVER RE-BUCKET
# Perfect for bucketing because data is immutable

date_dimension.write \
    .bucketBy(50, "date_key") \
    .sortBy("date_key") \
    .saveAsTable("dim_date")

# Benefit: Joins on date_key are ALWAYS fast, forever
```

**Characteristics:**
- 🟢 Bucketing cost: One-time (initial load only)
- 🟢 Maintenance: Zero
- 🟢 Join performance: Optimal forever

---

### SCD Type 1: Overwrite (Current Value Only)

**Pattern:** When dimension changes, old value is overwritten. No history kept.

**Example - Customer Dimension:**
```
Before update:
customer_id | name  | city    | phone
1           | John  | NYC     | 555-1111

After address change (Type 1):
customer_id | name  | city    | phone
1           | John  | Boston  | 555-1111  ← Overwritten
```

**Bucketing Strategy:**
```python
# ✅ RE-BUCKET PERIODICALLY
# Acceptable if changes are infrequent (weekly/monthly)

# Weekly update process:
updated_customers = extract_customer_updates()

updated_customers.write \
    .bucketBy(100, "customer_id") \
    .mode("overwrite") \  # Type 1: Overwrites entire table
    .saveAsTable("dim_customer")

# Monday-Sunday: Fast joins (bucketed)
# Sunday night: Re-bucket with updates (one-time cost)
```

**When to use this strategy:**
- Changes are **infrequent** (weekly, monthly, quarterly)
- Benefits of fast joins **outweigh** re-bucketing cost
- Dimension table is **not huge** (re-bucketing time is acceptable)

**Cost-Benefit Analysis:**
```python
# Scenario: Customer dimension, 10M rows, updated weekly

# Cost: 
# - Re-bucketing time: 10 minutes (weekly)

# Benefit:
# - 7 days × 50 queries/day = 350 fast joins per week
# - Each join 5 minutes faster = 1,750 minutes saved
# - ROI: 175x (1,750 min saved / 10 min cost)

# Conclusion: Re-bucketing is worth it! ✅
```

**Characteristics:**
- 🟡 Bucketing cost: Periodic (weekly/monthly)
- 🟡 Maintenance: Scheduled re-bucketing
- 🟢 Join performance: Optimal between re-buckets

---

### SCD Type 2: Historical Tracking (Keep Full History)

**Pattern:** When dimension changes, create new row with effective dates. Keep all history.

**Example - Customer Dimension:**
```
After address change (Type 2):
customer_id | name  | city    | effective_from | effective_to | is_current
1           | John  | NYC     | 2023-01-01     | 2024-06-01   | false
1           | John  | Boston  | 2024-06-01     | 9999-12-31   | true  ← New row added
```

**Bucketing Strategy:**
```python
# ✅✅✅ BEST FOR BUCKETING!
# Append-only pattern = Never need to re-bucket

# Initial load:
initial_customers.write \
    .bucketBy(100, "customer_id") \
    .saveAsTable("dim_customer_scd2")

# Weekly updates (new rows for changed customers):
customer_changes.write \
    .bucketBy(100, "customer_id") \
    .mode("append") \  # Type 2: Appends new rows
    .saveAsTable("dim_customer_scd2")

# NEVER need to re-bucket! Old buckets remain valid ✅
```

**Why this is PERFECT for bucketing:**
1. **Append-only** - New rows don't affect old buckets
2. **Bucketing never breaks** - Hash(customer_id) is consistent
3. **Historical queries benefit** - Can join on past effective dates
4. **Zero maintenance** - Never re-bucket

**Query patterns:**
```python
# Current state query (most common)
spark.sql("""
    SELECT f.*, c.customer_name, c.city
    FROM fact_orders f
    JOIN dim_customer_scd2 c 
        ON f.customer_id = c.customer_id 
        AND c.is_current = true
""")
# No shuffle! Bucketed join ✅

# Historical point-in-time query
spark.sql("""
    SELECT f.*, c.customer_name, c.city
    FROM fact_orders f
    JOIN dim_customer_scd2 c 
        ON f.customer_id = c.customer_id 
        AND f.order_date BETWEEN c.effective_from AND c.effective_to
""")
# No shuffle! Still bucketed ✅
```

**Characteristics:**
- 🟢 Bucketing cost: One-time (initial load only)
- 🟢 Maintenance: Zero (append forever)
- 🟢 Join performance: Optimal forever
- 🟢 Historical queries: Supported and fast

**🎯 RECOMMENDATION: Use Type 2 SCD whenever possible for maximum bucketing benefit!**

---

### SCD Type 3: Limited History (Previous + Current)

**Pattern:** Keep current value + one previous value. No full history.

**Example - Customer Dimension:**
```
customer_id | name  | current_city | previous_city | city_change_date
1           | John  | Boston       | NYC           | 2024-06-01
```

**Bucketing Strategy:**
```python
# ✅ RE-BUCKET WHEN CHANGES OCCUR
# Similar to Type 1, but changes may be less frequent

# Monthly update:
updated_customers.write \
    .bucketBy(100, "customer_id") \
    .mode("overwrite") \
    .saveAsTable("dim_customer_type3")
```

**When to use:**
- Need to track **only recent change** (not full history)
- Changes are **infrequent**
- Want **simpler queries** than Type 2

**Characteristics:**
- 🟡 Bucketing cost: Periodic
- 🟡 Maintenance: Re-bucket on updates
- 🟢 Join performance: Optimal between updates

---

### SCD Type 6: Hybrid (Type 1 + Type 2 + Type 3)

**Pattern:** Combines aspects of multiple types.

**Example:**
```
customer_id | name  | city    | current_city | effective_from | effective_to | is_current
1           | John  | NYC     | Boston       | 2023-01-01     | 2024-06-01   | false
1           | John  | Boston  | Boston       | 2024-06-01     | 9999-12-31   | true
```

**Bucketing Strategy:**
```python
# ⚠️ COMPLEX - Combine append + update
# Re-bucket periodically or use partition + bucket

# Option 1: Re-bucket monthly
dimension.write \
    .bucketBy(100, "customer_id") \
    .mode("overwrite") \
    .saveAsTable("dim_customer_type6")

# Option 2: Partition by effective_date + bucket
dimension.write \
    .partitionBy("effective_from") \
    .bucketBy(100, "customer_id") \
    .mode("append") \
    .saveAsTable("dim_customer_type6")
```

**Characteristics:**
- 🟡 Bucketing cost: Variable
- 🟡 Maintenance: Complex
- 🟡 Join performance: Good

---

### Summary: SCD Types Comparison

| SCD Type | Change Pattern | Bucketing Strategy | Re-bucket Frequency | Join Performance |
|----------|---------------|-------------------|---------------------|------------------|
| **Type 0** | Never changes | ✅ Bucket once | Never | ⚡⚡⚡ Perfect |
| **Type 1** | Overwrite current | ✅ Re-bucket periodically | Weekly/Monthly | ⚡⚡ Good |
| **Type 2** | Append history | ✅✅✅ Bucket + append | Never | ⚡⚡⚡ Perfect |
| **Type 3** | Keep previous | ✅ Re-bucket periodically | Monthly | ⚡⚡ Good |
| **Type 6** | Hybrid | ⚠️ Complex | Variable | ⚡⚡ Good |

**Recommendation:** **Use Type 2 SCD for dimensions that change frequently** - it's append-only, perfect for bucketing!

---

## Fact Table Patterns → Bucketing Strategies

### Transaction Fact Tables (High Velocity)

**Pattern:** Individual transactions recorded as they occur. Append-only, high volume.

**Examples:**
- Sales transactions
- Website clicks
- Order events
- Log events

**Data characteristics:**
- 📈 **Volume:** Millions to billions of rows
- ⏱️ **Velocity:** Continuous append (hourly/daily)
- 📅 **Time-bound:** Always has a timestamp
- 🔗 **Joins:** Frequently joined with dimensions

**Bucketing Strategy:**
```python
# ✅ PARTITION BY TIME + BUCKET BY DIMENSION KEY
# Perfect for high-velocity append-only data

# Daily ETL:
daily_orders.write \
    .partitionBy("order_date") \       # New partition each day
    .bucketBy(200, "customer_id") \    # Bucket within partition
    .sortBy("customer_id", "order_time") \
    .mode("append") \                   # Safe! Never re-bucket
    .saveAsTable("fact_orders")

# Directory structure:
# /fact_orders/
#   order_date=2024-01-01/
#     bucket_000.parquet
#     bucket_001.parquet
#     ...
#     bucket_199.parquet
#   order_date=2024-01-02/  ← New partition daily
#     bucket_000.parquet
#     ...
```

**Why this works:**
1. **Each partition is independent** - New data doesn't touch old partitions
2. **Each partition is bucketed** - Fast joins within partitions
3. **Old partitions stay bucketed forever** - Never need to re-bucket
4. **Queries filter by date** - Scan only relevant partitions

**Query pattern:**
```python
# Partition pruning + bucketed join
spark.sql("""
    SELECT c.customer_name, SUM(o.amount) as total_sales
    FROM fact_orders o
    JOIN dim_customer c ON o.customer_id = c.customer_id
    WHERE o.order_date >= '2024-01-01'  -- Partition pruning
    GROUP BY c.customer_name
""")
# 1. Scans only partitions >= 2024-01-01
# 2. Within those partitions, bucketed join (no shuffle!)
# 3. Very fast! ⚡
```

**Choosing bucket count:**
```python
# Rule of thumb: Aim for 128MB-1GB per bucket

daily_data_size_gb = 100  # 100GB per day
partition_count = 1       # 1 partition per day
target_bucket_size_gb = 0.5  # 500MB per bucket

num_buckets = daily_data_size_gb / target_bucket_size_gb
# = 100 / 0.5 = 200 buckets

# Round to power of 2 for better hash distribution: 128 or 256
```

**Characteristics:**
- 🟢 Bucketing cost: One-time per partition
- 🟢 Maintenance: Zero (append-only)
- 🟢 Join performance: Optimal
- 🟢 Historical queries: Fast with partition pruning

---

### Periodic Snapshot Fact Tables (Scheduled Batch)

**Pattern:** Regular snapshots of state at specific points in time.

**Examples:**
- Daily inventory levels
- Monthly account balances
- Weekly warehouse stock

**Data characteristics:**
- 📊 **Volume:** All entities × snapshot frequency
- ⏱️ **Velocity:** Batch loads (daily/weekly/monthly)
- 📅 **Time-bound:** One snapshot per time period
- 🔄 **Pattern:** Append-only (one snapshot = one partition)

**Bucketing Strategy:**
```python
# ✅ PARTITION BY SNAPSHOT DATE + BUCKET BY ENTITY
# Similar to transaction facts

# Daily snapshot:
daily_inventory.write \
    .partitionBy("snapshot_date") \
    .bucketBy(100, "product_id") \
    .mode("append") \
    .saveAsTable("fact_inventory_snapshot")

# Each day is a complete snapshot in its own partition
```

**Query pattern:**
```python
# Latest snapshot analysis
spark.sql("""
    SELECT p.product_name, i.quantity_on_hand
    FROM fact_inventory_snapshot i
    JOIN dim_product p ON i.product_id = p.product_id
    WHERE i.snapshot_date = '2024-06-01'  -- Latest snapshot
""")
# No shuffle on join! ✅

# Trend analysis (multiple snapshots)
spark.sql("""
    SELECT p.product_name, i.snapshot_date, AVG(i.quantity_on_hand)
    FROM fact_inventory_snapshot i
    JOIN dim_product p ON i.product_id = p.product_id
    WHERE i.snapshot_date >= '2024-01-01'
    GROUP BY p.product_name, i.snapshot_date
""")
# Scans multiple partitions, each bucketed (fast!) ✅
```

**Characteristics:**
- 🟢 Bucketing cost: One-time per snapshot
- 🟢 Maintenance: Zero
- 🟢 Join performance: Optimal
- 🟢 Trend queries: Fast

---

### Accumulating Snapshot Fact Tables (State Changes)

**Pattern:** Rows represent processes with multiple milestones. Rows are UPDATED as process progresses.

**Examples:**
- Order fulfillment pipeline (ordered → packed → shipped → delivered)
- Loan applications (applied → reviewed → approved → funded)
- Patient treatment (admitted → diagnosed → treated → discharged)

**Data characteristics:**
- 🔄 **Updates:** Rows updated as milestones occur
- 📅 **Multiple dates:** Many date fields (one per milestone)
- ⚠️ **Challenging:** Not append-only!

**Bucketing Strategy:**
```python
# ⚠️ CHALLENGING - Updates break bucketing
# Option 1: Re-bucket periodically (if updates are batch)
# Option 2: Partition by last_update_date + bucket

# Option 1: Daily re-bucket (if volume is manageable)
updated_orders.write \
    .bucketBy(100, "order_id") \
    .mode("overwrite") \  # Re-bucket entire table
    .saveAsTable("fact_order_fulfillment")

# Option 2: Partition by update date
updated_orders.write \
    .partitionBy("last_update_date") \
    .bucketBy(100, "order_id") \
    .mode("append") \
    .saveAsTable("fact_order_fulfillment")
# New partition for each update (old partitions have stale data)
```

**Better alternative - Convert to Type 2:**
```python
# Instead of updating rows, append new rows with state changes
# This makes it append-only (perfect for bucketing!)

order_state_changes.write \
    .partitionBy("state_change_date") \
    .bucketBy(100, "order_id") \
    .mode("append") \
    .saveAsTable("fact_order_state_history")

# Structure:
# order_id | state      | state_date  | ...
# 1001     | ordered    | 2024-01-01  |
# 1001     | packed     | 2024-01-02  | ← New row instead of update
# 1001     | shipped    | 2024-01-03  | ← New row instead of update
```

**Characteristics:**
- 🔴 Bucketing cost: High (frequent re-bucketing)
- 🔴 Maintenance: Complex
- 🟡 Join performance: Good (if re-bucketed)
- 💡 **Recommendation:** Convert to append-only pattern

---

### Factless Fact Tables (Event Tracking)

**Pattern:** Records events/relationships without numeric measures.

**Examples:**
- Student course enrollment
- Product promotions
- Customer service interactions

**Data characteristics:**
- 📝 **Purpose:** Track relationships/events
- 📈 **Volume:** Can be large
- ✅ **Pattern:** Usually append-only

**Bucketing Strategy:**
```python
# ✅ STANDARD APPEND-ONLY BUCKETING
# Usually append-only, so same as transaction facts

enrollments.write \
    .partitionBy("enrollment_date") \
    .bucketBy(100, "student_id") \
    .mode("append") \
    .saveAsTable("fact_enrollment")
```

**Characteristics:**
- 🟢 Bucketing cost: One-time per partition
- 🟢 Maintenance: Zero
- 🟢 Join performance: Optimal

---

### Summary: Fact Table Patterns

| Fact Type | Update Pattern | Bucketing Strategy | Best For |
|-----------|---------------|-------------------|----------|
| **Transaction** | Append-only | ✅ Partition + Bucket | High-volume events |
| **Periodic Snapshot** | Append-only | ✅ Partition + Bucket | Scheduled snapshots |
| **Accumulating Snapshot** | Updates | ⚠️ Complex | Consider converting to append-only |
| **Factless** | Append-only | ✅ Partition + Bucket | Event tracking |

**Key Insight:** **Append-only facts are perfect for bucketing!** Convert update-based facts to append-only when possible.

---

## Complete Data Warehouse Example

### Scenario: E-commerce Analytics Platform

**Business Requirements:**
- 50M customers, 100K products, 500 stores
- 10M orders per day
- Analytics on customer behavior, product performance, regional sales
- Historical trending and reporting

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   DIMENSION TABLES                       │
├─────────────────────────────────────────────────────────┤
│ dim_customer (Type 2 SCD - Track customer changes)      │
│ dim_product (Type 2 SCD - Track product/price changes)  │
│ dim_store (Type 1 SCD - Rare updates)                   │
│ dim_date (Type 0 SCD - Fixed)                           │
│ dim_promotion (Type 2 SCD - Track promotion history)    │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Star Schema Joins
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     FACT TABLES                          │
├─────────────────────────────────────────────────────────┤
│ fact_orders (Transaction - 10M rows/day)                │
│ fact_inventory (Periodic Snapshot - Daily)              │
│ fact_web_events (Factless - Click tracking)             │
└─────────────────────────────────────────────────────────┘
```

---

### Implementation

#### 1. Dimension Tables

```python
# ===================================================================
# DIM_CUSTOMER (Type 2 SCD - Most Important!)
# ===================================================================
# Change frequency: ~1% of customers change info per week
# Volume: 50M customers, ~70M rows (with history)
# Join frequency: 1000+ queries per day

# Initial load:
initial_customers.write \
    .bucketBy(100, "customer_id") \
    .sortBy("customer_id") \
    .saveAsTable("dim_customer")

# Weekly change capture (append new versions):
customer_changes = spark.sql("""
    SELECT 
        customer_id,
        customer_name,
        email,
        city,
        state,
        current_date() as effective_from,
        to_date('9999-12-31') as effective_to,
        true as is_current
    FROM customer_changes_staging
""")

# Expire old versions:
spark.sql("""
    UPDATE dim_customer
    SET effective_to = current_date(), is_current = false
    WHERE customer_id IN (SELECT customer_id FROM customer_changes_staging)
    AND is_current = true
""")

# Append new versions (maintains bucketing!):
customer_changes.write \
    .bucketBy(100, "customer_id") \
    .mode("append") \
    .saveAsTable("dim_customer")

# ✅ NEVER re-bucket! Append-only pattern
# ✅ All joins on customer_id are fast forever

# ===================================================================
# DIM_PRODUCT (Type 2 SCD)
# ===================================================================
# Change frequency: Price/description changes daily
# Volume: 100K products, ~500K rows (with history)

products.write \
    .bucketBy(50, "product_id") \
    .sortBy("product_id") \
    .saveAsTable("dim_product")

# Daily updates (append new versions):
product_changes.write \
    .bucketBy(50, "product_id") \
    .mode("append") \
    .saveAsTable("dim_product")

# ===================================================================
# DIM_STORE (Type 1 SCD)
# ===================================================================
# Change frequency: 1-2 stores per month (very rare)
# Volume: 500 stores

stores.write \
    .bucketBy(10, "store_id") \
    .saveAsTable("dim_store")

# Monthly updates (re-bucket - acceptable because rare):
updated_stores.write \
    .bucketBy(10, "store_id") \
    .mode("overwrite") \
    .saveAsTable("dim_store")

# ===================================================================
# DIM_DATE (Type 0 SCD)
# ===================================================================
# Never changes
# Volume: ~10K rows (30 years of dates)

date_dimension.write \
    .bucketBy(10, "date_key") \
    .saveAsTable("dim_date")

# Loaded once, never updated ✅

# ===================================================================
# DIM_PROMOTION (Type 2 SCD)
# ===================================================================
# Track promotion history

promotions.write \
    .bucketBy(20, "promotion_id") \
    .mode("append") \
    .saveAsTable("dim_promotion")
```

---

#### 2. Fact Tables

```python
# ===================================================================
# FACT_ORDERS (Transaction Fact - Most Critical!)
# ===================================================================
# Volume: 10M orders per day = 3.65B per year
# Velocity: Continuous throughout the day
# Retention: 2 years = ~7.3B rows
# Primary join key: customer_id (most common queries)

# Daily ETL:
daily_orders.write \
    .partitionBy("order_date") \              # 1 partition per day
    .bucketBy(200, "customer_id") \           # 200 buckets per partition
    .sortBy("customer_id", "order_time") \    # Sort for better compression
    .mode("append") \
    .saveAsTable("fact_orders")

# Schema:
# order_id, order_date, order_time, customer_id, product_id, 
# store_id, promotion_id, quantity, amount, ...

# Bucketing math:
# 10M orders/day ÷ 200 buckets = 50K orders per bucket
# Assuming ~500 bytes per row: 50K × 500 = 25MB per bucket ✅

# ===================================================================
# FACT_INVENTORY (Periodic Snapshot)
# ===================================================================
# Volume: 100K products × 500 stores = 50M rows per day
# Frequency: Daily snapshot at midnight

daily_inventory.write \
    .partitionBy("snapshot_date") \
    .bucketBy(100, "product_id") \
    .mode("append") \
    .saveAsTable("fact_inventory")

# ===================================================================
# FACT_WEB_EVENTS (Factless - Event Tracking)
# ===================================================================
# Volume: 100M events per day (clicks, views, etc.)

daily_events.write \
    .partitionBy("event_date", "event_type") \  # Multi-level partitioning
    .bucketBy(200, "customer_id") \
    .mode("append") \
    .saveAsTable("fact_web_events")
```

---

#### 3. Common Queries (All Optimized!)

```python
# ===================================================================
# QUERY 1: Customer Lifetime Value
# ===================================================================
# Join orders with customers (most common query - runs 100+ times/day)

spark.sql("""
    SELECT 
        c.customer_id,
        c.customer_name,
        c.city,
        c.state,
        COUNT(DISTINCT o.order_id) as total_orders,
        SUM(o.amount) as lifetime_value
    FROM fact_orders o
    JOIN dim_customer c 
        ON o.customer_id = c.customer_id 
        AND c.is_current = true  -- Get current customer info
    WHERE o.order_date >= '2024-01-01'
    GROUP BY c.customer_id, c.customer_name, c.city, c.state
""")

# Execution plan:
# 1. Partition pruning on fact_orders (scans only 2024 partitions)
# 2. Bucketed join (NO SHUFFLE!) ✅
# 3. Aggregation
# Result: 2 minutes (vs 20 minutes without bucketing)

# ===================================================================
# QUERY 2: Product Performance by Region
# ===================================================================

spark.sql("""
    SELECT 
        p.product_name,
        p.category,
        s.region,
        SUM(o.quantity) as units_sold,
        SUM(o.amount) as revenue
    FROM fact_orders o
    JOIN dim_product p 
        ON o.product_id = p.product_id 
        AND p.is_current = true
    JOIN dim_store s 
        ON o.store_id = s.store_id
    WHERE o.order_date >= '2024-01-01'
    GROUP BY p.product_name, p.category, s.region
""")

# Execution plan:
# 1. Partition pruning on fact_orders
# 2. Bucketed join with dim_product (NO SHUFFLE on product_id)
# 3. Regular join with dim_store (small table, can broadcast)
# 4. Aggregation

# ===================================================================
# QUERY 3: Point-in-Time Historical Analysis
# ===================================================================
# "What were customer addresses at the time of their orders?"

spark.sql("""
    SELECT 
        o.order_id,
        o.order_date,
        c.customer_name,
        c.city as city_at_order_time  -- Historical address!
    FROM fact_orders o
    JOIN dim_customer c 
        ON o.customer_id = c.customer_id 
        AND o.order_date BETWEEN c.effective_from AND c.effective_to
    WHERE o.order_date >= '2024-01-01'
""")

# Execution plan:
# 1. Partition pruning
# 2. Bucketed join (works with date range join too!) ✅
# 3. Type 2 SCD enables point-in-time accuracy

# ===================================================================
# QUERY 4: Customer Behavior Funnel
# ===================================================================
# Join web events with orders

spark.sql("""
    SELECT 
        e.customer_id,
        COUNT(DISTINCT CASE WHEN e.event_type = 'view' THEN e.event_id END) as views,
        COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.event_id END) as adds,
        COUNT(DISTINCT o.order_id) as purchases
    FROM fact_web_events e
    LEFT JOIN fact_orders o 
        ON e.customer_id = o.customer_id 
        AND e.event_date = o.order_date
    WHERE e.event_date >= '2024-01-01'
    GROUP BY e.customer_id
""")

# Execution plan:
# 1. Both tables partitioned by date
# 2. Both tables bucketed by customer_id
# 3. Co-partitioned join (NO SHUFFLE!) ✅✅
# Result: Very fast cross-fact analysis
```

---

### Performance Metrics

**Before Bucketing:**
| Query | Execution Time | Shuffle Data |
|-------|---------------|--------------|
| Customer LTV | 22 min | 150 GB |
| Product Performance | 18 min | 120 GB |
| Historical Analysis | 28 min | 180 GB |
| Behavior Funnel | 35 min | 250 GB |
| **Total Daily** | **6.9 hours** | **4.2 TB** |

**After Bucketing:**
| Query | Execution Time | Shuffle Data |
|-------|---------------|--------------|
| Customer LTV | 2 min | 0 GB ✅ |
| Product Performance | 3 min | 5 GB (store join) |
| Historical Analysis | 4 min | 0 GB ✅ |
| Behavior Funnel | 5 min | 0 GB ✅ |
| **Total Daily** | **42 minutes** | **150 GB** |

**Improvement:**
- ⚡ **10x faster** query execution
- 💾 **96% reduction** in shuffle data
- 💰 **Significant cost savings** on cluster resources

---

## Decision Trees

### Decision Tree 1: Should I Use Bucketing?

```
START: Considering bucketing for a table
│
├─ Is this table joined frequently (10+ times per day)?
│  ├─ NO → Don't bucket (overhead not worth it)
│  └─ YES → Continue
│
├─ Do joins always use the same column(s)?
│  ├─ NO → Don't bucket (benefit only for consistent join keys)
│  └─ YES → Continue
│
├─ Can the other table(s) also be bucketed on the same key?
│  ├─ NO → Consider broadcast join instead
│  └─ YES → Continue
│
├─ What's the data change pattern?
│  ├─ Real-time streaming → Don't bucket
│  ├─ Hourly updates → Partition + Bucket (if append-only)
│  ├─ Daily appends → ✅ BUCKET (partition by date)
│  ├─ Weekly updates → ✅ BUCKET (re-bucket weekly)
│  ├─ Monthly updates → ✅ BUCKET (re-bucket monthly)
│  └─ Rarely/never changes → ✅ BUCKET (ideal!)
│
└─ DECISION: Use bucketing with appropriate strategy ✅
```

---

### Decision Tree 2: Which SCD Type Should I Use?

```
START: Designing a dimension table
│
├─ Do you need to track historical changes?
│  │
│  ├─ NO (only current values matter)
│  │  └─ How often does data change?
│  │     ├─ Never/Rarely → Type 0 (Fixed)
│  │     └─ Occasionally → Type 1 (Overwrite)
│  │
│  └─ YES (need history)
│     └─ How much history?
│        ├─ Just previous value → Type 3 (Limited History)
│        └─ Full history → Type 2 (Full History) ← RECOMMENDED!
│
└─ DECISION + BUCKETING STRATEGY:
   ├─ Type 0 → ✅✅✅ Bucket once, perfect forever
   ├─ Type 1 → ✅✅ Bucket, re-bucket on updates
   ├─ Type 2 → ✅✅✅ Bucket, append forever (BEST!)
   └─ Type 3 → ✅ Bucket, re-bucket on updates
```

---

### Decision Tree 3: Partition + Bucket Configuration

```
START: Configuring fact table
│
├─ Is there a time dimension?
│  ├─ NO → Bucket by primary join key
│  └─ YES → Continue
│
├─ What's the data arrival frequency?
│  ├─ Real-time → Don't partition by time (use processing time windows)
│  ├─ Hourly → Partition by hour
│  ├─ Daily → Partition by day ← Most common
│  ├─ Weekly → Partition by week
│  └─ Monthly → Partition by month
│
├─ What's the most common join key?
│  └─ Bucket by that key
│
├─ How many buckets?
│  └─ target_buckets = partition_size_gb / target_bucket_size_gb
│     └─ target_bucket_size_gb = 0.5 (500MB recommended)
│     └─ Round to power of 2: [64, 128, 256, 512, 1024]
│
└─ CONFIGURATION:
   .partitionBy("date_column")
   .bucketBy(num_buckets, "join_key")
   .sortBy("join_key")  ← Optional but recommended
```

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Bucketing Streaming Data

**Wrong:**
```python
# DON'T DO THIS!
streaming_df \
    .writeStream \
    .bucketBy(100, "customer_id") \  # ❌ Not supported!
    .format("parquet") \
    .start()
```

**Why it's wrong:**
- Streaming writes don't support bucketing
- Data arrives continuously, can't maintain bucket organization

**Right:**
```python
# Option 1: Micro-batch with partition + append
streaming_df \
    .writeStream \
    .partitionBy("event_date", "event_hour") \
    .format("parquet") \
    .start()

# Option 2: Batch re-bucket periodically
# Stream to temp location → Batch job buckets it daily
```

---

### ❌ Anti-Pattern 2: Appending to Bucketed Table Without Bucketing

**Wrong:**
```python
# Initial data is bucketed
initial_data.write.bucketBy(100, "id").saveAsTable("my_table")

# Later append WITHOUT bucketing
new_data.write.mode("append").saveAsTable("my_table")  # ❌ Breaks bucketing!
```

**Why it's wrong:**
- New data is not bucketed
- Table is now partially bucketed (broken state)
- Joins will fail to skip shuffle

**Right:**
```python
# ALWAYS bucket when appending to bucketed table
new_data.write \
    .bucketBy(100, "id") \  # ✅ Same bucket count and key
    .mode("append") \
    .saveAsTable("my_table")
```

---

### ❌ Anti-Pattern 3: Different Bucket Counts in Join

**Wrong:**
```python
# Table A: 100 buckets
tableA.write.bucketBy(100, "id").saveAsTable("A")

# Table B: 200 buckets
tableB.write.bucketBy(200, "id").saveAsTable("B")  # ❌ Different count!

# Join won't benefit from bucketing
spark.table("A").join(spark.table("B"), "id")  # Shuffle required!
```

**Why it's wrong:**
- Buckets don't align (bucket 0 in A ≠ bucket 0 in B)
- Spark must shuffle anyway

**Right:**
```python
# SAME bucket count for tables that join
tableA.write.bucketBy(100, "id").saveAsTable("A")
tableB.write.bucketBy(100, "id").saveAsTable("B")  # ✅ Same count

spark.table("A").join(spark.table("B"), "id")  # No shuffle! ✅
```

---

### ❌ Anti-Pattern 4: Over-Bucketing Small Tables

**Wrong:**
```python
# Small dimension table: 1MB, 10K rows
small_dim.write \
    .bucketBy(500, "id") \  # ❌ 500 buckets for 1MB = 2KB per bucket!
    .saveAsTable("dim_small")
```

**Why it's wrong:**
- Too many tiny files (overhead)
- Small file problem
- Should use broadcast join instead

**Right:**
```python
# For small tables, don't bucket - use broadcast join
from pyspark.sql.functions import broadcast

large_fact.join(broadcast(small_dim), "id")  # ✅ Faster than bucketing
```

**Rule of thumb:**
- Table < 10MB → Broadcast join
- Table > 10MB → Consider bucketing

---

### ❌ Anti-Pattern 5: Bucketing on Low-Cardinality Columns

**Wrong:**
```python
# Bucket by status (only 5 distinct values: pending, approved, shipped, delivered, cancelled)
orders.write \
    .bucketBy(100, "status") \  # ❌ Poor distribution!
    .saveAsTable("orders")
```

**Why it's wrong:**
- Only 5 distinct values → Only 5 buckets will be used
- 95 buckets are empty
- Uneven data distribution (severe skew)

**Right:**
```python
# Bucket by high-cardinality column
orders.write \
    .bucketBy(100, "customer_id") \  # ✅ Millions of distinct values
    .saveAsTable("orders")
```

**Rule of thumb:**
- Bucket column should have cardinality >> bucket count
- Ideal: distinct_values > 10 × num_buckets

---

### ❌ Anti-Pattern 6: Bucketing Without Statistics

**Wrong:**
```python
# Bucket tables but never analyze
orders.write.bucketBy(100, "customer_id").saveAsTable("orders")
customers.write.bucketBy(100, "customer_id").saveAsTable("customers")

# Spark doesn't know they're bucketed!
spark.table("orders").join(spark.table("customers"), "customer_id")
# Might still shuffle if Spark doesn't detect bucketing
```

**Why it's wrong:**
- Spark's optimizer needs table statistics
- Without stats, might not recognize bucketing

**Right:**
```python
# After bucketing, analyze tables
spark.sql("ANALYZE TABLE orders COMPUTE STATISTICS")
spark.sql("ANALYZE TABLE customers COMPUTE STATISTICS")

# Verify bucketing is recognized
spark.table("orders").join(spark.table("customers"), "customer_id").explain()
# Should show "BucketJoin" in plan ✅
```

---

### ❌ Anti-Pattern 7: Type 1 SCD with High Update Frequency

**Wrong:**
```python
# Customer dimension updated HOURLY (Type 1 SCD)
hourly_customer_updates.write \
    .bucketBy(100, "customer_id") \
    .mode("overwrite") \
    .saveAsTable("dim_customer")

# Re-bucketing 24 times per day! ❌ Very expensive
```

**Why it's wrong:**
- Re-bucketing overhead > benefit
- Constant table rewrites

**Right:**
```python
# Convert to Type 2 SCD (append-only)
hourly_customer_updates.write \
    .bucketBy(100, "customer_id") \
    .mode("append") \  # ✅ Never re-bucket
    .saveAsTable("dim_customer_scd2")

# Or use Type 1 with less frequent updates (daily/weekly)
```

---

## Real-World Case Studies

### Case Study 1: Financial Services - Trading Analytics

**Company:** Mid-size trading firm  
**Data Volume:** 500M trades per day  
**Challenge:** Slow customer trading pattern analysis

#### Before Bucketing:

```python
# Tables:
# - trades: 500M rows/day, 5 years = 900B rows total
# - customers: 10M customers (Type 1 SCD, updated weekly)

# Query: Customer trading patterns (run 1000+ times/day)
trades_df = spark.read.parquet("/data/trades")
customers_df = spark.read.parquet("/data/customers")

result = trades_df.join(customers_df, "customer_id")  
# Execution time: 45 minutes
# Shuffle: 800 GB
# Cost: $500 per query (cluster resources)
```

**Problem:** Shuffling 800 GB × 1000 queries/day = 800 TB shuffle/day!

#### Solution: Partition + Bucket

```python
# Redesign:
# 1. Trades: Partition by date + bucket by customer_id
trades_df.write \
    .partitionBy("trade_date") \
    .bucketBy(500, "customer_id") \
    .sortBy("customer_id", "trade_time") \
    .saveAsTable("trades_bucketed")

# 2. Customers: Type 1 SCD, weekly re-bucket
customers_df.write \
    .bucketBy(500, "customer_id") \
    .saveAsTable("customers_bucketed")

# 3. Weekly re-bucket job (Sunday night)
# Re-bucketing time: 1 hour (acceptable for weekly update)

# Query performance:
result = spark.table("trades_bucketed") \
    .join(spark.table("customers_bucketed"), "customer_id")
# Execution time: 3 minutes (15x faster!)
# Shuffle: 0 GB (partition pruning + bucketed join)
# Cost: $30 per query (95% reduction!)
```

#### Results:
- ⚡ **15x faster** queries (45 min → 3 min)
- 💰 **$470K saved per day** ($500 → $30 × 1000 queries)
- 💾 **800 TB → 0 TB** shuffle per day
- ✅ Weekly re-bucketing overhead acceptable (1 hour/week)

---

### Case Study 2: E-commerce - Customer 360

**Company:** Large online retailer  
**Data Volume:** 100M customers, 50M orders/day  
**Challenge:** Point-in-time customer analytics

#### Problem:

```python
# Need to know: "What was customer's address when they placed this order?"
# Using Type 1 SCD (overwrites) → Lost historical data
# Can't answer historical questions accurately
```

#### Solution: Convert to Type 2 SCD + Bucketing

```python
# Migrate from Type 1 to Type 2:
# Old schema (Type 1):
# customer_id | name | email | city | state

# New schema (Type 2):
# customer_id | name | email | city | state | effective_from | effective_to | is_current

# Implementation:
customer_scd2.write \
    .bucketBy(200, "customer_id") \
    .sortBy("customer_id", "effective_from") \
    .saveAsTable("dim_customer_scd2")

# Daily change capture (append new versions):
customer_changes.write \
    .bucketBy(200, "customer_id") \
    .mode("append") \  # ✅ Never re-bucket!
    .saveAsTable("dim_customer_scd2")

# Historical query (point-in-time accurate):
spark.sql("""
    SELECT 
        o.order_id,
        o.order_date,
        c.city as city_at_purchase_time,
        c.state as state_at_purchase_time
    FROM fact_orders o
    JOIN dim_customer_scd2 c 
        ON o.customer_id = c.customer_id 
        AND o.order_date BETWEEN c.effective_from AND c.effective_to
    WHERE o.order_date >= '2023-01-01'
""")
# No shuffle! Bucketed join works with date range ✅
```

#### Results:
- ✅ **Accurate historical analytics** (can answer "what was true when")
- ⚡ **Fast queries** (bucketed joins, no shuffle)
- 💾 **Append-only** (never re-bucket, zero maintenance)
- 📊 **Enabled new analytics** (customer migration patterns, retention by region)

#### Bonus Insight:
```python
# New analytics possible with Type 2:
# "How many customers moved to California in Q1 2024?"
spark.sql("""
    SELECT COUNT(DISTINCT customer_id) as movers
    FROM dim_customer_scd2
    WHERE state = 'CA'
    AND effective_from BETWEEN '2024-01-01' AND '2024-03-31'
    AND customer_id IN (
        SELECT customer_id FROM dim_customer_scd2
        WHERE state != 'CA' AND is_current = false
    )
""")
# This query impossible with Type 1 SCD!
```

---

### Case Study 3: Healthcare - Patient Records

**Company:** Hospital network  
**Data Volume:** 5M patients, 100K visits/day  
**Challenge:** Slow patient history queries

#### Before:

```python
# Accumulating snapshot fact (visits table)
# Rows UPDATED as patient progresses through care

# patient_id | visit_id | admitted_date | diagnosed_date | treated_date | discharged_date

# Problem: Updates break bucketing!
# Can't maintain bucketed organization with frequent updates
```

#### Solution: Convert to Event History (Append-Only)

```python
# Instead of updating rows, append state changes:
# patient_id | visit_id | event_type | event_date | ...

# visit_id | event_type | event_date
# 1001     | admitted   | 2024-01-01
# 1001     | diagnosed  | 2024-01-02  ← New row instead of update
# 1001     | treated    | 2024-01-05  ← New row instead of update
# 1001     | discharged | 2024-01-08  ← New row instead of update

# Now it's append-only! Perfect for bucketing:
visit_events.write \
    .partitionBy("event_date") \
    .bucketBy(100, "patient_id") \
    .mode("append") \
    .saveAsTable("fact_visit_events")

# Reconstruct current state with window functions:
current_visit_status = spark.sql("""
    SELECT 
        patient_id,
        visit_id,
        MAX(CASE WHEN event_type = 'admitted' THEN event_date END) as admitted_date,
        MAX(CASE WHEN event_type = 'diagnosed' THEN event_date END) as diagnosed_date,
        MAX(CASE WHEN event_type = 'treated' THEN event_date END) as treated_date,
        MAX(CASE WHEN event_type = 'discharged' THEN event_date END) as discharged_date
    FROM fact_visit_events
    GROUP BY patient_id, visit_id
""")
```

#### Results:
- ✅ **Append-only pattern** (perfect for bucketing)
- ⚡ **Fast joins** with patient dimension (bucketed)
- 📊 **Richer analytics** (can track time between events, delays, patterns)
- 💾 **Zero re-bucketing overhead**

---

### Case Study 4: Social Media - User Engagement

**Company:** Social media platform  
**Data Volume:** 500M users, 10B events/day  
**Challenge:** Real-time-ish analytics on massive scale

#### Architecture:

```python
# Dimension: User profiles (Type 2 SCD)
# - Track profile changes over time
# - 500M users, ~2B historical records

user_profiles.write \
    .bucketBy(1000, "user_id") \  # 1000 buckets for large scale
    .sortBy("user_id") \
    .saveAsTable("dim_user_profile")

# Fact: User events (High velocity!)
# - 10B events per day
# - Can't do real-time bucketing

# Solution: Micro-batch with partition + bucket
# Events processed every 5 minutes:
events_batch.write \
    .partitionBy("event_date", "event_hour", "event_5min") \  # Fine-grained partitions
    .bucketBy(1000, "user_id") \
    .mode("append") \
    .saveAsTable("fact_user_events")

# Directory structure:
# /fact_user_events/
#   event_date=2024-01-01/
#     event_hour=00/
#       event_5min=00/
#         bucket_0000.parquet ... bucket_0999.parquet
#       event_5min=05/
#         bucket_0000.parquet ... bucket_0999.parquet

# Query: User engagement metrics (millions of queries per day)
spark.sql("""
    SELECT 
        u.user_id,
        u.country,
        u.signup_date,
        COUNT(e.event_id) as event_count,
        COUNT(DISTINCT e.event_type) as unique_event_types
    FROM fact_user_events e
    JOIN dim_user_profile u 
        ON e.user_id = u.user_id 
        AND u.is_current = true
    WHERE e.event_date = current_date()
    GROUP BY u.user_id, u.country, u.signup_date
""")
# Scans only today's partitions + bucketed join = very fast!
```

#### Results:
- ⚡ **Sub-minute latency** for analytics (5-min batch + fast join)
- 💾 **No shuffle** on 10B row table (bucketed joins)
- 📊 **Scalable** to 500M users, 10B events/day
- 🔄 **Near-real-time** with micro-batching

---

## Key Takeaways

### The Core Principle

**Data change pattern determines bucketing strategy:**

```
Append-only → ✅✅✅ Perfect for bucketing (never re-bucket)
Infrequent updates → ✅✅ Good for bucketing (re-bucket periodically)
Frequent updates → ⚠️ Challenging (partition + bucket or don't bucket)
Streaming → ❌ Don't bucket (use broadcast joins)
```

---

### The SCD Connection

**SCD types ARE data change patterns:**

| SCD Type | Pattern | Bucketing Strategy |
|----------|---------|-------------------|
| Type 0 (Fixed) | Never changes | ✅✅✅ Bucket once |
| Type 1 (Overwrite) | Infrequent overwrites | ✅✅ Re-bucket periodically |
| **Type 2 (History)** | **Append-only** | **✅✅✅ Bucket + append (BEST!)** |
| Type 3 (Limited) | Occasional updates | ✅ Re-bucket periodically |

**Recommendation:** Use Type 2 SCD for dimensions that change - it's append-only and perfect for bucketing!

---

### The Fact Table Pattern

**Fact tables are usually append-only:**

- Transaction facts → Partition by time + Bucket by dimension
- Periodic snapshots → Partition by snapshot date + Bucket by entity
- Event tracking → Partition by time + Bucket by entity
- Accumulating snapshots → Convert to append-only event history if possible

**Strategy:** Partition + Bucket for all high-volume fact tables

---

### Cost-Benefit Decision

**Use bucketing when:**
1. ✅ Tables are joined frequently (10+ times/day)
2. ✅ Join key is consistent across queries
3. ✅ Both tables can be bucketed on same key
4. ✅ Data is append-only OR updates are infrequent
5. ✅ Tables are large enough (> 10 MB, can't broadcast)

**Don't use bucketing when:**
1. ❌ Tables are small (< 10 MB) - use broadcast join
2. ❌ Joins are infrequent (< 5 times/day)
3. ❌ Join keys vary across queries
4. ❌ Data updates frequently (hourly/continuous)
5. ❌ Real-time streaming data

---

### Implementation Checklist

When implementing bucketing:

- [ ] Analyze join patterns (identify common join keys)
- [ ] Classify tables (dimension vs fact, SCD type)
- [ ] Choose bucketing strategy based on change pattern
- [ ] Calculate bucket count (target 128MB-1GB per bucket)
- [ ] Implement partitioning for fact tables
- [ ] Test with representative queries
- [ ] Run ANALYZE TABLE to collect statistics
- [ ] Monitor query plans (verify bucketed joins)
- [ ] Set up re-bucketing jobs if needed (Type 1 SCD)
- [ ] Document strategy for team

---

## Conclusion

The connection between data warehouse design patterns and Spark optimization strategies is **powerful** but **rarely made explicit** in training materials.

By understanding how SCD types and fact table patterns map to bucketing strategies, you can:

1. **Design better data warehouses** (choose SCD types that optimize for Spark)
2. **Optimize query performance** (10x-100x speedups possible)
3. **Reduce infrastructure costs** (less shuffle = fewer resources)
4. **Enable new analytics** (Type 2 SCD enables historical analysis)

**The key insight:** 

> "Append-only data is perfect for bucketing. Design your data warehouse to be append-only wherever possible (Type 2 SCD for dimensions, partitioned facts). You'll get massive performance benefits with zero maintenance overhead."

---

## Further Reading

- **Kimball's Dimensional Modeling:** The definitive guide to SCD types
- **Spark SQL Performance Tuning:** Official Spark bucketing documentation
- **Databricks Best Practices:** Real-world bucketing strategies at scale
- **Star Schema Design:** How to structure data warehouses for analytics

---

## About This Guide

This guide documents the connection between data warehouse patterns and Spark optimization that many senior engineers know intuitively but is rarely taught explicitly.

If you found this useful, share it with your team! The industry needs more resources that connect these domains.

**Created:** 2024  
**Focus:** Practical data engineering insights  
**Audience:** Data engineers, analytics engineers, data architects

---

*"The best optimization is the one you design into your data architecture from the start."*