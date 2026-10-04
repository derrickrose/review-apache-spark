"""Shared paths and loaders for the core labs (plan §3, §7).

Real public datasets are used when LAB_SOURCE=real. With the default LAB_SOURCE=synthetic, labs whose
dataset is not staged locally (OSM, Common Crawl, NEXRAD, Landsat STAC) use a seeded substitute
with the SAME column names and the same distribution shape, so the lab code is identical on both.
"""
import os

from pyspark.sql import functions as F, types as T

BASE = os.environ.get("LAB_BASE", "s3a://lake")
SOURCE = os.environ.get("LAB_SOURCE", "synthetic")

TRIPS = f"{BASE}/tlc/yellow"
ZONES = f"{BASE}/raw/tlc/zones/taxi_zone_lookup.csv"
OUT = f"{BASE}/out"

REAL = {
    "osm": "s3a://osm-pds/planet/planet-latest.orc",
    "cc": "s3a://commoncrawl/cc-index/table/cc-main/warc/",
    "nexrad": "s3a://unidata-nexrad-level2/2024/06/01/",
    "stac": f"{BASE}/raw/landsat/stac/",
}
SYN = {k: f"{BASE}/syn/{k}" for k in REAL}


def exists(spark, path):
    """True only if the path holds at least one data file. Object stores (SeaweedFS, S3) can keep an empty
    "directory" marker after a delete, so a plain fs.exists() would wrongly skip the data preparation."""
    p = spark._jvm.org.apache.hadoop.fs.Path(path)
    fs = p.getFileSystem(spark._jsc.hadoopConfiguration())
    if not fs.exists(p):
        return False
    it = fs.listFiles(p, True)
    while it.hasNext():
        if not it.next().getPath().getName().startswith(("_", ".")):
            return True
    return False


def rm(spark, path):
    p = spark._jvm.org.apache.hadoop.fs.Path(path)
    p.getFileSystem(spark._jsc.hadoopConfiguration()).delete(p, True)


def file_stats(spark, path):
    """(file_count, total_bytes) of data files under a path — used by write labs (plan M17)."""
    p = spark._jvm.org.apache.hadoop.fs.Path(path)
    fs = p.getFileSystem(spark._jsc.hadoopConfiguration())
    it = fs.listFiles(p, True)
    n = size = 0
    while it.hasNext():
        st = it.next()
        name = st.getPath().getName()
        if not name.startswith(("_", ".")):
            n += 1
            size += st.getLen()
    return n, size


def trips(spark, cols=None):
    df = spark.read.parquet(TRIPS)
    return df.select(*cols) if cols else df


def zones(spark):
    return (spark.read.option("header", True).csv(ZONES)
            .select(F.col("LocationID").cast("int").alias("LocationID"), "Borough", "Zone"))


def materialize_skew(spark, path, frac=0.90, hot=1, key="PULocationID", seed=42):
    """Write the skewed copy ONCE (rand() is non-deterministic, plan §3)."""
    if not exists(spark, path):
        (trips(spark).withColumn("k", F.when(F.rand(seed) < frac, F.lit(hot)).otherwise(F.col(key)))
         .write.mode("overwrite").parquet(path))
    return spark.read.parquet(path)


# ---------------------------------------------------------------- synthetic substitutes (same schema)

def _zipf(n, s, seed):
    a = 1.0 - s
    return F.floor(F.pow((F.lit(float(n) ** a) - 1) * F.rand(seed) + 1, F.lit(1.0 / a))).cast("long")


def osm(spark, rows=20_000_000):
    """OSM planet schema subset: id, type, tags MAP, lat, lon, nds ARRAY<STRUCT<ref>>."""
    if SOURCE == "real":
        return spark.read.orc(REAL["osm"])
    path = SYN["osm"]
    if not exists(spark, path):
        n_nodes = int(rows * 0.85)
        nodes = (spark.range(n_nodes)
                 .withColumn("type", F.lit("node"))
                 .withColumn("lat", 40 + F.pow(F.rand(1), 3) * 10)              # dense "city" around lat 40
                 .withColumn("lon", -74 + F.pow(F.rand(2), 3) * 10)
                 .withColumn("nds", F.lit(None).cast("array<struct<ref:bigint>>")))
        ways = (spark.range(n_nodes, rows)
                .withColumn("type", F.lit("way"))
                .withColumn("lat", F.lit(None).cast("double")).withColumn("lon", F.lit(None).cast("double"))
                .withColumn("nds", F.transform(F.sequence(F.lit(1), (F.rand(3) * 30).cast("int") + 2),
                                               lambda i: F.struct(F.pmod(F.xxhash64("id", i), F.lit(n_nodes)).alias("ref")))))
        tag_keys = F.array(*[F.lit(k) for k in ["highway", "building", "name", "surface", "amenity", "source"]])
        df = nodes.unionByName(ways).withColumn(
            "tags", F.map_from_arrays(F.slice(tag_keys, 1, (F.rand(5) * 6).cast("int") + 1),
                                      F.transform(F.slice(tag_keys, 1, (F.rand(5) * 6).cast("int") + 1),
                                                  lambda k: F.concat(k, F.lit("_v")))))
        df.write.mode("overwrite").orc(path)
    return spark.read.orc(path)


