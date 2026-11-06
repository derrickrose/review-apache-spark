"""
PySpark port of scala/part5rddtransformations/ReusingObjects.scala
Notes: 03_reusing_jvm_objects_part_1_to_read.md (versions 1-2), 04_..._part_2_to_read.md (version 3)

Text batches from many data sources: "35 // some text" -> (source_id, text).
Stats per source id:
  - number of lines
  - total number of words
  - length of the longest word
  - occurrences of the word "imperdiet"

⚠️ In PySpark the aggregation functions run in Python workers: there is no JVM GC involved
and pickling dominates, so expect much smaller differences than the course shows on the JVM.
The structure is kept identical so you can compare.

Run `python -m common.rdd_data_generator` (from optimization_spark_rock_jvm/) first (writes generated_data/lipsum/300k.txt).
"""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.rdd_data_generator import GENERATED  # noqa: E402
from common.spark_session import get_spark, keep_ui_open, timed  # noqa: E402

spark = get_spark("Reusing objects")
sc = spark.sparkContext

TEXT_PATH = (
    GENERATED / "lipsum" / "300k.txt"
)  # course: 3m.txt (60M words, 3M lines, 200 senders)
CRITICAL_WORD = "imperdiet"

# Same parsing as the course: split("//") keeps the spaces, so the key is "35 " and
# text.split(" ") yields a leading "" -> nWords is over-counted by 1 per line, and
# "imperdiet," / "imperdiet." / "Imperdiet" are not counted. Kept on purpose:
# all versions must return the same (wrong) numbers as the Scala code.
text = sc.textFile(str(TEXT_PATH)).map(lambda line: tuple(line.split("//", 1))).cache()


# ------------------------------------------------------------------ version 1
# immutable record: a NEW object per input line
@dataclass(frozen=True)
class TextStats:
    n_lines: int = 0
    n_words: int = 0
    max_word_length: int = 0
    occurrences: int = 0


def collect_stats():
    def aggregate_new_record(stats, record):
        new_words = record.split(" ")
        return TextStats(
            stats.n_lines + 1,
            stats.n_words + len(new_words),
            max(stats.max_word_length, max(map(len, new_words))),
            stats.occurrences + new_words.count(CRITICAL_WORD),
        )

    def combine_stats(s1, s2):
        return TextStats(
            s1.n_lines + s2.n_lines,
            s1.n_words + s2.n_words,
            max(s1.max_word_length, s2.max_word_length),
            s1.occurrences + s2.occurrences,
        )

    agg = text.aggregateByKey(TextStats(), aggregate_new_record, combine_stats)
    return {
        k: (s.n_lines, s.n_words, s.max_word_length, s.occurrences)
        for k, s in agg.collectAsMap().items()
    }


# ------------------------------------------------------------------ version 2
# mutable object, updated in place and returned
# (allowed: Spark gives each key its own deserialized copy of the zero value)
class MutableTextStats:
    # no __slots__: classes defined in a script are pickled by value (cloudpickle),
    # and slotted instances then fail to unpickle ("no attribute '__dict__'")
    def __init__(self):
        self.n_lines = self.n_words = self.max_word_length = self.occurrences = 0


def collect_stats_2():
    def aggregate_new_record(stats, record):
        new_words = record.split(" ")
        stats.n_lines += 1
        stats.n_words += len(new_words)
        stats.max_word_length = max(stats.max_word_length, max(map(len, new_words)))
        stats.occurrences += new_words.count(CRITICAL_WORD)
        return stats

    def combine_stats(s1, s2):
        s1.n_lines += s2.n_lines
        s1.n_words += s2.n_words
        s1.max_word_length = max(s1.max_word_length, s2.max_word_length)
        s1.occurrences += s2.occurrences
        return s1

    agg = text.aggregateByKey(MutableTextStats(), aggregate_new_record, combine_stats)
    return {
        k: (s.n_lines, s.n_words, s.max_word_length, s.occurrences)
        for k, s in agg.collectAsMap().items()
    }


# ------------------------------------------------------------------ version 3
# "ugly" flat list + index constants + single pass over the words
N_LINES, N_WORDS, LONGEST_WORD, OCCURRENCES = 0, 1, 2, 3


def aggregate_new_record_3(stats, record):
    new_words = record.split(" ")
    for word in new_words:  # one pass instead of max() + count()
        if len(word) > stats[LONGEST_WORD]:
            stats[LONGEST_WORD] = len(word)
        if word == CRITICAL_WORD:
            stats[OCCURRENCES] += 1
    stats[N_LINES] += 1
    stats[N_WORDS] += len(new_words)
    return stats


def combine_stats_3(s1, s2):
    s1[N_LINES] += s2[N_LINES]
    s1[N_WORDS] += s2[N_WORDS]
    s1[LONGEST_WORD] = max(s1[LONGEST_WORD], s2[LONGEST_WORD])
    s1[OCCURRENCES] += s2[OCCURRENCES]
    return s1


def collect_stats_3():
    agg = text.aggregateByKey([0, 0, 0, 0], aggregate_new_record_3, combine_stats_3)
    return {k: tuple(v) for k, v in agg.collectAsMap().items()}


if __name__ == "__main__":
    text.count()  # load + cache once
    r1 = timed("v1 immutable dataclass", collect_stats)
    r2 = timed("v2 mutable object", collect_stats_2)
    r3 = timed("v3 flat list, one pass", collect_stats_3)
    print("same results:", r1 == r2 == r3)
    keep_ui_open()
