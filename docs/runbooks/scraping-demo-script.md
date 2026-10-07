# Scraping demo script (dry run, about 90 seconds)

This shows the law-update scraper working live, safely:
- **Dry runs only.** It fetches real pages and PDFs and compares them, but
  writes nothing.
- **No database.** The scraping tables are not in the shared database: their
  migration hasn't been applied, and the dry run doesn't need them.
- **No model calls.**
- **Nothing becomes searchable.**

Checked on 2026-10-07, branch `kb-v2`.

## Before the demo (once)

Open a **new PowerShell terminal**. Your app servers on 8000/5173 keep
running; this doesn't touch them.

```powershell
cd E:\Users\fyp-legalease-ai-main\legalease-kb
$PY = "E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend\venv\Scripts\python.exe"
$C  = "..\fyp-legalease-ai-main\data\processed\statutes\legal_statutes_corpus.json"
$env:PYTHONIOENCODING = "utf-8"
```

Run command 2 once beforehand. It checks the sites are up, and its saved
hashes make step 4 show "unchanged". Each command takes 10-15 seconds,
because the scraper waits 2 seconds between requests to a site.

## The commands (paste one at a time)

```powershell
# 1. Pakistan Code (federal statutes)
& $PY scripts\scraping\scrape_laws.py --dry-run --sources "Pakistan Code" --limit 2 --corpus $C

# 2. Khyber Pakhtunkhwa Code (provincial statutes); remembers the hashes
& $PY scripts\scraping\scrape_laws.py --dry-run --sources "Khyber Pakhtunkhwa Code" --limit 2 --corpus $C --out $env:TEMP\kp_run1.json

# 3. Federal Shariat Court (judgments: staged only, never shown in the app)
& $PY scripts\scraping\scrape_laws.py --dry-run --sources "Federal Shariat Court" --limit 2 --corpus $C

# 4. Khyber Pakhtunkhwa Code again, compared with run 2: change detection
& $PY scripts\scraping\scrape_laws.py --dry-run --sources "Khyber Pakhtunkhwa Code" --limit 2 --corpus $C --compare-with $env:TEMP\kp_run1.json
```

`--out` writes to your temp folder, not the repository. Nothing else is
written.

## What to point at

Output of command 2 (2026-10-07):

```
[Khyber Pakhtunkhwa Code] https://kpcode.kp.gov.pk/homepage/recent_updated: 10 items
  new       THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025. (54961 chars)
  new       THE KHYBER PAKHTUNKHWA PROVINCIAL ASSEMBLY (POWERS, IMMUNITIES AND PRI (42574 chars)
...
Summary (dry run: nothing was written)
Source                   URL                                                Status  Hash      Would stage  Indexed
Khyber Pakhtunkhwa Code  https://kpcode.kp.gov.pk/homepage/lawDetails/1619  new     30919254  yes          no
Khyber Pakhtunkhwa Code  https://kpcode.kp.gov.pk/homepage/lawDetails/1618  new     a133f126  yes          no
2 documents: 2 new, 0 changed, 0 unchanged, 0 already in the corpus, 0 failed. 6 requests. Indexed: none (staged documents wait for review).
```

**Point at:**
1. **"Summary (dry run: nothing was written)"** and the **Indexed: no**
   column. Nothing fetched becomes searchable.
2. **The Hash column:** a fingerprint of each law's text.
3. **"6 requests":** a handful of polite requests, 2 seconds apart.

**Command 1 (Pakistan Code)** shows **baseline / "no (already in corpus)"**:
- "Abandoned Properties (Management) Act, 1975" (hash 92d7a166);
- "Abolition of the Discretionary Quotas in Housing Schemes Act, 2013".

The scraper recognises laws we already hold and doesn't report them as new.

**Command 3 (Federal Shariat Court)** shows two judgments as "new":
"Prohibition of attempt to commit Suicide" and "Chaddar or Parchi". They
would be staged, but the app is statutes-only, so judgments are never shown
to users.

**Command 4** is the change detection:

```
Comparing with ...\kp_run1.json (2 documents)
Khyber Pakhtunkhwa Code  https://kpcode.kp.gov.pk/homepage/lawDetails/1619  unchanged  30919254  no (same hash)  no
Khyber Pakhtunkhwa Code  https://kpcode.kp.gov.pk/homepage/lawDetails/1618  unchanged  a133f126  no (same hash)  no
2 documents: 0 new, 0 changed, 2 unchanged, ...
```

**Same hash means unchanged, so nothing is staged.** If the site had amended
the Act, the hash would differ. The row would say **changed**, and a real
run would stage the new version and keep the old one.

## 90-second script (simple English)

> "Laws change, so LegalEase has a scraper that checks official Pakistani
> law websites for new and amended laws.
>
> **First, a whitelist.** It only visits sources we listed and checked, in
> `scripts/scraping/sources.json`: Pakistan Code, the Khyber Pakhtunkhwa
> Code and the Federal Shariat Court. It doesn't crawl the web.
>
> **Second, it fetches politely.** It reads each site's robots.txt and obeys
> it. It says who it is in every request, waits two seconds between
> requests, and stops at a small page limit. Here it made six requests.
>
> *(run command 2)*
>
> **Third, change detection.** It turns the text of each law into a
> fingerprint, this hash. Next time it compares fingerprints. *(run command
> 4)* Same fingerprint: unchanged, nothing to do. A different fingerprint
> would mean the law was amended. It would be kept as a new version, and the
> old version is never deleted. Laws we already have, like these from the
> Pakistan Code, are recognised and not reported as new. *(command 1)*
>
> **Fourth, staging before indexing.** Anything new is only staged, waiting
> for a person to review it. As the last column says, nothing is indexed: a
> scraped law can't appear in a chat answer until it's approved and the
> search index is rebuilt.
>
> **Finally, provenance.** For every document we keep where it came from
> (the page and the PDF link) and when we fetched it. So every answer can
> be traced back to its source and date."

## Honest limits

- **Coverage:** only **3 of the 19 sources** we surveyed are verified and
  switched on.
  - **12 need a custom parser.**
  - **2 are blocked:** the Lahore High Court's robots.txt disallows us, and
    the Supreme Court site refuses automated requests.
  - **2 weren't reachable.**
- **Schedule:** the **weekly schedule is written but not switched on.**
  Every run so far was started by hand.
- **Storage:**
  - **The scraping tables exist only in a throwaway test schema.** Their
    migration hasn't been applied to the shared database, so today's demo
    is a dry run, compared against a saved earlier run instead of the
    database.
  - In a real run, new and changed documents are stored in the staging
    table, with their source URL, PDF link and fetch time.
- **Indexing:** **nothing scraped is indexed without review.** The search
  library the app uses today was built separately; no scraped text has been
  added to it.
- **Judgments:** the Federal Shariat Court judgments are staged only. The
  app answers from statutes, and no judgment is shown to users.

## If something goes wrong

- **A site is slow or down:**
  - its row shows `listing failed` or an error count, and the other sources
    still run;
  - say that the scraper records failures and retries next time;
  - show this document's saved output instead.
- **No internet:** use the saved output above. The tests also cover all of
  this offline: `backend\app\tests\unit\test_scraping.py`, including "dry
  run compares with an earlier run without a database".
