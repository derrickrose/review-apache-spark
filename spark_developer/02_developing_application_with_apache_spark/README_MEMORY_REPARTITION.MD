# 🧠 Spark Memory Repartition — Full Analysis (with Formulas, Off-Heap, and OS Overhead per Environment)

This document provides a full breakdown of **PySpark driver memory allocation (5.5 GB JVM heap)** — including managed vs
unmanaged memory, off‑heap usage, and OS overhead across different deployment platforms (Linux VM, Docker, Kubernetes,
YARN, Kerberos).

---

## ⚙️ PySpark Configuration

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
        .appName("spark_memory_analysis")
        .config("spark.driver.memory", "5632m")           # 5.5 GB JVM heap
        .config("spark.memory.fraction", "0.8")           # 80% of usable heap managed by Spark
        .config("spark.memory.storageFraction", "0.8")    # 80% of unified memory for caching
        .config("spark.memory.offHeap.enabled", "true")   # enable off-heap Tungsten memory
        .config("spark.memory.offHeap.size", "512m")      # 512 MB off-heap pool
        .getOrCreate()
)
```

---

## 🧮 Step-by-Step Memory Computation Formulas

| # | Formula                                                                            | Description                                  | Managed by Spark | Result (MB) |
|---|------------------------------------------------------------------------------------|----------------------------------------------|------------------|-------------|
| ① | `reservedMemory = max(300, 0.1 × 5632)`                                            | Fixed JVM overhead (GC, threads, JIT)        | ❌ No             | **563.2**   |
| ② | `usableHeap = 5632 − reservedMemory`                                               | Memory available for Spark                   | ✅ Yes            | **5068.8**  |
| ③ | `sparkManagedMemory = usableHeap × 0.8`                                            | Spark-managed unified memory                 | ✅ Yes            | **4055.0**  |
| ④ | `userMemory = usableHeap × (1 − 0.8)`                                              | Memory for Catalyst, scheduler, UDFs         | ✅ Yes            | **1013.8**  |
| ⑤ | `storageMemory = sparkManagedMemory × 0.8`                                         | Cached DataFrames / RDDs                     | ✅ Yes            | **3244.0**  |
| ⑥ | `executionMemory = sparkManagedMemory − storageMemory`                             | Joins, sorts, shuffle, aggregations          | ✅ Yes            | **811.0**   |
| ⑦ | `offHeapMemory = 512`                                                              | Native Tungsten memory (outside JVM)         | ✅ Yes            | **512.0**   |
| ⑧ | `totalProcessMemory = spark.driver.memory + offHeapMemory + OS_overhead(platform)` | Full process usage including system overhead | ❌ Partially      | **≈7.1 GB** |

---

## 🧩 ⑧ Detailed OS Overhead per Environment

| Platform                  | Typical Overhead     | Causes                                                       | Notes                                            |
|---------------------------|----------------------|--------------------------------------------------------------|--------------------------------------------------|
| **Linux VM (bare metal)** | 10–15 % of total RAM | Kernel daemons, filesystem cache, JVM native libs            | Lightest overhead                                |
| **Docker container**      | 15–20 %              | Docker engine, overlayFS layers, container runtime isolation | Slightly higher due to cgroups                   |
| **Kubernetes pod**        | 20–25 %              | Kubelet, CRI‑O/Containerd overhead, network & metrics agents | Common in production clusters                    |
| **YARN cluster**          | 18–22 %              | NodeManager, shuffle service, application master, monitoring | Each executor runs inside YARN-managed container |
| **Kerberos-secured**      | +2–5 %               | Authentication cache, keytabs, encryption buffers            | Adds security layer on top                       |

### 🔢 Extended Formula

```text
totalProcessMemory ≈ spark.driver.memory + offHeapMemory + (platformOverhead% × hostRAM)
```

### 💡 Example Calculations (5.5 GB JVM + 512 MB Off‑Heap)

| Platform              | OS Overhead              | Total Memory Footprint         |
|-----------------------|--------------------------|--------------------------------|
| Linux VM              | 10% → 0.55 GB            | 5.5 + 0.5 + 0.55 = **6.55 GB** |
| Docker                | 15% → 0.83 GB            | 5.5 + 0.5 + 0.83 = **6.83 GB** |
| Kubernetes            | 20% → 1.1 GB             | 5.5 + 0.5 + 1.1 = **7.1 GB**   |
| YARN                  | 22% → 1.21 GB            | 5.5 + 0.5 + 1.21 = **7.21 GB** |
| Kerberos + Kubernetes | 25% + 3% = 28% → 1.54 GB | 5.5 + 0.5 + 1.54 = **7.54 GB** |

---

## 🧱 Memory Design — JVM Heap + Off-Heap + OS Layout

```text
+=================================================================================================================+
| SYSTEM MEMORY — Total physical RAM on host machine                                                              |
|                                                                                                                 |
|  +-----------------------------------------------------------------------------------------------------------+  |
|  | ① OS & SYSTEM SERVICES — ~10–25% (varies by environment)                                                 |  |
|  | • Linux kernel, daemons, filesystem cache                                                                 |  |
|  | • Kubernetes/YARN resource management, cgroups isolation                                                  |  |
|  | • Kerberos authentication cache, SSL buffers                                                              |  |
|  | ➜ This memory is NOT visible to Spark or the JVM heap.                                                    |  |
|  +-----------------------------------------------------------------------------------------------------------+  |
|                                                                                                                 |
|  +-----------------------------------------------------------------------------------------------------------+  |
|  | ② JVM HEAP — 100 % → 5632 MB (5.5 GB total allocated to Spark Driver)                                    |  |
|  |                                                                                                           |  |
|  |  +----------------------------------------------------------------------------------------------------+   |  |
|  |  | ②-A RESERVED MEMORY — max(300 MB, 0.10 × 5632 MB) = 563.2 MB                                       |   |  |
|  |  | • JVM internals: GC, threads, JIT compiler, Netty buffers                                            |   |  |
|  |  | • Spark UI logs, heartbeat, deserialization buffers                                                  |   |  |
|  |  +----------------------------------------------------------------------------------------------------+   |  |
|  |                                                                                                           |  |
|  |  +----------------------------------------------------------------------------------------------------+   |  |
|  |  | ②-B SPARK MANAGED MEMORY — usableHeap × 0.8 = 4055 MB                                               |   |  |
|  |  |   +----------------------------------------------+----------------------------------------------+    |   |  |
|  |  |   | STORAGE MEMORY = 4055 × 0.8 = 3244 MB         | EXECUTION MEMORY = 4055 × 0.2 = 811 MB       |    |   |  |
|  |  |   |  • Cached RDDs / DataFrames                   |  • Shuffle, join, sort, aggregate buffers    |    |   |  |
|  |  |   |  • BlockManager cached blocks                 |  • Tungsten task execution memory           |    |   |  |
|  |  |   |  • Broadcast variables, serialized data       |  • Temporary spill data                     |    |   |  |
|  |  |   +----------------------------------------------+----------------------------------------------+    |   |  |
|  |  |                                                                                                  |   |  |
|  |  | ②-C USER MEMORY = usableHeap × (1 − 0.8) = 1013.8 MB                                             |   |  |
|  |  |  • Catalyst optimizer, DAGScheduler, accumulators                                                |   |  |
|  |  |  • UDF execution, logical plan parsing, listener bus                                             |   |  |
|  |  +----------------------------------------------------------------------------------------------------+   |  |
|  +-----------------------------------------------------------------------------------------------------------+  |
|                                                                                                                 |
|  +-----------------------------------------------------------------------------------------------------------+  |
|  | ③ OFF-HEAP MEMORY — spark.memory.offHeap.size = 512 MB                                                  |  |
|  | • Native Tungsten / Unsafe memory region (outside JVM)                                                  |  |
|  | • Used for: columnar caching, vectorized I/O, joins, Arrow buffers, UDF native conversions              |  |
|  | • Managed by Spark, bypasses JVM GC                                                                    |  |
|  +-----------------------------------------------------------------------------------------------------------+  |
+=================================================================================================================+
```

---

## ⚠️ When Spark Spills to Disk

Spark only writes to disk when:

1. **Execution Memory** exceeds 811 MB → shuffle spill files created.
2. **Storage Memory** exceeds 3244 MB → cached partitions spilled (if MEMORY_AND_DISK).
3. **Off‑Heap region** (512 MB) full → Tungsten spills to disk.
4. **Broadcast join** size exceeds threshold.
5. **UDFs** or **Python serialization buffers** overflow JVM allocation.

✅ In this workload:

- No shuffle or join → no execution spill
- 2.1 GB cached < 3.2 GB → fits in Storage Memory
- Off‑heap idle → no spill
- UDFs lightweight → stay in heap

**Result:** All cached data remains in‑memory (on‑heap).

---

## ✅ Effective Breakdown (5.5 GB JVM, 512 MB Off‑Heap)

| Region             | Memory                                         | Managed by Spark | Purpose                                  |
|--------------------|------------------------------------------------|------------------|------------------------------------------|
| OS / Container     | ~1.0–1.5 GB                                    | ❌ No             | Linux, Kubernetes, Docker, YARN daemons  |
| Reserved (JVM)     | 563 MB                                         | ❌ No             | GC, threads, JIT, event logs             |
| Spark‑managed heap | 5.07 GB                                        | ✅ Yes            | Unified + User Memory                    |
| ‣ Unified Memory   | 4.05 GB                                        | ✅ Yes            | Shared between storage & execution       |
| ‣ Storage pool     | 3.24 GB                                        | ✅ Yes            | Cached RDDs, DataFrames                  |
| ‣ Execution pool   | 0.81 GB                                        | ✅ Yes            | Shuffle, join, sort, aggregate           |
| User Memory        | 1.01 GB                                        | ✅ Yes            | Query planning, UDFs, Catalyst optimizer |
| Off‑Heap           | 0.5 GB                                         | ✅ Yes            | Tungsten, Arrow, vectorized execution    |
| **Total**          | **≈7.1 GB (≈7.5 GB on Kubernetes + Kerberos)** | —                | Full process memory footprint            |