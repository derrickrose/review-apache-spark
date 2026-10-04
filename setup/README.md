# Lab environment & tooling

Companion to [`../plan/plan.md`](../plan/plan.md). Each file implements one section of the plan.

| File | Plan section | Purpose |
|---|---|---|
| `docker-compose.yml`, `Dockerfile` | §2.1 | Local stack: Spark 4.1.1 (Java 21) + Iceberg 1.12.0 REST catalog `lab` + SeaweedFS (S3 API) + History Server + Jupyter |
| `conf/spark-defaults.conf` | §1.6, M04 | Baseline config (catalog, s3a, event logs, Prometheus). Every override goes into the config record. |
| `conf/s3.json` | §2.1 | Local S3 credentials (`admin` / `password`) |
| `data/download_tlc.sh` | §3 | Downloads NYC TLC monthly Parquet + zone lookup from the official CloudFront host |
| `data/prepare_tlc.py` | §3 | Normalizes schema drift across years, partitions by `pickup_date`, optional `--copies N` scale-up |
| `data/gen_synthetic.py` | §3 | Seeded pathological data: uniform, zipf, hotkey, multihot, nullheavy, tinyfiles, mixedfiles, nested, wide |
| `bench/bench.py` | §1.4–§1.5, §11 | Warm-up + N fresh-session runs, Spark REST metrics, checksum correctness gate, numeric pass criteria, one CSV row per variant |
| `bench/run_labs.sh` | §7 | Runs every variant of every lab (baseline first) and prints `OK/ERROR :: verdict | correctness | runtime` |
| `bench/labs/common.py` | §3 | Paths, loaders, file statistics, and same-schema synthetic substitutes for OSM / Common Crawl / NEXRAD / Landsat STAC |
| `bench/labs/lab01…lab30_*.py` | §7 | The 30 core labs, one module each |

## Version and component choices
| Choice | Reason |
|---|---|
| Spark **4.1.1**, not 4.2.0 | Iceberg 1.12.0 publishes runtimes only for Spark 4.0 / 4.1 |
| **Java 21** | The Debian trixie base image no longer ships OpenJDK 17; Spark 4.1 supports 17 and 21 |
| **SeaweedFS** instead of MinIO | MinIO images are no longer published on Docker Hub or quay.io |
| SeaweedFS `-master.volumeSizeLimitMB=1024 -volume.max=200` | The default 30 GB volumes cannot be allocated on a host with little free disk ("No writable volumes") |
| `hadoop-aws` + AWS SDK v2 `bundle` resolved from the bundled Hadoop version | `s3a://` needs the SDK v2 transfer manager, which `iceberg-aws-bundle` does not include (`ClassNotFoundException: software.amazon.awssdk.transfer.s3...`) |

## Quick start
```bash
cd setup && docker compose up -d --build
# Jupyter http://localhost:8888 · Spark UI :4040 · History :18080 · S3 http://localhost:8333 (admin/password)

# 1. Data: download, upload to the local S3, normalize
./data/download_tlc.sh ./raw/tlc yellow 2024 2024
docker run --rm --network setup_default -v "$PWD/raw:/raw" \
  -e AWS_ACCESS_KEY_ID=admin -e AWS_SECRET_ACCESS_KEY=password -e AWS_DEFAULT_REGION=us-east-1 \
  amazon/aws-cli --endpoint-url http://s3:8333 s3 sync /raw/tlc s3://lake/raw/tlc
docker compose exec spark spark-submit /workspace/setup/data/prepare_tlc.py \
  --src s3a://lake/raw/tlc/yellow --dst s3a://lake/tlc/yellow

# 2. One lab, one variant (3 measured runs after 1 warm-up)
docker compose exec spark python /workspace/setup/bench/bench.py \
  --lab /workspace/setup/bench/labs/lab03_join_skew.py --variant baseline --out /workspace/results/lab03_join_skew.csv

# 3. All labs, all variants
docker compose exec spark /workspace/setup/bench/run_labs.sh /workspace/results 3 1
docker compose exec spark /workspace/setup/bench/run_labs.sh /workspace/results 3 1 lab05_aggregation_skew.py   # a subset
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

## Verified results (local, 2024 yellow taxi, 41.2M rows)
Lab 03, 3 runs after warm-up, identical checksums across all variants:

| Variant | Median runtime | Max/median task | Max task | Shuffle read |
|---|---|---|---|---|
| baseline (SMJ, skew join off) | 19.2 s | 7.6 | 16.4 s | 454 MB |
| aqe_skew | 9.7 s | 1.7 | 5.1 s | 454 MB |
| salted ×32 | 13.6 s | 2.2 | 5.7 s | 510 MB |

The validation status of all 30 labs is in `../results/validate/`.

## Limits
- Local mode is a single JVM. Network, executor loss, S3 throttling, dynamic allocation and Kubernetes labs need EMR or EKS (plan §2.1).
- Pass criteria are calibrated for the local 2024 dataset. Relative (`x_baseline`) criteria carry over to other scales; absolute ones (e.g. file counts) do not.
- Leave at least 20 GB of free disk for the local S3 volume; scale-up (`--copies`) needs proportionally more.
