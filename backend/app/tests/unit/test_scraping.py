"""Scraping prototype: parsing (saved HTML fixtures), hashing and change
detection, politeness limits, and the stats fields. No live requests: HTTP is
a fake session, time is a fake clock, PDFs are built in memory."""

import json
import subprocess
import sys
from pathlib import Path

import pymupdf
import pytest
import requests

from app.models.scraping import ScrapedDocument, ScrapeRun
from app.scraping import runner as runner_mod
from app.scraping.fetcher import USER_AGENT, DisallowedError, Fetcher, LimitReachedError
from app.scraping.parse import content_hash, find_pdf_url, normalise_title, parse_listing
from app.scraping.stats import scrape_updates

ROOT = Path(__file__).resolve().parents[4]
FIX = Path(__file__).resolve().parents[1] / "fixtures" / "scraping"
SOURCES = {s["name"]: s for s in json.loads((ROOT / "scripts/scraping/sources.json").read_text(encoding="utf-8"))}


def fixture(name):
    return (FIX / name).read_bytes()


def make_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


# ---- parsing -----------------------------------------------------------------

def test_pakistan_code_listing_and_pdf():
    cfg = SOURCES["Pakistan Code"]
    items = parse_listing(fixture("pakistancode_listing.html"), "https://pakistancode.gov.pk/english/LGu0xAD?alp=A", cfg)
    assert len(items) == 4 and items[0].title == "Abandoned Properties (Management) Act, 1975"
    assert items[0].url.startswith("https://pakistancode.gov.pk/english/UY2F")
    pdf = find_pdf_url(fixture("pakistancode_law.html"), items[0].url, cfg)
    assert pdf.startswith("https://pakistancode.gov.pk/pdffiles/") and pdf.endswith(".pdf")  # viewer iframe resolved


def test_kp_code_listing_and_pdf():
    cfg = SOURCES["Khyber Pakhtunkhwa Code"]
    items = parse_listing(fixture("kpcode_recent.html"), "https://kpcode.kp.gov.pk/homepage/recent_updated", cfg)
    assert len(items) == 3 and all("/homepage/lawDetails/" in i.url for i in items)
    assert "TRADE TESTING BOARD" in items[0].title
    pdf = find_pdf_url(fixture("kpcode_law.html"), items[0].url, cfg)
    assert pdf.startswith("https://kpcode.kp.gov.pk/uploads/") and pdf.endswith(".pdf")


def test_federal_shariat_court_titles_come_from_the_row():
    cfg = SOURCES["Federal Shariat Court"]
    items = parse_listing(fixture("fsc_leading.html"), "https://www.federalshariatcourt.gov.pk/en/leading-judgements/", cfg)
    assert len(items) == 3 and cfg["item_is_pdf"] is True
    assert items[0].title.startswith("Judgement on Prohibition of attempt to commit Suicide")
    assert items[0].url.endswith(".pdf") and "/Judgments/" in items[0].url


def test_only_built_sources_are_enabled_and_judgments_marked():
    enabled = {n for n, s in SOURCES.items() if s["enabled"]}
    assert enabled == {"Pakistan Code", "Khyber Pakhtunkhwa Code", "Federal Shariat Court"}
    assert SOURCES["Federal Shariat Court"]["content_type"] == "judgment"
    assert SOURCES["Lahore High Court"]["status"] == "blocked"
    for s in SOURCES.values():
        assert s["status"] in ("blocked", "not reachable", "needs custom parser", "verified")
        assert (s["status"] == "verified") == s["enabled"]
        assert s["check"]["date"]


# ---- hashing and titles ------------------------------------------------------

def test_hash_ignores_whitespace_but_not_text():
    assert content_hash("Section 1.  Short\n title") == content_hash("Section 1. Short title")
    assert content_hash("Section 1. Short title") != content_hash("Section 1. Long title")


@pytest.mark.parametrize("a, b", [
    ("1 THE LAW RE FORMS ORDINANCE, 1972", "Law Reforms Ordinance, 1972"),
    ("THE MUSLIM FAMILY LAWS ORDINAN CE, 1961", "Muslim Family Laws Ordinance, 1961"),
    ("Abandoned Properties (Management) Act, 1975", "ABANDONED PROPERTIES (MANAGEMENT) ACT, 1975"),
])
def test_corpus_titles_match_despite_noise(a, b):
    assert normalise_title(a) == normalise_title(b)


# ---- politeness --------------------------------------------------------------

