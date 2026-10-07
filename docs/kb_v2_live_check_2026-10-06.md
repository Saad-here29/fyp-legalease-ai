# kb-v2 live check (2026-10-06, evening)

**Setup.** Both servers ran from the `legalease-kb` worktree (branch `kb-v2`,
commit `145007c` plus docs):
- **Backend** on port 8000 against the **shared database**, started with
  `KB_V2=true` set at launch;
- **Frontend** on port 5173.

`/health` confirmed the mode: `{"kb_v2":true,"v1_index_chunks":53739,"v2_index_chunks":11289,"threshold":0.65}`.

**What was not touched:**
- master (`9c1992a`), the tag `mock-2026-10-07` and the main folder;
- no migration was applied (the scraping tables are absent);
- nothing was deleted.

**Accounts:** new throwaway accounts were used, and left in place (see the
end).

**Groq tokens:** read from the backend log (`LLM usage: … total=N`), with a
cap of 40,000. **Used: 15,913. No 429 or rate-limit line appeared.**

| Step | Groq tokens | Model calls | Result |
|---|---:|---:|---|
| a) Contracts | 2,242 | 1 (draft) | Works, including the edit |
| b) Document Analysis | 3,232 | 1 (summary) | Works; NER loads from the worktree |
| c) AI Chat, 5 questions | 7,564 | 8 | 3 answered, 2 refused (one of them wrongly, see Q3) |
| d) Research, 6 searches | 2,460 | 6 (query rewrite) | Works; the category filter drops key laws |
| e) Case flow | 0 | 0 | Works |
| UI tour (pages only, one Research page load) | 415 | 1 | All 7 pages load, no console errors |
| **Total** | **15,913** | 17 | |

Note: Research is not model-free. Every search runs the LLM query rewrite
(about 400 tokens), in both modes.

## 1. Running from the worktree on the shared database

- **Copies (all git-ignored; the originals were only read):**
  - the old FAISS index (byte-identical SHA-256);
  - the NER weights (542,002,832 bytes, same as the original);
  - `backend/.env`;
  - `frontend/node_modules`.
- **`KB_V2`** comes only from the launch environment.
- **`/health`, login, dashboard, cases, contracts, Knowledge Base, Research
  and AI Chat** all worked: through the API, and in a headless browser
  through the worktree frontend.
- **Missing scraping tables:**
  - **Runtime code that reads them:** only `app/scraping/stats.py`, behind the
    Research page's "Sources checked" line. It checks
    `has_table("scrape_runs")` first and returns "not available", so the line
    is hidden.
  - **`app/scraping/runner.py`:** writes them, but runs only from
    `scripts/scraping/scrape_laws.py`, never from the server.
  - **`create_all`:** runs only on SQLite, so the server never tries to
    create them.
  - **No errors** in the backend log.
- **One harmless issue:** without `PYTHONIOENCODING=utf-8`, Windows' cp1252
  console prints "Logging error … UnicodeEncodeError" tracebacks for log lines
  with a non-Latin hyphen (seen twice, on Research query rewrites). The
  requests still return 200. The runbook sets the variable.

## 2. Results

### a) Contracts (first live run of the edit path)

**Account:** `eval.b5.lawyer…` (lawyer).

| Step | Result |
|---|---|
| Draft NDA (both parties with full addresses, 7 Oct 2026, three years) | 201; version 1, 8,115 characters, 13.6 s for the whole step; 2,242 tokens |
| Compliance check, v1 | 200; **all 4 clauses pass** (confidentiality, term, governing law, remedies); no unfilled placeholders |
| **Edit** (`POST /contracts/{id}/versions`: "three (3) years" → "five (5) years" + an addendum) | **201; version 2 created** (8,197 characters). Its compliance check ran automatically: all 4 pass, and the term snippet now reads "five (5) years" |
| History (`GET …/versions`) | **Both versions listed**: v1 (8,115 chars, compliance all pass), v2 (8,197 chars, contains "five (5) years", compliance all pass) |
| Contract after the edit | `latest_version` = 2 |

