# EMR Serverless Sizing

Every fact below with a ✓ was checked today (two independent passes) against current AWS documentation/blogs — see Sources.
Everything under "Heuristics" is an engineering rule of thumb, not an AWS-documented rule — validate it with the Spark UI on your own workload.

## 1. Mental model

Cluster (EMR on EC2): fixed box → slice into executors.
Serverless: start from the workload → task parallelism → worker shape → concurrent workers → cost ceiling.

No HDFS. Input/output is S3; shuffle/spill goes to ephemeral worker disk (or to Serverless Storage, see §3).
No YARN/ApplicationManager reserving host cores — AWS eats that overhead, not you.

## 2. Worker grid ✓

| vCPU | Memory | Increment |
|---|---|---|
| 1 | 2–8 GB | 1 GB |
| 2 | 4–16 GB | 1 GB |
| 4 | 8–30 GB | 1 GB |
| 8 | 16–60 GB | 4 GB |
| 16 | 32–120 GB | 8 GB |
| 32 | 60 / 120 / 244 GB only | discrete |

Standard disk: 20–200 GB/worker (first 20 GB free).
Shuffle-optimized disk (EMR 7.1.0+): 20 GB–2 TB/worker, higher IOPS, billed from the first GB.

**32-vCPU rule:** `executor.memory + overhead` must land within 8 GB of 60/120/244 GB or the job is rejected.
Example: `executor.memory=100g` → +10% overhead = 110g → rejected (not within 8 GB of 120g). Valid range for the 120g tier: 102–109g.

## 3. Storage options

- **Standard local disk** (default): 20–200 GB/worker, S3 for persistent data.
- **Shuffle-optimized disk** (EMR 7.1.0+): use for shuffle/IO-heavy jobs; up to 2 TB/worker.
- **Serverless Storage** (EMR 7.12.0+): fully managed intermediate storage, no local disk to size, no storage charge for intermediate data — but capped at 200 GB of intermediate data per job. Above that, use local/shuffle-optimized disk instead.

## 4. Defaults ✓

```
spark.driver.cores                          = 4
spark.driver.memory                         = 14g   (109g on a 32-vCPU worker)
spark.executor.cores                        = 4
spark.executor.memory                       = 14g   (109g on a 32-vCPU worker)
spark.executor.instances                    = 3
spark.dynamicAllocation.enabled             = true
spark.dynamicAllocation.initialExecutors    = 3
spark.dynamicAllocation.minExecutors        = 0
spark.dynamicAllocation.maxExecutors        = infinity (EMR 6.10+) / 100 (EMR ≤6.9)
spark.dynamicAllocation.executorIdleTimeout = 60s
spark.emr-serverless.executor.disk          = 20g
spark.emr-serverless.driver.disk            = 20g
spark.emr-serverless.memoryOverheadFactor   = 0.1 (min 384 MB)
spark.emr-serverless.allocation.batch.size  = 20 containers/cycle, 1s between cycles
```

Driver/executor cores and memory must be set via the `StartJobRun` API (`sparkSubmitParameters` or `configurationOverrides`), not inside your script — workers can be pre-provisioned before your script runs, so in-script `SparkConf` is too late.

## 5. Billing ✓

Billed on aggregate vCPU-seconds + memory GB-seconds + disk GB-seconds. Standard disk: only above the free 20 GB is billed. Shuffle-optimized disk: billed from GB 1, including the first 20 GB (confirmed on the pricing page — no free tier for this disk type). Metered per second with a 1-minute minimum per worker.

Cap spend with the application's `maximumCapacity` (required at creation). AWS's own sizing rule: `max workers × worker size`.
Example: 50 workers × 2 vCPU/16 GB/20 GB → `maximumCapacity` = 100 vCPU / 800 GB / 1000 GB.

Also check your account's regional "max concurrent vCPUs" service quota.

## 6. Sizing heuristics (not AWS rules — verify per workload)

1. **Estimate input parallelism**: `input_tasks ≈ input_bytes / spark.sql.files.maxPartitionBytes` (Spark default 128 MB).
   Actual partition count also depends on file count/size/splittability — check the Spark UI, don't trust the formula alone.
