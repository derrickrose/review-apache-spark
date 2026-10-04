"""Benchmark harness implementing plan §1.4–§1.5.

Runs one lab variant N times (after a warm-up) in a fresh SparkSession per run, pulls stage and
task metrics from the Spark REST API, verifies correctness against the baseline checksum, and
appends one row per variant to a CSV that matches the §1.5 benchmark table.

A lab module exposes:
    VARIANTS = {"baseline": {conf...}, "fix": {conf...}}       one variable changed per variant (plan §1.2)
    def build(spark, variant) -> DataFrame                      lazy query; executed with a noop write
  optional:
    def run(spark, variant) -> None                             custom action (writes, collect, multi-action)
    def result(spark, variant) -> DataFrame                     what to checksum (default: build)
    def setup(spark) -> None                                    one-off data preparation (idempotent)
    EXPECT = {"variant": {"metric": ("<", 2.0), ...}}          numeric pass criteria (plan §11)
    CHECK_CORRECTNESS = True                                    False when a variant changes the result by design

    python bench.py --lab labs/lab03_join_skew.py --variant baseline --runs 3 --out results.csv
    python bench.py --lab labs/lab03_join_skew.py --variant fix      --runs 3 --out results.csv
"""
import argparse
import csv
import importlib.util
import json
import os
import statistics
import sys
import time

import requests
from pyspark.sql import SparkSession, functions as F


def load_lab(path):
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))     # labs import common.py
    spec = importlib.util.spec_from_file_location("lab", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def session(conf):
    b = SparkSession.builder.appName("bench")
    for k, v in conf.items():
        b = b.config(k, v)
    return b.getOrCreate()


def checksum(df):
    # Order-independent: row count + sum of per-row hashes (plan §0.4 rule 12)
    r = df.select(F.count(F.lit(1)).alias("n"),
                  F.sum(F.xxhash64(*df.columns).cast("decimal(38,0)")).alias("h")).first()
    return f"{r['n']}:{r['h']}"


def pct(values, p):
    if not values:
        return 0
    s = sorted(values)
    return s[min(len(s) - 1, int(round(p / 100 * (len(s) - 1))))]


def collect_metrics(spark):
    ui = spark.sparkContext.uiWebUrl
    app = spark.sparkContext.applicationId
    api = f"{ui}/api/v1/applications/{app}"
    stages = requests.get(f"{api}/stages?details=false", timeout=30).json()
    m = dict(input=0, output=0, shuffle_r=0, shuffle_w=0, spill_mem=0, spill_disk=0, tasks=0, failed=0,
             gc_ms=0, run_ms=0, peak_mem=0)
    durations = []
    for st in stages:
        m["input"] += st.get("inputBytes", 0)
        m["output"] += st.get("outputBytes", 0)
        m["shuffle_r"] += st.get("shuffleReadBytes", 0)
        m["shuffle_w"] += st.get("shuffleWriteBytes", 0)
        m["spill_mem"] += st.get("memoryBytesSpilled", 0)
        m["spill_disk"] += st.get("diskBytesSpilled", 0)
        m["tasks"] += st.get("numCompleteTasks", 0)
        m["failed"] += st.get("numFailedTasks", 0)
        m["gc_ms"] += st.get("jvmGcTime", 0)
        m["run_ms"] += st.get("executorRunTime", 0)
        m["peak_mem"] = max(m["peak_mem"], st.get("peakExecutionMemory", 0))
        tl = requests.get(f"{api}/stages/{st['stageId']}/{st['attemptId']}/taskList?length=100000", timeout=60).json()
        durations += [t.get("duration", 0) for t in tl if t.get("status") == "SUCCESS"]
    med = statistics.median(durations) if durations else 0
    m.update(max_task_ms=max(durations, default=0), median_task_ms=med, p95_task_ms=pct(durations, 95),
             max_over_median=round(max(durations, default=0) / med, 2) if med else 0,
             gc_pct=round(100 * m["gc_ms"] / m["run_ms"], 1) if m["run_ms"] else 0)
    return m


def run_once(lab, variant, conf):
    spark = session(conf)
    spark.catalog.clearCache()
    t0 = time.time()
    extra = {}
    if hasattr(lab, "run"):
        extra = lab.run(spark, variant) or {}      # labs may return extra metrics (files, sizes, rows)
    else:
        # A full write to a no-op sink forces complete execution without collecting to the driver
        lab.build(spark, variant).write.format("noop").mode("overwrite").save()
    runtime = time.time() - t0
    metrics = collect_metrics(spark)
    if getattr(lab, "CHECK_CORRECTNESS", True):
        cs = checksum(lab.result(spark, variant) if hasattr(lab, "result") else lab.build(spark, variant))
    else:
        cs = "skipped"
    env = {k: v for k, v in spark.sparkContext.getConf().getAll()}
    spark.stop()
    return runtime, metrics, cs, env, extra


OPS = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}


