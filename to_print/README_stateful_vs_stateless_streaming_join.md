# Stateless vs Stateful Processing in This Spark Structured Streaming Pipeline

This README explains whether the provided Spark Structured Streaming pipeline is **stateless or stateful**, and why.

The conclusion is precise and Spark-accurate.

---

## Short Answer

**The pipeline is stateful.**

Even though there is:
- No `groupBy`
- No `agg`
- No `window`

the pipeline is still **stateful because it contains a stream–stream join**.

---

## Step-by-Step Classification

### 1. Order Stream

```python
order_stream_df = spark.readStream ...
```

- Streaming source only
- No aggregation
- No join

**Stateless**

---

### 2. Status Stream

```python
status_stream_df = spark.readStream ...
```

- Streaming source only
- No aggregation
- No join

**Stateless**

---

### 3. User DataFrame (Static)

```python
user_df = spark.read.json(...)
```

- Static (batch) DataFrame
- No streaming semantics
- No buffering required

**Stateless**

---

### 4. Stream–Stream Join (Critical Part)

```python
order_stream_df.join(status_stream_df, "order_id", "inner")
```

This is a **stream–stream INNER JOIN**.

In Spark Structured Streaming:

> Any stream–stream join is a **stateful operation**.

Why?
- Spark must buffer rows from both streams
- It waits until matching rows arrive
- That buffering is internal **state**

Even without windowing or aggregation, Spark maintains state.

**Stateful**

---

### 5. Stream–Static Join

```python
.join(user_df, "user_id")
```

- Stream joined with static data
- No buffering
- No waiting for future data

**Stateless**

---

## Final Classification

| Pipeline Part            | Stateless | Stateful |
|--------------------------|-----------|----------|
| Stream sources           | Yes       | No       |
| Stream–Stream INNER join | No        | Yes      |
| Stream–Static join       | Yes       | No       |
| Entire pipeline          | No        | Yes      |

---

## Why No Watermark Is Required Here

The join type is **INNER**.

INNER JOIN semantics:
- Rows are emitted only when both sides exist
- Spark can safely drop unmatched rows
- State remains bounded

Therefore:
- No watermark is required
- Output mode `append` is valid
- The query is still stateful internally

---

## Key Rule to Remember

> **Stateful does not mean aggregation only.**
>
> Joins, especially stream–stream joins, are also stateful operations.

---

## One-Line Verdict

**This pipeline is stateful because it contains a stream–stream join, even though it does not use aggregation or windowing.**

---

End of document.
