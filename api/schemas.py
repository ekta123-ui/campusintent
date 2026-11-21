from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, examples=["What is the last date to apply for MCA admission?"])


class IntentScore(BaseModel):
    intent: str
    confidence: float


class QueryResponse(BaseModel):
    query: str
    intent: str
    confidence: float
    low_confidence: bool
    entities: Dict[str, str]
    top3: List[IntentScore]
    model: str
    department: Optional[str] = None
    reply: str


# ------------------------------------------------------------------ RAG
class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    save: bool = True            # remember the question in the vector database


class Source(BaseModel):
    kb_id: str
    question: str
    answer: str
    score: float
    intent: str = ""
    source: str = ""


class AskResponse(BaseModel):
    query: str
    status: str                  # answered | unanswered | out_of_scope | unclear
    answer: str
    intent: str
    confidence: float
    entities: Dict[str, str]
    department: Optional[str] = None
    sources: List[Source] = []
    related: List[Dict[str, Any]] = []
    query_id: Optional[str] = None
    saved: bool = False
    times_asked: Optional[int] = None
    new_question: Optional[bool] = None
    generator: str = "rule"      # claude | extractive | rule
    model: str = ""


class ResolveRequest(BaseModel):
    query_id: str
    answer: str = Field(..., min_length=3)
    intent: Optional[str] = None
    question: Optional[str] = None
    course: str = ""


class KnowledgeRequest(BaseModel):
    question: str = Field(..., min_length=3)
    answer: str = Field(..., min_length=3)
    intent: str = ""
    course: str = ""
    alt_questions: List[str] = []


class FeedbackRequest(BaseModel):
    query_id: str
    helpful: bool
