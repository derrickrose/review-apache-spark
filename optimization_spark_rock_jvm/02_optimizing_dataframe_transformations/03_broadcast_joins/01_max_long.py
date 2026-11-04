import time
from pyspark.sql import SparkSession, Row
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

# Doc: 00_broadcast_joins.md, sections 1 (the idea in short) and 2 (the threshold)
#
# Why the innocent join (01_innocent_join.py) is slow:
# Spark doesn't know the size of a DataFrame created from an RDD, so it assumes the worst:
# sizeInBytes = spark.sql.defaultSizeInBytes = Long.MaxValue bytes (~9.2 EB).
# That is far above spark.sql.autoBroadcastJoinThreshold (10 MB), so Spark treats the
# 4-row table as huge, never broadcasts it, and falls back to a SortMergeJoin
# (shuffle + sort of both sides, including the 100M-row table).

spark = (
    SparkSession.builder.appName("Long.MaxValue")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)
sc = spark.sparkContext


def stats(df):
    s = df._jdf.queryExecution().optimizedPlan().stats()
    row_count = s.rowCount()
    return int(s.sizeInBytes().toString()), (
        row_count.get().toString() if row_count.isDefined() else None
    )


# 4 rows, but created from an RDD -> Spark can't measure its size
lookup_table = spark.createDataFrame(
    sc.parallelize(
        [Row(0, "zero"), Row(1, "first"), Row(2, "second"), Row(3, "third")]
    ),
    StructType([StructField("id", IntegerType()), StructField("order", StringType())]),
)

LONG_MAX = 2**63 - 1
size, row_count = stats(lookup_table)
print("sizeInBytes == Long.MaxValue :", size == LONG_MAX)  # expected: True
print("≈ exaoctets                  :", size / 10**18)  # expected: ≈ 9.22 (≈ 8 EiB)
print(
    "rowCount                     :", row_count
)  # expected: None -> it's a size in bytes, not a row count

# Table from section 2: for a range, Spark knows the exact size
print("range(1, 10)          :", stats(spark.range(1, 10)))  # expected: (72, '9')
print(
    "range(1, 100000000)   :", stats(spark.range(1, 100_000_000))
)  # expected: (799999992, '99999999')

table = spark.range(1, 100_000_000)

# RDD: no broadcast despite its 4 rows, because Spark thinks it's Long.MaxValue bytes
# expected: SortMergeJoin (slow: both sides shuffled and sorted)
table.join(lookup_table, "id").explain()

# range(1, 10): 72 bytes < 10 MB -> broadcast automatically
# expected: BroadcastHashJoin
table.join(spark.range(1, 10), "id").explain()

if __name__ == "__main__":
    time.sleep(1000)
