"""Load FAQ / document files into the knowledge-base vector store."""
import csv
import hashlib
import re
from pathlib import Path

from . import config


def chunk_text(text: str, max_chars: int = 700) -> list:
    """Split a document into paragraph-based chunks of at most ~max_chars characters."""
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) + 1 > max_chars:
            chunks.append(cur)
            cur = ""
        while len(p) > max_chars:                       # very long paragraph
            chunks.append(p[:max_chars])
            p = p[max_chars:]
        cur = f"{cur} {p}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"[kb] skipping {path.name}: pip install pypdf to read PDFs")
        return ""
    return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)


def ingest(rag, kb_dir=None, reset: bool = False) -> dict:
    """(Re)build the knowledge base from the files in kb_dir. Staff-added entries (source='admin') are kept."""
    kb_dir = Path(kb_dir or config.KB_DIR)
    if reset:
        stale = [h["id"] for h in rag.kb.all() if h["metadata"].get("source") != "admin"]
        rag.kb.delete(stale)
    counts = {"faq_rows": 0, "chunks": 0, "files": 0}
    for path in sorted(kb_dir.glob("*")):
        if not path.is_file() or path.name.lower() == "readme.md":
            continue
        suffix = path.suffix.lower()
        if suffix == ".csv":
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if not (row.get("question") and row.get("answer")):
                        continue
                    alts = [a.strip() for a in (row.get("alt_questions") or "").split("|") if a.strip()]
                    rag.add_knowledge(row["question"].strip(), row["answer"].strip(), intent=row.get("intent", ""),
                                      course=row.get("course", ""), source=row.get("source") or path.name,
                                      alt_questions=alts)
                    counts["faq_rows"] += 1
        elif suffix in (".md", ".txt", ".pdf"):
            text = _read_pdf(path) if suffix == ".pdf" else path.read_text(encoding="utf-8", errors="ignore")
            ids, texts, metas = [], [], []
            for chunk in chunk_text(text):
                pred = rag.predictor.predict(chunk[:300])
                intent = pred["intent"] if pred["confidence"] >= 0.5 else ""
                ids.append("kb_" + hashlib.sha1(f"{path.name}||{chunk}".encode("utf-8")).hexdigest()[:14])
                texts.append(chunk)
                metas.append({"question": chunk[:100], "answer": chunk, "intent": intent, "course": "",
                              "source": path.name})
            rag.kb.add(ids, texts, metas)
            counts["chunks"] += len(ids)
        else:
            continue
        counts["files"] += 1
    return counts
