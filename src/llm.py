"""Optional answer writing with Claude (the 'G' in RAG).

Set the environment variable ANTHROPIC_API_KEY and `pip install anthropic` to enable it.
Without them the pipeline simply returns the best matching knowledge-base answer (extractive mode).
"""
import os

from . import config

SYSTEM = (
    "You are a helpful college helpdesk assistant. Answer the student's question using ONLY the "
    "context provided. If the context does not contain the answer, say you do not have that "
    "information and suggest contacting the relevant college office. Never invent fees, dates, "
    "phone numbers or rules. Be concise (2-4 sentences) and reply in the same language style as "
    "the student (English or Hinglish)."
)


def available() -> bool:
    if not os.getenv("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def generate(query: str, contexts: list):
    """contexts: [{"question":..., "answer":...}]. Returns text, or None if the LLM is unavailable/failed."""
    if not available() or not contexts:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic()
        ctx = "\n\n".join(f"[{i + 1}] Q: {c.get('question', '')}\nA: {c['answer']}" for i, c in enumerate(contexts))
        msg = client.messages.create(
            model=config.CLAUDE_MODEL, max_tokens=400, system=SYSTEM,
            messages=[{"role": "user", "content": f"Context:\n{ctx}\n\nStudent question: {query}"}])
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        return text or None
    except Exception as exc:  # network / key / model errors -> fall back to extractive mode
        print(f"[llm] generation failed, using extractive answer: {type(exc).__name__}: {exc}")
        return None
