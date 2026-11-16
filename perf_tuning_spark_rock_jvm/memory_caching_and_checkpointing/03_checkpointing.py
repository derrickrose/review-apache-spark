import time
from pathlib import Path

from pyspark import StorageLevel
from pyspark.sql import SparkSession

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
FLIGHTS_PATH = DATA_DIR / "flights"
CHECKPOINT_DIR = Path(__file__).resolve().parent / "spark-warehouse"

spark = (
    SparkSession.builder.appName("Checkpointing")
    .master("local")  # 1 core -> 1 task at a time
    .getOrCreate()
)

sc = spark.sparkContext

# checkpointing needs a directory (on a cluster: a reliable FS like HDFS/S3, not local disk)
sc.setCheckpointDir(str(CHECKPOINT_DIR))


def read_flights():
    return spark.read.option("inferSchema", "true").json(str(FLIGHTS_PATH))


# Checkpoint vs cache
#
#                      cache / persist                       checkpoint
#   stored where       executor memory and/or local disk     checkpoint dir (reliable storage: HDFS/S3)
#   lineage            KEPT (can recompute lost partitions)   CUT (plan starts from the saved files)
#   if executor dies   lost partitions recomputed from lineage data still in the checkpoint dir
#   after the app      gone                                   files stay (Spark does not delete them by default,
#                                                             see spark.cleaner.referenceTracking.cleanCheckpoints)
#   cost               cheap-ish (memory / local disk)        expensive: full write to (distributed) storage
#   use when           reuse a result several times           very long lineage / iterative jobs (ML, graphs),
#                                                             avoid recomputing from scratch after a failure
#
# localCheckpoint(): cuts lineage too, but stores on executor local storage -> faster, NOT fault tolerant.


def demo_checkpoint():
    flights_df = read_flights()

    # do some expensive computation
    ordered_flights_df = flights_df.orderBy("dist")

    # checkpoint a DF = save the DF to disk
    # eager=True (default) -> runs a job now (it behaves like an action) and returns a NEW DataFrame
    checkpointed_flights_df = ordered_flights_df.checkpoint()

    # query plan difference with checkpointed DFs
    ordered_flights_df.explain()
    # output - before checkpoint: Sort <- Exchange <- FileScan json (the whole lineage)
    #   == Physical Plan ==
    #   AdaptiveSparkPlan isFinalPlan=false
    #   +- Sort [dist ASC NULLS FIRST], true, 0
    #      +- Exchange rangepartitioning(dist ASC NULLS FIRST, 200), ENSURE_REQUIREMENTS
    #         +- FileScan json [_id, arrdelay, carrier, ...] Location: .../data/flights

    checkpointed_flights_df.explain()
    # output - after checkpoint: the plan starts from the checkpointed data, lineage is gone
    #   == Physical Plan ==
    #   *(1) Scan ExistingRDD[_id, arrdelay, carrier, ...]

    checkpointed_flights_df.show()


def caching_job_rdd():
    numbers = sc.parallelize(range(1, 10_000_001))
    # persist() / cache() mark THIS RDD in place (lazy, filled at the next action) AND return
    # the same object (self) -> chaining like here works, reassigning is optional (not wrong).
    # Different from rdd.checkpoint(), which returns None - see checkpointing_job_rdd.
    desc_numbers = numbers.sortBy(lambda x: -x).persist(StorageLevel.DISK_ONLY)
    desc_numbers.sum()  # job computes the sort + writes the cache
    desc_numbers.sum()  # shorter time here (reads from the cache)
    # check it worked:
    #   desc_numbers.is_cached          -> True
    #   desc_numbers.getStorageLevel()  -> Disk Serialized 1x Replicated


def checkpointing_job_rdd():
    numbers = sc.parallelize(range(1, 10_000_001))
    desc_numbers = numbers.sortBy(lambda x: -x)
    # RDD checkpoint is LAZY and returns None (Scala: Unit) - it only marks the RDD.
    # On the next action Spark runs the job, THEN launches a 2nd job that recomputes the RDD
    # to write it to the checkpoint dir -> the RDD is computed twice.
    # Tip: persist() before checkpoint() so the 2nd job reads the cache instead of recomputing.
    #
    # NO reassignment: checkpoint() marks THIS RDD in place and returns None
    #   desc_numbers = desc_numbers.checkpoint()  # WRONG -> desc_numbers is None
    #   desc_numbers.sum()                        # AttributeError: 'NoneType' object has no attribute 'sum'
    # (the opposite of df.checkpoint(), which returns a new DF - see checkpointing_job_df)
    #
    #                      rdd.checkpoint()               df.checkpoint()
    #   returns            None (Scala: Unit)             a new DataFrame
    #   changes object     yes (marks the RDD)            no (original DF keeps its full plan)
    #   when it runs       lazy, at the next action       now (eager=True by default)
    #   reassign?          no                             yes
    desc_numbers.checkpoint()
    desc_numbers.sum()  # job + checkpoint job
    desc_numbers.sum()  # reads from the checkpoint files -> shorter
    # check it worked:
    #   desc_numbers.isCheckpointed()     -> True
    #   desc_numbers.getCheckpointFile()  -> path inside spark-warehouse/


def caching_job_df():
    flights_df = read_flights()

    ordered_flights_df = flights_df.orderBy("dist")
    # NO reassignment needed: persist() / cache() mark THIS DF in place and return the same DF (self)
    #   ordered_flights_df = ordered_flights_df.persist(...)  # also fine, same object
    # lazy: nothing is cached until the next action. Lineage is kept (plan shows InMemoryTableScan).
    # Different from df.checkpoint(), which returns a NEW DF you must use - see checkpointing_job_df.
    #
    #                      persist() / cache()            checkpoint()
    #   returns            same object (self)             RDD: None | DF: a new DataFrame
    #   changes object     yes (marks it)                 RDD: yes  | DF: no
    #   when it runs       lazy, at the next action       RDD: lazy | DF: now (eager=True)
    #   reassign?          optional                       RDD: no   | DF: yes
    #   lineage            kept                           cut
    ordered_flights_df.persist(StorageLevel.DISK_ONLY)
    ordered_flights_df.count()  # job computes the sort + writes the cache
    ordered_flights_df.count()  # shorter job (reads from the cache)
    # check it worked:
    #   ordered_flights_df.is_cached     -> True
    #   ordered_flights_df.storageLevel  -> Disk Serialized 1x Replicated


def checkpointing_job_df():
    flights_df = read_flights()

    ordered_flights_df = flights_df.orderBy("dist")
    # DF checkpoint is EAGER by default and returns a new DF -> always use the returned DF
    # (calling ordered_flights_df.count() would still run the original plan)
    checkpointed_flights_df = ordered_flights_df.checkpoint()
    checkpointed_flights_df.count()
    checkpointed_flights_df.count()


if __name__ == "__main__":
    caching_job_df()
    checkpointing_job_df()

    # keep the app alive so the Spark UI (http://localhost:4040) can be inspected:
    # compare the jobs of the caching vs checkpointing functions
    time.sleep(1000000)
