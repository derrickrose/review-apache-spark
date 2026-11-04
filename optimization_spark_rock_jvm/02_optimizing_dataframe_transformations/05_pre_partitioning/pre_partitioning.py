from pyspark.sql import SparkSession, DataFrame

spark = SparkSession.builder.appName("Column Pruning").master("local[2]").getOrCreate()

spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
spark.conf.set("spark.sql.adaptive.enabled", "false")

initial_table = spark.range(1, 10000000).repartition(10)  # Round robin partitioning
narrow_table = spark.range(1, 5000000).repartition(7)


# in order to join the two tables, spark has to repartition in the same partitioning scheme


def add_column(df: DataFrame, n: int) -> DataFrame:
    new_columns = list[str](
        map(lambda x: f"id * {x} as new_col_{x}", list[int](range(1, n + 1)))
    )
    new_df = df.selectExpr(*(["id"] + new_columns))
    return new_df


# scenario 1
wide_table = add_column(initial_table, 30)
join_1 = wide_table.join(narrow_table, "id")
join_1.explain()
"""
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [id#0L, new_col_1#8L, new_col_2#9L, new_col_3#10L, new_col_4#11L, new_col_5#12L, new_col_6#13L, new_col_7#14L, new_col_8#15L, new_col_9#16L, new_col_10#17L, new_col_11#18L, new_col_12#19L, new_col_13#20L, new_col_14#21L, new_col_15#22L, new_col_16#23L, new_col_17#24L, new_col_18#25L, new_col_19#26L, new_col_20#27L, new_col_21#28L, new_col_22#29L, new_col_23#30L, ... 7 more fields]
   +- SortMergeJoin [id#0L], [id#4L], Inner
      :- Sort [id#0L ASC NULLS FIRST], false, 0
      :  +- Exchange hashpartitioning(id#0L, 200), ENSURE_REQUIREMENTS, [plan_id=29]
      :     +- Project [id#0L, (id#0L * 1) AS new_col_1#8L, (id#0L * 2) AS new_col_2#9L, (id#0L * 3) AS new_col_3#10L, (id#0L * 4) AS new_col_4#11L, (id#0L * 5) AS new_col_5#12L, (id#0L * 6) AS new_col_6#13L, (id#0L * 7) AS new_col_7#14L, (id#0L * 8) AS new_col_8#15L, (id#0L * 9) AS new_col_9#16L, (id#0L * 10) AS new_col_10#17L, (id#0L * 11) AS new_col_11#18L, (id#0L * 12) AS new_col_12#19L, (id#0L * 13) AS new_col_13#20L, (id#0L * 14) AS new_col_14#21L, (id#0L * 15) AS new_col_15#22L, (id#0L * 16) AS new_col_16#23L, (id#0L * 17) AS new_col_17#24L, (id#0L * 18) AS new_col_18#25L, (id#0L * 19) AS new_col_19#26L, (id#0L * 20) AS new_col_20#27L, (id#0L * 21) AS new_col_21#28L, (id#0L * 22) AS new_col_22#29L, (id#0L * 23) AS new_col_23#30L, ... 7 more fields]
      :        +- Exchange RoundRobinPartitioning(10), REPARTITION_BY_NUM, [plan_id=21]
      :           +- Range (1, 10000000, step=1, splits=2)
      +- Sort [id#4L ASC NULLS FIRST], false, 0
         +- Exchange hashpartitioning(id#4L, 200), ENSURE_REQUIREMENTS, [plan_id=30]
            +- Exchange RoundRobinPartitioning(7), REPARTITION_BY_NUM, [plan_id=24]
               +- Range (1, 5000000, step=1, splits=2)

#############################  why ?                
repartition(10) / repartition(7) produce round-robin partitioning, which doesn’t match the join key. Catalyst
The join needs hash partitioning on id, so Spark adds a second shuffle (ENSURE_REQUIREMENTS). Tungsten
"""
join_1.count()

