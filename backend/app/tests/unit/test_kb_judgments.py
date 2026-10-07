"""kb-v2 C1: judgment parser, chunk rule and index builder (synthetic fixtures, offline)."""

import json
import re

import numpy as np
import pytest

from app.core.config import settings
from app.kb import judgments as jd

SC = """IN THE SUPREME COURT OF PAKISTAN
(Appellate Jurisdiction)

Present:
Mr. Justice Qazi Faez Isa, CJ
Mr. Justice Amin-ud-Din Khan, J.

Civil Petition No. 1234 of 2022
(Against the judgment of the Lahore High Court)

Mst. Ayesha Bibi ...Petitioner
versus
Muhammad Aslam and others ...Respondents

Date of hearing: 14.03.2023

JUDGMENT

1. This petition arises from a suit for recovery of dower and maintenance filed by the petitioner in the Family Court, which decreed the dower but dismissed the claim for past maintenance.

2. The learned counsel for the petitioner submits that the Family Court misread the nikahnama; the dower was prompt and payable on demand, and maintenance was due for the whole period.

3. We have heard the learned counsel and examined the record. The nikahnama records the dower as prompt. A wife is entitled to maintenance during the subsistence of the marriage; the Family Court erred in refusing it for the period after the suit was filed.

4. The petition is converted into an appeal and allowed. The dower and maintenance are decreed as prayed.

Judge
"""

LAW_REPORT = """2023 SCMR 456
[Supreme Court of Pakistan]
Present: Umar Ata Bandial, C.J. and Ijaz ul Ahsan, J.
HEADNOTE
(a) Muslim Family Laws Ordinance (VIII of 1961)---S. 10---Dower---Prompt dower payable on demand.
Cases referred: PLD 2015 SC 123.
""" + ("1. The facts are these. " * 200)

STUB = "Order sheet. Adjourned."


def test_metadata_from_the_first_page():
    m = jd.metadata(SC)
    assert m["court"] == "Supreme Court of Pakistan"
    assert m["case_number"] == "Civil Petition No. 1234 of 2022"
    assert m["year"] == 2023
    assert m["case_name"] == "Mst. Ayesha Bibi v. Muhammad Aslam and others"
    assert any("Qazi Faez Isa" in j for j in m["judges"]) and any("Amin-ud-Din Khan" in j for j in m["judges"])
    assert {"dower", "maintenance", "family", "nikah"} <= set(m["topics"])
    assert m["citation"] is None                        # no neutral citation; publisher cites are never copied


def test_metadata_fields_are_none_when_not_found():
    m = jd.metadata("Some text without any heading. " * 80)
    assert (m["case_name"], m["court"], m["year"], m["case_number"]) == (None, None, None, None)
    assert m["judges"] == [] and m["topics"] == []


def test_numbered_paragraphs_keep_their_numbers():
    paras = jd.paragraphs(SC)
    nums = [p["n"] for p in paras]
    assert nums[0] == 0 and nums[1:] == [1, 2, 3, 4]       # 0 = heading, parties, bench
    assert paras[1]["text"].startswith("This petition arises") and "\n" not in paras[1]["text"]


def test_unnumbered_text_falls_back_to_blocks():
    text = "First block of reasoning about the custody of the minor.\n\nSecond block about the guardian's duties.\n\nok"
    assert [p["n"] for p in jd.paragraphs(text)] == [1, 2]   # "ok" is too short to keep


@pytest.mark.parametrize("text,info,why", [
    (SC * 2, {"pages": None}, None),
    (STUB, {"pages": None}, "near-empty"),
    (LAW_REPORT, {"pages": None}, "law-report copy (publisher headnotes)"),
    ("x" * 3000, {"pages": 10, "pages_without_text": 8}, "needs OCR"),
])
def test_quality_flags(text, info, why):
    assert jd.quality(text, info)["exclude"] == why


def test_record_has_spec_fields_and_provenance(tmp_path):
    f = tmp_path / "cp_1234_2022.txt"
    f.write_text(SC * 2, encoding="utf-8")
    text, info = jd.read_text(f)
    rec = jd.make_record(f, text, info, source="Supreme Court txt")
    assert jd.validate(rec) == []
    assert rec["source_type"] == "case_law" and rec["provenance_note"] == jd.PROVENANCE
    assert rec["file_sha256"] == jd.sha256_file(f) and rec["original_file"] == str(f)
    assert rec["doc_id"].startswith("judgment/supreme-court-txt/")
    assert jd.validate({**rec, "source_type": "statute"}) == ["source_type must be case_law"]


def test_pdf_text_and_ocr_flag(tmp_path):
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "IN THE SUPREME COURT OF PAKISTAN. Civil Appeal No. 5 of 2020.", fontsize=10)
    doc.new_page()                                          # a page with no text layer
    doc.new_page()
    p = tmp_path / "j.pdf"
    doc.save(p)
    text, info = jd.read_text(p)
    assert "SUPREME COURT" in text and info == {"format": "pdf", "pages": 3, "pages_without_text": 2}
    assert jd.quality(text, info)["needs_ocr"] is True


class WordTokenizer:
    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        spans = [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]
        out = {"input_ids": list(range(len(spans)))}
        if return_offsets_mapping:
            out["offset_mapping"] = spans
        return out


def _rec(tmp_path, name="a.txt", body=SC * 3):
    f = tmp_path / name
    f.write_text(body, encoding="utf-8")
    text, info = jd.read_text(f)
    return jd.make_record(f, text, info, source="test")


