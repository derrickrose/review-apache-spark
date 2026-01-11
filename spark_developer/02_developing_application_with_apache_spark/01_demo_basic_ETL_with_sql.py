## flight etl sql

# from pyspark.sql import SparkSession
#
# spark = SparkSession.builder.appName("01_demo_basic_ETL_with_sql").getOrCreate()
# flights_df = spark.read.format("parquet").load("flights_1988_2008.parquet")
# print(flights_df.schema)
# flights_df.show(10)
# print(flights_df)
# import time
#
# time.sleep(60 * 60)

"""
Note that with the previous tiny code above, we see 3 jobs son the UI because starting from spark 3.*
there are many background jobs for metadata like the metrics collection and the AEQ (adaptive query execution)
"""

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("01_demo_basic_ETL_with_sql")
    .config("spark.memory.fraction", "0.9")
    .config("spark.sql.adaptive.enabled", "false")
    .config("spark.driver.memory", "5632m")
    .config("spark.memory.storageFraction", "0.9")
    .getOrCreate()
)

flights_df = spark.read.format("parquet").load("flights_1988_2008.parquet")
# flights_df.cache()
flights_df.createOrReplaceTempView("flights")

flights_df.show(10)
print("flights_df count", flights_df.count())

output_df = spark.sql(
    """
SELECT Extract(year FROM year_month_dayofmonth)  AS Year,
       Extract(month FROM year_month_dayofmonth) AS Month,
       Extract(day FROM year_month_dayofmonth)   AS DayOfMonth,
       Coalesce(crsdeptime, '')                                AS DepTime,
       FlightNum,
       (Coalesce(crselapsedtime, 0) + Coalesce(arrdelay, 0))             AS ActualElapsedTime,
       CRSElapsedTime
FROM   flights
WHERE  year_month_dayofmonth IS NOT NULL
       AND flightnum IS NOT NULL
       AND crselapsedtime IS NOT NULL 
"""
)
output_df.show(10)
print("output_df count", output_df.count())

airfcraft_monthly_flights_duration = spark.sql(
    """
SELECT Concat(Extract(year FROM year_month_dayofmonth),
       Concat('_', Extract(month FROM
       year_month_dayofmonth)))                   AS YearMonth,
       TailNum,
       Count(crsdeptime)                          AS TotalFlights,
       Round(Sum(Coalesce(crselapsedtime, 0) + Coalesce(arrdelay, 0)) / 60) AS MonthlyDurationHours
FROM   flights
WHERE   year_month_dayofmonth IS NOT NULL
        AND tailnum IS NOT NULL
        AND tailnum <> 'Unknown'
        AND crselapsedtime IS NOT NULL
GROUP  BY Concat(Extract(year FROM year_month_dayofmonth),
          Concat('_', Extract(month FROM
          year_month_dayofmonth))),
          tailnum
ORDER  BY yearmonth DESC,
          tailnum DESC 

"""
)
airfcraft_monthly_flights_duration.show(10)
print("count", airfcraft_monthly_flights_duration.count())

# à optimiser les requetes

"""
import time

time.sleep(60 * 60)

# """

print("end")

## TODO SQL OPTIMIZATION THEN COMPARE COUNT RESULT OF DATAFRAME API AND SQL
