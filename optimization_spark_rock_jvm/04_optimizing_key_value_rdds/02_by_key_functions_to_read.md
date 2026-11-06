# By Key Functions (23:10)

Source: [`scala/part5rddtransformations/ByKeyFunctions.scala`](../scala/part5rddtransformations/ByKeyFunctions.scala) (run on the Docker cluster, `master("local[2]")` in the file)

## Scenario
`wordCounts`: 2M random `(word, occurrences)` pairs, with words picked from `words.txt`.
Goal: the total count per word, returned with `collectAsMap()`.

Data: `words.txt` is the same file as [`data/lipsum/words.txt`](../../data/lipsum/words.txt) in your repo. The pairs
are generated on the driver with `Seq.fill(2000000)` and then `sc.parallelize`d, so all 2M tuples are built in driver
memory first.

## 1. `groupByKey` + `mapValues(_.sum)`: the intuitive, dangerous version
```scala
wordCounts.groupByKey().mapValues(_.sum)   // about 6s, shuffle write = the entire dataset
```
`groupByKey` is dangerous in 2 ways:
- it **shuffles every value** so that all data for a key ends up on one machine;
- with **skewed** data, the values of one key may not fit in an executor's memory, which causes an OOM.

## 2. `reduceByKey`
```scala
wordCounts.reduceByKey(_ + _)
```
- Does a **partial aggregation on the executor before the shuffle** ("map-side").
- Shuffles much less data and avoids the skew/OOM problem.

## 3. `foldByKey`
```scala
wordCounts.foldByKey(0)(_ + _)
```
Like `reduceByKey` but with a zero value. Similar performance.

## 4. `aggregateByKey`
```scala
wordCounts.aggregateByKey(0.0)(_ + _, _ + _)
```
- Zero value + **2 functions**: (aggregate, record) → aggregate, and (aggregate, aggregate) → aggregate.
- The output type can differ from the value type (here `Int` → `Double`). Similar performance.

## 5. `combineByKey`: the most general one
```scala
wordCounts.combineByKey(
  (count: Int) => count,                       // createCombiner: value → aggregate
  (sum: Int, v: Int) => sum + v,               // mergeValue: inside a partition
  (s1: Int, s2: Int) => s1 + s2,               // mergeCombiners: across partitions
  numPartitions = 10                           // or a Partitioner
)
```
- All the others are built on it.
- Lets you choose the **output partitioning**, so later joins can be shuffle-free (link to lesson 01 of the previous section).
- ⚠️ It can be **as dangerous as `groupByKey`** if your functions make the data grow (e.g. appending to a list)
  instead of reducing it.

## To remember
- Never `groupByKey` just to aggregate. Use `reduceByKey` / `foldByKey` / `aggregateByKey` / `combineByKey`.
- They are all fast **when the functions reduce the data**.
- Compare the **shuffle write** in the Spark UI: that is where the difference shows.
- `collectAsMap()` itself still costs about 2s, because the result travels to the driver.
