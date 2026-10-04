"""Lab 31 — Statistics poisoning: a correct query made slow by stale optimizer statistics (plan M28, M08 lab 3).

Scenario: a dimension table is ANALYZEd while small, then an external writer appends millions of rows
directly to its location. The catalog still says "tiny", so the planner broadcasts a large table.
AQE cannot undo this: the broadcast is chosen at planning time; AQE only converts SMJ -> BHJ, never back.

Uses Parquet tables in a persistent Hive catalog (embedded Derby): ANALYZE TABLE is not supported on
Iceberg tables in Spark, and the in-memory session catalog would lose statistics between sessions.

Tables (rebuilt in every run so each variant starts from a known statistics state):
    l31.fact : all trips (~41M rows) with trip_key
    l31.dim  : DIM_ROWS trips keyed by trip_key (a large "dimension")

Variants (all return the same rows):
    baseline : no catalog statistics -> size from files (real, large) -> SortMergeJoin   (correct plan)
    stale    : ANALYZEd at ~31k rows, then the other ~25M rows appended behind the catalog's back -> BroadcastHashJoin
    refreshed: same as stale + ANALYZE TABLE again -> correct size -> SortMergeJoin

What this lab proves locally: the planner's estimate is wrong (estimate_ratio), the join choice flips to
BroadcastHashJoin, and memory pressure jumps (peak_mem). The runtime penalty needs a real cluster (see EXPECT).

Read in each run: `estimated_dim_mb` (what the planner believed) vs `actual_dim_mb` (files on storage),
the chosen join (`bhj` = 1 if BroadcastHashJoin), and `query_s` (join only, preparation excluded).
Inspect manually:  DESCRIBE EXTENDED l31.dim ;  spark.table("l31.dim").explain("cost")
"""
import time

from pyspark.sql import functions as F
import common as C

DB_PATH = f"{C.OUT}/lab31/db"
DIM_PATH = f"{C.OUT}/lab31/dim"
DIM_SRC = f"{C.OUT}/lab31/dim_source"
FACT_PATH = f"{C.OUT}/lab31/fact"
DIM_ROWS = 25_000_000
SEED_MOD = 800            # first load = rows with pmod(trip_key, 800) == 0  (~DIM_ROWS / 800 ≈ 31k rows)

_hive = {
    "spark.sql.catalogImplementation": "hive",
    "spark.sql.warehouse.dir": f"{C.OUT}/lab31/warehouse",
    "spark.hadoop.javax.jdo.option.ConnectionURL": "jdbc:derby:;databaseName=/tmp/lab31_metastore;create=true",
    "spark.sql.statistics.size.autoUpdate.enabled": "false",   # the default: stats are NOT refreshed on write
}
VARIANTS = {"baseline": dict(_hive), "stale": dict(_hive), "refreshed": dict(_hive)}
EXPECT = {
    "baseline": {"bhj": ("<", 1), "estimate_ratio": (">", 0.5)},
    "stale": {"bhj": (">=", 1), "estimate_ratio": ("<", 0.05), "peak_mem": (">", 2, "x_baseline")},
    "refreshed": {"bhj": ("<", 1), "estimate_ratio": (">", 0.5), "peak_mem": ("<", 0.5, "x_stale")},
}
# On a multi-executor cluster add:  "stale": {"query_s": (">", 1.2, "x_baseline")}
# Measured locally (Spark 4.1.1, single JVM, dim = 25M rows / 318 MB): the poisoned broadcast is NOT slower
# (24.7 s vs 25.7 s) because there is no network and no per-executor copy, but it uses 4.3x the peak
# execution memory (27.6 GB vs 6.4 GB). On a cluster the build side is also collected to the driver and
# shipped to every executor: that is where it turns into timeouts and OOMs.

KEY_COLS = ["VendorID", "tpep_pickup_datetime", "PULocationID", "DOLocationID"]


def _with_key(df):
    return df.withColumn("trip_key", F.xxhash64(*KEY_COLS))


def setup(spark):
    spark.sql(f"CREATE DATABASE IF NOT EXISTS l31 LOCATION '{DB_PATH}'")
    if not C.exists(spark, FACT_PATH):
        _with_key(C.trips(spark)).select("trip_key", "PULocationID", "fare_amount", "pickup_date") \
            .write.mode("overwrite").parquet(FACT_PATH)
    spark.sql(f"CREATE TABLE IF NOT EXISTS l31.fact USING parquet LOCATION '{FACT_PATH}'")
    if not C.exists(spark, DIM_SRC):
        (_with_key(C.trips(spark)).select("trip_key", "tip_amount", "total_amount", "payment_type", "trip_distance")
         .orderBy("trip_key").limit(DIM_ROWS).write.mode("overwrite").parquet(DIM_SRC))


def _prepare_dim(spark, variant):
    spark.sql("DROP TABLE IF EXISTS l31.dim")
    C.rm(spark, DIM_PATH)
    full = spark.read.parquet(DIM_SRC)
    seed = F.pmod(F.col("trip_key"), F.lit(SEED_MOD)) == 0      # deterministic split, no row lost or duplicated
    if variant == "baseline":
        full.write.mode("overwrite").parquet(DIM_PATH)
        spark.sql(f"CREATE TABLE l31.dim USING parquet LOCATION '{DIM_PATH}'")
        return
    # Small first load, analyzed while small
    full.where(seed).write.mode("overwrite").parquet(DIM_PATH)
    spark.sql(f"CREATE TABLE l31.dim USING parquet LOCATION '{DIM_PATH}'")
    spark.sql("ANALYZE TABLE l31.dim COMPUTE STATISTICS")
    # External writer appends the rest directly to the location: the catalog statistics are not touched
    full.where(~seed).write.mode("append").parquet(DIM_PATH)
    spark.sql("REFRESH TABLE l31.dim")                          # new files become visible, stats stay stale
    if variant == "refreshed":
        spark.sql("ANALYZE TABLE l31.dim COMPUTE STATISTICS")


def _query(spark):
    return spark.table("l31.fact").join(spark.table("l31.dim"), "trip_key")


def run(spark, variant):
    _prepare_dim(spark, variant)
    q = _query(spark)
    est = spark.table("l31.dim")._jdf.queryExecution().optimizedPlan().stats().sizeInBytes()
    _, actual = C.file_stats(spark, DIM_PATH)
    t0 = time.time()
    q.write.format("noop").mode("overwrite").save()
    query_s = time.time() - t0
    plan = q._jdf.queryExecution().executedPlan().toString()
    return {"bhj": int("BroadcastHashJoin" in plan),
            "estimated_dim_mb": round(est / 2**20, 2), "actual_dim_mb": round(actual / 2**20, 2),
            "estimate_ratio": round(est / max(actual, 1), 4), "query_s": round(query_s, 2)}


def result(spark, variant):
    return _query(spark).select("trip_key", "PULocationID", "fare_amount", "tip_amount", "total_amount")
