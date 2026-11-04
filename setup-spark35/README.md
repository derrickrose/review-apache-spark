# Spark 3.5.0 lab stack (cloud parity)

Local lab environment for [`../plan/plan.md`](../plan/plan.md), pinned to the Spark line used by EMR 7.x and Glue 5.0.
Same labs and harness as [`../setup`](../setup) (Spark 4.1.1). Both stacks can run at the same time.

**Stack:** Spark 3.5.0 / Scala 2.12 / Java 17 · Iceberg 1.12.0 REST catalog `lab` · SeaweedFS (S3 API) · History Server · Jupyter

| Service | URL |
|---|---|
| Jupyter | http://localhost:8889 |
| Spark UI (live apps) | http://localhost:4050 – 4055 |
| History Server | http://localhost:18081 |
| S3 (`admin` / `password`) | http://localhost:8334 |
| Iceberg REST | http://localhost:8182 |

## Quick start
```bash
# from the repo root
cd setup-spark35 && docker compose up -d --build

# 1. Data (raw files are shared with ../setup; skip the download if already there)
./data/download_tlc.sh ../setup/raw/tlc yellow 2024 2024
docker run --rm --network setup-spark35_default -v "$PWD/../setup/raw:/raw" \
  -e AWS_ACCESS_KEY_ID=admin -e AWS_SECRET_ACCESS_KEY=password -e AWS_DEFAULT_REGION=us-east-1 \
  amazon/aws-cli --endpoint-url http://s3:8333 s3 sync /raw/tlc s3://lake/raw/tlc
docker compose exec spark spark-submit /workspace/setup-spark35/data/prepare_tlc.py \
  --src s3a://lake/raw/tlc/yellow --dst s3a://lake/tlc/yellow

# 2. One lab, one variant (1 warm-up + 3 measured runs)
docker compose exec spark python /workspace/setup-spark35/bench/bench.py \
  --lab /workspace/setup-spark35/bench/labs/lab03_join_skew.py --variant baseline \
  --out /workspace/results-spark35/lab03_join_skew.csv

# 3. All labs (or a subset by name)
docker compose exec spark /workspace/setup-spark35/bench/run_labs.sh /workspace/results-spark35 3 1
docker compose exec spark /workspace/setup-spark35/bench/run_labs.sh /workspace/results-spark35 3 1 lab05_aggregation_skew.py
```
Labs that use OSM, Common Crawl, NEXRAD or Landsat run on same-schema synthetic data by default. Set `LAB_SOURCE=real` (AWS credentials, us-east-1) to use the public datasets.

## Interactive shell & Spark UI
The shells run inside the `spark` container, so no local Spark install is needed. `cd` into this folder and use `docker compose exec`.
`spark` (SparkSession) and `sc` (SparkContext) are ready at the prompt, and the repo root is mounted at `/workspace`.

**Scala (spark-shell)**: Spark UI at http://localhost:4054, exit with `:quit`
```bash
cd setup-spark35
docker compose exec spark spark-shell --conf spark.ui.port=4044
```
```scala
import org.apache.spark.sql.functions._
val df = spark.range(20000000).withColumn("k", col("id") % 100)
df.groupBy("k").agg(count("*").as("n"), sum("id").as("total")).orderBy("k").show(5)
```

**Python (pyspark)**: Spark UI at http://localhost:4055, exit with `exit()`
```bash
cd setup-spark35
docker compose exec spark pyspark --conf spark.ui.port=4045
```
```python
from pyspark.sql import functions as F
df = spark.range(20_000_000).withColumn("k", F.col("id") % 100)
df.groupBy("k").agg(F.count("*").alias("n"), F.sum("id").alias("total")).orderBy("k").show(5)
```
Both run the same job (20M rows, 100 keys) and print the same table: `n = 200000` per key, `total = 1999990000000, 1999990200000, …`. It appears in the Jobs and SQL tabs of the UI.

**As a script** (save the file anywhere in the repo, it is visible under `/workspace/...`):
```bash
docker compose exec spark spark-shell -i /workspace/job.scala   # end job.scala with System.exit(0)
docker compose exec spark spark-submit /workspace/job.py        # job.py creates spark = SparkSession.builder.getOrCreate()
```
- Container ports 4040–4045 map to host ports 4050–4055. Without `spark.ui.port`, each app (shell, notebook, `bench.py`) takes the first free port starting at 4040 (→ 4050). Check yours with `sc.uiWebUrl` (Scala) or `spark.sparkContext.uiWebUrl` (Python), then add 10.
- The live UI goes away when the app exits. Finished apps are in the History Server at http://localhost:18081.