**Worth knowing:** the contract's stored `fields` still say "three (3) years"
after the edit. Editing changes the text, not the form fields it was drafted
from. This is expected, but a viewer comparing the two might notice.

### b) Document Analysis

**Document:** `docs/demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf`.

| Step | Result |
|---|---|
| Upload | 201; 6,856 characters extracted (text layer) |
| Analyse | 200 in 5.5 s; 3,232 tokens |
| Summary | 4,524 characters, starting "The Supreme Court of Pakistan heard a criminal petition filed by Nadar Khan seeking leave to appeal a Peshawar High Court decision that refused him bail…"; 6 key clauses, 8 risks |
| NER | `ner_available: true`, `entities_source: ner_model`. Entities: 15 PER, 4 DATE, 4 LOC, 3 APPEALCASENO, and 1 each of ORG, CASENO, APPEALCOURT, REF, MONEY, REFCOURT, plus 1 of a type labelled "Approved" |
| NER weights | Loaded from the worktree's copy: log "Loading NER model from storage\models\legal_ner" (relative to the worktree backend) → "NER model ready" |

**Looks wrong:**
- **Parties:** the list includes "SUPREME COURT OF PAKISTAN" (a court, not a
  party).
- **Entity labels:** one entity type is labelled "Approved", which isn't one
  of the model's real labels. Probably a stray line ("Approved for
  reporting") tagged as a label.

Both are NER-model output, unchanged by kb-v2.

### c) AI Chat, `KB_V2` on

**Setup:** a new conversation per question, one minute apart. The lawyer
account, the live LLM query rewrite, and the 0.65 threshold.

| # | Question | Expected section | Answer (first lines) | Sources shown (Act - section heading; link) | Response time | Tokens | Reviewer grade |
|---|---|---|---|---|---:|---:|---|
| Q1 | What is the punishment for theft under the Pakistan Penal Code? | PPC s.379 (theft defined s.378) | "The basic punishment for theft … imprisonment for a term which may extend to three years, or a fine, or both [1]", then aggravated forms (ss.380-382) | PPC, 1860 - s.379 Punishment for theft; s.382; s.380; s.381; s.108 Abettor. Each with "Record in Knowledge Base" | 4.9 s | 1,971 | |
| Q2 | What is the procedure for talaq under the Muslim Family Laws Ordinance? | MFLO s.7 | "…a wife's delegated right to talaq, or any divorce other than talaq, must be carried out in accordance with … Section 7 … mutatis mutandis…" (answers mainly from s.8) | MFLO - s.7 Talaq; s.4 Succession; s.3; s.8 Dissolution of marriage otherwise than by talaq; s.13 Omitted | 3.7 s | 2,613 | |
| Q3 | Can a Muslim wife get her marriage dissolved on the ground of cruelty? | DMMA s.2(viii) | **Refused** ("outside my scope") | none | 1.3 s | 390 | |
| Q4 | What is a suit for restitution of conjugal rights? | FCA Schedule item 4 (and s.5) | "a court action that seeks a decree compelling a spouse to resume marital co-habitation … under the West Pakistan Family Courts Act it can be raised as part of the written statement…" | FCA, 1964 - s.9 Written statement; **Schedule item 4 Restitution of conjugal rights**; MFLO s.4; DMMA s.3; Child Marriage Restraint Act s.3 [Omitted] | 4.1 s | 2,223 | |
| Q5 | Can you recommend a good cricket bat? | refusal | Refused | none | 0.8 s | 367 | |

**Links:** every v2 source carries its record id. The chat page renders it as
"Record in Knowledge Base", because no record has a `source_url` yet.
**Checked in the API response; the rendered chat page wasn't seen with a
live answer** (the UI tour sent no message).

