# Scraping demo (mock presentation)

A live, polite run of the scraping prototype into the throwaway schema
`scrapelive_1791254533`:
- run once, and the run finds something new;
- run again, and it reports **0 new**;
- then list what was staged.

Nothing touches the app's own tables, and no AI calls are made.

**Before the demo:**
- the worktree `E:\Users\fyp-legalease-ai-main\legalease-scraping` exists,
  on branch `scraping`;
- the main folder can stay on `master` at the tag;
- the internet is up.

Each run takes about 30–45 s. That's on purpose: the scraper waits 2
seconds between requests to the same site.

## Commands (PowerShell, from the main backend folder)

```powershell
cd E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend
venv\Scripts\activate
$env:HF_HUB_OFFLINE = "1"
$S = "scrapelive_1791254533"
$W = "..\..\legalease-scraping\scripts"
```

**1. First run:** three Federal Shariat Court judgments, the first two
already stored.
```powershell
python $W\scrape_laws.py --schema $S --sources "Federal Shariat Court" --limit 3 --corpus ..\data\processed\statutes\legal_statutes_corpus.json
```
Expected:
- `unchanged` twice and `new` once;
- the summary line `checked 3  new 1  changed 0  unchanged 2  errors 0`.

**2. The same command again:** shows change detection.
```powershell
python $W\scrape_laws.py --schema $S --sources "Federal Shariat Court" --limit 3 --corpus ..\data\processed\statutes\legal_statutes_corpus.json
```
Expected: `checked 3  new 0  changed 0  unchanged 3  errors 0`.

**3. What is staged:** title, source, URL, fetch date and hash, never the
text.
```powershell
python $W\scraping\list_staged.py --schema $S
```

Each stored document becomes "unchanged" in later runs. To show something
new again (after a rehearsal, for example), raise `--limit` by one:
`--limit 4`, then `5`, and so on. The Shariat Court list has 21 judgments
and the KP Code list has 10 statutes. As of 2026-10-06 10:59, the stored
items are:
- Federal Shariat Court: the first 2;
- KP Code: the first 5;
- Pakistan Code: the first 4 under "A", all already in our corpus, so stored
  as baseline.

## What to say

- "It's a polite crawler. It identifies itself with a contact address,
  reads each site's robots.txt, waits 2 seconds between requests, and stops
  at a per-run cap."
- "It compares a hash of each document's text with the version it stored
  last time. Unchanged documents aren't stored again. A changed one gets a
  new version, and the old one is kept."
- "Everything lands staged, with its source URL and fetch date. Nothing
  reaches search or the chat until a person approves it. Judgments stay
  staged, so the app remains statutes-only."
- "We checked 19 Pakistani law sites. 3 work end to end. 12 allow it but
  need their own parser. 2 are blocked: Lahore High Court's robots.txt, and
  the Supreme Court refuses our crawler. We respect both. 2 didn't answer."

## If a site is slow or unreachable

- **Slow:** that's mostly the deliberate 2-second spacing, plus large PDFs.
  Say so. Each request has a 30 s timeout and 3 retries with back-off, so a
  run never hangs indefinitely. Worst case is about 2 minutes for this
  command.
- **One site fails:** the run still finishes. The summary shows `errors N`
  and a status such as `listing failed: ConnectionError`, and the other
  sources are unaffected. Say: "The site is down right now; the run records
  the error and moves on."
- **Fallback 1, a different site:** run the same commands with
  `--sources "Khyber Pakhtunkhwa Code" --limit 6`. That shows 1 new, then
  0 new.
- **Fallback 2, no network:** open
  `E:\Users\fyp-legalease-ai-main\scraping_demo_backup_2026-10-06.txt`. It's
  the saved output of a real run and its repeat, with the staged list (4
  unchanged + 1 new, then 5 unchanged and 0 new). Or show
  `docs/architecture/scraping.md` § "Live runs".
- **Fallback 3, the database is unreachable:** add `--dry-run`. It fetches
  and compares without writing, so with no database it reports every
  document as new. Say that it couldn't compare.

## Don't

- Don't run without `--schema`. The script refuses anyway: the shared
  database has no scraping tables until the merge is approved.
- Don't drop or reuse `scrapelive_1791254533` until you decide to.
- Don't merge the `scraping` branch before the mock.
