# Optimizing Key-Value RDDs

Course source: [`scala/part5rddtransformations/`](../scala/part5rddtransformations/)

| # | Lesson | Duration | Notes | Source |
|---|--------|----------|-------|--------|
| 1 | RDD Transformations | 5:06 | [01_rdd_transformations_to_read.md](01_rdd_transformations_to_read.md) | (intro, no file) |
| 2 | By Key Functions | 23:10 | [02_by_key_functions_to_read.md](02_by_key_functions_to_read.md) | [`ByKeyFunctions.scala`](../scala/part5rddtransformations/ByKeyFunctions.scala) |
| 3 | Reusing JVM Objects, Part 1 | 24:57 | [03_reusing_jvm_objects_part_1_to_read.md](03_reusing_jvm_objects_part_1_to_read.md) | [`ReusingObjects.scala`](../scala/part5rddtransformations/ReusingObjects.scala) |
| 4 | Reusing JVM Objects, Part 2 | 12:11 | [04_reusing_jvm_objects_part_2_to_read.md](04_reusing_jvm_objects_part_2_to_read.md) | [`ReusingObjects.scala`](../scala/part5rddtransformations/ReusingObjects.scala) |
| 5 | Iterator-to-iterator Transformations | 21:19 | [05_iterator_to_iterator_transformations_to_read.md](05_iterator_to_iterator_transformations_to_read.md) | [`I2ITransformations.scala`](../scala/part5rddtransformations/I2ITransformations.scala) |
| 6 | Iterator-to-iterator Transformations - Exercises | 9:40 | [06_iterator_to_iterator_transformations_exercises_to_read.md](06_iterator_to_iterator_transformations_exercises_to_read.md) | [`I2ITransformations.scala`](../scala/part5rddtransformations/I2ITransformations.scala) |

## PySpark scripts

Run `python -m common.rdd_data_generator` once from `optimization_spark_rock_jvm/` first ([`common/rdd_data_generator.py`](../common/rdd_data_generator.py), writes `generated_data/`, git-ignored).
Each script prints timings, then keeps the Spark UI (http://localhost:4040) open; `KEEP_UI=0` to exit right away.

| Script | What it compares |
|---|---|
| [`02_by_key_functions.py`](02_by_key_functions.py) | groupByKey vs reduce/fold/aggregate/combineByKey |
| [`03_reusing_objects.py`](03_reusing_objects.py) | immutable dataclass vs mutable object vs flat list (parts 1 and 2) |
| [`05_i2i_transformations.py`](05_i2i_transformations.py) | sortBy + take vs iterator-to-iterator top 10 |
| [`06_i2i_transformations_exercises.py`](06_i2i_transformations_exercises.py) | the 2 flawed versions from the exercises |
