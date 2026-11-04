from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast

# Doc : 00_joins_and_size_estimation.md, sections 3 (côté build vs streamé) et 5.3 (hint impossible)

spark = (
    SparkSession.builder.appName("Build Side")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)
# le WARN du hint ignoré apparaît dans la console à ce niveau
spark.sparkContext.setLogLevel("WARN")

big = spark.range(1, 10_000_000)  # ~80 Mo : jamais broadcast auto
small = spark.range(1, 100)

# inner : les deux côtés sont possibles
# attendu : BroadcastHashJoin ... BuildLeft
broadcast(small).join(big, "id", "inner").explain()

# left outer, broadcast à droite : possible
# attendu : BroadcastHashJoin ... LeftOuter, BuildRight
big.join(broadcast(small), "id", "left").explain()

# left outer, broadcast à gauche : impossible
# attendu : SortMergeJoin + WARN "Hint (strategy=broadcast) is not supported in the query: build left for left outer join"
broadcast(small).join(big, "id", "left").explain()

# left semi / left anti, broadcast à gauche : impossible aussi
# attendu : SortMergeJoin + WARN
broadcast(small).join(big, "id", "left_semi").explain()
broadcast(small).join(big, "id", "left_anti").explain()

# right outer, broadcast à gauche : possible
# attendu : BroadcastHashJoin ... RightOuter, BuildLeft
broadcast(small).join(big, "id", "right").explain()

# full outer : aucun côté
# attendu : SortMergeJoin (+ WARN) pour les deux
big.join(broadcast(small), "id", "full").explain()
broadcast(small).join(big, "id", "full").explain()

# le hint ignoré ne change pas le résultat, juste la stratégie
with_hint = broadcast(small).join(big, "id", "left").count()
without_hint = small.join(big, "id", "left").count()
print(
    f"left outer avec hint ignoré : {with_hint}, sans hint : {without_hint}"
)  # attendu : 99 et 99
