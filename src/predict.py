"""Inference: predict(query) -> intent, confidence, entities, human-fallback flag."""
import numpy as np

from . import config
from .nlp_features import extract_entities


def _softmax(x):
    x = np.asarray(x, dtype=float)
    e = np.exp(x - x.max())
    return e / e.sum()


class IntentPredictor:
    """Loads the fine-tuned DistilBERT model if present, otherwise the TF-IDF baseline."""

    def __init__(self, backend: str = "auto", threshold: float = config.CONFIDENCE_THRESHOLD):
        self.threshold = threshold
        self.backend = None
        if backend in ("auto", "transformer") and (config.TRANSFORMER_DIR / "config.json").exists():
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                self._torch = torch
                self.tokenizer = AutoTokenizer.from_pretrained(config.TRANSFORMER_DIR)
                self.model = AutoModelForSequenceClassification.from_pretrained(config.TRANSFORMER_DIR).eval()
                self.backend = "distilbert"
            except Exception as exc:  # torch/transformers missing -> fall back
                if backend == "transformer":
                    raise
                print(f"[predict] transformer unavailable ({exc}); using baseline")
        if self.backend is None:
            import joblib
            if not config.BASELINE_MODEL.exists():
                raise FileNotFoundError("No trained model found. Run: python -m src.train_baseline")
            self.pipe = joblib.load(config.BASELINE_MODEL)
            self.backend = "tfidf"

    def _probs(self, query: str) -> np.ndarray:
        if self.backend == "distilbert":
            enc = self.tokenizer(query, return_tensors="pt", truncation=True, max_length=config.MAX_LEN)
            with self._torch.no_grad():
                logits = self.model(**enc).logits[0].numpy()
            return _softmax(logits)
        clf = self.pipe.named_steps["clf"]
        if hasattr(self.pipe, "predict_proba"):
            probs = self.pipe.predict_proba([query])[0]
            classes = list(clf.classes_)
        else:  # LinearSVC: turn margins into pseudo-probabilities
            scores = self.pipe.decision_function([query])[0]
            probs = _softmax(scores * 3.0)
            classes = list(clf.classes_)
        full = np.zeros(len(config.LABELS))
        for c, p in zip(classes, probs):
            full[config.LABEL2ID[c]] = p
        return full

    def predict(self, query: str) -> dict:
        probs = self._probs(query)
        idx = int(np.argmax(probs))
        conf = float(probs[idx])
        top3 = [{"intent": config.ID2LABEL[i], "confidence": round(float(probs[i]), 4)} for i in np.argsort(-probs)[:3]]
        return {
            "query": query,
            "intent": config.ID2LABEL[idx],
            "confidence": round(conf, 4),
            "low_confidence": conf < self.threshold,
            "entities": extract_entities(query),
            "top3": top3,
            "model": self.backend,
        }


if __name__ == "__main__":
    import sys
    p = IntentPredictor()
    q = " ".join(sys.argv[1:]) or "What is the last date to apply for MCA admission?"
    print(p.predict(q))
