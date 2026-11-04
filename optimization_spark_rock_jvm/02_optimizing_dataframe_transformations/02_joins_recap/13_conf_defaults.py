from pyspark.sql import SparkSession

# Doc : 00_joins_and_size_estimation.md, section 13 (référence des confs)
# Lancer SANS config personnalisée (spark-defaults.conf, variables d'env) pour lire les vrais défauts.

spark = SparkSession.builder.appName("Conf Defaults").master("local[2]").getOrCreate()

SQL_CONFS = [
    "spark.sql.autoBroadcastJoinThreshold",  # attendu : 10485760b (10 Mo)
    "spark.sql.defaultSizeInBytes",  # attendu : 9223372036854775807
    "spark.sql.sources.fileCompressionFactor",  # attendu : 1.0
    "spark.sql.cbo.enabled",  # attendu : false
    "spark.sql.cbo.joinReorder.enabled",  # attendu : false
    "spark.sql.statistics.histogram.enabled",  # attendu : false
    "spark.sql.join.preferSortMergeJoin",  # attendu : true
    "spark.sql.adaptive.enabled",  # attendu : true
    "spark.sql.adaptive.autoBroadcastJoinThreshold",  # attendu : non défini
    "spark.sql.adaptive.nonEmptyPartitionRatioForBroadcastJoin",  # attendu : 0.2
    "spark.sql.adaptive.coalescePartitions.enabled",  # attendu : true
    "spark.sql.adaptive.advisoryPartitionSizeInBytes",  # attendu : 64MB
    "spark.sql.adaptive.skewJoin.enabled",  # attendu : true
    "spark.sql.adaptive.skewJoin.skewedPartitionFactor",  # attendu : 5.0
    "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes",  # attendu : 256MB
    "spark.sql.shuffle.partitions",  # attendu : 200
    "spark.sql.broadcastTimeout",  # attendu : 300
]

for key in SQL_CONFS:
    try:
        value = spark.conf.get(key)
    except Exception:
        value = "<non défini>"
    print(f"{key:62} {value}")

# confs du driver : pas des confs SQL, lues sur le SparkConf
for key, default in [
    ("spark.driver.memory", "1g"),
    ("spark.driver.maxResultSize", "1g"),
]:
    print(
        f"{key:62} {spark.sparkContext.getConf().get(key, f'<non défini, défaut documenté {default}>')}"
    )