class FakeResponse:
    def __init__(self, url, status=200, content=b"", ctype="text/html"):
        self.url, self.status_code, self.content = url, status, content
        self.headers = {"content-type": ctype}
        self.text = content.decode("utf-8", "ignore")


class FakeSession:
    def __init__(self, routes, fail_first=None):
        self.routes, self.headers, self.calls = routes, {}, []
        self.fail_first = dict(fail_first or {})

    def get(self, url, timeout=None, allow_redirects=True):
        self.calls.append((url, timeout))
        if self.fail_first.get(url):
            self.fail_first[url] -= 1
            return FakeResponse(url, 503)
        if url.endswith("/robots.txt") and url not in self.routes:
            return FakeResponse(url, 404)
        if url not in self.routes:
            raise requests.ConnectionError(f"no route {url}")
        body, ctype = self.routes[url]
        return FakeResponse(url, 200, body, ctype)


class Clock:
    def __init__(self):
        self.t, self.sleeps = 0.0, []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(round(s, 3))
        self.t += s


def fetcher(routes, **kw):
    clock = Clock()
    f = Fetcher(session=FakeSession(routes, kw.pop("fail_first", None)), clock=clock, sleep=clock.sleep, **kw)
    return f, clock


def test_user_agent_and_timeout_are_set():
    f, _ = fetcher({"https://a.pk/x": (b"x", "text/html")})
    f.get("https://a.pk/x")
    assert f.session.headers["User-Agent"] == USER_AGENT and "i228795@nu.edu.pk" in USER_AGENT
    assert all(t == f.timeout for _, t in f.session.calls)


def test_two_seconds_between_requests_to_the_same_site():
    routes = {f"https://a.pk/{i}": (b"x", "text/html") for i in range(3)} | {"https://b.pk/0": (b"x", "text/html")}
    f, clock = fetcher(routes)
    for u in ("https://a.pk/0", "https://a.pk/1", "https://b.pk/0", "https://a.pk/2"):
        f.get(u)
    # robots.txt for a.pk, then a/0 waits 2 s after it, a/1 waits 2 s, b.pk's
    # first requests don't wait for a.pk, a/2 waits what's left of 2 s.
    assert all(s <= 2.0 for s in clock.sleeps) and sum(clock.sleeps) >= 6.0


def test_crawl_delay_from_robots_is_honoured():
    routes = {"https://na.pk/robots.txt": (b"User-agent: *\nCrawl-delay: 10\n", "text/plain"),
              "https://na.pk/1": (b"x", "text/html"), "https://na.pk/2": (b"x", "text/html")}
    f, clock = fetcher(routes)
    f.get("https://na.pk/1")
    f.get("https://na.pk/2")
    assert clock.sleeps and max(clock.sleeps) == 10.0


def test_retries_with_back_off_then_succeeds():
    f, clock = fetcher({"https://a.pk/x": (b"ok", "text/html")}, fail_first={"https://a.pk/x": 2})
    assert f.get("https://a.pk/x").content == b"ok"
    assert [s for s in clock.sleeps if s in (2.0, 4.0)][-2:] == [2.0, 4.0]  # back-off doubles


def test_gives_up_after_the_retries():
    f, _ = fetcher({"https://a.pk/x": (b"ok", "text/html")}, fail_first={"https://a.pk/x": 9}, retries=2)
    with pytest.raises(requests.HTTPError):
        f.get("https://a.pk/x")


def test_page_and_pdf_caps():
    routes = {f"https://a.pk/{i}": (b"x", "text/html") for i in range(5)}
    f, _ = fetcher(routes, max_pages=3, max_pdfs=1)
    f.get("https://a.pk/0", pdf=True)
    with pytest.raises(LimitReachedError):
        f.get("https://a.pk/1", pdf=True)
    f.get("https://a.pk/2")
    f.get("https://a.pk/3")
    with pytest.raises(LimitReachedError):
        f.get("https://a.pk/4")


def test_robots_disallow_is_obeyed():
    routes = {"https://lhc.pk/robots.txt": (b"User-agent: *\nDisallow: /\n", "text/plain"),
              "https://lhc.pk/judgments": (b"x", "text/html")}
    f, _ = fetcher(routes)
    with pytest.raises(DisallowedError):
        f.get("https://lhc.pk/judgments")
    assert ("https://lhc.pk/judgments", f.timeout) not in f.session.calls


