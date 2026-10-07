"""kb-v2 C3: file-staged scraping, validation and quarantine, the scraped
index, SCRAPED_V2 search and the update log. Saved HTML and PDF fixtures; a
stand-in HTTP session (no network), a stand-in tokenizer and embedding."""

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from app.ai import embeddings
from app.core.config import settings
from app.kb import catalog, judgment_catalog, judgment_search, scraped
from app.main import app
from app.middlewares.auth import get_current_user
from app.scraping import kb_run, stage
from app.scraping.fetcher import Fetcher

ROOT = Path(__file__).resolve().parents[4]
FIX = Path(__file__).resolve().parents[1] / "fixtures" / "scraping"
PDFS = FIX / "c3"
SOURCES = {s["name"]: s for s in json.loads((ROOT / "scripts/scraping/sources.json").read_text(encoding="utf-8"))}
KP, FSC, PC = SOURCES["Khyber Pakhtunkhwa Code"], SOURCES["Federal Shariat Court"], SOURCES["Pakistan Code"]
API = settings.API_V1_PREFIX


def pdf(name):
    return (PDFS / f"{name}.pdf").read_bytes()


class Resp:
    def __init__(self, url, content, ctype, status=200):
        self.url, self.content, self.status_code = url, content, status
        self.headers = {"content-type": ctype}
        self.text = content.decode("utf-8", "replace") if isinstance(content, bytes) else content


class FakeSession:
    """URL -> (bytes, content type); robots.txt is a 404 (allowed); anything else a 404."""

    def __init__(self, pages):
        self.pages, self.headers, self.calls = dict(pages), {}, []

    def get(self, url, timeout=None, allow_redirects=True):
        self.calls.append(url)
        if url in self.pages:
            content, ctype = self.pages[url]
            return Resp(url, content, ctype)
        return Resp(url, b"not found", "text/html", 404)


def fetcher(pages):
    return Fetcher(max_pages=500, max_pdfs=200, delay=0, session=FakeSession(pages), sleep=lambda s: None)


KP_LIST = KP["listing_urls"][0]
LAW = "https://kpcode.kp.gov.pk/homepage/lawDetails/"


def law_page(pdf_url):
    return f'<html><body><a href="{pdf_url}">Download</a></body></html>'.encode()


def kp_site(**pdfs):
    """The KP listing fixture's three laws (1619, 1618, 1617), each page linking to its PDF."""
    pages = {KP_LIST: ((FIX / "kpcode_recent.html").read_bytes(), "text/html")}
    for n, (name, data) in zip((1619, 1618, 1617), pdfs.items(), strict=False):
        url = f"https://kpcode.kp.gov.pk/uploads/{name}.pdf"
        pages[f"{LAW}{n}"] = (law_page(url), "text/html")
        pages[url] = (data, "application/pdf")
    return pages


@pytest.fixture
def kb(tmp_path, monkeypatch):
    d = tmp_path / "kb"
    (d / "records").mkdir(parents=True)
    core = {"doc_id": "legalease-corpus/contract-act-1872/s1", "title": "Contract Act, 1872", "section": "1",
            "heading": "Short title", "text": "This Act may be called the Contract Act, 1872."}
    (d / "records" / "contract-act-1872.jsonl").write_text(json.dumps(core) + "\n", encoding="utf-8")
    monkeypatch.setattr(settings, "KB_DIR", str(d))
    monkeypatch.chdir(tmp_path)
    for name in ("KB_SCRAPED_INDEX_PATH", "KB_SCRAPED_METADATA_PATH", "KB_SCRAPED_JUDGMENTS_INDEX_PATH",
                 "KB_SCRAPED_JUDGMENTS_METADATA_PATH"):
        monkeypatch.setattr(settings, name, str(d / Path(getattr(settings, name)).name))
    stage.reset_caches()
    scraped.reset()
    judgment_search.reset()
    judgment_catalog.reset()
    catalog.reset()
    yield d
    stage.reset_caches()
    scraped.reset()
    judgment_search.reset()
    judgment_catalog.reset()
    catalog.reset()


def quiet(_msg):
    pass


# --------------------------------------------------------------------------- validation units

@pytest.mark.parametrize("name, reason", [
    ("garbled", "garbled text"),
    ("scan", "no text layer"),
])
def test_unusable_text_is_named(name, reason):
    text, info = stage.pdf_text_info(pdf(name))
    assert stage.text_problem(text, info, 300).startswith(reason)


