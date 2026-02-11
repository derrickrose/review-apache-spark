# monitoring and optimizing spark workloads on databricks

## VERSIONS COMPATIBILITY

- Spark 3.5.3
- Scala 2.13
- Delta Lake 3.1.0

## RUNNING SPARK WORKLOADS WITH SPARK SUBMIT PARAMS ??? to be tested

```shell
PYSPARK_SUBMIT_ARGS="--packages io.delta:delta-spark_2.12:3.1.0 pyspark-shell" \
spark-submit spark_developer/04_monitoring_and_optimizing_apache_spark_workloads_on_databricks/02_spark_with_delta_lake_demo.py
```

# Spark with Delta Lake Demo

(check the python file to run the demo)
First of all a _delta_log directory is created
Inside the _delta_log directory, we can find the transaction logs of the delta table

## spark write mode overwrite and delta set to default (Copy-On-Write) without any partitioning

Checkpoint is created when ```python version%10==0```, meaning that checkpoint is created every 10 versions , this is
controlled by ```python delta.checkpointInterval=10```

- each write is subject to:
    - new parquet file : data (actual data written by the spark job)
    - VERY IMPORTANT : while reading the table, since mode is overwrite, data in the table are the data written by the
      last spark job (count)
    - crc file : verification for data integrity
    - json file is metadata about :
        - commitInfo : timestamp, operation, operationParameters, mode, isolationLevel, operationMetrics, partitions
          ```json
              {
                  "commitInfo": {
                  "timestamp": 1769685019478,
                  "operation": "WRITE",
                  "operationParameters": {
                  "mode": "Overwrite",
                  "partitionBy": "[]"
                  },
                  "isolationLevel": "Serializable",
                  "isBlindAppend": false,
                  "operationMetrics": {
                  "numFiles": "1",
                  "numOutputRows": "110",
                  "numOutputBytes": "2579"
                  },
                  "engineInfo": "Apache-Spark/3.5.3 Delta-Lake/3.1.0",
                  "txnId": "a2b216e4-4dbb-4847-8e46-b8f6958252ea"
                  }
              }
          ```
        - metaData : id, format, schema, partitionColumns, configuration, createdTime,
          lastUpdatedTime,
          deleted
            ```json
                {
              "metaData": {
                "id": "61ec76ca-376d-472f-ab06-a7e05d6da87a",
                "format": {
                  "provider": "parquet",
                  "options": {}
                },
                "schemaString": "{\"type\":\"struct\",\"fields\":[{\"name\":\"id\",\"type\":\"integer\",\"nullable\":true,\"metadata\":{}},{\"name\":\"name\",\"type\":\"string\",\"nullable\":true,\"metadata\":{}},{\"name\":\"age\",\"type\":\"integer\",\"nullable\":true,\"metadata\":{}},{\"name\":\"gender\",\"type\":\"string\",\"nullable\":true,\"metadata\":{}}]}",
                "partitionColumns": [],
                "configuration": {},
                "createdTime": 1769685015514
              }
          }
          ```

        - protocol : minReaderVersion, minWriterVersion
        - add : path, modificationTime, size, stats, dataChange, partitionValues, tags, deleteFiles,
          transactional
            ```json
               {
          "add": {
          "path": "part-00000-99d18753-9738-4f39-b4e9-6f5ae0028f01-c000.snappy.parquet",
          "partitionValues": {},
          "size": 2579,
          "modificationTime": 1769685018102,
          "dataChange": true,
          "stats": "{\"numRecords\":110,\"minValues\":{\"id\":1,\"name\":\"abro\",\"age\":14,\"gender\":
          \"female\"},\"maxValues\":{\"id\":100,\"name\":\"zoe\",\"age\":56,\"gender\":\"male\"},\"nullCount\":{\"id\":
          0,\"name\":0,\"age\":0,\"gender\":0}}"
          }
          }

            ```

## spark write mode append and delta set to default (Copy-On-Write) without any partitioning

- each parquet file contains data written by each spark job run
- the table actually contains blindly all data written during each run of the spark job (duplications)

## spark write mode overwrite and delta set to default (Copy-On-Write) with partitioning by gender

- if dataframe count is zero:
    - no parquet file created , in contrast without partitioning it will be created but no data in it (just schema)
    - metadata file created
- otherwise:
    - folder created for each partition value, for our use case `gender=male` and  `gender=female` folders created
    - metadata file created
    - parquet files created
- VERY IMPORTANT : repartitioning only affect parquet files, not delta version, for delta one job is one version(not
  number of parquet files nor number partitions; it does mean no checkpoint is created even if millions of files were
  written by the job)