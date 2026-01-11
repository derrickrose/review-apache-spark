# drop column with .drop("col1", "col2") not .drop(col("col1"), col("col2")) the second one add functions overhead
# add column with withColumns({"col1": col("col2") + 1}) not many .withColumn("col1", col("col2") + 1).withColumn("col1", col("col2") + 1)
# extract year from DateType() column with .withColumn("Year", year("date_column"))"
# rename column with .withColumnRenamed("old_name", "new_name") note: do it grouped with other column transformation
# select specific columns with .select("col1", "col2") not .select(col("col1"), col("col2")) neither selectExpr("col1", "col2") the second one is for sql expression like "year(date_column) as year"

"""
Function make_timestamp_ntz to check too
Function withColumn with when() to check too and otherwise()

BAD way filtering

    .filter(
        "year_month_dayofmonth IS NOT NULL AND flightnum IS NOT NULL AND crselapsedtime IS NOT NULL"
    )

BETTER way filtering ## a good practice too is to cast to a type then add isNotNull col("duration").cast("integer").isNotNull()
    .filter(
        col("year_month_dayofmonth").isNotNull()
        & col("flightnum").isNotNull()
        & col("crselapsedtime").isNotNull()
    )

    .filter(
        (trim(lower(col("TailNum"))) != "unknown")
        & (trim(lower(col("TailNum"))) != "unknow")
    )

ORDER Columns
    .orderBy(col("col1"), col("col2"))
    .orderBy(desc(col("col1")), desc(col("col2")))

DIVISION
    from pyspark.sql.functions import lit, try_divide as divide
    divide(
                sum(col("CRSElapsedTime")) + sum(coalesce(col("ArrDelay"), lit(0))),
                lit(60),
            ),

DROP ROWS to apply on a subset of rows where condition is true
    .na.drop(subset=["CRSDepTime", "ArrDelay"])
    .dropna(subset=["CRSDepTime", "ArrDelay"])

"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    year,
    concat,
    month,
    dayofmonth,
    coalesce,
    lit,
    sum,
    try_divide as divide,
    round as pyround,
    count,
    desc,
    trim,
    lower,
)

spark = SparkSession.builder.appName(
    "01_demo_basic_ETL_with_dataframe_api"
).getOrCreate()
flights_df = spark.read.format("parquet").load("flights_1988_2008.parquet")

output_df = (
    flights_df.drop(
        "DayOfWeek",
        "CRSArrTime",
        "UniqueCarrier",
        "Origin",
        "TailNum",
        "Dest",
        "Distance",
    )
    .filter(
        col("year_month_dayofmonth").isNotNull()
        & col("flightnum").isNotNull()
        & col("crselapsedtime").isNotNull()
        # "year_month_dayofmonth IS NOT NULL AND flightnum IS NOT NULL AND crselapsedtime IS NOT NULL"
    )
    .withColumns(
        {
            "Year": year(col("year_month_dayofmonth")),
            "Month": month(col("year_month_dayofmonth")),
            "Day": dayofmonth(col("year_month_dayofmonth")),
            "ActualElapsedTime": col("crselapsedtime") + col("arrdelay"),
        }
    )
    .withColumnRenamed("crsdeptime", "DepTime")
    .drop(
        "year_month_dayofmonth",
        "arrdelay",
    )
    .select(
        "Year",
        "Month",
        "Day",
        "DepTime",
        "FlightNum",
        "ActualElapsedTime",
        "CRSElapsedTime",
    )
)

output_df.show(10)
print("output_df count", output_df.count())

aircraft_monthly_flights_duration = (
    flights_df.drop(
        "DayOfWeek",
        "CRSArrTime",
        "UniqueCarrier",
        "Origin",
        "FlightNum",
        "Dest",
        "Distance",
    )
    .filter(
        col("year_month_dayofmonth").isNotNull()
        & col("TailNum").isNotNull()
        & col("CRSElapsedTime").isNotNull()
        & (trim(lower(col("TailNum"))) != "unknown")
        & (trim(lower(col("TailNum"))) != "unknow")
        # "year_month_dayofmonth IS NOT NULL AND TailNum IS NOT NULL AND TailNum <> 'Unknown'"
    )
    .withColumns(
        {
            "Year": year(col("year_month_dayofmonth")),
            "Month": month(col("year_month_dayofmonth")),
        }
    )
    .drop("year_month_dayofmonth")
    .groupBy("Year", "Month", "TailNum")
    .agg(
        count(col("CRSDepTime")).alias("TotalFlights"),
        concat(col("Year"), lit("_"), col("Month")).alias("YearMonth"),
        pyround(
            divide(
                sum(col("CRSElapsedTime")) + sum(coalesce(col("ArrDelay"), lit(0))),
                lit(60),
            ),
            0,
        ).alias("MonthlyDurationHours"),
    )
    .drop("Year", "Month")
    .select("YearMonth", "TailNum", "TotalFlights", "MonthlyDurationHours")
    .orderBy(desc(col("YearMonth")), desc(col("TailNum")))
)

aircraft_monthly_flights_duration.show(10)
print(
    "aircraft_monthly_flights_duration count", aircraft_monthly_flights_duration.count()
)
