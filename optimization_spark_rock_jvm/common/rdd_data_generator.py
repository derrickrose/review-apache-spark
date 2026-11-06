"""
Python port of scala/generator/DataGenerator.scala + LaptopsDomain.scala.

Shared by the PySpark lessons in:
  - 03_optimizing_rdd_transformations_mostly_joins/
  - 04_optimizing_key_value_rdds/

Files are written to optimization_spark_rock_jvm/generated_data/ (ignored by git).
Plain Python, no Spark.

Two Scala quirks are fixed here on purpose (see the *_to_read.md notes):
  - generate_exam_data writes to the folder the lessons read (not "studentgen")
  - the `limit` of generate_metrics and `uniform` of random_laptop* are honored
"""

import random
import string
from dataclasses import dataclass
from pathlib import Path

COURSE = Path(__file__).resolve().parents[1]  # optimization_spark_rock_jvm/
REPO = COURSE.parent
DATA = REPO / "data"
GENERATED = COURSE / "generated_data"  # not in repo data/: that folder is root-owned
WORDS_FILE = DATA / "lipsum" / "words.txt"


# --------------------------------------------------------------------------- #
# general helpers (same semantics as the Scala ones)
# --------------------------------------------------------------------------- #
def random_string(n: int) -> str:
    # Scala: (0 to n) -> n + 1 lowercase letters
    return "".join(random.choices(string.ascii_lowercase, k=n + 1))


def random_long() -> int:
    return random.randrange(0, 2**63 - 1)


# --------------------------------------------------------------------------- #
# laptops (skewed joins lessons)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Laptop:
    registration: str
    make: str
    model: str
    proc_speed: float


@dataclass(frozen=True)
class LaptopOffer:
    make: str
    model: str
    proc_speed: float
    sale_price: float


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


def random_price() -> int:
    return 500 + random.randrange(1500)


def random_laptop(uniform: bool = False) -> Laptop:
    make, model = random_laptop_model(uniform)
    return Laptop(random_registration(), make, model, random_proc_speed())


def random_laptop_offer(uniform: bool = False) -> LaptopOffer:
    make, model = random_laptop_model(uniform)
    return LaptopOffer(make, model, random_proc_speed(), random_price())


# --------------------------------------------------------------------------- #
# files
# --------------------------------------------------------------------------- #
def generate_metrics(dest: Path, n_metrics: int, limit: float = 1_000_000) -> Path:
    """'<name> <value>' lines, for the iterator-to-iterator lessons."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w") as w:
        for _ in range(n_metrics):
            w.write(f"{random_string(16)} {random.random() * limit}\n")
    return dest


def generate_exam_data(root: Path, n_students: int, n_attempts: int = 5) -> Path:
    """examIds.txt / examEmails.txt / examScores.txt, for the RDD joins + cogroup lessons."""
    root.mkdir(parents=True, exist_ok=True)
    names = [random_string(16) for _ in range(n_students + 1)]  # Scala: 0 to nStudents
    ids = [random_long() for _ in names]

    with (root / "examIds.txt").open("w") as fi, (root / "examEmails.txt").open(
        "w"
    ) as fe:
        for name, sid in zip(names, ids):
            fi.write(f"{sid} {name}\n")
            fe.write(f"{sid} {name}@rockthejvm.com\n")

    # Scala uses .toSet -> duplicate (id, major, minor) attempts are dropped
    scores = {
        (sid, random.randrange(10), random.randrange(10))
        for sid in ids
        for _ in range(n_attempts)
    }
    with (root / "examScores.txt").open("w") as fs:
        for sid, major, minor in scores:
            fs.write(f"{sid} {major}.{minor}\n")
    return root


def generate_text(
    dest: Path, n_words: int, n_paragraphs: int, n_senders: int = 0
) -> Path:
    """
    Lorem ipsum, one paragraph per line. With n_senders > 0 each line is
    '<1..n_senders> // <text>' (for the reusing-objects lessons).
    Simplified iterative version of the Scala recursive generator, same output shape.
    """
    assert n_words > 1 and n_paragraphs > 0 and n_senders >= 0
    words = WORDS_FILE.read_text().split()
    avg = max(n_words // n_paragraphs, 2)
    low, high = max(avg // 2, 1), max(avg * 3 // 2, 2)

    def word(last: bool) -> str:
        w = random.choice(words)
        return w + ("," if not last and random.randrange(5) == 0 else "")

    dest.parent.mkdir(parents=True, exist_ok=True)
    left = n_words
    with dest.open("w") as w:
        for p in range(n_paragraphs):
            par_len = (
                left
                if p == n_paragraphs - 1
                else min(random.randrange(low, high), left)
            )
            left -= par_len
            sentences = []
            while par_len > 0:
                s_len = par_len if par_len < 14 else random.randrange(2, 14)
                par_len -= s_len
                sent = " ".join(word(i == s_len - 1) for i in range(s_len)) + "."
                sentences.append(sent[0].upper() + sent[1:])
            prefix = f"{random.randrange(n_senders) + 1} // " if n_senders else ""
            w.write(prefix + " ".join(sentences) + "\n")
    return dest


if __name__ == "__main__":
    # small defaults so it runs in seconds; raise them to match the course sizes
    # (course: 1M students, 10M metrics, 60M words / 3M lines / 200 senders)
    generate_exam_data(GENERATED / "examData", 100_000)
    generate_metrics(GENERATED / "metrics" / "metrics1m.txt", 1_000_000)
    generate_text(GENERATED / "lipsum" / "300k.txt", 6_000_000, 300_000, 200)
    print(f"written to {GENERATED}")
