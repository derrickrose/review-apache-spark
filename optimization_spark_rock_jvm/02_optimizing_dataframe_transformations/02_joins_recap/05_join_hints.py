from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast

# Doc : 00_joins_and_size_estimation.md, sections 5 (hints) et 6 (explain)

spark = (
    SparkSession.builder.appName("Join Hints")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

big = spark.range(1, 10_000_000)
small = spark.range(1, 1_000)
big.createOrReplaceTempView("big")
small.createOrReplaceTempView("small")

# Syntaxe DataFrame
big.join(broadcast(small), "id").explain()  # attendu : BroadcastHashJoin
big.join(small.hint("merge"), "id").explain()  # attendu : SortMergeJoin
big.join(small.hint("shuffle_hash"), "id").explain()  # attendu : ShuffledHashJoin

# Syntaxe SQL + alias
for hint in [
    "BROADCAST",
    "BROADCASTJOIN",
    "MAPJOIN",  # attendu : BroadcastHashJoin
    "MERGE",
    "SHUFFLE_MERGE",
    "MERGEJOIN",  # attendu : SortMergeJoin
    "SHUFFLE_HASH",
]:  # attendu : ShuffledHashJoin
    print(f"=== /*+ {hint}(s) */")
    spark.sql(
        f"SELECT /*+ {hint}(s) */ * FROM big b JOIN small s ON b.id = s.id"
    ).explain()

# SHUFFLE_REPLICATE_NL : attendu CartesianProduct
spark.sql(
    "SELECT /*+ SHUFFLE_REPLICATE_NL(s) */ * FROM big b JOIN small s ON b.id < s.id"
).explain()

# Les hints restent actifs quand le broadcast auto est désactivé
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
big.join(small, "id").explain()  # attendu : SortMergeJoin
big.join(broadcast(small), "id").explain()  # attendu : BroadcastHashJoin
spark.conf.unset("spark.sql.autoBroadcastJoinThreshold")

# Astuce right -> left : mêmes lignes, ordre des colonnes différent
a = spark.createDataFrame([(1, "a"), (2, "b"), (3, "c")], ["id", "x"])
b = spark.createDataFrame([(1, "A"), (4, "D")], ["id", "y"])
right = broadcast(a).join(b, "id", "right").select("id", "x", "y")
left = b.join(broadcast(a), "id", "left").select("id", "x", "y")
print(sorted(right.collect()) == sorted(left.collect()))  # attendu : True
