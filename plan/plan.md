# SPARK EXPERT 10/10 — PRODUCTION MASTERY CURRICULUM

> A program for becoming a production Spark expert: someone who can diagnose an **unknown** Spark workload, find the root cause from evidence, apply a fix, and **prove** the improvement with measurements.

## Contents
- §0 [Expert standard](#0-expert-standard)
- §1 [Methodology toolkit](#1-methodology-toolkit)
- §2 [Environment, scale, budget](#2-environment-scale-ladder-budget)
- §3 [Datasets](#3-datasets)
- §4 [Roadmap](#4-program-roadmap)
- §5 [Modules M01–M29](#5-modules)
- §6 [Lab card template](#6-lab-card-template)
- §7 [30 core production labs](#7-the-30-core-production-labs)
- §8 [Combined pathologies](#8-combined-production-pathologies)
- §9 [Unknown incident labs](#9-unknown-incident-labs)
- §10 [Capstones & final test](#10-capstones--final-test)
- §11 [10/10 acceptance criteria](#11-1010-acceptance-criteria)
- §12 [Official documentation](#12-official-documentation)

---

## 0. Expert standard

### 0.1 Objective
```
UNKNOWN PRODUCTION SPARK JOB
  → observe the symptom → measure → Spark UI → SQL / physical plan → Catalyst / AQE
  → classify the resource (CPU / memory / GC / disk / network / I/O / scheduler / driver / metadata / object store)
  → data distribution → root cause → hypothesis
  → ONE controlled experiment → prove or refute
  → fix → benchmark → functional correctness → no regression
  → cost impact → production recommendation → document
```

An expert is not someone who knows 300 configs. An expert explains **why** a config changes behaviour.

### 0.2 What "Spark expert" means
These are **not** the definition:
- "I know PySpark / the Spark APIs."
- "I completed 30 labs."
- "I ran 500 GB."
- "I know `repartition()`, `cache()` and `broadcast()`."
- "I know the configuration parameters."

The definition: take an unknown 100–500 GB production-like workload and explain
- **WHAT** is slow, **WHERE** it is slow, **WHY** it is slow;
- **WHICH** data causes it, **WHICH** operator, **WHICH** saturated resource;
- **WHICH** optimization addresses the cause;
- **WHETHER** it actually worked, proven with metrics.

> "Give me the application. Give me the Spark UI. Give me the data. Give me the logs.
> I will find the bottleneck, prove the root cause, fix it, measure it, and explain the trade-off."

### 0.3 The system you must understand end to end
```
SQL / DataFrame → Catalyst → CBO / statistics → physical plan → AQE → Exchange → shuffle
→ scheduler → tasks → JVM → Python workers → network → storage → Parquet → S3
→ Iceberg → metadata → commit
```
Skill stack: PySpark + Spark SQL + Spark UI + physical plans + AQE + partitioning + shuffle + joins + skew + memory + JVM + serialization + file formats + small files + S3 + Iceberg (including distribution mode) + streaming + Kafka + Kubernetes + observability + fault injection + benchmarking + source-code reading + production incident diagnosis.

### 0.4 Absolute rules (every lab)
1. Start from a deliberately bad baseline.
2. Use a real or realistic large-scale dataset.
3. Have a measurable symptom.
4. Use the Spark UI.
5. Read the SQL tab and physical plan.
6. Collect metrics.
7. Write hypotheses.
8. Run a controlled experiment (ONE variable).
9. Find the root cause.
10. Apply the fix.
11. Benchmark before and after (§1.4).
12. Check correctness.
13. Document the trade-offs.
14. Write a production recommendation, using the incident report (§1.3).

### 0.5 Forbidden
- Changing 10 configs at once.
- Saying "AQE should fix it", "broadcast is faster" or "repartition improves performance" without proof and explanation.
- Optimizing without a baseline.
- Using runtime as the only metric.
- Concluding from one run ("it was faster once").
- Fixing every memory problem by adding memory.
- Accepting a faster query that changes the result. That is **not** an optimization.

---

## 1. Methodology toolkit
Every module (§5) and lab (§7–§10) uses these tools.

### 1.1 Diagnostic template (30 questions)
1. What is slow?
2. Where is it slow?
3. Which stage?
4. Which operator?
5. Which task?
6. What metric differs?
7–20. Is it CPU, memory, GC, disk, network, shuffle, input, output, metadata, scheduler, driver, object store, Python or JVM?
21–30. Is it data skew, cardinality explosion, bad statistics, the wrong join, wrong partitioning, wrong file layout, the wrong Iceberg distribution, wrong resource sizing, the wrong configuration, or the wrong algorithm?

Always finish with three more questions: **Which exact change should be tested? Did it actually improve the job? Can you prove it with metrics?**

### 1.2 Experiment protocol
```
BASELINE     runtime / shuffle / spill / CPU / network / files / cost = measured
HYPOTHESIS   e.g. "the bottleneck is an excessive shuffle partition count"
CHANGE ONE VARIABLE → RUN → MEASURE → COMPARE → ACCEPT / REJECT
ONLY THEN move to the next variable.
```

### 1.3 Production incident report
```
INCIDENT        Symptom / Impact / Detection
EVIDENCE        Spark UI / Physical plan / Metrics / Logs
HYPOTHESES      accepted + REJECTED (with the evidence that rejected them)
ROOT CAUSE
FIX
BENCHMARK       Before / After (table §1.5), n runs, variance
CORRECTNESS     row count, checksum, sample diff
COST            $ / vCPU-h before vs after
REGRESSION      test added, threshold
ROLLOUT         production recommendation + when this fix becomes harmful
```

### 1.4 Benchmarking science
- **Keep constant:** same input, same cluster, same data layout, same cache state.
- **Runs:** warm-up, then at least 3 repeated runs (5 for small effects). Report median, p95 and variance. Do an A/B comparison with controlled variables.
- **Record:** configuration (Environment tab dump), Spark/Iceberg versions, dataset size, input rows, output rows, runtime, CPU, shuffle, spill, task distribution, cost, throughput, latency, resource utilization.
- **Between runs:** clear caches (fresh session, `spark.catalog.clearCache()`; watch the OS page cache in local mode).
- **Row counts per operator:** capture them with `DataFrame.observe()` or SQL metrics, not with extra `count()` actions, which change the DAG.

### 1.5 Benchmark table (mandatory)
| Version | Runtime (median / p95) | Stage runtime | Input | Output | Shuffle R | Shuffle W | Spill (mem / disk) | GC % | Peak mem | Tasks | Failed tasks | Max task | Median task | p95 task | Max/median | Files | Avg file size | Cost |

### 1.6 Configuration experiment record
For each tuning parameter, record:
- parameter
- default for your version
- current value
- **origin**: Spark default, cluster/EMR/Glue default, `spark-submit`, session config, SQL `SET`, or application code
- reason
- expected effect
- observed effect
- regression risk

Banned reasoning: "I raise the value because it should be faster."

**Lab:** run the same application with config set at several levels, then determine where each effective value came from.

### 1.7 Automated performance regression suite
For each workload, version-control:
- input dataset, query, Spark version, configuration
- expected runtime, shuffle, spill, output, correctness checksum

Run baseline vs optimized automatically and fail above a threshold.

Re-run the suite to catch regressions from: Spark version, Iceberg version, connector, data growth, schema evolution, partition evolution, file layout. Keep a historical baseline.

---

## 2. Environment, scale ladder, budget

### 2.1 Environments
| Env | Use |
|---|---|
| Local Docker (Spark 4.x + Iceberg REST catalog + MinIO) | Levels 1–2, plan/Catalyst labs, correctness, fast iteration |
| EMR on EC2 (Spark 3.5) | Levels 3–7, S3, EMRFS, S3-optimized committer |
| EMR Serverless / Glue 5.0 (Spark 3.5) | Cloud runtime comparison (M17) |
| Spark on Kubernetes (EKS or kind) | M23, dynamic allocation with shuffle tracking |

**Version policy:** run each lab on Spark 4.x (current docs: 4.2.0; Java 17/21, Scala 2.13) and, for cloud parity, Spark 3.5. Note every behaviour difference (e.g. `spark.sql.ansi.enabled` is on by default since 4.0). Pin and record one Iceberg 1.x version per lab (current docs: 1.12.0). Read the SQL migration guide for known correctness bugs in your exact release (e.g. the DSv2 `PartitionPredicate` bug in 4.2.0).

### 2.2 Scale ladder
| Level | Size |
|---|---|
| L1 | 1–10 GB |
| L2 | 10–50 GB |
| L3 | 50–100 GB |
| L4 | 100–250 GB |
| L5 | 250–500 GB |
| L6 | 500 GB–1 TB |
| L7 | multi-TB, only when justified |

The scale must be large enough for the symptom to appear: skew, shuffle, spill, GC, network saturation, file discovery, small files, partition explosion, executor imbalance, driver pressure, metadata pressure.

### 2.3 Cost guard-rails
- Run in us-east-1, where most public datasets live; cross-region egress is charged.
- Set an AWS Budget alarm, tag every resource, use EMR auto-terminate.
- Landsat is **requester-pays**.
- Copy each subset into your own bucket once, convert it to Parquet, and reuse it.
- Run explosion labs (§7 labs 04 and 21, M15) on a sample first. Compute the expected output **before** running at scale.

---

## 3. Datasets

| Dataset | Location | Format / real columns | Use for | Pitfalls |
|---|---|---|---|---|
| **NYC TLC** (yellow / green / FHV / FHVHV) | `https://d37ci6vzurychx.cloudfront.net/trip-data/…parquet` (TLC site; registry entry `nyc-tlc-trip-records-pds`) | Parquet: `VendorID, tpep_pickup_datetime, tpep_dropoff_datetime, PULocationID, DOLocationID, fare_amount, tip_amount, total_amount…`. Zone lookup CSV has 265 rows (`LocationID, Borough, Zone`). | Joins, skew, aggregation, windows, partitioning, global sort, small files, cardinality, large scans, cache, UDF, Iceberg | Green taxi uses `lpep_` prefixes. Types drift across years, so read with an explicit schema. Reach 100–500 GB by adding FHVHV and a synthetic scale-up (replicate with key offsets and a `copy_id`). |
| **NOAA NEXRAD L2** | `s3://unidata-nexrad-level2/` | Binary radar volumes, path `YYYY/MM/DD/STATION/…` | Huge file counts, file listing / discovery, small files, large scans, object-storage behaviour, semi-structured paths | Not tabular. Read `format("binaryFile")` and select only `path, length, modificationTime` (the `content` column is pruned). Derive columns from the path. |
| **NOAA GOES** | `s3://noaa-goes16/`, `noaa-goes18/`, `noaa-goes19/` | NetCDF objects, key = product/year/day-of-year/hour | Huge data, object storage, file parallelism, large scans, partitioning | Not natively readable. Derive `product, date, hour, channel` from object keys into a Parquet file-catalog table. |
| **USGS Landsat** | `s3://usgs-landsat/` (STAC) | STAC JSON: `id, properties.datetime, properties."eo:cloud_cover", geometry, assets` | Large data, geographic distribution, nested JSON, file layout, object storage, partitioning | Requester-pays. Ingest the STAC JSON once. |
| **OpenStreetMap** | `s3://osm-pds/planet/planet-latest.orc` | ORC: `id, type (node/way/relation), tags MAP<string,string>, lat, lon, nds ARRAY<STRUCT<ref>>, members ARRAY<STRUCT<type,ref,role>>` | Nested data, geographic keys, graph-like joins, explode, large scans | Nodes, ways and relations share one table, so filter on `type`. Ways→nodes needs `explode(nds)`. |
| **Common Crawl** (columnar index) | `s3://commoncrawl/cc-index/table/cc-main/warc/` (authenticated S3) | Parquet: `url, url_host_name, url_host_registered_domain, url_host_tld, fetch_status, content_mime_type, content_languages, warc_record_length, crawl, subset` | Massive data, huge file counts, metadata/file discovery, text processing, natural domain skew, partitioning, large scans | Partitioned by `crawl` / `subset`; prune on them. |
| **Apache Iceberg tables** (built from the above) | your catalog | — | Small files, snapshots, manifests, deletes, MERGE, partition evolution, distribution-mode, write performance | — |
| **Synthetic & pathological** (seeded generators) | your code | Realistic logs, user events, transactions, IoT, clickstream, Kafka streams | Controlled pathologies | Distributions: uniform, **Zipf**, hot keys, long tail, null-heavy, high / low cardinality. File shapes: many tiny files, few huge files, mixed file sizes. Partition imbalance, wide rows, arrays of arrays. |

**Skew-injection pattern.** Always materialize it: `rand()` is non-deterministic, so a retry or a cache eviction would re-assign the keys.
```python
skewed = trips.withColumn("k", F.when(F.rand(42) < 0.90, F.lit(1)).otherwise(F.col("PULocationID")))
skewed.write.mode("overwrite").parquet(f"{BASE}/trips_skewed")   # then re-read
```

---

## 4. Program roadmap

| Phase | Modules | Target level (§11.3) | Indicative time* |
|---|---|---|---|
| P1 Foundations | M01–M04 | L2 → L3 | 6 wks |
| P2 Execution engines | M05–M11 | L3 → L4 | 10 wks |
| P3 Data, memory, storage & cloud | M12–M17 | L4 → L5 | 8 wks |
| P4 Iceberg | M18–M20 | L5 | 7 wks |
| P5 Streaming & infrastructure | M21–M23 | L5 | 4 wks |
| P6 Reliability, correctness, internals | M24–M29 | L5 → L6 | 4 wks |
| P7 Proof | §8 combined, §9 incidents, §10 capstones | L6 → L7 | 6 wks+ |

\* About 10 h/week. The 30 core labs (§7) run **inside** their modules; each module lists its labs.

**Gate to the next phase:** module labs done with incident reports (§1.3), and the module's §11 items ticked without notes.

---

## 5. Modules
> Format: **Topics → Labs → Must answer.** AQE is a cross-cutting module (M29) exercised in M05–M11.

### P1 — FOUNDATIONS

#### M01 Execution model
**Topics:**
- Spark application lifecycle; SparkContext / SparkSession; local vs cluster execution.
- Driver, executors, executor cores, executor memory and memory overhead, driver memory.
- Jobs, stages, tasks, DAG; job, stage and task generation; stage reuse.
- Narrow vs wide transformations, shuffle boundaries.
- Lazy evaluation and actions; lineage, recomputation, `checkpoint` / `localCheckpoint`.
- Spark Connect (client/server) and its impact on driver-side diagnostics.

**Lab:** reconstruct the complete execution graph of a real application from the UI, then confirm it against the code.

#### M02 Catalyst optimizer
**Topics:**
- Pipeline: SQL/DataFrame → unresolved (parsed) logical plan → analyzed → optimized → physical plan; `QueryExecution`.
- Catalyst rules and rule batches: predicate / filter pushdown, projection and column pruning, constant folding, null propagation, boolean and expression simplification, filter inference, subquery optimization, join reorder, aggregation optimization.
- Physical operator selection, Exchange insertion, operator compatibility.
- `explain("extended" | "formatted" | "cost" | "codegen")`.

**Lab:** take a complex SQL query and explain every Catalyst transformation from logical SQL to physical execution. Find the rule names with `spark.sql.planChangeLog.level=WARN`.

#### M03 Physical plan mastery
**Operators:**
- Scan / FileScan / Parquet scan / BatchScan (DSv2, Iceberg), Filter, Project.
- Exchange (`hashpartitioning`, `rangepartitioning`, `SinglePartition`, `RoundRobin`), repartition, Coalesce.
- HashAggregate, ObjectHashAggregate, SortAggregate (partial / final).
- Sort, Window, WindowGroupLimit.
- BroadcastHashJoin, SortMergeJoin, ShuffledHashJoin, BroadcastNestedLoopJoin, CartesianProduct.
- WholeStageCodegen, ReusedExchange, ReusedSubquery.
- AdaptiveSparkPlan, AQEShuffleRead (coalesced / skew-split / local reader modes).

**For each operator know:**
1. Why Spark generated it.
2. What data it moves.
3. Whether it shuffles.
4. Whether it can spill.
5. Whether it can bottleneck.
6. Which configuration affects it.

**For each Exchange ask:**
- Why is Spark shuffling?
- How much data?
- Why this partitioning?
- How many partitions?
- Is it necessary?
- Is it balanced?

**Lab:** given only EXPLAIN and the Spark UI, reconstruct the actually expensive operators.

#### M04 Spark UI forensics & observability
**Navigation:**
- Tabs: Jobs, Stages, Tasks, SQL, Storage, Executors, Environment.
- Event logs, History Server.
- Metrics: executor, task, stage, SQL, GC, shuffle, input/output.
- Prometheus, Grafana, application logs.

**Drill-down path:**
application → SQL query → job → stage → task → input/output → shuffle read/write → spill → GC → task duration → partition size.

**Identify:**
- The slowest SQL query, job, stage and task.
- Whether the problem is localized to one or a few tasks, or spread across all of them.
- Per task: input, output, shuffle read and write.
- Spill (memory and disk).
- Executor CPU time vs run time, GC time, peak execution memory.
- Failed, retried and speculative tasks.
- Task locality, scheduler delay, fetch wait, task deserialization, result serialization.
- Stage dependencies.
- Executor, GC, CPU, network and disk imbalance.
- The **first** abnormality.

**Skew drill-down:** which task is abnormal → how much data → which key/partition produced it → why it grew → which mitigation to test.

**Expert question:** "Why is Task 57 10× slower than Task 56?" Investigate skew, partition size, input file, shuffle data, spill, GC, CPU, network, remote I/O and bad key distribution.

**Post-mortem lab:** given only the event log, History Server and application config (no code), determine the slow stage, skew, shuffle, executor problem, GC, task imbalance and retries.

### P2 — EXECUTION ENGINES

#### M05 Partitioning
**APIs & configs:**
- `repartition()`, `repartition(n)`, `repartition(col)`, `repartition(n, col)`, `repartitionByRange()`, `coalesce()`, write-time `partitionBy()`.
- The `REBALANCE` hint (AQE-aware).
- `spark.sql.shuffle.partitions`, `spark.default.parallelism`, `spark.sql.files.minPartitionNum`.

**Concepts:**
- Partition, partition count, partition size, partition distribution.
- Logical vs physical partitioning; hash vs range partitioning.
- File / input / shuffle / output partitioning.

**Identities:**
- Input partitions ≠ shuffle partitions ≠ output files ≠ table partitions.
- Partition count ≠ data size; partition count ≠ file count.
- Spark partition ≠ Iceberg partition.

**Pathologies:**
- Too few or too many partitions.
- Empty, small or huge (oversized) partitions; underutilization.
- Partition skew; partition explosion.
- Task count vs CPU cores; over- vs under-parallelization.

**Labs:**
- Sweep 10 / 100 / 1,000 / 10,000 partitions. Measure task count, task duration, shuffle, scheduler and task overhead, CPU and I/O utilization, output files and runtime.
- Find the parallelism sweet spot (parallelism vs overhead) empirically.

Core labs 08 and 09.

#### M06 Shuffle
**Topics:**
- Map → shuffle write → shuffle storage (shuffle files, external shuffle service) → shuffle read → reduce; ShuffleMapStage; partitioner.
- Shuffle volume, partition count, block sizes, remote vs local bytes, network transfer, fetch wait, fetch failures.
- Shuffle compression; memory vs disk spill.
- Bottlenecks: network, disk, CPU.
- Excessive or unnecessary shuffle and shuffle amplification; skewed, huge, too many tiny, or too few shuffle partitions; exchange reuse; partition sizing.
- Push-based shuffle (YARN), remote shuffle service (Apache Celeborn) on Kubernetes, executor decommissioning with shuffle migration.

**Metrics for every shuffle lab:** total and per-task read/write, median and max task size, max/median ratio, spill, runtime.

**Labs:**
- **A.** Annotate every Exchange in a plan (Exchange #1 → why? #2 → why? …) and try to remove or reduce each one.
- **B.** Diagnose a 500 GB shuffle **without changing the code first**.

Core labs 01 and 08.

#### M07 Distribution & ordering requirements
**Topics:**
- Required distribution, required ordering.
- Child output partitioning, compatible partitioning, partitioning satisfaction.
- Partitioning vs distribution vs ordering.
- Why Spark needs Exchange + Sort, and when an existing ordering avoids work.
- Bucketing (`bucketBy`); Storage-Partitioned Join (Iceberg version in M19).

**Lab:** analyze a join, a window, a global sort and range partitioning. Remove one shuffle with bucketing or SPJ.

#### M08 Joins
**Strategies:** BroadcastHashJoin, SortMergeJoin, ShuffledHashJoin, BroadcastNestedLoopJoin (why it appears, why it is expensive, how it differs from BHJ), CartesianProduct (accidental cross join, N × M).

**Selection:**
- Join strategy selection; statistics; join hints (`BROADCAST`, `MERGE`, `SHUFFLE_HASH`, `SHUFFLE_REPLICATE_NL`).
- Broadcast threshold (`autoBroadcastJoinThreshold`, `spark.sql.adaptive.autoBroadcastJoinThreshold`); join build side; AQE join conversion and runtime statistics.

**Broadcast lifecycle:** build relation → collect to driver → distribute → executor memory. Diagnose broadcast creation, transfer, memory, timeout, oversized broadcast and broadcast failure.

**Data:**
- Join key distribution and cardinality, selectivity.
- Estimated vs actual rows (estimation error contaminates planner decisions).
- Join ordering, multi-way joins.
- Many-to-many joins, accidental many-to-many, duplicate keys, join explosion, skewed joins.
- NULL semantics: null-safe equality `<=>`, NULL filtering, three-valued logic. An optimization must not change semantics.

**Techniques:** salting, pre-aggregation, filtering and column pruning before the join.

**Method:** estimate input cardinality → estimate output cardinality → inspect key distribution → read the plan → measure the shuffle → test one alternative strategy.

**Labs:**
1. Small + large.
2. Large + large (100 GB × 5 GB).
3. The same join with incorrect or corrupted statistics.
4. Many-to-many explosion.
5. Hidden duplicate key.
6. Broadcast failure.
7. A join skewed on one hot key.
8. Skew + many-to-many.
9. A scenario where Spark chooses BNLJ.
10. A deliberate cross join: compute N × M growth.

Core labs 01–04 and 17.

#### M09 Data skew
**Taxonomy:** random distribution, moderate, severe, single hot key, multiple hot keys; partition / join / aggregation / window / write skew.

**Detection:**
- Spark UI: task duration, input size, shuffle read/write, spill and CPU-time distributions.
- Key frequency analysis, top-N keys, frequency histogram, approximate frequency (`approx_count_distinct`, sampling).
- Partition size, SQL plan, AQE information.

**Distinguish:** skew vs straggler vs slow executor vs bad locality vs GC vs network.

**Find:** exact key → exact partition → exact task → exact stage.

**Mitigations:**
- Salting (and the replication cost on the other side).
- Partial aggregation, pre-aggregation, two-stage aggregation.
- Broadcast; filtering; repartitioning.
- Better key selection; splitting hot keys (manual skew splitting + union).
- AQE skew join (`skewedPartitionFactor`, `skewedPartitionThresholdInBytes`); alternative join strategies.

**Method:** detect → identify the exact key → quantify (max/median) → mitigate → re-benchmark.

**Lab:** from the Spark UI, identify the EXACT key responsible for the huge task.

Core labs 03, 05, 06, 15 and 18.

#### M10 Aggregation internals
**Topics:**
- Partial / map-side aggregation → shuffle → final aggregation; aggregation buffer and state.
- HashAggregate vs ObjectHashAggregate vs SortAggregate: why Spark picks each, memory, sort fallback, spill, performance.
- Low / high / skewed-cardinality `groupBy`.
- Distinct aggregation, `count(distinct)` (Expand), `approx_count_distinct`, multiple aggregations, aggregation memory and spill, aggregation pushdown.

**Key insight:** partial aggregation neutralizes hot-key skew for decomposable aggregates (`count`, `sum`, `min`, `max`). See core lab 05.

**Labs:**
- A 250 GB `groupBy` with pathological cardinality.
- Compare low vs high vs skewed cardinality.
- Build datasets that trigger Hash vs Sort aggregation.

Core labs 05 and 19.

#### M11 Window functions & sorting
**Topics:**
- `partitionBy()` groups rows into window partitions; `orderBy()` orders rows inside each partition.
- Functions: `row_number`, `rank`, `dense_rank`, `lag`, `lead`, running and cumulative aggregates.
- Frames: ROWS vs RANGE; bounded vs unbounded.
- Pipeline: window partition → Sort → window computation.

**Pathologies:**
- Window skew, huge or giant window partitions.
- Global window (no `partitionBy` puts everything in one partition).
- Expensive or unnecessary ordering; multiple window functions; memory pressure; spill.

**Alternatives:** WindowGroupLimit for top-N, `max_by` / `min_by`.

**Global sort:** `orderBy()` (range exchange + sampling, global shuffle) vs `sortWithinPartitions()`.

**Labs:**
- Normal distribution vs hot partition vs huge window partition.
- Find why one window partition takes 100× longer than the others.

Core labs 06 and 07.

### P3 — DATA, MEMORY, STORAGE & CLOUD

#### M12 Python / JVM boundary & serialization
**Execution paths to compare:** JVM/native Spark SQL expressions, Scala, PySpark DataFrame, RDD operations, Python UDF, Arrow-optimized Python UDF (`useArrow=True`), Pandas UDF, iterator Pandas UDF, `mapInArrow`, Python UDTF, Python Data Source API.

**Overheads:**
- JVM ↔ Python serialization, pickling vs Arrow, Arrow batch size and Arrow overhead.
- Python worker CPU and memory.
- Deserialization, object allocation, GC.
- Java vs Kryo serialization.

**Lab:** implement identical logic as native, Python UDF, Arrow UDF and Pandas UDF on tens or hundreds of GB. Explain the differences from the Spark UI and executor metrics. **Measure rather than assume.**

Core labs 20 and 25.

#### M13 JVM, memory & code generation
**Memory:**
- Executor heap, JVM heap, off-heap.
- Unified memory: execution vs storage memory.
- Memory overhead, serialization memory, Python worker memory.
- Cached data, broadcast memory.

**GC & objects:**
- GC: young / old, pauses, allocation rate.
- Object overhead, huge rows.
- Serialized vs deserialized storage; Tungsten / UnsafeRow; fragmentation.

**Diagnose:**
- Executor OOM, container killed (YARN / K8s exit 137), executor lost, driver OOM.
- GC pressure / overhead, excessive spill.
- Oversized broadcast, cache or partition.
- `collect()` / `toPandas()`.

**Code generation:**
- Whole-stage codegen, generated Java code (`explain("codegen")`), codegen boundaries and fallbacks, interpreted execution.
- Expression evaluation, vectorized Parquet, batch processing, CPU cache behaviour, expensive SQL functions.

**Native accelerators:** Apache Gluten + Velox, DataFusion Comet, and how JVM fallback cancels their benefit.

**Labs:**
- Distinguish real data pressure vs GC problem vs Python memory vs broadcast memory vs driver metadata problem.
- Find a CPU bottleneck where the plan looks superficially correct.

Core labs 23 and 24.

#### M14 Cache & persistence
**Lineage:** source → transformation → transformation → action. Multiple actions recompute the lineage unless the intermediate result is persisted.

**Topics:**
- `cache()`, `persist()`, storage levels (MEMORY_ONLY, MEMORY_AND_DISK, `_SER`, DISK_ONLY), `unpersist()`.
- Cache hit / miss, eviction, cache serialization, storage memory.
- Lineage duplication; cache + multiple actions / joins / windows.
- Oversized cache; cache vs recomputation; caching correctness.

**Lab:** `df → transformation A → transformation B → actions 1..5`. Compare no cache vs `cache()` vs `persist()` at several storage levels. Measure number of jobs, recomputation, input read, CPU, memory and runtime. Determine whether caching actually wins, and find a case where it makes things **worse**.

Core labs 22 and 23.

#### M15 Nested / semi-structured data & cardinality explosion
**Nested data:**
- StructType, ArrayType, MapType; nested column access; nested field pruning.
- `explode`, `explode_outer`, `posexplode`, `inline`.
- `from_json`, `to_json`, schema inference, malformed JSON (`mode`, corrupt-record column).
- JSON string vs native StructType vs VARIANT (`parse_json`, `variant_get`).
- Arrays of arrays, map explosion, flattening strategy.
- Measure parsing CPU, row explosion, memory and serialization.

**Cardinality:** input rows → transformation → output rows. Always compute input cardinality, output cardinality and the expansion factor `output_rows / input_rows`. You must know **where** the volume exploded. Example: 100 GB × 10 expansion = 1 TB of logical output.

**Sources of explosion:** explode, nested arrays, crossJoin, many-to-many join, duplicate keys or multiplication, bad join conditions, window explosion, distinct or aggregation after explosion.

**Fixes:** early filtering, pre-aggregation.

**Labs:**
- A 100 GB JSON workload where a naive explode causes a cardinality explosion.
- Start from 100 GB, accidentally produce multiple TB of intermediate data, then diagnose and redesign.

Core labs 16, 21 and 26.

#### M16 File formats, Parquet internals & data skipping
**Formats:** Parquet, ORC, JSON, CSV, Avro (Iceberg in M18–M20).

**Parquet internals:**
- File → row groups → column chunks → pages.
- Encodings: dictionary, RLE.
- Min/max and null statistics, bloom filters, file metadata.
- Vectorized reader, batch size; row-group and page sizing.
- Schema, schema evolution, nested structures.

**Compression:** Snappy, ZSTD, GZIP, LZ4. Measure separately: write CPU, write size, read CPU, read throughput, storage footprint, compression ratio. Don't conclude from runtime alone.

**Data skipping:**
- Distinguish partition pruning, file pruning, row-group skipping, column pruning and predicate pushdown.
- Dynamic partition pruning; runtime filters.
- Data clustering, sort order, clustering quality.

**Bloom filters:** test them separately from min/max. Consider false positives, lookup-oriented filtering, column selection, write cost vs read cost. Run OFF vs ON.

**File size:** write 1 MB / 10 MB / 128 MB / 512 MB / 1 GB files. Measure planning, task count, I/O, throughput, parallelism and metadata overhead. Pick the size for **the workload**; there is no universal value.

**Labs:**
- CSV → Parquet, JSON → Parquet; different compressions and file sizes; predicate filtering.
- Large vs small files; wide schema vs narrow projection; full scan vs predicate pushdown.
- The same logical dataset in different Parquet layouts: measure read CPU, bytes read, scan time and storage.
- 1 TB logical with only 10 GB actually read, verified in the Spark UI.
- Make the same 500 GB dataset take dramatically different scan times through physical layout alone.

Core labs 13 and 14.

#### M17 File source, small files, S3 & cloud runtime
**Read parallelism:**
- `spark.sql.files.maxPartitionBytes`, `openCostInBytes`; file splitting and split calculation.
- Small, giant and mixed files.
- File listing, parallel listing, driver-side file discovery.
- Task explosion; excessive vs insufficient read parallelism.

**Small-file masterclass:**
- **Where small files come from:** small input files, small output files, small Iceberg data files, small delete files, small manifests.
- **Related explosions:** snapshot explosion, excessive partitions, excessive task count, object-store request explosion.
- **Fixes:** repartition / coalesce / REBALANCE before write, target file size, distribution mode, fanout (M19), compaction, Iceberg `rewrite_data_files`.
- **Measure:** file count; average, median, smallest and largest file size; input partitions; task count; listing, planning and scan time; driver overhead; S3 request pressure.
- **Reproduce the chain:** 1 large dataset → 100,000+ output files → read → many input partitions → many tasks → scheduling, metadata and S3 overhead.

**S3 / object storage:**
- Request model: GET, HEAD, LIST.
- Request concurrency, executor concurrency, HTTP connection pools (`fs.s3a.connection.maximum`, EMRFS max connections), connection-pool exhaustion.
- Retries, timeouts, throttling (503 SlowDown, per-prefix limits), transient failures.
- Latency, slow objects, remote I/O, network throughput, multipart operations.
- Object count, prefix distribution.
- S3 is strongly consistent; committers exist for rename-free atomic output. Know FileOutputCommitter v1 / v2, the **EMRFS S3-optimized committer** (EMR) and the **S3A magic committer** (Hadoop).

**Cloud runtime (EMR, Glue, EMR Serverless, Iceberg on S3):**
- Executor and worker sizing, vCPU, memory, memory overhead.
- Autoscaling, dynamic allocation, startup latency.
- Shuffle storage, network bottlenecks, connection pools.
- Cloud-specific defaults, Graviton, cost vs runtime.

**Labs:**
- 1M tiny files vs 100k vs 10k vs 1k large files: compare read time, planning time, task count, driver overhead and S3/HTTP activity.
- Create 1 million tiny files and compare several discovery and read strategies.
- MANY FILES → MANY TASKS → MANY SIMULTANEOUS S3 REQUESTS → connection / throughput pressure.
- Spark reads 500 GB successfully but performs terribly because of object-store request pressure, not CPU.
- The same application on two AWS execution models: explain the performance and cost differences.

Core labs 10–12 and 27.

### P4 — ICEBERG

#### M18 Iceberg architecture & read path
**Architecture:**
- Iceberg table, catalog → `metadata.json` (metadata files) → manifest list → manifests → data files / delete files.
- Snapshots, sequence numbers, snapshot isolation, time travel, branches, tags.
- Partition specs, transforms, hidden partitioning, partition evolution, schema evolution, sort order.
- Format v3: deletion vectors, row lineage, VARIANT, default values. Check your table's `format-version`.

**Read path:**
- Pruning: manifest, partition and file pruning; column statistics; Puffin statistics; vectorization.
- Split planning: `read.split.target-size`, `read.split.open-file-cost`, `read.split.planning-lookback`, `read.split.adaptive-size.enabled`.
- `read.data-planning-mode` and `read.delete-planning-mode` (AUTO / LOCAL / DISTRIBUTED); delete-file planning; executor cache; async micro-batch planning.
- Data-grouping preservation (`spark.sql.iceberg.planning.preserve-data-grouping`) → Storage-Partitioned Join.

**Metadata statistics:**
- `write.metadata.metrics.default` (none / counts / truncate / full), per-column metrics.
- Min/max usefulness, statistics quality vs cost, metadata size, query pruning.

**Diagnostic tool:** the metadata tables `.files`, `.manifests`, `.snapshots`, `.partitions`, `.all_delete_files`.

**Lab:** an Iceberg table with millions of files. Separate the metadata bottleneck, planning bottleneck, file-read bottleneck and delete-file bottleneck.

#### M19 Iceberg write path: distribution, file size, fanout, sort order
**Pipeline:**
input → Spark transformations → Exchange / distribution → Spark partitions / tasks → Iceberg writer (DataSource V2) → task output → Iceberg partition boundary → file rolling → data files → manifest generation → snapshot commit.

Spark partition, Iceberg partition and output file are **three different concepts**.

**Writes:** INSERT, INSERT OVERWRITE, dynamic overwrite, UPDATE, DELETE, MERGE INTO (row-level ops in M20).

**Distribution mode (`write.distribution-mode`):**
- `hash`: a hash exchange on partition values.
- `range`: sampling + a range exchange; gives global ordering and clustering at extra cost.
- `none`: no automatic distribution. You manage clustering yourself, or accept the file-handle and small-file consequences.
- Default (verified, Iceberg docs): since Iceberg 1.2.0 the Spark writer requests `hash` by default; `range` is used by default when the table has a sort order; `none` was the pre-1.2 default. Spark ignores distribution mode in CTAS/RTAS before Spark 3.5.0.
- Related defaults: `write.delete.mode` / `write.update.mode` / `write.merge.mode` = `copy-on-write`; `write.delete.granularity` = `partition` (check your version); `format-version` = 2 since Iceberg 1.4.0.
- Separate settings: `write.delete.distribution-mode`, `write.update.distribution-mode`, `write.merge.distribution-mode`.

**File size:**
- `write.target-file-size-bytes` is a **target, not a guarantee**.
- A file can never be larger than its Spark task and never crosses an Iceberg partition boundary.
- Spark's in-memory task size ≠ compressed on-disk Parquet size: a 100 MB task does not give a 100 MB file.
- Multiple Iceberg partitions inside one task produce several smaller files per task. Distinguish task-level from partition-level file creation; tiny output files; write amplification.
- Tune with `spark.sql.adaptive.advisoryPartitionSizeInBytes` and AQE coalescing.

**Fanout (`write.spark.fanout.enabled`):** removes the need for clustered input, at the cost of more open file handles and executor memory. Trade-offs: partition cardinality, small files, memory pressure, fanout vs distribution.

**Sort order:** `WRITE ORDERED BY` / `LOCALLY ORDERED BY`; range distribution; clustering; read locality; data skipping; write cost vs read benefit.

**Object storage:** `write.object-storage.enabled` gives hashed object paths instead of partitioned paths, spreading S3 requests and improving object-store scalability.

**Labs:**
- **19.1 `none`:** measure stages, Exchange operators, shuffle R/W, task duration and input, output files and sizes, partition distribution.
- **19.2 `hash` (same dataset):** compare to `none` on shuffle, task count, task balance, write duration, file count and sizes, partition distribution.
- **19.3 `range`:** compare all three modes. When is range useful, and what extra sorting/distribution work does it add?
- **19.4 Iceberg partition skew:** 90–95% of records in one partition value. Observe Spark partition, task-duration, shuffle, output-file and Iceberg-partition distributions.
- **19.5 Distribution + skew:** run `none` / `hash` / `range` and find the largest, smallest, median, p95 and p99 task. Find where the bottleneck occurs. Never say "hash is better"; prove it with the UI, plan, metrics and file statistics.
- **19.6 Distribution + small files:** many Spark partitions + many Iceberg partitions + little input. Observe task count, Iceberg file count, average file size, partition distribution and write duration. Then vary Spark partition count, distribution mode and Iceberg write settings **each independently**.
- **19.7 Distribution + partition spec:** `days(ts)`, `months(ts)`, `bucket(N, id)`, `identity(country)` × each mode. Measure shuffle, task balance, output files, file sizes and write time.
- **19.8 Distribution + overwrite:** INSERT vs INSERT OVERWRITE vs dynamic overwrite. Investigate scan, filter, shuffle, distribution, affected partitions and rewritten files.
- **19.9 Distribution + MERGE:** target scan, source scan, join, shuffle, distribution, data-file rewrite, delete files, output files. Connect the Spark plan to the table changes.
- **19.10 Fanout:** hash vs range vs none + fanout. Measure runtime, shuffle, files, average file size, executor memory and commit time.
- **19.11 Blind slow Iceberg write:** the cause could be skew, small files, bad partitioning, excessive shuffle, distribution, too many or too few Spark partitions, expensive MERGE, delete files, metadata or object-store I/O. Diagnose via Spark UI → physical plan → task distribution → shuffle metrics → Iceberg metadata → data-file statistics → root cause.

#### M20 Iceberg row-level operations, maintenance, concurrency
**Row-level operations:**
- DELETE, UPDATE, MERGE INTO.
- Copy-on-write (default) vs merge-on-read (`write.delete.mode`, `write.update.mode`, `write.merge.mode`).
- Position deletes, equality deletes, v3 deletion vectors.
- Delete granularity (`write.delete.granularity`: file / partition); file-level vs partition-level deletes.
- Delete-file accumulation; read amplification; write and rewrite amplification.
- Distribution mode for delete, update and merge.

**Maintenance:**
- `expire_snapshots`, `remove_orphan_files`.
- `rewrite_data_files` (compaction of small files; binpack / sort / zorder), delete-file compaction (`rewrite_position_delete_files`), `rewrite_manifests`.
- Metadata cleanup, metadata growth, manifest explosion, snapshot explosion.
- Streaming append metadata, commit frequency, maintenance scheduling.

**Concurrency:**
- Optimistic concurrency, commit conflicts, conflicting snapshots, retry strategy.
- Snapshot vs serializable isolation.
- Concurrent append, overwrite and MERGE.

**Diagnose:** small files, metadata explosion, snapshot explosion, delete files, rewrite amplification, partition problems, write skew, read planning, partition evolution.

**Labs:** Iceberg small files, too many snapshots, too many manifests, frequent appends, DELETE, MERGE, file rewrite, partition evolution, read planning.

Core labs 28–30.

### P5 — STREAMING & INFRASTRUCTURE

#### M21 Structured Streaming
**Topics:**
- Micro-batches, triggers (including `availableNow`), checkpointing, offsets.
- State and the state store (RocksDB, changelog checkpointing); state growth, state skew.
- Watermark, late data.
- Stream-stream joins, streaming aggregations, output modes.
- Exactly-once semantics, idempotency.
- Backpressure (`maxOffsetsPerTrigger`), throughput vs latency.
- `transformWithState` and the State Data Source reader.
- Kafka → Spark → Iceberg (commit interval vs small files and snapshots).

**Lab:** build a streaming pipeline, intentionally create a state explosion, then bound it.

#### M22 Kafka, connectors, DataSource V2, catalogs, JDBC
**Kafka:**
- Partitions, consumer parallelism (`minPartitions`), batch and fetch size, offset management.
- Partition and producer skew, serialization, compression, lag, throughput.
- Spark micro-batch scheduling.

**Connectors:** JDBC, Kafka, REST/API, cloud storage, databases. Separate a connector bottleneck from a Spark bottleneck.

**DataSource V2:** scan planning, batch scan, partition readers, write builders, commit protocol, pushdown, column pruning, partitioning and ordering reporting, connector behaviour.

**Catalogs:** Spark catalog, Iceberg catalog, REST / Hive / Glue catalogs; catalog latency, metadata consistency, namespace behaviour, table resolution.

**JDBC:**
- `partitionColumn`, `lowerBound`, `upperBound`, `numPartitions`, `fetchsize`.
- Predicate and aggregate pushdown, column pruning, parallel JDBC reads.
- Connection count, database parallelism and pressure, transaction behaviour, source overload, incremental extraction.
- A faster Spark job does **not** mean a healthier database.

**Database pushdown:** Spark → connector → database. Determine which operations run in the database and which in Spark.

**Labs:**
- 1 JDBC connection vs parallel JDBC reads.
- Extract 500 GB from a database without destroying the source system.

#### M23 Kubernetes, dynamic allocation, scheduler, speculation
**Kubernetes:** driver pod, executor pods, pod scheduling, CPU and memory requests and limits, shuffle on local storage, dynamic allocation, executor lifecycle, locality, pod startup overhead.

**Dynamic allocation:** executor idle timeout, allocation ratio, initial / min / max executors, shuffle tracking, executor removal, startup latency, workload burstiness, cost/performance.

**Scheduler:** FIFO, FAIR, scheduler pools; locality levels PROCESS_LOCAL / NODE_LOCAL / NO_PREF / RACK_LOCAL / ANY; `spark.locality.wait`; executor placement; interaction with dynamic allocation.

**Speculation & stragglers:** speculation, straggler detection, skew vs straggler; slow node, noisy neighbour, GC / network / disk stragglers, cloud instance variability.

**Labs:**
- Fixed executors vs dynamic allocation on a bursty workload.
- A workload whose performance is dominated by scheduling or locality.
- Decide whether speculation helps or hides the real problem.

### P6 — RELIABILITY, CORRECTNESS, INTERNALS

#### M24 Driver performance
**Topics:**
- `collect`, `collectAsList`, `toPandas`, `spark.driver.maxResultSize`, large result serialization.
- Driver CPU, memory and GC; query planning, large query plans.
- File listing pressure, metadata handling.
- Broadcast creation and preparation.
- Task scheduling, task metadata, huge task descriptions.

**Lab:** an application where executors are fast or idle but the driver is the bottleneck.

Core lab 24.

#### M25 Bottleneck classification, backpressure, latency decomposition
**Classify every job as:** CPU-, memory-, network-, disk-, I/O-, metadata-, scheduler-, object-store-, driver-, executor-, Python- or JVM-bound. Prove it with metrics.

**Backpressure across layers:** S3 → Spark → shuffle → executor → Iceberg. A slow layer can make another layer *look* saturated. Find the real limiting layer.

**Latency decomposition:**
total runtime = planning + scheduling + scan + shuffle + compute + write + commit, with a number for each. Never just say "the job takes 2 hours".

#### M26 Production failures, reliability & fault injection
**Inject and diagnose:**
- Kill an executor; kill the driver; executor lost.
- Network delay or failures; disk pressure.
- Corrupted input, missing file, schema mismatch, malformed data.
- Transient S3 failure, throttling, connection-pool exhaustion.
- Executor OOM, driver OOM.
- Failed tasks, task and stage retries, fetch failures, shuffle failures.
- Long-running tasks, speculative-execution problems.
- Commit failure, Iceberg commit conflict.

**For each:** symptom → Spark UI / logs evidence → root cause → corrective action → re-run → verification.

#### M27 Correctness vs performance & semantics
**Correctness hazards:**
- Duplicate rows, lost rows, incorrect joins.
- NULL semantics; timestamp semantics and time zones.
- Decimal precision, floating point.
- Approximate algorithms, non-deterministic functions (`rand`, `monotonically_increasing_id` under retries).
- Ordering assumptions, partition assumptions.
- Caching correctness, streaming exactly-once.

**ANSI mode:** on by default in Spark 4. Covers casts, overflow, invalid operations, `try_*` functions, malformed data, and permissive vs strict behaviour.

**Rule:** a 50% faster query that changes the result is NOT an optimization.

#### M28 CBO, advanced SQL, version migration, source-code reading
**CBO / statistics:**
- Table and column statistics, row count, data size, NDV, histograms.
- Cardinality estimation, selectivity, optimizer cost model, join order.
- Stale or missing statistics, `ANALYZE TABLE … FOR COLUMNS`.
- Static statistics vs runtime statistics; wrong plans caused by wrong stats.
- **Lab:** make a correct query slow by deliberately poisoning optimizer information.

**Advanced SQL:**
- Correlated and scalar subqueries; EXISTS, IN (NOT IN null trap); semi and anti joins.
- UNION, INTERSECT, EXCEPT, DISTINCT.
- GROUPING SETS, ROLLUP, CUBE; recursive-like transformations.

**Version migration (3.5 → 4.x):**
- Catalyst, AQE and default changes; SQL behaviour and ANSI changes.
- Connector, Iceberg, Java and Scala compatibility.
- Regression testing (§1.7).

**Spark source-code reading:**
- Catalyst, SQL execution (`QueryExecution`, `EnsureRequirements`), Exchange, joins (`JoinSelection`).
- Aggregation, AQE (`AdaptiveSparkPlanExec`), scheduler (`DAGScheduler`), shuffle.
- File source (`FileSourceScanExec`), memory management (`UnifiedMemoryManager`).

**Iceberg spec / source reading:** planning, manifests, scans, writes, distribution, partitioning, deletes, commits, snapshots.

**Goal:** go from "Spark does this" to "I can explain where and why Spark makes this decision". Understand the system; don't just memorize properties.

#### M29 AQE (cross-cutting, exercised in M05–M11)
**Topics:**
- `spark.sql.adaptive.enabled`, AdaptiveSparkPlan, runtime statistics.
- Coalescing post-shuffle partitions: `coalescePartitions.enabled`, advisory partition size, min partition size.
- Skew join: `skewJoin.enabled`, skew thresholds, max partition size. Does **not** apply to aggregations or windows.
- Adaptive join selection / broadcast conversion; local shuffle reader; dynamic partition pruning.
- Interaction with repartition, Iceberg and writes; false assumptions about AQE.

**Lab:** run the same application with AQE OFF, ON, and ON + controlled parameters. Compare plans, task counts, runtimes, skew handling and partition sizes. Explain what changed in the plan, why Spark changed it, which stage and tasks changed, and how much shuffle and time changed. Do NOT blindly enable AQE.

---

## 6. Lab card template
```
ID / Module / Dataset + scale (§2.2) / Spark + Iceberg version
Bad baseline (code) → expected symptom
Evidence to collect (UI tab, plan operator, metric)
Hypotheses H1..Hn
Experiment (ONE variable, §1.2)
Fix + why it works physically + when it becomes harmful
Benchmark table (§1.5) + correctness check + cost → incident report (§1.3)
```

---

## 7. The 30 core production labs
> `BASE` = your bucket. `trips` = Yellow taxi with an explicit schema. `zones` = the 265-row lookup.
> Run every lab with AQE ON and OFF (M29).

| # | Lab | Module | Dataset | Bad baseline | Goals / fixes to test | Pitfalls |
|---|---|---|---|---|---|---|
| 01 | Shuffle JOIN | M08 | TLC | Set `spark.sql.autoBroadcastJoinThreshold=-1` (and the adaptive one), then `trips.join(zones, trips.PULocationID == zones.LocationID)`. Better: a large × large join (trips ⋈ trips of another month on a synthetic id). | Identify SMJ and the two `Exchange hashpartitioning`, shuffle R/W; compare join strategies; Spark UI diagnosis | Without disabling broadcast, the 265-row table is broadcast automatically. |
| 02 | Broadcast JOIN | M08 | TLC | `trips.join(F.broadcast(zones), …)`, then broadcast a multi-GB side | BHJ, threshold, hint, broadcast memory, broadcast failure, compare with shuffle join | Capture the timeout / OOM error. |
| 03 | JOIN skew | M09 | TLC | Materialized `trips_skewed` (§3, 90% `k=1`), broadcast disabled, `join(zones, k == LocationID)` | Abnormal task, exact hot key, normal vs skewed partitions, salting (replicate zones × N), AQE skew join | Materialize the `rand()` key. |
| 04 | Many-to-many / join explosion | M08/M15 | TLC | **First** compute `Σ_k count(k)²`. Then, on one day: `trips.select("PULocationID","tpep_pickup_datetime")` ⋈ `trips.select("PULocationID","tpep_dropoff_datetime")` on PULocationID | Detect duplicate keys, expected cardinality, output amplification, prevent accidental many-to-many | On full data the output is effectively unbounded. |
| 05 | Aggregation skew | M10 | TLC / CC | **A:** 95% `"HOT"` key + `groupBy("k").count()`. **B:** `groupBy("k").agg(F.collect_list("tpep_pickup_datetime"))` | A shows **no** skew (partial aggregation); B shows a huge reducer. Examine the partition distribution; salted two-stage aggregation; compare strategies. | Decomposable aggregates hide hot keys. |
| 06 | Window skew | M11 | TLC | `Window.partitionBy("PULocationID").orderBy("tpep_pickup_datetime")` + `row_number()` | Huge window partition, slow task, sort spill, alternative partitioning, top-N | AQE skew join does not help windows. |
| 07 | Global sort | M11 | TLC | `orderBy("tpep_pickup_datetime")` vs `sortWithinPartitions(...)` | Global shuffle, range exchange + sampling, plan comparison, shuffle cost | The two are not semantically equivalent. |
| 08 | Repartition / shuffle | M05/M06 | TLC | `repartition("PULocationID")`, then `explain("formatted")`; vs `repartition(n)`, `coalesce(n)`, `REBALANCE` | Understand the Exchange, shuffle cost, empty / uneven partitions | ~265 keys hashed into 200 partitions. |
| 09 | Partition explosion at write | M05/M17 | TLC | `write.partitionBy(<high-cardinality col>).parquet(out)` without repartitioning first | Thousands or millions of directories and files; small-file consequences. Fix: repartition by the partition column / REBALANCE, lower cardinality | `PULocationID` alone is mild; directories × tasks = files. |
| 10 | Small files | M17 | TLC → Parquet | `df.repartition(100_000).write.parquet(out)`, then `spark.read.parquet(out)` | Many files → many file partitions → many tasks; file listing; compare file sizes. Fix: repartition / coalesce before write | Build the small files from tabular data. |
| 11 | Excessive read parallelism | M17 | Lab 10 output, NEXRAD | `maxPartitionBytes` 16 MB vs 512 MB; `openCostInBytes` | Input partitions → tasks → S3 concurrency → throughput; connection pool | Tiny files are packed into one split up to maxPartitionBytes. |
| 12 | Massive file discovery / listing | M17/M24 | NEXRAD | `spark.read.format("binaryFile").option("recursiveFileLookup","true").load(<busy period>).select("path","length")` | File listing, driver-side discovery, planning, metadata overhead, input partitions, pruning | Select only metadata columns. |
| 13 | Partition pruning | M16 | GOES file catalog / TLC | Write `partitionBy("date","channel")`, then `filter(F.col("date") == "2024-01-01")`. Add a pruning-**failure** variant (function on the partition column) and a DPP variant. | Full vs pruned scan; verify `PartitionFilters` and files read | Derive GOES columns from object keys. |
| 14 | Large table scan | M16 | Landsat STAC → Parquet / scaled TLC | 100–500 GB `select("*")` + full aggregate vs a projection of `id, datetime, eo:cloud_cover` + `filter(cloud_cover < 10)` | Column pruning, predicate pushdown, scan volume, read throughput, task count, file sizes | `count()` alone already prunes columns. |
| 15 | Geographic / key skew | M09 | OSM / Landsat | Natural geo key (lat/lon grid, WRS path/row; country/state/city), then `repartition(key)`. 90% `HOT_REGION` injection as the extreme case. | Dominant key, key frequency, overloaded partition, shuffle read, task duration, partition size | Prefer natural skew. |
| 16 | Nested data / explode | M15 | OSM | `explode("tags")` (MAP → key, value), `posexplode("nds")` | Row amplification, Array / Struct / Map types | — |
| 17 | Complex / graph-like JOIN | M08 | OSM | `ways.select("id", F.posexplode("nds"))` ⋈ `nodes` on `col.ref == nodes.id`; then relations → members → ways | Multiple joins, same dataset joined several times, join ordering, intermediate cardinality, shuffle amplification, skew | Explode `nds` before joining. |
| 18 | Domain / key skew | M09 | Common Crawl | `groupBy("url_host_registered_domain").count()`; `repartition("url_host_registered_domain")` | Natural business keys, hot domain, why hash partitioning is affected | — |
| 19 | Huge aggregation | M10 | Common Crawl | `groupBy(domain).agg(F.count("*").alias("pages"), F.avg("warc_record_length"))` → `orderBy(F.desc("pages"))` | Scan → shuffle → aggregation → sort; aggregation memory, spill, reducer imbalance | — |
| 20 | String processing at scale | M12/M13 | Common Crawl `url` | `lower`, `split`, `regexp_extract`, `regexp_replace`, `substring`, `length` vs Python UDF vs Arrow UDF | Expensive string expressions, CPU profiling, codegen | — |
| 21 | Cardinality explosion | M15 | CC / OSM | `F.sequence(F.lit(1), F.lit(100))` + `explode`; then `crossJoin`; many-to-many; nested arrays | Quantify row amplification (1 → 100 rows, N × M) | Bound the input first. |
| 22 | Cache / recomputation | M14 | TLC | `base = trips.filter(fare_amount > 10)`; groupBy PULocationID / DOLocationID / VendorID + 3 counts; then `base.cache(); base.count()` | DAG recomputation, cache vs persist, cache effectiveness, execution time | Also find a case where cache hurts. |
| 23 | Oversized cache / memory pressure | M13/M14 | Scaled TLC | `df.cache().count()` beyond storage memory vs a projected subset cache vs `MEMORY_AND_DISK_SER` | Storage tab, memory, GC, eviction, spill, storage vs execution memory | — |
| 24 | Driver OOM | M24 | TLC | `trips.limit(1_000_000).toPandas()`, increased step by step, then `trips.collect()` | Data leaves the executors for the driver; driver memory, driver-side bottleneck, `maxResultSize`, Arrow | Expected failure. Capture the error. |
| 25 | Python UDF vs native | M12 | TLC | `@F.udf("double") def tip(f): return f*0.20` vs `F.col("fare_amount")*F.lit(0.20)` vs Arrow UDF vs Pandas UDF | Serialization, Python worker, Arrow, benchmark of equivalent implementations; BatchEvalPython vs ArrowEvalPython in the plan | — |
| 26 | JSON parsing / from_json | M15 | Landsat STAC / CC | `from_json(col, schema)` with an explicit schema vs inference vs native struct vs VARIANT; malformed records. Synthetic variant: `to_json(struct(url, url_host_registered_domain, crawl))` → `from_json`. | JSON strings, StructType, nested parsing, malformed records, CPU cost | — |
| 27 | Small files + skew combined | M17/M09 | Skewed TLC | 90% HOT `station_key`/`k` + `repartition(100_000, "k").write.parquet(out)` | Combined diagnosis: many files, skewed data, excessive parallelism, overloaded tasks | Hashing one hot key puts all hot rows in ONE partition: one giant file + many tiny or empty ones. |
| 28 | Iceberg small files | M19/M20 | TLC / NEXRAD / GOES | `df.repartition(100_000).writeTo("catalog.db.events").using("iceberg").createOrReplace()`, then `CALL catalog.system.rewrite_data_files(table => 'db.events')` | Small files → metadata → manifests → file planning → compaction; table layout, file sizing | On partitioned tables the default `hash` distribution re-shuffles and undoes the `repartition()` (CTAS/RTAS respect it only from Spark 3.5). Test unpartitioned vs partitioned. |
| 29 | Iceberg snapshot / append explosion | M20 | TLC | For each month (or hour), `df_month.writeTo("catalog.db.trips").append()` over many batches | Many commits → snapshots → metadata → manifests; snapshot management; `expire_snapshots`, `rewrite_manifests` | — |
| 30 | Iceberg DELETE / UPDATE / MERGE | M20 | TLC | `DELETE FROM catalog.db.trips WHERE PULocationID = 132;` then `… = 138;` then `MERGE INTO` from a source with the same keys; under COW vs MOR | Row-level operations, affected files, rewrite, delete files vs data files, snapshots, read amplification | The default is COW; MOR must be configured. |

---

## 8. Combined production pathologies
Build these after the matching single-cause labs (§7), using the lab card template (§6).

1. Small files + skew
2. Skew + shuffle
3. Skew + window
4. Skew + Iceberg
5. Small files + Iceberg
6. Small files + S3 request pressure
7. Many-to-many + skew
8. JSON + Python UDF
9. Broadcast + memory pressure
10. AQE + pathological partitioning
11. Dynamic allocation + short tasks
12. Streaming + state explosion
13. MERGE + delete files
14. Bad statistics + bad join order
15. Huge metadata + tiny data
16. Driver bottleneck + idle executors

---

## 9. Unknown incident labs
**These are the most important labs.** A partner, or a seeded generator script you don't read, injects the cause. You get the dataset, source code, Spark configuration, Spark UI, logs, metrics and cluster information, but **never** a hint like "the problem is skew". Deliver an incident report (§1.3) for each one, including rejected hypotheses.

| # | Situation |
|---|---|
| 01 | A 500 GB job where one task is 70× slower |
| 02 | A 200 GB scan with low CPU and thousands of tasks |
| 03 | A query got slower after the data doubled (same SQL) |
| 04 | A 100 GB join where broadcast looks available but isn't selected |
| 05 | A 300 GB aggregation where one executor spills massively |
| 06 | A 500 GB Iceberg read with only 40 GB relevant, and runtime is still terrible |
| 07 | An Iceberg write creates tens of thousands of tiny files |
| 08 | An Iceberg write has an unexpected shuffle |
| 09 | MERGE gets progressively slower every week |
| 10 | A streaming job starts fast, then progressively slows |
| 11 | Executors are idle while the driver is busy |
| 12 | CPU 20%, network 90% |
| 13 | CPU 95% with unchanged input |
| 14 | Runtime varies between identical runs |
| 15 | One executor repeatedly becomes slow |
| 16 | AQE is enabled but runtime doesn't improve |
| 17 | Caching makes the query slower |
| 18 | Adding a filter unexpectedly increases runtime |
| 19 | Adding one column makes the query dramatically slower |
| 20 | Same query: Parquet is fast, Iceberg is slow |
| 21 | Same Iceberg table: fast yesterday, slow today |
| 22 | Same logical data, different file layout, 5× runtime difference |
| 23 | One partition holds most of the data |
| 24 | A join is slow even though both tables look balanced |
| 25 | The Spark UI shows many tasks but little actual work |
| 26 | Task input sizes look normal, but durations are wildly different |
| 27 | Shuffle write is normal, shuffle read is extremely slow |
| 28 | Read is fast, write is extremely slow |
| 29 | Write is fast, commit is extremely slow |
| 30 | The plan looks perfect, the application is still slow |
| 31 | A 300 GB dataset, 500+ tasks, several joins, aggregation, Iceberg write, S3 and several actions: runtime went from **20 min → 2 h**. Possible causes include skew, shuffle, join strategy, small files, partitioning, distribution mode, cache, recomputation, memory, GC, Python UDF, nested data, cardinality explosion, Iceberg metadata, Iceberg delete files, S3, connection pool or excessive parallelism. |

---

## 10. Capstones & final test

- **Capstone A — 500 GB end to end:** S3, Parquet, Iceberg, skew, small files, nested JSON, multiple joins, windows, aggregation. Produce an optimized end-to-end pipeline.
- **Capstone B — 1 TB Iceberg:** MERGE, delete files, metadata growth, concurrent writers, compaction. Diagnose read and write amplification.
- **Capstone C — Streaming:** Kafka → Structured Streaming (state, skew) → Iceberg. Sustain the target throughput while keeping state and latency bounded.
- **Capstone D — Blind incident (4 hours, no hints):**
  - **You receive:** History Server, event log, source, configs, metrics, cluster description, data profile.
  - **You deliver:** incident report, root cause, evidence, rejected hypotheses, fix, benchmark, correctness validation, cost impact, regression test, production rollout plan.
- **Capstone E — Data platform end to end:** source → ingestion → Spark → shuffle → Iceberg → S3 → downstream query. Introduce a single bottleneck and find it without reading the lab code.

### Final expert exam
**You are given** a 100–500 GB production-like Spark application with Iceberg, S3, multiple joins, aggregations, windows, nested data, several writes and an unknown performance problem.

**Steps:**
1. Diagnose.
2. Explain.
3. Identify the root cause.
4. Produce a hypothesis.
5. Apply ONE optimization.
6. Benchmark.
7. Compare metrics.
8. Explain the improvement.
9. Check for regressions.
10. Document the solution.

### The final test
**The application:** 500 GB, with Iceberg, S3, Parquet, 1M+ files, a skewed key, a skewed partition, nested JSON, a Python UDF, 3 joins, a window, an aggregation, MERGE, delete files, AQE and dynamic allocation. You are **not** told the problem.

**You must identify:**
1. The dominant bottleneck.
2. Secondary bottlenecks.
3. The root cause.
4. The evidence.
5. The correct fix.
6. Incorrect fixes, and why they are wrong.
7. A benchmark.
8. A correctness check.
9. The cost.
10. Regression prevention.

---

## 11. 10/10 acceptance criteria
You are **not** 10/10 because you completed the list. You are 10/10 when you can reliably answer these **without guessing**, on workloads you have never seen.

### 11.1 Checklist
**Plans & engine**
- [ ] Read an unknown physical plan; explain every Exchange and every major shuffle.
- [ ] Why is Spark shuffling? Can this shuffle be avoided?
- [ ] Identify the expensive operator.
- [ ] Explain partitioning requirements and ordering requirements.
- [ ] Why did Spark choose this join? Explain a bad join choice. Can broadcast be used? Why did broadcast fail?
- [ ] Explain how statistics affected the plan.
- [ ] Why did AQE change the plan? Why did AQE NOT solve the problem?
- [ ] Explain vectorized execution and JVM/Python overhead.

**Stages, tasks, resources**
- [ ] Why is this stage slow? Why is this task 20× slower?
- [ ] Find the abnormal task and the exact key causing the skew.
- [ ] Distinguish skew from a straggler, CPU from an I/O bottleneck, an executor from a driver bottleneck.
- [ ] Explain Spark task parallelism: why so many tasks, why so few, why they are unbalanced.
- [ ] Why so many or too few shuffle partitions?
- [ ] Why is there spill? Why is GC high? Why is an executor or the driver OOM?
- [ ] Diagnose broadcast pressure and driver pressure.

**Data & storage**
- [ ] Explain file split creation and small-file explosion. Why is Spark reading millions of files?
- [ ] Explain Parquet pruning.
- [ ] Why did caching help? Why did caching make things worse?
- [ ] Why did a window become extremely slow? Why did explode multiply the data? Why did a join explode the dataset?
- [ ] Why is S3 slow? Why is the HTTP connection pool exhausted?
- [ ] Diagnose S3 request pressure and metadata pressure.

**Iceberg**
- [ ] Diagnose Iceberg planning and Iceberg writing.
- [ ] What is distribution-mode doing? Why does it cause a shuffle? How does it interact with Iceberg partitioning, with skew, and with output files?
- [ ] Explain target file size vs task size, and the fanout trade-offs.
- [ ] Why are Iceberg writes producing too many files? Why are snapshots growing? Why are delete files accumulating?
- [ ] Explain delete files, COW vs MOR, and MERGE amplification. Why is MERGE slow?
- [ ] Diagnose Iceberg metadata explosion.

**Streaming**
- [ ] Diagnose streaming state growth and Kafka/Spark imbalance.

**Method**
- [ ] Benchmark correctly, prove an optimization, verify correctness, prevent regression.
- [ ] Prove which configuration is better for THIS workload.
- [ ] Diagnose a Spark problem you have never seen before.
- [ ] Explain the trade-off to another engineer.

### 11.2 The 8 questions for every optimization
1. **WHY** was it slow?
2. **WHAT** evidence proves it?
3. **WHAT** changed physically?
4. **WHY** does the change improve performance?
5. **WHAT** does it cost?
6. **WHEN** would it become harmful?
7. **HOW** do we verify correctness?
8. **HOW** do we prevent regression?

If you can't answer them, you have memorized a tuning trick. If you can answer them on an unknown production incident, you are operating at expert level.

### 11.3 Expert levels
| Level | Title | Can do |
|---|---|---|
| L1 | User | Writes PySpark transformations |
| L2 | Advanced user | Understands joins, windows, partitioning, caching |
| L3 | Performance engineer | Reads the Spark UI and physical plans |
| L4 | Spark specialist | Understands shuffle, AQE, memory, JVM, files, joins |
| L5 | Data platform performance engineer | Understands Spark + S3 + Iceberg + cloud runtime |
| L6 | Production Spark expert | Diagnoses unknown incidents |
| L7 | Architect / performance authority | Designs data layout, execution strategy, infrastructure and operating model **before** the incident |

---

## 12. Official documentation
- Apache Spark: https://spark.apache.org/docs/latest/
  - Performance tuning: https://spark.apache.org/docs/latest/tuning.html
  - SQL performance tuning: https://spark.apache.org/docs/latest/sql-performance-tuning.html
  - Generic file source options: https://spark.apache.org/docs/latest/sql-data-sources-generic-options.html
  - Parquet: https://spark.apache.org/docs/latest/sql-data-sources-parquet.html
  - SQL hints: https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-hints.html
  - SQL migration guide: https://spark.apache.org/docs/latest/sql-migration-guide.html
  - Monitoring: https://spark.apache.org/docs/latest/monitoring.html
- Apache Iceberg: https://iceberg.apache.org/docs/latest/
  - Spark writes: https://iceberg.apache.org/docs/latest/spark-writes/
  - Spark procedures: https://iceberg.apache.org/docs/latest/spark-procedures/
  - Maintenance: https://iceberg.apache.org/docs/latest/maintenance/
  - Configuration: https://iceberg.apache.org/docs/latest/configuration/
  - Spark configuration: https://iceberg.apache.org/docs/latest/spark-configuration/
  - Spark Structured Streaming: https://iceberg.apache.org/docs/latest/spark-structured-streaming/
  - Table spec: https://iceberg.apache.org/spec/
- AWS:
  - EMR Spark performance: https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-performance.html
  - EMR + S3 Spark performance: https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-s3-performance.html
  - EMRFS S3-optimized committer: https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-spark-s3-optimized-committer.html
- Data:
  - AWS Open Data Registry: https://registry.opendata.aws/ (`nyc-tlc-trip-records-pds`, `noaa-nexrad`, `noaa-goes`, `usgs-landsat`, `osm`, `commoncrawl`)
  - NYC TLC: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
  - Common Crawl columnar index: https://commoncrawl.org/columnar-index

> Verified on 2026-10-04 against the Spark 4.2.0 and Iceberg 1.12.0 docs; public buckets `unidata-nexrad-level2`, `noaa-goes16/19`, `osm-pds` list anonymously; `usgs-landsat`, `commoncrawl` need credentials; TLC files are served from CloudFront. Re-check when you pin other versions (§2.1). Environment and tooling: see `../setup/README.md`.