def test_robots_server_error_means_stay_off():
    f, _ = fetcher({"https://x.pk/page": (b"x", "text/html")}, fail_first={"https://x.pk/robots.txt": 1})
    f.session.routes["https://x.pk/robots.txt"] = (b"", "text/plain")
    with pytest.raises(DisallowedError):
        f.get("https://x.pk/page")


# ---- change detection (end to end on SQLite) --------------------------------

KP = SOURCES["Khyber Pakhtunkhwa Code"]
LIST = KP["listing_urls"][0]


def kp_routes(text_1619="Trade Testing Board Act text v1"):
    pdfs = {"1619": text_1619, "1618": "Provincial Assembly Act text", "1617": "Climate Action Board Act text"}
    routes = {LIST: (fixture("kpcode_recent.html"), "text/html")}
    for n, txt in pdfs.items():
        law = f"https://kpcode.kp.gov.pk/homepage/lawDetails/{n}"
        pdf = f"https://kpcode.kp.gov.pk/uploads/law_{n}.pdf"
        routes[law] = (f'<html><body><a href="/uploads/law_{n}.pdf">Download</a></body></html>'.encode(), "text/html")
        routes[pdf] = (make_pdf(txt), "application/pdf")
    return routes


def run_once(db, routes, *, corpus=frozenset(), dry_run=False, limit=None):
    f, _ = fetcher(routes, max_pages=50, max_pdfs=10)
    return runner_mod.run([dict(KP, enabled=True)], f, db=db, corpus_titles=set(corpus), limit=limit,
                          dry_run=dry_run, log=lambda *_: None)


def test_new_then_unchanged_then_changed_keeps_old_version(db_session):
    s1 = run_once(db_session, kp_routes())
    assert s1["per_source"]["Khyber Pakhtunkhwa Code"]["new"] == 3 and s1["new"] == 3
    assert db_session.query(ScrapedDocument).filter_by(status="staged").count() == 3

    s2 = run_once(db_session, kp_routes())
    c2 = s2["per_source"]["Khyber Pakhtunkhwa Code"]
    assert (c2["new"], c2["changed"], c2["unchanged"]) == (0, 0, 3)
    assert db_session.query(ScrapedDocument).count() == 3

    s3 = run_once(db_session, kp_routes(text_1619="Trade Testing Board Act text v2 amended"))
    c3 = s3["per_source"]["Khyber Pakhtunkhwa Code"]
    assert (c3["changed"], c3["unchanged"]) == (1, 2)
    url = "https://kpcode.kp.gov.pk/homepage/lawDetails/1619"
    versions = db_session.query(ScrapedDocument).filter_by(source_url=url).order_by(ScrapedDocument.version).all()
    assert [(v.version, v.is_latest, v.change_kind, v.status) for v in versions] == [
        (1, False, "new", "staged"), (2, True, "changed", "staged")]
    assert "v1" in versions[0].text and "v2" in versions[1].text   # the old version is kept
    assert versions[1].first_seen_at == versions[0].first_seen_at
    assert db_session.query(ScrapeRun).count() == 3


def test_statute_already_in_the_corpus_is_not_new(db_session):
    corpus = {normalise_title("THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025")}
    s = run_once(db_session, kp_routes(), corpus=corpus)
    c = s["per_source"]["Khyber Pakhtunkhwa Code"]
    assert (c["baseline"], c["new"]) == (1, 2)
    base = db_session.query(ScrapedDocument).filter_by(change_kind="baseline").one()
    assert base.status == "approved" and base.in_corpus is True
    # A later text change to that statute IS reported, as changed.
    s2 = run_once(db_session, kp_routes(text_1619="amended text"), corpus=corpus)
    assert s2["per_source"]["Khyber Pakhtunkhwa Code"]["changed"] == 1


def test_dry_run_writes_nothing(db_session):
    s = run_once(db_session, kp_routes(), dry_run=True)
    assert s["new"] == 3 and s["dry_run"] is True
    assert db_session.query(ScrapedDocument).count() == 0 and db_session.query(ScrapeRun).count() == 0


def test_limit_caps_documents_and_errors_are_counted(db_session):
    routes = kp_routes()
    del routes["https://kpcode.kp.gov.pk/uploads/law_1618.pdf"]   # one PDF is missing
    s = run_once(db_session, routes, limit=2)
    c = s["per_source"]["Khyber Pakhtunkhwa Code"]
    assert c["checked"] == 2 and c["new"] == 1 and c["errors"] == 1 and c["error_samples"]


