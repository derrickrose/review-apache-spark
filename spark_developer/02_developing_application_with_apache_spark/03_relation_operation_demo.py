from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import json


def get_value(path):
    with open(path, "r") as f:
        return json.load(f)


# TODO
## spark does not see df aliasing inside a join
## spark remove aliasing after projection, filtering ....
## what is column pruning ??
## better select than drop if data still on physical storage
## TODO demo with subtract and intersect

spark = SparkSession.builder.appName("relation").getOrCreate()

clients = get_value("clients.json")
customers_df = (
    spark.createDataFrame(clients)
    .select("id", col("name").alias("customer_nam"))
    .alias("c")
)
customers_df.printSchema()

products = get_value("products.json")
products_df = (
    spark.createDataFrame(products)
    .select(
        "id",
        "brand",
        "model",
        col("name").alias("product_name"),
        col("price").alias("unit_price"),
        "category",
    )
    .alias("p")
)
products_df.printSchema()

orders = get_value("orders.json")
orders_df = (
    spark.createDataFrame(orders)
    .select(
        "product_id",
        "client_id",
        "order_date",
        "payment_method",
        "quantity",
        "shipping_address",
        "status",
        "total_price",
    )
    .alias("o")
)
orders_df.printSchema()

customers_df.show()
products_df.show()
orders_df.show()

import pyspark.sql.functions as F

enriched_orders_df = (
    customers_df.join(
        orders_df,  # c.id == o.client_id,
        # F.col("id") == F.col("client_id"),
        [F.col("c.id") == F.col("o.client_id")],
        "inner",
    ).drop("id")
).alias("t")

enriched_orders_df.show()

enriched_transactions_df = products_df.join(
    enriched_orders_df,
    [F.col("p.id") == F.col("t.product_id")],
    "inner",
).drop("id")
enriched_transactions_df.show()
enriched_transactions_df.printSchema()