# scenario 2
alt_narrow_table = narrow_table.repartition(
    "id"
)  # Hashpartitioning scheme because of id
alt_initial_table = initial_table.repartition("id")
join_2 = alt_initial_table.join(alt_narrow_table, "id", "inner")
result_2 = add_column(join_2, 30)
result_2.explain()
"""
== Physical Plan ==
AdaptiveSparkPlan isFinalPlan=false
+- Project [id#0L, (id#0L * 1) AS new_col_1#141L, (id#0L * 2) AS new_col_2#142L, (id#0L * 3) AS new_col_3#143L, (id#0L * 4) AS new_col_4#144L, (id#0L * 5) AS new_col_5#145L, (id#0L * 6) AS new_col_6#146L, (id#0L * 7) AS new_col_7#147L, (id#0L * 8) AS new_col_8#148L, (id#0L * 9) AS new_col_9#149L, (id#0L * 10) AS new_col_10#150L, (id#0L * 11) AS new_col_11#151L, (id#0L * 12) AS new_col_12#152L, (id#0L * 13) AS new_col_13#153L, (id#0L * 14) AS new_col_14#154L, (id#0L * 15) AS new_col_15#155L, (id#0L * 16) AS new_col_16#156L, (id#0L * 17) AS new_col_17#157L, (id#0L * 18) AS new_col_18#158L, (id#0L * 19) AS new_col_19#159L, (id#0L * 20) AS new_col_20#160L, (id#0L * 21) AS new_col_21#161L, (id#0L * 22) AS new_col_22#162L, (id#0L * 23) AS new_col_23#163L, ... 7 more fields]
   +- SortMergeJoin [id#0L], [id#4L], Inner
      :- Sort [id#0L ASC NULLS FIRST], false, 0
      :  +- Exchange hashpartitioning(id#0L, 200), REPARTITION_BY_COL, [plan_id=317]
      :     +- Range (1, 10000000, step=1, splits=2)
      +- Sort [id#4L ASC NULLS FIRST], false, 0
         +- Exchange hashpartitioning(id#4L, 200), REPARTITION_BY_COL, [plan_id=319]
            +- Range (1, 5000000, step=1, splits=2)

########################## why ? 
repartition(10) followed by repartition("id"): CollapseRepartition keeps only the last one. Catalyst
##### =====>>>>> note that if an operation between repartitions, there is no colapse
repartition("id") gives hashpartitioning(id, 200), which already satisfies the join.
No extra exchange is added: 1 shuffle per side.
"""
result_2.count()

# scenario 3
enhanced_initial = add_column(initial_table, 30)
repartitioned_narrow = narrow_table.repartition("id")

# repartitioned_enhanced = enhanced_initial.repartition("id") # this is not necessary
# result_3 = repartitioned_enhanced.join(repartitioned_narrow, "id")

result_3 = enhanced_initial.join(repartitioned_narrow, "id")
result_3.explain()
## repartitioning late is what spark does at best naturally
## even not running the enhanced repartitioning, spark will perform hash repartitioning by join key since it is a requirement
"""
== Physical Plan ==
*(6) Project [id#0L, new_col_1#238L, new_col_2#239L, new_col_3#240L, new_col_4#241L, new_col_5#242L, new_col_6#243L, new_col_7#244L, new_col_8#245L, new_col_9#246L, new_col_10#247L, new_col_11#248L, new_col_12#249L, new_col_13#250L, new_col_14#251L, new_col_15#252L, new_col_16#253L, new_col_17#254L, new_col_18#255L, new_col_19#256L, new_col_20#257L, new_col_21#258L, new_col_22#259L, new_col_23#260L, ... 7 more fields]
+- *(6) SortMergeJoin [id#0L], [id#4L], Inner
   :- *(3) Sort [id#0L ASC NULLS FIRST], false, 0
   :  +- Exchange hashpartitioning(id#0L, 200), REPARTITION_BY_COL, [plan_id=334]
   :     +- *(2) Project [id#0L, (id#0L * 1) AS new_col_1#238L, (id#0L * 2) AS new_col_2#239L, (id#0L * 3) AS new_col_3#240L, (id#0L * 4) AS new_col_4#241L, (id#0L * 5) AS new_col_5#242L, (id#0L * 6) AS new_col_6#243L, (id#0L * 7) AS new_col_7#244L, (id#0L * 8) AS new_col_8#245L, (id#0L * 9) AS new_col_9#246L, (id#0L * 10) AS new_col_10#247L, (id#0L * 11) AS new_col_11#248L, (id#0L * 12) AS new_col_12#249L, (id#0L * 13) AS new_col_13#250L, (id#0L * 14) AS new_col_14#251L, (id#0L * 15) AS new_col_15#252L, (id#0L * 16) AS new_col_16#253L, (id#0L * 17) AS new_col_17#254L, (id#0L * 18) AS new_col_18#255L, (id#0L * 19) AS new_col_19#256L, (id#0L * 20) AS new_col_20#257L, (id#0L * 21) AS new_col_21#258L, (id#0L * 22) AS new_col_22#259L, (id#0L * 23) AS new_col_23#260L, ... 7 more fields]
   :        +- Exchange RoundRobinPartitioning(10), REPARTITION_BY_NUM, [plan_id=330]
   :           +- *(1) Range (1, 10000000, step=1, splits=2)
   +- *(5) Sort [id#4L ASC NULLS FIRST], false, 0
      +- Exchange hashpartitioning(id#4L, 200), REPARTITION_BY_COL, [plan_id=340]
         +- *(4) Range (1, 5000000, step=1, splits=2)
"""

result_3.count()

import time

time.sleep(10000)

# lesson : partition data early so spark do not have to do it
# make the joined DFs share the same partitioner, eg partition by the same column
# decorate the joined DF later (especially if you have lots of transformations)

# lesson: partitioning late is bad
# at best same perf as spark out of the box
# at worst worse perf than not partitioning at all
