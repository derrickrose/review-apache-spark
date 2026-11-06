# Optimizing RDD Transformations (Mostly Joins)

Course source: [`scala/part4rddjoins/`](../scala/part4rddjoins/)

| # | Lesson | Duration | Notes | Source |
|---|--------|----------|-------|--------|
| 1 | Optimizing RDD Joins | 24:38 | [01_optimizing_rdd_joins_to_read.md](01_optimizing_rdd_joins_to_read.md) | [`SimpleRDDJoins.scala`](../scala/part4rddjoins/SimpleRDDJoins.scala) |
| 2 | Cogrouping | 20:30 | [02_cogrouping_to_read.md](02_cogrouping_to_read.md) | [`CogroupingRDDs.scala`](../scala/part4rddjoins/CogroupingRDDs.scala) |
| 3 | Broadcast Joins | 14:46 | [03_broadcast_joins_to_read.md](03_broadcast_joins_to_read.md) | [`RDDBroadcastJoins.scala`](../scala/part4rddjoins/RDDBroadcastJoins.scala) |
| 4 | Skewed Joins | 31:26 | [04_skewed_joins_to_read.md](04_skewed_joins_to_read.md) | [`RDDSkewedJoins.scala`](../scala/part4rddjoins/RDDSkewedJoins.scala) |

Common thread: the RDD API has **no Catalyst, no AQE, no automatic broadcast**. Spark executes exactly
what you write, so the techniques from the DataFrame section must be applied **by hand**.

## PySpark scripts

Run `python -m common.rdd_data_generator` once from `optimization_spark_rock_jvm/` first ([`common/rdd_data_generator.py`](../common/rdd_data_generator.py), writes `generated_data/`, git-ignored).
Each script prints timings, then keeps the Spark UI (http://localhost:4040) open; `KEEP_UI=0` to exit right away.

| Script | What it compares |
|---|---|
| [`01_simple_rdd_joins.py`](01_simple_rdd_joins.py) | 5 versions: plain, pre-aggregate, pre-filter, co-partition, combined |
| [`02_cogrouping_rdds.py`](02_cogrouping_rdds.py) | 2 chained joins vs one N-way cogroup (`groupWith` in PySpark) |
| [`03_rdd_broadcast_joins.py`](03_rdd_broadcast_joins.py) | shuffle join vs manual broadcast + `mapPartitions` lookup |
| [`04_rdd_skewed_joins.py`](04_rdd_skewed_joins.py) | skewed `(make, model)` join vs exploded `(make, model, speed)` key; 10x smaller by default (`SCALE=1` for course sizes) |
