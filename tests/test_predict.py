import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config

pytestmark = pytest.mark.skipif(not config.BASELINE_MODEL.exists(), reason="train the baseline first")


def test_labels_match_dataset():
    import pandas as pd
    df = pd.read_csv(config.DATA_RAW, keep_default_na=False)
    mapping = df.drop_duplicates("intent").set_index("intent")["intent_id"].to_dict()
    assert mapping == config.LABEL2ID


def test_predict_known_intents():
    from src.predict import IntentPredictor
    p = IntentPredictor(backend="tfidf")
    assert p.predict("What is the last date to apply for MCA admission?")["intent"] == "Admission"
    assert p.predict("What time does the canteen open?")["intent"] == "Cafeteria_Food"
    r = p.predict("How do I reach the college from Gurgaon?")
    assert r["intent"] == "Location_Directions" and 0 <= r["confidence"] <= 1
