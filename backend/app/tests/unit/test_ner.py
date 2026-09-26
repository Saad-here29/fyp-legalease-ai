"""Legal NER wrapper (app/ai/ner.py).

Most tests use a stand-in pipeline, so they run without the 539 MB model.
`test_real_model_*` load the actual weights and are skipped when
backend/storage/models/legal_ner/ is absent (the folder is gitignored)."""

from pathlib import Path

import pytest

from app.ai import ner
from app.core.config import settings


class _FakeTokenizer:
    """One 'token' per whitespace word — easy to reason about budgets."""

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": text.split()}


class _FakePipeline:
    """Tags whole words found in `lexicon`, returning offsets relative to the
    chunk it was given — the same contract as the HF pipeline."""

    def __init__(self, lexicon: dict[str, tuple[str, float]]):
        self.tokenizer = _FakeTokenizer()
        self.lexicon = lexicon
        self.calls: list[list[str]] = []

    def __call__(self, chunks, batch_size=8):
        self.calls.append(list(chunks))
        out = []
        for chunk in chunks:
            preds = []
            for phrase, (label, score) in self.lexicon.items():
                start = chunk.find(phrase)
                while start != -1:
                    preds.append({"entity_group": label, "score": score,
                                  "start": start, "end": start + len(phrase)})
                    start = chunk.find(phrase, start + 1)
            out.append(sorted(preds, key=lambda p: p["start"]))
        return out


@pytest.fixture
def fake(monkeypatch):
    def install(lexicon):
        pipe = _FakePipeline(lexicon)
        monkeypatch.setattr(ner, "_load", lambda: pipe)
        return pipe
    return install


def _count(s):
    return len(s.split())


# ---- chunking -----------------------------------------------------------

def test_chunks_respect_budget_and_offsets_map_back():
    text = " ".join(f"Sentence number {i} is here." for i in range(50))
    chunks = ner.chunk_text(text, _count, max_tokens=12)
    assert len(chunks) > 1
    for offset, chunk in chunks:
        assert _count(chunk) <= 12
        assert text[offset:offset + len(chunk)] == chunk


def test_chunks_break_at_sentence_ends():
    text = "One two three. Four five six. Seven eight nine."
    chunks = [c for _, c in ner.chunk_text(text, _count, max_tokens=6)]
    assert chunks == ["One two three. Four five six.", "Seven eight nine."]


def test_oversized_sentence_is_split_on_words():
    text = " ".join(f"w{i}" for i in range(25))          # one 25-word sentence
    chunks = ner.chunk_text(text, _count, max_tokens=10)
    assert [_count(c) for _, c in chunks] == [10, 10, 5]
    assert " ".join(c for _, c in chunks) == text


def test_single_huge_word_is_cut_by_characters():
    def by_chars(s):              # 1 token per 10 characters
        return (len(s) + 9) // 10
    text = "x" * 500
    chunks = ner.chunk_text(text, by_chars, max_tokens=20)
    assert all(by_chars(c) <= 20 for _, c in chunks)
    assert "".join(c for _, c in chunks) == text


def test_blank_text_gives_no_chunks():
    assert ner.chunk_text("   \n\n  ", _count) == []


# ---- word splitting + BIO decoding ------------------------------------------

def test_word_spans_split_edge_punctuation_like_training_data():
    text = '(Against W.P.No. 11983/2005), dated 30.7.1983, "Rs. 4,000/-"'
    words = [text[s:e] for s, e in ner.word_spans(text)]
    assert words == ["(", "Against", "W.P.No", ".", "11983/2005", ")", ",", "dated",
                     "30.7.1983", ",", '"', "Rs", ".", "4,000/-", '"']

def test_decode_bio_joins_words_and_averages_scores():
    text = "Mr. Khalid Abbas Khan on 30.7.1983 at Lahore"
    spans = [(m.start(), m.end()) for m in __import__("re").finditer(r"\S+", text)]
    tags = [("B-per", 0.9), ("I-per", 0.8), ("I-per", 0.7), ("I-per", 0.6),
            ("O", 1.0), ("B-date", 0.95), ("O", 1.0), ("B-loc", 0.9)]
    ents = ner._decode_bio(spans, tags)
    assert [(text[e["start"]:e["end"]], e["entity_group"]) for e in ents] == [
        ("Mr. Khalid Abbas Khan", "per"), ("30.7.1983", "date"), ("Lahore", "loc")]
    assert ents[0]["score"] == pytest.approx(0.75)


def test_decode_bio_stray_or_mismatched_inside_tag_starts_new_entity():
    spans = [(0, 1), (2, 3), (4, 5)]
    ents = ner._decode_bio(spans, [("I-org", 0.9), ("I-per", 0.9), ("I-per", 0.9)])
    assert [(e["entity_group"], e["start"], e["end"]) for e in ents] == [("org", 0, 1), ("per", 2, 5)]


