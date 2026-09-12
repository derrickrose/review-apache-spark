# data generator — plain python, no spark
# 5 makes: the first is picked 50% of the time, the other 4 share the remaining
# 50% (12.5% each). models are picked uniformly from a much longer list.

import random
import string

# the first make is the hot key
MAKES = ["Fender", "Gibson", "Ibanez", "ESP", "PRS"]
HOT_MAKE_WEIGHT = 0.5

MODELS = [
    "Stratocaster",
    "Telecaster",
    "Jazzmaster",
    "Jaguar",
    "Mustang",
    "LesPaul",
    "SG",
    "ES335",
    "Explorer",
    "Firebird",
    "Flying V",
    "RG",
    "S",
    "Iceman",
    "Artcore",
    "Horizon",
    "Eclipse",
    "Custom24",
    "SE",
    "McCarty",
]

SOUND_SCORES = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]


def random_string(n=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def random_make():
    """MAKES[0] at 50%, the other four at 12.5% each"""
    if random.random() < HOT_MAKE_WEIGHT:
        return MAKES[0]
    return random.choice(MAKES[1:])


def random_guitar():
    """(configurationId, make, model, soundScore)"""
    return (
        random_string(),
        random_make(),
        random.choice(MODELS),
        random.choice(SOUND_SCORES),
    )


def random_guitar_sale():
    """(registration, make, model, soundScore, salePrice)"""
    return (
        random_string(),
        random_make(),
        random.choice(MODELS),
        random.choice(SOUND_SCORES),
        random.random() * 5000,
    )


def make_guitars(n, seed=None):
    if seed is not None:
        random.seed(seed)
    return [random_guitar() for _ in range(n)]


def make_guitar_sales(n, seed=None):
    if seed is not None:
        random.seed(seed)
    return [random_guitar_sale() for _ in range(n)]


if __name__ == "__main__":
    from collections import Counter

    sales = make_guitar_sales(100_000, seed=42)

    print(f"{len(sales)} sales rows")
    counts = Counter(make for _, make, _, _, _ in sales)
    for make, count in counts.most_common():
        print(f"  {make:10s} {count:7d}  {count / len(sales) * 100:5.2f}%")

    keys = Counter((make, model) for _, make, model, _, _ in sales)
    print(f"{len(keys)} distinct (make, model) keys, top 5:")
    for key, count in keys.most_common(5):
        print(f"  {key} {count}")
