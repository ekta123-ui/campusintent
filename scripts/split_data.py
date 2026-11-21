"""Write train/val/test CSVs using the `split` column of the raw dataset."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src import config

df = pd.read_csv(config.DATA_RAW, keep_default_na=False)
config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
for name, path in [("train", config.TRAIN_CSV), ("val", config.VAL_CSV), ("test", config.TEST_CSV)]:
    part = df[df["split"] == name]
    part.to_csv(path, index=False)
    print(f"{name}: {len(part)} rows -> {path}")