## Files
| File | Plan § | Purpose |
|---|---|---|
| `docker-compose.yml`, `Dockerfile` | 2.1 | The stack above |
| `conf/spark-defaults.conf` | 1.6, M04 | Baseline config (catalog, s3a, event logs, Prometheus) |
| `conf/s3.json` | 2.1 | Local S3 credentials |
| `data/download_tlc.sh` | 3 | Downloads NYC TLC monthly Parquet and the zone lookup |
| `data/prepare_tlc.py` | 3 | Fixes schema drift, partitions by `pickup_date`, optional `--copies N` |
| `data/gen_synthetic.py` | 3 | Seeded skewed data: zipf, hotkey, nullheavy, tinyfiles, nested, wide, … |
| `bench/bench.py` | 1.4–1.5, 11 | Warm-up + N fresh-session runs, metrics, checksum gate, pass criteria, one CSV row per variant |
| `bench/run_labs.sh` | 7 | Runs every variant of every lab, baseline first |
| `bench/labs/common.py` | 3 | Paths, loaders, synthetic stand-ins for the public datasets |
| `bench/labs/lab01…lab31_*.py` | 7 | The 31 labs, one module each |

## Lab contract
```python
VARIANTS = {"baseline": {...conf}, "fix": {...conf}}   # each variant changes ONE variable
def build(spark, variant): return <DataFrame>           # lazy query, executed with a noop write
# optional
def setup(spark): ...                                   # idempotent one-off preparation
def run(spark, variant): return {"files": n, ...}       # custom action + extra metrics
def result(spark, variant): return <DataFrame>          # what to checksum, if not build()
CHECK_CORRECTNESS = True                                # False only when a variant changes the result by design
EXPECT = {"fix": {"max_over_median": ("<", 2.0),                     # absolute
                  "runtime_median_s": ("<", 0.8, "x_baseline")}}    # relative to baseline
```
Each variant writes one row to `<out>/<lab>.csv`: runtime (median / p95 / CV), I/O, shuffle, spill, GC %, peak memory, task skew (max / median / p95), `correct` (OK / MISMATCH / reference / n/a) and `verdict` (PASS / FAIL + failed criterion). The effective config is saved as `<lab>.csv.<variant>.env.json`.

## Differences from `../setup`
| | `../setup` | this folder |
|---|---|---|
| Spark / Scala / Java | 4.1.1 / 2.13 / 21 | 3.5.0 / 2.12 / 17 |
| Iceberg runtime | `iceberg-spark-runtime-4.1_2.13` | `iceberg-spark-runtime-3.5_2.12` |
| s3a (Hadoop → AWS SDK) | 3.4.2 → SDK v2 | 3.3.4 → SDK v1 `aws-java-sdk-bundle:1.12.262` |
| Python libs | latest | `pandas<2.2`, `pyarrow<15`, `numpy<2` |
| ANSI mode | on | off |
| Event logs | `s3a://spark-events/` | `s3a://spark-events/spark35/` (Hadoop 3.3 rejects a bucket root) |
| Host ports (Jupyter / UI / History / S3 / REST) | 8888 / 4040 / 18080 / 8333 / 8181 | 8889 / 4050 / 18081 / 8334 / 8182 |
| Lab 26 | baseline / explicit / variant | baseline / explicit (VARIANT is Spark 4.0+) |

**Verified:** smoke test (s3a Parquet, Iceberg REST, History Server) and lab 03 (41.2M rows, median of 3 runs after 1 warm-up). All variants PASS with identical checksums. The other labs have not been run on this stack yet.

| lab03 variant | Spark 3.5.0 (2026-11-02) median (max/median) | Spark 4.1.1 (2026-10-04) median (max/median) |
|---|---|---|
| baseline | 25.3 s (9.6) | 19.2 s (7.6) |
| aqe_skew | 9.5 s (1.7) | 9.7 s (1.7) |
| salted | 12.4 s (1.9) | 13.6 s (2.2) |

## Limits
- Local mode (`local[8]`, 8 GB driver, 12 GB container) is a single JVM. Network, executor-loss, S3-throttling, dynamic-allocation and Kubernetes labs need EMR or EKS.
- Pass criteria are calibrated on the 2024 dataset. Relative (`x_baseline`) criteria carry over to other scales; absolute ones (e.g. file counts) do not.
- Keep at least 20 GB free for the local S3 volume; `--copies` needs proportionally more.
