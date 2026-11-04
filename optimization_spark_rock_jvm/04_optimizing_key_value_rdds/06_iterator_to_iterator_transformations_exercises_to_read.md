# Iterator-to-iterator Transformations - Exercises (9:40)

Source: `scala/part5rddtransformations/I2ITransformations.scala` (`printTopMetricsEx1`, `printTopMetricsEx2`)

The exercise: explain why each of these 2 "almost right" top-10 implementations is better than the naive `sortBy`
but worse than the I2I version.

## Exercise 1: sort each partition
```scala
readMetrics()
  .mapPartitions(_.toList.sortBy(_._2).take(LIMIT).iterator)
  .repartition(1)
  .mapPartitions(_.toList.sortBy(_._2).take(LIMIT).iterator)
  .take(LIMIT)
```
- ✅ Better than the naive version: it doesn't sort the whole RDD, and only a tiny amount of data is shuffled.
- ❌ It sorts the **entire partition** (O(n log n)) to keep 10 items.
- ❌ `toList` **forces the iterator into memory**, which can OOM the executors.

## Exercise 2: TreeSet, but after `toList`
```scala
.mapPartitions { records =>
  val limited = new mutable.TreeSet[(String, Double)]()(Ordering.by(_._2))
  records.toList.foreach { r => limited.add(r); if (limited.size > LIMIT) limited.remove(limited.last) }
  limited.iterator
}
```
- ✅ Better than ex. 1: it extracts the top 10 with a bounded structure instead of sorting everything.
- ❌ `toList` still **materializes the partition**, so it can still OOM.
- ❌ It iterates **twice** (once to build the list, once in `foreach`).
- ❌ Building an immutable `List` allocates a cons cell per record, which adds GC time (link to *Reusing JVM Objects*).

## The fix
Remove `.toList`: `records.foreach { ... }` directly on the iterator. That is exactly `printTopMetricsI2I`
(previous lesson).

## Takeaway
I2I quality checklist:
1. one pass over the iterator,
2. no conversion to a collection,
3. bounded state,
4. no unnecessary allocations.
