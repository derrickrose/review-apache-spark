"""
array_contains in Spark
=======================

ONE IDEA:
    array_contains(array_column, value)
    -> "Is `value` inside this array?"  (asked for every row)

That's it. The rest of this file is examples and exercises.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.master("local[*]").appName("array_contains").getOrCreate()
spark.sparkContext.setLogLevel("WARN")


# =============================================================================
# PART 1 — THE SIMPLEST EXAMPLE
# =============================================================================
# A basket of fruits per person.

df = spark.createDataFrame(
    [
        ("Alice", ["apple", "banana"]),
        ("Bob", ["orange"]),
    ],
    ["name", "fruits"],
)

df.select(
    "name",
    "fruits",
    F.array_contains("fruits", "apple").alias("has_apple"),
).show()

# +-----+---------------+---------+
# | name|         fruits|has_apple|
# +-----+---------------+---------+
# |Alice|[apple, banana]|     true|
# |  Bob|       [orange]|    false|
# +-----+---------------+---------+


# =============================================================================
# PART 2 — ALL POSSIBLE RESULTS (only 3: true, false, null)
# =============================================================================
#
#   Case | array               | search "apple" | result
#   -----+---------------------+----------------+--------
#    A   | [apple, banana]     | found          | true
#    B   | [orange]            | not found      | false
#    C   | []   (empty)        | not found      | false
#    D   | null (no array)     | -              | null
#    E   | [orange, null]      | not found      | null   <- surprise!
#    F   | [apple, null]       | found          | true
#
#   Rule to remember:
#     - found                        -> true  (even if the array has nulls)
#     - not found, no null inside    -> false
#     - array is null                -> null
#     - not found, null inside       -> null  ("maybe the null was an apple?")
#
#   And the searched value? (official doc: "Returns null if the array or value is null")
#     - value from a column that is null on a row -> null
#     - literal None: array_contains(col, None)   -> ERROR (DATATYPE_MISMATCH.NULL_TYPE)

all_cases = spark.createDataFrame(
    [
        ("A", ["apple", "banana"]),
        ("B", ["orange"]),
        ("C", []),
        ("D", None),
        ("E", ["orange", None]),
        ("F", ["apple", None]),
    ],
    "case string, fruits array<string>",
)

all_cases.select(
    "case",
    "fruits",
    F.array_contains("fruits", "apple").alias("has_apple"),
).show()


# =============================================================================
# PART 3 — THE 3 EVERYDAY USES
# =============================================================================

# 3.1 Create a column (seen above)

# 3.2 Filter rows: keeps only `true` (false AND null are dropped)
print("Rows WITH apple:")
all_cases.filter(F.array_contains("fruits", "apple")).show()  # A, F

# Watch out with NOT: NOT(null) = null -> D and E are dropped too!
print("Rows WITHOUT apple (naive):")
all_cases.filter(~F.array_contains("fruits", "apple")).show()  # B, C only

print("Rows WITHOUT apple (null-safe):")
all_cases.filter(
    ~F.coalesce(F.array_contains("fruits", "apple"), F.lit(False))
).show()  # B, C, D, E

# 3.3 SQL — same function
all_cases.createOrReplaceTempView("baskets")
spark.sql("SELECT case FROM baskets WHERE array_contains(fruits, 'apple')").show()


# =============================================================================
# PART 4 — EXERCISES  (try first, solutions at the bottom)
# =============================================================================

students = spark.createDataFrame(
    [
        ("Tom", ["math", "physics"], [12, 15]),
        ("Lina", ["history", "math"], [18, 20]),
        ("Sam", ["art"], [9]),
        ("Nora", [], []),
        ("Max", None, None),
        ("Zoe", ["Math", None], [20, None]),
    ],
    "name string, courses array<string>, grades array<int>",
)
students.show(truncate=False)

# EX 1: Add a column `takes_math` (true/false/null). Predict each row first!
# EX 2: Keep only students who take "math".
# EX 3: Keep students who got a 20 (grades is an int array).
# EX 4: Keep students who take "math" AND "physics".
# EX 5: Keep students who do NOT take "math" — including Max (null array).
# EX 6: Zoe writes "Math" with a capital M. Make the "math" check case-insensitive.
# EX 7: Same as EX 2 but in Spark SQL.


# =============================================================================
# SOLUTIONS
# =============================================================================
print("=" * 30, "SOLUTIONS", "=" * 30)

# EX 1  Tom true | Lina true | Sam false | Nora false | Max null | Zoe null
students.select("name", F.array_contains("courses", "math").alias("takes_math")).show()

# EX 2  -> Tom, Lina
students.filter(F.array_contains("courses", "math")).show()

# EX 3  -> Lina, Zoe
students.filter(F.array_contains("grades", 20)).show()

# EX 4  -> Tom
students.filter(
    F.array_contains("courses", "math") & F.array_contains("courses", "physics")
).show()

# EX 5  -> Sam, Nora, Max, Zoe
students.filter(~F.coalesce(F.array_contains("courses", "math"), F.lit(False))).show()

# EX 6  -> Tom, Lina, Zoe   (lowercase every element first; needs Spark 3.1+)
students.filter(F.array_contains(F.transform("courses", F.lower), "math")).show()

# EX 7
students.createOrReplaceTempView("students")
spark.sql("SELECT * FROM students WHERE array_contains(courses, 'math')").show()


# =============================================================================
# PART 5 — MORE EXERCISES (fill the TODOs, then run and compare)
# =============================================================================
# Each exercise: write your answer in place of `None`, then check the expected
# rows written in the comment. Solutions are in PART 6.

orders = spark.createDataFrame(
    [
        (1, "Ana", ["laptop", "mouse"], ["promo", "express"]),
        (2, "Ben", ["phone"], ["express"]),
        (3, "Cleo", ["mouse", "keyboard"], []),
        (4, "Dan", [], None),
        (5, "Eli", ["laptop", None], ["promo"]),
        (6, "Fay", None, ["gift"]),
    ],
    "id int, customer string, items array<string>, tags array<string>",
)
orders.show(truncate=False)

# --- QUIZ: predict the result WITHOUT running (true / false / null) ---------
# Q1  array_contains(["a", "b"], "a")          -> ?
# Q2  array_contains(["a", "b"], "c")          -> ?
# Q3  array_contains([], "a")                  -> ?
# Q4  array_contains(null, "a")                -> ?
# Q5  array_contains(["b", null], "a")         -> ?
# Q6  array_contains(["a", null], "a")         -> ?
# Q7  array_contains(["A"], "a")               -> ?
# Q8  array_contains([1, 2, 3], 2)             -> ?

# EX 8: Add column `has_laptop`. Expected: 1 true, 2 false, 3 false, 4 false, 5 true, 6 null
ex8 = None  # TODO

# EX 9: Keep orders that contain a "mouse". Expected ids: 1, 3
ex9 = None  # TODO

# EX 10: Keep orders tagged "express" but NOT "promo". Expected ids: 2
ex10 = None  # TODO

# EX 11: Add column `status`:
#        "unknown"  if items is null
#        "laptop"   if items contains "laptop"
#        "other"    otherwise
#        Expected: 1 laptop, 2 other, 3 other, 4 other, 5 laptop, 6 unknown
ex11 = None  # TODO

# EX 12: Count how many orders contain "laptop". Expected: 2
ex12 = None  # TODO

# EX 13: Keep orders with no "laptop" — null rows included. Expected ids: 2, 3, 4, 6
ex13 = None  # TODO

# EX 14: Write EX 9 in SQL. Expected ids: 1, 3
ex14 = None  # TODO


# =============================================================================
# PART 6 — SOLUTIONS FOR PART 5
# =============================================================================
print("=" * 30, "SOLUTIONS PART 5", "=" * 30)

# QUIZ: Q1 true | Q2 false | Q3 false | Q4 null | Q5 null | Q6 true
#       Q7 false (case-sensitive) | Q8 true
spark.sql("""
    SELECT
        array_contains(array('a','b'), 'a')                 AS q1,
        array_contains(array('a','b'), 'c')                 AS q2,
        array_contains(cast(array() AS array<string>), 'a') AS q3,
        array_contains(cast(null AS array<string>), 'a')    AS q4,
        array_contains(array('b', null), 'a')               AS q5,
        array_contains(array('a', null), 'a')               AS q6,
        array_contains(array('A'), 'a')                     AS q7,
        array_contains(array(1, 2, 3), 2)                   AS q8
