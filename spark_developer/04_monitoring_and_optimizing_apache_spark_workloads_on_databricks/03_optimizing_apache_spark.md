# Monitoring and optimizing Apache Spark workload

## Understanding Spark Performance

Knowing where and why your Spark applications spend their time

Key factors affecting Spark performance :

- Resource utilization (CPU, memory, network, disk I/O)
- Data characteristics (size, format, distribution)
- Configuration settings and cluster setup
- Understand where time is spent in Spark jobs2715.59

Common bottlenecks:

- Data skew and uneven or inadequate partitioning
- Excessive shuffling and data movement
- Memory pressure and garbage collection

Anatomy of a Spark job: actions, stages and tasks

````
Action -----------------------> Job -------------> Stage1 (read+narrow transformations) -------------> Tasks (one per partition)
(display, count, write)                              | 
                                                     | (shuffle)
                                                     | Stage2 (after shuffle boundary) --------------> Tasks (one per shuffle partition)
````

## Spark Partitioning

Partitions are the unit of parallelism in Apache Spark: every stage runs one task per partition. How data is partitioned
determines memory use per executor, join and aggregation efficiency and network traffic. Where partition counts come
from:

- Initial partitions : set by the files or blocks read from a table or directory
- Shuffle partitions : created by wide transformations (groupBy, join) or explicit repartition/coalesce
- The default partitioner is the hash partitioner hash (key) % numPartitions

The foundation of distributed processing performance

- DataFrame partitioning determines data distribution
- Partitions are determined by :
    - Files or blocks when data is read from a table or directory (typically distributed)
        - these are known as initial memory partitions
        - driver decides the number based on conf like
            - pyspark.sql.files.maxPartitionBytes (default 128 MB) and
            - pyspark.sql.default.parallelism (used when reading non-file data like collections)
    - As a result of a Wide Transformation (groupBy, join, distinct) or repartition/coalesce
        - these are referred to as shuffle partitions
        - The default partitioner in APache Spark is the Hash Partitionel (hash (key)% numPartitions)
        - controlled by pyspark.sql.shuffle.partitions (default 200)
- Importance of data distribution:
    - Enables parallel processing across executors
    - Impacts memory utilization per executor
    - Influences join and aggregation efficiency
    - Determines network traffic patterns

## Spark Partitioning (what can you do?)

- choosing partition keys
    - use high-cardinality columns for even distribution
    - groupBy () automatically repartitions on group key (s)
    - df.repartition (n) full shuffle to exactly n evenly sized partitions,
    - df.repartition (n, col ("your_column")) to repartition on another key
- right-sizing shuffle partitions
    - target 100MB - 200MB per shuffle partition
    - Partitions should not be less than number of cores
    - df.repartition (n) or df.coalesce (n)
    - monitor task duration (aim for 50-200 ms) under 50ms means too many partitions

AQE changed this game (actully active by default), Spark coalesces shuffle partitions at runtime based on data size.
Manual spark.sql.shuffle.partitions tuning is now mostly a legacy technique, reach for explicit repartition only when
you have a specific layout requirement

## Shuffle operations

understanding and optimizing Apache Spark's most expensive operation data is serialized, written to disk, sent accross
the network and read back by the next stage

- Recall that shuffles are triggered by Wide Transformation, or changes to partition counts (esp. df.repartition)
- Every shuffle is a stage boundary, the whole stage must finish before the next begins
- Shuffle spill (memory to disk) is a key warning sign to monitor in the Spark UI
- Network I/O required by shuffles impacts job performance
- How to minimize shuffle impact
    - Filter early/filter Often, select only the columns you need before wide operations
    - Use broadcast joins for small tables (< 10 GB) so the large side never shuffles
    - Configure shuffle partitions based on data size
    - Maintain consistent partitioning where possible
- Monitor shuffle spill metrics (memory vs disk)

What to observe: in the Spark UI stages tab, the Shuffle Read and Shuffle Write columns quantify data movement, and
Spill (Memory)/Spill (Disk) reveal memory pressure. These four numbers diagnose most slow stages

wide transformation (groupBy, join, distinct, orderBy)

## Adaptive Query Execution

Adaptive Query Execution (AQE) re-optimizes query plans at runtime using real statistics from completed shuffle stages.
It is enabled by default in Spark 4. AQE makes three major optimizations :

- Coalescing shuffle partitions : too many small post-shuffle partitions wasting task overhead
- Skew join handling : one giant partition stalling in entire stage
- Dynamic join strategy switching : a sort-merge join that should have been broadcast join, once actual sizes are known

