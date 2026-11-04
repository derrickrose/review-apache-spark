# Iterator-to-iterator Transformations (21:19)

Source: `scala/part5rddtransformations/I2ITransformations.scala` (`printTopMetrics`, `printTopMetricsI2I`)

## Scenario
Science project: 10M metrics `(identifier, value)` (`generated/metrics/metrics10m.txt`).
Return the **10 smallest ("best")** metrics.

## Naive version
```scala
readMetrics().sortBy(_._2).take(LIMIT)
```
Sorts the **whole RDD** (range partitioning + shuffle of all 10M records) to keep 10.

## Iterator-to-iterator (I2I) version
```scala
val i2i = (records: Iterator[(String, Double)]) => {
  implicit val ordering: Ordering[(String, Double)] = Ordering.by(_._2)
  val limited = new mutable.TreeSet[(String, Double)]()
  records.foreach { r =>
    limited.add(r)
    if (limited.size > LIMIT) limited.remove(limited.last)   // keep only the 10 best
  }
  limited.iterator
}

readMetrics()
  .mapPartitions(i2i)   // top 10 per partition
  .repartition(1)       // tiny shuffle: 10 × numPartitions records
  .mapPartitions(i2i)   // global top 10
  .take(LIMIT)
```

## What an I2I transformation is
A function `Iterator[T] => Iterator[U]` passed to `mapPartitions` that **consumes the input iterator once,
as a stream**, and keeps only **bounded state** (here a `TreeSet` of at most 10 elements).
- It is a **narrow transformation**: no shuffle.
- Spark can **spill data to disk selectively** when a partition doesn't fit in memory, because the records are never
  all held in memory at once.

## Rules from the course
- ⚠️ **Don't traverse the iterator more than once.** An iterator can only be consumed once.
- ⚠️ **Don't convert it to a collection** (`toList`, `toSeq`, `toArray`, sorting). That forces the whole partition into
  memory and can OOM the executor.

## To remember
- Top-N / per-partition summaries: use `mapPartitions` + a bounded structure, then `repartition(1)` + the same
  function again.
- Shuffle 10 records per partition instead of sorting 10M.

## PySpark equivalent
```python
import heapq
def top10(it):
    return iter(heapq.nsmallest(10, it, key=lambda kv: kv[1]))  # streams, keeps 10 items
rdd.mapPartitions(top10).repartition(1).mapPartitions(top10).collect()
# or simply: rdd.takeOrdered(10, key=lambda kv: kv[1])  (same idea, built in)
```
