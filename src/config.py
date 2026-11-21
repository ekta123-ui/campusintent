"""Central configuration: paths, labels and hyper-parameters."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw" / "campus_intent_dataset_v2.csv"
DATA_PROCESSED = ROOT / "data" / "processed"
TRAIN_CSV = DATA_PROCESSED / "train.csv"
VAL_CSV = DATA_PROCESSED / "val.csv"
TEST_CSV = DATA_PROCESSED / "test.csv"
REAL_TEST_CSV = ROOT / "data" / "real_queries" / "real_test_queries.csv"  # optional: columns query,intent

MODELS_DIR = ROOT / "models"
BASELINE_DIR = MODELS_DIR / "baseline"
BASELINE_MODEL = BASELINE_DIR / "best_model.joblib"
TRANSFORMER_DIR = MODELS_DIR / "distilbert_intent"

REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
RESULTS_MD = REPORTS_DIR / "results.md"

# Order matches the intent_id column in the dataset.
LABELS = [
    "Admission", "Fees", "Exam_Results", "Timetable_Schedule", "Hostel_Accommodation",
    "Transport_Bus", "Placement", "Scholarship", "Documents_Certificates", "Faculty_Department",
    "Cafeteria_Food", "Location_Directions", "Library_Facilities", "Attendance_Leave",
    "Complaint_Support", "Out_of_Scope",
]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

RANDOM_SEED = 42
CONFIDENCE_THRESHOLD = 0.40   # below this the predictor flags the query for human help

# Transformer settings
TRANSFORMER_NAME = "distilbert-base-uncased"
MAX_LEN = 48
BATCH_SIZE = 32
EPOCHS = 4
LEARNING_RATE = 5e-5


# ------------------------------------------------------------------ RAG / vector database
import os

KB_DIR = ROOT / "data" / "knowledge_base"          # FAQ csv / md / txt / pdf files to ingest
VECTORDB_DIR = ROOT / "data" / "vectordb"          # persistent vector database lives here
VECTOR_BACKEND = "auto"                            # auto | chroma | simple
EMBEDDER = "auto"                                  # auto | sentence-transformer | hashing
ST_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 4
INTENT_BOOST = 0.20        # re-ranking bonus for KB entries that have the predicted intent (it only re-orders; the threshold uses raw similarity)
COURSE_BOOST = 0.04        # bonus / penalty when the query names a course
# Similarity needed before the system answers from the knowledge base.
# Tune with:  python -m src.eval_rag
ANSWER_THRESHOLD = {"hashing": 0.30, "st": 0.45}
# Similarity above which a new query is treated as a repeat of a stored one.
DUPLICATE_THRESHOLD = {"hashing": 0.88, "st": 0.92}

# Optional LLM answer writing (set ANTHROPIC_API_KEY in your environment to enable)
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
