import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.nlp_features import extract_entities
from src.preprocessing import clean_text, preprocess


def test_clean_text_expands_short_forms():
    assert clean_text("Pls tell whn 3rd sem results?") == "please tell when 3rd semester results"


def test_clean_text_normalises_course_names():
    assert "btech ai and ml" in clean_text("B.Tech AI & ML fees")


def test_preprocess_returns_string():
    assert isinstance(preprocess("What are the library opening hours?"), str)


def test_entities_course_and_term():
    e = extract_entities("When will the 3rd semester results of MCA be declared?")
    assert e["COURSE"] == "MCA" and e["TERM"] == "3 semester"


def test_entities_btech_streams():
    assert extract_entities("fee for B.Tech Cyber Security")["COURSE"] == "B.Tech Cyber Security"
    assert extract_entities("fee for B.Tech Web Development")["COURSE"] == "B.Tech Web Development"
    assert extract_entities("fee for B.Tech AI and ML")["COURSE"] == "B.Tech AI & ML"
