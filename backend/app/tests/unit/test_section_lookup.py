"""TOC-guided section lookup (app/ai/section_lookup.py), on a small fake
index shaped like the real MFLO chunks: a CSV copy ("Section 6 — Polygamy")
and a PDF copy with a contents list and OCR damage ("7. Tala q.—")."""

import pytest

from app.ai import embeddings, section_lookup

TOC_TEXT = ("Page 1 of 7 THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 CONTENTS SECTIONS : "
            "1. Short title, extent, application and commencement . 2. Definition s. "
            "5. Registration of marriage s. 6. Polygamy . 7. Talaq . "
            "8. Dissolution of marriage otherwise than by talaq . 9. Maintenance .")

META = [
    {"source": "Muslim Family Laws Ordinance, 1961",                # 0 CSV s1
     "text": "Chapter I — Muslim Family Laws Ordinance 1961 Section 1 — Short title (1) This Ordinance may be called"},
    {"source": "Muslim Family Laws Ordinance, 1961",                # 1 CSV s5 end + s6 heading
     "text": "(5) The form of nikahnama shall be prescribed. Section 6 — Polygamy (1) No man, during the subsistence"},
    {"source": "Muslim Family Laws Ordinance, 1961",                # 2 CSV s6 continued
     "text": "of an existing marriage, shall, except with the previous permission in writing of the Arbitration Council"},
    {"source": "THE MUSLIM FAMILY LAWS ORDINAN CE, 1961", "text": TOC_TEXT},   # 3 PDF contents list
    {"source": "THE MUSLIM FAMILY LAWS ORDINAN CE, 1961",           # 4 PDF s7 heading, OCR-split
     "text": "with fine which may extend to five thous and rupees, or with both. 7. Tala q.—(1) Any man who wish es to divorce"},
    {"source": "THE MUSLIM FAMILY LAWS ORDINAN CE, 1961",           # 5 PDF s7 continued
     "text": "his wife shall, as soon as may be after the pronoun cement of talaq, give the Chairman notice in writing"},
    {"source": "Pakistan Penal Code",                               # 6 another statute
     "text": "Section 6 — Definitions in the Code to be understood subject to exceptions"},
]


@pytest.fixture
def fake_index(monkeypatch):
    monkeypatch.setattr(embeddings, "_META", META)
    section_lookup._chunks_by_statute.cache_clear()
    yield
    section_lookup._chunks_by_statute.cache_clear()


def _retrieved(*ids, score=0.75):
    return [{**META[i], "relevance": score} for i in ids]


def _texts(records):
    return [META.index({k: v for k, v in r.items() if k in ("source", "text")}) for r in records]


def test_toc_detection():
    assert section_lookup.is_toc(TOC_TEXT)
    assert not section_lookup.is_toc(META[1]["text"])


def test_topic_word_follows_toc_to_section_text(fake_index):
    extra = section_lookup.section_passages("What are the legal restrictions on polygamy?", _retrieved(3, 0))
    assert _texts(extra) == [1, 2]                      # heading chunk + continuation
    assert all(e["via_toc"] == "6. Polygamy" for e in extra)


def test_explicit_section_number(fake_index):
    extra = section_lookup.section_passages("What is Section 6 of MFLO?", _retrieved(3))
    assert _texts(extra) == [1, 2]


def test_ocr_split_heading_in_other_copy_is_found(fake_index):
    # "7. Tala q.—" only exists in the PDF copy
    extra = section_lookup.section_passages("procedure for talaq under Section 7", _retrieved(3))
    assert _texts(extra) == [4, 5]


def test_toc_chunk_itself_never_refetched(fake_index):
    extra = section_lookup.section_passages("Section 6 polygamy", _retrieved(3))
    assert 3 not in _texts(extra)


def test_other_statutes_section_with_same_number_not_used(fake_index):
    # PPC also has a "Section 6 —" heading; only the TOC's own statute counts
    extra = section_lookup.section_passages("What is Section 6?", _retrieved(3))
    assert 6 not in _texts(extra)


def test_already_retrieved_chunks_not_duplicated(fake_index):
    extra = section_lookup.section_passages("polygamy", _retrieved(3, 1))
    assert _texts(extra) == [2]


def test_no_toc_retrieved_means_no_lookup(fake_index):
    assert section_lookup.section_passages("polygamy", _retrieved(0, 6)) == []


def test_unrelated_question_matches_no_entry(fake_index):
    assert section_lookup.section_passages("What is the weather today?", _retrieved(3)) == []


def test_dotless_toc_entries_are_parsed():
    # DMMA 1939's contents list numbers entries without a dot
    toc = ("THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 CONTENTS PREAMBLE. 1 Short title and "
           "extent. 2 Grounds for decree for dissolution of marriage. 3Notice to be served on heirs.")
    assert ("2", "Grounds for decree for dissolution of marriage") in section_lookup.toc_entries(toc)


def test_page_headers_are_not_entries():
    # "Page 1 of 7 THE ..." must not become a bogus entry 7 (7 is Talaq)
    toc = ("Page 1 of 7 THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 CONTENTS SECTIONS : 1. Short "
           "title . 6. Polygamy . 7. Talaq . 8. Dissolution of marriage .")
    entries = section_lookup.toc_entries(toc)
    assert [n for n, _ in entries] == ["1", "6", "7", "8"]
    assert ("7", "Talaq") in entries


def test_title_words_come_from_the_question_not_the_rewrite():
    # A real false positive: the rewrite added "Transfer of Property Act",
    # whose word "transfer" matched an unrelated Land Reforms Act entry.
    entries = [("5", "Partitioning of joint holdings"), ("6", "Certain transfers void")]
    question = "The land we bought was replatted and the road moved; do we keep access?"
    rewrite = "easement of access claim after road realignment under Transfer of Property Act 1882"
    assert section_lookup.pick_entries(question, entries, rewrite) == []


def test_section_number_from_the_rewrite_still_counts():
    entries = [("6", "Polygamy"), ("7", "Talaq")]
    assert section_lookup.pick_entries("how is talaq done?", entries, "MFLO Section 7 talaq") == [("7", "Talaq")]


def test_generic_title_words_do_not_match():
    entries = section_lookup.toc_entries(TOC_TEXT)
    # "title", "extent", "application" are in the stop list
    assert section_lookup.pick_entries("short title and extent of application", entries) == []
