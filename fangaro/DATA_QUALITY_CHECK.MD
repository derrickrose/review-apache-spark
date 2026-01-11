# Modern Data Quality Checks

## 1. Null or Missing Value Checks
Ensure no essential field (like customer_id, transaction_id) contains missing data

## 2. Primary Key Uniqueness Validation
Verify that key columns (like IDs) remain unique to prevent duplicate business entities or revenue double counting.

## 3. Duplicate Record Detection
Detect duplicates across ingestion stages

## 4. Referential Integrity Validation
Confirm that all foreign key relationships hold true

## 5. Data Type Validation
Ensure incoming data matches schema definitions — no strings in numeric fields, no invalid dates.

## 6. Numeric Range Validation
Catch impossible values (e.g., negative ages, >100% percentages, invalid ratings).

## 7. String Length & Pattern Checks
Enforce length constraints and validate formats (emails, phone numbers, IDs) with regex rules.

## 8. Allowed Value / Domain Validation
Ensure categorical columns only contain valid entries — e.g., gender ∈ {‘M’, ‘F’, ‘Other’}.

## 9. Business Rule Consistency
Check rules like order_amount = item_price * quantity or revenue = sum(product_sales).

## 10. Cross-Column Consistency
Validate logical dependencies — e.g., delivery_date ≥ order_date.

## 11. Timeliness / Freshness Checks
Detect data delays and SLA breaches — especially important for near real-time systems.

## 12. Completeness Check
Verify all partitions, expected files, or dates are present — no missing data slices.

## 13. Volume Check Against Historical Data
Compare record counts or data sizes vs previous runs to detect anomalies in ingestion.

## 14. Statistical Distribution Checks
Validate stability of metrics like mean, median, and standard deviation to catch silent drifts.

## 15. Outlier Detection
Identify records that deviate significantly from normal ranges

## 16. Schema Drift Detection
Automatically detect added, removed, or renamed columns — common in dynamic source systems.

## 17. Duplicate File Ingestion Check
Prevent reprocessing of already-loaded files or data across multiple sources.

## 18. Negative / Invalid Value Checks
Block impossible values like negative prices or zero quantities where not allowed.

## 19. Percentage / Total Consistency Check
Ensure calculated percentages correctly sum to 100% or totals match constituent values.

## 20. Hierarchy Validation
Validate hierarchical consistency.

## 21. Audit Column Consistency
Confirm audit columns like created_by, updated_at, and load_date are properly populated.