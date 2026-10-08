"""kb-v2 C17: scraped copies of core laws left out, and a small core-law priority, in scraped.merged_search."""

import pytest

from app.core.config import settings
from app.kb import catalog, index_v2, scraped


@pytest.mark.parametrize("a, b, same", [
    ("Code of Criminal Procedure (CrPC), 1898 (Under Review)", "Code of Criminal Procedure, 1898", True),
    ("Code of Civil Procedure (CPC) , 1908 (Under Review)", "Code of Civil Procedure, 1908", True),
    ("The Pakistan Penal Code (XLV of 1860), 1860", "Pakistan Penal Code, 1860", True),
    ("Customs Act, 1969 (Same as on the official website of FBR dated 30-06-2025)", "Customs Act, 1969", True),
    ("Limitation (Emergency and War Conditions) Act, 1965", "Limitation Act, 1908", False),   # descriptive bracket
    ("Arbitration Act, 2011", "Arbitration Act, 1940", False),                                 # another year
    ("West Pakistan Muslim Personal Law (Shariat) Application Act, 1962",
     "West Pakistan Muslim Personal Law Application Act, 1962", False),
])
def test_title_key(a, b, same):
    assert (scraped.title_key(a) == scraped.title_key(b)) is same


CORE_LAW = {"title": "Code of Criminal Procedure, 1898", "set": "core", "record_ids": ["core/crpc/s61", "core/crpc/s50"]}
CORPUS_LAW = {"title": "Railways Act, 1890", "set": "corpus", "record_ids": ["corpus/railways/s5"]}


def _hit(doc_id, source, score, kb):
    return {"doc_id": doc_id, "source": source, "relevance": score, "kb": kb, "text": "t"}


@pytest.fixture
def merged(monkeypatch):
    data = {"laws": {"crpc": CORE_LAW, "railways": CORPUS_LAW}, "records": {}}
    monkeypatch.setattr(catalog, "data", lambda: data)
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    monkeypatch.setattr(settings, "CORE_PRIORITY", 0.03)
    monkeypatch.setattr(scraped._INDEX, "ready", lambda: True)
    monkeypatch.setattr(scraped._INDEX, "excluded", frozenset())
    base = [_hit("core/crpc/s61", "Code of Criminal Procedure, 1898", 0.70, "v2"),
            _hit("corpus/railways/s5", "Railways Act, 1890", 0.705, "v2")]
    extra = [_hit("pakistan-code/crpc-under-review/s61", "Code of Criminal Procedure (CrPC), 1898 (Under Review)",
                  0.76, "scraped"),
             _hit("pakistan-code/customs-act-1969/s161", "Customs Act, 1969", 0.72, "scraped")]
    monkeypatch.setattr(index_v2, "search", lambda q, k, f=None, hint_ids=None: [dict(h) for h in base])
    monkeypatch.setattr(scraped, "search_statutes", lambda q, k, f=None: [dict(h) for h in extra])
    return lambda: scraped.merged_search("arrest without warrant", 5)


def test_scraped_copy_of_a_core_law_is_left_out(merged):
    assert "pakistan-code/crpc-under-review/s61" not in [h["doc_id"] for h in merged()]


def test_core_sections_win_a_near_tie_and_scores_are_unchanged(merged):
    hits = merged()
    assert [h["doc_id"] for h in hits] == ["core/crpc/s61", "pakistan-code/customs-act-1969/s161",
                                           "corpus/railways/s5"]           # 0.70 + 0.03 beats 0.72; corpus gets none
    assert [h["relevance"] for h in hits] == [0.70, 0.72, 0.705]            # the gate still sees the real scores


def test_priority_zero_is_the_plain_score_order(merged, monkeypatch):
    monkeypatch.setattr(settings, "CORE_PRIORITY", 0.0)
    assert [h["doc_id"] for h in merged()][:2] == ["pakistan-code/customs-act-1969/s161", "corpus/railways/s5"]


def test_without_the_scraped_index_nothing_changes(merged, monkeypatch):
    monkeypatch.setattr(scraped._INDEX, "ready", lambda: False)
    assert [h["doc_id"] for h in merged()] == ["core/crpc/s61", "corpus/railways/s5"]