def test_near_empty_and_split_letters():
    assert stage.text_problem("Act 2025 short", {}, 300).startswith("near-empty text")
    spaced = " ".join("T h e A c t s h a l l a p p l y t o a l l p e r s o n s".split()) * 20
    assert "single letters" in stage.text_problem(spaced, {}, 50)
    text, info = stage.pdf_text_info(pdf("act"))
    assert stage.text_problem(text, info, 300) is None


def test_titles_years_and_amendments():
    assert stage.clean_title("Apprenticeship Ordinance, 1962 (Repeal by Act I of 2019,s.18)") == \
        ("Apprenticeship Ordinance, 1962", True)
    assert stage.clean_title("Women in Distress Act, 1996 (Repealed by Act XVI of 2020)")[1] is True
    assert stage.nice_title("THE KHYBER PAKHTUNKHWA FINANCE ACT, 2025.") == "The Khyber Pakhtunkhwa Finance Act, 2025"
    assert stage.year_of("Carriers Act, 1865") == 1865
    assert stage.year_of("Some Notice", "(KHYBER PAKHTUNKHWA ACT NO. IV OF 2025)") == 2025
    assert stage.year_of("Some Notice", "no year here") is None
    assert stage.document_type("Anti-Dumping Duties Ordinance, 2000") == "Ordinance"
    text, _ = stage.pdf_text_info(pdf("act"))
    assert stage.short_title(text) == "Khyber Pakhtunkhwa Trade Testing Board Act, 2025"
    assert stage.short_title("This Act may be called the 2 * Naturalization Act, 1926.") is None   # amendment marks
    assert stage.amendments(text) == ["Khyber Pakhtunkhwa Finance Act, 2025"]


# --------------------------------------------------------------------------- a staging run

