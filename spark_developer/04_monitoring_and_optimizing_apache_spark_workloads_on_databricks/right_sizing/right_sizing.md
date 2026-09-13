# fat and skinny executors

- skinny executors <=> lots of executors with few resources
- fat executors <=> few executors with lots of resources
- fit executors <=> balanced resources for each executor
- our machine 4 nodes, 64GB each, 16 cores

## skinny executors

- 64 executors, 1 core each, 4GB each
    - spark.executor.memory = 4g
    - spark.executor.cores = 1
    - spark.executor.instances = 64
    - or spark-submit --num-executors 64 --executor-memory 4g --executor-cores 1
- pros:
    - good I/O throughput (write data or read data with lots of partitions)
    - maybe good for lots of small tasks
- cons:
    - each executor is single-threaded
    - bigger tasks will OOM the executors
    - managing so many incurs a large overhead

## fat executors

- 4 executors (one per machine), 16 cores each, 64 GB each
    - spark.executor.memory = 64g
    - spark.executor.cores = 16
    - spark.executor.instances = 4
    - or spark-submit --num-executors 4 --executor-memory 64g --executor-cores 16
- pros:
    - can accommodate enormous tasks
    - can leverage executor parallelism
- cons:
    - bad for hdfs and concurrent I/O
    - 64GB wont fit in the container mem
    - one executor down = 25% of the cluster down
- also in really we cannot allocate all of that 64 giga to the executors since the machine overhead

## fit executors

- allocate some CPU and memory for YARN, OS and HDFS, e.g. 3 to 4 GB and 3 to 4 cores per machine (overhead)
- left 60GB and 12 cores each (we have 4 nodes to recall)
- allocate ~1GB for ApplicationMaster (not significant for large clusters but here 4 nodes of 64 it is ok)
- keep <= 5 cores/executor for good hdfs throughput
- left 48/5 = 9 executors
- memory/executor = (4*60-1)/9 = 26 GB
- keep 7-8 percent of the ram for executor overhead
- => net memory 24 GB
- spark-submit --num-executors 9 --executor-memory 24g --executor-cores 5

## exercises :

- 10 machines, 64GB RAM and 16 CPU each
- 1 master node r5.12xlarge, 19 r5.12xlarge worker nodes, 8TB total RAM, 960 total vCPUs
    - keep 4 cores and 4 GB RAM per machine => 76 cores and 76GB
    - remaining 7920 GB RAM, 884 cores
    - 5 cores per executor => 176 executors
    - memory per executor = 790/176 = 45
    - minus 8% overhead => net executor memory = 41 GB
    - spark-submit --num-executors 176 --executor-memory 41g --executor-cores 5

# dynamic resource allocation

allows spark to request/terminate executors as the job is running

- useful for multi-tenancy/cluster sharing/when cluster is idle
- maximize cluster utilization
- good for long-running jobs
- can impact performance for low-latency jobs
    - spark.dynamicAllocation.enabled=true
    - spark.dynamicAllocation.initialExecutors=10
    - spark.dynamicAllocation.minExecutors=10
    - spark.dynamicAllocation.maxExecutors=176
    - spark.dynamicAllocation.schedulerBacklogTimeout=10s
    - spark.dynamicAllocation.cachedExecutorIdleTimeout=60s
    - spark.dynamicAllocation.sustainedSchedulerBacklogTimeout=60s (only if the task duration is still long after the
      first executor request)
    - spark.dynamicAllocation.executorIdleTimeout=60s not really necessary the rest
    - spark.dynamicAllocation.shuffleTracking.enabled=true
    - spark.dynamicAllocation.shuffleTracking.excludedApplications=spark-history-server
    - spark.dynamicAllocation.shuffleTracking.reportMissingExecutors=true

spark requesting executors usually by 2 in exponential