"""Classical NLP baselines: TF-IDF (word + char n-grams) with NB / Logistic Regression / Linear SVM.

Run:  python -m src.train_baseline
"""
import json
import time

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.svm import LinearSVC

from . import config
from .evaluate import compute_metrics, most_confused, plot_confusion_matrix, report
from .preprocessing import preprocess_many


def build_pipeline(clf):
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        # character n-grams make the model robust to typos such as "hsotel" or "admsion"
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)),
    ])
    return Pipeline([("prep", FunctionTransformer(preprocess_many)), ("tfidf", features), ("clf", clf)])


def get_models():
    return {
        "TF-IDF + Naive Bayes": ComplementNB(alpha=0.3),
        "TF-IDF + Logistic Regression": LogisticRegression(max_iter=3000, C=10, random_state=config.RANDOM_SEED),
        "TF-IDF + Linear SVM": LinearSVC(C=1.0, random_state=config.RANDOM_SEED),
    }


def main():
    train = pd.read_csv(config.TRAIN_CSV, keep_default_na=False)
    val = pd.read_csv(config.VAL_CSV, keep_default_na=False)
    test = pd.read_csv(config.TEST_CSV, keep_default_na=False)
    real = pd.read_csv(config.REAL_TEST_CSV, keep_default_na=False) if config.REAL_TEST_CSV.exists() else None

    config.BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    results, best_name, best_f1, best_pipe = [], None, -1.0, None
    for name, clf in get_models().items():
        pipe = build_pipeline(clf)
        t0 = time.time()
        pipe.fit(train["query"], train["intent"])
        secs = time.time() - t0
        mv = compute_metrics(val["intent"], pipe.predict(val["query"]))
        mt = compute_metrics(test["intent"], pipe.predict(test["query"]))
        row = {"model": name, "val_accuracy": mv["accuracy"], "val_f1_macro": mv["f1_macro"],
               "test_accuracy": mt["accuracy"], "test_f1_macro": mt["f1_macro"], "train_seconds": round(secs, 2)}
        if real is not None and len(real):
            mr = compute_metrics(real["intent"], pipe.predict(real["query"]))
            row["real_accuracy"], row["real_f1_macro"] = mr["accuracy"], mr["f1_macro"]
        results.append(row)
        print(f"{name:32s} val F1={mv['f1_macro']:.4f}  test acc={mt['accuracy']:.4f}  test F1={mt['f1_macro']:.4f}")
        if mv["f1_macro"] > best_f1:
            best_name, best_f1, best_pipe = name, mv["f1_macro"], pipe

    joblib.dump(best_pipe, config.BASELINE_MODEL)
    print(f"\nBest baseline: {best_name} -> saved to {config.BASELINE_MODEL}")

    pred = best_pipe.predict(test["query"])
    plot_confusion_matrix(test["intent"], pred, config.LABELS, config.FIGURES_DIR / "confusion_baseline.png",
                          f"{best_name} - test set")
    text_report = report(test["intent"], pred, config.LABELS)
    (config.REPORTS_DIR / "baseline_report.txt").write_text(text_report)
    print(text_report)

    df = pd.DataFrame(results)
    (config.REPORTS_DIR / "baseline_metrics.json").write_text(json.dumps(results, indent=2))
    lines = ["# Results", "", "## Classical baselines", "", df.round(4).to_markdown(index=False), "",
             f"Best baseline (by validation macro F1): **{best_name}**", "",
             "Most confused intent pairs on the test set (true, predicted, count):", ""]
    for t, p, c in most_confused(test["intent"], pred, config.LABELS):
        lines.append(f"- {t} -> {p}: {c}")
    config.RESULTS_MD.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
