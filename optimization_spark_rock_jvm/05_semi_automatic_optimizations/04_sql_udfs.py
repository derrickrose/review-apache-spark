from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, LongType

spark = SparkSession.builder.appName("SQL UDFs").master("local[*]").getOrCreate()

from pathlib import Path

PATH = Path(__file__).parents[2]

movies = spark.read.json(str(PATH / "data" / "movies" / "movies.json"))


def sql_udf():
    spark.sql("""
    CREATE OR REPLACE TEMPORARY FUNCTION movie_tier(budget BIGINT, gross BIGINT) 
    RETURNS STRING
        RETURN CASE 
            WHEN gross IS NULL OR budget IS NULL THEN 'Unknown'
            WHEN gross > budget * 2 THEN 'blockbuster'
            WHEN gross > budget THEN 'profitable'
            ELSE 'flop'
        END
    """)

    movies.createOrReplaceTempView("movies")

    tiered = spark.sql("""
                       SELECT Title,
                              Worldwide_Gross,
                              Production_Budget,
                              movie_tier(Production_Budget, Worldwide_Gross) AS Tier
                       FROM movies
                       WHERE movie_tier(Production_Budget, Worldwide_Gross) = 'blockbuster'
                       """)

    tiered.explain()
    """
    == Physical Plan ==
*(1) Project [Title#18, Worldwide_Gross#21L, Production_Budget#13L, CASE WHEN (isnull(Worldwide_Gross#21L) OR isnull(Production_Budget#13L)) THEN Unknown WHEN (Worldwide_Gross#21L > (Production_Budget#13L * 2)) THEN blockbuster WHEN (Worldwide_Gross#21L > Production_Budget#13L) THEN profitable ELSE flop END AS Tier#25]
+- *(1) Filter CASE WHEN (isnull(Worldwide_Gross#21L) OR isnull(Production_Budget#13L)) THEN false WHEN (Worldwide_Gross#21L > (Production_Budget#13L * 2)) THEN true WHEN (Worldwide_Gross#21L > Production_Budget#13L) THEN false ELSE false END
   +- FileScan json [Production_Budget#13L,Title#18,Worldwide_Gross#21L] Batched: false, DataFilters: [CASE WHEN (isnull(Worldwide_Gross#21L) OR isnull(Production_Budget#13L)) THEN false WHEN (Worldw..., Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/movies/mov..., PartitionFilters: [], PushedFilters: [], ReadSchema: struct<Production_Budget:bigint,Title:string,Worldwide_Gross:bigint>

===> note that the filter is pushed down as possible to the source, and the second filter is inlined (it will not be the case for python or scala udf)
    """
    tiered.show()


from pyspark.sql.functions import udf


@udf(returnType=StringType())
def python_udf(budget, gross) -> str:
    if gross is None or budget is None:
        return "Unknown"
    elif gross > budget * 2:
        return "blockbuster"
    elif gross > budget:
        return "profitable"
    else:
        return "flop"


def run_with_python_udf():
    tiered = (
        movies.withColumn(
            "Tier",
            python_udf(movies["Production_Budget"], movies["Worldwide_Gross"]),
        )
        .selectExpr("Title", "Worldwide_Gross", "Production_Budget", "Tier")
        .filter("Tier = 'blockbuster'")
    )
    tiered.explain()
    """
    == Physical Plan ==
*(2) Project [Title#18, Worldwide_Gross#21L, Production_Budget#13L, pythonUDF0#52 AS Tier#50]
+- BatchEvalPython [python_udf(Production_Budget#13L, Worldwide_Gross#21L)#48], [pythonUDF0#52]
   +- *(1) Project [Production_Budget#13L, Title#18, Worldwide_Gross#21L]
      +- *(1) Filter (pythonUDF0#51 = blockbuster)
         +- BatchEvalPython [python_udf(Production_Budget#13L, Worldwide_Gross#21L)#48], [pythonUDF0#51]
            +- FileScan json [Production_Budget#13L,Title#18,Worldwide_Gross#21L] Batched: false, DataFilters: [], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/movies/mov..., PartitionFilters: [], PushedFilters: [], ReadSchema: struct<Production_Budget:bigint,Title:string,Worldwide_Gross:bigint>
=>> see the diff,  Filter (pythonUDF0#51 = blockbuster) it is a black box spark cannot optimize it 
    """
    tiered.show()


def composed_sql_udf():
    spark.sql("""
    CREATE OR REPLACE TEMPORARY FUNCTION profit(gross BIGINT, budget BIGINT) RETURNS BIGINT 
    RETURN gross - budget
    """)

    spark.sql("""
    CREATE OR REPLACE TEMPORARY FUNCTION roi(gross BIGINT, budget BIGINT) RETURNS DOUBLE 
    RETURN CAST(profit(gross, budget) AS DOUBLE) / CAST(budget AS DOUBLE) * 100 
    """)
    movies.createOrReplaceTempView("movies")

    high_roi = spark.sql("""
                         SELECT Title,
                                Production_Budget,
                                Worldwide_Gross,
                                roi(Worldwide_Gross, Production_Budget) AS Roi
                         FROM movies
                         WHERE roi(Worldwide_Gross, Production_Budget) > 10
                         """)
    high_roi.explain()
    """
    == Physical Plan ==
*(1) Project [Title#18, Production_Budget#13L, Worldwide_Gross#21L, ((cast((Worldwide_Gross#21L - Production_Budget#13L) as double) / cast(Production_Budget#13L as double)) * 100.0) AS Roi#83]
+- *(1) Filter ((isnotnull(Worldwide_Gross#21L) AND isnotnull(Production_Budget#13L)) AND (((cast((Worldwide_Gross#21L - Production_Budget#13L) as double) / cast(Production_Budget#13L as double)) * 100.0) > 10.0))
   +- FileScan json [Production_Budget#13L,Title#18,Worldwide_Gross#21L] Batched: false, DataFilters: [isnotnull(Worldwide_Gross#21L), isnotnull(Production_Budget#13L), (((cast((Worldwide_Gross#21L -..., Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/movies/mov..., PartitionFilters: [], PushedFilters: [IsNotNull(Worldwide_Gross), IsNotNull(Production_Budget)], ReadSchema: struct<Production_Budget:bigint,Title:string,Worldwide_Gross:bigint>

==> filter is inlined even composed 
    """

    high_roi.show()


import re


@udf(returnType=StringType())
def extract_year(title):
    if not title:
        return None
    match = re.search(r"\((\d{4})\)", title)
    return str(match.group(1)) if match else None


from pyspark.sql.functions import col


def python_udf_required():
    year_df = movies.withColumn("year_from_title", extract_year("Title")).filter(
        col("year_from_title").isNotNull()
    )
    year_df.explain()
    year_df.show()


# note the SQL UDF can be called from the data frame API using selectExpr
# note sometimes we should use python udf for example to extract year within the title
# native col functions > SQL UDFs > python udf in optimization potential
# SQL UDFs are inlined (by Catalyst) to native expressions whenever possible
# python udfs are black boxed (not inlined) - use this only if SQL/dataframe api cannot or with difficulty compute the same thing
# dont be affraid to compose SQL UDFs
# can use sql udfs from the dataframe API from the selectExpr
if __name__ == "__main__":
    sql_udf()
    run_with_python_udf()
    composed_sql_udf()
    python_udf_required()