# ---- extraction + post-processing ----------------------------------------

def test_entities_found_across_chunks_keep_document_offsets(fake):
    filler = " ".join(["filler"] * 300) + "."
    text = f"Heard at Lahore on 20.3.2009. {filler} Appeal by Muhammad Aslam dated 5.1.2010."
    fake({"Lahore": ("loc", 0.9), "20.3.2009": ("date", 0.95),
          "Muhammad Aslam": ("per", 0.9), "5.1.2010": ("date", 0.9)})
    res = ner.extract_entities(text)
    assert res.available
    assert [e.text for e in res.entities] == ["Lahore", "20.3.2009", "Muhammad Aslam", "5.1.2010"]
    for e in res.entities:
        assert text[e.first_offset:e.first_offset + len(e.text)] == e.text


def test_label_merging_threshold_dropping_and_dedup(fake):
    text = ("Cited in C.A. 12 of 2001 and again C.A. 12 of 2001. "
            "The Lahore High Court held so. FIR 44/2019 was lodged by Ali Khan. "
            "Weak guess here.")
    fake({
        "C.A. 12 of 2001": ("refCase", 0.9),      # LHC spelling -> refcase
        "Lahore High Court": ("refCourt", 0.8),   # LHC spelling -> refcourt
        "FIR 44/2019": ("FIRno", 0.99),           # dropped type
        "Ali Khan": ("Misc.name", 0.9),           # dropped type
        "Weak guess": ("org", 0.49),              # below 0.5
    })
    res = ner.extract_entities(text)
    got = [(e.type, e.text, e.count) for e in res.entities]
    assert got == [("refcase", "C.A. 12 of 2001", 2), ("refcourt", "Lahore High Court", 1)]
    assert res.as_json() == {
        "refcase": [{"text": "C.A. 12 of 2001", "count": 2, "score": 0.9}],
        "refcourt": [{"text": "Lahore High Court", "count": 1, "score": 0.8}],
    }


def test_text_is_capped_before_tagging(fake):
    pipe = fake({})
    ner.extract_entities("word. " * 20_000)
    tagged = "".join(c for batch in pipe.calls for c in batch)
    assert len(tagged) <= ner.MAX_CHARS


def test_model_unavailable_reports_it(monkeypatch):
    monkeypatch.setattr(ner, "_load", lambda: None)
    res = ner.extract_entities("Some text.")
    assert res.available is False and res.entities == []


def test_missing_weights_marks_unavailable(monkeypatch, tmp_path):
    ner.reset()
    monkeypatch.setattr(settings, "NER_ENABLED", True)
    monkeypatch.setattr(settings, "NER_MODEL_PATH", str(tmp_path))
    try:
        assert ner.extract_entities("text").available is False
    finally:
        ner.reset()


# ---- real model (skipped without weights) ---------------------------------

_WEIGHTS = Path(__file__).resolve().parents[3] / "storage" / "models" / "legal_ner"


@pytest.fixture(scope="module")
def real_model():
    if not (_WEIGHTS / "model.safetensors").exists():
        pytest.skip("NER weights not present (gitignored) — see docs/ner_training_results.md")
    ner.reset()
    mp = pytest.MonkeyPatch()
    mp.setattr(settings, "NER_ENABLED", True)
    mp.setattr(settings, "NER_MODEL_PATH", str(_WEIGHTS))
    yield
    mp.undo()
    ner.reset()


def test_real_model_tags_a_supreme_court_heading(real_model):
    # Sentence from the held-out SCP test split.
    text = ("CIVIL APPEAL NO.1074 OF 2009 (Against the judgment dated 20.3.2009 of the "
            "Lahore High Court, Lahore passed in W.P.No. 11983/2005)")
    res = ner.extract_entities(text)
    got = {(e.type, e.text) for e in res.entities}
    assert ("caseno", "CIVIL APPEAL NO.1074 OF 2009") in got
    assert ("date", "20.3.2009") in got
    assert ("appealcourt", "Lahore High Court, Lahore") in got
    assert ("appealcaseno", "W.P.No. 11983/2005") in got


def test_real_model_keeps_words_whole(real_model):
    res = ner.extract_entities("Islamabad, the 19th January, 2017")
    texts = [e.text for e in res.entities]
    assert "Islamabad" in texts
    assert not any(t.startswith("##") for t in texts)


def test_real_model_keeps_dotted_dates_as_one_entity(real_model):
    # The HF pipeline split "30.7.1983" at the dots into two dates.
    res = ner.extract_entities("The sale deed was registered on 30.7.1983 at Lahore.")
    dates = [e.text for e in res.entities if e.type == "date"]
    assert dates == ["30.7.1983"]
