from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import BooleanType

spark = (
    SparkSession.builder.appName("predicate pushdown").master("local[*]").getOrCreate()
)


@udf(returnType=BooleanType())
def is_expensive_udf(budget):
    return budget is not None and budget > 100_000_000


from pathlib import Path

PATH = Path(__file__).parents[2]


def predicate_pushdown():
    movies = spark.read.json(str(PATH / "data/movies/"))

    movies.write.mode("overwrite").parquet("movies_parquet")

    movies_df = spark.read.parquet("movies_parquet")

    good_movies = movies_df.filter("IMDB_Rating > 7")
    good_movies.explain()
    """
    == Physical Plan ==
*(1) Filter (isnotnull(IMDB_Rating#75) AND (IMDB_Rating#75 > 7.0))
+- *(1) ColumnarToRow
   +- FileScan parquet [Creative_Type#72,Director#73,Distributor#74,IMDB_Rating#75,IMDB_Votes#76L,MPAA_Rating#77,Major_Genre#78,Production_Budget#79L,Release_Date#80,Rotten_Tomatoes_Rating#81L,Running_Time_min#82L,Source#83,Title#84,US_DVD_Sales#85L,US_Gross#86L,Worldwide_Gross#87L] Batched: true, DataFilters: [isnotnull(IMDB_Rating#75), (IMDB_Rating#75 > 7.0)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(IMDB_Rating), GreaterThan(IMDB_Rating,7.0)], ReadSchema: struct<Creative_Type:string,Director:string,Distributor:string,IMDB_Rating:double,IMDB_Votes:bigi...

==> note there are pushed filters all the way down to the source (parquet file) PushedFilters: [IsNotNull(IMDB_Rating)
    
    """
    good_movies.show()


def udf_blocks_filters():
    # UDF only -> PushedFilters: []
    movies = spark.read.json(str(PATH / "data/movies/"))
    movies.write.mode("overwrite").parquet("movies_parquet")
    movies_df = spark.read.parquet("movies_parquet")

    expensive = movies_df.filter(is_expensive_udf(col("Production_Budget")))
    expensive.explain()
    """"
== Physical Plan ==
*(2) Project [Creative_Type#72, Director#73, Distributor#74, IMDB_Rating#75, IMDB_Votes#76L, MPAA_Rating#77, Major_Genre#78, Production_Budget#79L, Release_Date#80, Rotten_Tomatoes_Rating#81L, Running_Time_min#82L, Source#83, Title#84, US_DVD_Sales#85L, US_Gross#86L, Worldwide_Gross#87L]
+- *(2) Filter pythonUDF0#106: boolean
   +- BatchEvalPython [is_expensive_udf(Production_Budget#79L)#104], [pythonUDF0#106]
      +- *(1) ColumnarToRow
         +- FileScan parquet [Creative_Type#72,Director#73,Distributor#74,IMDB_Rating#75,IMDB_Votes#76L,MPAA_Rating#77,Major_Genre#78,Production_Budget#79L,Release_Date#80,Rotten_Tomatoes_Rating#81L,Running_Time_min#82L,Source#83,Title#84,US_DVD_Sales#85L,US_Gross#86L,Worldwide_Gross#87L] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [], ReadSchema: struct<Creative_Type:string,Director:string,Distributor:string,IMDB_Rating:double,IMDB_Votes:bigi...

==> note that pushed filters empty PushedFilters: [],
=+> spark have to apply the filter row by row on +- *(2) Filter pythonUDF0#106: boolean
    
    """
    expensive.show()

    # prefer using native filter
    # Native pre-filter (pushed down) + UDF
    expensive_pushed = movies.filter(
        col("Production_Budget").isNotNull() & (col("Production_Budget") > 100_000_000)
    ).filter(is_expensive_udf(col("Production_Budget")))
    expensive_pushed.explain()

    """
    == Physical Plan ==
*(2) Project [Creative_Type#8, Director#9, Distributor#10, IMDB_Rating#11, IMDB_Votes#12L, MPAA_Rating#13, Major_Genre#14, Production_Budget#15L, Release_Date#16, Rotten_Tomatoes_Rating#17L, Running_Time_min#18L, Source#19, Title#20, US_DVD_Sales#21L, US_Gross#22L, Worldwide_Gross#23L]
+- *(2) Filter pythonUDF0#175: boolean
   +- BatchEvalPython [is_expensive_udf(Production_Budget#15L)#174], [pythonUDF0#175]
      +- *(1) Filter (isnotnull(Production_Budget#15L) AND (Production_Budget#15L > 100000000))
         +- FileScan json [Creative_Type#8,Director#9,Distributor#10,IMDB_Rating#11,IMDB_Votes#12L,MPAA_Rating#13,Major_Genre#14,Production_Budget#15L,Release_Date#16,Rotten_Tomatoes_Rating#17L,Running_Time_min#18L,Source#19,Title#20,US_DVD_Sales#21L,US_Gross#22L,Worldwide_Gross#23L] Batched: false, DataFilters: [isnotnull(Production_Budget#15L), (Production_Budget#15L > 100000000)], Format: JSON, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/data/movies], PartitionFilters: [], PushedFilters: [IsNotNull(Production_Budget), GreaterThan(Production_Budget,100000000)], ReadSchema: struct<Creative_Type:string,Director:string,Distributor:string,IMDB_Rating:double,IMDB_Votes:bigi...

==> the python filter is not necessary here +- *(2) Filter pythonUDF0#175: boolean
   +- BatchEvalPython [is_expensive_udf(Production_Budget#15L)#174], [pythonUDF0#175]

    """


