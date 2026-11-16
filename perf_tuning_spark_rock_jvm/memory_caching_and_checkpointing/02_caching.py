import time
from pathlib import Path

from pyspark import StorageLevel
from pyspark.sql import SparkSession

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
FLIGHTS_PATH = DATA_DIR / "flights"

spark = (
    SparkSession.builder.appName("Caching")
    .config("spark.memory.offHeap.enabled", "true")
    .config(
        "spark.memory.offHeap.size", 10000000
    )  # 10 MB - small: OFF_HEAP blocks that don't fit go to disk
    .master("local")  # 1 core -> 1 task at a time
    .getOrCreate()
)

flights_df = spark.read.option("inferSchema", "true").json(str(FLIGHTS_PATH))

flights_df.count()

# simulate an "expensive" operation
ordered_flights_df = flights_df.orderBy("dist")

# scenario: use this DF multiple times
#
# Rule of thumb:
#   NOT serialized -> CPU efficient (no decoding on read), memory expensive (bigger objects)
#   serialized     -> memory efficient (compact bytes), costs CPU (decode on every read)
#   disk           -> saves RAM, but slow (disk I/O + decode); data on disk is ALWAYS serialized
#   (for DataFrames the gap is small: the cache is already compressed columnar batches)
#
# MEMORY_ONLY
#   PySpark: memory only, serialized      -> memory efficient, CPU cost to read
#   Scala:   memory only, NOT serialized  -> CPU efficient, memory expensive
#   both:    disk: none used (most disk efficient)
#            partitions that don't fit are not cached -> recomputed each time (CPU cost)
#
# MEMORY_ONLY_SER
#   PySpark: does not exist (PySpark MEMORY_ONLY already does this)
#   Scala:   memory only, serialized      -> memory efficient, CPU cost to read
#            disk: none used
#
# MEMORY_AND_DISK
#   PySpark: memory first, overflow to disk, serialized      -> memory efficient, CPU cost to read
#   Scala:   memory first, overflow to disk, NOT serialized  -> CPU efficient, memory expensive
#   both:    disk: only what doesn't fit in memory (overflow); those partitions are slower to read (I/O)
#
# MEMORY_AND_DISK_SER
#   PySpark: does not exist (PySpark MEMORY_AND_DISK already does this)
#   Scala:   memory first, overflow to disk, serialized      -> memory efficient, CPU cost to read
#            disk: only overflow (less overflow than MEMORY_AND_DISK, since data is smaller in memory)
#
# MEMORY_AND_DISK_DESER
#   PySpark: memory first, overflow to disk, NOT serialized  -> CPU efficient, memory expensive (= Scala MEMORY_AND_DISK)
#            disk: only overflow (more overflow, since data is bigger in memory)
#   Scala:   does not exist
#
# DISK_ONLY (_2, _3 = 2 or 3 copies)
#   both:    disk only, serialized -> most memory efficient (no RAM), slowest (I/O + decode)
#            disk: whole dataset on disk (least disk efficient; x2 / x3 with _2 / _3)
#
# OFF_HEAP
#   both:    memory outside the JVM heap, overflow to disk, serialized
#            -> memory efficient + no GC pressure, CPU cost to read
#            disk: only overflow beyond spark.memory.offHeap.size
#
# *_2 suffix (e.g. MEMORY_ONLY_2)
#   both:    same level but each partition is stored on 2 nodes
#            -> 2x whatever the base level uses (memory and/or disk), extra network to copy; gain = no recompute if a node dies
#            (Scala also has MEMORY_ONLY_SER_2, MEMORY_AND_DISK_SER_2)
#
# NONE
#   both:    not persisted (what unpersist() sets back) -> no memory, no disk, recomputed every action
#
# Eviction (all memory levels): when storage memory is full, Spark evicts old blocks (LRU)
#   -> MEMORY_ONLY*: evicted partitions are dropped and recomputed later (CPU cost)
#   -> *_AND_DISK / OFF_HEAP: evicted partitions are written to disk (disk cost)
#
# Defaults:
#   df.cache() / df.persist()   PySpark: MEMORY_AND_DISK_DESER  == Scala: MEMORY_AND_DISK
#   rdd.cache() / rdd.persist() PySpark: MEMORY_ONLY (pickled)  ~  Scala: MEMORY_ONLY (Java objects)
#
# Note: a DataFrame cache always lives in the JVM as compressed columnar batches (both languages);
# the level only decides memory/disk/off-heap and whether those batches are serialized again.
ordered_flights_df.persist(
    # no argument = MEMORY_AND_DISK_DESER (PySpark) = MEMORY_AND_DISK (Scala)
    # StorageLevel.MEMORY_ONLY
    #   PySpark: serialized -> space-efficient, more CPU to read (= Scala MEMORY_ONLY_SER)
    #   Scala:   deserialized -> fast to read, memory expensive
    #   both:    partitions that don't fit are NOT cached, recomputed when needed; disk: none used
    StorageLevel.DISK_ONLY  # disk only - saves memory, slower to read; whole dataset on disk; worth it only if recomputing is expensive
    # StorageLevel.MEMORY_AND_DISK
    #   memory first, per partition; partitions that don't fit (or are evicted) go to disk - not "both"
    #   PySpark: serialized (= Scala MEMORY_AND_DISK_SER) | Scala: deserialized (= PySpark MEMORY_AND_DISK_DESER)
    #   disk: only the overflow
    # replication:
    # StorageLevel.MEMORY_ONLY_2  # 2 copies on 2 nodes - resiliency, 2x memory (only 1 copy in local mode)
    # off-heap:
    # StorageLevel.OFF_HEAP
    #   docs: experimental, "similar to MEMORY_ONLY_SER" but off-heap; needs offHeap.enabled + offHeap.size > 0
    #   code: useDisk=True -> stored off-heap OR on disk (behaves like off-heap MEMORY_AND_DISK_SER)
    #   outside the JVM heap -> less GC pressure (G1 is the JVM default GC); serialized -> CPU cost to read
    #   disk: only overflow beyond spark.memory.offHeap.size
)

