# Scheduled scraping (prototype, branch `scraping`)

This prototype checks Pakistani law websites on a schedule and stages new or
changed documents for review. It's on the `scraping` branch only, and **not
merged**.
- **Database:** its migration is not applied to the shared database, which
  has no scraping tables. Writes go to a throwaway schema.
- **Index:** scraped text never reaches the search index, the chat or the UI
  without a person approving it.
- **Judgments:** they stay staged and are never shown, so the app remains
  "statutes only".
- **Git:** scraped text stays out of git. The test fixtures keep only page
  structure (titles and links).

## Result on 2026-10-06

**3 of 19 sources work end to end:**
- Pakistan Code (statutes);
- Khyber Pakhtunkhwa Code (statutes);
- Federal Shariat Court leading judgments (judgments, staged only).

All three were verified by a live run, `--limit 10`, into a throwaway schema.

**The rest:** 12 are reachable and allowed
but need their own selectors (not built). 2 are
blocked and 2 are not reachable.

## Sources

Every candidate was checked before being added (`scripts/scraping/check_sources.py`,
raw results in `scripts/scraping/source_checks.json`). Each check covered:
- robots.txt, evaluated for our User-Agent;
- the home page;
- terms, disclaimer and copyright links.

No candidate's terms forbid automated access; the only robots.txt ban is the
Lahore High Court's. None of the sites grants a reuse licence, and every
government law site warns that its text is **not authoritative**: the Gazette
notification is the official source. So scraped text stays staged, with its
source URL and fetch date kept for provenance.

