## Join Types

- inner
- left_outer
- right_outer
- full_outer

## More join types (DFs only not RDD)

- left_semi : all the rows in the left DF for which there is a row in the right DF passing the condition (behave like
  exits in )
- left_anti : all ther rows in the left DF for which there is no row in the right DF passing the condition (behave like
  not exits in )
- cross_join : n rows left * m rows right (dangerous), also the outer if duplicates can make disaster on explode also

## Why are joins slow ?

If DFs or RDDs dont have a known partitioner, a shuffle is needed

- data transfer overhead
- potential OOMs (have to fit in memory )
- limited parallelism

### Co-located RDD

- have the same partitioner
- reside in the same physical location in memory (on the same executor)
- can be joined without a network transfer

### Co-partitioned RDDs

- have the same partitioner
- may be on different executors
- will (in general) be joined with network traffic
    - although much less than without the partitioning information (a proper shuffle)

## Shuffled Join

- No partitioner is known
- Rows with the same key must be on the same partition
- Spark needs fo shuffle both RDDs
- very expensive

## Optimized Join

One RDD doesnt have a known partitioner, or partitioners are different

- we can for the other RDD to obey the same partitioner
- one shuffle instead of two

## Optimized Join +

Both RDDs have the same partitioner (co-partitioned)

- just fetch the existing partitions and do the join
- no shuffles
- narrow dependency

## Optimized Join ++

Same partitioners, partitions loaded in memory (co-located)

- no partition fetching
- no shuffle
- no network transfer
- fatest joints possible 




