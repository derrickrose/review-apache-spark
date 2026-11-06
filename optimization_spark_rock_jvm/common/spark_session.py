"""Shared helpers for the PySpark RDD lessons (03_ and 04_)."""

import os
import time

from pyspark.sql import SparkSession

COURSE = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)  # optimization_spark_rock_jvm/


def get_spark(app_name: str, master: str = "local[*]") -> SparkSession:
    # The Python workers must be able to import `common` to unpickle objects from it
    # (e.g. the Laptop dataclass). sys.path changes on the driver don't reach them,
    # but in local mode the workers inherit the driver's environment -> PYTHONPATH.
    paths = os.environ.get("PYTHONPATH", "").split(os.pathsep)
    if COURSE not in paths:
        os.environ["PYTHONPATH"] = os.pathsep.join([COURSE, *filter(None, paths)])
    return SparkSession.builder.appName(app_name).master(master).getOrCreate()


def timed(label: str, fn):
    """Run fn(), print its duration, return its result."""
    start = time.perf_counter()
    result = fn()
    print(
        f"{label:<30} {time.perf_counter() - start:6.2f}s  -> {result if not isinstance(result, dict) else f'{len(result)} keys'}"
    )
    return result


def keep_ui_open():
    """Keep the Spark UI (http://localhost:4040) alive. Set KEEP_UI=0 to exit immediately."""
    if os.environ.get("KEEP_UI", "1") != "0":
        input("Spark UI on http://localhost:4040 - press Enter to stop...")