2. **Shuffle partitions**: default `spark.sql.shuffle.partitions` (200) is usually too coarse for large shuffles. Setting it high (e.g. 2000–4000) and letting AQE coalesce down is a common starting point — it does not *guarantee* spill avoidance or spill occurrence; that depends on execution memory, skew, and join type too.
3. **Executor shape**: 4 vCPU is a common general-purpose starting point (grid only offers 1/2/4/8/16/32, so treat "≤5 cores/executor" cluster advice as "try 4"). Go 8+ vCPU for heavy UDFs, wide rows, or large broadcasts/caching.
4. **Concurrency / waves**: `maxExecutors ≈ input_tasks / (cores_per_executor × desired_waves)`. More waves = faster, roughly flat total cost for CPU-bound jobs — but the "flat cost" curve bends up at very high concurrency (JVM startup, S3 listing overhead) and at very low concurrency (spill).
5. **Disk**: `disk_per_executor ≳ (shuffle_bytes / num_executors) × 1.5` as a starting estimate — not a guarantee. Start at the free 20 GB, watch the `WorkerEphemeralStorageUsed` / `WorkerEphemeralStorageAllocated` CloudWatch metrics ✓, raise disk before raising memory if you see `No space left on device`.

## 7. Worked example — 500 GB shuffle-heavy Parquet

```bash
aws emr-serverless start-job-run \
  --application-id "$APP_ID" \
  --execution-role-arn "$ROLE" \
  --job-driver '{"sparkSubmit":{
    "entryPoint":"s3://my-bucket/jobs/etl.py",
    "sparkSubmitParameters":"
      --conf spark.driver.cores=4
      --conf spark.driver.memory=14g
      --conf spark.executor.cores=4
      --conf spark.executor.memory=14g
      --conf spark.executor.memoryOverhead=2g
      --conf spark.emr-serverless.executor.disk=20g
      --conf spark.dynamicAllocation.enabled=true
      --conf spark.dynamicAllocation.initialExecutors=20
      --conf spark.dynamicAllocation.minExecutors=0
      --conf spark.dynamicAllocation.maxExecutors=100
      --conf spark.sql.shuffle.partitions=4000
      --conf spark.sql.adaptive.enabled=true
      --conf spark.sql.adaptive.coalescePartitions.enabled=true
      --conf spark.sql.adaptive.skewJoin.enabled=true"
  }}'
```

- `14g + 2g = 16g` → exactly a 4 vCPU/16 GB worker, no rounding tax.
- `minExecutors=0`, not a floor — a floor just burns money during driver-only phases.

## 8. dynamicAllocationOptimization ✓

```json
[{ "Classification": "spark", "Properties": { "dynamicAllocationOptimization": "true" } }]
```

Aligns Spark's executor request/cancel rate with how fast EMR Serverless provisions/releases workers → better worker reuse across stages, lower cost on multi-stage jobs. Available on all EMR release versions; requires dynamic allocation on. No gain on trivial single-stage jobs. Can *regress* runtime on a big → small → big stage pattern (fewer workers retained for the final large stage).

## 9. Converge after run #1

Data-volume sizing gets you within ~2x. Read the Spark UI / EMR job metrics, change one variable at a time:

| Signal | Action |
|---|---|
| Spill (memory/disk) > 0 | Raise `shuffle.partitions` first (free), then executor memory |
| GC time > ~10% of task time | Executor too fat — drop 8 vCPU to 4 |
| A few tasks ~10x the median | Skew — salt the key or use `adaptive.skewJoin`; more executors won't fix it |
| `maxExecutors` never reached | Parallelism capped by partition count, not your ceiling — lower it |
| Long ramp at stage boundaries | Consider pre-initialized capacity (bills while warm; released on the 15-min auto-stop) |

## Sources

- https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/jobs-spark.html
- https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/app-behavior.html
- https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/jobs-shuffle-optimized-disks.html
- https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/jobs-serverless-storage.html
- https://aws.amazon.com/emr/pricing/
- https://aws.amazon.com/blogs/big-data/accelerate-spark-on-emr-serverless-with-larger-workers-and-shuffle-optimized-disks/
- https://docs.aws.amazon.com/emr/latest/EMR-Serverless-UserGuide/app-job-metrics.html
