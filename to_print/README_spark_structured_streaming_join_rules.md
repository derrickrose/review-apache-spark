# Spark Structured Streaming - Join Rules (Quick Reference)

## Default Rule

Default join type in Spark is **INNER JOIN**.

---

## 1. Static JOIN Static (Batch)

- All join types allowed: inner, left, right, full
- No watermark required
- No time condition required

---

## 2. Stream JOIN Static (or Static JOIN Stream)

- All join types allowed: inner, left, right, full
- No watermark required
- Commonly used for enrichment

Example:
```python
orders_stream.join(users_static, "user_id", "left")
```

---

## 3. Stream JOIN Stream - INNER JOIN

- Allowed without watermark
- No time condition required
- Output mode: append

Example:
```python
orders.join(status, "order_id", "inner")
```

---

## 4. Stream JOIN Stream - LEFT / RIGHT OUTER JOIN

Restricted. All conditions below are mandatory:

- Event-time column required
- Watermark required
- Time-bounded join condition required
- Output mode: append

Example:
```python
orders.withWatermark("order_time", "5 minutes") \
.join(
    status.withWatermark("status_time", "5 minutes"),
    orders.order_id = status.order_id AND
    status.status_time BETWEEN
        orders.order_time AND orders.order_time + interval 5 minutes,
    "leftOuter"
)
```

---

## 5. Stream JOIN Stream - FULL OUTER JOIN

- Not supported in Structured Streaming
- Reason: infinite state, no safe eviction

---

## 6. Quick Decision Table

| Join scenario                    | Allowed     | Watermark needed |
|---------------------------------|-------------|------------------|
| Static JOIN Static              | Yes         | No               |
| Stream JOIN Static              | Yes         | No               |
| Stream JOIN Stream (inner)      | Yes         | No               |
| Stream JOIN Stream (left/right) | Conditional | Yes              |
| Stream JOIN Stream (full)       | No          | -                |

---

## 7. One Rule to Remember

If Spark cannot prove that join state is bounded in time, the join is rejected.

---

## 8. Mental Shortcuts

- Inner join = easy
- Stream-Static join = safe
- Outer stream joins = time-bounded only
- No watermark = Spark refuses

---
