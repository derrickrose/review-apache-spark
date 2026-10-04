# Lab environment & tooling — Spark 3.5.0 / Java 17 (cloud-parity stack)

Duplicate of [`../setup`](../setup) pinned to the Spark line used by EMR 7.x and Glue 5.0 (plan §2.1 version policy).
Only the differences are listed here; everything else (data scripts, harness, lab contract) is identical.

| | `../setup` | `setup-spark35` (this folder) |
|---|---|---|
| Spark / Scala | 4.1.1 / 2.13 | **3.5.0 / 2.12** |
| Java | 21 (Debian trixie) | **17** (Debian bookworm) |
| Iceberg runtime | `iceberg-spark-runtime-4.1_2.13:1.12.0` | `iceberg-spark-runtime-3.5_2.12:1.12.0` |
| Bundled Hadoop → s3a SDK | 3.4.2 → AWS SDK **v2** `bundle` | 3.3.4 → AWS SDK **v1** `aws-java-sdk-bundle:1.12.262` |
| Python libs | latest pandas / pyarrow / numpy | `pandas<2.2`, `pyarrow<15`, `numpy<2` |
| ANSI mode default | on | **off** |
| Event log dir | `s3a://spark-events/` | `s3a://spark-events/spark35/` (Hadoop 3.3 rejects a bucket root) |
| Host ports: Jupyter / UI / History / S3 / REST | 8888 / 4040 / 18080 / 8333 / 8181 | **8889 / 4050 / 18081 / 8334 / 8182** |
| Results dir | `/workspace/results-spark35` | `/workspace/results-spark35-spark35` |
| Lab 26 | baseline / explicit / **variant** (VARIANT) | baseline / explicit (VARIANT is Spark 4.0+) |

Both stacks can run at the same time (separate networks, volumes and ports).

**Verified (2026-10-04):** smoke test (s3a Parquet, Iceberg REST create/insert/read, History Server), and lab 03 on 41.2M rows, 3 runs after warm-up:

| Variant | Spark 3.5.0 median | max/median | Spark 4.1.1 median | max/median |
|---|---|---|---|---|
| baseline | 23.6 s | 9.2 | 19.2 s | 7.6 |
| aqe_skew | 11.2 s | 1.3 | 9.7 s | 1.7 |
| salted | 13.1 s | 2.4 | 13.6 s | 2.2 |

All variants PASS their criteria with identical checksums. The remaining labs have not been executed on this stack.

Commands below are the same as in `../setup`, with `setup` → `setup-spark35`, ports shifted, and the network `setup-spark35_default`.

---


Companion to [`../plan/plan.md`](../plan/plan.md). Each file implements one section of the plan.

| File | Plan section | Purpose |
|---|---|---|
| `docker-compose.yml`, `Dockerfile` | §2.1 | Local stack: Spark 3.5.0 (Java 17) + Iceberg 1.12.0 REST catalog `lab` + SeaweedFS (S3 API) + History Server + Jupyter |
| `conf/spark-defaults.conf` | §1.6, M04 | Baseline config (catalog, s3a, event logs, Prometheus). Every override goes into the config record. |
| `conf/s3.json` | §2.1 | Local S3 credentials (`admin` / `password`) |
| `data/download_tlc.sh` | §3 | Downloads NYC TLC monthly Parquet + zone lookup from the official CloudFront host |
| `data/prepare_tlc.py` | §3 | Normalizes schema drift across years, partitions by `pickup_date`, optional `--copies N` scale-up |
| `data/gen_synthetic.py` | §3 | Seeded pathological data: uniform, zipf, hotkey, multihot, nullheavy, tinyfiles, mixedfiles, nested, wide |
| `bench/bench.py` | §1.4–§1.5, §11 | Warm-up + N fresh-session runs, Spark REST metrics, checksum correctness gate, numeric pass criteria, one CSV row per variant |
| `bench/run_labs.sh` | §7 | Runs every variant of every lab (baseline first) and prints `OK/ERROR :: verdict | correctness | runtime` |
| `bench/labs/common.py` | §3 | Paths, loaders, file statistics, and same-schema synthetic substitutes for OSM / Common Crawl / NEXRAD / Landsat STAC |
| `bench/labs/lab01…lab30_*.py` | §7 | The 30 core labs, one module each |


## Quick start
```bash
cd setup-spark35 && docker compose up -d --build
# Jupyter http://localhost:8889 · Spark UI :4050 · History :18081 · S3 http://localhost:8334 (admin/password)

# 1. Data: download, upload to the local S3, normalize
./data/download_tlc.sh ./raw/tlc yellow 2024 2024
docker run --rm --network setup-spark35_default -v "$PWD/../setup/raw:/raw" \
  -e AWS_ACCESS_KEY_ID=admin -e AWS_SECRET_ACCESS_KEY=password -e AWS_DEFAULT_REGION=us-east-1 \
  amazon/aws-cli --endpoint-url http://s3:8333 s3 sync /raw/tlc s3://lake/raw/tlc
docker compose exec spark spark-submit /workspace/setup-spark35/data/prepare_tlc.py \
  --src s3a://lake/raw/tlc/yellow --dst s3a://lake/tlc/yellow

# 2. One lab, one variant (3 measured runs after 1 warm-up)
docker compose exec spark python /workspace/setup-spark35/bench/bench.py \
  --lab /workspace/setup-spark35/bench/labs/lab03_join_skew.py --variant baseline --out /workspace/results-spark35/lab03_join_skew.csv

# 3. All labs, all variants
docker compose exec spark /workspace/setup-spark35/bench/run_labs.sh /workspace/results-spark35 3 1
docker compose exec spark /workspace/setup-spark35/bench/run_labs.sh /workspace/results-spark35 3 1 lab05_aggregation_skew.py   # a subset
```
Labs that use OSM, Common Crawl, NEXRAD or Landsat run on same-schema synthetic substitutes by default. Set `LAB_SOURCE=real` (with AWS credentials, on EMR/EC2 in us-east-1) to use the public datasets.

## Lab contract
```python
VARIANTS = {"baseline": {...conf}, "fix": {...conf}}   # each variant changes ONE variable (plan §1.2)
def build(spark, variant): return <DataFrame>           # lazy query, executed with a noop write
# optional
def setup(spark): ...                                   # idempotent one-off preparation (e.g. materialize a skewed copy)
def run(spark, variant): return {"files": n, ...}       # custom action (writes, collect, multi-action) + extra metrics
def result(spark, variant): return <DataFrame>          # what to checksum, when it is not build()
CHECK_CORRECTNESS = True                                # False only when a variant changes the result by design
EXPECT = {"fix": {"max_over_median": ("<", 2.0),                     # absolute criterion
                  "runtime_median_s": ("<", 0.8, "x_baseline")}}    # relative to the baseline row
```
Output per variant: one row in `<out>/<lab>.csv` with runtime median/p95/CV, input/output, shuffle R/W, spill, GC %, peak memory, tasks, max/median/p95 task, max/median ratio, extra metrics, `correct` (OK / MISMATCH / reference / n/a), and `verdict` (PASS / FAIL with the failed criterion). The effective Spark config is saved next to it (`<lab>.csv.<variant>.env.json`) for the config record (plan §1.6).


## Limits
- Local mode is a single JVM. Network, executor loss, S3 throttling, dynamic allocation and Kubernetes labs need EMR or EKS (plan §2.1).
- Pass criteria are calibrated for the local 2024 dataset. Relative (`x_baseline`) criteria carry over to other scales; absolute ones (e.g. file counts) do not.
- Leave at least 20 GB of free disk for the local S3 volume; scale-up (`--copies`) needs proportionally more.