# ---- stats -------------------------------------------------------------------

def test_stats_unavailable_without_a_run(db_session):
    assert scrape_updates(db_session) == {"available": False}


def test_stats_after_a_run(db_session):
    run_once(db_session, kp_routes())
    u = scrape_updates(db_session)
    assert u["available"] and u["new"] == 3 and u["changed"] == 0 and u["errors"] == 0
    assert u["last_checked"] is not None and u["last_updated"] is not None
    assert u["sources"] == [{"name": "Khyber Pakhtunkhwa Code", "content_type": "statute",
                             "checked": 3, "new": 3, "changed": 0, "errors": 0}]


def test_stats_without_tables_is_unavailable():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    eng = create_engine("sqlite://")
    assert scrape_updates(sessionmaker(bind=eng)()) == {"available": False}


def test_stats_endpoint_is_additive(client, monkeypatch):
    from app.api.v1 import research as research_router
    from app.scraping import stats as stats_mod
    monkeypatch.setattr(research_router.embeddings, "index_stats", lambda: {"chunks": 53739, "documents": 900})
    monkeypatch.setattr(stats_mod, "_cache", {"at": 0.0, "value": None})
    r = client.get("/api/v1/research/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["chunks"] == 53739 and body["documents"] == 900   # unchanged fields
    assert body["updates"]["available"] is False                    # no tables in the shared DB yet


def test_cli_refuses_to_write_without_a_schema():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scrape_laws.py"), "--limit", "1"],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "Refusing to write without --schema" in r.stderr


def test_item_stopped_by_the_cap_is_not_counted_as_checked(db_session):
    f, _ = fetcher(kp_routes(), max_pages=50, max_pdfs=2)
    s = runner_mod.run([dict(KP, enabled=True)], f, db=db_session, corpus_titles=set(), log=lambda *_: None)
    c = s["per_source"]["Khyber Pakhtunkhwa Code"]
    assert c["checked"] == 2 and c["new"] == 2 and c["status"].startswith("stopped: PDF cap")


# ---- dry-run summary and comparison without tables (kb-v2 B8) ---------------

from app.scraping.report import previous_hashes, render  # noqa: E402


def test_dry_run_compares_with_an_earlier_run_without_a_database():
    s1 = run_once(None, kp_routes(), dry_run=True)
    assert [i["outcome"] for i in s1["items"]] == ["new", "new", "new"]
    assert all(len(i["content_hash"]) == 64 for i in s1["items"])
    prev = previous_hashes(s1)
    f, _ = fetcher(kp_routes(text_1619="Trade Testing Board Act text v2 amended"), max_pages=50, max_pdfs=10)
    s2 = runner_mod.run([dict(KP, enabled=True)], f, db=None, corpus_titles=set(), dry_run=True,
                        log=lambda *_: None, previous=prev)
    outcomes = {i["url"].rsplit("/", 1)[-1]: i["outcome"] for i in s2["items"]}
    assert outcomes == {"1619": "changed", "1618": "unchanged", "1617": "unchanged"}
    c = s2["per_source"]["Khyber Pakhtunkhwa Code"]
    assert (c["changed"], c["unchanged"], c["new"]) == (1, 2, 0)


def test_summary_table_is_readable_and_says_nothing_is_indexed():
    s = run_once(None, kp_routes(), dry_run=True, corpus={normalise_title(
        "THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025")})
    out = render(s)
    lines = out.splitlines()
    assert "Summary (dry run: nothing was written)" in out
    header = next(line for line in lines if line.startswith("Source"))
    for col in ("Source", "URL", "Status", "Hash", "Would stage", "Indexed"):
        assert col in header
    rows = [line for line in lines if line.startswith("Khyber Pakhtunkhwa Code")]
    assert len(rows) == 3 and all(line.rstrip().endswith("no") for line in rows)       # indexed: no
    assert any("baseline" in r and "no (already in corpus)" in r for r in rows)
    assert any(" new " in r and " yes " in r for r in rows)
    h = s["items"][0]["content_hash"][:8]
    assert h in out and s["items"][0]["content_hash"][:9] not in out
    assert "3 documents: 2 new, 0 changed, 0 unchanged, 1 already in the corpus, 0 failed" in out


def test_cli_compare_with_needs_dry_run(tmp_path):
    prev = tmp_path / "run1.json"
    prev.write_text('{"items": []}', encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scrape_laws.py"), "--compare-with", str(prev)],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 2 and "for dry runs" in r.stderr
