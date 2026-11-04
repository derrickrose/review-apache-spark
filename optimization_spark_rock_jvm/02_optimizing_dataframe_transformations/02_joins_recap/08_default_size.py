from pyspark.sql import SparkSession
from pyspark.sql.functions import lit

# Doc : 00_joins_and_size_estimation.md, section 8 (defaultSize)

spark = SparkSession.builder.appName("Default Size").master("local[2]").getOrCreate()

DataType = spark._jvm.org.apache.spark.sql.types.DataType


def size_in_bytes(df):
    return int(
        df._jdf.queryExecution().optimizedPlan().stats().sizeInBytes().toString()
    )


# 8.1 / 8.2 : defaultSize par type
for ddl in [
    "boolean",
    "tinyint",
    "smallint",
    "int",
    "bigint",
    "float",
    "double",
    "decimal(18,2)",
    "decimal(38,2)",
    "string",
    "binary",
    "date",
    "timestamp",
    "timestamp_ntz",
    "interval day to second",
    "interval year to month",
    "array<int>",
    "map<string,bigint>",
    "struct<a:int,b:string>",
    "array<array<string>>",
]:
    print(f"{ddl:28} {DataType.fromDDL(ddl).defaultSize()}")
# attendu : voir tableaux 8.1 / 8.2 ; array<array<string>> = 20 (1 élément × 1 élément × 20)

# 8.3 petite table : 1 000 lignes (id int, nom string) en LocalRelation (VALUES)
values = ", ".join(f"({i}, 'n{i}')" for i in range(1000))
local = spark.sql(f"SELECT * FROM VALUES {values} AS t(id, nom)")
print(
    "1 000 × (int + string) :", size_in_bytes(local)
)  # attendu : 32 000 = 1 000 × (8 + 4 + 20), en-tête de 8 octets inclus

# 8.3 grosse table : 2 M lignes × 100 colonnes string, dérivée d'un range
wide = spark.range(2_000_000).select(
    [lit("x").cast("string").alias(f"c{i}") for i in range(100)]
)
print("2 M × 100 string (via range + select) :", size_in_bytes(wide))
# attendu : PAS 4 Go. Le select est estimé par ratio sur le range :
#   16 000 000 (range) × (8 + 2 000) / (8 + 8) ≈ 2,008 Go
# le 4 Go de la doc suppose un rowCount connu (CBO) : 2 M × (8 + 2 000) ≈ 4,016 Go

# la vraie taille des valeurs n'est pas prise en compte
short = spark.range(1000).select(lit("x").alias("s"))
long_ = spark.range(1000).select(lit("x" * 5000).alias("s"))
print(
    "string de 1 car. vs 5 000 car. :", size_in_bytes(short), size_in_bytes(long_)
)  # attendu : identiques