**What went wrong, and why:**
- **Q3 was refused.** The LLM query rewrite turned it into "khula on grounds
  of cruelty for Muslim wife", which reaches no passage at 0.65 **in either
  mode**: OFF best 0.609, ON best 0.636 (checked offline with the same
  index). The raw question passes in both: OFF 0.723, ON 0.767, DMMA. So this
  is a rewrite problem, not a kb-v2 one. The demo's wording, *"On what
  grounds can a Muslim wife obtain a decree for dissolution of marriage?"*,
  scores ON 0.899 (DMMA s.2 first) vs OFF 0.838 (raw).
- **Q1:** the right section is cited ([1] = s.379), but the answer text says
  "Section 378 (unverified)". The model mixed up the definition and the
  punishment section, and the citation check flagged it as unverified.
- **Q2:** cites s.7 but explains it badly. It answers from s.8 and describes
  s.7 as "filing a petition, serving notice, and obtaining a decree". s.7
  is actually notice to the Chairman, an Arbitration Council, and 90 days.
  Keep avoiding the talaq question in the demo.
- **Q4:** good. The new Schedule item record reaches the model and is cited.
- **Two weak sources:** a near-empty "[Omitted]" section (Child Marriage
  Restraint Act s.3) and MFLO s.4 Succession appear as low-ranked sources.

**Offline, same rewrites, top-1 OFF vs ON** (no tokens):

| Query (as rewritten live) | OFF top-1 | ON top-1 |
|---|---|---|
| "Section 378 theft punishment Pakistan Penal Code" | CrPC (0.856), **wrong Act** | PPC s.379 (0.887) |
| "talaq procedure under Muslim Family Laws Ordinance" | MFLO, unsectioned chunk (0.721) | MFLO s.7 (0.826) |
| "petition for restitution of conjugal rights under MFLO" | FCA chunk (0.726) | FCA s.9 (0.764), Schedule item 4 next (0.761) |

### d) Research

**Setup:** top 5, with the LLM rewrite (live); "with filter" = the category
filter.

| Query | Filter | Top 3 (section, heading, tier, score) | Tokens |
|---|---|---|---:|
| bail in a non-bailable offence | none | **CrPC s.497 When bail may be taken in case of non-bailable offence (0.825)**; s.496; s.498A | 417 |
| | Criminal Laws | Extradition Act 1972 (0.706); Security of Pakistan Act 1952; Terrorist Affected Areas Act. **CrPC is gone** | 416 |
| khula procedure | none | MFLO s.3 (0.781), s.4 (0.777), s.7 Talaq (0.765). None of these is about khula. In our records the FCA mentions it in s.9(1b) (a wife may claim dissolution including khula) and Schedule item 1; neither is in the top 5 | 385 |
| | Family Laws | Child Marriage Restraint s.3 [Omitted] (0.776); s.10; DMMA s.6 Repeal. **MFLO and the FCA are gone** | 383 |
| share of a daughter in inheritance | none | MFLO s.4 Succession (0.823); Companies Act 2017 (0.703); Succession Act s.58 | 428 |
| | Family Laws | Child Marriage Restraint s.3 [Omitted]; DMMA s.4; Child Marriage Restraint s.10. **Not useful** | 431 |

**Coverage line:** "Filters cover laws with known metadata (500 of 895)".

**Defect: the category filter hides the most important laws.** CrPC, PPC,
QSO, MFLO, the Family Courts Act, the Constitution and the Shariat Act are in
**no Pakistan Code category listing**, so their category is empty and any
category filter drops them. So the filter gives worse results exactly for
criminal and family questions.

**Fix options, not done:**
- a LegalEase-assigned category for these core laws, clearly labelled as
  ours, not Pakistan Code's;
- or hide the category filter until then.

**Second defect: near-empty "[Omitted]" sections** score high for unrelated
queries (Child Marriage Restraint Act s.3, 0.776 for "khula procedure").
Excluding records with almost no text from the index would fix it.

### e) Case flow (API, lawyer and client)

