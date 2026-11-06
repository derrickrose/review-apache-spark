# RDD Transformations (5:06)

Short intro lesson. There is **no source file** for it in [`scala/part5rddtransformations/`](../scala/part5rddtransformations/), so this note is
inferred from the section content.

## What the section is about
Once the data is a key-value RDD, performance depends on **how you write the transformations**, because
Spark will not rewrite them for you:
1. **Which by-key function** you pick decides how much data is shuffled → *By Key Functions*.
2. **How many objects you allocate** per record decides GC pressure → *Reusing JVM Objects*.
3. **Whether you keep partitions as iterators** decides whether executors OOM or spill → *Iterator-to-iterator*.

## Prerequisites to keep in mind
- Narrow transformations (`map`, `filter`, `mapValues`, `mapPartitions`) stay in the same stage.
- Wide transformations (`groupByKey`, `reduceByKey`, `aggregateByKey`, `join`, `repartition`, `sortBy`) shuffle
  and start a new stage.
- "Map-side" work = work done on the executors **before** the shuffle (partial aggregation).
