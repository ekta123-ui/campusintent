"""Build / refresh the knowledge base vector database from data/knowledge_base/.

  python scripts/ingest_kb.py            # add or update entries
  python scripts/ingest_kb.py --reset    # remove file-based entries first (staff-added answers are kept)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.kb_loader import ingest
from src.rag import RAGPipeline

ap = argparse.ArgumentParser()
ap.add_argument("--reset", action="store_true")
args = ap.parse_args()

rag = RAGPipeline()
print("ingested:", ingest(rag, reset=args.reset))
print("stats   :", rag.stats())