| Step | Result |
|---|---|
| Lawyer creates a criminal case with the client's email | 201, status **assigned** automatically |
| In the lawyer's list | yes |
| Mark as in progress | 200, `in_progress` |
| Edit next hearing (20 → 27 Oct) | 200 |
| Timeline | Case opened → Client linked → created → assigned (automatic) → Next hearing 20 Oct → assigned → in_progress → Next hearing 27 Oct (was 20 Oct) |
| Client sees the case / opens it | yes / 200 |
| Client tries to change status / create a case | **403 / 403** (as designed) |
| Lawyer stats | 1 active; upcoming hearing 27 Oct listed |

## 3. Recommendation: **KB_V2 ON for the demo, with the fallback ready**

**Reasons:**
1. **Everything works with it on.** Every module was run live from the
   worktree on the shared database: contracts incl. the edit, documents with
   NER, chat, research, cases, the Knowledge Base page.
2. **It finds the right section where OFF doesn't.**
   - **Live rewrites:** theft gets PPC s.379 instead of CrPC chunks; talaq
     gets MFLO s.7 (0.826 vs 0.721); the demo's DMMA question scores 0.899
     vs 0.838.
   - **Gold set** (earlier work): 14/26 vs 7/26 at top 5, with the same
     off-topic refusals.
3. **Answers can cite "Act - s.N Heading"** and link to the stored record.
   The Knowledge Base page shows where each record came from.
4. **The fallback takes about a minute** (stop two servers, start two in the
   main folder) and needs no data change.

**Conditions for the demo:**
- **Don't use the Research category filter** on criminal or family queries
  (defect above). Use no filter, or the year filter.
- **Keep the planned chat questions:** DMMA grounds, PPC theft, the
  cricket-bat refusal. Still avoid talaq procedure, khula and inheritance.
  Avoid "cruelty" phrasing: it's refused because of the rewrite, in both
  modes.
- **Start the backend exactly as in `docs/DEMO_RUNBOOK.md`,** and check
  `/health` shows `"kb_v2":true`.
- **Upload the demo PDF in the mode you present from.**

**Against, honestly:**
- **Unmerged code:** the demo would run from a branch that isn't merged or
  reviewed, 33 commits ahead of the mock tag, incl. the scraping
  merge.
- **Grading:** answer quality was not graded by a lawyer.
- **Weak spots:** the two Research defects above are visible if someone
  explores the filters.

## 4. Failed or looks wrong

1. **Q3 (cruelty)** refused, caused by the LLM query rewrite; happens in both
   modes.
2. **Q2 (talaq)** answer misdescribes s.7, in both modes. The talaq question
   remains one to avoid.
3. **Q1** answer text names s.378 for the punishment (cited s.379 correctly;
   flagged "unverified").
4. **Research category filter** drops CrPC, PPC, QSO, MFLO, the FCA, the
   Constitution and the Shariat Act (no Pakistan Code category).
5. **Near-empty "[Omitted]" records** rank high for unrelated queries.
6. **NER:** "SUPREME COURT OF PAKISTAN" listed as a party; an entity type
   labelled "Approved".
7. **Console:** "Logging error … UnicodeEncodeError" tracebacks without
   `PYTHONIOENCODING=utf-8` (harmless; the runbook sets it).
8. **Contracts:** after an edit, the stored form fields don't change, only
   the text (by design).

## 5. Not verified

- **The chat page rendering a live answer's sources** ("Act - s.N Heading" +
  link). The API response contains the fields, and the rendering was tested
  in unit tests and the B4 browser pass, but not with a live chat answer.
- **The master fallback.** It wasn't started in this pass, so as not to stop
  the worktree servers mid-check. It's the same code as the mock tag that
  ran on 2026-10-06.
- **Uploads across modes:** whether the other mode can open a document
  uploaded in one mode (expected: listed with its analysis, original file not
  served).
- **Timing:** response times are single samples.

## Accounts created (left in place)

- `eval.b5.lawyer.10062334@example.com`: lawyer. It owns:
  - contract "Eval B5 NDA" (2 versions);
  - the uploaded demo PDF;
  - case "Eval B5 — Nadar Khan v. The State (bail)";
  - five chat sessions.
- `eval.b5.client.10062334@example.com`: client, linked to that case.

The password is in the session scratchpad (`b5_pw.txt`), not in the repo.
