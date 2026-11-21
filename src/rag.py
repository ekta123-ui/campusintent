"""Retrieval-Augmented Generation for the college helpdesk.

ask(question):
  1. classify the intent + extract entities      (NLP classifier from the earlier milestones)
  2. retrieve the best knowledge-base entries     (vector database, reranked by intent/course)
  3. answer from them                             (Claude if configured, otherwise extractive)
  4. remember the question in a second vector collection ("queries") so that
       - repeated questions are counted (what do students ask most?)
       - questions the KB cannot answer are queued for staff (status = unanswered)
  Staff then call resolve(): the answer is added to the KB, so the system now knows the new problem.

Run:  python -m src.rag "how do I get a bonafide certificate?"
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config, llm
from .embeddings import get_embedder
from .predict import IntentPredictor
from .vector_store import open_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _kb_id(*parts) -> str:
    return "kb_" + hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()[:14]


class RAGPipeline:
    def __init__(self, base_dir=None, embedder=None, backend=None, predictor=None, use_llm: bool = True):
        self.base_dir = Path(base_dir or config.VECTORDB_DIR)
        self.embedder = embedder or get_embedder(config.EMBEDDER)
        self.kb = open_store("kb", self.embedder, backend, self.base_dir)
        self.queries = open_store("queries", self.embedder, backend, self.base_dir)
        self.predictor = predictor or IntentPredictor()
        self.use_llm = use_llm
        self.answer_thr = config.ANSWER_THRESHOLD[self.embedder.kind]
        self.dup_thr = config.DUPLICATE_THRESHOLD[self.embedder.kind]
        self.responses = json.loads((config.ROOT / "api" / "responses.json").read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ knowledge base
    def add_knowledge(self, question, answer, intent="", course="", source="admin", alt_questions=()):
        """Add one FAQ (plus optional alternative phrasings) to the knowledge base."""
        ids, texts, metas = [], [], []
        for q in [question, *alt_questions]:
            ids.append(_kb_id(q, answer))
            texts.append(q)
            metas.append({"question": question, "answer": answer, "intent": intent or "", "course": course or "",
                          "source": source, "added": _now()})
        self.kb.add(ids, texts, metas)
        return ids

    def _retrieve(self, query, cls, k):
        raw = self.kb.query(query, k=max(10, k * 3))
        course = cls["entities"].get("COURSE")
        for h in raw:
            m, s = h["metadata"], h["score"]
            h["similarity"] = round(s, 4)
            if m.get("intent") and m["intent"] == cls["intent"] and not cls["low_confidence"]:
                s += config.INTENT_BOOST
            if course and m.get("course"):
                s += config.COURSE_BOOST if m["course"] == course else -config.COURSE_BOOST
            h["score"] = round(s, 4)
        raw.sort(key=lambda h: -h["score"])
        seen, out = set(), []
        for h in raw:                                   # alternative phrasings share an answer: keep the best one
            key = h["metadata"].get("answer")
            if key in seen:
                continue
            seen.add(key)
            out.append(h)
            if len(out) >= k:
                break
        return out

    # ------------------------------------------------------------------ question memory
    def _remember(self, query, cls, status, best):
        now = _now()
        near = self.queries.query(query, k=1)
        if near and near[0]["score"] >= self.dup_thr:   # same problem asked again
            d = near[0]
            meta = dict(d["metadata"])
            meta["count"] = int(meta.get("count", 1)) + 1
            meta["last_seen"] = now
            if meta.get("status") == "unanswered" and status == "answered":
                meta["status"] = "resolved"             # the KB covers it now
            self.queries.update_metadata(d["id"], meta)
            return d["id"], meta["count"], False, meta["status"]
        qid = "q_" + uuid.uuid4().hex[:10]
        self.queries.add([qid], [query], [{
            "intent": cls["intent"], "confidence": float(cls["confidence"]), "status": status, "count": 1,
            "best_score": float(best), "created": now, "last_seen": now,
            "course": cls["entities"].get("COURSE", ""), "answer": "", "labeled": False, "up": 0, "down": 0}])
        return qid, 1, True, status

    # ------------------------------------------------------------------ main entry point
    def ask(self, query: str, save: bool = True, k: int = config.TOP_K) -> dict:
        query = query.strip()
        cls = self.predictor.predict(query)
        intent = cls["intent"]
        info = self.responses.get(intent, {})
        base = {"query": query, "intent": intent, "confidence": cls["confidence"], "entities": cls["entities"],
                "model": cls["model"], "department": info.get("department"), "sources": [], "related": [],
                "query_id": None, "saved": False, "times_asked": None, "new_question": None, "generator": "rule"}

        if intent == "Out_of_Scope" and not cls["low_confidence"]:
            return {**base, "status": "out_of_scope", "department": None,
                    "answer": self.responses["Out_of_Scope"]["reply"]}

        hits = self._retrieve(query, cls, k)
        best = hits[0]["similarity"] if hits else 0.0      # raw similarity decides; the intent boost only re-orders
        related = [{"question": h["metadata"].get("question", ""), "score": h["score"]} for h in hits[:3]]

        if cls["low_confidence"] and best < 0.5 * self.answer_thr:     # gibberish / unclear: do not pollute the queue
            return {**base, "status": "unclear", "related": related,
                    "answer": "I could not understand that. Could you rephrase your question with a few more details?"}

        if best >= self.answer_thr:
            status = "answered"
            ctx = [h for h in hits if h["similarity"] >= self.answer_thr * 0.85][:3]
            text = None
            if self.use_llm:
                text = llm.generate(query, [{"question": h["metadata"].get("question", ""),
                                             "answer": h["metadata"]["answer"]} for h in ctx])
            generator = "claude" if text else "extractive"
            answer = text or ctx[0]["metadata"]["answer"]
            sources = [{"kb_id": h["id"], "question": h["metadata"].get("question", ""),
                        "answer": h["metadata"]["answer"], "score": h["score"], "intent": h["metadata"].get("intent", ""),
                        "source": h["metadata"].get("source", "")} for h in ctx]
        else:
            status, generator, sources = "unanswered", "rule", []
            office = info.get("department") or "the Student Help Desk"
            answer = ("I could not find a confirmed answer to this in the college knowledge base. "
                      + ("I have saved your question so staff can add an answer. " if save else "")
                      + f"For now, please contact: {office}.")

        result = {**base, "status": status, "answer": answer, "sources": sources, "related": related,
                  "generator": generator}
        if save:
            qid, count, new, final_status = self._remember(query, cls, status, best)
            result.update(query_id=qid, saved=True, times_asked=count, new_question=new)
            if final_status == "resolved":
                result["status"] = "answered"
        return result

    # ------------------------------------------------------------------ learning loop
    def resolve(self, query_id, answer, intent=None, question=None, course=""):
        """Staff answer a saved question: it becomes part of the knowledge base."""
        rec = self.queries.get(query_id)
        if rec is None:
            raise KeyError(query_id)
        question = (question or rec["text"]).strip()
        intent = intent or rec["metadata"].get("intent", "")
        ids = self.add_knowledge(question, answer, intent=intent, course=course, source="admin")
        self.queries.update_metadata(query_id, {"status": "resolved", "answer": answer, "intent": intent,
                                                "labeled": True})
        return {"query_id": query_id, "kb_ids": ids, "intent": intent}

    def feedback(self, query_id, helpful: bool):
        rec = self.queries.get(query_id)
        if rec is None:
            raise KeyError(query_id)
        m = rec["metadata"]
        upd = {"up": int(m.get("up", 0)) + (1 if helpful else 0), "down": int(m.get("down", 0)) + (0 if helpful else 1)}
        if not helpful and m.get("status") in ("answered", "resolved"):
            upd["status"] = "needs_review"
        self.queries.update_metadata(query_id, upd)
        return {**m, **upd}

    def list_queries(self, status=None, limit=50):
        items = self.queries.all({"status": status} if status else None)
        items.sort(key=lambda h: (int(h["metadata"].get("count", 1)), h["metadata"].get("last_seen", "")), reverse=True)
        return [{"query_id": h["id"], "query": h["text"], **h["metadata"]} for h in items[:limit]]

    def stats(self):
        items = self.queries.all()
        by_status = {}
        for h in items:
            s = h["metadata"].get("status", "")
            by_status[s] = by_status.get(s, 0) + 1
        top = sorted(items, key=lambda h: -int(h["metadata"].get("count", 1)))[:5]
        return {"kb_entries": self.kb.count(), "questions_saved": len(items), "by_status": by_status,
                "unanswered": by_status.get("unanswered", 0) + by_status.get("needs_review", 0),
                "top_questions": [{"query": h["text"], "count": h["metadata"].get("count", 1)} for h in top],
                "embedder": self.embedder.name, "backend": self.kb.backend, "llm": llm.available()}


if __name__ == "__main__":
    import sys
    from .kb_loader import ingest
    rag = RAGPipeline()
    if rag.kb.count() == 0:
        print("Knowledge base empty -> ingesting", ingest(rag))
    q = " ".join(sys.argv[1:]) or "How do I get a bonafide certificate?"
    r = rag.ask(q, save=False)
    print(json.dumps({k: r[k] for k in ("status", "intent", "confidence", "answer", "generator")}, indent=2))
    for s in r["sources"]:
        print(f"  source ({s['score']}): {s['question']}")
