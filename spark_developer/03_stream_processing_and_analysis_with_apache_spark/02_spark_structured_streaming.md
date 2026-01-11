# spark structured streaming

## Introduction to Structured Streaming

A declarative API for distributed stream processing.

- Structured Streaming treats streaming data as an infinite table
    - each new record is a row appended to the table
    - queries are continuously updated as new data arrives
    - same DataFrame APis as batch processing
    - automatic optimization of query plans
- key features:
    - event-time processing (can be based on record timestamps or processing time)
    - watermark support for late data (deal with late-arriving data or data arriving out of order)
    - end to end exactly once guarantees (ensures no duplicates or data loss across failures, critical for correctness
      in financial or transactional systems)

## Streaming Data Sources and sinks

Built-in sources (Inputs)

| Type   | Description                                        |
|--------|----------------------------------------------------|
| Kafka  | Reads data from Apache Kafka topics                |
| File   | Reads files from a directory as they appear        |
| Socket | Reads data from TCP sockets (for testing)          |
| Rate   | Testing source that generates data at a fixed rate |

Built-in sinks (Outputs)

| Type                                                         | Description                                   |
|--------------------------------------------------------------|-----------------------------------------------|
| Kafka                                                        | Writes output to Kafka topics                 |
| File                                                         | Stores the output to a directory              |
| Foreach (let apply custom logic such as writing to database) | Runs computation on the records in the output |
| Console, memory                                              | used for testing or debugging                 |

Autoloader (cloud_files) is a Databricks Source for high-performance cloud storage ingestion with auto schema handling.

## DataStreamReader and DataStreamWriter

- DataStreamReader: Creates streaming DataFrames
    - access through SparkSession.readStream
  ```python
    df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "localhost:9092") \
      .option("subscribe", "topic1") \
      .load()
  ```
- DataStreamWriter: Writes streaming results
    - access through DataFrame.writeStream
  ```python
    df = spark.writeStream.format("kafka").outputMode("append") \
      .option("kafka.bootstrap.servers", "localhost:9093 \
      .start()
  ```

These APIs behave similarly to batch .read() and .write() but they designed for continuous data

## Streaming transformations

```python 
  df = (spark
        .readStream
        .option("maxOffsetsPerTrigger", 1)
        .format("delta")
        .load("your_input_path"))  # creates a streaming dataframe with a source and option

from pyspark.sql.functions import col

email_traffic_df = df.filter(col("traffic_source") == "email"))  # perform dataframe transformations as with a normal df
```

Key takeaway is that Structured Streaming uses the same transformation logic as batch, making it easy to adopt

## Streaming Queries

```python 

email_query = (
    email_traffic_df
    .writeStream
    .format("delta")
    .outputMode("append")
    .queryName("email_query")
    .trigger(processingTime="10 seconds")
    .option("checkpointLocation", "checkpoint_path")
    .start("your_output_path")
)

# Stop the query
email_query.stop()

# Wait for termination
email_query.awaitTermination()

```

A streaming query is analogous to an action in the DataFrame API, it will trigger sequence of Jobs (recall lazy
evaluation)

## triggers

controlling when Structured Streaming processes data

- Default trigger (ASAP as soon as possible) (unspecified)
    - processes data as soon as the previous micro-batch completes
      ```python
          spark.readStream.format("json").schema().load("path").writeStream.format("memory").queryName("query").start()
          # no trigger specified
      ```
- Fixed interval trigger
    - process data at specified time intervals (every 10 seconds for example)
    - useful for controlling resource usage
    ```python
        .trigger(Trigger.ProcessingTime("10 seconds"))
        .trigger(processingTime="10 seconds")
    ```

- Once Trigger
    - processes data only once and then stops
      ```python
          .trigger(Trigger.Once())
          .trigger(once=True)
      ```
- Available now trigger (Spark 3.3+) (faster than once trigger)
    - processes available data then stops
    - wont wait for more new data to arrive afterwards
      ```python
          .trigger(Trigger.AvailableNow())
          .trigger(availableNow=True)
      ```
- Continuous trigger (low latency mode)
    - continuously processes data as new data arrives
      ```python
         .trigger(Trigger.Continuous("1 second"))
         .trigger(continuous="1 second")
      ```

Mention the tradeoff between latency and throughput that is controlled by triggers

## Output Modes

How Structured Streaming writes output results to sinks

- append() (default)
    - only adds new records to the sink
    - best for simple (or stateless) queries without aggregations
- update (ideal for dashboards and real-time metrics)
    - modifies existing records and adds new ones
    - only outputs records that changed since last trigger
- complete (ideal for running totals or leaderboards)
    - writes entire result table to sink each time
    - required for some aggregations
      The choice of output mode depends on whether your query is stateless or involves aggregations

## Monitoring Streaming Queries

Understand your streaming applications health

- Monitoring via Spark UI
    - Stream tab shows active queries
    - progress details per batch
- Use external Monitoring Tools
    - Datadog, Grafana, Prometheus, etc
    - Monitor processing rates and latency
    - Memory usage and garbage collection
- SOme useful inspection functions
    - showActiveStreams()
    - showCurrentOffsets()
    - showProgress()

```python

df.isStreaming  # check if DataFrame is a streaming DataFrame

streaming_query.id  # get the query id

streaming_query.status  # get current state for query 

streaming_query.lastProgress  # get the last progress details for the query
```

Monitoring helps detect lag, bottlenecks, and failure conditions before they become critical

Streaming applications are long lived so monitoring is essential 
