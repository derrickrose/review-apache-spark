# data skew: skewed join vs salted join
#
# the join key is (make, model) and MAKES[0] carries 50% of the rows, so half
# the sales land on 20 of the 100 keys. the soundScore predicate is applied
# after the equi-join, so each key first materializes its full cross product —
# that is the cost the salt breaks up.

import time

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
)

from generator import make_guitars, make_guitar_sales


SHUFFLE_PARTITIONS = 100
N_GUITARS = 40_000
N_SALES = 5_000_000
SALT_INTERVAL = 100  # salting interval 0-99

spark = (
    SparkSession.builder.appName("data_skew")
    .master("local[*]")
    # broadcast would remove the shuffle entirely and hide the skew
    .config("spark.sql.autoBroadcastJoinThreshold", -1)
    # AQE would split the skewed partitions for us
    .config("spark.sql.adaptive.enabled", False)
    .config("spark.sql.shuffle.partitions", SHUFFLE_PARTITIONS)
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

GUITAR_SCHEMA = StructType(
    [
        StructField("configurationId", StringType()),
        StructField("make", StringType()),
        StructField("model", StringType()),
        StructField("soundScore", DoubleType()),
    ]
)

GUITAR_SALE_SCHEMA = StructType(
    [
        StructField("registration", StringType()),
        StructField("make", StringType()),
        StructField("model", StringType()),
        StructField("soundScore", DoubleType()),
        StructField("salePrice", DoubleType()),
    ]
)


def timed(label, fn):
    """run fn, print how long it took and what it returned"""
    start = time.time()
    result = fn()
    print(f"{label}: {result} rows in {time.time() - start:.1f}s")
    return result


def show_partition_skew(df, keys, label):
    """
    row count per shuffle partition after hashing on keys — this is what the
    join tasks will each have to chew through.
    """
    counts = (
        df.repartition(SHUFFLE_PARTITIONS, *[F.col(k) for k in keys])
        .withColumn("pid", F.spark_partition_id())
        .groupBy("pid")
        .count()
    )
    stats = counts.agg(
        F.min("count").alias("min"),
        F.expr("percentile_approx(count, 0.5)").alias("median"),
        F.max("count").alias("max"),
        F.count("*").alias("non_empty_partitions"),
    ).first()

    ratio = stats["max"] / stats["median"] if stats["median"] else float("nan")
    print(
        f"{label} on {keys}: min={stats['min']} median={stats['median']} "
        f"max={stats['max']} max/median={ratio:.1f}x "
        f"non_empty={stats['non_empty_partitions']}/{SHUFFLE_PARTITIONS}"
    )


def skew_solution(guitars, guitar_sales):
    """the naive join: every row of a (make, model) key lands in one partition"""
    skewed_join = (
        guitars.join(guitar_sales, ["make", "model"])
        .where(F.abs(guitar_sales["soundScore"] - guitars["soundScore"]) <= 0.1)
        .groupBy("configurationId")
        .agg(F.avg("salePrice").alias("averagePrice"))
    )

    skewed_join.explain()
    return skewed_join.count()


def no_skew_solution(guitars, guitar_sales):
    """
    salted join: spread each key across SALT_INTERVAL partitions.

    the sales side gets one random salt per row; the guitars side is exploded
    over every salt value so each sales row still meets all of its matches.
    correctness is unchanged, the key is just SALT_INTERVAL times more diverse.
    """
    # multiplying the guitars DF x100
    exploded_guitars = guitars.withColumn(
        "salt", F.explode(F.sequence(F.lit(0), F.lit(SALT_INTERVAL - 1)))
    )
    # deterministic salt: survives task retries and recomputation, unlike rand()
    salted_guitar_sales = guitar_sales.withColumn(
        "salt", F.pmod(F.hash("registration"), F.lit(SALT_INTERVAL))
    )

    non_skewed_join = (
        exploded_guitars.join(salted_guitar_sales, ["make", "model", "salt"])
        .where(
            F.abs(salted_guitar_sales["soundScore"] - exploded_guitars["soundScore"])
            <= 0.1
        )
        .groupBy("configurationId")
        .agg(F.avg("salePrice").alias("averagePrice"))
    )

    non_skewed_join.explain()
    return non_skewed_join.count()


if __name__ == "__main__":
    guitars = spark.createDataFrame(make_guitars(N_GUITARS, seed=1), GUITAR_SCHEMA)
    guitar_sales = spark.createDataFrame(
        make_guitar_sales(N_SALES, seed=2), GUITAR_SALE_SCHEMA
    )

    # where the skew is, before any join runs
    # show_partition_skew(guitar_sales, ["make", "model"], "sales")
    # show_partition_skew(
    #     guitar_sales.withColumn(
    #         "salt", F.pmod(F.hash("registration"), F.lit(SALT_INTERVAL))
    #     ),
    #     ["make", "model", "salt"],
    #     "sales salted",
    # )

    # skewed = timed("skewed", lambda: skew_solution(guitars, guitar_sales))
    salted = timed("salted", lambda: no_skew_solution(guitars, guitar_sales))
    # both paths must agree — salting changes the partitioning, not the result
    # print(f"same result: {skewed == salted}")

    # keep the spark UI (http://localhost:4040) alive to compare the stages
    time.sleep(1000)
