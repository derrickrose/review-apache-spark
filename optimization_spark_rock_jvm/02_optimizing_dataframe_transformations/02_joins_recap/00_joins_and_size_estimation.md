# Spark 3.5 — Joins, size estimation, CBO and AQE

This file is the general reference: join types, physical strategies, hints, `sizeInBytes` estimation, CBO and AQE.
Broadcast-specific topics (threshold, compressed-file pitfall, conversion by AQE) are in
`03_broadcast_joins/broadcast_joins.md`.

**Verification legend:**

- **(verified)**: tested locally on PySpark 3.5.
- **(script: `NN_….py`)**: a script in this folder reproduces it, with the expected result as a comment. Run it to
  confirm.
- **(source)**: confirmed in the official docs or in the `branch-3.5` code of apache/spark (see section 17).
- **(unverified)**: written from memory, neither tested nor found in the sources.

## Contents

**Part 1 — Joins**

1. [Join types](#1-join-types)
2. [Physical strategies](#2-physical-strategies)
3. [Build side vs streamed side](#3-build-side-vs-streamed-side)
4. [BroadcastNestedLoopJoin vs SortMergeJoin](#4-broadcastnestedloopjoin-vs-sortmergejoin)
5. [Join hints](#5-join-hints)
6. [Checking the strategy in `explain()`](#6-checking-the-strategy-in-explain)

**Part 2 — How Spark estimates the size of a table**

7. [Reminder: prefixes](#7-reminder-prefixes)
8. [Sizes per type (`defaultSize`)](#8-sizes-per-type-defaultsize)
9. [CBO in brief](#9-cbo-in-brief)
10. [Where `sizeInBytes` comes from](#10-where-sizeinbytes-comes-from)
11. [Effect of operations (without / with CBO)](#11-effect-of-operations-without--with-cbo)

**Part 3 — Execution**

12. [AQE](#12-aqe)

**Part 4 — In practice**

13. [Checklist: slow join job](#13-checklist-slow-join-job)

**Appendices**

14. [Config reference](#14-config-reference)
15. [By Spark version](#15-by-spark-version)
16. [Scripts](#16-scripts)
17. [Sources](#17-sources)

---

# Part 1 — Joins

## 1. Join types

> **In short:** the join type says **what** result you get, independently of how Spark computes it.

| Type        | `how`                         | Result                                                                       |
|-------------|-------------------------------|------------------------------------------------------------------------------|
| Inner       | `inner` (default)             | Only rows with a match on both sides                                         |
| Left outer  | `left`, `left_outer`          | All left rows, nulls on the right if no match                                |
| Right outer | `right`, `right_outer`        | All right rows, nulls on the left if no match                                |
| Full outer  | `full`, `outer`, `full_outer` | All rows, nulls for unmatched rows on each side                              |
| Left semi   | `left_semi`                   | Left rows (left columns only) that have a match on the right (like `EXISTS`) |
| Left anti   | `left_anti`                   | Left rows (left columns only) with no match on the right (like `NOT EXISTS`) |
| Cross       | `cross`, `crossJoin()`        | Cartesian product of both sides                                              |

## 2. Physical strategies

> **In short:** the strategy says **how** Spark computes the result. For an equality, it tries broadcast first, then
> SortMergeJoin. Without an equality, only nested loops remain. (script: `02_join_strategies.py`)

| Strategy                | Principle                                                                                                                                                   | Shuffle                                          | Equality condition required |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|-----------------------------|
| BroadcastHashJoin       | the small side is copied to every executor as a hash table, the other side is read partition by partition                                                   | no                                               | yes                         |
| ShuffledHashJoin        | both sides are shuffled by key, then a hash table is built per partition on the smaller side                                                                | yes                                              | yes                         |
| SortMergeJoin           | both sides are shuffled and sorted by key, then merged in a single pass                                                                                     | yes                                              | yes                         |
| BroadcastNestedLoopJoin | one side is broadcast, each row of the other side is compared with each broadcast row                                                                       | no                                               | no                          |
| CartesianProduct        | each row of one side paired with each row of the other (cross join); one task per pair of partitions (N × M tasks), each reading one partition of each side | no (narrow dependencies, no `Exchange`) (source) | no                          |

**Spark's order of preference** for an equi-join (`a.id = b.id`), without a hint (source: `JoinSelection` comment):

1. BroadcastHashJoin, if one side is under `spark.sql.autoBroadcastJoinThreshold` (10 MB by default) and the join type
   allows it (section 3);
2. ShuffledHashJoin, only if `spark.sql.join.preferSortMergeJoin=false` (`true` by default) and one side is small enough
   (see below);
3. SortMergeJoin, if the keys are sortable;
4. CartesianProduct, if the join is inner-like;
5. BroadcastNestedLoopJoin as a last resort ("It may OOM but we don't have other choice").

For a join **without equality** (`a.x < b.y`, `BETWEEN`, `LIKE`…), hash and sort-merge strategies are impossible:
BroadcastNestedLoopJoin if one side is broadcastable, otherwise CartesianProduct (inner), otherwise
BroadcastNestedLoopJoin anyway (source).

**When Spark picks ShuffledHashJoin.** With default settings, almost never: `spark.sql.join.preferSortMergeJoin=true`
puts SortMergeJoin first. It is picked (script: `02_join_strategies.py`):

- with the `SHUFFLE_HASH` hint (section 5);
- with `spark.sql.join.preferSortMergeJoin=false`, if the small side fits in a per-partition hash table (estimate <
  `autoBroadcastJoinThreshold` × `spark.sql.shuffle.partitions`) and is at least `spark.sql.shuffledHashJoinFactor`
  times smaller than the other side (3 by default) (source: `canBuildLocalHashMapBySize` and `muchSmaller`);
- by AQE, at runtime, if all partitions are under `spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold` (`0` by
  default, so disabled) and this threshold is not smaller than `spark.sql.adaptive.advisoryPartitionSizeInBytes`. In
  that case, `preferSortMergeJoin` is ignored (source: *Performance Tuning* doc).

Benefit over SortMergeJoin: no sort. Risk: a partition's hash table must fit in memory (OOM if one key is very
frequent).

## 3. Build side vs streamed side

> **In short:** in a broadcast hash join, an executor sees **all** of the build side but **only a chunk** of the
> streamed side. So the side whose unmatched rows must be kept has to be streamed. A ShuffledHashJoin is less
> constrained,
> because after the shuffle each partition holds all rows of its keys (see 3.3). (script: `03_build_side.py`)

Hash-based strategies (BroadcastHashJoin, ShuffledHashJoin) give each side a role:

- **build side**: loaded entirely into a hash table (for a broadcast, copied to every executor);
- **streamed side**: read row by row, each row is looked up in the hash table.

### 3.1 Why the side matters for a broadcast

Outer joins must return **unmatched** rows. To claim a row has no match, it must have been compared with **all** of the
other table. With a broadcast, the side whose unmatched rows are kept must therefore be the **streamed** side.

Example: `left outer` with the left side broadcast (impossible). Each executor has all left rows, but only a chunk of
the right side. For a left row `id=3` whose match is on executor 2:

| Executor | Chunk of the right side | Result for `id=3`                 |
|----------|-------------------------|-----------------------------------|
| 1        | no `id=3`               | "no match" → `(3, null)` ❌ wrong |
| 2        | `id=3`                  | `(3, match)` ✅                   |

No executor can decide alone: you'd get duplicates or false nulls.

This is the **only** reference table for the broadcastable side (the broadcast file points here). It applies to
**BroadcastHashJoin**:

| Join                               | Unmatched rows to keep | Must be streamed  | Can be the build side (broadcastable) |
|------------------------------------|------------------------|-------------------|---------------------------------------|
| inner                              | none                   | either            | left or right                         |
| left outer / left semi / left anti | left ones              | left              | right only                            |
| right outer                        | right ones             | right             | left only                             |
| full outer                         | both sides             | both (impossible) | none                                  |

`left semi` / `left anti` have the same constraint as `left outer`: for each left row, Spark must decide "match" or "no
match".

### 3.2 Why a full outer join cannot be broadcast

With A streamed and B broadcast, unmatched rows of A are not a problem: each is processed once, with all of B. But a row
of B `id=7` may have its match in any partition of A:

| Executor | Chunk of A | Does it see a match for `id=7`?  |
|----------|------------|----------------------------------|
| 1        | no `id=7`  | no → would return `(null, 7)` ❌ |
| 2        | `id=7`     | yes ✅                           |
| 3        | no `id=7`  | no → would return `(null, 7)` ❌ |

Knowing that `id=7` had a match **nowhere** would require a global step gathering the results of all executors.
BroadcastHashJoin doesn't do that: its whole point is that each executor works alone.

Spark uses a SortMergeJoin instead: after the shuffle, all `id=7` rows of A and B are in the **same partition**, so a
single executor sees everything for that key.

"Impossible" here means "not implemented in BroadcastHashJoin": BroadcastNestedLoopJoin can do a full outer join with a
broadcast (it then broadcasts the smaller side), at the cost of an expensive global step (see section 4) (source:
`JoinSelection` comment).

### 3.3 ShuffledHashJoin: fewer constraints

After the shuffle, each partition contains all rows of its keys on both sides, so the "an executor sees only a chunk"
problem disappears. The ShuffledHashJoin tracks which build-side rows matched and emits the others at the end of its
partition:

- **full outer**: supported since Spark 3.1 (SPARK-32399) (source);
- **left outer with build left / right outer with build right**: supported since Spark 3.5 (SPARK-36612, codegen in
  SPARK-44060) (source).

So in Spark 3.5, the build side of a ShuffledHashJoin can be either side for inner, left outer, right outer and full
outer. Left semi / left anti still build on the right only (source: `canBuildShuffledHashJoinLeft/Right` in
`joins.scala`; verified: `ShuffledHashJoin ... LeftOuter, BuildLeft` with correct results, and a `shuffle_hash` hint on
the left of a left semi join is ignored with the WARN `build left for left semi join`).

## 4. BroadcastNestedLoopJoin vs SortMergeJoin

> **In short:** BNLJ compares everything with everything (N × M). That's acceptable if one side is tiny or the condition
> isn't an equality; otherwise it's a red flag. (script: `02_join_strategies.py`, timing)

|                             | BroadcastNestedLoopJoin                       | SortMergeJoin                              |
|-----------------------------|-----------------------------------------------|--------------------------------------------|
| Principle                   | each row of A compared with **each** row of B | shuffle + sort both sides, then merge      |
| Comparisons                 | N × M (quadratic)                             | ~ N log N + M log M (sort) + N + M (merge) |
| Shuffle                     | none (B is broadcast)                         | yes, both sides                            |
| Example 100 M × 10,000 rows | 10¹² comparisons                              | sort + one pass, far fewer                 |

For an equi-join, BroadcastNestedLoopJoin is usually more expensive. It is not worse when:

- **the broadcast side is tiny** (a few dozen rows): 100 M × 10 = 10⁹ simple comparisons may cost less than shuffling
  and sorting 100 M rows;
- **the join is not an equality**: SortMergeJoin is impossible (it needs equal keys to sort and merge), and
  BroadcastNestedLoopJoin is usually better than CartesianProduct if one side is small.

**Red flag:** a `BroadcastNestedLoopJoin` in `explain()` on a large table often indicates a badly written join condition
(an `OR` in the condition, a forgotten equality) or an unintended `crossJoin`. It's a frequent cause of jobs that never
finish.

## 5. Join hints

> **In short:** a hint forces a strategy. If it cannot be applied, Spark ignores it without error, with a simple WARN.
> (script: `05_join_hints.py`)

Hints and aliases: source (*Join Hints* doc). `MERGE`, `SHUFFLE_HASH` and `SHUFFLE_REPLICATE_NL` exist since Spark 3.0;
before, only `BROADCAST` existed. If both sides carry different hints, priority: `BROADCAST` > `MERGE` >
`SHUFFLE_HASH` > `SHUFFLE_REPLICATE_NL`. If both sides carry `BROADCAST` (or `SHUFFLE_HASH`), Spark picks the build side
based on the join type and the sizes (source).

| Hint                                             | Strategy                                                        |
|--------------------------------------------------|-----------------------------------------------------------------|
| `BROADCAST` (aliases `BROADCASTJOIN`, `MAPJOIN`) | BroadcastHashJoin (or BroadcastNestedLoopJoin without equality) |
| `MERGE` (aliases `SHUFFLE_MERGE`, `MERGEJOIN`)   | SortMergeJoin                                                   |
| `SHUFFLE_HASH`                                   | ShuffledHashJoin                                                |
| `SHUFFLE_REPLICATE_NL`                           | CartesianProduct (nested loop)                                  |

### 5.1 Syntax

DataFrame:

```python
from pyspark.sql.functions import broadcast

big.join(broadcast(small), "id")  # BROADCAST
big.join(small.hint("merge"), "id")  # MERGE
big.join(small.hint("shuffle_hash"), "id")  # SHUFFLE_HASH
```

SQL:

```sql
SELECT /*+ BROADCAST(s) */ *
FROM big b
         JOIN small s ON b.id = s.id
```

Hints remain active even with `spark.sql.autoBroadcastJoinThreshold=-1` (script: `05_join_hints.py`).

### 5.2 Where to put `broadcast()`

On the side that doesn't need to keep its unmatched rows (see section 3.1), usually the small lookup table.

| Join                         | Where to put `broadcast()`      | Example                                     |
|------------------------------|---------------------------------|---------------------------------------------|
| inner                        | on the small table, either side | `big.join(broadcast(small), "id")`          |
| left / left_semi / left_anti | on the **right**                | `big.join(broadcast(small), "id", "left")`  |
| right                        | on the **left**                 | `broadcast(small).join(big, "id", "right")` |
| full outer                   | nowhere (no broadcast possible) | `big.join(small, "id", "full")`             |

Tip for a `right` join: swapping the order and writing a `left` join is more readable and gives the same rows (only the
column order changes) (script: `05_join_hints.py`):

```python
# instead of
broadcast(small).join(big, "id", "right")
# write
big.join(broadcast(small), "id", "left")
```

### 5.3 Hint that cannot be applied

A hint that cannot be honored (e.g. `broadcast()` on the left of a left outer join) doesn't crash the query: Spark
ignores it and picks another strategy. The result is identical, only the strategy changes. Nothing shows in `explain()`,
only a WARN in the driver logs:
`Hint (strategy=broadcast) is not supported in the query: build left for left outer join.` (source: `HintErrorLogger` +
`JoinSelection.checkHintBuildSide`; script: `03_build_side.py`). A `MERGE` or `SHUFFLE_HASH` hint on a non-equi join
gives the same kind of WARN, with the reason `no equi-join keys` (source).

## 6. Checking the strategy in `explain()`

> **In short:** `explain()` shows the chosen strategy and, for a hash join, the build side (`BuildRight` / `BuildLeft`).

```python
df.explain()
```

- `BroadcastHashJoin ... BuildRight` / `BuildLeft`: the broadcast side.
- `SortMergeJoin` instead of `BroadcastHashJoin` after a `broadcast()` hint: the hint was ignored, probably on the wrong
  side (see 5.3).
- `BroadcastNestedLoopJoin` on a large table: check the join condition (see section 4).
- With AQE, `explain()` before an action shows the **initial** plan (`isFinalPlan=false`): the strategy may still change
  at runtime (see section 12).

---

# Part 2 — How Spark estimates the size of a table

To pick a strategy (section 2), Spark needs a size estimate for each side: `sizeInBytes`. This part explains where it
comes from.

## 7. Reminder: prefixes

Exa (E) = 10¹⁸, i.e. a billion billion (1,000,000,000,000,000,000).

The sequence of prefixes:

| Prefix | Symbol | Value |
|--------|--------|-------|
| kilo   | k      | 10³   |
| mega   | M      | 10⁶   |
| giga   | G      | 10⁹   |
| tera   | T      | 10¹²  |
| peta   | P      | 10¹⁵  |
| exa    | E      | 10¹⁸  |
| zetta  | Z      | 10²¹  |
| yotta  | Y      | 10²⁴  |

## 8. Sizes per type (`defaultSize`)

> **In short:** without statistics, Spark counts a fixed size per column type (20 bytes for a string, whatever its real
> length). It's an approximation to make decisions, not a measurement. (script: `08_default_size.py`)

Values used by the optimizer (Catalyst) to **estimate** the size of a plan (`sizeInBytes`) when the row count is known.
They don't reflect actual memory usage.

Verified locally on PySpark 3.5 via `DataType.defaultSize()` (verified).

### 8.1 Simple types

| Spark type                           | Bytes                 |
|--------------------------------------|-----------------------|
| `BooleanType`                        | 1                     |
| `ByteType`                           | 1                     |
| `ShortType`                          | 2                     |
| `IntegerType`                        | 4                     |
| `LongType`                           | 8                     |
| `FloatType`                          | 4                     |
| `DoubleType`                         | 8                     |
| `DecimalType` (precision ≤ 18)       | 8                     |
| `DecimalType` (precision > 18)       | 16                    |
| `StringType`                         | 20 (arbitrary value)  |
| `BinaryType`                         | 100 (arbitrary value) |
| `DateType`                           | 4                     |
| `TimestampType` / `TimestampNTZType` | 8                     |
| `NullType`                           | 1                     |
| `DayTimeIntervalType`                | 8                     |
| `YearMonthIntervalType`              | 4                     |

### 8.2 Complex types

| Type         | Rule                         | Example                                |
|--------------|------------------------------|----------------------------------------|
| `ArrayType`  | size of a single element     | `array<int>` = 4                       |
| `MapType`    | key + value (a single entry) | `map<string,bigint>` = 20 + 8 = 28     |
| `StructType` | sum of fields                | `struct<a:int,b:string>` = 4 + 20 = 24 |

**Why a single element for `ArrayType` / `MapType`?** The number of elements is variable and absent from the schema:
Spark can't know it without reading the data. So it assumes **1 element on average** (comment in `ArrayType.scala`,
SPARK-18853). Before this change, the assumption was 100 elements: estimates exploded (`array<array<string>>` = 100 ×
100 × 20 = 200 KB per row) and blocked the broadcast of tables that were actually small (source: SPARK-18853, fixed in
2.0.3 / 2.1.0, which proposed "a safer sane default is probably 1"; the 3.5 code says "We assume that there is only 1
element on average in an array").

`StructType` doesn't have this problem: its number of fields is fixed and known from the schema, Spark simply adds them
up.

Consequence: an `array<int>` column holding 1,000 integers per row is estimated at 4 bytes instead of ~4,000. Spark may
broadcast a table much bigger than it thinks (OOM risk, same pitfall as compressed files: see
`03_broadcast_joins/broadcast_joins.md`, section 4).

### 8.3 Calculation examples

**Small table.** 1,000 rows, columns `id: int` and `name: string` (script: `08_default_size.py`, via `VALUES`):

- one row = 4 + 20 = 24 bytes of data, **+ 8 bytes** of row header added by Spark;
- estimate = 1,000 × (8 + 24) = **32,000 bytes** (source: `LocalRelation.computeStats` uses
  `EstimationUtils.getSizePerRow`, which is `8 + sum of defaultSize`).

Without the header, you'd get 24,000 bytes: that's the "by hand" calculation, but not Spark's.

If names are 3 characters ("Bob"), the real size is smaller. If they're 5,000-character texts, it's much bigger, but
Spark still counts 20 bytes. The JVM also adds object headers and padding, not counted. It's an approximation to make
decisions, not a measurement.

**Large table.** 100 `string` columns, 2,000,000 rows, **row count known** (e.g. table analyzed with CBO):

- one row = 100 × 20 = 2,000 bytes;
- estimate = 2,000,000 × 2,000 = **4,000,000,000 bytes ≈ 4 GB** (≈ 3.7 GiB).

Spark adds 8 bytes of header per row (`getSizePerRow`), so the exact estimate is 2,000,000 × (8 + 2,000) ≈ **4.016 GB**
(source). Either way, it's far above the 10 MB broadcast threshold.

**Careful, the result depends on the path.** If the same table is built with `spark.range(2_000_000).select(...)`, Spark
doesn't recompute rows × size: it applies a **ratio** to the `range` estimate (16 MB × (8 + 2,000) / (8 + 8) ≈ **2
GB**). That's because `range` is estimated at 8 bytes per row **without** a header, while the ratio does count the
header (source: `Range.computeStats` and `SizeInBytesOnlyStatsPlanVisitor.visitUnaryNode`; script:
`08_default_size.py`).

## 9. CBO in brief

> **In short:** CBO replaces default sizes with **real statistics**, but only for catalog tables on which
> `ANALYZE TABLE` has been run. (script: `11_operations_cbo.py`)

**CBO** (*Cost-Based Optimizer*) is a mode of the Catalyst optimizer. Without it, Spark only uses fixed rules and
default sizes (section 8). With it, it uses **real statistics** on tables to estimate how many rows come out of a filter
or a join, then picks the best plan (join strategy, join order).

**Enable CBO:** `spark.sql.cbo.enabled=true` (`false` by default). Join reordering is configured separately:
`spark.sql.cbo.joinReorder.enabled=true` (`false` by default).

**Compute statistics:** they are not computed automatically, you must run `ANALYZE TABLE`. They are then stored in the
catalog.

| Command                                                                        | Statistics computed                                                                                                                                                                              |
|--------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ANALYZE TABLE t COMPUTE STATISTICS`                                           | table level: row count and size in bytes                                                                                                                                                         |
| `ANALYZE TABLE t COMPUTE STATISTICS NOSCAN`                                    | table level: size in bytes only (no table scan)                                                                                                                                                  |
| `ANALYZE TABLE t COMPUTE STATISTICS FOR COLUMNS c1, c2` (or `FOR ALL COLUMNS`) | table level + column level: `min`, `max`, `num_nulls`, `distinct_count`, `avg_col_len`, `max_col_len`, `histogram` (filled if `spark.sql.statistics.histogram.enabled=true`, `false` by default) |

(source: *ANALYZE TABLE* doc)

These column statistics are visible with `DESCRIBE EXTENDED t column` (script: `11_operations_cbo.py`).

**Main limit:** CBO only works for analyzed **catalog tables**. A direct `spark.read.parquet(...)`, an RDD or a
`spark.range` have no stored statistics: CBO changes nothing for them (see 10.1).

Statistics are not recomputed automatically: if the table changes, rerun `ANALYZE TABLE`. After a write done by Spark
(e.g. append):

- with `spark.sql.statistics.size.autoUpdate.enabled=false` (default), Spark **clears** the table's stats;
- with `true`, it replaces them with the new size in bytes only (`rowCount` and column stats are lost).

(source: `CommandUtils.updateTableStats`; script: `11_operations_cbo.py`, append case). Stats become truly **stale**
when files are modified outside Spark (unverified).

Note: with stats present but CBO **off** (and `spark.sql.cbo.planStats.enabled=false`), the catalog stats are converted
to plan stats as `sizeInBytes` only, without `rowCount` (source: `CatalogStatistics.toPlanStats`).

## 10. Where `sizeInBytes` comes from

> **In short:** it depends on the source. Files = size on disk, cache = real size in memory, RDD = unknown
> (`Long.MaxValue`). (script: `10_size_in_bytes_sources.py`)

### 10.1 By source

| Source                                                                          | Without CBO                                              | With CBO (`spark.sql.cbo.enabled=true`, `false` by default, + `ANALYZE TABLE`)                                                                                                                          |
|---------------------------------------------------------------------------------|----------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Files (Parquet, ORC, CSV…)                                                      | disk size × `fileCompressionFactor`                      | same (no stats without a catalog table)                                                                                                                                                                 |
| Catalog table, `ANALYZE TABLE t COMPUTE STATISTICS`                             | `totalSize` (disk size)                                  | `rowCount` × estimated row size                                                                                                                                                                         |
| Catalog table, `... FOR COLUMNS c1, c2`                                         | `totalSize`                                              | `rowCount` × row size (columns' `avgLen`), selectivity of filters/joins via min/max, `distinctCount`, `nullCount` (and histograms if `spark.sql.statistics.histogram.enabled=true`, `false` by default) |
| Cached DataFrame (`cache()` + action)                                           | real in-memory size (columnar cache) and real `rowCount` | same                                                                                                                                                                                                    |
| `spark.range`                                                                   | rows × 8 (no row header)                                 | same (`rowCount` known)                                                                                                                                                                                 |
| `LocalRelation` (e.g. `SELECT … FROM VALUES …`)                                 | rows × (8 + sum of `defaultSize`)                        | same (`rowCount` known)                                                                                                                                                                                 |
| RDD (`LogicalRDD`), `createDataFrame(rdd)` / `createDataFrame(list)` in PySpark | `Long.MaxValue` (unknown)                                | same                                                                                                                                                                                                    |

- `Range`: size computed arithmetically (`(end - start) / step × 8`), without reading data (source:
  `Range.computeStats`).
- Files: `sizeInBytes = file size × fileCompressionFactor` (source: `HadoopFsRelation.sizeInBytes`).
- Cache: until the cache is materialized, Spark keeps the original plan's estimate; after an action, it uses the real
  size and row count (source: `InMemoryRelation.computeStats`).
- `LogicalRDD`: Spark can't know the size without running the RDD, so it uses `spark.sql.defaultSizeInBytes`
  (`Long.MaxValue` by default) as an "unknown" sentinel. It's not a row count: it's a **weight in bytes** (≈ 8
  exabytes), and `rowCount` stays empty.

### 10.2 File sources: size on disk

For Parquet, `sizeInBytes` = size of the compressed files. `spark.sql.sources.fileCompressionFactor` (1.0 by default)
multiplies this size in the estimate.

Consequence for broadcast (a compressed table may be broadcast while it's much bigger in memory) and when to use this
factor: see `03_broadcast_joins/broadcast_joins.md`, section 4.

### 10.3 Inspecting the estimate

```python
stats = df._jdf.queryExecution().optimizedPlan().stats()
stats.sizeInBytes()  # estimated weight in bytes
stats.rowCount()  # row count, if known (Option)
```

## 11. Effect of operations (without / with CBO)

> **In short:** without CBO, a `filter` never reduces the estimate and a `select` adjusts it by ratio. With CBO, Spark
> estimates selectivity. (source: `SizeInBytesOnlyStatsPlanVisitor`, `EstimationUtils`; script: `11_operations_cbo.py`)

| Operation | Without CBO                                                                                                                                                                                                                                                                                                                                                                                                                      | With CBO                                                                                                                      |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `select`  | **adjusts** the estimate proportionally to the row size: `child size × (8 + Σ defaultSize kept) / (8 + Σ defaultSize of child)`. It can go down (columns dropped) or **up** (wider columns added, see the `range` example in 8.3)                                                                                                                                                                                                | `rowCount` × row size, with `avgLen` instead of `defaultSize` (+ 12 bytes per string)                                         |
| `filter`  | no reduction                                                                                                                                                                                                                                                                                                                                                                                                                     | `rowCount` × estimated selectivity (e.g. `id < 10` on min=1/max=1,000,000 ≈ 0.001 %)                                          |
| `join`    | usually the **product** of both sides' sizes (often huge; always for `cross`). Exceptions: `left semi` / `left anti` = left size; inner / outer equi-join where one side's `distinctKeys` cover its join keys (e.g. that side went through `distinct()` or `groupBy(key)`) = **sum** of sizes. A plain `spark.range` does **not** qualify: `range(1000).join(range(500), "id")` is estimated at 8,000 × 4,000 = 32 MB (verified) | estimate from the keys' `distinctCount`; `spark.sql.cbo.joinReorder.enabled=true` (`false` by default) allows join reordering |

**A filter doesn't reduce the estimate (without CBO).** `spark.range(1, 1000000).filter("id < 10")` stays estimated at ~
8 MB. You need `spark.sql.cbo.enabled=true` (`false` by default) and `ANALYZE TABLE ... COMPUTE STATISTICS FOR COLUMNS`
for Spark to evaluate selectivity.

---

# Part 3 — Execution

## 12. AQE

> **In short:** AQE re-optimizes the plan **during** execution using real numbers. It merges small partitions, splits
> skewed partitions and can convert a join to a broadcast. (script: `12_aqe.py`)

### 12.1 AQE in brief

**AQE** (*Adaptive Query Execution*) re-optimizes the plan **during execution**, from the real statistics of already
completed stages (partition sizes, bytes written). CBO decides before execution from stored statistics; AQE then
corrects with real numbers.

Enabled by default since Spark 3.2: `spark.sql.adaptive.enabled` (`true` by default) (source: *Performance Tuning* doc
and migration guide). What it can do:

- merge small partitions (coalescing, section 12.3);
- split skewed partitions (skew, section 12.4);
- convert a SortMergeJoin into a BroadcastHashJoin: see `03_broadcast_joins/broadcast_joins.md`, section 6;
- convert a SortMergeJoin into a ShuffledHashJoin (section 2).

### 12.2 `isFinalPlan`

`isFinalPlan` is a state flag of `AdaptiveSparkPlanExec` (root node added by AQE). It becomes `true` only once this plan
has been executed to completion.

1. Before an action: the plan is split into *query stages* at shuffle/broadcast boundaries → `isFinalPlan=false`.
2. During execution: at each completed stage, AQE collects real stats (partition sizes, bytes written) and re-optimizes
   the rest (coalescing, broadcast conversion, skew…).
3. All stages materialized: AQE creates and runs the final stage → `isFinalPlan=true`, `explain()` shows `Final Plan` +
   `Initial Plan`.

Pitfall (verified) — also applies to `count()`, which runs a different plan too (aggregate):

| Moment               | `isFinalPlan` |
|----------------------|---------------|
| before action        | `false`       |
| after `df.show()`    | `false`       |
| after `df.collect()` | `true`        |

`show()` runs a new plan (with `limit`), not the DataFrame's own: `df.explain()` stays at `false`. To see the final
plan: **SQL** tab of the Spark UI, or `explain()` after an action that runs the full plan (`collect()`, `write`…).

### 12.3 Partition coalescing

After a shuffle, Spark creates `spark.sql.shuffle.partitions` partitions (200 by default), often nearly empty on small
data. AQE **merges** them. Enabled by `spark.sql.adaptive.coalescePartitions.enabled` (`true` by default).

The target size depends on `spark.sql.adaptive.coalescePartitions.parallelismFirst` (`true` by default, since 3.2). The
code computes (source: `CoalesceShufflePartitions` and `ShufflePartitionsUtil.coalescePartitions`):

`target = max(min(total shuffle size / minNumPartitions, advisoryPartitionSizeInBytes), minPartitionSize)`

- **`true` (default)**: `minNumPartitions` = `spark.sparkContext.defaultParallelism`. The target is
  `total / defaultParallelism`, **capped** at `advisoryPartitionSizeInBytes` (64 MB) and floored at
  `spark.sql.adaptive.coalescePartitions.minPartitionSize` (1 MB). So partitions are usually much smaller than 64 MB.
  Goal: maximize parallelism.
- **`false`**: `minNumPartitions` = 1, so the target is `advisoryPartitionSizeInBytes` (64 MB). The docs recommend this
  setting.

Example (verified, `local[4]`, a few-MB shuffle): `parallelismFirst=true` → 4 partitions; `false` → 1 partition.

In the final plan: `AQEShuffleRead coalesced` (script: `12_aqe.py`).

### 12.4 Skew join

A partition is considered **skewed** if it is both:

- larger than `spark.sql.adaptive.skewJoin.skewedPartitionFactor` (5 by default) × the median partition size;
- and larger than `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` (256 MB by default).

AQE **splits** it into several chunks (and duplicates the matching partition on the other side), which prevents a single
task from processing almost all the data. Enabled by `spark.sql.adaptive.skewJoin.enabled` (`true` by default). Only
applies to SortMergeJoin and ShuffledHashJoin (source: `OptimizeSkewedJoin`).

Only a "streamed" side can be split: the left side for inner / cross / left outer / left semi / left anti, the right
side for inner / cross / right outer. A skewed **full outer** join is therefore never split (source:
`canSplitLeftSide` / `canSplitRightSide`).

In the final plan: `SortMergeJoin(skew=true)` (source: `ShuffledJoin.nodeName`; script: `12_aqe.py`).

When AQE isn't enough (very dominant key, unsupported join): the **salting** technique, see `../07_skewed_joins/`.

---

# Part 4 — In practice

## 13. Checklist: slow join job

1. **Look at the final plan**, not the initial one: SQL tab of the Spark UI, or `explain()` after `collect()` (section
   12.2).
2. **SortMergeJoin while one side is small?** Check its `sizeInBytes` (10.3). Frequent causes: RDD / `createDataFrame`
   (`Long.MaxValue`), filter not taken into account without CBO (section 11). Fixes: `broadcast()`, `cache()` + action,
   CBO.
3. **`BroadcastNestedLoopJoin` or `CartesianProduct` on a large table?** Check the join condition: `OR`, forgotten
   equality, unintended cross join (section 4).
4. **Hint ignored?** Check the side (section 5.2) and look for the WARN in the driver logs (5.3).
5. **Slow broadcast, timeout or driver OOM?** The broadcast side is probably bigger than its estimate: compressed files,
   arrays (see `03_broadcast_joins/broadcast_joins.md`, sections 3 and 4).
6. **One task much longer than the others?** Skew: check that AQE detected it (`SortMergeJoin(skew=true)`, 12.4),
   otherwise salting.
7. **Many tiny tasks, or partitions much smaller than 64 MB?** By default coalescing favors parallelism (12.3): set
   `spark.sql.adaptive.coalescePartitions.parallelismFirst=false` to target `advisoryPartitionSizeInBytes`, or reduce
   `spark.sql.shuffle.partitions`.
8. **CBO enabled but wrong estimates?** Stats cleared or stale: rerun `ANALYZE TABLE` (section 9).

---

# Appendices

## 14. Config reference

All configs cited in both docs, with their default value in Spark 3.5. All values are confirmed in `SQLConf.scala` and
`core/.../config/package.scala` of branch 3.5 (source; script: `13_conf_defaults.py`). "B" = detailed in
`03_broadcast_joins/broadcast_joins.md`. This is the **only** complete list: the broadcast file points here.

| Config                                                        | Default                                                              | Role                                                                                                                  |
|---------------------------------------------------------------|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `spark.sql.autoBroadcastJoinThreshold`                        | `10485760` (10 MB)                                                   | automatic broadcast threshold; `-1` disables it (hints stay active) (see 2, B section 2)                              |
| `spark.sql.defaultSizeInBytes`                                | `Long.MaxValue` (≈ 8 EiB)                                            | assumed size when unknown (RDD) (see 10.1)                                                                            |
| `spark.sql.sources.fileCompressionFactor`                     | `1.0`                                                                | multiplies the disk size of file sources in the estimate (see 10.2, B section 4)                                      |
| `spark.sql.cbo.enabled`                                       | `false`                                                              | enables CBO (see 9, 10.1, 11)                                                                                         |
| `spark.sql.cbo.joinReorder.enabled`                           | `false`                                                              | reorders joins with CBO (see 9, 11)                                                                                   |
| `spark.sql.statistics.histogram.enabled`                      | `false`                                                              | computes histograms during `ANALYZE ... FOR COLUMNS` (see 9, 10.1)                                                    |
| `spark.sql.join.preferSortMergeJoin`                          | `true`                                                               | prefers SortMergeJoin over ShuffledHashJoin (see 2)                                                                   |
| `spark.sql.shuffledHashJoinFactor`                            | `3`                                                                  | one side must be N times smaller for a ShuffledHashJoin (see 2)                                                       |
| `spark.sql.statistics.size.autoUpdate.enabled`                | `false`                                                              | updates the table size after a write; otherwise stats are cleared (see 9)                                             |
| `spark.sql.adaptive.enabled`                                  | `true`                                                               | enables AQE (see 12.1)                                                                                                |
| `spark.sql.adaptive.autoBroadcastJoinThreshold`               | unset → same value as `spark.sql.autoBroadcastJoinThreshold`         | separate threshold for AQE's runtime decisions (see B section 6)                                                      |
| `spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin`   | `0.2`                                                                | below it, AQE refuses to convert to broadcast (see B section 6)                                                       |
| `spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold`     | `0`                                                                  | AQE converts to ShuffledHashJoin if all partitions are under this threshold (see 2)                                   |
| `spark.sql.adaptive.coalescePartitions.enabled`               | `true`                                                               | merges small partitions after a shuffle (see 12.3)                                                                    |
| `spark.sql.adaptive.coalescePartitions.parallelismFirst`      | `true`                                                               | if `true`, the coalescing target is `total / defaultParallelism`, capped at `advisoryPartitionSizeInBytes` (see 12.3) |
| `spark.sql.adaptive.coalescePartitions.minPartitionSize`      | `1MB`                                                                | minimum partition size after coalescing (see 12.3)                                                                    |
| `spark.sql.adaptive.advisoryPartitionSizeInBytes`             | `64MB` (via `spark.sql.adaptive.shuffle.targetPostShuffleInputSize`) | coalescing target if `parallelismFirst=false`, upper cap otherwise; also the split size for skew (see 12.3, 12.4)     |
| `spark.sql.adaptive.skewJoin.enabled`                         | `true`                                                               | splits skewed partitions in joins (see 12.4)                                                                          |
| `spark.sql.adaptive.skewJoin.skewedPartitionFactor`           | `5`                                                                  | factor relative to the median to detect skew (see 12.4)                                                               |
| `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` | `256MB`                                                              | minimum size of a skewed partition (see 12.4)                                                                         |
| `spark.sql.shuffle.partitions`                                | `200`                                                                | number of partitions after a shuffle (see 12.3, B section 6)                                                          |
| `spark.sql.broadcastTimeout`                                  | `300` (s)                                                            | max time to build/send the broadcast (see B section 3)                                                                |
| `spark.driver.memory`                                         | `1g`                                                                 | driver memory, which collects the broadcast side (see B section 3)                                                    |
| `spark.driver.maxResultSize`                                  | `1g`                                                                 | max size of results collected on the driver (see B section 3)                                                         |

## 15. By Spark version

This document describes Spark 3.5. Main differences from earlier versions:

| Version       | Change                                                                                                                                                                                                                                       |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2.0.3 / 2.1.0 | arrays / maps estimated at 1 element instead of 100 (SPARK-18853) (source)                                                                                                                                                                   |
| 3.0           | AQE with its 3 features: coalescing, SortMergeJoin → BroadcastHashJoin conversion, skew join (disabled by default); `MERGE`, `SHUFFLE_HASH`, `SHUFFLE_REPLICATE_NL` hints (before: only `BROADCAST`) (source)                                |
| 3.1           | ShuffledHashJoin possible for full outer (SPARK-32399) (source)                                                                                                                                                                              |
| 3.2           | AQE enabled by default; introduction of `spark.sql.adaptive.autoBroadcastJoinThreshold`, `spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold`, `spark.sql.adaptive.coalescePartitions.parallelismFirst` and `minPartitionSize` (source) |
| 3.5           | ShuffledHashJoin can build left for left outer and right for right outer (SPARK-36612, codegen SPARK-44060) (source)                                                                                                                         |
| before 3.0    | `spark.sql.adaptive.enabled` exists since 1.6 (source: `.version("1.6.0")` in `SQLConf.scala`), but without join conversion or skew join: a SortMergeJoin chosen at planning stays a SortMergeJoin (unverified for the feature details)      |

## 16. Scripts

Each script uses the number of the section it illustrates. Expected results are in comments (`# expected: …`).

| Script                        | Sections                                                  |
|-------------------------------|-----------------------------------------------------------|
| `02_join_strategies.py`       | 2 (strategies, ShuffledHashJoin), 4 (BNLJ vs SMJ, timing) |
| `03_build_side.py`            | 3 (build side), 5.3 (ignored hint, WARN)                  |
| `05_join_hints.py`            | 5 (syntax, aliases, `right` → `left`), 6                  |
| `08_default_size.py`          | 8 (`defaultSize`, calculation examples)                   |
| `10_size_in_bytes_sources.py` | 10 (range, RDD, files, factor, cache)                     |
| `11_operations_cbo.py`        | 9 (CBO, `ANALYZE TABLE`), 11 (effect of operations)       |
| `12_aqe.py`                   | 12 (`isFinalPlan`, coalescing, skew)                      |
| `13_conf_defaults.py`         | 14 (default values)                                       |

## 17. Sources

- Source code: `sql/api/src/main/scala/org/apache/spark/sql/types/` (each type overrides `defaultSize`, e.g.
  `StringType.scala`: `override def defaultSize: Int = 20`). "1 element" assumption for arrays/maps: comment in
  `ArrayType.scala` and ticket SPARK-18853.
- Source code, all on `branch-3.5` unless stated:
    - `sql/core/.../execution/SparkStrategies.scala` (`JoinSelection`: strategy order, hint WARNs);
    - `sql/catalyst/.../optimizer/joins.scala` (`canBuildBroadcastLeft/Right`, `canBuildShuffledHashJoinLeft/Right`,
      `canBuildLocalHashMapBySize`, `muchSmaller`);
    - `sql/catalyst/.../statsEstimation/SizeInBytesOnlyStatsPlanVisitor.scala` and `EstimationUtils.scala` (estimation
      without CBO, `getSizePerRow` = 8 + …);
    - `sql/catalyst/.../logical/LocalRelation.scala`, `basicLogicalOperators.scala` (`Range`);
    - `sql/core/.../columnar/InMemoryRelation.scala` (cache stats);
    - `sql/core/.../datasources/HadoopFsRelation.scala` (`fileCompressionFactor`);
    - `sql/core/.../command/CommandUtils.scala` (`updateTableStats`);
    - `sql/core/.../exchange/BroadcastExchangeExec.scala` (`MAX_BROADCAST_TABLE_BYTES = 8L << 30`);
    - `sql/core/.../adaptive/OptimizeSkewedJoin.scala`, `joins/ShuffledJoin.scala` (`skew=true`);
    - `sql/core/.../joins/CartesianProductExec.scala` and `core/.../rdd/CartesianRDD.scala` (narrow dependencies, no
      shuffle);
    - `sql/catalyst/.../analysis/HintErrorLogger.scala`, `plans/logical/hints.scala`;
    - `sql/catalyst/.../internal/SQLConf.scala`, `core/.../internal/config/package.scala` (default values);
    - `python/pyspark/sql/session.py` (`createDataFrame(list)` → `parallelize` → `LogicalRDD`).
- Tickets: SPARK-18853 (arrays with 1 element), SPARK-32399 (ShuffledHashJoin full outer), SPARK-36612 and SPARK-44060
  (ShuffledHashJoin outer build side, 3.5.0).
- Spark 3.5.0 release notes.
- Spark SQL migration guide (AQE enabled by default in 3.2).
- Scaladoc: `org.apache.spark.sql.types.DataType.defaultSize`.
- Official docs: Spark SQL *Performance Tuning* — `spark.sql.autoBroadcastJoinThreshold`, join hints, AQE (coalescing,
  skew join, join conversion).
- Official docs: Spark 3.5 SQL configuration table (`parallelismFirst`, `minPartitionSize`,
  `maxShuffledHashJoinLocalMapThreshold`).
- Official docs: Spark SQL *ANALYZE TABLE* (statistics used by CBO).