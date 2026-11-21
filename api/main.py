"""FastAPI backend.  Run from the project root:  python -m uvicorn api.main:app --reload

Public endpoints : GET /, /health, /stats      POST /predict, /ask, /feedback
Staff endpoints  : GET /admin/questions         POST /admin/resolve, /admin/knowledge
(Set the environment variable ADMIN_KEY to require the header  X-Admin-Key  on staff endpoints.)
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (AskRequest, AskResponse, FeedbackRequest, KnowledgeRequest, QueryRequest, QueryResponse,
                         ResolveRequest)
from src.kb_loader import ingest
from src.rag import RAGPipeline

app = FastAPI(title="CampusIntent API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

RESPONSES = json.loads((ROOT / "api" / "responses.json").read_text(encoding="utf-8"))
rag = RAGPipeline()
predictor = rag.predictor
if rag.kb.count() == 0:                                   # first start: load the starter knowledge base
    print("Knowledge base is empty -> ingesting data/knowledge_base:", ingest(rag))

ADMIN_KEY = os.getenv("ADMIN_KEY")
FALLBACK = {"department": "Student Help Desk",
            "reply": "I am not fully sure what you need. Please contact the Student Help Desk and a staff member will help you."}


def admin_guard(x_admin_key: Optional[str] = Header(default=None)):
    if ADMIN_KEY and x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key header")


@app.get("/")
def root():
    return {"message": "CampusIntent API is running. Open /docs to try it.", "version": app.version}


@app.get("/health")
def health():
    return {"status": "ok", "classifier": predictor.backend, "vector_backend": rag.kb.backend,
            "embedder": rag.embedder.name, "llm": rag.stats()["llm"]}


@app.get("/stats")
def stats():
    return rag.stats()


@app.post("/predict", response_model=QueryResponse)
def predict(req: QueryRequest):
    result = predictor.predict(req.query)
    info = FALLBACK if result["low_confidence"] else RESPONSES.get(result["intent"], FALLBACK)
    return {**result, "department": info["department"], "reply": info["reply"]}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    return rag.ask(req.query, save=req.save)


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    try:
        rag.feedback(req.query_id, req.helpful)
    except KeyError:
        raise HTTPException(404, "Unknown query_id")
    return {"ok": True}


@app.get("/admin/questions", dependencies=[Depends(admin_guard)])
def admin_questions(status: Optional[str] = None, limit: int = 50):
    """Saved student questions. Use status=unanswered (or needs_review) to see what the KB cannot answer yet."""
    return rag.list_queries(status=status, limit=limit)


@app.post("/admin/resolve", dependencies=[Depends(admin_guard)])
def admin_resolve(req: ResolveRequest):
    """Answer a saved question; the answer is added to the knowledge base so the system learns it."""
    try:
        return rag.resolve(req.query_id, req.answer, intent=req.intent, question=req.question, course=req.course)
    except KeyError:
        raise HTTPException(404, "Unknown query_id")


@app.post("/admin/knowledge", dependencies=[Depends(admin_guard)])
def admin_knowledge(req: KnowledgeRequest):
    ids = rag.add_knowledge(req.question, req.answer, intent=req.intent, course=req.course, source="admin",
                            alt_questions=req.alt_questions)
    return {"added": len(ids)}
