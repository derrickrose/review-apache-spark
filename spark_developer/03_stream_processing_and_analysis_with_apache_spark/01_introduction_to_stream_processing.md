# Stream processing

## Streaming Processing Background
t
A stream is an unbounded data set

- it has no theoretical beginning nor end
- in contrast to batch which is of known size at the time of processing
- streams can be messages from a messaging system such as Kafka or Kinesis or files arriving continuously in cloud
  storage
- streams can be anything event driven such as files being processed in real time as they arrive

## Spark Streaming background

From DStream to Structured Streaming

- Spark Streaming was introduced in 2013 as an extension to core Spark
    - build on top of the RDD API
    - Using the DStream (Discretized Stream) model
    - Processing data in small time-based (RDD) batches
- Structured Streaming was introduced in 2016
    - build on top of the Dataset/DataFrame API
    - introduced event-time processing
    - simplified api with SQL-like operations
    - better handling of late and out-of-order data (late data arriving with watermarking)

## microbatching

The basis of stream processing in a distributed environment

Micro batching processes a stream as a series of small batches

- data is collected into time-based chunks
- each chunk processed as a mini-batch job
- typical batch intervals: 100ms to few seconds

```text
     t=n+3   t=n+2      t=n+1    t=n
+----+ | +----+ | +----+ | +----+ |
| b4 | | | b3 | | | b2 | | | b1 | |
+----+ | +----+ | +----+ | +----+ |
       <-------->      
       batch interval       
```

## Streaming in the real world

Streaming use cases:

- Fraud detection
- Live dashboards
- Anomaly detection
- Clickstream analysis
- Sensor & Iot Monitoring
- Data ingestion and transformation

Common sources and destinations :

- Kafka
- Kinesis
- Event Hubs
- Alerts/Notifications
- Lakehouse (Delta Lake, Iceberg)

Note that not all stream processing use cases are real-time, file ingestions may process data only as files arrive 


