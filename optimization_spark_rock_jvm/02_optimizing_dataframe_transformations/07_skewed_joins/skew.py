from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("Skew joins")
    .master("local[*]")
    .config("spark.sql.adaptive.enabled", "false")
    .getOrCreate()
)

spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "false")
# deactivate autobroadcast
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")

"""
2 laptops are similar if they have the same make and model, but proc speed within 0.1

for each laptop configuration, we are interested in average sale price of similar laptops


Acer Predator 2.9GHz  avlfaskjhrw -> average sale price for all acer predators with CPU speed between 2.8 and 3.0 GHz
"""
import data_generator

laptops = [data_generator.random_laptop() for _ in range(40000)]

laptops_df = spark.createDataFrame(laptops, data_generator.LAPTOP_SCHEMA)

laptops_offers_df = spark.createDataFrame(
    [data_generator.random_laptop_offer() for _ in range(100000)],
    data_generator.LAPTOP_OFFER_SCHEMA,
)

import pyspark.sql.functions as F

joined_df = (
    laptops_df.join(laptops_offers_df, on=["make", "model"])
    .filter(F.round(F.abs(laptops_df["proc_speed"] - laptops_offers_df["proc_speed"]), 1) <= 0.1)
    .groupBy(laptops_df["registration"])
    .agg(F.avg(laptops_offers_df["sale_price"]).alias("avg_price"))
)

# why groupBy registration because it is the unique identifier, make model is not unique
# joined_df.show()
# joined_df.explain()
"""
== Physical Plan ==
*(6) HashAggregate(keys=[registration#0], functions=[avg(sale_price#11)])
+- Exchange hashpartitioning(registration#0, 200), ENSURE_REQUIREMENTS, [plan_id=134]
   +- *(5) HashAggregate(keys=[registration#0], functions=[partial_avg(sale_price#11)])
      +- *(5) Project [registration#0, sale_price#11]
         +- *(5) SortMergeJoin [make#1, model#2], [make#8, model#9], Inner, (abs((proc_speed#3 - proc_speed#10)) <= 0.1)
            :- *(2) Sort [make#1 ASC NULLS FIRST, model#2 ASC NULLS FIRST], false, 0
            :  +- Exchange hashpartitioning(make#1, model#2, 200), ENSURE_REQUIREMENTS, [plan_id=119]
            :     +- *(1) Scan ExistingRDD[registration#0,make#1,model#2,proc_speed#3]
            +- *(4) Sort [make#8 ASC NULLS FIRST, model#9 ASC NULLS FIRST], false, 0
               +- Exchange hashpartitioning(make#8, model#9, 200), ENSURE_REQUIREMENTS, [plan_id=125]
                  +- *(3) Scan ExistingRDD[make#8,model#9,proc_speed#10,sale_price#11]
                  
on the UI one stage tooks most of the time and the shuffle is pretty tiny, it is not the real problem of this job                   

| Stage Id | Description | Submitted           | Duration | Tasks   | Input | Output | Shuffle Read | Shuffle Write |
|----------|-------------|---------------------|----------|---------|-------|--------|--------------|---------------|
| 3        | showString  | 2026/11/06 11:39:08 | 50 ms    | 1/1     |       |        | 3.1 KiB      |               |
| 2        | showString  | 2026/11/06 11:38:18 | 49 s     | 200/200 |       |        | 1427.6 KiB   | 655.9 KiB     |
| 1        | showString  | 2026/11/06 11:38:15 | 0.6 s    | 8/8     |       |        |              | 540.0 KiB     |
| 0        | showString  | 2026/11/06 11:38:15 | 3 s      | 8/8     |       |        |              | 887.6 KiB     |

I you click on the stage 2, you will see that one of the tasks is taking most of the time. Task index 6

| Index | Task ID | Attempt | Status  | Locality      | Executor | Host         | Launch Time         | Duration | GC Time | Shuffle Write Size / Records | Shuffle Read Size / Records |
|-------|---------|---------|---------|---------------|----------|--------------|---------------------|----------|---------|------------------------------|-----------------------------|
| 6     | 16      | 0       | SUCCESS | NODE_LOCAL    | driver   | 192.168.1.88 | 2026-11-06 11:38:18 | 49 s     | 0.1 s   | 315 KiB / 22995              | 814.9 KiB / 80230           |
| 162   | 19      | 0       | SUCCESS | NODE_LOCAL    | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 4 s      | 62.0 ms | 56.1 KiB / 2880              | 102.4 KiB / 9968            |
| 128   | 17      | 0       | SUCCESS | NODE_LOCAL    | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 4 s      | 62.0 ms | 57.4 KiB / 2864              | 102.8 KiB / 10020           |
| 191   | 22      | 0       | SUCCESS | NODE_LOCAL    | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 3 s      | 36.0 ms | 56.9 KiB / 2763              | 101.7 KiB / 9971            |
| 167   | 20      | 0       | SUCCESS | NODE_LOCAL    | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 3 s      | 29.0 ms | 57 KiB / 2827                | 101.5 KiB / 9924            |
| 185   | 21      | 0       | SUCCESS | NODE_LOCAL    | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 3 s      | 29.0 ms | 56.8 KiB / 2846              | 102.1 KiB / 9960            |
| 129   | 18      | 0       | SUCCESS | NODE_LOCAL    | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 3 s      | 29.0 ms | 56.7 KiB / 2825              | 102.2 KiB / 9927            |
| 0     | 23      | 0       | SUCCESS | PROCESS_LOCAL | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 0.4 s    |         |                              |                             |
| 3     | 26      | 0       | SUCCESS | PROCESS_LOCAL | driver   | 192.168.1.88 | 2026-11-06 11:38:19 | 0.2 s    |         |                              |                             |

=> this task index 6 is called a straggling task (struggle + lagging), even if we are not doing any shuffle (shuffle in order or megabite) 
=> this task is taking lot of time 
=> to identify a straggling task by analysing the metrics of the tasks (still on the stage page)

Summary Metrics for 200 Completed Tasks

| Metric                       | Min       | 25th percentile | Median    | 75th percentile | Max               |
|------------------------------|-----------|-----------------|-----------|-----------------|-------------------|
| Duration                     | 10.0 ms   | 23.0 ms         | 35.0 ms   | 52.0 ms         | 49 s              |
| GC Time                      | 0.0 ms    | 0.0 ms          | 0.0 ms    | 0.0 ms          | 0.1 s             |
| Shuffle Read Size / Records  | 0.0 B / 0 | 0.0 B / 0       | 0.0 B / 0 | 0.0 B / 0       | 814.9 KiB / 80230 |
| Shuffle Write Size / Records | 0.0 B / 0 | 0.0 B / 0       | 0.0 B / 0 | 0.0 B / 0       | 315 KiB / 22995   |

=> this summy tells us everything median duration is 23.0 ms and the max is 49 s, more than 3 order magnitude difference 

=>> why ? because we using a join which send the same key to the same executor 
=>> this is taking time because this particular executor has a disproportion amount of data to process 

"""

