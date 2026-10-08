"""kb-v2 C5: query hints (retrieval only) and the legal-consequence rule.
Offline: the committed hints file, a stand-in search and a mocked model."""

import json
import re
from pathlib import Path

import pytest

from app.ai import embeddings
from app.ai.citation_check import check_citations
from app.core.config import settings
from app.kb import query_hints
from app.services import legal_chat_service as chat

HINTS_FILE = Path(__file__).resolve().parents[3] / "storage" / "kb" / "query_hints.json"


@pytest.fixture(autouse=True)
def real_hints(monkeypatch):
    monkeypatch.setattr(settings, "QUERY_HINTS_PATH", str(HINTS_FILE))
    query_hints.reset()
    yield
    query_hints.reset()


# --------------------------------------------------------------------------- hints

@pytest.mark.parametrize("question, ids", [
    ("What is the procedure for talaq?", ["talaq"]),
    ("How do I divorce my wife?", ["talaq"]),
    ("Can a wife get khula?", ["khula"]),
    ("Grounds for dissolution of marriage", ["khula"]),
    ("Is haq mehr payable on demand?", ["dower"]),
    ("Can a wife claim maintenance?", ["maintenance"]),
    ("Who gets custody of the minor child?", ["custody"]),
    ("Who are the heirs of a deceased Muslim?", ["inheritance"]),
    ("Is registration of marriage compulsory?", ["nikah_registration"]),
    ("Talaq, dower and maintenance after divorce", ["talaq", "dower", "maintenance"]),
])
def test_triggers(question, ids):
    assert [h["id"] for h in query_hints.matching(question)] == ids


@pytest.mark.parametrize("question", [
    "What is the punishment for theft?",                       # no family term
    "Can an accused be kept in police custody for 15 days?",   # criminal custody
    "How does a Christian couple get a divorce?",              # another community's law
    "How do I file for divorce in California?",                # foreign law
    "Can a wife get khula in India?",
    "Maintenance of public order by the police",
])
def test_no_hint(question):
    assert query_hints.matching(question) == []
    assert query_hints.expand(question) == question


def test_terms_are_search_terms_never_conclusions():
    data = json.loads(HINTS_FILE.read_text(encoding="utf-8"))
    assert {h["id"] for h in data["hints"]} == {"talaq", "khula", "dower", "maintenance", "custody", "inheritance",
                                                  "nikah_registration"}
    banned = re.compile(r"\b(void|invalid|illegal|unlawful|punishable|penalty|entitled|must|shall|cannot|can|may|"
                        r"not|valid|right|liable|guilty|compulsory)\b", re.I)
    for h in data["hints"]:
        assert not banned.search(h["terms"]), (h["id"], banned.search(h["terms"]).group(0))


def test_expand_appends_terms_and_keeps_the_question():
    q = "What is the procedure for talaq?"
    out = query_hints.expand(q)
    assert out.startswith(q + " ") and "union council" in out and "notice" in out


def test_hints_apply_only_with_kb_v2_and_the_switch(monkeypatch):
    seen = []
    monkeypatch.setattr(embeddings, "_search_v1", lambda q, k, f=None, **kw: seen.append(q) or [])
    from app.kb import index_v2
    monkeypatch.setattr(index_v2, "search", lambda q, k, f=None, **kw: seen.append(q) or [])
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    q = "What is the procedure for talaq?"
    monkeypatch.setattr(settings, "KB_V2", False)
    embeddings.search(q, 5)
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "QUERY_HINTS", False)
    embeddings.search(q, 5)
    monkeypatch.setattr(settings, "QUERY_HINTS", True)
    embeddings.search(q, 5)
    assert seen[0] == q and seen[1] == q and seen[2].startswith(q + " ") and "union council" in seen[2]


def test_missing_or_broken_file_means_no_hints(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "QUERY_HINTS_PATH", str(tmp_path / "none.json"))
    query_hints.reset()
    assert query_hints.expand("talaq procedure") == "talaq procedure"
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(settings, "QUERY_HINTS_PATH", str(tmp_path / "bad.json"))
    assert query_hints.expand("talaq procedure") == "talaq procedure"


# --------------------------------------------------------------------------- legal consequences

MFLO_5 = {"source": "Muslim Family Laws Ordinance, 1961", "section": "5", "text": (
    "(1) Every marriage solemnized under Muslim Law shall be registered in accordance with the provisions of this "
    "Ordinance. (2) For the purpose of registration of marriages under this Ordinance, the Union Council shall "
    "grant licences to one or more persons, to be called Nikah Registrars. (3) Every marriage not solemnized by the "
    "Nikah Registrar shall, for the purpose of registration under this Ordinance, be reported to him by the person "
    "who has solemnized such marriage. (4) Whoever contravenes the provisions of sub-section (3) shall be "
    "punishable with simple imprisonment for a term which may extent to three months, or with fine which may "
    "extend to one thousand rupees, or with both.")}


class FakeAI:
    def __init__(self, answer):
        self.answer, self.system = answer, None

    def chat(self, history, system=None):
        self.system = system
        return self.answer


OVERCLAIM = ("Short answer: every Muslim marriage must be registered [1]. A marriage that is not registered is void "
             "and the spouses are liable to imprisonment for 2 years.")
FAITHFUL = ("Short answer: every marriage solemnized under Muslim Law shall be registered [1]. If the Nikah "
            "Registrar did not solemnize it, the person who solemnized it must report it to him; failing to report "
            "is punishable with simple imprisonment up to three months, a fine up to one thousand rupees, or both [1].")


def test_registration_overclaim_is_flagged(monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", True)
    ai = FakeAI(OVERCLAIM)
    checked = chat.compose_answer(ai, [dict(MFLO_5, relevance=0.8)],
                                  [{"role": "user", "content": "Is it compulsory to register a nikah?"}], "en")
    assert "LEGAL CONSEQUENCES" in ai.system and "don't add what happens if it isn't done" in ai.system
    assert "(unverified)" not in checked.text and "is void and" in checked.text
    assert 'Legal consequence not stated in the retrieved text: "void"' in checked.unverified
    assert "Figure not in the retrieved text: 2 years" in checked.unverified


def test_registration_answer_that_says_only_what_the_text_says_passes(monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", True)
    checked = chat.compose_answer(FakeAI(FAITHFUL), [dict(MFLO_5, relevance=0.8)],
                                  [{"role": "user", "content": "Is it compulsory to register a nikah?"}], "en")
    assert checked.unverified == [] and "(unverified)" not in checked.text


def test_flag_off_prompt_and_check_unchanged(monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", False)
    ai = FakeAI(OVERCLAIM)
    checked = chat.compose_answer(ai, [dict(MFLO_5, relevance=0.8)],
                                  [{"role": "user", "content": "Is it compulsory to register a nikah?"}], "en")
    assert "LEGAL CONSEQUENCES" not in ai.system and "void (unverified)" not in checked.text
    assert check_citations(OVERCLAIM, [MFLO_5]).text == check_citations(OVERCLAIM, [MFLO_5], consequences=False).text
