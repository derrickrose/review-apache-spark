from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast

# Doc : 00_broadcast_joins.md, section 5 (forcer ou contourner)

spark = (
    SparkSession.builder.appName("Force or Cache")
    .master("local[2]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

table = spark.range(1, 100_000_000)
# créé depuis un RDD, comme 01_innocent_join.py : taille inconnue (Long.MaxValue)
lookup_table = spark.createDataFrame(
    spark.sparkContext.parallelize(
        [(0, "zero"), (1, "first"), (2, "second"), (3, "third")]
    ),
    ["id", "order"],
)

# sans rien : taille inconnue → attendu : SortMergeJoin
table.join(lookup_table, "id").explain()

# 5.1 hint broadcast() → attendu : BroadcastHashJoin
table.join(broadcast(lookup_table), "id").explain()

# 5.1 broadcast auto désactivé : le hint reste actif → attendu : BroadcastHashJoin
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
table.join(broadcast(lookup_table), "id").explain()
spark.conf.unset("spark.sql.autoBroadcastJoinThreshold")

# 5.2 cache() + action : taille réelle connue dès la planification → attendu : BroadcastHashJoin
lookup_table.cache()
lookup_table.count()
table.join(lookup_table, "id").explain()