# fix: explode each laptop into its 3 neighbour speeds (-0.1, same, +0.1)
# so the join becomes a pure equi-join on (make, model, proc_speed).
# round(..., 1) is required: 3.0 + 0.1 == 3.1000000000000005 != 3.1 in floating point
laptops_2_df = laptops_df.withColumn(
    "proc_speed",
    F.explode(
        F.array(
            F.round(F.col("proc_speed") - 0.1, 1),
            F.col("proc_speed"),
            F.round(F.col("proc_speed") + 0.1, 1),
        )
    ),
)

joined_2_df = (
    laptops_2_df.join(laptops_offers_df, on=["make", "model", "proc_speed"])
    .groupBy("registration")
    .agg(F.avg("sale_price").alias("avg_price"))
)

joined_2_df.show()
joined_2_df.explain()


"""
== Physical Plan ==
*(6) HashAggregate(keys=[registration#0], functions=[avg(sale_price#11)])
+- Exchange hashpartitioning(registration#0, 200), ENSURE_REQUIREMENTS, [plan_id=154]
   +- *(5) HashAggregate(keys=[registration#0], functions=[partial_avg(sale_price#11)])
      +- *(5) Project [registration#0, sale_price#11]
         +- *(5) SortMergeJoin [make#1, model#2, knownfloatingpointnormalized(normalizenanandzero(proc_speed#33))], [make#8, model#9, knownfloatingpointnormalized(normalizenanandzero(proc_speed#10))], Inner
            :- *(2) Sort [make#1 ASC NULLS FIRST, model#2 ASC NULLS FIRST, knownfloatingpointnormalized(normalizenanandzero(proc_speed#33)) ASC NULLS FIRST], false, 0
            :  +- Exchange hashpartitioning(make#1, model#2, knownfloatingpointnormalized(normalizenanandzero(proc_speed#33)), 200), ENSURE_REQUIREMENTS, [plan_id=139]
            :     +- *(1) Filter isnotnull(proc_speed#33)
            :        +- *(1) Generate explode(array(round((proc_speed#3 - 0.1), 1), proc_speed#3, round((proc_speed#3 + 0.1), 1))), [registration#0, make#1, model#2], false, [proc_speed#33]
            :           +- *(1) Scan ExistingRDD[registration#0,make#1,model#2,proc_speed#3]
            +- *(4) Sort [make#8 ASC NULLS FIRST, model#9 ASC NULLS FIRST, knownfloatingpointnormalized(normalizenanandzero(proc_speed#10)) ASC NULLS FIRST], false, 0
               +- Exchange hashpartitioning(make#8, model#9, knownfloatingpointnormalized(normalizenanandzero(proc_speed#10)), 200), ENSURE_REQUIREMENTS, [plan_id=145]
                  +- *(3) Scan ExistingRDD[make#8,model#9,proc_speed#10,sale_price#11]
"""

# still skewed but we already better
# if we compare the 2 query plan, the only difference is the additional Generate
# query plan will not explain the difference

"""
To Remember

Non-uniform data distribution = data skews

Can cause massive performance problems
    - extremely long jobs
    - sometimes executor OOMs

Reason
    - prior to join, Spark shuffles data
    - same key will stay on the same executor
    - if one key is disproportionate, that executor will have a disproportionately large task
    - that executor takes longer than everyone else
    - the whole job waits for that task to finish

Solutions
    - include extra information in the join key (here: explode proc_speed into its
      neighbours -0.1 / same / +0.1 and join on make, model, proc_speed)
        -> the big key (Razer Blade) is split into many smaller keys, spread over more tasks
        -> the range condition becomes an equi-join: no more "compare everything, filter after"
        -> a join key does not have to be one column: it can be a set of columns
           (make, model, proc_speed); the more selective the set, the smaller each key group
"""

if __name__ == "__main__":
    import time

    time.sleep(10000)
