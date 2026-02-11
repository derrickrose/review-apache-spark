# CSV

Column Separated Values, default schema inferrence FALSE.
Note: Schema inference is Spark guessing data types by reading data

- Spark does not infer schema by default for CSV files, need to explicitly specify it by setting option `inferSchema` to
  `true`

    ```python
    df = spark.read.csv("file.csv", inferSchema=True)
    
    df = spark.read
        .option("inferSchema", "true")
        .csv("file.csv")
    ```
