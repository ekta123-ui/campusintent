"""Fine-tune DistilBERT for intent classification.

Needs:  pip install torch transformers   (a GPU makes it much faster, e.g. Google Colab)
Run:    python -m src.train_transformer
"""
import inspect
import json

import numpy as np
import pandas as pd

from . import config
from .evaluate import compute_metrics, most_confused, plot_confusion_matrix, report


def main():
    import torch
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments,
                              set_seed)

    set_seed(config.RANDOM_SEED)
    train = pd.read_csv(config.TRAIN_CSV, keep_default_na=False)
    val = pd.read_csv(config.VAL_CSV, keep_default_na=False)
    test = pd.read_csv(config.TEST_CSV, keep_default_na=False)

    tok = AutoTokenizer.from_pretrained(config.TRANSFORMER_NAME)

    class DS(torch.utils.data.Dataset):
        def __init__(self, df):
            self.enc = tok(list(df["query"]), truncation=True, padding="max_length", max_length=config.MAX_LEN)
            self.labels = [config.LABEL2ID[l] for l in df["intent"]]

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, i):
            item = {k: torch.tensor(v[i]) for k, v in self.enc.items()}
            item["labels"] = torch.tensor(self.labels[i])
            return item

    model = AutoModelForSequenceClassification.from_pretrained(
        config.TRANSFORMER_NAME, num_labels=len(config.LABELS), id2label=config.ID2LABEL, label2id=config.LABEL2ID)

    def metrics_fn(p):
        preds = np.argmax(p.predictions, axis=1)
        m = compute_metrics(p.label_ids, preds)
        return {"accuracy": m["accuracy"], "f1_macro": m["f1_macro"]}

    kw = dict(output_dir=str(config.TRANSFORMER_DIR / "checkpoints"), num_train_epochs=config.EPOCHS,
              per_device_train_batch_size=config.BATCH_SIZE, per_device_eval_batch_size=64,
              learning_rate=config.LEARNING_RATE, weight_decay=0.01, warmup_ratio=0.1,
              save_strategy="epoch", load_best_model_at_end=True, metric_for_best_model="f1_macro",
              save_total_limit=1, logging_steps=50, report_to="none", seed=config.RANDOM_SEED)
    # argument was renamed across transformers versions
    key = "eval_strategy" if "eval_strategy" in inspect.signature(TrainingArguments.__init__).parameters else "evaluation_strategy"
    kw[key] = "epoch"

    trainer = Trainer(model=model, args=TrainingArguments(**kw), train_dataset=DS(train), eval_dataset=DS(val),
                      compute_metrics=metrics_fn)
    trainer.train()

    out = trainer.predict(DS(test))
    pred = [config.ID2LABEL[i] for i in np.argmax(out.predictions, axis=1)]
    m = compute_metrics(test["intent"], pred)
    print(report(test["intent"], pred, config.LABELS))

    trainer.save_model(str(config.TRANSFORMER_DIR))
    tok.save_pretrained(str(config.TRANSFORMER_DIR))
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot_confusion_matrix(test["intent"], pred, config.LABELS, config.FIGURES_DIR / "confusion_distilbert.png",
                          "DistilBERT - test set")
    (config.REPORTS_DIR / "transformer_metrics.json").write_text(json.dumps(m, indent=2))

    section = ["", "## DistilBERT (fine-tuned)", "",
               f"- Test accuracy: {m['accuracy']:.4f}", f"- Test macro F1: {m['f1_macro']:.4f}", "",
               "Most confused intent pairs (true, predicted, count):", ""]
    section += [f"- {t} -> {p}: {c}" for t, p, c in most_confused(test["intent"], pred, config.LABELS)]
    with open(config.RESULTS_MD, "a") as f:
        f.write("\n".join(section) + "\n")


if __name__ == "__main__":
    main()
