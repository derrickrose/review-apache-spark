import time
from pyspark.sql import SparkSession, Row
from pyspark.sql.types import StructType, StructField, IntegerType, StringType

spark = (
    SparkSession.builder
    .appName("Broadcast Joins")
    .master("local")
    .getOrCreate()
)

sc = spark.sparkContext

rows = sc.parallelize([
    Row(0, "zero"),
    Row(1, "first"),
    Row(2, "second"),
    Row(3, "third"),
])

rows_schema = StructType([
    StructField("id", IntegerType()),
    StructField("order", StringType()),
])

# small table
lookup_table = spark.createDataFrame(rows, rows_schema)

# large table
table = spark.range(1, 100000000)  # column is "id"

table_x = spark.range(1, 10)

# the innocent join
# pas de broadcast auto meme si la table est petite car spark croit que la table contient autant de row que la valeur max


joined = table.join(lookup_table, "id")
joined.explain()
joined.show()
joined.explain()
# auto broadcasted ? why ???? il connait exactement la valeur de range
dd = table_x.join(table, "id")
dd.explain()
dd.show()
dd.explain()
if __name__ == "__main__":
    time.sleep(1000)
