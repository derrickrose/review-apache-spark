from datetime import datetime


date1 = datetime.now()
print(date1)
print(type(date1))
print(date1.year)
executor_memory_gb = 16
safe_broadcast_mb = executor_memory_gb * 1024 * 0.1  # 10%
# spark.conf.set("spark.sql.autoBroadcastJoinThreshold", int(safe_broadcast_mb * 1024 * 1024))