ordered_flights_df.count()  # 1st action: computes the sort + materializes the cache
ordered_flights_df.count()  # 2nd action: reads from cache

# remove from cache
ordered_flights_df.unpersist()

# named cache (shows "orderedFlights" in the Storage tab)
ordered_flights_df.createOrReplaceTempView("orderedFlights")
spark.catalog.cacheTable(
    "orderedFlights"
)  # lazy (SQL "CACHE TABLE" is eager by default)
spark.table("orderedFlights").count()  # materializes the named cache

# RDDs
flights_rdd = ordered_flights_df.rdd  # RDD of Python Row objects (costly conversion)
flights_rdd.persist(StorageLevel.MEMORY_ONLY)
#   PySpark: pickled bytes -> always serialized, equivalent to Scala MEMORY_ONLY_SER
#            (Storage tab: "Memory Serialized 1x Replicated")
#   Scala:   has BOTH, so the size difference is visible there:
#              flightsRDD.persist(StorageLevel.MEMORY_ONLY)     // deserialized Java objects -> BIGGER in memory, fastest to read
#              flightsRDD.persist(StorageLevel.MEMORY_ONLY_SER) // one byte array per partition -> SMALLER, more CPU to read
#            run each once and compare "Size in Memory" in the Storage tab
#            (docs: serialized is "generally more space-efficient than deserialized objects ... but more CPU-intensive to read")
#   PySpark cannot reproduce the deserialized case - there is no way to keep Python objects inside the JVM
flights_rdd.count()

"""
MEASURED CACHE SIZES - same data, different APIs and storage levels
=====================================================================
Input   : data/flights = 8.5 MB of JSON (8,549,942 bytes), 41,348 rows x 12 columns
Query   : spark.read.json(...).orderBy("dist")   (1 partition, local mode)
Version : Spark 3.5.0 (PySpark from venv + bundled spark-shell for Scala)
Measured: SparkContext.getRDDStorageInfo (= "Size in Memory" / "Size on Disk" in the Storage tab)

#  API      Cached object        Call                                         Storage tab label                       Size          vs JSON
-- -------  -------------------  -------------------------------------------  --------------------------------------  ------------  -------
1  Scala    RDD[Row]             rdd.persist(StorageLevel.MEMORY_ONLY)        Memory Deserialized 1x Replicated       17.78 MiB     x2.2
2  Scala    RDD[Row]             rdd.persist(StorageLevel.MEMORY_ONLY_SER)    Memory Serialized 1x Replicated          6.99 MiB     x0.86
3  Scala    RDD[Row] + Kryo      same as 2 + spark.serializer=Kryo            Memory Serialized 1x Replicated         16.94 MiB     x2.1  (!)
4  PySpark  RDD[Row] (pickled)   rdd.persist(StorageLevel.MEMORY_ONLY)        Memory Serialized 1x Replicated          2.04 MiB     x0.25
5  PySpark  DataFrame            df.persist()  -> MEMORY_AND_DISK_DESER       Disk Memory Deserialized 1x Replicated   2.88 MiB     x0.35
6  PySpark  DataFrame            df.persist(StorageLevel.MEMORY_ONLY)         Memory Serialized 1x Replicated          0.66 MiB     x0.08
7  PySpark  DataFrame            df.persist(StorageLevel.DISK_ONLY)           Disk Serialized 1x Replicated            0.66 MiB(disk) x0.08

Reading the table
- 1 vs 2 (Scala RDD): deserialized Java objects are ~2.5x bigger than the serialized bytes,
  and even bigger than the raw JSON -> this is the trade-off from the docs:
  serialized = "more space-efficient ... but more CPU-intensive to read".
- 4 (PySpark RDD): always pickled -> PySpark has no deserialized RDD level, so 1 vs 2 cannot be reproduced in Python.
  Pickle is also more compact here than Java serialization (2.04 vs 6.99 MiB).
- 5 vs 6 (DataFrame): the cache is always Tungsten columnar + compressed, but the level still matters:
    DESER      -> columnar batches kept as JVM objects   (2.88 MiB)
    serialized -> the same batches stored as byte arrays (0.66 MiB, ~12x smaller than the JSON)
- Level names differ between APIs for the same flags:
    PySpark MEMORY_ONLY      == Scala MEMORY_ONLY_SER       (deserialized=False)
    PySpark MEMORY_AND_DISK  == Scala MEMORY_AND_DISK_SER   (deserialized=False)
    PySpark df.persist() default MEMORY_AND_DISK_DESER == Scala MEMORY_AND_DISK (Dataset default)
- DataFrame vs RDD: the DataFrame cache (5/6) is smaller than any RDD cache (1-4) because Spark knows
  the schema and stores columns compactly - RDD rows are opaque objects to Spark.
- (!) 3 is NOT explained: Kryo was expected to be smaller than Java serialization (2) but measured ~2.4x bigger.
  Possible cause: unregistered classes (Kryo writes full class names) and each GenericRowWithSchema
  carrying its schema - not verified.
"""

# keep the app alive so the Spark UI (http://localhost:4040) can be inspected
time.sleep(1000000)
