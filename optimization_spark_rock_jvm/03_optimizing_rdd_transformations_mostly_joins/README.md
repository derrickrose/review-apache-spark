# Optimizing RDD Transformations (Mostly Joins)

Course source: `scala/part4rddjoins/`

| # | Lesson | Duration | Notes | Source |
|---|--------|----------|-------|--------|
| 1 | Optimizing RDD Joins | 24:38 | [01_optimizing_rdd_joins_to_read.md](01_optimizing_rdd_joins_to_read.md) | `SimpleRDDJoins.scala` |
| 2 | Cogrouping | 20:30 | [02_cogrouping_to_read.md](02_cogrouping_to_read.md) | `CogroupingRDDs.scala` |
| 3 | Broadcast Joins | 14:46 | [03_broadcast_joins_to_read.md](03_broadcast_joins_to_read.md) | `RDDBroadcastJoins.scala` |
| 4 | Skewed Joins | 31:26 | [04_skewed_joins_to_read.md](04_skewed_joins_to_read.md) | `RDDSkewedJoins.scala` |

Common thread: the RDD API has **no Catalyst, no AQE, no automatic broadcast**. Spark executes exactly
what you write, so the techniques from the DataFrame section must be applied **by hand**.