""").show()

# EX 8
orders.select("id", F.array_contains("items", "laptop").alias("has_laptop")).show()

# EX 9
orders.filter(F.array_contains("items", "mouse")).show()

# EX 10  (Ben: tags=[express] -> promo false -> kept)
orders.filter(
    F.array_contains("tags", "express") & ~F.array_contains("tags", "promo")
).show()

# EX 11  (test null FIRST, otherwise null falls into "other")
orders.select(
    "id",
    F.when(F.col("items").isNull(), "unknown")
    .when(F.array_contains("items", "laptop"), "laptop")
    .otherwise("other")
    .alias("status"),
).show()

# EX 12
print("laptop orders:", orders.filter(F.array_contains("items", "laptop")).count())

# EX 13
orders.filter(~F.coalesce(F.array_contains("items", "laptop"), F.lit(False))).show()

# EX 14
orders.createOrReplaceTempView("orders")
spark.sql("SELECT * FROM orders WHERE array_contains(items, 'mouse')").show()

spark.stop()


# =============================================================================
# CONCLUSION — what to remember (with the lines where each point is shown)
# =============================================================================
#
# 1. What it does                                         -> lines 20-44
#    array_contains(array_col, value) asks, row by row:
#    "is `value` inside this array?"
#
# 2. Only 3 possible results: true / false / null         -> lines 47-86
#    - found                         -> true   (even with nulls inside)
#    - not found, no null inside     -> false  (empty array too)
#    - array is null                 -> null
#    - not found, but null inside    -> null
#    - searched value null (column)  -> null
#    - literal None as value         -> ERROR
#    Rule summary                                         -> lines 59-67
#
# 3. filter() keeps only `true` (false and null dropped)  -> line 96
#
# 4. NOT trap: ~array_contains drops null rows too        -> line 99
#    Fix: ~coalesce(array_contains(...), lit(False))      -> line 102
#    Practiced in                                         -> EX 5 (line 157), EX 13 (line 269)
#
# 5. Works with any type (strings, ints, ...)             -> EX 3 (line 149), Q8 (line 199)
#
# 6. Case-sensitive: "Math" != "math"                     -> Q7 (line 198)
#    Fix: array_contains(transform(col, lower), "math")   -> EX 6 (line 162)
#
# 7. Combine with & (AND), | (OR), ~ (NOT)                -> EX 4 (line 152), EX 10 (line 252)
#
# 8. With when/otherwise: test isNull() FIRST,
#    otherwise null arrays fall into "otherwise"          -> EX 11 (line 257)
#
# 9. Same function in SQL                                 -> line 109, EX 7 (line 167), EX 14 (line 274)
#
# 10. To search for the value stored in ANOTHER column, wrap it with F.col():
#     array_contains("items", F.col("wanted"))  -> compares with the column
#     array_contains("items", "wanted")         -> searches the TEXT "wanted"!
#
# Source: official docs (checked against Spark 3.5.0 run + latest docs)
#   https://spark.apache.org/docs/latest/api/sql/array-functions/#array_contains
#   https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.array_contains.html
#
# One sentence: array_contains = "is X in the list?" -> true / false / null,
# and always think about the null case when you negate or classify.
