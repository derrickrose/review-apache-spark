# Cogrouping (20:30)

Source: [`scala/part4rddjoins/CogroupingRDDs.scala`](../scala/part4rddjoins/CogroupingRDDs.scala)

## Scenario
Same exam data plus a third file, `examEmails.txt` (id, email).
For every candidate: if the best attempt is ≥ 9.0, send "PASSED" to their email, otherwise "FAILED".

Data: same exam files as lesson 01 (see the *Data* section there).

## Plain version: 2 chained joins
```scala
val scores = readExamScores().reduceByKey(Math.max)
candidates
  .join(scores)   // RDD[(Long, (String, Double))]
  .join(emails)   // RDD[(Long, ((String, Double), String))]
  .mapValues { case ((_, maxAttempt), email) =>
    if (maxAttempt >= 9.0) (email, "PASSED") else (email, "FAILED")
  }
```
Each `join` is its own shuffle stage.

## Cogroup version: 3 RDDs grouped in one go
```scala
candidates.cogroup(scores, emails)
// RDD[(Long, (Iterable[String], Iterable[Double], Iterable[String]))]
  .mapValues { case (nameIt, maxAttemptIt, emailIt) =>
    for {
      e <- emailIt.headOption
      s <- maxAttemptIt.headOption
    } yield (e, if (s >= 9.0) "PASSED" else "FAILED")
  }   // RDD[(Long, Option[(String, String)])]
```
- `cogroup` **co-partitions all 3 RDDs** with one partitioner and groups them in a single stage.
  That stage is cheaper than two chained joins.
- `join` in Spark is implemented on top of `cogroup`. Calling `cogroup` directly lets you skip the
  intermediate tuples and choose the join semantics yourself (here `Option` handles missing keys).

## To remember
- When joining **3+ RDDs on the same key**, use `cogroup` instead of chaining `join`s.
- The values come back as `Iterable`s, so use `headOption` when you expect one value per key.
- Pre-aggregate first (`reduceByKey(Math.max)`) so each key has one score.

## Notes on the code
- **Different pass threshold from lesson 01:** `SimpleRDDJoins` counts a pass as `> 9.0`, while `CogroupingRDDs` uses
  `>= 9.0`. With scores in steps of 0.1, a best attempt of exactly `9.0` passes here but fails in lesson 01.
- `coGroupedJoin` calls `result.count()` twice. The second call recomputes the whole lineage because nothing is cached.
  Look at it in the UI if the second job surprises you.

## PySpark gotcha
PySpark's `rdd.cogroup(other, numPartitions=None)` accepts **only one** other RDD.
`candidates.cogroup(scores, emails)` passes `emails` as `numPartitions` and fails with a confusing
`RDD_TRANSFORM_ONLY_VALID_ON_DRIVER` pickling error. The N-way version is **`groupWith`**:
```python
candidates.groupWith(scores, emails)   # (id, (names, scores, emails)) as ResultIterables
```
See [`02_cogrouping_rdds.py`](02_cogrouping_rdds.py).