```aiignore
static plan (from Catalyst) ------------------------>                             ------> Coalesce small shuffle partitions
                                                            AQE re-optimization   -------> split skewed partitions
runtime statistics (actual shuffle sizes) ---------->                             -------->  switch to broadcast join
```

manual tuning is legacy (spark.sql.shuffle.partitions), hand-splitting skewed keys, forcing join order is now handled by
AQE you job is to verify it in the Spark UI (look for AQEShuffleRead in the plan) and step in only where AQE cannot help
(such as the initial read layout and caching decisions)

## Join Strategies

Joins are where shuffle costs concentrate. Spark chooses a strategy automatically, and the choice matters mor than
almost any other plan decision

broadcast hash join, one side first under the broadcast threshold, small side copied to every executor, no shuffle of
the large side sort-merge join, both sides large, both sides shuffled and sorted - the expensive default shuffle hash
join, one side moderately smaller, both sides shuffled -smaller side hashed

influencing the choice :

````python 
from pyspark.sql.functions import broadcast

small_df = ""
large_df = ""
result_df = large_df.join(broadcast(small_df), "key")
````

- The automatic broadcast threshold is controlled by spark.sql.autoBroadcastJoinThreshold
- AQE can convert a planned sort-merge join to a broadcast join at runtime once it sees the true size
- project only needed columns before joining, and watch for join key skew in the Stages tab

## DataFrame caching

Data persistence for iterative and interactive workloads (executor memory and disk) to avoid recomputation

- When to use caching :
    - Multiple actions over the same transformed Dataframe
    - Expensive transformations upstream (joins, aggregations) feeding several outputs
    - Interactive analysis and ML iterations
    - Lookup tables used across operations
- Cache managment
    - use df.cache () or df.persist () explicitly, the first action actually populates the cache
    - monitor the storage tab in the spark UI for size and memory fraction cached
    - call df.unpersist () when no longer needed

Caching is not free, cached data competes with shuffle and execution memory.

Caching a DataFrame used only once makes the workload slower, not faster. Cache deliberately verify in the Storage tab,
and unpersist when done.

## More Join Performance Considerations

Optimizing relational operations in distributed environment

- Data Skew Handling
    - Uneven distribution of join keys can impact performance
    - Consider repartitioning in some cases
- Memory Management
    - Monitor shuffle spill metrics for joins
    - Consider caching frequently joined DataFrames
    - Use projection to select only needed columns before joining

## Query Optimization with Catalyst Optimizer

The Catalyst optimizer rewrites every query SQL or DataFrame into an optimized physical plan before execution What
Catalyst does for you automatically :

- Predicate pushdown, filters move down to the scan, so less data is read at the source
- Column pruning, only the referenced columns are read from columnar formats
- Filter combination, multiple filters collapse into one operation
- Dynamic file pruning, join-driven file skipping on Delta tables at runtime

Understanding Spark optimizes and executes your queries

- Catalyst optimizer Unresolved Logical plan ==> analyzed logical plan ==> optimized logical plan ==> physical plan
  Analysis => logical optimizations => physical optimizations => code generation

- Use df.explain () or df.explain (extended=True) to see the logical and physical plans
- df.explain ("formatted") readable plan with operator details
- df.explain ("extended") logical and physical plans


- Spark UI, Jobs/Stages -> Where time goes, shuffle read/write, spill, task skew
- Spark UI, SQL/DataFrame -> Executed plans with per-operator rows and timing
- Spark UI, Storage -> What is cached and how much memory it holds
- Spark UI, Executors -> Resource usage, GC time, failed tasks per executor
- explain () -> the plan before execution, join strategies, pushed filters
- DESCRIBE DETAIL / DESCRIBE HISTORY -> table file layout and operation metrics
- Structured logging (Spark 4) -> JSON driver and executor logs, queryable with Spark itself

monitoring workflow :

- start at sql/dataframe tab to find the slow query and the slow operator within it
- drill into the matching stage for shuffle and spill metrics
- only then change code or configuration and re measure after

## Best practices

General tips for maximizing Spark application performance

- Use the Spark UI
    - track job progress, stages and task metrics
    - monitor shuffle, storage and executor details
- Filter Early/ Filter Often
- Use projection (SELECT) to eliminate non needed columns early in your routines
- Minimize the use of UDFs (use built-in functions if available)
- let AQE manage shuffle partition counts, reach for repartition only with a specific layout goal
- Broadcast small join inputs and verify the strategy in the plan
- Cache deliberately, verify in the Storage tab and unpersist when done
- Keep tables healthy with OPTIMIZE and liquid clustering, engine tuning cannot fix fragmented table
- Use Pandas UDFs as previously discussed if you need these
- Optimize partitioning and tune shuffle involing operations
    - optimize join as discussed
    - detect and avoid data skew 
