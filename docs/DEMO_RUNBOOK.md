# Demo runbook (2026-10-07)

Two ways to run the demo. Both use the **same shared database and the same
accounts**, on the same ports, so you can switch between them in a minute.

| Mode | Code | Search | Knowledge Base page |
|---|---|---|---|
| **Primary: kb-v2** | `legalease-kb` worktree, branch `kb-v2` | `KB_V2=true`: section-level index first, then the old index | Yes |
| **Fallback: master** | main folder, tag `mock-2026-10-07` / master `9c1992a` | the old index only | No |

Use **PowerShell**, one terminal per server, and start them yourself.
Close any terminal that still runs the other mode first (ports 8000 and 5173).

## Primary: kb-v2 from the worktree

**Terminal A: backend** (http://localhost:8000)

```powershell
cd E:\Users\fyp-legalease-ai-main\legalease-kb\backend
$env:KB_V2 = "true"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:PYTHONIOENCODING = "utf-8"
E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

**Terminal B: frontend** (http://localhost:5173)

```powershell
cd E:\Users\fyp-legalease-ai-main\legalease-kb\frontend
npm run dev
```

**What these commands rely on.** Each of these is set up already, and none
of them changes the main folder:

- **Python environment:** the main folder's `venv`. It's only run, not
  changed; the worktree has no venv of its own.
- **`.env`:** `backend\.env` is a copy of the main folder's (git-ignored).
  `KB_V2` is not in it; it is set only by `$env:KB_V2` above.
- **Search indexes and NER weights:**
  - `backend\storage\faiss\` holds a byte-identical copy of the old index;
  - `backend\storage\models\legal_ner\` holds a copy of the NER weights;
  - `backend\storage\kb\` holds the v2 records and index.

  All of them are git-ignored.
- **`frontend\node_modules`:** a copy of the main folder's.
- **`PYTHONIOENCODING=utf-8`:** stops "Logging error … UnicodeEncodeError"
  tracebacks when a log line has a non-Latin character. They're harmless
  (the request still succeeds) but alarming on screen.

**Confirm the mode.** Two places show it:

1. **Terminal A's log** shows this line at startup:
   ```
   Search mode: KB_V2=True | v1 index ./storage/faiss/legal_corpus.faiss (53739 chunks) | v2 index ./storage/kb/faiss_v2.faiss (11193 chunks) | threshold 0.65
   ```
2. **http://localhost:8000/health** returns:
   ```json
   {"status":"ok","kb_v2":true,"v1_index_chunks":53739,"v2_index_chunks":11193,"threshold":0.65}
   ```

If it says `KB_V2=False` / `"kb_v2":false`, the variable wasn't set in that
terminal. Stop the server, run `$env:KB_V2 = "true"`, and start it again.

**Ready when:**
- Terminal A prints `NER model ready` and `Application startup complete`;
- the Knowledge Base page shows 35 laws.

## Fallback: master from the main folder (KB_V2 off)

Stop both servers (Ctrl+C in each), then open **new** terminals, so no
`KB_V2` variable carries over.

**Terminal A: backend**

```powershell
cd E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:PYTHONIOENCODING = "utf-8"
venv\Scripts\uvicorn.exe app.main:app --port 8000
```

**Terminal B: frontend**

```powershell
cd E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\frontend
npm run dev
```

**Confirm the mode:**
- **/health** returns only `{"status":"ok"}`. Master predates the mode
  fields, so a missing `kb_v2` field means you are on master.
- **The startup log** has no "Search mode" line.

**Fallback checked 2026-10-07 (kb-v2 B6).** The master backend was started
from the main folder with the command above, plus
`PYTHONDONTWRITEBYTECODE=1` and empty AI keys so the check made no model
calls:
- `/health` answered `{"status":"ok"}`;
- a Research search for "bail in a non-bailable offence" returned 5 results,
  CrPC s.497 first (0.81);
- the server was then stopped, and the main folder showed no changes. Only
  its git-ignored log file for the day was written.

## Changes in kb-v2 B6 (2026-10-07)

- **Category overrides:** `backend/app/kb/category_overrides.json`, one
  documented reason per line. Seven core laws are in no Pakistan Code
  category, so they get a hand-written one:
  - PPC and CrPC: Criminal Laws;
  - Qanun-e-Shahadat: Law of Evidence;
  - MFLO, the Family Courts Act 1964 and the Shariat Act 1962: Family Laws;
  - the Constitution: a new "Constitutional Law".

  The Knowledge Base page labels these "assigned by LegalEase; not in a
  Pakistan Code category listing".
- **The Research category filter now keeps these laws:**
  - Criminal Laws keeps PPC s.379 and CrPC s.497;
  - Law of Evidence keeps QSO Art.17;
  - Family Laws keeps FCA s.9 and Schedule item 4, and MFLO;
  - Constitutional Law keeps the Constitution.

  Filter coverage is now 507 of 895 documents with KB_V2 on (was 500), and
  511 of 900 with it off (was 501).
- **Near-empty sections are kept out of the v2 index.** 96 records:
  - 82 omitted/repealed notes such as "Rep. by A.O., 1937";
  - 14 bare markers.

  They stay in the records and on the Knowledge Base page. The index went
  from 11,289 to 11,193 chunks.
- **Retrieval numbers are unchanged from B3:** gold 14/26 (OFF 7/26),
  off-topic 1/15 (O14). See `docs/kb_v2_comparison_2026-10-06_b6.md`.
- **Still true:** a bare two-word query such as "talaq procedure" or "khula
  procedure" doesn't reach MFLO on its own embedding. In the app the query
  rewrite adds "under Muslim Family Laws Ordinance" and MFLO comes first. So
  the filter works when the rewrite is on (it always is with a Groq key).

## Changes in kb-v2 B7 (2026-10-07): restart the backend to get them

All of these apply only with `KB_V2=true`; the master fallback is unchanged.

- **Exact section lookup.** A question naming a section or article of a law
  we hold puts that record first, marked as the section named in the
  question. Examples: "Section 302 of the Pakistan Penal Code", "u/s 154
  CrPC", "Article 10A of the Constitution". It never fires for foreign laws
  such as "Indian Penal Code".
- **Section numbers reach the model and the citation check.** Each source
  line now reads "Act - s.N Heading", so a retrieved section is no longer
  flagged "(unverified)".
- **Scope gate.** Before the chat refuses, it also searches the raw
  question. A question with clear legal terms (dower, nikah, talaq, family
  court, decree, bail, FIR, "section 9", "… Act") and no foreign country may
  then use passages down to 0.60 (`KB_V2_SCOPE_RESCUE_FLOOR`), shown with the
  weak-match note. Off-topic questions are still refused.
- **Reference completeness.** These now join the "unverified" note:
  - an Act named in the answer but not in the retrieved text;
  - a `[n]` that points to a different Act than its sentence names.

  Grouped markers ("[1, 2]", "[1-3]") are split, so every cited source is
  listed.
- **Progress wording while chat works:** "Searching the legal library…",
  "Reading the sources…", "Writing the answer…". This is frontend-only, and
  the Vite dev server picks it up without a restart.
- **`STRICT_GROUNDING` stays off.** See
  `docs/kb_v2_live_check_2026-10-07_b7.md`.

## Judgments (kb-v2 C2, 2026-10-07): optional, off unless set

Judgments are added to Research, AI Chat and the Knowledge Base only when the
backend starts with `JUDGMENTS_V2=true`. Without it, nothing changes.

**Start (Terminal A),** with the dev index (1,000 chunks, 14 judgments) while
the full pilot is still being built:

```powershell
cd E:\Users\fyp-legalease-ai-main\legalease-kb\backend
$env:KB_V2 = "true"
$env:JUDGMENTS_V2 = "true"
$env:JUDGMENTS_INDEX_PATH = "./storage/kb/faiss_judgments_dev.faiss"
$env:HF_HUB_OFFLINE = "1"; $env:TRANSFORMERS_OFFLINE = "1"; $env:PYTHONIOENCODING = "utf-8"
E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

When the full pilot has finished, drop the `JUDGMENTS_INDEX_PATH` line (the
default is `./storage/kb/faiss_judgments.faiss`) and restart. The index file
is also re-read on its own when it changes.

**Check:** `http://127.0.0.1:8000/health` shows `"judgments_v2": true`,
`"judgment_chunks": 1000`, `"judgments": 14` (dev index). With the full
pilot: about 64,000 chunks and 400 judgments.

**Demo path (about 3 minutes):**
1. **Knowledge Base, Judgments tab.** Point out the counts, the court and
   topic filters, and the yellow "Staged, not yet reviewed" tag. Open
   *Shaista Habib v. Muhammad Arif Habib*: the numbered paragraphs and the
   provenance note ("dataset supplied by the team; original source and
   licence to be confirmed").
2. **Research, Judgments.** Search "custody of minor children welfare".
   Each result is one judgment's best paragraph, with court, year, case
   number and paragraph number; "Read judgment, para N" opens that
   paragraph. Then **All**: statutes first, then "Past relevant cases".
3. **AI Chat.** Ask "Who gets custody of minor children after divorce?".
   Under Sources, the "Case law" group lists the judgment paragraphs the
   answer was given, each linking to its judgment.

**What to say:** judgments are context, never the law itself. The answer
may name a case only as "Case name (Court, year), para N", only from the
paragraphs retrieved, and the check removes any other case and flags a wrong
paragraph number. The dataset's source and licence are still to be
confirmed, so judgments are marked staged.

**Watch out:**
- The dev index holds only 14 judgments, so many questions find none.
- About half the judgments are shown by case number, because their party
  names weren't read cleanly from the first page.
- Each chat answer with cases costs about 900 more Groq tokens.

## Scraped laws (kb-v2 C3, 2026-10-07): optional, off unless set

Add `$env:SCRAPED_V2 = "true"` before starting the backend (Terminal A) to
search and list the scraped laws and judgments. `/health` then shows
`"scraped_v2": true` and the chunk counts (pilot: 2,400 statute chunks,
5,593 judgment chunks).

**Fetch and embed** (in `backend`, in your own terminal; both stop after a
time budget and continue when run again):

```powershell
cd E:\Users\fyp-legalease-ai-main\legalease-kb\backend
$env:HF_HUB_OFFLINE = "1"; $env:TRANSFORMERS_OFFLINE = "1"; $env:PYTHONIOENCODING = "utf-8"
$py = "E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend\venv\Scripts\python.exe"
& $py ..\scripts\scrape_laws.py --stage-files --budget 0          # caps PC 120, KP 60, FSC 100
& $py ..\scripts\kb\build_index_scraped.py --budget 0
```

**Weekly:** `scripts\scraping\register_weekly_task.ps1` registers
`run_weekly.py` every Sunday at 03:00 (run it yourself once).

**Demo path:** Knowledge Base, then "Sources and updates" (fetched, new,
quarantined and searchable per source); a law with the "Scraped" badge
(e.g. Stamp Act, 1899): source link, fetch date, "Under review"; Research
"stamp duty on a bond": Stamp Act sections from the scraped index.

## Document Analysis reasoning (kb-v2 C4, 2026-10-07): optional, off unless set

Add `$env:REASONING_V2 = "true"` before starting the backend. Each Analyse
then makes ONE extra Groq call (about 2k–6k tokens: up to 4,200 of document
text, ~500 of instructions, a 1,500-token reply cap) after the summary and
NER, and the page gets a **Reasoning** tab beside Summary & entities.

**What it shows:** issues, arguments by party, the court's reasoning in
order, holding, statutes cited (linked to the Knowledge Base when the Act
and section are held), strong and weak points, risks, open questions. Each
item has its verbatim evidence quote (expandable) and a "Quote found" badge;
items whose quote isn't in the document, or that name a date, case number,
FIR or section not in it, are removed and counted ("N unverifiable items
removed"). With `JUDGMENTS_V2` on, each issue lists up to 2 related past
cases, labelled as not cited in the document.

**What to say:** the check proves each quote is in the document; it can't
prove the sentence draws the right conclusion from it. Read the evidence.

**Rate limit:** the summary and the reasoning call fall in the same minute,
so on Groq's 8,000 tokens/minute the second call may get a 429. It backs off
(Groq's retry-after, else 5 s, 10 s, 20 s; at most 45 s) and then gives up
with "The AI service is busy …"; the summary and entities still show.

## Differences to know before switching

- **Same data:** same database, same accounts, same cases and contracts.
  Anything created in one mode appears in the other.
- **Uploaded files are not shared.** Each folder keeps its own
  `backend\uploads\`. A document uploaded in one mode is listed in the other,
  with its extracted text and analysis (stored in the database), but its
  original file can't be served by the other folder. That's expected from
  how the upload path is stored; it wasn't tested. For the demo, upload the
  demo PDF in the mode you present from.
- **The Knowledge Base page, the Research filters and section-level
  citations** exist only in kb-v2. In master, those parts of the demo script
  are skipped.
- **The scraping tables** (`scraped_documents`, `scrape_runs`) are not in the
  shared database: their migration was never applied. kb-v2 runs without
  them. The only code that reads them at runtime is the "Sources checked"
  line on the Research page (`app/scraping/stats.py`). It checks that the
  table exists first, and hides the line when it doesn't.

## Demo paths

- **Main demo:** `DEMO_BRIEF.md` § "Demo start checklist" and § "Demo order".
- **Knowledge Base in 60 seconds:** `DEMO_BRIEF.md` § "Knowledge Base in 60
  seconds" (kb-v2 only).
- **Live check of this setup, 2026-10-06:**
  `docs/kb_v2_live_check_2026-10-06.md`.
