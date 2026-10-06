"""kb-v2 Phase B3: schedule items, community gating, incremental builds, KB_V2_THRESHOLD."""

import json
import re

import numpy as np
import pytest

from app.ai import embeddings
from app.core.config import settings
from app.kb import index_v2
from app.kb.records import CORPUS_SOURCE, make_records, validate
from app.kb.sectioner import Section, list_items, split_schedule_items

faiss = pytest.importorskip("faiss")

FCA_SCHEDULE = ("[see SECTION 5] [PART I] 1. Dissolution of marriage [including Khula]. 2. Dower. 3. Maintenance. "
                "4. Restitution of conjugal rights. 5. Custody of children [, and the visitation rights of parents "
                "to meet them]. 6. Guardian ship. [7. Jactitation of marriage.] [8. Dowry.] [9. Personal property "
                "and belongings of a wife.] PART II Offences and aid and abetment thereof under Section 337A (i), "
                "341 and 509 of the Pakistan Penal Code (Act XLV of l860)]")
FORM = ("(See section 12) NOTICE OF MARRIAGE To a Minister of I hereby give you notice that a marriage is "
        "intended to be had within three months from the date hereof between me and the other party herein "
        "named and described (that is to say) Name and surname, Condition, Rank or profession, Age, Dwelling.")
RULES = ("ORDER I PARTIES TO SUITS 1. Who may be joined as plaintiffs. All persons may be joined in one suit as "
         "plaintiffs in whom any right to relief in respect of, or arising out of, the same act or transaction is "
         "alleged to exist, whether jointly, severally or in the alternative, where, if such persons brought "
         "separate suits, any common question of law or fact would arise; and judgment may be given for such one "
         "or more of the plaintiffs as may be found to be entitled to relief, for such relief as he or they may be "
         "entitled to, without any amendment, provided always that the court may order separate trials where it "
         "appears that the joinder may embarrass or delay the trial of the suit, and may make any order it thinks "
         "fit in the interests of justice in respect of the parties so joined. 2. Power of Court to order separate "
         "trial. Where it appears to the Court that any joinder of plaintiffs may embarrass or delay the trial.")


# --------------------------------------------------------------------------- schedule items

def test_numbered_list_schedule_is_split_into_items():
    lead, items, rest = list_items(FCA_SCHEDULE)
    assert [n for n, _ in items] == [str(i) for i in range(1, 10)]
    assert items[1] == ("2", "Dower")
    assert items[3] == ("4", "Restitution of conjugal rights")
    assert items[0][1] == "Dissolution of marriage [including Khula]"      # brackets balanced
    assert rest.startswith("PART II Offences")


def test_forms_and_long_rules_are_left_alone():
    assert list_items(FORM) is None
    assert list_items(RULES) is None                     # only 2 items, and the first is too long
    assert list_items("1. Dower. 2. Maintenance.") is None   # fewer than 3 items
    assert list_items("1. Dower. 3. Maintenance. 4. Dowry.") is None   # a gap: not reliably numbered


def test_split_schedule_items_records():
    secs, labels = split_schedule_items([Section("5", "Jurisdiction", "text"), Section("Schedule", None, FCA_SCHEDULE),
                                         Section("Schedule 2", None, FORM)])
    assert labels == ["Schedule"]
    ids = [s.section for s in secs]
    assert ids[:2] == ["5", "Schedule item 1"] and "Schedule item 9" in ids
    assert ids[-2:] == ["Schedule Part II", "Schedule 2"]
    item4 = next(s for s in secs if s.section == "Schedule item 4")
    assert item4.heading == "Restitution of conjugal rights"
    item5 = next(s for s in secs if s.section == "Schedule item 5")
    assert item5.heading == "Custody of children, and the visitation rights of parents to meet them"
    meta = {"title": "West Pakistan Family Courts Act, 1964", "year": 1964, "category": None, "act_number": None,
            "status": "current", "source": CORPUS_SOURCE, "source_tier": 2, "source_url": None,
            "original_file": None, "scraped_at": None, "jurisdiction": "Pakistan"}
    recs = make_records(meta, secs)
    r4 = next(r for r in recs if r["section"] == "Schedule item 4")
    assert r4["doc_id"].endswith("/schedule-item-4") and validate(r4) == [] and r4["audience"] == "general"
    assert index_v2.prefix_for(r4) == ("West Pakistan Family Courts Act, 1964 - Schedule item 4 "
                                       "Restitution of conjugal rights:")


