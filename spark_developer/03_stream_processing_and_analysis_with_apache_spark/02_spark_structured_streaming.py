# spark structured streaming


from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

spark = SparkSession.builder.appName("structured_streaming").getOrCreate()

schema = StructType(
    [
        StructField("id", IntegerType()),
        StructField("name", StringType()),
        StructField("age", IntegerType()),
        StructField("gender", StringType()),
    ]
)

df = (
    spark.readStream.format("json")
    # .option("maxFilesPerTrigger", 1)
    .option("maxOffsetsPerTrigger", 1)
    # .option("multiLine", True)
    .option("mode", "PERMISSIVE")
    .schema(schema)
    .load("input")
)


query = df.writeStream.format("console").outputMode("append").start()

#
query.awaitTermination()  # this makes spark wait for data to be processed
# print(query.isActive)