def common_crawl(spark, rows=50_000_000, domains=2_000_000):
    """cc-index columns: url, url_host_name, url_host_registered_domain, url_host_tld,
    fetch_status, content_mime_type, warc_record_length, crawl, subset. Domains are Zipf(1.1)."""
    if SOURCE == "real":
        return spark.read.parquet(REAL["cc"]).where("crawl = 'CC-MAIN-2024-33' AND subset = 'warc'")
    path = SYN["cc"]
    if not exists(spark, path):
        d = _zipf(domains, 1.1, 11)
        tld = F.element_at(F.array(*[F.lit(t) for t in ["com", "org", "net", "de", "fr", "io"]]),
                           (F.rand(12) * 6).cast("int") + 1)
        dom = F.concat(F.lit("site"), d.cast("string"), F.lit("."), tld)
        (spark.range(rows)
         .withColumn("url_host_registered_domain", dom)
         .withColumn("url_host_tld", tld)
         .withColumn("url_host_name", F.concat(F.lit("www."), F.col("url_host_registered_domain")))
         .withColumn("url", F.concat(F.lit("https://"), F.col("url_host_name"), F.lit("/p/"),
                                     F.col("id").cast("string"), F.lit("?ref=Campaign_"), (F.rand(13) * 99).cast("int")))
         .withColumn("fetch_status", F.when(F.rand(14) < 0.9, 200).when(F.rand(15) < 0.5, 404).otherwise(301))
         .withColumn("content_mime_type", F.when(F.rand(16) < 0.85, "text/html").otherwise("application/pdf"))
         .withColumn("warc_record_length", (F.rand(17) * 60000 + 500).cast("int"))
         .withColumn("crawl", F.lit("CC-MAIN-2024-33")).withColumn("subset", F.lit("warc"))
         .drop("id").write.mode("overwrite").parquet(path))
    return spark.read.parquet(path)


def stac(spark, rows=5_000_000):
    """Landsat STAC items as JSON lines: id, properties{datetime, eo:cloud_cover, landsat:wrs_path,
    landsat:wrs_row}, geometry, assets. Read as text so labs can parse with from_json / VARIANT."""
    path = REAL["stac"] if SOURCE == "real" else SYN["stac"]
    if SOURCE != "real" and not exists(spark, path):
        props = F.struct(F.date_format(F.timestamp_seconds(F.lit(1_400_000_000) + (F.rand(21) * 3e8).cast("long")),
                                       "yyyy-MM-dd'T'HH:mm:ss'Z'").alias("datetime"),
                         F.round(F.rand(22) * 100, 2).alias("eo:cloud_cover"),
                         (F.pow(F.rand(23), 2) * 233 + 1).cast("int").alias("landsat:wrs_path"),
                         (F.rand(24) * 248 + 1).cast("int").alias("landsat:wrs_row"))
        assets = F.map_from_arrays(F.array(*[F.lit(b) for b in ["red", "green", "blue", "nir08", "swir16", "qa_pixel"]]),
                                   F.transform(F.array(*[F.lit(b) for b in ["red", "green", "blue", "nir08", "swir16", "qa_pixel"]]),
                                               lambda b: F.struct(F.concat(F.lit("s3://usgs-landsat/x/"), b).alias("href"))))
        (spark.range(rows)
         .select(F.to_json(F.struct(F.concat(F.lit("LC08_"), F.col("id").cast("string")).alias("id"),
                                    props.alias("properties"),
                                    F.struct(F.lit("Polygon").alias("type")).alias("geometry"),
                                    assets.alias("assets"))).alias("value"))
         .write.mode("overwrite").text(path))
    return spark.read.text(path)


def nexrad_listing(spark, objects=300_000):
    """NEXRAD object listing via binaryFile metadata only (content column pruned). The synthetic
    substitute writes many tiny objects with the real key layout YYYY/MM/DD/STATION/file."""
    if SOURCE == "real":
        return (spark.read.format("binaryFile").option("recursiveFileLookup", "true").load(REAL["nexrad"])
                .select("path", "length", "modificationTime"))
    path = SYN["nexrad"]
    if not exists(spark, path):
        stations = [f"K{c}{d}{e}" for c in "ABCDEFGH" for d in "MNOP" for e in "XYZ"]
        (spark.range(objects)
         .withColumn("station", F.element_at(F.array(*[F.lit(s) for s in stations]), (F.col("id") % len(stations)).cast("int") + 1))
         .withColumn("payload", F.sha2(F.col("id").cast("string"), 512))
         .repartition(objects // 50, "station", F.col("id") % (objects // 50 // len(stations)))   # ~50 rows per tiny file
         .write.mode("overwrite").partitionBy("station").parquet(path))
    return (spark.read.format("binaryFile").option("recursiveFileLookup", "true").load(path)
            .select("path", "length", "modificationTime"))
