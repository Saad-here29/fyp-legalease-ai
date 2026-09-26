# LegalEase AI — Project Context (read this before doing anything)

> Paste or reference this file at the start of every Claude Code session.
> It has no memory of past sessions — this file is its only memory.

## What this project is
LegalEase AI — an AI-powered legal case management + research platform for
Pakistani law (Family Law scope). FYP for NUCES Islamabad, Software Engineering,
Session 2022-2026. Team: Saadullah, Ali Mehmood Khan, Uzair Siddique.

## Current status (fill in / correct before first session)
- FYP-1 finished ~4 months ago. Panel feedback received (see FEEDBACK.md — add this too).
- Modules already built: Case Management, AI Legal Chat, Document Analysis (backend
  endpoint exists but UI was NEVER connected — confirm if still true),
  AI Legal Research, OCR, Auth/Roles, **Contract Drafting & Compliance**
  (built + fully verified end-to-end 2026-09-21 — see "Contract Drafting &
  Compliance status" below).
- **Notifications — confirmed NOT implemented (2026-09-20)**: no backend
  route, model, or service exists at all (`app/main.py` registers exactly 5
  routers — auth, cases, chat, research, documents — nothing else; live
  probes of `/notifications`, `/notifications/`, `/notification` all
  returned `404`). Still purely the frontend "Coming Soon" placeholder from
  the original audit. **Decision: explicitly de-scoped for this
  iteration** — to be documented in the report as planned future work,
  not silently omitted. Priority shifts to the two genuinely missing
  modules below.
- Modules NOT built yet: **Practice Simulator (last missing core module,
  current priority)**. Notifications backend work still deferred past it
  (de-scoped, see above). Legal NER is trained and integrated into
  Document Analysis (2026-09-26) — see "Legal NER status" below.
- UI redesign done (every page on the design system) and accuracy-swept
  2026-09-26 — see "UI accuracy sweep" below.

## ⚠️ Known constraint — Groq free-tier limits (CRITICAL for demo day)
Every AI feature — chat (query rewrite + answer), Research analysis,
Document Analysis summaries, contract drafting — runs on one Groq key,
free ("on_demand") tier, model `openai/gpt-oss-120b`. Its limits, confirmed
2026-09-26 from Groq's own responses:
- **200,000 tokens per day** — the binding limit. Hit on 2026-09-26 after a
  day of retrieval testing: Groq's 429 read "tokens per day (TPD): Limit
  200000, Used 199915". Once exhausted, every AI feature above fails or
  stalls; the rest of the app (login, cases, document upload and text
  extraction, contracts list) keeps working, and Legal Research search
  still returns results but with the raw question (its LLM query rewrite
  falls back silently), so matches are less precise.
- **8,000 tokens per minute** and **1,000 requests per day** (from the
  `x-ratelimit-*` headers). A chat answer needs ~5,000 tokens including its
  reserved reply, so back-to-back questions are paced by the SDK retrying
  Groq 429s (8–16 s waits) rather than failing.
- **What 200k/day means:** roughly **35–40 chat answers per day** in total,
  across all users and all testing.
- **Recovery is a rolling 24-hour window, ~8k tokens/hour on average** —
  but only on average: tokens come back 24 hours after they were spent, so
  recovery follows the previous day's usage. A heavy testing burst means a
  lockout at the same time the next day.

**Demo-day plan:**
1. **Do not run heavy testing on demo day**, or in the 24 hours before the
   demo slot — anything spent then is unavailable during the demo.
2. **Strongly consider a paid Groq tier** (Dev tier, console.groq.com →
   Settings → Billing) for the demo period, **or a dedicated demo-day API
   key kept completely unused until then** — switch `GROQ_API_KEY` in
   `backend/.env` to it on the day and restart the backend. **The key must
   come from a separate Groq account/organisation:** Groq meters limits per
   organisation (its 429 names `organization org_…`), so a second key in the
   same account shares the same 200k/day.
3. Rehearse with the questions you'll show, the day *before* the day
   before — then leave the budget untouched.
4. If the budget runs out mid-demo, the app degrades rather than crashes:
   cases, document upload and research search still work; AI answers
   return an error toast. Keep a recorded fallback (the documented real-document run in
   `docs/demo_examples.md`) ready to show instead.

## Backend / database status (confirmed 2026-09-13)
- `backend/app/models/` was found completely missing on audit (every router/
  service imported ORM classes — User, Case, Document, ChatSession, etc. —
  from modules that did not exist on disk, so the backend could not start
  at all). Fully reconstructed field-by-field from actual usage in routers,
  services, and schemas, cross-checked against `docs/database-schema.md`.
  Verified against the real test suite, not just import — **31/31 backend
  tests passing** (`pytest`, run from `backend/venv`, Python 3.11.9).
- Database: **Supabase Postgres**, connected via the **Transaction Pooler**
  (`aws-0-ap-southeast-1.pooler.supabase.com:6543`), not the direct
  connection host. The direct host (`db.<project-ref>.supabase.co:5432`) is
  IPv6-only and is unreachable from this network/machine (`getaddrinfo`
  fails — no IPv6 route, even though the AAAA DNS record itself resolves
  fine). Always use the pooler connection string from here on for this
  environment.
- Migration `initial schema` (revision `2b7806a018fc`) generated via
  `alembic revision --autogenerate` and applied via `alembic upgrade head`.
  Created all 12 model tables + `alembic_version` on the live Supabase DB.
- Backend confirmed booting cleanly end-to-end: `uvicorn app.main:app
  --reload` starts with no errors, connects to the live DB, auto-seeds the
  legal corpus, and serves `GET /` and `GET /health` with 200 responses.
- Known gap: **Tesseract OCR is not installed locally** — `TESSERACT_CMD` in
  `.env` points to a path that doesn't exist on this machine. The backend
  still boots fine (it only logs a warning), but scanned-image/PDF OCR will
  not work until Tesseract is actually installed and the path is corrected.

## Git / repository status (confirmed 2026-09-13)
- Project had **no git repository at all** before this session — `git init`
  run in the project root for the first time.
- Remote `origin` = `https://github.com/Saad-here29/fyp-legalease-ai.git`,
  already had one prior commit from FYP-1 (`4d0339f`) on `main`, which we
  fetched and rebased onto rather than overwriting.
- History is now **two commits on `origin/main`**, pushed and confirmed live:
  - `4d0339f` — original FYP-1 deliverable commit (pre-existing on GitHub).
  - `e4d9508` — this session's work: `backend/app/models/` reconstruction,
    the initial Alembic migration, and the folder-structure cleanup below.
- Local branch is named `master` (tracks `origin/main` via
  `git branch --set-upstream-to`) — intentionally left as `master` rather
  than renamed, so don't be surprised it doesn't match the remote branch name.
- Folder-structure cleanup done this session (all reversible file moves —
  no backend logic touched): archived the stale root `Claude.md` (described
  an old Node/Mongo rebuild plan) into `Documents and Reports/`; fixed
  several pre-existing filename typos (`Algortihm 1.png`, `Agorithm2.png`,
  `State transition  DIagram...pdf`); removed the empty
  `ai-services/corpus-builder/` duplicate (`docs/folder-structure.md`
  corrected to reference the real `corpus_builder/` package — Python
  identifiers can't contain hyphens); deleted the dead
  `frontend/src/features/legal-research/data.js`; removed three backend
  packages that were empty placeholders with zero real code
  (`app/ai/prompts/`, `app/ocr/`, `app/validators/`). Also fixed two
  `.gitignore` bugs found along the way: it was excluding
  `alembic/versions/*.py` (migrations must be tracked) and had a bare
  `models/` rule that was silently also matching `backend/app/models/`.
- Not yet done (deliberately deferred, needs its own approved pass): moving
  hardcoded prompt strings into `app/ai/prompts/`, and deciding whether to
  fully adopt or drop the `repositories/` pattern and the frontend
  `services/` folder — both would require editing import statements across
  multiple files, not just moving files around.

## AI Chat / Research status — fully validated end-to-end (confirmed 2026-09-20)
- **FAISS index rebuilt**: 901 documents → **53,739 chunks** (800 chars /
  100 overlap), built by `ai-services/corpus_builder/build_corpus.py` from
  the cleaned `data/processed/statutes/legal_statutes_corpus.json`. Covers
  family, criminal, commercial/banking, property, and other domains of
  Pakistani law — **no longer family-law-only**. (The `88,036 chunks from
  2,600 documents` figure previously in "Tech stack" below was from an
  earlier, unrelated build and is now stale — corrected below.)
- **Query-rewrite step added**: `backend/app/ai/query_rewrite.py`. Real user
  questions are long/conversational and multi-clause; statute text is short
  and precise, so embedding the raw question directly under-matched. Any
  query over ~150 chars now gets LLM-compressed into a short, focused
  search query *before* embedding (e.g. a 280-char tenancy complaint became
  "Recovery of security deposit from landlord under Pakistani tenancy law,
  remedies for unlawful delay"). Wired into both `ResearchService.search()`
  and `LegalChatService.send()` — the original text is still what's stored/
  shown to the user; only the embedding/search call sees the rewritten
  version. Falls back to the raw query untouched if the AI provider is
  unavailable, so it never breaks retrieval.
- **500-char query-length bug — fixed**: `ResearchSearchRequest.query`
  `max_length` raised from 500 to 2000 (was rejecting ~10% of real eval
  questions with a `422 string_too_long`).
- **`RAG_SIMILARITY_THRESHOLD` tuned 0.7 → 0.65**, based on the real
  78-question eval set (`data/processed/qa_eval/Legal_QA_dataset_From_lawyers_clean.csv`
  through `/api/v1/research/search`), run twice — before and after the
  query-rewrite fix:
  | | before rewrite | after rewrite |
  |---|---|---|
  | scored / 78 | 70 (8 × 422) | 78 (0 errors) |
  | mean | 0.583 | 0.649 |
  | median | 0.596 | 0.656 |
  | pass rate @ 0.7 | 1.4% | 25.6% |

  At 0.65, everything in the 0.65–0.8+ band passes (~55–60% of real
  questions) while the genuinely weakest matches (<0.6, ~20–25%) still
  correctly refuse. Full per-question results:
  `data/processed/qa_eval/retrieval_eval_results.json`.
- **End-to-end verification after both fixes + the threshold change**:
  - 3 in-scope questions (family: khula grounds under MFLO; criminal: PPC
    theft punishment; commercial: AML suspicious-transaction reporting) all
    returned real, cited Groq-generated answers — including the AML one,
    which scored 0.6887 under the old 0.7 threshold (borderline refusal)
    and now passes cleanly at 0.65.
  - 3 out-of-scope questions (weather, baking a cake, capital of France)
    still correctly refused, with a wide safety margin — scores 0.27–0.46,
    well clear of the new 0.65 cutoff (nowhere near the weakest genuine
    legal-question scores, ~0.50).
- **AI provider: Groq, model `openai/gpt-oss-120b`** — not
  `llama-3.3-70b-versatile`, which was **retired from Groq's catalog**
  (confirmed via `GET /v1/models`, got a 404 `model_not_found` before
  switching). `backend/.env`'s `GROQ_MODEL` updated accordingly.
- Retrieval verified 3 ways throughout this work: direct
  `embeddings.search()`, the live `/api/v1/research/search` endpoint, and
  live HTTP with a real signed-up/verified/logged-in test user + JWT. All
  three agree.
- **Known limitation — broad multi-topic questions may be refused**
  (observed 2026-09-26, deliberately not fixed). A single message spanning
  many distinct legal issues — e.g. talaq notice, khula grounds,
  maintenance, dower and custody jurisdiction all at once — was refused as
  out-of-scope: no single retrieved passage scored above the 0.65
  threshold, because one query embedding spread across that many issues
  matches none of them strongly. Focused single-topic versions of the same
  questions answer normally. This is a documented boundary for the report:
  users should ask one clear legal question at a time, much as a lawyer
  would want a client to ask one clear question rather than six mixed
  together.
- **Known limitation — Urdu khula question misses the relevant statute**
  (observed 2026-09-27, future work, not urgent). "خلع کیا ہے اور عورت
  عدالت سے خلع کیسے لے سکتی ہے؟" (what is khula and how can a woman obtain
  it from the court?) retrieved a single, unrelated Code of Criminal
  Procedure passage, so the answer honestly said the library has no khula
  provision — although the Muslim Family Laws Ordinance, 1961 (dissolution
  of marriage) is indexed. Likely the same terminology-mismatch pattern as
  the earlier English divorce/talaq fix, which taught the query rewrite to
  map everyday wording onto the statutes' terms but hasn't been extended to
  Urdu phrasing. Next step: replay a handful of Urdu family-law questions
  through `rewrite_search_query` and compare the rewrites and retrieved
  passages with their English equivalents (offline apart from the rewrite
  calls — mind the Groq token budget).

## Reliability pass — citations, DB connections, output polish (confirmed 2026-09-26)
Committed `cbc48ad` and `1c32ff3`, pushed to `origin/main`. Full backend
suite **57/57 passing** (31 before + 20 citation-check + 6 parser tests).
- **Citation grounding** — `backend/app/ai/citation_check.py`, run on every
  chat answer (deterministic regex matching, no extra LLM call):
  - Removes the sentence/table cell around any case-law citation (PLD/SCMR/
    MLD/… reporters, "X v. Y" names) not found verbatim in the retrieved
    passages — the corpus is statutes-only, so these are fabrications.
  - Flags Section/Article references whose number isn't in the retrieved
    passages as "(unverified)" + a closing note; statute-aware when the
    answer names the Act (so MFLO §5 cited for custody is flagged even if a
    different Act's §5 was retrieved). English + Urdu.
  - **Replay on real stored answers: 10/10 known fabricated citations
    removed** (5 PLD cites + 5 "Mst. X v. Mst. Y" names from 3 pre-fix
    answers dated 2026-09-20); **0 false positives** — all 4 clean
    post-fix answers passed through byte-identical. Replay fixtures live in
    `app/tests/unit/fixtures/citation_replay.json`.
  - Chat system prompt, the default prompt in `client.py`, and the
    `/research/analyze` template no longer claim judgment access or ask for
    case citations. Live re-tests: 0 case citations across all runs.
  - **Model's own citation format normalised (2026-09-27).** gpt-oss
    sometimes cites as "【5】" / "【5†L1-L3】" instead of "[5]" (10 of 56
    stored answers with sources). `normalize_markers()` rewrites these to
    "[n]" before the checks, so they're range-checked like any other marker
    (an out-of-range "【9】" used to slip through); the chat page applies the
    same rewrite when displaying answers stored before the fix.
  - Known limits: it checks a section number *exists* in the retrieved
    text, not that the answer describes it correctly; table-of-contents
    chunks make every listed section look present; same-numbered sections
    in different Acts pass when the answer doesn't name the Act.
- **Dead judgment seed data removed** — the 2 judgments (PLD 1967 SC 97,
  PLD 1959 Lah 566) dropped from `seed_corpus.py` (docstring now states the
  searchable corpus is FAISS statutes-only) **and** deleted from the live
  `legal_corpus` table (12 → 10 rows, 0 judgments).
- **DB-connection-during-AI-call bug fixed properly.** Root cause: the auth
  dependency's user lookup opens a transaction on the request session that
  stayed open across the slow LLM call, which Supabase's pooler kills —
  the endpoints' own queries were not the whole story. Confirmed and
  re-verified by watching `pg_stat_activity` during live calls.
  - `/chat/message`: `send()` split into three phases (its phase-1 commit
    also ends the auth transaction). Previously 500'd on the first message
    after a backend restart; now 200.
  - `/research/analyze` and `/documents/{id}/analyze`: close the request
    session before the LLM call. (The earlier `/documents` three-phase fix
    had missed the auth transaction — up to 2 idle-in-transaction
    connections were still held during its call.)
  - Side effect: a question and its AI reply no longer share an identical
    `created_at` (before, both were inserted in one transaction and got the
    same Postgres `now()`, making history order a tie).
- **Output polish:** chat `max_tokens` 800 → 2000 (gpt-oss-120b's reasoning
  counts against the budget, which cut long answers mid-sentence; a
  `finish_reason == "length"` now logs a warning). Research-analysis
  parser fixed — "**Issue:**" had left a stray "** " at the start of every
  field.

## Legal NER status — trained + integrated (confirmed 2026-09-26)
- Model: `distilbert-base-multilingual-cased` fine-tuned on Colab on LHC +
  SCP judgment data (`ai-services/ner_training/ner_training_colab.ipynb`).
  Validation F1 0.811 (reproduced exactly by a local re-score); held-out
  SCP test F1 0.784. Full results, weak-category analysis and integration
  details: `docs/ner_training_results.md`.
- Integrated into `POST /documents/{id}/analyze` (commit `ce04f28`):
  `parties` / `dates` / `references` / `entities` from NER, `key_clauses` /
  `risks` parsed from the LLM summary and labelled as such. Live test on a
  real SCP judgment: entity precision 0.843, recall 0.893. Poor on
  non-legal documents (expected, documented).
- **Model weights are NOT in git** (`backend/storage/` is gitignored; 539 MB).
  - Local: `backend/storage/models/legal_ner/` (what the backend loads) and
    the original download `ai-services/ner_training/trained_model/ner_model_output.zip`.
  - **Backup: `ner_model_output.zip` on Google Drive** (backed up 2026-09-26,
    confirmed by the user). To restore on a fresh clone, download the zip
    and extract its six files into `backend/storage/models/legal_ner/`.
    Without them the backend still runs — analysis returns the LLM summary
    with `ner_available: false`.
- **Frontend** (commit `4caeb58`): the Documents page now calls `/analyze`
  and shows the LLM summary / clauses / risks and the NER entities in two
  visually separate, labelled panels; `ner_available: false` shows a note.
- **Tested on a real, unseen document** — an SC bail order, Crl.P.
  187-P/2026, uploaded through the web app. Full output and line-by-line
  review in `docs/demo_examples.md` (for the report and panel demo). Three
  NER errors found; each traced to its cause before fixing (commit
  `6124d26`): a line-break abbreviation bleed (`KP Tahir Khan`) and a
  mislabelled own case number were fixed with narrow, tested rules; a
  place name tagged as a person was left as a documented model limitation.
  Kept visible as "found → fixed", not deleted.
- **Future work** for the next retrain (capitalisation gap in case numbers,
  duplicate label spellings, tiny classes, place-name coverage):
  `docs/ner_training_results.md` "Future work — retraining checklist" and
  `data/README.md` (commit `3151d44`).

## Contract Drafting & Compliance status — built + fully verified (confirmed 2026-09-21)
- New `/contracts/*` endpoints: draft a contract from one of 3 templates
  (NDA, Employment, Service Agreement — config in
  `app/ai/contract_templates.py`, not a DB table) + filled fields, check it
  against a deterministic required-clauses checklist, browse version
  history. `Contract` + `ContractVersion` models, `ContractService`,
  Alembic migration applied to the live DB. Committed `062624f`, pushed.
- **Verified end-to-end with a real signed-up lawyer test user over real
  HTTP** (same standard as the AI Chat/Research and Case Management passes):
  - Drafted a real NDA — Groq (`openai/gpt-oss-120b`) generated a genuine
    2,889-character contract from the filled fields.
  - **Compliance checker confirmed genuinely functional, not just a
    synthetic pass**: running it against the AI's own real draft found a
    real gap — 3/4 required clauses present, but the Remedies clause was
    missing despite the drafting prompt explicitly listing it as required.
    This is exactly the point of keeping the checker deterministic
    (keyword/section-presence matching) rather than another LLM call — it
    catches the LLM's own omissions instead of trusting it to self-report.
  - Negative-detection path also confirmed: attached a deliberately
    incomplete version (inserted directly via DB, since forcing the LLM to
    omit clauses on request isn't reliable — disclosed, not hidden) and
    re-ran the real `/check-compliance` endpoint against it; all 4 clauses
    correctly flagged failed.
  - Version history endpoint confirmed working.
- Full backend suite: **31/31 passing**, no regressions.
- **Frontend committed + verified 2026-09-26** (commits `f88ad1a`,
  `bc23611`): contract list, draft form for the 3 templates, detail page
  with compliance check and version history. Smoke-tested through the dev
  proxy: draft 201, list/open/check-compliance/versions 200 (all 4 NDA
  clauses pass), client draft 403, client access to another party's
  contract 403. Contract text renders through the shared
  `lib/MarkdownBlocks.jsx` (current drafts use headings, rules and
  numbered clauses, which the old inline renderer showed as raw symbols).

## UI accuracy sweep — every claim matches the system (confirmed 2026-09-26)
Commits `60e81d2`, `4cede9f`, `2a5745f`, `dee2bf0` (plus the chat welcome
text in `bc23611`). Every user-facing statement was checked against
actual system behaviour, not just reworded:
- **Corpus is statutes only**, described everywhere in the chat system
  prompt's terms ("Pakistani statute text — Acts, Ordinances, Codes and
  Orders … no court judgments or case law"): chat welcome text, Student
  dashboard, landing "How answers are grounded", Legal Research subtitle,
  Research detail page. The only remaining mention of judgments is the
  Library coming-soon page, which describes a planned feature.
- **Current AI model**: the Research detail loading text said "Llama-3.3"
  (retired); it now says "The AI is structuring…" so it can't go stale again.
- **Corpus size read live**: new `GET /research/stats` returns
  `{chunks, documents}` from the loaded index (currently 53,739 / 900); the
  Research page's loading text uses it instead of a hard-coded, stale
  "88,036 chunks".
- **Inert controls removed**: the Type (All/Statutes/Judgments), Court and
  Year filters. Tested against the live API first: "Statutes" returned the
  same results as "All", "Judgments" always 0, and Court / Year ranges
  returned exactly the same results as no filter (the index has no court or
  year metadata).
- Backend suite **91/91 passing**; frontend lint clean on changed files;
  production build clean.

## Folder structure
```
FYP Project/
  backend/     -> FastAPI, Python
  frontend/    -> React
```
(Confirm this is still accurate — paths may have changed since FYP-1.)

## Tech stack
- Backend: FastAPI + PostgreSQL
- Frontend: React
- AI providers (fallback chain — first available key wins):
  1. Groq (primary, free) — model: **openai/gpt-oss-120b** (updated
     2026-09-20; `llama-3.3-70b-versatile` was retired by Groq)
  2. OpenAI — model: gpt-4o-mini
  3. Gemini — model: gemini-2.0-flash
- Embeddings: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions)
- Vector search: FAISS (flat index) — **last build (2026-09-20): 53,739
  chunks from 901 documents**, see "AI Chat / Research status" above. The
  `88,036 chunks from 2,600 documents` figure this replaced was from an
  earlier, unrelated build.
- RAG settings: top_k=5, similarity_threshold=0.65 (tuned down from 0.7
  2026-09-20 based on real eval data — see "AI Chat / Research status"
  above), chunk_size=800, chunk_overlap=100
- OCR: Tesseract (eng+urd)
- Auth: JWT (access + refresh tokens), bcrypt password hashing

## Key environment variables (do not commit real values)
```
DATABASE_URL, SECRET_KEY, GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY,
EMBEDDING_MODEL_NAME, FAISS_INDEX_PATH, RAG_TOP_K, RAG_SIMILARITY_THRESHOLD,
RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, UPLOAD_DIR, DOC_MAX_SIZE_MB, TESSERACT_CMD
```

## FYP-1 panel feedback to address in this phase
- "Lack of AI" — chat/research modules feel like thin API wrappers; need real
  engineering depth (see plan below).
- Panel didn't know what FAISS was / confused it with a full vector database —
  consider migrating to pgvector or Qdrant.
- No understanding of RAG/foundation models demonstrated — team must be able
  to explain these in plain language.
- Severe lack of legal domain knowledge — need a legal reviewer/validator.
- UI needs improvement.
- More test cases needed.
- Report: duplicated sections, weak dataset/preprocessing discussion, missing
  security details (prompt injection, rate limiting, file sanitization),
  overloaded class diagram.

## Rules for Claude Code sessions (UI work)
- NEVER redesign more than one page/screen per session unless explicitly told.
- Follow the style rules in STYLE_GUIDE.md exactly — do not improvise colors,
  fonts, or spacing.
- Before changing any page, run existing tests / do a manual click-through
  check afterward — do not proceed to the next page until confirmed working.
- Do not touch backend logic while doing UI work unless explicitly asked.

## Git workflow
- After completing any meaningful task (a bug fix, a feature, a data
  pipeline change, a UI page, a config change) — commit it immediately
  with a clear, specific message describing what changed and why. Do not
  batch multiple unrelated changes into one commit.
- Never commit large regenerable data/index files (see `.gitignore`).
- Before ending any session, run `git status` and commit/push anything
  meaningful left uncommitted, so no session's work is ever lost or left
  only on the local machine.
- Commit messages should read like real engineering log entries (what
  changed, why) — not generic messages like "update" or "fix stuff".

## Immediate next steps (Iteration 3 / Iteration 4)
1. ~~Audit current codebase state~~ — done. See "Backend / database status"
   above; full findings also live in the audit plan file from that session.
2. ~~Folder structure cleanup~~ — done. See "Git / repository status" above
   for exactly what moved/was renamed/was deleted. Tier B follow-ups
   (prompt-file relocation, repositories/services pattern decision) still
   open, deliberately deferred to their own session.
3. ~~UI redesign~~ — done: every page converted to the design system (see
   `docs/STYLE_GUIDE.md`), followed by the 2026-09-26 accuracy sweep (see
   "UI accuracy sweep" above).
4. ~~Build Contract Drafting & Compliance module~~ — done (2026-09-21),
   built + fully verified end-to-end. See "Contract Drafting & Compliance
   status" above.
5. **Next up, in this order** (set 2026-09-26):
   a. ~~NER Colab training~~ — done (2026-09-26): trained, validated,
      integrated into Document Analysis (backend + frontend), tested on a
      real unseen judgment. See "Legal NER status" above.
   b. ~~Finalize + commit the Contracts UI~~ — done (2026-09-26), committed
      and smoke-tested. See "Contract Drafting & Compliance status" above.
   c. **Next up: Practice Simulator (Iteration 4) — the last missing core
      module.** Conversation via LLM, but grading/rubric logic must be
      custom-built, not just LLM-judged.
   d. **Before the demo: secure LLM capacity** — paid Groq tier or an
      unused demo-day key; see "⚠️ Known constraint — Groq free-tier
      limits" above.
6. Add missing security pieces: rate limiting, file upload sanitization,
   basic prompt-injection input handling.
7. Add test coverage for RAG acceptance criteria (MRR, recall@5, refusal rate).
8. The 78-question run above gave a relevance-score distribution, not real
   MRR/recall (that needs a ground-truth relevant-document mapping per
   question, which this pass didn't build) — **still open**: run the full
   QA eval set properly for real MRR/recall numbers.
9. ~~Test Document Analysis, Case Management, and OCR modules
   end-to-end~~ — done (2026-09-20), real signed-up test users + live HTTP
   calls throughout, same rigor as the AI Chat/Research pass:
   - **Case Management: fully working** — create, assign client
     (created→assigned auto-transition), invalid transition correctly
     rejected (409), valid transition + timeline all correct, client
     view-only enforced (403 on write attempts).
   - **Document Analysis + OCR: partially working**. Upload + PyMuPDF text
     extraction work well on real PDFs. The "detected clauses" feature
     **confirmed not real** — `analyze_document()` hardcodes
     `key_clauses`/`parties`/`dates`/`risks` to `[]` on every call; only a
     plain LLM summary is genuine. The OCR fallback (Tesseract) is
     confirmed blocked for scanned PDFs/images specifically (verified with
     a synthetic no-text-layer image — `extracted_text: null`); digital
     PDFs are unaffected since PyMuPDF/PyPDF2 don't need Tesseract. Also
     found and **fixed** a transient 500 on `/analyze` (DB session held
     open across the slow Groq call, killed by Supabase's pooler) —
     restructured into three phases so no session spans the LLM call;
     confirmed with 6 repeated calls, all 200. (That fix turned out to be
     incomplete — the auth lookup's transaction was still held; completed
     2026-09-26, see "Reliability pass" above.)
   - **RBAC: fully working**, confirmed live (403s on every cross-role
     write attempt) — though the dedicated `require_role` middleware in
     `app/middlewares/rbac.py` turns out to be dead code; enforcement
     actually happens via manual role checks inside each service method.
   - **Notifications: confirmed not implemented** — see "Current status"
     above.