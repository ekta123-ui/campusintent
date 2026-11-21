import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config
from src.embeddings import HashingEmbedder
from src.vector_store import open_store

try:
    import chromadb  # noqa: F401
    BACKENDS = ["simple", "chroma"]
except Exception:
    BACKENDS = ["simple"]


@pytest.mark.parametrize("backend", BACKENDS)
def test_vector_store_roundtrip(tmp_path, backend):
    e = HashingEmbedder()
    s = open_store("kb", e, backend, tmp_path)
    s.add(["a", "b"], ["How do I get a bonafide certificate?", "What time does the canteen open?"],
          [{"intent": "Documents_Certificates"}, {"intent": "Cafeteria_Food"}])
    assert s.query("bonafide certificate", k=1)[0]["id"] == "a"
    assert s.query("canteen", k=5, where={"intent": "Documents_Certificates"})[0]["id"] == "a"
    s.add(["a"], ["bonafide certificate application"], [{"intent": "Documents_Certificates", "n": 2}])   # upsert
    assert s.count() == 2
    s.update_metadata("b", {"n": 7})
    assert open_store("kb", e, backend, tmp_path).get("b")["metadata"]["n"] == 7     # persisted
    s.delete(["b"])
    assert s.count() == 1


needs_model = pytest.mark.skipif(not config.BASELINE_MODEL.exists(), reason="train the baseline first")


@needs_model
@pytest.mark.parametrize("backend", BACKENDS)
def test_rag_learns_new_questions(tmp_path, backend):
    from src.rag import RAGPipeline
    rag = RAGPipeline(base_dir=tmp_path, embedder=HashingEmbedder(), backend=backend, use_llm=False)
    rag.add_knowledge("How do I get a bonafide certificate?", "Apply at the student services office.",
                      intent="Documents_Certificates", source="test")

    ok = rag.ask("how can I get a bonafide certificate?")
    assert ok["status"] == "answered" and "student services" in ok["answer"]

    new = rag.ask("Is there a robotics club in the college?")
    assert new["status"] == "unanswered" and new["saved"] and new["new_question"] and new["query_id"]

    again = rag.ask("is there a robotics club in the college")             # same problem again
    assert again["query_id"] == new["query_id"] and again["times_asked"] == 2 and not again["new_question"]
    assert rag.stats()["unanswered"] == 1

    rag.resolve(new["query_id"], "Yes, the robotics club meets on Fridays.", intent="Faculty_Department")
    learned = rag.ask("Is there a robotics club in the college?")
    assert learned["status"] == "answered" and "robotics club meets" in learned["answer"]
    assert rag.stats()["unanswered"] == 0

    # everything survives a restart
    rag2 = RAGPipeline(base_dir=tmp_path, embedder=HashingEmbedder(), backend=backend, use_llm=False)
    assert rag2.kb.count() == rag.kb.count() and rag2.queries.count() == rag.queries.count()


@needs_model
def test_out_of_scope_is_not_saved(tmp_path):
    from src.rag import RAGPipeline
    rag = RAGPipeline(base_dir=tmp_path, embedder=HashingEmbedder(), backend="simple", use_llm=False)
    r = rag.ask("tell me a joke")
    assert r["status"] == "out_of_scope" and not r["saved"] and rag.queries.count() == 0


@needs_model
def test_feedback_flags_answer_for_review(tmp_path):
    from src.rag import RAGPipeline
    rag = RAGPipeline(base_dir=tmp_path, embedder=HashingEmbedder(), backend="simple", use_llm=False)
    rag.add_knowledge("What are the cafeteria timings?", "Check the notice at the cafeteria.", intent="Cafeteria_Food")
    r = rag.ask("what are the cafeteria timings")
    rag.feedback(r["query_id"], helpful=False)
    assert rag.queries.get(r["query_id"])["metadata"]["status"] == "needs_review"
