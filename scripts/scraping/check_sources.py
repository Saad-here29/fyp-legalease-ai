"""Check candidate Pakistani law websites before adding them as scraping sources.

For each candidate: robots.txt (status, whether our User-Agent may fetch the
home and listing pages, any crawl-delay), the home page (reachable? final URL,
title), and links to terms / disclaimer / copyright pages. Polite: identified
User-Agent, 2 s between requests to the same site, one try each.

    python scripts/scraping/check_sources.py --out scripts/scraping/source_checks.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.robotparser
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

import requests
from lxml import html as lxml_html

USER_AGENT = "LegalEase-FYP/0.1 (+research prototype; contact: i228795@nu.edu.pk)"
DELAY = 2.0
TIMEOUT = 25

# (name, home URL, listing URL to test against robots, content type). Addresses
# are candidates; the check records which are real.
CANDIDATES = [
    ("Pakistan Code", "https://pakistancode.gov.pk/", "https://pakistancode.gov.pk/english/LGu0xAD.php", "statute"),
    ("Ministry of Law and Justice", "https://molaw.gov.pk/", "https://molaw.gov.pk/", "statute"),
    ("Law and Justice Commission of Pakistan", "https://ljcp.gov.pk/", "https://ljcp.gov.pk/", "statute"),
    ("National Assembly of Pakistan", "https://na.gov.pk/", "https://na.gov.pk/en/acts-tenure.php", "statute"),
    ("Senate of Pakistan", "https://senate.gov.pk/", "https://senate.gov.pk/en/acts.php", "statute"),
    ("Printing Corporation of Pakistan (Gazette)", "https://pcp.gov.pk/", "https://pcp.gov.pk/", "statute"),
    ("Punjab Code", "https://punjabcode.punjab.gov.pk/", "https://punjabcode.punjab.gov.pk/", "statute"),
    ("Punjab Laws", "https://punjablaws.gov.pk/", "https://punjablaws.gov.pk/", "statute"),
    ("Sindh Laws", "https://sindhlaws.gov.pk/", "https://sindhlaws.gov.pk/", "statute"),
    ("Khyber Pakhtunkhwa Code", "https://kpcode.kp.gov.pk/", "https://kpcode.kp.gov.pk/", "statute"),
    ("Balochistan Code", "https://balochistancode.gob.pk/", "https://balochistancode.gob.pk/", "statute"),
    ("Supreme Court of Pakistan", "https://www.supremecourt.gov.pk/", "https://www.supremecourt.gov.pk/latest-judgements/", "judgment"),
    ("Islamabad High Court", "https://www.ihc.gov.pk/", "https://www.ihc.gov.pk/", "judgment"),
    ("Lahore High Court", "https://www.lhc.gov.pk/", "https://www.lhc.gov.pk/", "judgment"),
    ("Sindh High Court", "https://www.shc.gov.pk/", "https://caselaw.shc.gov.pk/", "judgment"),
    ("Peshawar High Court", "https://www.peshawarhighcourt.gov.pk/", "https://www.peshawarhighcourt.gov.pk/", "judgment"),
    ("Balochistan High Court", "https://bhc.gov.pk/", "https://bhc.gov.pk/", "judgment"),
    ("Federal Shariat Court", "https://www.federalshariatcourt.gov.pk/", "https://www.federalshariatcourt.gov.pk/", "judgment"),
    ("PakLII", "https://www.paklii.org/", "https://www.paklii.org/", "judgment"),
]

TERMS_RE = re.compile(r"terms|disclaimer|copyright|privacy|policy|conditions", re.I)


def get(session, url):
    try:
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        return r, None
    except requests.RequestException as e:
        return None, f"{type(e).__name__}: {str(e)[:120]}"


def check(session, name, home, listing, kind):
    out = {"name": name, "home": home, "listing": listing, "content_type": kind,
           "checked_at": datetime.now(UTC).isoformat(timespec="seconds")}
    r, err = get(session, urljoin(home, "/robots.txt"))
    time.sleep(DELAY)
    rp = urllib.robotparser.RobotFileParser()
    if r is None:
        out["robots"] = {"status": None, "error": err}
        rp.parse([])  # unknown: treated as allowed, but the source is unreachable anyway
    else:
        body = r.text if r.status_code == 200 and "html" not in r.headers.get("content-type", "") else ""
        out["robots"] = {"status": r.status_code, "lines": [ln for ln in body.splitlines() if ln.strip()][:25]}
        rp.parse(body.splitlines())
        delay = rp.crawl_delay(USER_AGENT)
        out["robots"]["crawl_delay"] = delay
    out["robots_allows_home"] = rp.can_fetch(USER_AGENT, home)
    out["robots_allows_listing"] = rp.can_fetch(USER_AGENT, listing)

    r, err = get(session, home)
    time.sleep(DELAY)
    if r is None:
        out["home_status"], out["error"] = None, err
        out["status"] = "not reachable"
        return out
    out["home_status"], out["final_url"] = r.status_code, r.url
    terms = []
    try:
        doc = lxml_html.fromstring(r.content)
        title = doc.findtext(".//title")
        out["title"] = (title or "").strip()[:120]
        for a in doc.iter("a"):
            text = " ".join(a.text_content().split())
            href = a.get("href") or ""
            if TERMS_RE.search(text) or TERMS_RE.search(href):
                terms.append({"text": text[:60], "href": urljoin(r.url, href)})
        page_text = " ".join(doc.text_content().split())
        m = re.search(r"(copyright|©)[^.]{0,120}", page_text, re.I)
        out["copyright"] = m.group(0)[:140] if m else None
        out["mentions_scraping_ban"] = bool(re.search(
            r"(scrap|crawl|automated (access|means|download)|bots?\b).{0,60}(prohibit|not (allowed|permitted))",
            page_text, re.I))
    except Exception as e:  # noqa: BLE001
        out["parse_error"] = str(e)[:120]
    out["terms_links"] = terms[:8]
    if r.status_code >= 400:
        out["status"] = "not reachable"
    elif not (out["robots_allows_home"] and out["robots_allows_listing"]) or out.get("mentions_scraping_ban"):
        out["status"] = "blocked"
    else:
        out["status"] = "allowed (robots/home)"
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    results = []
    for cand in CANDIDATES:
        res = check(s, *cand)
        results.append(res)
        print(f"{res['status']:24} {res['name']:42} home={res.get('home_status')} robots={res['robots'].get('status')} "
              f"terms={len(res.get('terms_links', []))} {res.get('error') or ''}", flush=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