# --------------------------------------------------------------------------- community gating

@pytest.mark.parametrize("question,audience,title,shown", [
    ("What are the grounds for divorce?", "Christian", "Divorce Act, 1869", False),
    ("Can a husband marry a second wife without permission?", "Christian", "Christian Marriage Act, 1872", False),
    ("How can a Christian wife get a divorce?", "Christian", "Divorce Act, 1869", True),
    ("What does the Divorce Act, 1869 say about adultery?", "Christian", "Divorce Act, 1869", True),
    ("What does the divorce act say?", "Christian", "Divorce Act, 1869", False),     # 1-word name needs the year
    ("Who can marry under the Special Marriage Act?", "non-Muslim (other faiths)", "Special Marriage Act, 1872", True),
    ("Rules for a Zoroastrian marriage", "Parsi", "Parsi Marriage and Divorce Act, 1936", True),
    ("Anand karaj registration", "Sikh", "Anand Marriage Act, 1909", True),
    ("Can a non-Muslim wife keep her earnings?", "non-Muslim (Christian, Parsi and others)",
     "Married Women's Property Act, 1874", True),
    ("Can a wife keep her earnings?", "non-Muslim (Christian, Parsi and others)",
     "Married Women's Property Act, 1874", False),
    ("ہندو بیوہ کی دوسری شادی", "Hindu", "Hindu Widows' Re-marriage Act, 1856", True),
    ("Any question at all", "general", "Muslim Family Laws Ordinance, 1961", True),
    ("Any question at all", None, "Pakistan Penal Code, 1860", True),
])
def test_names_audience(question, audience, title, shown):
    assert index_v2.names_audience(question, audience, title) is shown


def fake_embed(texts):
    out = np.zeros((len(texts), 384), np.float32)
    for i, t in enumerate(texts):
        for w in re.findall(r"\w+", t.lower()):
            out[i, hash(w) % 384] += 1.0
        out[i] /= max(np.linalg.norm(out[i]), 1e-9)
    return out


class WordTokenizer:
    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        spans = [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]
        out = {"input_ids": list(range(len(spans)))}
        if return_offsets_mapping:
            out["offset_mapping"] = spans
        return out


META = {"year": 1869, "category": "Family Laws", "act_number": None, "status": "current", "source": CORPUS_SOURCE,
        "source_tier": 1, "source_url": None, "original_file": None, "scraped_at": None, "jurisdiction": "Pakistan"}


def write_records(d, extra=""):
    d.mkdir(exist_ok=True)
    christian = make_records({**META, "title": "Divorce Act, 1869", "audience": "Christian"},
                             [Section("10", "When husband may petition for dissolution",
                                      "husband wife petition dissolution of marriage adultery divorce" + extra)])
    muslim = make_records({**META, "title": "Dissolution of Muslim Marriages Act, 1939", "year": 1939},
                          [Section("2", "Grounds for decree for dissolution of marriage",
                                   "woman married dissolution of marriage grounds maintenance cruelty")])
    (d / "a.jsonl").write_text("\n".join(json.dumps(r) for r in christian + muslim), encoding="utf-8")
    return d


@pytest.fixture
def kb(tmp_path, monkeypatch):
    d = write_records(tmp_path / "records")
    index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=fake_embed,
                   excluded_v1_sources=[])
    monkeypatch.setattr(embeddings, "_INDEX", None)
    monkeypatch.setattr(embeddings, "_META", [])
    monkeypatch.setattr(embeddings, "embed", fake_embed)
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "KB_V2_INDEX_PATH", str(tmp_path / "v2.faiss"))
    monkeypatch.setattr(settings, "KB_V2_METADATA_PATH", str(tmp_path / "v2.json"))
    index_v2.reset()
    yield tmp_path
    index_v2.reset()


