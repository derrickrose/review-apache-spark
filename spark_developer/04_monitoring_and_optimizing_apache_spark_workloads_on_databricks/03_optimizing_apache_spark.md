# Monitoring and optimizing Apache Spark workload

## Understanding Spark Performance

Knowing where and why your Spark applications spend their time

- Key factors affecting Spark performance :
- Resource utilization (CPU, memory, network, disk I/O)
- Data characteristics (size, format, distribution)
- Configuration settings and cluster setup
- Understand where time is spent in Spark jobs2715.59
- Common bottlenecks:
    - Data skew and uneven or inadequate partitioning
    - Excessive shuffling and data movement
    - Memory pressure and garbage collection

## Spark Partitioning

The foundation of distributed processing performance

- DataFrame partitioning determines data distribution
- Partitions are determined by :
    - Files or blocks when data is read from a table or directory (typically distributed)
        - these are know as initial memory partitions
        - driver decides the number based on conf like pyspark.sql.files.maxPartitionBytes (default 128 MB) and
          pyspark.sql.default.parallelism (used when reading non-file data like collections)
    - As a result of a Wide Transformation (groupBy, join, distinct) or repartition/coalesce
        - these are referred to as shuffle partitions
        - The default partitioner in APache Spark is the Hash Partitionel (hash(key)% numPartitions)
        - controlled by pyspark.sql.shuffle.partitions (default 200)
- Importance of data distribution:
    - Enables parallel processing across executors
    - Impacts memory utilization per executor
    - Influences join and aggregation efficiency
    - Determines network traffic patterns

## Spark Partitioning (what can you do?)

- choosing partition keys
    - use high-cardinality columns for even distribution
    - groupBy() automatically repartitions on group key(s)
    - df.repartition(n, col("your_column")) to repartition on another key
- right-sizing shuffle partitions
    - target 100MB - 200MB per partition
    - Partitions should not be less than number of cores
    - df.repartition(n) or df.coalesce(n)
    - monitor task duration(aim for 50-200 ms)

## Shuffle operations

understanding and optimizing Apache Spark's most expensive operation

- Recall that shuffles are triggered by Wide Transformation, or changes to partition counts (esp. df.repartition)
- Networ I/O required by shuffles impacts job performance
- How to minimize shuffle impact
    - Filter early/filter Often
    - Use broadcast joins for small tables (< 10 GB)
    - Configure shuffle partitions based on data size
    - Maintain consistent partitioning where possible
- Monitor shuffle spill metrics (memory vs disk)

## DataFrame caching

Data persistence for iterative and interactive workloads

- When to use caching :
    - Multipe accesses to same DataFrame/RDD
    - Expensive transformations upstream
    - Interactive analysis and ML iterations
    - Lookup tables used across operations
- Cache managment
    - use df.cache() or df.persist() explicitly
    - monitor executor memory usage with UI
    - call df.unpersist() when no longer needed

## Join performance consideration

Optimizing relatinal operations in a distributed environment

- Join strategy selection
    - Apache Spark automatically chooses the join strategy based on the join keys and data distribution
    - Smaller DataFrame should be referenced first
- Use tbe broadcast() hint
    - Apache Spark can optimize join performance by broadcasting small tables using the broadcast hint
  ```python

  from pyspark.sql.functions import broadcast
  large_df.join(broadcast(small_df, "key))
  
  ```

## More Join Performance Considerations

Optimizing relational operations in distributed environment

- Data Skew Handling
    - Uneven distribution of join keys can impact performance
    - Consider repartitioning in some cases
- Memory Management
    - Monitor shuffle spill metrics for joins
    - Consider caching frequently joined DataFrames
    - Use projection to select only needed columns before joining

## Query Optimization

Understanding Spark optimizes and executes your queries

- Catalyst optimizer
  Unresolved Logical plan ==> analyzed logical plan ==> optimized logical plan ==> physical plan
  Analysis => logical optimizations => physical optimizations => code generation

- Use df.explain() or df.explain(extended=True) to see the logical and physical plans
- Predicate pushdown
- Adaptive Query Execution (AQE)

## Best practices

General tips for maximizing Spark application performance

- Use the Spark UI
    - track job progress, stages and task metrics
    - monitor shuffle, storage and executor details
- Filter Early/ Filter Often
- Use projection (SELECT) to eliminate non needed columns early in your routines
- Minimize the use of UDFs(use built-in functions if available)
- Use Pandas UDFs as previously discussed if you need these
- Optimize partitioning and tune shuffle involing operations
    - optimize join as discussed
    - detect and avoid data skew 
