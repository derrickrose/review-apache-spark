from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("Dynamic Partition Pruning")
    .master("local[*]")
    .config("spark.sql.optimizer.dynamicPartitionPruning.enabled", "true")
    .getOrCreate()
)

sales_df = spark.range(5000000).selectExpr(
    "id as sale_id",
    "CAST(id % 100 AS INT) as product_id",
    "CAST(id % 365 AS INT) as day_of_year",
    "CAST(rand() * 1000 AS DECIMAL(10,2)) as amount",
)

sales_region_df = spark.range(5000000).selectExpr(
    "id as sale_id",
    "CAST(id % 10 AS INT) as region_id",
    "CAST(id % 100 AS INT) as product_id",
    "CAST(id % 365 AS INT) as day_of_year",
    "CAST(rand() * 1000 AS DECIMAL(10,2)) as amount",
)

sales_df.write.format("parquet").partitionBy("product_id").mode("overwrite").save(
    "dynamic_pruning/sales_data/"
)

sales_region_df.write.format("parquet").partitionBy("region_id", "product_id").mode(
    "overwrite"
).save("dynamic_pruning/sales_region_data/")

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

region_products = [
    (
        region_id,
        product_id,
        {0: "US", 1: "EU", 2: "APAC", 3: "LATAM"}.get(region_id, "OTHER"),
        "featured" if region_id == 3 and product_id < 5 else "standard",
    )
    for region_id in range(10)
    for product_id in range(100)
]

from pyspark.sql.types import StructType, StructField, IntegerType, StringType

products_schema = StructType(
    [
        StructField("product_id", IntegerType()),
        StructField("product_name", StringType()),
        StructField("product_category", StringType()),
    ]
)

products_df = spark.createDataFrame(products, products_schema)
products_df.write.format("parquet").mode("overwrite").save(
    "dynamic_pruning/products_data/"
)

from pyspark.sql.types import StructType, StructField, IntegerType, StringType

region_products_schema = StructType(
    [
        StructField("region_id", IntegerType()),
        StructField("product_id", IntegerType()),
        StructField("region_name", StringType()),
        StructField("product_tier", StringType()),
    ]
)

region_products_df = spark.createDataFrame(region_products, region_products_schema)
region_products_df.write.format("parquet").mode("overwrite").save(
    "dynamic_pruning/region_products_data/"
)


# static partition pruning (on the exec, the engine have information about the partition)
# if the data was not partitioned, the engine will have to scan the entire dataset
def static_pruning():
    sales_df = spark.read.parquet("dynamic_pruning/sales_data/").filter(
        "product_id = 5"
    )
    sales_df.explain()
    """
    == Physical Plan ==
*(1) ColumnarToRow
+- FileScan parquet [sale_id#20L,day_of_year#21,product_id#22] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [isnotnull(product_id#22), (product_id#22 = 5)], PushedFilters: [], ReadSchema: struct<sale_id:bigint,day_of_year:int>
    
===> look at PartitionFilters: [isnotnull(product_id#22), (product_id#22 = 5)]   this is a partition pruning at source level with product id is 5   
    
    """
    print(sales_df.count())


