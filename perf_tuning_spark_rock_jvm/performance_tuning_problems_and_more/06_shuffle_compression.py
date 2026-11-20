"""

Once you set a compression codec in the spark conf (before starting the spark session)
YOU CANNOT CHANGE IT -> a new SparkSession is created for every benchmark.

Tradeoff
- shuffle size - data transfer (IO-bound clusters)
- compression time
- cpu load

Difference with Scala: PySpark cannot subclass the JVM `SparkListener`, so the shuffle
bytes written are read from the Spark monitoring REST API (/api/v1/.../stages),
which exposes the same task metrics (shuffleWriteBytes).
"""
import json
import time
import urllib.request
from dataclasses import dataclass

from pyspark import SparkConf
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


@dataclass
class Result:
    codec: str
    time_ms: int
    shuffle_bytes: int

    @property
    def shuffle_mb(self) -> float:
        return self.shuffle_bytes / (1024 * 1024)

    def __str__(self) -> str:
        return f"Result({self.codec}, {self.time_ms} ms, {self.shuffle_mb:.1f} MB shuffled)"


def total_shuffle_write_bytes(spark: SparkSession) -> int:
    """Sum of shuffle write bytes over all stages (equivalent of ShuffleWriteListener)."""
    sc = spark.sparkContext
    url = f"{sc.uiWebUrl}/api/v1/applications/{sc.applicationId}/stages"
    with urllib.request.urlopen(url) as response:
        stages = json.load(response)
    return sum(stage.get("shuffleWriteBytes", 0) for stage in stages)


# compression codecs: lz4, snappy, zstd, lzf
def benchmark(
    codec: str,
    rows: int = 15_000_000,
    shuffle_partitions: int = 64,
    zstd_workers: int = 0,
    zstd_level: int = 3,
) -> Result:
    parallel_zstd = codec == "zstd" and zstd_workers > 0

    conf = (
        SparkConf()
        .setAppName("Shuffle compression")
        .set("spark.io.compression.codec", codec)
        .set("spark.shuffle.compress", "true")
        .set("spark.ui.enabled", "true")  # needed for the REST API metrics
        .setMaster("local[2]" if parallel_zstd else "local[*]")
    )
    if parallel_zstd:
        conf.set("spark.io.compression.zstd.workers", str(zstd_workers))
        conf.set("spark.io.compression.zstd.level", str(zstd_level))

    spark = SparkSession.builder.config(conf=conf).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    try:
        # wide strings - log lines
        df = spark.range(0, rows).select(
            (F.col("id") % 5000).alias("key"),
            F.concat(
                F.lit("26/06/20 15:39:18 INFO MyService"),
                F.lit("session="), (F.col("id") % 10000).cast("string"),
                F.lit(": Server created on 192.168.1.149:64414 path=/opt/spark/mything/app/... user="),
                (F.col("id") % 800).cast("string"),
            ).alias("payload"),
        )

        t0 = time.perf_counter_ns()
        # force the evaluation of this DF
        (
            df.repartition(shuffle_partitions, F.col("key"))
            .write.format("noop").mode("overwrite").save()
        )
        time_ms = (time.perf_counter_ns() - t0) // 1_000_000
        return Result(codec, time_ms, total_shuffle_write_bytes(spark))
    finally:
        spark.stop()


def run_benchmark() -> None:
    # warmup
    benchmark("lz4", rows=3_000_000)

    codecs = ["lz4", "snappy", "zstd", "lzf"]
    parallel_run = benchmark("zstd", zstd_workers=4, zstd_level=12)
    codec_runs = [benchmark(codec) for codec in codecs] + [parallel_run]
    for result in codec_runs:
        print(result)


if __name__ == "__main__":
    run_benchmark()


# ---------------------------------------------------------------------------
# Results (15M rows, local machine)
# ---------------------------------------------------------------------------
# Result(lz4, 3002 ms, 225.8 MB shuffled)
# Result(snappy, 3300 ms, 262.7 MB shuffled)
# Result(zstd, 2568 ms, 1.1 MB shuffled)
# Result(lzf, 7830 ms, 274.6 MB shuffled)
# Result(zstd, 7690 ms, 0.4 MB shuffled)   <- zstd level 12 + 4 workers, local[2]
#
# | Codec                     | Time    | Shuffle  | Verdict                              |
# |---------------------------|---------|----------|--------------------------------------|
# | zstd (level 3)            | 2568 ms | 1.1 MB   | best on both time and size           |
# | lz4 (default)             | 3002 ms | 225.8 MB | fast but compresses little           |
# | snappy                    | 3300 ms | 262.7 MB | slightly worse than lz4 on both      |
# | lzf                       | 7830 ms | 274.6 MB | worst: slowest and biggest           |
# | zstd level 12 + 4 workers | 7690 ms | 0.4 MB   | even smaller, but 3x slower          |
#
# Why these runs:
# - warmup lz4 (3M rows, discarded): pays the JVM / JIT start-up cost so the first
#   measured codec is not unfairly slow.
# - lz4 = Spark default (baseline), zstd = main alternative -> the essential pair.
# - snappy / lzf: optional, show the other codecs.
# - zstd level 12 + workers: optional, shows "stronger compression with background
#   threads"; not a fair comparison (local[2] instead of local[*]).
#
# Analysis:
# 1. zstd compresses ~200x better here because the data is very repetitive (a fixed
#    log line where only two small numbers change) and zstd looks back over a much
#    larger window than lz4/snappy/lzf. Real data won't compress 200x: expect zstd
#    ~2-4x smaller than lz4, test on your own data.
# 2. Less data shuffled can mean a faster job: writing/reading 1 MB instead of
#    226 MB saves more time than zstd's extra CPU costs. On a real cluster the
#    network makes this matter even more.
# 3. More compression has a limit: level 12 saves another 0.7 MB but triples the
#    time (partly because it only uses 2 cores).
# 4. lzf is outdated: slower and bigger than everything else.
# 5. lz4 vs snappy is about even; lz4 is a bit better, one reason it's the default.
#
# Conclusion:
# - CPU-bound cluster            -> stay on lz4 (default).
# - IO/network-bound or big shuffles -> zstd at default level
#   (spark.io.compression.codec=zstd, set BEFORE the session starts).
# - Don't push zstd levels high: the small extra gain costs a lot of CPU/time.
