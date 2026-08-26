# Shared nothing architecture
# Core principles of distributed computing
## Key characteristics:
#### Independence: each node works independently and manages its won resources (CPU, memory, disk)
#### Scalability: adding more nodes can improve performance without resource contention
#### Fault tolerance: Failures are isolated to individual nodes, minimizing system-wide impacts
#### Resource partitioning: data and workloads are partitioned across nodes to eliminate contention

# spark resilience
## resilience means fault tolerance, ability to recover automatically from failures
#### without losing computation or data (node crashes, network issues, or lost data partitions)
## this property comes from spark's fundamental data structure called the RDD Resilient Distributed Dataset
## how does spark achieve resilience
#### spark doesnt rely on data replication (like Hadoop)
#### instead, it uses lineage and lazy evaluation
###### lazy evaluation : spark doesnt execute transformations immediately, it waits until an action is called
######## this allows it to optimize the entire DAG before running, and track dependencies efficiently for fault recovery.
###### lineage : each rdd remembers how it was created (the sequence of transformation applied to generate it)
######## so from there spark builds a lineage graph (a DAG Directed Acyclic Graph), so if a partition of an rdd is lost,
######## it recomputes it from the lineage

# spark checking point
## for very long lineage chains, you can use checkpointing : saving an RDD to reliable storage (e.g. HDFS, S3)
#### if a node fails, spark loads the checkpoints instead of recomputing everything
## rdd.checkpoint()

# task and executor resilience
## spark driver and cluster manager (YARN, Kubernetes or standalone) monitor executors :
#### if an executor dies, spark relaunches tasks on another node
#### if a node fails, spark recomputes lost partitions on surviving nodes

# Partitioning
# How spark distributes data across the cluster
## Data distribution :
#### Data divided into manually exclusive in-memory partitions
#### Default partitioning bases upon input, can be manipulated
#### Size and number of partitions affect parallelism
## Processing Model :
#### Each partition processed independently
#### Multiple partitions can run in parallel
#### One partition = one task in Spark
#### Impacts performance and shuffle operations
## These partitions are not to be confused with table, disk, or Hive partitioning.
## In spark, data is broken into chunks called partitions, which are processed independently.
## Default partitioning is often determined by data size or the number of available cores.
## Each partition is processed by a single task within a spark job, enabling parallel processing by running multiple tasks
#### withing a spark job, enabling parallel processing by running multiple tasks simultaneously across executors.
## Understanding partitioning is crucial for performance optimization, especially during shuffling.
## Adjusting partition size can improve memory usage and reduce shuffle overhead,
#### making monitoring and tuning partitioning an essential step in performance tuning.

# The shuffle operation
# Data movement in distributed processing
## What is shuffling ?
#### redistribution of data across partitions
#### required for operations like groupBy, join and sorting (data needs to be aggregated across partitions)
#### most expensive operation in spark
## when it occurs ?
#### wide transformations
#### key-based transformations
#### data repartitioning
## It occurs basically during operation that needs data reorganization
## Minimizing shuffling is critical for performance and optimization techniques include:
#### avoid unnecessary partitioning
#### using co-located data
#### applying effective partitioning strategies
""" "
+---------+   +------------+    +------------+
| k1, k2 |    | k2, k3     |   |  k2, k3    |      stage1
+--------+    +------------+   +------------+
   | |    \        |      |     |   /              shuffle
   \/      \       |  ----|----/  /
+-----+     \ +----+/   +----+   /
| k1  |       | k2 |   | k3 |---|                  stage2
+-----+       +----+   +----+
"""

# Map Reduce in Action
## The map stage is the initial transformation where data is filtered, mapped, or otherwise prepared.
## Operations like select() and filter() are narrow transformations (data remains on the same node)
## The shuffle stage restructures data across partitions to meet aggregation or join in requirements
## The resource stage involves aggregation or final transformation of the shuffled data,
#### with result often writen to storage or returned to the driver
## Understanding how spark execute Map, Shuffle and Reduce stages is key to optimization and
#### properly tuning each stage can drastically improve performance

# Spark's implementation
# MapReduce at the core of everything
## Fundamental Pattern:
#### Every spark operation maps to Map/Reduce/Shuffle
#### even simple transformations follow this model
#### core building blocks for all distributed operations
## Examples
#### groupBy : Map(extract keys) => Shuffle (by key) => Reduce(aggregate)
#### join : Map(prepare keys) => Shuffle (co-locate) => Reduce(combine)
#### filter : Map(evaluate condition) => No shuffle or reduce needed
## Understanding how these operations map  to the underlying model helps in fine-tuning perf
## and knowing which stages introduce shuffling is key to minimizing latency and maximizing throughput
