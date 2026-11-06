# Reusing JVM Objects, Part 2 (12:11)

Source: [`scala/part5rddtransformations/ReusingObjects.scala`](../scala/part5rddtransformations/ReusingObjects.scala), version 3 (`UglyTextStats`)

## Version 3: raw JVM `Array[Int]` + while loops
Push the idea from part 1 to the extreme:
```scala
object UglyTextStats extends Serializable {
  val nLinesIndex = 0; val nWordsIndex = 1; val longestWordIndex = 2; val occurrencesIndex = 3

  def aggregateNewRecord(stats: Array[Int], record: String): Array[Int] = {
    val newWords = record.split(" ")
    var i = 0
    while (i < newWords.length) {          // while loop: no closures, no iterator objects
      val word = newWords(i)
      stats(longestWordIndex) = math.max(word.length, stats(longestWordIndex))
      stats(occurrencesIndex) += (if (word == criticalWord) 1 else 0)
      i += 1
    }
    stats(nLinesIndex) += 1
    stats(nWordsIndex) += newWords.length
    stats
  }
  def combineStats(s1: Array[Int], s2: Array[Int]): Array[Int] = { ...; s1 }
}

text.aggregateByKey(Array.fill(4)(0))(UglyTextStats.aggregateNewRecord, UglyTextStats.combineStats)
```

## What changes compared to version 2
- `Array[Int]` is a **primitive JVM array**: no object header per field, no boxing, compact to serialize.
- **One pass** over the words instead of 2 (`maxBy` + `count` in v1/v2), with a `while` loop,
  so no lambda or iterator allocations.
- It's ugly (magic indices, no names). That's the price for the fastest version.

## Comparing the 3 versions
`main` runs `collectStats()`, `collectStats2()` and `collectStats3()` one after the other. Compare their job durations
and **GC time** in the Spark UI. Each version is faster than the previous one.

## To remember
- Immutable case class < mutable class < primitive arrays + while loops, in speed (and the reverse in readability).
- Only go "ugly" on proven hot paths: aggregations over millions of records where the UI shows GC/CPU as the bottleneck.
- The same thinking explains why DataFrames (Tungsten's binary rows) beat RDDs of objects.