def evaluate(expect, row, refs):
    """Criteria: {"metric": (op, value)} absolute, or {"metric": (op, factor, "x_<variant>")} relative to
    the last row of another variant of the same lab (usually "x_baseline") — relative criteria stay valid
    at every scale (plan §2.2). Returns 'PASS', 'FAIL: ...', or '' when the variant has no criteria."""
    if not expect:
        return ""

    def get(r, k):
        return float(r[k]) if k in r else float(r["extra"].get(k, 0))

    failed = []
    for k, spec in expect.items():
        op, v = spec[0], spec[1]
        got = get(row, k)
        if len(spec) == 3:
            ref_name = spec[2][2:]
            ref = refs.get(ref_name)
            if not ref:
                failed.append(f"{k}: run the '{ref_name}' variant first")
                continue
            v = v * get(ref, k)
        if not OPS[op](got, v):
            failed.append(f"{k} {op} {v:g} (got {got:g})")
    return "PASS" if not failed else "FAIL: " + "; ".join(failed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", required=True)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--out", default="results.csv")
    a = ap.parse_args()

    lab = load_lab(a.lab)
    conf = lab.VARIANTS[a.variant]
    if hasattr(lab, "setup"):
        sp = session(conf)
        lab.setup(sp)
        sp.stop()
    for _ in range(a.warmup):
        run_once(lab, a.variant, conf)

    runtimes, last = [], None
    for _ in range(a.runs):
        rt, m, cs, env, extra = run_once(lab, a.variant, conf)
        runtimes.append(rt)
        last = (m, cs, env, extra)
    m, cs, env, extra = last

    row = dict(lab=os.path.basename(a.lab), variant=a.variant, runs=a.runs,
               runtime_median_s=round(statistics.median(runtimes), 2), runtime_p95_s=round(pct(runtimes, 95), 2),
               runtime_cv_pct=round(100 * statistics.pstdev(runtimes) / statistics.mean(runtimes), 1),
               checksum=cs, **m)
    row["extra"] = extra

    # Reference rows of every variant already run (relative criteria) and correctness gate vs baseline (plan §0.5)
    refs = {}
    prefix = os.path.basename(a.out) + "."
    for f in os.listdir(os.path.dirname(os.path.abspath(a.out))):
        if f.startswith(prefix) and f.endswith(".row.json"):
            refs[f[len(prefix):-len(".row.json")]] = json.load(open(os.path.join(os.path.dirname(os.path.abspath(a.out)), f)))
    baseline = refs.get("baseline")
    if a.variant == "baseline":
        row["correct"] = "reference"
    elif cs == "skipped" or not baseline:
        row["correct"] = "n/a"
    else:
        row["correct"] = "OK" if baseline["checksum"] == cs else f"MISMATCH (baseline {baseline['checksum']})"
    row["verdict"] = evaluate(getattr(lab, "EXPECT", {}).get(a.variant), row, refs)
    json.dump(row, open(f"{a.out}.{a.variant}.row.json", "w"), indent=1)
    row["extra"] = json.dumps(extra)
    row["conf"] = json.dumps(conf)

    new = not os.path.exists(a.out)
    with open(a.out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    json.dump(env, open(f"{a.out}.{a.variant}.env.json", "w"), indent=1)   # config record (plan §1.6)
    print(json.dumps(row, indent=1))


if __name__ == "__main__":
    main()
