from pathlib import Path

from pyspark import RDD, SparkContext
from pyspark.sql import Column, DataFrame, SparkSession

spark: SparkSession = (
    SparkSession.builder.appName("Joins Recap").master("local[2]").getOrCreate()
)
sc: SparkContext = spark.sparkContext

# repo root -> data/
DATA: Path = Path(__file__).resolve().parents[3] / "data"

# inferSchema is ignored by the JSON reader (the schema is always inferred)
guitars_df: DataFrame = spark.read.json(str(DATA / "guitars"))
guitarists_df: DataFrame = spark.read.json(str(DATA / "guitarPlayers"))
bands_df: DataFrame = spark.read.json(str(DATA / "bands"))

# inner joins
join_condition: Column = guitarists_df["band"] == bands_df["id"]
guitarists_bands_df: DataFrame = guitarists_df.join(bands_df, join_condition, "inner")

# outer joins
# left outer = everything in inner join + all the rows in the LEFT table, with nulls in the rows not passing the condition in the RIGHT table
guitarists_df.join(bands_df, join_condition, "left_outer")
# right outer = everything in inner join + all the rows in the RIGHT table, with nulls in the rows not passing the condition in the LEFT table
guitarists_df.join(bands_df, join_condition, "right_outer")
# outer join = everything in left_outer + right_outer
guitarists_df.join(bands_df, join_condition, "outer")

# semi joins = everything in the left DF for which THERE IS a row in the right DF satisfying the condition
# essentially a filter
guitarists_df.join(bands_df, join_condition, "left_semi")

# anti join = everything in the left DF for which THERE IS NOT a row in the right DF satisfying the condition
# also a filter
guitarists_df.join(bands_df, join_condition, "left_anti")

# cross join = everything in the left table with everything in the right table
# dangerous: NRows(crossjoin) = NRows(left) x NRows(right)
# careful with outer joins with non-unique keys
guitarists_df.crossJoin(bands_df)

# RDD joins
colors_scores: list[tuple[str, int]] = [
    ("blue", 1),
    ("red", 4),
    ("green", 5),
    ("yellow", 2),
    ("orange", 3),
    ("cyan", 0),
]
colors_rdd: RDD[tuple[str, int]] = sc.parallelize(colors_scores)
text: str = "The sky is blue, but the orange pale sun turns from yellow to red"
words: list[tuple[str, int]] = [
    (w.lower(), 1) for w in text.split(" ")
]  # standard technique for counting words with RDDs
words_rdd: RDD[tuple[str, int]] = sc.parallelize(words).reduceByKey(
    lambda a, b: a + b
)  # counting word occurrence
scores: RDD[tuple[str, tuple[int, int]]] = words_rdd.join(
    colors_rdd
)  # implied join type is INNER -> (word, (count, score))

if __name__ == "__main__":
    guitarists_bands_df.show()
    print(scores.collect())
