"""Export the questions students asked (stored in the vector DB) to a CSV for review and retraining.

  python scripts/export_new_queries.py

Writes data/real_queries/collected_queries.csv. Review the `intent` column, then
  * copy verified rows to data/real_queries/real_test_queries.csv  (honest test set), and/or
  * append them to data/processed/train.csv  and re-run  python -m src.train_baseline
Rows with labeled=True were corrected/answered by staff and are the most reliable.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config
from src.rag import RAGPipeline

rag = RAGPipeline()
rows = rag.list_queries(limit=100000)
out = config.ROOT / "data" / "real_queries" / "collected_queries.csv"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["query", "intent", "confidence", "status", "times_asked", "labeled"])
    for r in rows:
        w.writerow([r["query"], r["intent"], r["confidence"], r["status"], r["count"], r["labeled"]])
print(f"{len(rows)} questions -> {out}")
