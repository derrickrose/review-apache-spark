#!/usr/bin/env bash
# Run every variant of the given labs (default: all). Usage inside the spark container:
#   run_labs.sh <out_dir> <runs> <warmup> [lab files...]
# The baseline variant always runs first: relative criteria and the correctness gate depend on it.
set -u
OUT=${1:-/workspace/results}; RUNS=${2:-3}; WARM=${3:-1}; shift 3 || true
cd "$(dirname "$0")/labs"
LABS=${*:-$(ls lab*.py)}
mkdir -p "$OUT"
for lab in $LABS; do
  name=${lab%.py}
  variants=$(python -c "import sys; sys.path.insert(0,'.'); import $name as m; print(' '.join(['baseline']+[v for v in m.VARIANTS if v!='baseline']))")
  for v in $variants; do
    start=$(date +%s)
    if python ../bench.py --lab "$lab" --variant "$v" --runs "$RUNS" --warmup "$WARM" --out "$OUT/$name.csv" > "$OUT/$name.$v.log" 2>&1; then
      verdict=$(python -c "import csv;r=list(csv.DictReader(open('$OUT/$name.csv')))[-1];print(r['verdict'] or '-', '|', r['correct'], '|', r['runtime_median_s'],'s')")
      echo "$name $v OK $(( $(date +%s)-start ))s :: $verdict"
    else
      echo "$name $v ERROR $(( $(date +%s)-start ))s :: $(grep -E 'Error|Exception' "$OUT/$name.$v.log" | grep -v WARN | tail -1 | cut -c1-220)"
    fi
  done
done