def test_question_naming_no_community_gets_no_community_law(kb):
    hits = embeddings.search("husband wife petition dissolution of marriage adultery divorce", top_k=5)
    assert [h["source"] for h in hits] == ["Dissolution of Muslim Marriages Act, 1939"]


def test_question_naming_the_community_gets_it(kb):
    hits = embeddings.search("christian husband wife petition dissolution of marriage adultery divorce", top_k=5)
    assert hits[0]["source"] == "Divorce Act, 1869" and hits[0]["audience"] == "Christian"


# --------------------------------------------------------------------------- incremental build

def counting(embed_fn):
    calls = []

    def f(texts):
        calls.append(len(texts))
        return embed_fn(texts)
    f.calls = calls
    return f


def test_rebuild_reuses_vectors_and_embeds_only_changes(tmp_path):
    d = write_records(tmp_path / "records")
    e1 = counting(fake_embed)
    m1 = index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=e1,
                        excluded_v1_sources=[])
    assert m1["complete"] and sum(e1.calls) == m1["chunks"] == 2
    before = faiss.read_index(str(tmp_path / "v2.faiss")).reconstruct_n(0, 2)
    write_records(tmp_path / "records", extra=" changed")          # one record's text changes
    e2 = counting(fake_embed)
    m2 = index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=e2,
                        excluded_v1_sources=[])
    assert sum(e2.calls) == 1 and m2["reused_vectors"] == 1 and m2["embedded_now"] == 1
    after = faiss.read_index(str(tmp_path / "v2.faiss")).reconstruct_n(0, 2)
    assert np.allclose(before[1], after[1]) and not np.allclose(before[0], after[0])


def test_cache_seeded_from_an_existing_index(tmp_path):
    d = write_records(tmp_path / "records")
    index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=fake_embed,
                   excluded_v1_sources=[], cache_dir=tmp_path / "cache_a")
    e = counting(fake_embed)
    m = index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=e,
                       excluded_v1_sources=[], cache_dir=tmp_path / "cache_b")      # empty cache, old index
    assert m["seeded_from_previous"] == 2 and sum(e.calls) == 0


def test_build_stops_at_the_budget_and_resumes(tmp_path):
    d = tmp_path / "records"
    d.mkdir()
    recs = make_records({**META, "title": "Big Act, 1900", "year": 1900},
                        [Section(str(i), f"Heading {i}", f"text number {i} " * 5) for i in range(1, 26)])
    (d / "big.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    e = counting(fake_embed)
    m = index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=e,
                       excluded_v1_sources=[], checkpoint=10, time_budget=0.0)
    assert not m["complete"] and m["still_missing"] == 25 and not (tmp_path / "v2.faiss").exists()
    m = index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=e,
                       excluded_v1_sources=[], checkpoint=10)
    assert m["complete"] and e.calls == [10, 10, 5]                 # checkpointed batches
    assert len(list((tmp_path / "vector_cache").glob("shard_*.npz"))) == 3
    e2 = counting(fake_embed)
    index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=e2,
                   excluded_v1_sources=[], checkpoint=10)
    assert e2.calls == []


# --------------------------------------------------------------------------- threshold

def test_threshold_setting_only_applies_with_kb_v2(monkeypatch):
    monkeypatch.setattr(settings, "KB_V2_THRESHOLD", 0.60)
    monkeypatch.setattr(settings, "KB_V2", False)
    assert embeddings.similarity_threshold() == settings.RAG_SIMILARITY_THRESHOLD == 0.65
    monkeypatch.setattr(settings, "KB_V2", True)
    assert embeddings.similarity_threshold() == 0.60


def test_threshold_default_is_unchanged():
    from app.core.config import Settings
    assert Settings.model_fields["KB_V2_THRESHOLD"].default == 0.65
    assert Settings.model_fields["KB_V2"].default is False