| Source | Type | robots.txt (checked 2026-10-06) | Terms / disclaimer seen | Status | Notes |
|---|---|---|---|---|---|
| [Pakistan Code](https://pakistancode.gov.pk/) | statute | Disallow: /pdffiles/ | linked: Disclaimer | **verified** | Laws listed by letter; each law page embeds its PDF from /pdffiles/ (robots.txt disallows /pdffiles/ only for googlebot). |
| [Ministry of Law and Justice](https://molaw.gov.pk/) | statute | HTTP 404 (no rules) | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Law and Justice Commission of Pakistan](https://ljcp.gov.pk/) | statute | HTTP 404 (no rules) | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [National Assembly of Pakistan](https://na.gov.pk/) | statute | Crawl-delay: 10; Disallow: /manage/; Disallow: /_manage/; Disallow: /manage/; Disallow: /_manage/ | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Senate of Pakistan](https://senate.gov.pk/) | statute | HTTP 404 (no rules) | linked: Disclaimer, Privacy Policy, Terms of Use | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Printing Corporation of Pakistan (Gazette)](https://pcp.gov.pk/) | statute | no answer | none linked from the home page | **not reachable** | connection timed out (pcp.gov.pk) |
| [Punjab Code](https://punjabcode.punjab.gov.pk/) | statute | HTTP 403 (no rules) | linked: Disclaimer | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Punjab Laws](https://punjablaws.gov.pk/) | statute | Disallow: /cgi-bin/; Disallow: /temp/ | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Sindh Laws](https://sindhlaws.gov.pk/) | statute | Disallow: /admin/; Disallow: /App_Data/; Disallow: /bin/; Disallow: /obj/; Disallow: /scripts/ | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Khyber Pakhtunkhwa Code](https://kpcode.kp.gov.pk/) | statute | no restrictions | none linked from the home page | **verified** | 'Recently updated' list -> law page -> watermarked PDF under /uploads/. |
| [Balochistan Code](https://balochistancode.gob.pk/) | statute | no restrictions | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Supreme Court of Pakistan](https://www.supremecourt.gov.pk/) | judgment | HTTP 403 (no rules) | none linked from the home page | **blocked** | HTTP 403 'Access Denied' to the identified crawler (home and robots.txt); not worked around |
| [Islamabad High Court](https://www.ihc.gov.pk/) | judgment | HTTP 404 (no rules) | none linked from the home page | **needs custom parser** | home page is a 1.4 KB JavaScript shell with no links |
| [Lahore High Court](https://www.lhc.gov.pk/) | judgment | Disallow: / | none linked from the home page | **blocked** | robots.txt: 'User-agent: * / Disallow: /' |
| [Sindh High Court](https://www.shc.gov.pk/) | judgment | Disallow: /causelist/ | linked: Disclaimer | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Peshawar High Court](https://www.peshawarhighcourt.gov.pk/) | judgment | no restrictions | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Balochistan High Court](https://bhc.gov.pk/) | judgment | Disallow: /_scripts/; Disallow: /assets/; Disallow: /blocks/; Disallow: /lib/; Disallow: /media/; Disallow: /pages/ | none linked from the home page | **needs custom parser** | robots/terms allow polite access; listing selectors not written yet (not built today) |
| [Federal Shariat Court](https://www.federalshariatcourt.gov.pk/) | judgment | Disallow: /wp-admin/ | none linked from the home page | **verified** | Leading judgments table; each row links straight to the PDF. Judgments stay staged and never reach the UI. |
| [PakLII](https://www.paklii.org/) | judgment | no answer | none linked from the home page | **not reachable** | domain does not resolve (www.paklii.org) |

**Statuses:**
- **verified:** built and shown working end to end on 2026-10-06.
- **needs custom parser:** reachable and allowed, but no selectors written
  yet.
- **blocked:** robots.txt, or an access-denied response to our identified
  User-Agent. Not worked around.
- **not reachable:** no connection or no DNS on 2026-10-06.

**Provenance:**
- **Pakistan Code:** https://pakistancode.gov.pk/ (Ministry of Law and
  Justice), checked 2026-10-06. robots.txt blocks `/pdffiles/` for googlebot
  only. Disclaimer: "for general informational purposes only… refer to the
  original source i.e. the relevant Gazette notification(s)".
- **Khyber Pakhtunkhwa Code:** https://kpcode.kp.gov.pk/ (Law & Parliamentary
  Affairs Department, KP), checked 2026-10-06. robots.txt allows everything.
- **Federal Shariat Court:** https://www.federalshariatcourt.gov.pk/en/leading-judgements/,
  checked 2026-10-06. robots.txt blocks only `/wp-admin/`.
- Every stored document keeps its `source_url`, `pdf_url` and `fetched_at`.

## Design

```
scripts/scrape_laws.py            CLI (schedule target)
scripts/scraping/sources.json     one entry per site: URLs, XPath selectors, check result, status
scripts/scraping/check_sources.py the robots/terms check
backend/app/scraping/fetcher.py   polite HTTP: User-Agent, 2 s per site, retries, caps, robots.txt
backend/app/scraping/parse.py     listing -> document page -> PDF; text; hash; title normalisation
backend/app/scraping/runner.py    one run: change detection, staging, run summary
backend/app/scraping/stats.py     freshness for GET /research/stats
backend/alembic/versions/a3c5e7f90b12_scraping_tables.py
```

**Generic scraper, no per-site code.** A source is configured with:
- `listing_urls`;
- an `item_xpath` (one element per document);
- an optional `title_xpath` relative to the item;
- either `item_is_pdf`, or a `pdf_xpath` on the document page (viewer
  iframes like `ViewerJS/#../x.pdf` are resolved).

The PDF's text is extracted with PyMuPDF.

**Change detection.** The text is normalised (whitespace collapsed) and
hashed with SHA-256, then compared with the latest stored version of the same
URL:

| Situation | Result |
|---|---|
| Not seen before, and a statute whose title is already in the corpus | `baseline`, status `approved`, not reported as new |
| Not seen before | `new`, `staged` |
| Same hash | unchanged, nothing written |
| Different hash | `changed`: a new version, `staged`. The previous version stays, with `is_latest = false` |

Titles are compared after normalisation: a leading number and "the" are
dropped, and only letters and digits are kept. That makes
"1 THE LAW RE FORMS ORDINANCE, 1972" equal "Law Reforms Ordinance, 1972".
The corpus is `data/processed/statutes/legal_statutes_corpus.json` (892
normalised titles).

**Tables** (migration `a3c5e7f90b12`, additive):
- **`scraped_documents`:** source name, source URL, PDF URL, title, content
  type (statute or judgment), content hash, text, fetched_at, first_seen_at,
  status (staged / approved / rejected, checked by a CHECK constraint),
  change kind, in_corpus, version, is_latest, run id.
- **`scrape_runs`:** started_at, finished_at, pages checked, new, changed,
  errors, per-source counts (JSON), dry_run.

**Alembic chain, one head:**
```
<base> -> 2b7806a018fc -> 16e7f2d6727c -> aab3307a5ca9 -> c41e7d2b9a10
       -> d5a91c3e7f20 -> e7b3c9d14a02 (master's head) -> a3c5e7f90b12 (scraping)
```
`master` has no migration after `e7b3c9d14a02`, so merging gives one head.
If `master` gains a migration before the merge, change `down_revision`
before merging.

**Freshness in the app.** `GET /research/stats` has an additive `updates`
field:
- last checked, last updated, pages checked, new / changed / errors, and
  per-source counts;
- it is `available: false` when the tables don't exist (the shared database
  today) or the database is down;
- it's cached for 60 s and never fails the endpoint.

The Research page shows one line, with the sources checked, the date and the
counts, only when `available`. Search is unchanged.

## Limits (the same for every source)

- **User-Agent:** `LegalEase-FYP/0.1 (+research prototype; contact: i228795@nu.edu.pk)`.
- **robots.txt:** read for every site at run time; disallowed URLs are
  skipped and counted as errors. A 4xx robots.txt means allowed; a 5xx or no
  answer means stay off (RFC 9309).
- **Delay:** at least 2 s between requests to the same site, longer if
  robots.txt asks (the National Assembly asks for 10 s).
- **Retries:** 3, with back-off of 2 s, then 4 s, then 8 s, on network
  errors, 429 and 5xx. Every request has a 30 s timeout.
- **Caps:** `--max-pages` (default 60 requests per run) and `--limit`
  (PDFs per run, split evenly across sources). A run stops cleanly at a cap,
  and the source is marked "stopped".
- **Writes:** need `--schema`. The CLI refuses to write without it, so
  nothing lands in the shared public schema before the merge is approved.

## Running it

```powershell
# from the project root, with the backend venv
python scripts/scrape_laws.py --dry-run --limit 5                       # fetch and compare, write nothing
python scripts/scrape_laws.py --schema scrapetest_x --limit 10          # write to a throwaway schema
python scripts/scrape_laws.py --sources "Khyber Pakhtunkhwa Code" --limit 3 --dry-run
```

To create a throwaway schema with the tables, run `alembic -x schema=NAME
upgrade head` against the session pooler (port 5432). The test helper
creates one, tests up and down, and can keep it with `--keep`.

## Schedule (weekly)

**Windows Task Scheduler** (run once in an elevated PowerShell; adjust the
paths):

```powershell
$py  = "E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend\venv\Scripts\python.exe"
$arg = "scripts\scrape_laws.py --schema scraping --limit 40 --out logs\scrape_last.json"
$act = New-ScheduledTaskAction -Execute $py -Argument $arg -WorkingDirectory "E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main"
$trg = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
Register-ScheduledTask -TaskName "LegalEase weekly law check" -Action $act -Trigger $trg -Description "Polite weekly check of Pakistani law sites; stages new/changed documents"
```

**cron (Linux server):**
```
0 3 * * 0  cd /srv/legalease && backend/venv/bin/python scripts/scrape_laws.py --schema scraping --limit 40 --out logs/scrape_last.json >> logs/scrape.log 2>&1
```

Until the merge is approved, `--schema` must name a throwaway schema. After
it, the tables live in the public schema, and the scheduled command would
need a small change to allow writing there.

## From staged to the search index (documented only; not built)

1. **Review.** A person reads each `staged` document (title, source URL,
   version diff) and sets it to `approved` or `rejected`. Judgments are not
   approved while the app is "statutes only".
2. **Clean.** Approved statute text goes through the corpus cleaner
   (`scripts/clean_statute_corpus.py`, as used for the current corpus):
   - remove headers, footers, watermarks and page numbers;
   - split the text into sections;
   - record the source URL and fetch date in the metadata.
3. **Embed on Colab** with the same model as the live index
   (`paraphrase-multilingual-MiniLM-L12-v2`, L2-normalised). Use the same
   chunking as the index being added to: 800 characters with 100 overlap for
   today's v1 index. Export the vectors and metadata.
4. **Add to the index, as a new version.**
   - Load the current FAISS index and metadata into a copy, never the live
     files, add the new vectors, and give it a new version.
   - For a changed statute, remove its old chunks first. A rebuild of that
     statute is simpler than surgery on the index.
5. **Verify,** then switch:
   - run the offline replay (`scripts/eval_chat_quality.py`);
   - run the 78-question and off-topic checks;
   - switch the backend to the new index only if nothing regresses;
   - keep the old index for rollback.

## Live runs on 2026-10-06 (throwaway schema `scrapelive_1791254533`)

**Run 1** (`--limit 10`, 24 requests, 10 PDFs, about
48 s):

| Source | Checked | New | Changed | Unchanged | Already in corpus | Errors | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Pakistan Code | 4 | 0 | 0 | 0 | 4 | 0 | ok |
| Khyber Pakhtunkhwa Code | 4 | 4 | 0 | 0 | 0 | 0 | ok |
| Federal Shariat Court | 3 | 2 | 0 | 0 | 0 | 0 | stopped: PDF cap of 10 reached |

**Run 2** (same command, straight after):

| Source | Checked | New | Changed | Unchanged | Already in corpus | Errors | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Pakistan Code | 4 | 0 | 0 | 4 | 0 | 0 | ok |
| Khyber Pakhtunkhwa Code | 4 | 0 | 0 | 4 | 0 | 0 | ok |
| Federal Shariat Court | 2 | 0 | 0 | 2 | 0 | 0 | stopped: PDF cap of 10 reached |

**What's in the schema:**
- 4 Pakistan Code statutes stored as baseline: they're already in our corpus;
- 4 KP statutes, staged;
- 2 Federal Shariat Court judgments, staged.

Run 2 found every document unchanged. The public schema has no scraping
tables.

## What works, what doesn't, what's left

**Works:**
- the generic scraper for 3 sources, end to end, live;
- robots.txt and politeness limits;
- change detection with old versions kept;
- the corpus baseline;
- run summaries with per-source counts;
- the stats fields and the Research page line;
- the migration, up and down on a throwaway schema;
- 26 offline tests.

**Doesn't / not built:**
- selectors for the other 12 reachable sources;
- the review screen for staged documents;
- the staged-to-index path, which is documented only;
- OCR for scanned PDFs: a judgment with no text layer would be stored with
  empty text. None was hit in the live runs.

**Left:**
- approval of the merge;
- then applying `a3c5e7f90b12` to the shared database;
- then letting the CLI write to the public schema.