def combine_column_pruning_predicate_pushdown():
    # UDF only -> PushedFilters: []
    movies = spark.read.json(str(PATH / "data/movies/"))
    movies.write.mode("overwrite").parquet("movies_parquet")

    movies_df = spark.read.parquet("movies_parquet").alias("movies")
    expensive_movies = spark.read.parquet("movies_parquet").select(
        "Title", "Production_Budget"
    )
    fucked_up_movies = (
        movies_df.join(expensive_movies, "Title")
        .filter("movies.Production_Budget > 100000000 AND movies.IMDB_Rating < 7")
        .select("movies.Title", "movies.Production_Budget", "movies.IMDB_Rating")
    )

    fucked_up_movies.explain()
    """
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [Title#84, Production_Budget#79L, IMDB_Rating#75]
   +- BroadcastHashJoin [Title#84], [Title#116], Inner, BuildRight, false
      :- Filter ((((isnotnull(Production_Budget#79L) AND isnotnull(IMDB_Rating#75)) AND (Production_Budget#79L > 100000000)) AND (IMDB_Rating#75 < 7.0)) AND isnotnull(Title#84))
      :  +- FileScan parquet [IMDB_Rating#75,Production_Budget#79L,Title#84] Batched: true, DataFilters: [isnotnull(Production_Budget#79L), isnotnull(IMDB_Rating#75), (Production_Budget#79L > 100000000)..., Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(Production_Budget), IsNotNull(IMDB_Rating), GreaterThan(Production_Budget,100000000), ..., ReadSchema: struct<IMDB_Rating:double,Production_Budget:bigint,Title:string>
      +- BroadcastExchange HashedRelationBroadcastMode(List(input[0, string, false]),false), [plan_id=41]
         +- Filter isnotnull(Title#116)
            +- FileScan parquet [Title#116] Batched: true, DataFilters: [isnotnull(Title#116)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(Title)], ReadSchema: struct<Title:string>

==> WE CAN SEE THE PUSHED FILTERS ALSO THE PROJECTION PUSHDOWN    EVEN THE FILTER AND THE PROJECTION WAS DONE LAST

PushedFilters: [IsNotNull(Title)], ReadSchema: struct<Title:string>
    
    """
    fucked_up_movies.show()


## prefer parquet over csv/json (parquet support predicate pushdown)
## prefer native filtering instead of udf
## combine predicates pushdown with column pruning or dynamic partition pruning
## spark 4.3 optimizes the udf function to sql function ? to verify
## predicates pushdown work through operation like joins or aggs => catalyst engine will push the filters and projection down as possible
## sql udf (especially spark 4) are preferable because spark can inline sql udf and can analyze and push down the filters as much as possible


if __name__ == "__main__":
    # predicate_pushdown()
    # udf_blocks_filters()
    combine_column_pruning_predicate_pushdown()
