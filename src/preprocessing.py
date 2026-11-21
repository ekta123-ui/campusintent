"""Text preprocessing: cleaning, short-form expansion, tokenization, lemmatization."""
import re

# Student short forms -> full words (helps the word-level features).
EXPANSIONS = {
    "pls": "please", "plz": "please", "whn": "when", "wat": "what", "sem": "semester",
    "appln": "application", "info": "information", "certi": "certificate", "u": "you",
    "r": "are", "tmrw": "tomorrow", "admn": "admission", "dept": "department", "n": "and",
    "hw": "how", "wch": "which", "avlbl": "available", "clg": "college", "cafe": "cafeteria",
    "hstl": "hostel", "lib": "library", "kb": "kab", "kia": "kya",
}

# A small stop-word list. Question words and negations are intentionally KEPT
# because they carry intent ("when", "where", "how", "not").
STOPWORDS = {
    "the", "a", "an", "is", "am", "are", "was", "were", "be", "to", "of", "in", "on", "for",
    "at", "by", "it", "this", "that", "i", "my", "me", "can", "do", "does", "there", "any",
    "will", "would", "should", "about", "with", "from", "as", "or",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def clean_text(text: str) -> str:
    """Lowercase, normalise symbols, remove punctuation, expand short forms."""
    text = str(text).lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"(?<=\w)\.(?=\w)", "", text)          # b.tech -> btech, m.c.a -> mca
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    tokens = [EXPANSIONS.get(t, t) for t in text.split()]
    return " ".join(tokens)


def tokenize(text: str) -> list:
    return _TOKEN_RE.findall(clean_text(text))


# ---- Lemmatization: use NLTK WordNet if available, else simple rules -------------
try:
    from nltk.stem import WordNetLemmatizer
    _wn = WordNetLemmatizer()
    _wn.lemmatize("tests")  # raises LookupError if the WordNet data is missing
except Exception:  # nltk or its data not installed
    _wn = None


def _rule_lemma(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("sses"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    return w


def lemmatize(tokens: list) -> list:
    if _wn is not None:
        return [_wn.lemmatize(t) for t in tokens]
    return [_rule_lemma(t) for t in tokens]


def preprocess(text: str, remove_stopwords: bool = False, lemma: bool = True) -> str:
    """Full pipeline used by the classical models."""
    tokens = tokenize(text)
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]
    if lemma:
        tokens = lemmatize(tokens)
    return " ".join(tokens)


def preprocess_many(texts):
    """Vectorised helper used inside scikit-learn pipelines (must stay importable for joblib)."""
    return [preprocess(t) for t in texts]
