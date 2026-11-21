"""Text -> vector.

* SentenceTransformerEmbedder : real semantic embeddings (pip install sentence-transformers).
* HashingEmbedder             : offline fallback (character + word n-gram hashing). Needs no download,
                                is robust to typos, but only matches shared words, not meaning.
"""
import numpy as np

from . import config
from .preprocessing import STOPWORDS, clean_text

# For retrieval we drop generic question words so that content words drive the similarity.
EMBED_STOP = set(STOPWORDS) | {
    "what", "when", "where", "how", "which", "who", "please", "tell", "want", "know", "need", "get",
    "college", "student", "students", "kya", "hai", "hain", "ka", "ki", "ke", "mein", "kab", "kaise",
    "kahan", "kitna", "kitni", "mujhe", "kar", "karu", "sakte", "chahiye",
}


def _content_text(text: str) -> str:
    cleaned = clean_text(text)
    toks = [t for t in cleaned.split() if t not in EMBED_STOP]
    return " ".join(toks) if toks else cleaned


class HashingEmbedder:
    kind = "hashing"
    name = "hashing-v1"

    def __init__(self, char_features: int = 2048, word_features: int = 1024):
        from sklearn.feature_extraction.text import HashingVectorizer
        self._char = HashingVectorizer(analyzer="char_wb", ngram_range=(3, 5), n_features=char_features,
                                       alternate_sign=False, norm=None, lowercase=False)
        self._word = HashingVectorizer(analyzer="word", ngram_range=(1, 2), n_features=word_features,
                                       alternate_sign=False, norm=None, lowercase=False,
                                       token_pattern=r"(?u)\b\w+\b")
        self.dim = char_features + word_features

    def embed(self, texts) -> np.ndarray:
        import scipy.sparse as sp
        from sklearn.preprocessing import normalize
        t = [_content_text(x) for x in texts]
        c, w = self._char.transform(t), self._word.transform(t)
        c.data, w.data = np.log1p(c.data), np.log1p(w.data)
        x = normalize(sp.hstack([c, 1.5 * w]).tocsr())
        return x.toarray().astype(np.float32)


class SentenceTransformerEmbedder:
    kind = "st"

    def __init__(self, model_name: str = config.ST_MODEL):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.name = f"st:{model_name}"
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts) -> np.ndarray:
        v = self.model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(v, dtype=np.float32)


def get_embedder(kind: str = "auto"):
    if kind == "hashing":
        return HashingEmbedder()
    try:
        return SentenceTransformerEmbedder()
    except Exception as exc:
        if kind == "sentence-transformer":
            raise
        print(f"[embeddings] sentence-transformers unavailable ({type(exc).__name__}); using offline hashing embedder")
        return HashingEmbedder()
