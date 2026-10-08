"""kb-v2 C19: the core search's first CORE_KEEP_TOP results keep their places in scraped.merged_search."""

import pytest

from app.core.config import settings
from app.kb import catalog, index_v2, scraped


def _hit(doc_id, source, score, kb):
    return {"doc_id": doc_id, "source": source, "relevance": score, "kb": kb, "text": "t"}


# The core search's own (hybrid) order: s302 first although its vector score is lower than s108's.
BASE = [_hit("core/ppc/s302", "Pakistan Penal Code, 1860", 0.71, "v2"),
        _hit("core/ppc/s308", "Pakistan Penal Code, 1860", 0.70, "v2"),
        _hit("core/ppc/s322", "Pakistan Penal Code, 1860", 0.72, "v2"),
        _hit("core/ppc/s108", "Pakistan Penal Code, 1860", 0.83, "v2")]
EXTRA = [_hit("pc/army-act/s60", "Pakistan Army Act, 1952", 0.77, "scraped"),
         _hit("pc/army-act/s142", "Pakistan Army Act, 1952", 0.76, "scraped"),
         _hit("pc/clra/s11", "Pakistan Criminal Law Amendment Act, 1958", 0.75, "scraped")]


@pytest.fixture
def merged(monkeypatch):
    ids = [h["doc_id"] for h in BASE]
    data = {"laws": {"ppc": {"title": "Pakistan Penal Code, 1860", "set": "core", "record_ids": ids}}, "records": {}}
    monkeypatch.setattr(catalog, "data", lambda: data)
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    monkeypatch.setattr(settings, "CORE_PRIORITY", 0.03)
    monkeypatch.setattr(settings, "CORE_KEEP_TOP", 2)
    monkeypatch.setattr(scraped._INDEX, "ready", lambda: True)
    monkeypatch.setattr(scraped._INDEX, "excluded", frozenset())
    monkeypatch.setattr(index_v2, "search", lambda q, k, f=None, hint_ids=None: [dict(h) for h in BASE])
    monkeypatch.setattr(scraped, "search_statutes", lambda q, k, f=None: [dict(h) for h in EXTRA])
    return lambda k=5: [h["doc_id"] for h in scraped.merged_search("murder punishment", k)]


def test_core_top_two_keep_places_one_and_two_against_higher_scraped_scores(merged):
    assert merged()[:2] == ["core/ppc/s302", "core/ppc/s308"]          # 0.71 / 0.70 stay above 0.77 / 0.76


def test_the_rest_are_still_merged_by_score(merged):
    # after the head: s108 0.83+0.03, army s60 0.77, army s142 0.76, s322 0.72+0.03=0.75 (tie with clra 0.75)
    assert merged(7)[2:5] == ["core/ppc/s108", "pc/army-act/s60", "pc/army-act/s142"]


def test_keep_top_zero_is_the_old_score_order(merged, monkeypatch):
    monkeypatch.setattr(settings, "CORE_KEEP_TOP", 0)
    assert merged() == ["core/ppc/s108", "pc/army-act/s60", "pc/army-act/s142", "core/ppc/s322", "pc/clra/s11"]


def test_scores_are_unchanged(monkeypatch, merged):
    hits = scraped.merged_search("murder punishment", 3)
    assert [h["relevance"] for h in hits] == [0.71, 0.70, 0.83]
