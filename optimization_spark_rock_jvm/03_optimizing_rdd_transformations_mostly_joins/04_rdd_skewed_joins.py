"""
PySpark port of scala/part4rddjoins/RDDSkewedJoins.scala
Notes: 04_skewed_joins_to_read.md

An online store selling gaming laptops.
2 laptops are "similar" if they have the same make & model, but proc speed within 0.1.
For each laptop, compute the average sale price of "similar" offers.

~57% of rows are Razer Blade -> joining on (make, model) is skewed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.rdd_data_generator import random_laptop, random_laptop_offer  # noqa: E402
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

spark = get_spark("RDD Skewed Joins")
sc = spark.sparkContext

# Course: 40k laptops x 100k offers. The plain join on (make, model) then builds ~1.3 BILLION
# Razer Blade pairs alone (~23k x ~57k) - fine-ish on the JVM, hours in Python workers.
# 10x smaller here (~13M pairs) keeps the same skew. SCALE=1 for course sizes.
import os  # noqa: E402

SCALE = int(os.environ.get("SCALE", "10"))
laptops = sc.parallelize([random_laptop() for _ in range(40_000 // SCALE)])
laptop_offers = sc.parallelize([random_laptop_offer() for _ in range(100_000 // SCALE)])


def average(rdd):
    """(reg, sale_price) -> (reg, avg price), with a (sum, count) accumulator."""
    return rdd.aggregateByKey(
        (0.0, 0),
        lambda acc, price: (acc[0] + price, acc[1] + 1),  # state + record
        lambda a, b: (a[0] + b[0], a[1] + b[1]),  # state + state
    ).mapValues(lambda s: s[0] / s[1])


def plain_join():
    prepared_laptops = laptops.map(
        lambda l: ((l.make, l.model), (l.registration, l.proc_speed))
    )
    prepared_offers = laptop_offers.map(
        lambda o: ((o.make, o.model), (o.proc_speed, o.sale_price))
    )

    matches = (
        prepared_laptops.join(
            prepared_offers
        )  # ((make, model), ((reg, cpu), (cpu, price)))
        # Scala uses <= 0.1 on raw doubles: 3.3 - 3.2 = 0.0999... OK, 3.2 - 3.1 = 0.1000...004 KO!
        # compare in tenths to get the intended rule
        .filter(
            lambda kv: abs(round(kv[1][0][1] * 10) - round(kv[1][1][0] * 10)) <= 1
        ).map(lambda kv: (kv[1][0][0], kv[1][1][1]))
    )
    return average(matches)


def no_skew_join():
    # put proc speed in the key: explode each laptop to speed-0.1, speed, speed+0.1.
    # Keys are integer tenths: the Scala version uses doubles (3.2 + 0.1 = 3.3000000000000003)
    # and silently loses matches.
    def explode(l):
        tenths = round(l.proc_speed * 10)
        return [
            ((l.make, l.model, t), l.registration)
            for t in (tenths - 1, tenths, tenths + 1)
        ]

    prepared_laptops = laptops.flatMap(explode)
    prepared_offers = laptop_offers.map(
        lambda o: ((o.make, o.model, round(o.proc_speed * 10)), o.sale_price)
    )

    # exact join, only matching rows, no filter needed
    return average(prepared_laptops.join(prepared_offers).map(lambda kv: kv[1]))


if __name__ == "__main__":
    plain = timed("plain_join", lambda: plain_join().collectAsMap())
    no_skew = timed("no_skew_join", lambda: no_skew_join().collectAsMap())
    same = plain.keys() == no_skew.keys() and all(
        abs(plain[k] - no_skew[k]) < 1e-6 for k in plain
    )
    print("same results:", same)
    keep_ui_open()