def test_run_stages_quarantines_and_logs(kb):
    pages = kp_site(act=pdf("act"), garbled=pdf("garbled"), no_sections=pdf("no_sections"))
    f = fetcher(pages)
    s = kb_run.run([KP], f, caps={KP["name"]: 10}, log=quiet)
    e = s["per_source"][KP["name"]]
    assert (e["fetched"], e["new"], e["quarantined"], e["errors"]) == (3, 1, 2, 0) and s["complete"]
    # the act's records: section schema, source URL, fetch date, document type, amendments, provenance
    recs = [json.loads(x) for x in (kb / "scraped/records/statutes/khyber-pakhtunkhwa-trade-testing-board-act-2025.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    assert [r["section"] for r in recs] == ["1", "2", "3", "4", "5"]
    r = recs[0]
    assert r["title"] == "Khyber Pakhtunkhwa Trade Testing Board Act, 2025" and r["year"] == 2025
    assert r["jurisdiction"] == "KP" and r["source"] == "Khyber Pakhtunkhwa Code" and r["source_tier"] == 1
    assert r["source_url"] == f"{LAW}1619" and r["status"] == "under_review" and r["document_type"] == "Act"
    assert r["scraped_at"].endswith("Z") and r["amendments"] == ["Khyber Pakhtunkhwa Finance Act, 2025"]
    assert r["original_file"].endswith(".pdf") and "Downloaded from the Khyber Pakhtunkhwa Code" in r["provenance_note"]
    # quarantine: reasons kept, never in the records
    q = {json.loads(p.read_text(encoding="utf-8"))["reason"].split(" (")[0]
         for p in (kb / "scraped/quarantine/khyber-pakhtunkhwa-code").glob("*.json")}
    assert q == {"garbled text", "no recognisable sections"}
    assert len(list((kb / "scraped/records/statutes").glob("*.jsonl"))) == 1
    # originals saved unchanged, with URL, date and SHA-256 in the manifest
    man = [json.loads(x) for x in (kb / "scraped/originals/manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    pdf_rows = [m for m in man if m["role"] == "pdf"]
    assert len(pdf_rows) == 3 and {m["role"] for m in man} == {"listing", "page", "pdf"}
    row = next(m for m in pdf_rows if m["url"].endswith("act.pdf"))
    assert (Path(row["path"])).read_bytes() == pdf("act") and row["sha256"] == stage.sha256(pdf("act"))
    # the update log
    log = stage.read_log()
    assert log[-1]["kind"] == "scrape" and log[-1]["source"] == KP["name"] and log[-1]["new"] == 1
    assert log[-1]["quarantined"] == 2 and log[-1]["indexed"] is None
    # polite: robots.txt first, the identified User-Agent
    assert f.session.calls[0].endswith("/robots.txt") and "LegalEase-FYP" in f.session.headers["User-Agent"]


def test_second_run_unchanged_then_changed(kb):
    pages = kp_site(act=pdf("act"))
    kb_run.run([KP], fetcher(pages), caps={KP["name"]: 1}, log=quiet)
    again = kb_run.run([KP], fetcher(pages), caps={KP["name"]: 1}, skip_within_hours=0, log=quiet)
    assert again["per_source"][KP["name"]]["unchanged"] == 1
    import pymupdf
    doc = pymupdf.open(stream=pdf("act"), filetype="pdf")
    doc[0].insert_text((40, 820), "6. Repeal.-- The Trade Testing Ordinance, 1990 is hereby repealed.", fontsize=8)
    pages["https://kpcode.kp.gov.pk/uploads/act.pdf"] = (doc.tobytes(), "application/pdf")
    changed = kb_run.run([KP], fetcher(pages), caps={KP["name"]: 1}, skip_within_hours=0, log=quiet)
    e = changed["per_source"][KP["name"]]
    assert e["changed"] + e["new"] == 1 and e["unchanged"] == 0


def test_already_held_core_law_and_duplicates(kb):
    pages = kp_site(contract=pdf("contract_act"), act=pdf("act"), act_copy=pdf("act"))
    s = kb_run.run([KP], fetcher(pages), caps={KP["name"]: 10}, log=quiet)
    e = s["per_source"][KP["name"]]
    assert e["already_held"] == 1 and e["new"] == 1 and e["quarantined"] == 1        # copy in the same run
    reasons = {i["outcome"]: i.get("reason") for i in s["items"]}
    assert reasons["already_held"] == "a core law in the knowledge base"
    assert reasons["quarantined"].startswith("duplicate (same text as")
    # a later run: the same text at a new URL is already held
    pages2 = kp_site(other=pdf("act"))
    s2 = kb_run.run([KP], fetcher(pages2), caps={KP["name"]: 1}, skip_within_hours=0, log=quiet)
    held = s2["items"][0]
    assert held["outcome"] in ("unchanged", "already_held")


def test_resume_skips_recent_and_budget_stops(kb):
    pages = kp_site(act=pdf("act"), garbled=pdf("garbled"))
    ticks = iter(range(0, 10_000, 100))
    s = kb_run.run([KP], fetcher(pages), caps={KP["name"]: 10}, budget=150, log=quiet, clock=lambda: next(ticks))
    e = s["per_source"][KP["name"]]
    assert not s["complete"] and e["status"] == "stopped: time budget spent" and e["fetched"] == 1
    resumed = kb_run.run([KP], fetcher(pages), caps={KP["name"]: 10}, log=quiet)
    r = resumed["per_source"][KP["name"]]
    assert r["skipped_recent"] == 1 and r["fetched"] == 1 and resumed["complete"]


def test_fsc_judgment_record(kb):
    url = "https://www.federalshariatcourt.gov.pk/Judgments/Shariat%20Petition%2016-I%20of%202022%20Haji%20Saif" \
          "%20ur%20Rehman%20vs%20Govt%20of%20Pakistan%20-%20Khulla.pdf"
    pages = {FSC["listing_urls"][0]: ((FIX / "fsc_leading.html").read_bytes(), "text/html"),
             url: (pdf("judgment"), "application/pdf")}
    s = kb_run.run([FSC], fetcher(pages), caps={FSC["name"]: 3}, log=quiet)
    e = s["per_source"][FSC["name"]]
    assert e["new"] == 1 and e["errors"] == 2                       # the other two PDFs aren't in the fixture site
    rec = json.loads((kb / "scraped/records/judgments/federal-shariat-court.jsonl").read_text(encoding="utf-8"))
    assert rec["court"] == "Federal Shariat Court" and rec["source_tier"] == 1 and rec["source_url"] == url
    assert rec["case_name"] == "Haji Saif ur Rehman v. Federation of Pakistan through Secretary Ministry of Law"
    assert rec["year"] == 2023 and rec["case_number"] == "SHARIAT PETITION NO. 16/I OF 2022"
    assert rec["provenance_note"].startswith("Downloaded from the Federal Shariat Court website")
    assert rec["scraped"] is True and rec["paragraphs"] and rec["doc_id"].startswith("judgment/federal-shariat-court/")


def test_reparse_rebuilds_from_originals(kb):
    pages = kp_site(act=pdf("act"), garbled=pdf("garbled"))
    kb_run.run([KP], fetcher(pages), caps={KP["name"]: 10}, log=quiet)
    for p in (kb / "scraped/records/statutes").glob("*.jsonl"):
        p.write_text("broken\n", encoding="utf-8")
    counts = kb_run.reparse([KP], log=quiet)
    assert counts[KP["name"]]["new"] == 1 and counts[KP["name"]]["quarantined"] == 1
    rec = json.loads((kb / "scraped/records/statutes/khyber-pakhtunkhwa-trade-testing-board-act-2025.jsonl")
                     .read_text(encoding="utf-8").splitlines()[0])
    assert rec["section"] == "1"
    assert stage.read_log()[-1]["kind"] == "reparse"


def test_pakistan_code_priority_is_the_acts_not_held():
    cmap = {"categories": [{"name": "Civil Laws", "laws": [
        {"title": "Held Act, 1900", "url": "u1", "year": 1900, "match": {"how": "exact", "corpus": []}},
        {"title": "Missing Act, 1901", "url": "u2", "year": 1901, "status": "current", "match": None},
        {"title": "Maybe Act, 1902", "url": "u3", "year": 1902, "match": {"how": "possible"}}]}]}
    items = kb_run.pakistan_code_priority(cmap)
    assert [i.url for i in items] == ["u2", "u3"] and items[0].meta["category"] == "Civil Laws"


# --------------------------------------------------------------------------- index and search

class WordTokenizer:
    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        spans = [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]
        out = {"input_ids": list(range(len(spans)))}
        if return_offsets_mapping:
            out["offset_mapping"] = spans
        return out


def fake_embed(texts):
    out = np.zeros((len(texts), 384), np.float32)
    for i, t in enumerate(texts):
        for w in re.findall(r"\w+", t.lower()):
            out[i, hash(w) % 384] += 1.0
        out[i] /= max(np.linalg.norm(out[i]), 1e-9)
    return out


@pytest.fixture
def built(kb, monkeypatch):
    pytest.importorskip("faiss")
    url = "https://www.federalshariatcourt.gov.pk/Judgments/x.pdf"
    kb_run.run([KP], fetcher(kp_site(act=pdf("act"))), caps={KP["name"]: 1}, log=quiet)
    pages = {FSC["listing_urls"][0]: (f'<table><tr><td>1</td><td>Judgement on Khulla</td><td><a href="{url}">D</a>'
                                      f'</td></tr></table>'.replace("<td><a", '<td><a href="/Judgments/x.pdf"')
                                      .encode(), "text/html"),
             "https://www.federalshariatcourt.gov.pk/Judgments/x.pdf": (pdf("judgment"), "application/pdf")}
    kb_run.run([FSC], fetcher(pages), caps={FSC["name"]: 1}, log=quiet)
    v1 = [{"source": "THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025", "text": "old OCR copy of the board act"},
          {"source": "Other Act, 1990", "text": "trade testing board certificates"}]
    (kb / "v1_meta.json").write_text(json.dumps(v1), encoding="utf-8")
    monkeypatch.setattr(settings, "FAISS_METADATA_PATH", str(kb / "v1_meta.json"))
    result = scraped.build(tokenizer=WordTokenizer(), embed=fake_embed)
    stage.append_log(scraped.index_log_entry(result))
    monkeypatch.setattr(embeddings, "embed", fake_embed)
    return result


def test_build_writes_both_indexes_and_excludes_the_old_copy(built, kb):
    assert built["complete"]
    s, j = built["statutes"], built["judgments"]
    assert s["records"] == 5 and s["chunks"] >= 5 and j["chunks"] > 0
    assert s["excluded_v1_sources"] == ["THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025"]
    log = stage.read_log()[-1]
    assert log["kind"] == "index" and log["per_source"] == {"Khyber Pakhtunkhwa Code": 1, "Federal Shariat Court": 1}
    again = scraped.build(tokenizer=WordTokenizer(), embed=lambda t: (_ for _ in ()).throw(AssertionError("cached")))
    assert again["complete"] and again["statutes"]["embedded_now"] == 0          # resumable: all from the cache


def test_build_refuses_other_indexes(kb, monkeypatch):
    monkeypatch.setattr(settings, "KB_SCRAPED_INDEX_PATH", settings.KB_V2_INDEX_PATH)
    with pytest.raises(ValueError, match="refusing"):
        scraped.build(tokenizer=WordTokenizer(), embed=fake_embed)


def test_scraped_search_merges_and_drops_old_copies(built, monkeypatch):
    old = [{"source": "THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025", "text": "old", "relevance": 0.99},
           {"source": "Other Act, 1990", "text": "kept", "relevance": 0.10}]
    monkeypatch.setattr(embeddings, "_search_v1", lambda q, k, f=None, **kw: [dict(h) for h in old])
    monkeypatch.setattr(settings, "KB_V2", False)
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    assert [h["source"] for h in embeddings.search("trade testing board", 10)] == [h["source"] for h in old]
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    hits = embeddings.search("trade testing board", 10)
    sources = [h["source"] for h in hits]
    assert "THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025" not in sources and "Other Act, 1990" in sources
    top = next(h for h in hits if h.get("kb") == "scraped")
    assert top["source"] == "Khyber Pakhtunkhwa Trade Testing Board Act, 2025" and top["source_url"].startswith(LAW)


def test_half_written_scraped_index_is_ignored(built, monkeypatch):
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    Path(settings.KB_SCRAPED_METADATA_PATH).write_text("{", encoding="utf-8")
    monkeypatch.setattr(embeddings, "_search_v1", lambda q, k, f=None, **kw: [{"source": "A", "relevance": 0.5}])
    monkeypatch.setattr(settings, "KB_V2", False)
    assert [h["source"] for h in embeddings.search("board", 5)] == ["A"]
    assert scraped.status()["scraped_chunks"] == 0


def test_fsc_judgments_join_the_judgment_search(built, monkeypatch):
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    monkeypatch.setattr(settings, "JUDGMENTS_INDEX_PATH", str(Path(settings.KB_DIR) / "none.faiss"))
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    assert judgment_search.search("khula consent of the husband") == []
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    hits = judgment_search.search("khula consent of the husband", min_score=0.0)
    assert hits and hits[0]["court"] == "Federal Shariat Court" and hits[0]["doc_id"].startswith(
        "judgment/federal-shariat-court/")


# --------------------------------------------------------------------------- API and pages

@pytest.fixture
def authed(client):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="u1", role="student")
    yield client
    app.dependency_overrides.pop(get_current_user, None)


def test_updates_endpoint_and_flag_off(built, authed, monkeypatch):
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    assert authed.get(f"{API}/kb/updates").status_code == 404
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    body = authed.get(f"{API}/kb/updates").json()
    scrapes = [e for e in body["entries"] if e["kind"] == "scrape"]
    assert {e["source"] for e in scrapes} == {"Khyber Pakhtunkhwa Code", "Federal Shariat Court"}
    assert all(e["indexed"] == 1 for e in scrapes)                 # embedded by the later index build
    assert body["entries"][0]["kind"] == "index"


def test_scraped_laws_and_judgments_in_the_knowledge_base(built, authed, monkeypatch):
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    assert all(not d.get("scraped") for d in authed.get(f"{API}/kb/documents").json()["documents"])
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    catalog.reset()
    docs = {d["doc_id"]: d for d in authed.get(f"{API}/kb/documents").json()["documents"]}
    law = docs["khyber-pakhtunkhwa-trade-testing-board-act-2025"]
    assert law["scraped"] is True and law["fetched_at"] and law["source_url"].startswith(LAW)
    assert law["status"] == "under_review" and law["sections"] == 5 and law["document_type"] == "Act"
    rec = authed.get(f"{API}/kb/records/khyber-pakhtunkhwa-code/khyber-pakhtunkhwa-trade-testing-board-act-2025/s1")
    assert rec.status_code == 200
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    monkeypatch.setattr(settings, "JUDGMENTS_INDEX_PATH", str(Path(settings.KB_DIR) / "none.faiss"))
    rows = authed.get(f"{API}/kb/judgments").json()["judgments"]
    fsc = next(r for r in rows if r["court"] == "Federal Shariat Court")
    assert fsc["scraped"] is True and fsc["source_url"].endswith("x.pdf") and fsc["fetched_at"]
    detail = authed.get(f"{API}/kb/judgments/{fsc['doc_id']}").text
    assert "original_file" not in detail and "file_sha256" not in detail


def test_research_sources_line_reads_the_log(built, client, monkeypatch):
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    monkeypatch.setattr(embeddings, "build_or_load", lambda *a: 0)
    upd = client.get(f"{API}/research/stats").json()["updates"]
    assert upd["available"] is True and upd["searchable"] is True
    assert {s["name"] for s in upd["sources"]} == {"Khyber Pakhtunkhwa Code", "Federal Shariat Court"}
    assert upd["new"] == 2 and upd["last_checked"]


def test_health_reports_scraped(built, client, monkeypatch):
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    body = client.get("/health").json()
    assert body["scraped_v2"] is False and body["scraped_chunks"] is None
    monkeypatch.setattr(settings, "SCRAPED_V2", True)
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    body = client.get("/health").json()
    assert body["scraped_chunks"] == built["statutes"]["chunks"]
    assert body["scraped_judgment_chunks"] == built["judgments"]["chunks"]


# --------------------------------------------------------------------------- scripts

def test_weekly_runner_exit_codes(monkeypatch, tmp_path):
    sys.path.insert(0, str(ROOT / "scripts" / "scraping"))
    import run_weekly
    monkeypatch.setattr(run_weekly, "BACKEND", tmp_path)
    for codes, expected in (((0, 0), 0), ((3, 0), 3), ((0, 3), 3), ((1, 0), 1), ((0, 1), 1)):
        it = iter(codes)
        monkeypatch.setattr(run_weekly, "step", lambda name, cmd, log, it=it: next(it))
        monkeypatch.setattr(sys, "argv", ["run_weekly.py"])
        assert run_weekly.main() == expected


def test_scrape_script_caps():
    sys.path.insert(0, str(ROOT / "scripts"))
    import scrape_laws
    assert scrape_laws.parse_caps("") == {"Pakistan Code": 800, "Khyber Pakhtunkhwa Code": 60,
                                          "Federal Shariat Court": 100}
    assert scrape_laws.parse_caps("Pakistan Code=10, Federal Shariat Court=5")["Pakistan Code"] == 10
    with pytest.raises(SystemExit):
        scrape_laws.parse_caps("Pakistan Code")


def test_register_script_does_not_run_on_import():
    text = (ROOT / "scripts/scraping/register_weekly_task.ps1").read_text(encoding="utf-8")
    assert "-DaysOfWeek Sunday" in text and '$At = "03:00"' in text and "run_weekly.py" in text


# --------------------------------------------------------------------------- paged listing (kb-v2 C8)

def _listing(*ids):
    return ("<ul>" + "".join(f'<li><a href="https://kpcode.kp.gov.pk/homepage/lawDetails/{i}">Law {i}, 2020</a></li>'
                             for i in ids) + "</ul>").encode()


def test_paged_listing_walks_each_letter_until_a_page_adds_nothing(kb):
    base = "https://kpcode.kp.gov.pk/homepage/alphabetical/"
    pages = {f"{base}A/0": (_listing(1, 2), "text/html"), f"{base}A/10": (_listing(2, 3), "text/html"),
             f"{base}A/20": (_listing(3), "text/html"), f"{base}B/0": (_listing(4), "text/html"),
             f"{base}B/10": (_listing(), "text/html")}
    src = {**KP, "listing_urls": [], "paged_listing": {"url": base + "{letter}/{offset}", "letters": "AB",
                                                       "step": 10, "max_pages": 50}}
    f = fetcher(pages)
    items = list(kb_run._items(src, f, [], quiet))
    assert [i.url.rsplit("/", 1)[1] for i in items] == ["1", "2", "3", "4"]
    asked = [u for u in f.session.calls if "alphabetical" in u]
    assert asked == [f"{base}A/0", f"{base}A/10", f"{base}A/20", f"{base}B/0", f"{base}B/10"]   # no A/30


def test_kp_source_has_the_full_listing_and_pc_cap_is_800():
    assert KP["paged_listing"]["url"].endswith("/homepage/alphabetical/{letter}/{offset}")
    sys.path.insert(0, str(ROOT / "scripts"))
    import scrape_laws
    assert scrape_laws.DEFAULT_CAPS["Pakistan Code"] == 800
