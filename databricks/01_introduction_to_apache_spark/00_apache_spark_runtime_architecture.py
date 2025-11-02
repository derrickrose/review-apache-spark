# apache spark runtime architecture

# what is apache spark ?
## apache spark is an open-source, distributed, unified analytics engine for fast, large-scale data processing

# Apache spark features
## native support for SQL
## streaming data
## machine learning
## graph processing through a consistent API

# Apache spark delivers high performance through in-memory computation, making it significantly faster than other processing frameworks

# Apache spark operates seamlessly with diverse data sources including cloud storage
## (AWS S3, Azure, Google), local files, and databases

# brief history                                                                                     2020 spark 3.0          2024
##           2010 initial                 2014 spark becomes                  2018 delta            with AQE, databricks    databricks tabular
##           spark release                apache top level project            lake introduced       sql launches            maintainer for iceberg
## --|-----------|-----------------|----------|-----------------------|------------|------------|------- |-----------|--------|------------------------>
## 2009                         2013 databricks                  2016 spark 2.0              2019 MLflow       2021 unity
## project originated           founded, spark                  released with               released           catalog
## UC Berkeley's AMPLab      donated to apache foundation        structured streaming

# spark components
""""
+-----------------------+ +----------------------+ +------------+ +------------+ +-------------+
|  Python Scala/Java    | |    Python Scala/Java | |   SQL      | |  R         | |  Scala/Java |
|  Structured Streaming | |   MLlib              | |  Spark SQL | | SparkR API | |  GraphX     |
+-----------------------+ +----------------------+ +------------+ +------------+ +-------------+
         ||                    ||                      ||            ||              ||
         \/                   \ /                      \/            \/              ||
+---------------------------------------------------------------------------+        ||
|  Python Scala/java                        Dataframe API                   |        ||
+---------------------------------------------------------------------------+        ||
                                                                                     \/
+--------------------------------------------------------------------------------------------+
| Spark Core (RDD API)                                                                       |
+--------------------------------------------------------------------------------------------+
"""
