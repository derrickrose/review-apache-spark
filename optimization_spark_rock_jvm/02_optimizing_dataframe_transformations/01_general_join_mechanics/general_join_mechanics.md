## Join Types

- inner
- left_outer
- right_outer
- full_outer
- cross : n rows left * m rows right (dangerous) — DF: `crossJoin()`, RDD: `cartesian()`

## More join types (DFs only, not RDD)

- left_semi : all rows in the left DF for which there is a row in the right DF passing the condition (like `EXISTS` in
  SQL)
- left_anti : all rows in the left DF for which there is no row in the right DF passing the condition (like `NOT EXISTS`
  in SQL)

## Why are joins slow?

If DFs or RDDs don't have a known partitioner (a partition scheme Spark knows in advance), a shuffle is needed:

- data transfer overhead
- potential OOMs (partitions must fit in memory; data skew makes some partitions much bigger)
- limited parallelism (shuffle is a bottleneck to parallelism)

### Co-partitioned RDDs

- same partitioner (for `HashPartitioner`: same number of partitions)
- may be on different executors
- joined with some network traffic, but much less than a full shuffle
- narrow dependency (no shuffle)

### Co-located RDDs

- same partitioner
- corresponding partitions reside in memory on the same executor
- joined without network transfer, no shuffle

## Shuffled Join

- no partitioner is known
- rows with the same key must end up in the same partition
- Spark shuffles both RDDs
- very expensive

## Optimized Join

One RDD has no known partitioner, or the partitioners are different

- join reuses an existing partitioner (`defaultPartitioner`), only the other RDD is shuffled
- one shuffle instead of two
- exception: if the existing partitioner is not eligible (10x or more fewer partitions than the largest RDD AND fewer
  than the default number of partitions), Spark creates a new `HashPartitioner` → both RDDs are shuffled
- **Scala/Java only.** PySpark implements `join` as `union` + `groupByKey`: if only one side is partitioned, **both**
  sides are shuffled again

## Optimized Join +

Both RDDs have the same partitioner (co-partitioned)

- fetch the existing partitions and do the join
- no shuffle
- narrow dependency (`OneToOneDependency`)
- also works in PySpark (both sides `partitionBy(n)` with the same `n`), through a `PartitionerAwareUnionRDD` instead of
  `OneToOneDependency`

## Optimized Join ++

Same partitioner, partitions cached in memory on the same executors (co-located)

- no partition fetching
- no shuffle
- no network transfer
- fastest join possible

## Notes

- You can force a partitioner with `partitionBy()` so no shuffle is needed before the join, but `partitionBy()` is
  itself a shuffle: it only pays off if you `persist()` the result and reuse it
- `partitionBy()` on an RDD that already has that exact partitioner is a no-op (no shuffle)
- `map()` drops the partitioner (`preservesPartitioning=false` by default); use `mapValues()` / `flatMapValues()` to
  keep it, or `map(f, preservesPartitioning=True)` if `f` doesn't change the keys
- Row explosion is not specific to outer/cross joins: any join on duplicated keys