def test_chunks_stay_in_one_paragraph_with_prefix_inside_the_limit(tmp_path):
    rec = _rec(tmp_path)
    rec["paragraphs"].append({"n": 9, "text": " ".join(f"word{i}" for i in range(600))})
    chunks = jd.make_chunks([rec], WordTokenizer())
    tok = WordTokenizer()
    assert all(len(tok(c["chunk_text"])["input_ids"]) <= 120 for c in chunks)
    para9 = [c for c in chunks if c["para"] == 9]
    assert len(para9) > 5
    assert all(c["chunk_text"].startswith("Mst. Ayesha Bibi v. Muhammad Aslam and others (Supreme Court of "
                                          "Pakistan, 2023) - para 9:") for c in para9)
    assert all("word" in c["chunk_text"] and "This petition" not in c["chunk_text"] for c in para9)


def test_chunk_rule_with_the_real_tokenizer(tmp_path):
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(f"sentence-transformers/{settings.EMBEDDING_MODEL_NAME}",
                                            local_files_only=True)
    except Exception:  # noqa: BLE001
        pytest.skip("embedding model tokenizer not cached")
    rec = _rec(tmp_path)
    rec["paragraphs"].append({"n": 7, "text": "The learned Family Court rightly held that the dower was prompt. " * 40})
    for c in jd.make_chunks([rec], tok):
        assert len(tok(c["chunk_text"], add_special_tokens=False)["input_ids"]) <= 120


def test_pilot_takes_family_law_first(tmp_path):
    fam = _rec(tmp_path, "fam.txt")
    other = _rec(tmp_path, "crim.txt", body=SC.replace("dower", "theft").replace("maintenance", "sentence")
                 .replace("Family Court", "trial court").replace("nikahnama", "FIR") * 3)
    stub = _rec(tmp_path, "stub.txt", body=STUB)
    picked = jd.select_pilot([other, stub, fam], n=2)
    assert picked[0]["doc_id"] == fam["doc_id"] and stub not in picked and len(picked) == 2


def fake_embed(texts):
    out = np.zeros((len(texts), 384), np.float32)
    for i, t in enumerate(texts):
        for w in re.findall(r"\w+", t.lower()):
            out[i, hash(w) % 384] += 1.0
        out[i] /= max(np.linalg.norm(out[i]), 1e-9)
    return out


def test_builder_is_incremental_resumable_and_refuses_statute_indexes(tmp_path, monkeypatch):
    import faiss
    d = tmp_path / "records"
    d.mkdir()
    rec = _rec(tmp_path)
    (d / "pilot.jsonl").write_text(json.dumps(rec), encoding="utf-8")
    calls = []

    def embed(texts):
        calls.append(len(texts))
        return fake_embed(texts)
    m = jd.build_index(d, tmp_path / "j.faiss", tmp_path / "j.json", tokenizer=WordTokenizer(), embed=embed,
                      checkpoint=2, time_budget=0.0)
    assert m["complete"] is False and not (tmp_path / "j.faiss").exists()
    m = jd.build_index(d, tmp_path / "j.faiss", tmp_path / "j.json", tokenizer=WordTokenizer(), embed=embed,
                      checkpoint=2)
    assert m["complete"] and faiss.read_index(str(tmp_path / "j.faiss")).ntotal == m["chunks"]
    assert all(n <= 2 for n in calls)
    n_calls = len(calls)
    m = jd.build_index(d, tmp_path / "j.faiss", tmp_path / "j.json", tokenizer=WordTokenizer(), embed=embed)
    assert len(calls) == n_calls and m["reused_vectors"] == m["chunks"]            # nothing re-embedded
    meta = json.loads((tmp_path / "j.json").read_text(encoding="utf-8"))
    assert meta["chunks"][0]["source_type"] == "case_law" and meta["chunks"][0]["doc_id"] == rec["doc_id"]
    m = jd.build_index(d, tmp_path / "k.faiss", tmp_path / "k.json", tokenizer=WordTokenizer(), embed=embed,
                      max_chunks=3)
    assert m["chunks"] == 3
    for path_setting in ("FAISS_INDEX_PATH", "KB_V2_INDEX_PATH"):
        monkeypatch.setattr(settings, path_setting, str(tmp_path / "statute.faiss"))
        with pytest.raises(ValueError):
            jd.build_index(d, tmp_path / "statute.faiss", tmp_path / "x.json", tokenizer=WordTokenizer(),
                          embed=embed)


def test_inventory_script_end_to_end(tmp_path, monkeypatch):
    import importlib.util
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location("inv", root / "scripts" / "kb" / "inventory_judgments.py")
    inv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inv)
    monkeypatch.setattr(inv, "OUT", tmp_path / "out")
    src = tmp_path / "data"
    src.mkdir()
    (src / "a.txt").write_text(SC * 2, encoding="utf-8")
    (src / "a_copy.txt").write_text(SC * 2, encoding="utf-8")           # duplicate text
    (src / "stub.txt").write_text(STUB, encoding="utf-8")
    (src / "report.txt").write_text(LAW_REPORT, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["inv", "--source", "Test SC", str(src)])
    assert inv.main() == 0
    data = json.loads((tmp_path / "out" / "inventory_test-sc.json").read_text(encoding="utf-8"))
    assert data["files"] == 4 and data["kept"] == 1 and data["duplicate_text"] == 1
    assert data["excluded"] == {"near-empty": 1, "law-report copy (publisher headnotes)": 1,
                                "duplicate (same text)": 1}
    assert data["extraction_rate"]["court"] == 0.75 and data["law_report_files"][0].endswith("report.txt")
    lines = (tmp_path / "out" / "records" / "test-sc.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4 and all(jd.validate(json.loads(x)) == [] for x in lines)