def dynamic_pruning():
    from pyspark.sql.functions import sum

    sales = spark.read.parquet("dynamic_pruning/sales_data/")
    products = spark.read.parquet("dynamic_pruning/products_data/")
    electronics = (
        sales.join(products, "product_id")
        .filter("product_category = 'Electronics'")
        .groupBy("product_name")
        .agg(sum("amount").alias("total_revenue"))
    )

    electronics.explain()
    """
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[product_name#32], functions=[sum(amount#25)])
   +- Exchange hashpartitioning(product_name#32, 200), ENSURE_REQUIREMENTS, [plan_id=81]
      +- HashAggregate(keys=[product_name#32], functions=[partial_sum(amount#25)])
         +- Project [amount#25, product_name#32]
            +- BroadcastHashJoin [product_id#26], [product_id#31], Inner, BuildRight, false
               :- FileScan parquet [amount#25,product_id#26] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [isnotnull(product_id#26), dynamicpruningexpression(product_id#26 IN dynamicpruning#55)], PushedFilters: [], ReadSchema: struct<amount:decimal(10,2)>
               :     +- SubqueryAdaptiveBroadcast dynamicpruning#55, 0, true, Project [product_id#31, product_name#32], [product_id#31]
               :        +- AdaptiveSparkPlan isFinalPlan=false
               :           +- Project [product_id#31, product_name#32]
               :              +- Filter ((isnotnull(product_category#33) AND (product_category#33 = Electronics)) AND isnotnull(product_id#31))
               :                 +- FileScan parquet [product_id#31,product_name#32,product_category#33] Batched: true, DataFilters: [isnotnull(product_category#33), (product_category#33 = Electronics), isnotnull(product_id#31)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(product_category), EqualTo(product_category,Electronics), IsNotNull(product_id)], ReadSchema: struct<product_id:int,product_name:string,product_category:string>
               +- BroadcastExchange HashedRelationBroadcastMode(List(cast(input[0, int, true] as bigint)),false), [plan_id=76]
                  +- Project [product_id#31, product_name#32]
                     +- Filter ((isnotnull(product_category#33) AND (product_category#33 = Electronics)) AND isnotnull(product_id#31))
                        +- FileScan parquet [product_id#31,product_name#32,product_category#33] Batched: true, DataFilters: [isnotnull(product_category#33), (product_category#33 = Electronics), isnotnull(product_id#31)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(product_category), EqualTo(product_category,Electronics), IsNotNull(product_id)], ReadSchema: struct<product_id:int,product_name:string,product_category:string>

==> we can see that spark filtered the data at source then knows which data is inside which partition so performed a partition pruning 
PartitionFilters: [isnotnull(product_id#26), dynamicpruningexpression(product_id#26 IN dynamicpruning#55)] before the join
==> with dynamic partition pruning on it is pretty fast arount 1second 

==> now with dynamic partition pruning off it is pretty slow arount 2seconds (doubled down) 
==> also the query plan is different
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[product_name#32], functions=[sum(amount#25)])
   +- Exchange hashpartitioning(product_name#32, 200), ENSURE_REQUIREMENTS, [plan_id=70]
      +- HashAggregate(keys=[product_name#32], functions=[partial_sum(amount#25)])
         +- Project [amount#25, product_name#32]
            +- BroadcastHashJoin [product_id#26], [product_id#31], Inner, BuildRight, false
               :- FileScan parquet [amount#25,product_id#26] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [isnotnull(product_id#26)], PushedFilters: [], ReadSchema: struct<amount:decimal(10,2)>
               +- BroadcastExchange HashedRelationBroadcastMode(List(cast(input[0, int, true] as bigint)),false), [plan_id=65]
                  +- Project [product_id#31, product_name#32]
                     +- Filter ((isnotnull(product_category#33) AND (product_category#33 = Electronics)) AND isnotnull(product_id#31))
                        +- FileScan parquet [product_id#31,product_name#32,product_category#33] Batched: true, DataFilters: [isnotnull(product_category#33), (product_category#33 = Electronics), isnotnull(product_id#31)], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(product_category), EqualTo(product_category,Electronics), IsNotNull(product_id)], ReadSchema: struct<product_id:int,product_name:string,product_category:string>

    """
    electronics.show()


