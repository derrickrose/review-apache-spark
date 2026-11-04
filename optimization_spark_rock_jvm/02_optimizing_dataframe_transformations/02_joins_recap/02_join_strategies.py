import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast

# Doc : 00_joins_and_size_estimation.md, sections 2 (stratégies physiques) et 4 (BNLJ vs SMJ)

spark = (
    SparkSession.builder.appName("Join Strategies")
    .master("local[2]")
    # AQE désactivé pour voir le choix statique du planner dans explain()
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

big = spark.range(1, 10_000_000)  # ~80 Mo estimés : jamais broadcast auto
small = spark.range(1, 100)  # ~800 octets : broadcast auto

# 1. BroadcastHashJoin : un côté sous spark.sql.autoBroadcastJoinThreshold (10 Mo)
# attendu : BroadcastHashJoin ... BuildRight
big.join(small, "id").explain()

# 2. SortMergeJoin : aucun côté sous le seuil
# attendu : SortMergeJoin
big.join(spark.range(1, 10_000_000), "id").explain()

# 3. ShuffledHashJoin : jamais choisi par défaut (spark.sql.join.preferSortMergeJoin=true)
# attendu : ShuffledHashJoin
big.join(spark.range(1, 1_000_000).hint("shuffle_hash"), "id").explain()

# 3 bis. ShuffledHashJoin sans hint : preferSortMergeJoin=false et petit côté
# assez petit pour tenir en hash map par partition
# (sizeInBytes < autoBroadcastJoinThreshold × spark.sql.shuffle.partitions et 3× plus petit que l'autre)
# attendu : ShuffledHashJoin
spark.conf.set("spark.sql.join.preferSortMergeJoin", "false")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(1024 * 1024))  # 1 Mo
big.join(spark.range(1, 1_000_000), "id").explain()
spark.conf.unset("spark.sql.join.preferSortMergeJoin")
spark.conf.unset("spark.sql.autoBroadcastJoinThreshold")

# 4. BroadcastNestedLoopJoin : condition sans égalité, un côté broadcastable
# attendu : BroadcastNestedLoopJoin
big.join(small, big.id < small.id).explain()

# 5. CartesianProduct : cross join, aucun côté broadcastable
# attendu : CartesianProduct
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
spark.range(1, 1000).crossJoin(spark.range(1, 1000)).explain()
spark.conf.unset("spark.sql.autoBroadcastJoinThreshold")


# Section 4 : BNLJ vs SMJ sur une jointure d'égalité
def timed(label, df):
    start = time.perf_counter()
    n = df.count()
    print(f"{label}: {n} lignes en {time.perf_counter() - start:.1f} s")


a = spark.range(1, 2_000_000)
b = spark.range(1, 2_000)

# même résultat, stratégies différentes
# attendu : BNLJ (2 M × 2 000 comparaisons) nettement plus lent que SMJ
timed(
    "BroadcastNestedLoopJoin", a.join(broadcast(b), (a.id == b.id) | (a.id < 0))
)  # OR → plus d'égalité exploitable
timed("SortMergeJoin", a.join(b.hint("merge"), "id"))

# tout petit côté broadcasté : l'écart se réduit
tiny = spark.range(1, 10)
timed("BNLJ (côté minuscule)", a.join(broadcast(tiny), (a.id == tiny.id) | (a.id < 0)))
timed("SMJ  (côté minuscule)", a.join(tiny.hint("merge"), "id"))
