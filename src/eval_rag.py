"""Evaluate retrieval quality and help you choose ANSWER_THRESHOLD.

  python -m src.eval_rag

For every test query we retrieve from the knowledge base (without saving anything) and report:
  top-1 / hit@k intent accuracy of the retrieved entries (does retrieval fetch the right topic?),
  and, for several similarity thresholds, coverage (share of in-scope questions answered),
  precision (share of those answers from the right topic) and wrong answers to Out_of_Scope questions.
NOTE: queries come from the synthetic dataset, so treat the numbers as a sanity check, not as real-world accuracy.
"""
import tempfile

import pandas as pd

from . import config
from .kb_loader import ingest
from .rag import RAGPipeline


def main(split_csv=None, thresholds=(0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55)):
    df = pd.read_csv(split_csv or config.TEST_CSV, keep_default_na=False)
    with tempfile.TemporaryDirectory() as tmp:               # evaluate on a clean, temporary starter KB
        rag = RAGPipeline(base_dir=tmp, use_llm=False)
        ingest(rag)
        rows = []
        for q, true in zip(df["query"], df["intent"]):
            cls = rag.predictor.predict(q)
            hits = rag._retrieve(q, cls, config.TOP_K)
            top = hits[0] if hits else None
            rows.append({"true": true, "pred_intent": cls["intent"], "low": cls["low_confidence"],
                         "score": top["similarity"] if top else 0.0,
                         "top1_ok": bool(top) and top["metadata"].get("intent") == true,
                         "hitk_ok": any(h["metadata"].get("intent") == true for h in hits)})
        embedder = rag.embedder.name
    r = pd.DataFrame(rows)
    ins, oos = r[r.true != "Out_of_Scope"], r[r.true == "Out_of_Scope"]
    lines = [f"# RAG retrieval evaluation ({len(df)} test queries, embedder: {embedder})", "",
             f"- In-scope top-1 intent accuracy of retrieved entry: **{ins.top1_ok.mean():.3f}**",
             f"- In-scope hit@{config.TOP_K} (right topic somewhere in top {config.TOP_K}): **{ins.hitk_ok.mean():.3f}**", "",
             "| threshold | coverage (in-scope answered) | precision (right topic) | Out_of_Scope wrongly answered |",
             "|---|---|---|---|"]
    for t in thresholds:
        cov = ins[ins.score >= t]
        prec = cov.top1_ok.mean() if len(cov) else float("nan")
        wrong = oos[((oos.pred_intent != "Out_of_Scope") | oos.low) & (oos.score >= t)]
        lines.append(f"| {t:.2f} | {len(cov) / len(ins):.3f} | {prec:.3f} | {len(wrong) / len(oos):.3f} |")
    lines += ["", f"Current ANSWER_THRESHOLD for this embedder: {config.ANSWER_THRESHOLD[rag.embedder.kind]}"]
    text = "\n".join(lines)
    print(text)
    config.REPORTS_DIR.mkdir(exist_ok=True)
    (config.REPORTS_DIR / "rag_eval.md").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
