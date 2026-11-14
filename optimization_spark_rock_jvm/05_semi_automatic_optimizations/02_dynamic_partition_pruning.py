from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("Dynamic Partition Pruning")
    .master("local[*]")
    .config("spark.sql.optimize.dynamicPartitionPruning", "true")
    .getOrCreate()
)

sales_df = spark.range(5000000).selectExpr("""
id as sale_id,
CAST(id % 100 AS INT) as product_id, 
CAST(id % 365 AS INT) as day_of_year, 
CAST(rand() * 1000 AS DECIMAL(10,2)) as amount 
""")

sales_df.write.partitionBy("product_id").parquet("dynamic_pruning/sales_data/")

products = list(
    map(
        lambda x: (
            x,
            f"Product_{x}",
            "Electronics" if x < 10 else ("Clothing" if x < 30 else "Other"),
        ),
        range(100),
    )
)

from pyspark.sql.types import StructType, StructField, IntegerType, StringType

products_schema = StructType(
    [
        StructField("product_id", IntegerType()),
        StructField("product_name", StringType()),
        StructField("product_category", StringType()),
    ]
)

products_df = spark.createDataFrame(products, products_schema)
products_df.write.parquet("dynamic_pruning/products_data/")


def staticPruning():
    sales_df = spark.read.parquet("dynamic_pruning/sales_data/").filter(
        "product_id = 5"
    )
    sales_df.explain()
    """
    """
    print(sales_df.count())


if __name__ == "__main__":
    import time

    staticPruning()
    time.sleep(10000)
