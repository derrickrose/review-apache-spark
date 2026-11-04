# Broadcast Joins (14:46)

Source: `scala/part4rddjoins/RDDBroadcastJoins.scala` (shown on camera in the Spark Shell)

## Scenario
A competition with 10M participants. `prizes` is a tiny lookup RDD `(1, gold), (2, silver), (3, bronze)`,
and `leaderboard` is `RDD[(Int, String)]` with 10M (rank, name) pairs. Goal: who won what?

## Plain join
```scala
val medalists = leaderboard.join(prizes)   // shuffles 10M rows to match 3 rows
```
This takes about 38s for 10M elements, according to the course comments.

## Manual broadcast join
The RDD API has no automatic broadcast like `spark.sql.autoBroadcastJoinThreshold`, so you do it yourself:
1. Collect the small RDD to the driver: `prizes.collectAsMap()`.
2. Broadcast it to the executors.
3. Look the keys up on each partition of the big RDD with **`mapPartitions` + `flatMap`**. No shuffle.
```scala
val improvedMedalists = leaderboard.mapPartitions { iterator =>
  iterator.flatMap { case (index, name) =>
    medalsMap.get(index) match {
      case None => Seq.empty           // inner join: drop non-matching rows
      case Some(medal) => Seq((name, medal))
    }
  }
}
```
This takes about 2s and has no shuffle.

## ⚠️ Mistake in the course code
```scala
sc.broadcast(medalsMap)   // return value is discarded!
... medalsMap.get(index)  // uses the local Map, captured in the closure
```
The `Broadcast` handle is never used. The code works because the closure **captures `medalsMap` directly**,
so Spark serializes the map **into every task** instead of shipping it once per executor through the broadcast mechanism.
That's fine for 3 entries, but wrong for a large lookup table. The correct version is:
```scala
val medalsBc = sc.broadcast(prizes.collectAsMap())
leaderboard.mapPartitions(_.flatMap { case (i, name) => medalsBc.value.get(i).map(m => (name, m)) })
```
PySpark: `bc = sc.broadcast(prizes.collectAsMap())`, then use `bc.value` inside the function.

## To remember
- Broadcast join on RDDs = `collectAsMap` + `sc.broadcast` + map-side lookup.
- You implement the join type yourself (`None` → drop for an inner join, keep with `None` for a left join).
- The small side must fit in driver and executor memory.
