# Spark Optimization — Pluralsight Curriculum

**Provider:** Pluralsight  
**Title:** Spark Optimization  
**Duration:** 3 Days  
**Format:** Workshop  
**Languages:** Python / Scala  
**Focus:** Advanced Spark performance tuning and best practices  

---

## 📘 Course Overview
Learn techniques to optimize Spark Core and Spark SQL performance.  
Covers Spark architecture, execution, data formats, partitions, caching, joins, and SQL optimization.  

🔗 [Course link](https://www.pluralsight.com/professional-services/data-machine-learning/spark-optimization)

---

## 🧠 What You’ll Learn

### Spark Overview
- Logical Architecture  
- Physical Architecture of Spark  
- Common Concepts and Terms in Spark  
- Ways to Build Applications on Spark  
- Spark with Hadoop  

---

### Understanding Spark Execution Environment – YARN
- About YARN  
- Why YARN  
- Architecture of YARN  
- YARN UI and Commands  
- Internals of YARN  
- Experience Execution of Spark Application on YARN  
- Troubleshooting and Debugging Spark Applications on YARN  
- Optimizing Application Performance  

---

### Working with the Right Data Format
- Why Data Formats Are Important for Optimization  
- Key Data Formats  
- Comparisons – Which One to Choose When?  
- Working with Avro  
- Working with Parquet  
- Working with ORC  

---

### Dealing with Spark Partitions
- How Spark Determines Number of Partitions  
- Things to Keep in Mind While Determining Partition Count  
- Small Partitions Problem  
- Diagnosing & Handling Post-Filtering Issues (Skewness)  
- Repartition vs Coalesce  

---

### Spark Physical Execution
- Spark Core Plan  
- Modes of Execution (Standalone, YARN Client, YARN Cluster)  
- Physical Execution on Cluster  
- Narrow vs Wide Dependencies  
- Spark UI  
- Executor Memory Architecture  
- Key Properties  

---

### Effective Development Using Spark Core API
- Use of `groupByKey` and `reduceByKey`  
- Using the Right Datatype in RDD  
- How to Ensure Memory is Utilized Effectively  
- Performing Data Validation in an Optimal Manner  
- Use of `mapPartitions`  
- Partitioning Strategies: Hash Partitioner, Range Partitioner  
- Writing and Plugging a Custom Partitioner  

---

### Caching and Checkpointing
- When to Cache  
- How Caching Helps  
- Caching Strategies  
- How Spark Plans Change When Caching Is On  
- Caching in Spark UI  
- Role of Alluxio  
- Checkpointing  
- How Caching Differs from Checkpointing  

---

### Joins
- Why Optimizing Joins Is Important  
- Types of Joins  
- Quick Recap of MapReduce Map-Side Joins  
- Broadcasting  
- Bucketing  

---

### Spark SQL Optimization
- DataFrames vs Datasets  
- About Tungsten  
- Data Partitioning  
- Query Optimizer: Catalyst Optimizer  
- Debugging Spark Queries  
- `EXPLAIN` Plan  
- Partitioning & Bucketing in Spark SQL  
- Best Practices for Writing Spark SQL Code  
- Spark SQL with Binary Data Formats  

---

## 🎯 Productivity Objectives
- Integrate Aspects of Spark on YARN  
- Work with Binary Data Formats  
- Identify Internals of Spark  
- Optimize Spark Core and Spark SQL Code  
- Apply Best Practices When Writing Spark Core and Spark SQL Code  

---

## 🧾 Notes
This 3-day workshop provides in-depth exploration of Spark execution internals and performance tuning.  
Ensure you have a local or cloud Spark environment for hands-on exercises.