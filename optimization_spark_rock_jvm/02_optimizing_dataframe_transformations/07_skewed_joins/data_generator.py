import random
import string

from pyspark.sql.types import DoubleType, StringType, StructField, StructType

# --------------------------------------------------------------------------- #
# laptops (skewed joins lessons)
# --------------------------------------------------------------------------- #
LAPTOP_SCHEMA = StructType(
    [
        StructField("registration", StringType(), False),
        StructField("make", StringType(), False),
        StructField("model", StringType(), False),
        StructField("proc_speed", DoubleType(), False),
    ]
)

LAPTOP_MODEL_SCHEMA = StructType(
    [
        StructField("make", StringType(), False),
        StructField("model", StringType(), False),
    ]
)

LAPTOP_OFFER_SCHEMA = StructType(
    [
        StructField("make", StringType(), False),
        StructField("model", StringType(), False),
        StructField("proc_speed", DoubleType(), False),
        StructField("sale_price", DoubleType(), False),
    ]
)


LAPTOP_MODELS = [
    ("Razer", "Blade"),
    ("Alienware", "Area-51"),
    ("HP", "Omen"),
    ("Acer", "Predator"),
    ("Asus", "ROG"),
    ("Lenovo", "Legion"),
    ("MSI", "Raider"),
]


def random_laptop_model(uniform: bool = False):
    # 50% of the data is forced to the first model (Razer Blade) -> ~57% overall
    if not uniform and random.random() < 0.5:
        return LAPTOP_MODELS[0]
    return random.choice(LAPTOP_MODELS)


def random_proc_speed() -> float:
    return float(f"3.{random.randrange(9)}")  # 3.0 .. 3.8


def random_registration() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=7))


def random_price() -> float:
    return float(500 + random.randrange(1500))


def random_laptop(uniform: bool = False) -> tuple:
    make, model = random_laptop_model(uniform)
    return (random_registration(), make, model, random_proc_speed())


def random_laptop_offer(uniform: bool = False) -> tuple:
    make, model = random_laptop_model(uniform)
    return (make, model, random_proc_speed(), random_price())
