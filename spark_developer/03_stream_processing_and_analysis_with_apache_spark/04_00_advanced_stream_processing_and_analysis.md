# advanced stream processing and analysis

## stateless vs stateful

understand how streaming operations handle data over time

#### stateless operations

- process each operation independently
- no memory of previous records
- example: select, filter, ...

#### stateful operations

- maintain information across batches
- require checkpoint location
- examples : groupBy, join, dropDuplicates, ...
- window operations (covered later)
- why checkpoint operations?
    - it is needed to maintain state across batches
    - recover state in case of failures
    - handle replay of data without duplicating results

## maintaining state

managing state in distributed streaming applications

#### challenges in distributed state management

- data is distributed across worker nodes
- need fault tolerance for state recovery
- memory limitation for large state
- consistency across node failures

#### RocksDB as state backend

- built-in state store for Spark Structured Streaming
- provides persistence with high performance
- features :
    - efficient storage and retrieval
    - automatic compaction of data
    - supports for large state sizes

#### Key takeaway

Spark abstracts away the complexity of distributed state management.
But understanding how state is stored and recovered is crucial for tuning performance and ensuring fault tolerance.

```text
          |----->  Worker1   -------------
          |          RocksDB              \
          |                                \
Driver ---|--->    Worker2  ------------------>  Chekcpoint Directory
          |          RocksDB              /
          |                              /
          |---->   Worker3  ------------/
                    RocksDB
```

## Streaming joins

Understanding join types and limitations in streaming applications

- A Streaming DataFrame can be joined with
    - another streaming DataFrame
    - a static DataFrame, including:
        - a normal DataFrame
        - the result of a complete output mode streaming operation
- All join types are supported except full and cross
    - inner join
    - left outer join
    - right outer join
    - left semi join
    - left anti join
- Challenges and limitations:
    - joins require maintaining state, increasing memory usage
    - events from both streams must be with a defined interval
    - late arriving data can present challenges (discussed later)

## Streaming aggregations

Understanding aggregations in streaming applications

- Types of streaming aggregations (typically operating on grouped data)
    - count
    - sum/avg
    - min/max
- approximate functions are available which typically perform better e.g. approx_count_distinct()
- how can we aggregate an incomplete data set?
    - recall that streaming datasets are unbounded datasets
    - the answer is to aggregate based upon windows

To aggregate a streaming data, we must define when to finalize a result.
And windows provide that boundary.
This leads us to the next topic: windowing strategies

## windowing operations

- Tumbling windows
    - fixed non overlapping intervals
    - e.g. count events every 5 minutes
- Sliding windows
    - overlapping windows where an event can belong to multiple windows
- Session windows
    - dynamically sized windows based on user activity (with gaps or session timeouts)

Aggregating over a stream is only meaningful if we define boundaries in time.
Tumbling are time-based, while session windows are activity-based.
Choose based on the pattern you trying to measure.

## sliding window example

Get the number of authorization transactions for credit card in the last 60 seconds every 30 seconds.

```python
from pyspark.sql.functions import window, count

authorizations =  # schema { timestamp: Timestamp, card_id: String, amount: Double }

WindowedAuth = authorizations.groupBy(

    window(
        timestamp=authorizations.timestamp,
        windowDuration='60 seconds'
slideDuration = '30 seconds'

),
authorizations.card_id
).agg(count("*").alias('transaction_count'))

```

## handling late arriving data

- events can be delayed in arriving for many reasons
    - e.g. an event arrives with timestamp value for a window that has been processed
- watermark : defines how long Spark waits for out of order events

```python
windowed_auth = authorizations.withWatermark("timestamp", "10 minutes")
.groupBy(window(authorization.timestamp, "60 seconds", "30 seconds"), authorization.card_id)
.agg(count("*").alias("transaction_count"))

```

- a watermark tells Spark how long to wait for late data before finalizing a window
- think of it like a grace period
- Spark assumes no more events will arrive with timestamps earlier than currentEventTime - watermark

key tradeoffs:

- a long watermark increases correctness but may use more memory and delay results
- a short watermark improves speed but risks dropping late events

