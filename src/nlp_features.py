"""NLP feature helpers: rule-based entity extraction, POS tags (optional spaCy), n-grams."""
import re
from collections import Counter

from .preprocessing import clean_text, tokenize

# Ordered: the first matching pattern wins (specific before generic).
COURSE_PATTERNS = [
    ("B.Tech Cyber Security", r"\bbtech\b.*\bcyber"),
    ("B.Tech Web Development", r"\bbtech\b.*\bweb"),
    ("B.Tech AI & ML", r"\bbtech\b.*\b(ai|ml)\b"),
    ("Hotel Management", r"hotel management|\bbhm\b"),
    ("MCA", r"\bmca\b"),
    ("BCA", r"\bbca\b"),
    ("M.Sc", r"\bmsc\b"),
    ("B.Sc", r"\bbsc\b"),
    ("B.Com", r"\bbcom\b"),
    ("LLB", r"\bllb\b"),
    ("D.Pharmacy", r"\bdpharm\w*|diploma in pharmacy"),
    ("B.Pharmacy", r"\bbpharm\w*|\bpharmacy\b"),
]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]
DOC_KEYWORDS = ["bonafide", "transfer certificate", "migration", "character certificate", "marksheet",
                "degree certificate", "id card", "no-dues", "no dues", "provisional", "fee receipt", "noc"]


def extract_entities(query: str) -> dict:
    """Return the entities found in a query (course, term, weekday, date, document)."""
    c = clean_text(query)
    ents = {}
    for name, pat in COURSE_PATTERNS:
        if re.search(pat, c):
            ents["COURSE"] = name
            break
    m = re.search(r"\b(\d)(?:st|nd|rd|th)?\s*(semester|year)\b", c)
    if m:
        ents["TERM"] = f"{m.group(1)} {m.group(2)}"
    for d in WEEKDAYS:
        if re.search(rf"\b{d}\b", c):
            ents["WEEKDAY"] = d.capitalize()
            break
    m = re.search(rf"\b(\d{{1,2}})\s+({'|'.join(MONTHS)})\b", c)
    if m:
        ents["DATE"] = f"{m.group(1)} {m.group(2).capitalize()}"
    for k in DOC_KEYWORDS:
        if k in c:
            ents["DOCUMENT"] = k
            break
    return ents


def pos_tags(query: str):
    """POS tags with spaCy if installed (python -m spacy download en_core_web_sm); else None."""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        return None
    return [(t.text, t.pos_) for t in nlp(query)]


def ngrams(text: str, n: int = 2):
    toks = tokenize(text)
    return [" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)]


def top_ngrams(texts, n: int = 2, k: int = 10):
    c = Counter()
    for t in texts:
        c.update(ngrams(t, n))
    return c.most_common(k)