# improved in spark 4
# spark can broadcast multiple filtering keys for dynamic partition pruning
# joins gains compound fact tables prune at runtime
# when we filter by region_name and product_tier, neither of them are partition keys
# but spark is able to figure out which partition is relevant for the region name LATAM and product tier featured
def multi_key_dynamic_partition_pruning():
    from pyspark.sql.functions import sum

    sales_regions_df = spark.read.parquet("dynamic_pruning/sales_region_data/")
    regions_products_df = spark.read.parquet("dynamic_pruning/region_products_data/")
    featured_revenues = (
        sales_regions_df.join(regions_products_df, on=["region_id", "product_id"])
        .filter("region_name = 'LATAM' AND product_tier = 'featured'")
        .groupBy("region_name")
        .agg(sum("amount").alias("total"))
    )
    featured_revenues.explain()
    """"
    == Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- HashAggregate(keys=[region_name#64], functions=[sum(amount#54)])
   +- Exchange hashpartitioning(region_name#64, 200), ENSURE_REQUIREMENTS, [plan_id=125]
      +- HashAggregate(keys=[region_name#64], functions=[partial_sum(amount#54)])
         +- Project [amount#54, region_name#64]
            +- BroadcastHashJoin [region_id#55, product_id#56], [region_id#62, product_id#63], Inner, BuildRight, false
               :- FileScan parquet [amount#54,region_id#55,product_id#56] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [isnotnull(region_id#55), isnotnull(product_id#56), dynamicpruningexpression(region_id#55 IN dyna..., PushedFilters: [], ReadSchema: struct<amount:decimal(10,2)>
               :     :- SubqueryAdaptiveBroadcast dynamicpruning#90, 0, true, Project [region_id#62, product_id#63, region_name#64], [region_id#62, product_id#63]
               :     :  +- AdaptiveSparkPlan isFinalPlan=false
               :     :     +- Project [region_id#62, product_id#63, region_name#64]
               :     :        +- Filter (((((isnotnull(region_name#64) AND isnotnull(product_tier#65)) AND (region_name#64 = LATAM)) AND (product_tier#65 = featured)) AND isnotnull(region_id#62)) AND isnotnull(product_id#63))
               :     :           +- FileScan parquet [region_id#62,product_id#63,region_name#64,product_tier#65] Batched: true, DataFilters: [isnotnull(region_name#64), isnotnull(product_tier#65), (region_name#64 = LATAM), (product_tier#6..., Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(region_name), IsNotNull(product_tier), EqualTo(region_name,LATAM), EqualTo(product_tie..., ReadSchema: struct<region_id:int,product_id:int,region_name:string,product_tier:string>
               :     +- SubqueryAdaptiveBroadcast dynamicpruning#91, 1, true, Project [region_id#62, product_id#63, region_name#64], [region_id#62, product_id#63]
               :        +- AdaptiveSparkPlan isFinalPlan=false
               :           +- Project [region_id#62, product_id#63, region_name#64]
               :              +- Filter (((((isnotnull(region_name#64) AND isnotnull(product_tier#65)) AND (region_name#64 = LATAM)) AND (product_tier#65 = featured)) AND isnotnull(region_id#62)) AND isnotnull(product_id#63))
               :                 +- FileScan parquet [region_id#62,product_id#63,region_name#64,product_tier#65] Batched: true, DataFilters: [isnotnull(region_name#64), isnotnull(product_tier#65), (region_name#64 = LATAM), (product_tier#6..., Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(region_name), IsNotNull(product_tier), EqualTo(region_name,LATAM), EqualTo(product_tie..., ReadSchema: struct<region_id:int,product_id:int,region_name:string,product_tier:string>
               +- BroadcastExchange HashedRelationBroadcastMode(List((shiftleft(cast(input[0, int, true] as bigint), 32) | (cast(input[1, int, true] as bigint) & 4294967295))),false), [plan_id=120]
                  +- Project [region_id#62, product_id#63, region_name#64]
                     +- Filter (((((isnotnull(region_name#64) AND isnotnull(product_tier#65)) AND (region_name#64 = LATAM)) AND (product_tier#65 = featured)) AND isnotnull(region_id#62)) AND isnotnull(product_id#63))
                        +- FileScan parquet [region_id#62,product_id#63,region_name#64,product_tier#65] Batched: true, DataFilters: [isnotnull(region_name#64), isnotnull(product_tier#65), (region_name#64 = LATAM), (product_tier#6..., Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [], PushedFilters: [IsNotNull(region_name), IsNotNull(product_tier), EqualTo(region_name,LATAM), EqualTo(product_tie..., ReadSchema: struct<region_id:int,product_id:int,region_name:string,product_tier:string>


==> now look at this, we have 2 SubqueryAdaptiveBroadcast dynamicpruning (preparation of the real query of data for the relevant partition)
=+> each filter has its own section SubqueryAdaptiveBroadcast dynamicpruning (region id and product id ) 
 
note that on filescan the dynamic pruning expression is cutt off (using ...), better see at the UI :- FileScan parquet [amount#54,region_id#55,product_id#56] Batched: true, DataFilters: [], Format: Parquet, Location: InMemoryFileIndex(1 paths)[file:/home/frils/Documents/reviews/review-apache-spark/optimization_sp..., PartitionFilters: [isnotnull(region_id#55), isnotnull(product_id#56), dynamicpruningexpression(region_id#55 IN dyna..., PushedFilters: [], ReadSchema: struct<amount:decimal(10,2)>

on spark uI 


(1) Scan parquet 
Output [3]: [amount#54, region_id#55, product_id#56]
Batched: true
Location: InMemoryFileIndex [file:/home/frils/Documents/reviews/review-apache-spark/optimization_spark_rock_jvm/05_semi_automatic_optimizations/dynamic_pruning/sales_region_data]
PartitionFilters: [isnotnull(region_id#55), isnotnull(product_id#56), dynamicpruningexpression(region_id#55 IN dynamicpruning#102), dynamicpruningexpression(product_id#56 IN dynamicpruning#103)]
ReadSchema: struct<amount:decimal(10,2)>

==> we can see the dynamic pruning on region_id and product_id 
    """
    featured_revenues.show()


# when dynamic partition pruning is not applied ?
## tables are not partitioned
## for non equi joins
## if spark decides that it is too much of overhead (skip the dynamic pruning)

if __name__ == "__main__":
    import time

    # static_pruning()
    # dynamic_pruning()
    multi_key_dynamic_partition_pruning()
    time.sleep(10000)
