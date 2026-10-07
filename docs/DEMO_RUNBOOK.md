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
