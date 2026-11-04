# Bucketing

## To Remember

### 1. Split the data by the columns you will later use for joins

- `n` buckets **per partition**: rows are hashed on the bucket columns and written into `n` files.
- The bucketing metadata (columns, number of buckets, sort) lives in the **catalog**, so you must use
  `saveAsTable` (not `save` / `parquet`).

```python
my_df.write \
    .bucketBy(4, "id") \
    .sortBy("id") \
    .mode("overwrite") \
    .saveAsTable("bucketed_df")
```

### 2. Writing is almost as expensive as a regular shuffle

You pay the shuffle **once**, at write time. It is only worth it if the bucketed table is read and joined/grouped
**many times**.

### 3. Subsequent joins are much faster and do not incur shuffles

Both sides must be bucketed on the join key with the **same number of buckets**.

Without bucketing — 2 `Exchange hashpartitioning` (one per side):

```
SortMergeJoin [id#2L], [id#6L], Inner
:- Sort ... +- Exchange hashpartitioning(id#2L, 200)
+- Sort ... +- Exchange hashpartitioning(id#6L, 200)
```

With bucketing — **no Exchange**, Spark reads the buckets directly:

```
SortMergeJoin [id#17L], [id#15L], Inner
:- Sort ... FileScan parquet large_bucketed ... Bucketed: true, SelectedBucketsCount: 4 out of 4
+- Sort ... FileScan parquet small_bucketed ... Bucketed: true, SelectedBucketsCount: 4 out of 4
```

### 4. Same benefit for `groupBy`

- Pre-bucket your DFs by the columns you will use for grouping.
- Subsequent groupings will be much faster.

```python
flights_df.write \
    .partitionBy("origin") \
    .bucketBy(4, "dest", "carrier") \
    .mode("overwrite") \
    .saveAsTable("flights_bucketed")
```

The `groupBy("origin", "dest", "carrier")` goes from **2 shuffles** (round robin + `hashpartitioning`) to
**0 shuffles for the aggregation**: `partial_avg` and `avg` run in the same stage. The only remaining `Exchange`
is the `rangepartitioning` required by the final `orderBy`.

Bonus: the filter `origin = 'DEN'` becomes a **`PartitionFilter`** (partition pruning) because the table is
partitioned by `origin`.

### 5. Bonus: bucket pruning

Spark only reads a subset of the buckets when you filter by the column you bucketed by.

```python
spark.table("large_bucketed").filter("id = 10").explain()
```

```
FileScan parquet large_bucketed[id#17L] Bucketed: true, ..., SelectedBucketsCount: 1 out of 4
```

`SelectedBucketsCount: 1 out of 4` → only 1 bucket file out of 4 is scanned.

- Works with `=`, `<=>`, `IN`, `isNull` on the bucket column (and `AND` / `OR` of those).
- Does **not** work on a column you did not bucket by.

#### ⚠️ Gotcha: `autoBucketedScan` (Spark ≥ 3.1)

`spark.sql.sources.bucketing.autoBucketedScan.enabled` is `true` by default. The planner rule
`DisableUnnecessaryBucketedScan` turns off bucketed scans when no join/aggregation benefits from them,
so the plan shows:

```
FileScan parquet large_bucketed[id#17L] Batched: true, Bucketed: false (disabled by query planner), ...
```

→ no `SelectedBucketsCount`, **no bucket pruning visible**, all files are scanned.

To observe it, disable the rule:

```python
spark.conf.set("spark.sql.sources.bucketing.autoBucketedScan.enabled", "false")
```

## How to read the plan

| Plan says                                    | Meaning                                       |
|----------------------------------------------|-----------------------------------------------|
| `Bucketed: true`                             | bucketed scan used                            |
| `Bucketed: false (disabled by query planner)`| `autoBucketedScan` switched it off            |
| `SelectedBucketsCount: N out of N`           | bucketed scan, no pruning                     |
| `SelectedBucketsCount: 1 out of N`           | bucket pruning ✅                             |
| No `Exchange hashpartitioning` before a join | bucketing avoided the shuffle ✅              |
