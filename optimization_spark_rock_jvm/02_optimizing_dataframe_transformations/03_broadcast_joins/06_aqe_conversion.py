from pyspark.sql import SparkSession

# Doc : 00_broadcast_joins.md, section 6 (conversion en broadcast par AQE)

spark = (
    SparkSession.builder.appName("AQE Broadcast Conversion")
    .master("local[2]")
    .getOrCreate()  # AQE actif par défaut
)

table = spark.range(1, 10_000_000)
# créé depuis un RDD, comme 01_innocent_join.py : taille inconnue (Long.MaxValue)
lookup_table = spark.createDataFrame(
    spark.sparkContext.parallelize(
        [(0, "zero"), (1, "first"), (2, "second"), (3, "third")]
    ),
    ["id", "order"],
)


def final_plan(df):
    df.collect()  # collect() exécute le plan du DataFrame (show() non, voir 00_joins_and_size_estimation.md, 12.2)
    df.explain()


# 4 partitions non vides sur 200 (2 %) < nonEmptyPartitionRatioForBroadcastJoin (0.2)
# attendu : Initial Plan et Final Plan en SortMergeJoin
final_plan(table.join(lookup_table, "id"))

# ratio abaissé : AQE accepte de convertir
spark.conf.set("spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin", "0")
# attendu : Final Plan en BroadcastHashJoin, AQEShuffleRead local (shuffle déjà payé)
final_plan(table.join(lookup_table, "id"))
spark.conf.unset("spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin")

# moins de partitions de shuffle : 4 / 8 = 50 % > 0.2
spark.conf.set("spark.sql.shuffle.partitions", "8")
# attendu : Final Plan en BroadcastHashJoin
final_plan(table.join(lookup_table, "id"))
