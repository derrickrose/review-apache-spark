# post shuffle coalescing

shuffle partition statistics are available

- can detect partitions that are too big ==> split
- can detect partitions that are too small ==> stitch

- configurations :
    - spark.sql.adaptive.coalescePartitions.enabled true by default
    - spark.sql.adaptive.coalescePartitions.parallelismFirst true by default -aggressive split to maximize parallelism
    - spark.sql.adaptive.coalescePartitions.minPartitionNum - min size of partitions after coalescing
    - spark.sql.adaptive.advisoryPartitionSizeInBytes - hint of the ideal partition size after coalescing

# dynamically changing join strategy if the size is smaller than the threshold

shuffle partition statistics are available

- after a shuffle spark can determine the size of the DF
- if the DF is small, join impl can be broadcast, instead of the original join in the query plan

- configurations :
    - spark.sql.adaptive.autoBroadcastJoinThreshold - threshold for broadcast join

# data skew joins 

Shuffle partition statistics are available 
- can detect disproportionate partitions 
- spark can run mini joins on parts of the disproportionate partitions to reduce skew
- configs : 
  - spark.sql.adaptive.skewJoin.enabled - enable skew join optimization (default: `true`, only works if `spark.sql.adaptive.enabled` is `true`, default `true` since Spark 3.2)
  - spark.sql.adaptive.skewJoin.skewedPartitionFactor - factor to determine if a partition is skewed (default: `5.0`)
  - spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes - threshold for skew join optimization (default: `256MB`)
- a partition is considered skewed only if BOTH are true:
  - size > `skewedPartitionFactor` x median partition size
  - size > `skewedPartitionThresholdInBytes`

