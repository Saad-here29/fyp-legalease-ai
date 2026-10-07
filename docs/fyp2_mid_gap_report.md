# FYP-2 Mid — Requirements Gap Report

Prepared 2026-10-05 for the FYP-2 mid evaluation. It is read-only: no code
was changed and no AI calls were made.

**Sources:**
- the FYP-1 **Proposal** (Jan 2026, 14 pp.), **Mid report** (Mar 2026,
  42 pp.) and **Final report** (May 2026, 56 pp.) in `docs/reports/`;
- the current code at `80f57f5`;
- the October 2026 quality pass (`docs/TEST_PLAN.md` § 9);
- the September pre-demo audit (`docs/archive/PROJECT_CONTEXT.md`).

**Requirement IDs:**
- **The Final Report's IDs are used throughout:** FR-CM01–07, FR-AI-01–05,
  FR-DOC-01–04, FR-RES-01–04, FR-CON-01–04, FR-OCR-01–04, FR-PS-01–04,
  FR-NOT-01–03, plus REL/USE/PER/SEC NFRs. That's the document the panel
  holds.
- **The Mid report numbered them differently.** Its FR-AI-04 is
  "simplified language", its FR-RES-04 is "filters", and its FR-RES-05 is
  "similar cases".
- **The Proposal has no FR IDs, only modules and features.**
- Mid-report requirements that the Final Report dropped are listed in
  § 1.9.

**Status values:**
- **Implemented and tested:** automated tests, or a recorded end-to-end
  check, show it working.
- **Implemented, unverified:** it works, but the report's acceptance
  metric was never measured.
- **Partly implemented.**
- **Not implemented.**
- **Changed:** done differently from the report; the reason is given.

---

## Summary

| Status | Final Report FRs (33) |
|---|---|
| Implemented and tested | 9 (FR-CM01, CM02, CM03, CM05, CM06, CM07, DOC-01, CON-03, OCR-03) |
| Implemented, acceptance metric unverified | 5 (FR-AI-01, AI-02, DOC-02, OCR-04, RES-03 search exists but the 2 s target is not met) |
| Changed (works, but differs from the report) | 4 (FR-AI-03 threshold 0.65; FR-AI-04 statutes only; FR-RES-01 statutes only; FR-RES-02 filters removed) |
| Partly implemented | 7 (FR-AI-05, DOC-03, DOC-04, CON-01, CON-04, OCR-01, OCR-02 code present but not installed or measured) |
| Not implemented | 8 (FR-CM04, RES-04, CON-02, PS-01–04, and FR-NOT-01–03 counted as one group) |

**Biggest risks for the panel:**
1. **The Practice Simulator** (all of FR-PS) and **Notifications** (all of
   FR-NOT) don't exist.
2. **Judgments and similar cases** (FR-AI-04, FR-RES-01, FR-RES-04): the
   library is statutes only, but the Final Report says statutes **and
   judgments** throughout.
3. **The Final Report's technology claims** (OpenAI, Celery and Redis,
   800-*token* chunks, threshold 0.7, S3, a CHECK constraint) and its four
   unit-test tables no longer match the code (§ 2).
4. **Performance NFRs** (PER-01, PER-05, FR-RES-03) fail as written:
   Supabase in Singapore adds 0.2–0.4 s per query.

---

## 1. Requirement status, with notes

### 1.1 Case management (FR-CM01–07)
- **FR-CM01** (create a case): **Implemented and tested.**
  - Evidence: UT-CASE-001 and a live `POST /cases` 201 (Oct QA).
  - Not met: the "within 1 s" part. API calls take 3–8 s against the
    Singapore database.
- **FR-CM02** (assign clients): **Implemented and tested.**
  - Linking is by email.
  - Non-assigned users get 403/404 (Oct QA: an outsider lawyer and a
    student are blocked).
  - Co-counsel is not supported (the Final Report's module text mentions
    it).
- **FR-CM03** (upload to a case): **Implemented and tested.**
  - PDF, DOCX and TXT up to 20 MB; tests in `test_upload_*`.
  - Images are accepted only when OCR is installed. It isn't on the demo
    machine, so the UI says so.
- **FR-CM04** (record hearings with date, time and venue): **Not
  implemented.**
  - There is a `hearing_scheduled` *status*, but no hearing records, dates
    or venue.
  - The Proposal's "deadlines and reminders" aren't built either.
- **FR-CM05** (timeline): **Implemented and tested.**
  - It shows creation, client linking, every status change (including the
    automatic one), documents and saved research.
  - No hearing events, because FR-CM04 isn't built.
- **FR-CM06** (state machine): **Implemented and tested.**
  - Every valid and invalid transition was checked live.
  - Invalid moves return 409, and an audit row is written.
- **FR-CM07** (client read-only): **Implemented and tested.**
  - UT-CASE-004/005.
  - Live: the client gets 403 on writes and sees only their own cases.

### 1.2 AI legal chat (FR-AI-01–05)
- **FR-AI-01** (English and Urdu): **Implemented, metric unverified.**
  - `langdetect` runs per question, and the prompt says to answer in the
    question's language. Refusals exist in both languages.
  - Tests: `test_chat_language.py`; a live English check.
  - The "≥95% on a 100-question bilingual set" check hasn't been run.
  - Roman Urdu is treated as English.
- **FR-AI-02** (top 5 passages): **Implemented, metric unverified.**
  - `RAG_TOP_K=5`.
  - Recall@5 on a 50-pair set hasn't been measured. The draft gold set
    (`docs/retrieval_gold_set_draft.md`) is the planned measure.
  - Known misses: PPC s. 302, Contract Act s. 10, khula.
- **FR-AI-03** (refuse below 0.7): **Changed: the threshold is 0.65.**
  - It was tuned on 2026-09-20 with the 78 real lawyer questions: 0.7
    refused too many in-library questions.
  - Refusal is tested (`test_quality_pass_fixes.py`), and off-topic
    questions were refused live.
  - The "30 out-of-library questions" set exists only as a 15-question
    draft.
- **FR-AI-04** (inline citations to a statute **or judgment**):
  **Changed: statutes only.**
  - Every answer cites `[n]` passages, and the UI shows the numbered
    sources.
  - The citation checker (29 tests) flags section numbers it can't find in
    the passages. It **removes** case-law citations, because the library
    holds no judgments.
  - "No broken links" holds: citations point at the passages returned
    with the answer.
- **FR-AI-05** (last 50 exchanges per user per case): **Partly
  implemented.**
  - Every message is stored. Sessions belong to a user, with an optional
    case.
  - The history endpoint returns the whole session; there is no 50 cap.
  - The model is sent the last 10 messages, capped at 2,000 tokens (so
    requests stay under Groq's per-minute limit).
  - The ≤500 ms target hasn't been measured.

### 1.3 Document analysis (FR-DOC-01–04)
- **FR-DOC-01** (PDF/DOCX/TXT, others 415): **Implemented and tested.**
  Tests: `test_upload_cleanup.py` (.exe/.js/.zip → 415), Oct QA.
- **FR-DOC-02** (summary): **Implemented, metric unverified.**
  - The summary is written by the LLM (Groq), not by BERT as the
    Proposal and UT-DOC-003 suggest.
  - Verified live on a real petition (Crl.P. 187-P/2026, about 8 s).
  - "5–10% of the source, ROUGE-L ≥0.30 on 20 documents" hasn't been
    measured.
- **FR-DOC-03** (mark key clauses: parties, jurisdiction, term,
  indemnity, termination): **Partly implemented.**
  - Clauses and risks are parsed from the LLM summary's sections
    (`test_summary_sections.py`).
  - Parties, dates and references come from the fine-tuned legal NER
    model, which was trained on **judgments**, not contracts.
  - "P ≥0.80 / R ≥0.75 on 25 labelled contracts" hasn't been measured.
- **FR-DOC-04** (flag missing clauses against a template): **Partly
  implemented / changed.**
  - Uploaded documents get *risks* from the LLM summary, not a template
    comparison.
  - The template-based missing-clause check exists, but in the
    **Contracts** module (FR-CON-03), for drafts made there.
- **Document classification** (contract, FIR, judgment, …; in the
  Proposal and the Mid report's module list): **not implemented.** The
  `document_type` enum only has `other`.

### 1.4 Legal research (FR-RES-01–04)
- **FR-RES-01** (semantic search over statutes **and judgments**):
  **Changed: statutes only.**
  - Search works over about 900 documents (53,739 passages).
  - The best passage scores ≥0.65 for 48 of the 78 lawyer questions
    (that's a score distribution, not MRR).
  - The "MRR ≥0.60" target needs the gold set, which is drafted and
    awaiting review.
- **FR-RES-02** (filter by court, year, case type): **Changed:
  removed.**
  - Statute passages carry no court or year, so the filters returned
    nothing useful and were taken out of the UI in September.
  - The backend still accepts filter parameters.
- **FR-RES-03** (≤2 s for 95%, k6 test): **Implemented, target not met
  and not load-tested.**
  - Each search makes one LLM query-rewrite call before the vector search.
    Searches took about 3 s in the September audit.
  - No k6 run.
- **FR-RES-04** (similar past cases for a selected judgment): **Not
  implemented.** There are no judgments in the library. A frontend
  endpoint constant for it pointed at a route that never existed; it was
  removed in October.

### 1.5 Contracts (FR-CON-01–04)
- **FR-CON-01** (templates for Employment, NDA, Service; PDF export):
  **Partly implemented.**
  - Done: three templates; drafting by the LLM (lawyers only). Verified
    live on all three.
  - Missing: PDF export.
- **FR-CON-02** (suggest clauses while drafting): **Not implemented.**
  - The draft prompt makes the model include each template's required
    clauses.
  - There's no interactive suggestion.
- **FR-CON-03** (compliance report, pass/fail): **Implemented and
  tested.**
  - It's a deterministic keyword checklist plus a scan for unfilled
    placeholders.
  - 13 tests; live on 3 drafts.
  - The "15 test contracts" verification hasn't been done.
- **FR-CON-04** (version history with diff): **Partly implemented.**
  - Done: a version table and `/versions` endpoint.
  - Missing:
    - only version 1 is ever created (there's no edit or re-draft
      endpoint);
    - no diff;
    - the Mid report's "review and modify drafts" isn't built.
  - **Contract editing is a requirement** (FR-CON-04 versions only make sense if a draft can be edited; the Mid report asks to "review and modify drafts"). **Implemented on 2026-10-06** (`a6f5fdb`): "Edit draft" saves the edited text as the next version and re-runs the compliance and placeholder checks; lawyers only. A diff between versions is still missing.

### 1.6 OCR (FR-OCR-01–04)
- **FR-OCR-01** (scanned PDFs and PNG/JPG up to 50 MB): **Partly
  implemented.**
  - The code path exists (`pytesseract`, `pdf2image`).
  - Tesseract and Poppler are **not installed** on the development and
    demo machine. Image uploads say "OCR not installed", and scanned PDFs
    extract nothing (with a warning).
  - The size limit is 20 MB, not 50 MB.
- **FR-OCR-02** (≥90% English, ≥80% Urdu accuracy): **Not verified.**
  Without OCR installed there is no benchmark. `TESSERACT_LANG=eng+urd`
  is configured.
- **FR-OCR-03** (keep the original and the text): **Implemented and
  tested.** The file is kept on disk (generated name) and the text in
  `documents.extracted_text`.
- **FR-OCR-04** (text passed to document analysis within 30 s):
  **Implemented, latency unverified.** Analysis reads the extracted text;
  the timing for scanned documents isn't measured, since there's no OCR.

### 1.7 Practice simulator (FR-PS-01–04): **Not implemented**

There's no backend, no model and no page. The placeholder route was removed
in October; `/simulator` shows the 404 page.

**Who it's for differs across the three documents:**
- **Proposal** (§ 2.2.6, and iteration 4): "Lawyers, students and interns".
- **Mid report:** FR-PS-01 says "students or lawyers", and § 3.3 says it
  "stores simulation data for both lawyers and students".
- **Final Report:** § 1.4.5 says "law students and interns", and FR-PS-04
  tracks *student* progress.

**Timing:** the Proposal schedules the simulator for **iteration 4,
October–November**. That's now, so it's the next build, not a missed one.

### 1.8 Notifications (FR-NOT-01–03): **Not implemented**

There are no notification tables, endpoints or UI. Email is used only for
signup and password-reset codes, and even that needs SMTP credentials,
which aren't configured; codes appear in the server log.

UC-03 ("the client receives a notification") is affected too.

PROJECT_CONTEXT records the decision to de-scope notifications for this
iteration (2026-09-20).

### 1.9 Requirements only in the Mid report (dropped or reworded in the Final)

| Mid ID | Requirement | Status |
|---|---|---|
| FR-CM-02 | Assign cases to themselves **or other authorised users** | Partly: the creating lawyer is the assigned lawyer; no reassignment between lawyers |
| FR-CM-06 | Record hearings or deadlines | Not implemented (as FR-CM04) |
| FR-CM-08 | Clients view progress | Implemented and tested (client dashboard, case page) |
| FR-DOC-02 | "Analyse uploaded documents using …" (sentence cut off in the Mid report) | — |
| FR-DOC-05 | Highlight risks or missing clauses | Implemented (risks section of the summary) |
| FR-RES-02 | Retrieve relevant **cases** | Changed: statutes |
| FR-RES-05 | Suggest similar cases | Not implemented |
| FR-AI-04 | Explain in simplified language | Implemented: every substantive answer opens with a highlighted "Short answer" |
| FR-CON-04 | Review and modify drafts | Not implemented (no editing) |
| FR-OCR-03 | Convert to editable text | Partly: the text is stored and shown, not editable in the app |
| FR-NOT-03 | Notify on new case documents | Not implemented |

### 1.10 Scope: family law only, or general?

| Source | Scope it states |
|---|---|
| **Proposal § 2.1** | "Refined to focus specifically on **Family Law**": divorce, custody, maintenance, inheritance |
| **Mid report** | No family-law restriction. Research is over "massive datasets of Pakistani statutes" |
| **Final Report** | Case types are DIVORCE / CUSTODY / INHERITANCE / MAINTENANCE (domain model). The library is "Pakistani statutes and judgments". UT-CHAT-003 redirects to "family law topics" |

**What the code actually does:**
- **Case management is family law:** the `case_type` enum has exactly
  custody, inheritance, divorce and maintenance.
- **The AI library is general Pakistani law:** about 900 statutes,
  including the PPC, CrPC, the Contract Act and the Constitution. The chat
  answers criminal and commercial questions too.
- **Contracts are commercial:** NDA, employment and service agreements,
  none of them family-law instruments.

A consistent sentence for the panel: *"Case management is built for family-law matters; the AI research and chat cover Pakistani statute law generally, which family cases also draw on (PPC, CrPC, QSO)."*

### 1.11 Non-functional requirements (Final Report)

| NFR | Status | Evidence |
|---|---|---|
| REL-01 (99% uptime) | Not measured | No deployment, no uptime monitoring |
| REL-02 (daily backups) | Not verified by us | The database is on Supabase; the backup plan hasn't been checked |
| REL-03 (recovery ≤5 min) | Not tested | No chaos test |
| REL-04 (core works if AI fails) | **Met** | The September audit with Groq's budget exhausted: cases, uploads and search still worked; AI errors are 503 `ai_unavailable` |
| USE-01 (≤3 clicks to create a case) | Plausible, not user-tested | Cases → New case → Create |
| USE-02 (core tasks in 10 min) | Not studied | — |
| USE-03 (responsive, no overflow) | **Met** | 62 page loads, 2 widths, 3 roles, 0 overflow (Oct QA) |
| USE-04 (every error has a hint) | **Mostly met** | Every app error has `{code, message, hint}`. FastAPI's own 422 validation errors have no hint |
| USE-05 (SUS ≥70) | Not done | — |
| PER-01 (pages ≤2 s) | **Not met** | API calls take 3–8 s (Singapore DB) |
| PER-02 (chat ≤5 s cached / ≤15 s uncached) | **Partly** | Measured 9–27 s per answer (rewrite + generation) |
| PER-03 (20 MB upload ≤10 s) | Not measured | — |
| PER-04 (100 concurrent users) | Not tested | No Locust/k6 |
| PER-05 (DB p95 ≤200 ms) | **Not met** | 0.2–0.4 s per query |
| SEC-01 (bcrypt ≥12) | **Met** | `BCRYPT_ROUNDS=12` |
| SEC-02 (TLS ≥1.2) | Not applicable yet | Not deployed. Cookies become Secure outside development |
| SEC-03 (RBAC on every endpoint) | **Met in checks; no automated test of all endpoints** | Service-level checks; Oct QA cross-role checks on cases, documents, contracts, chat |
| SEC-04 (log every privileged action) | **Partly** | Logged: login, signup, logout, password reset, status change, client link, research save. **Not logged:** uploads, analyses, chat queries (though chat messages are stored), contract drafts |
| SEC-05 (no OWASP critical/high) | Not scanned | No ZAP run. An upload path-traversal (high) was found and fixed in October |
| SEC-06 (JWT ≤60 min / ≤7 days) | **Met** | 60 min / 7 days; logout now revokes both |

---

## 2. Architecture and technology: report vs code

These are the claims to fix before the panel reads them.

| # | Report claim | Where | What the code does | Suggested fix to the report |
|---|---|---|---|---|
| 1 | LLM is **OpenAI Chat Completions** | Final Table 4.1 | **Groq `openai/gpt-oss-120b`**, through the OpenAI-compatible client. OpenAI (gpt-4o-mini) and Gemini are optional fallbacks | Say Groq primary, OpenAI/Gemini fallback |
| 2 | **Celery + Redis** for OCR jobs | Final Table 4.1 | No task queue. OCR runs inside the upload request. Celery and Redis were removed in October | Remove the row |
| 3 | Library built from the **Pakistan Code + Peshawar and Sindh High Court judgments** | Final § 4.1 | **Statutes only**: about 900 documents, 53,739 passages, no judgments. Where the two raw datasets came from is **not recorded** | Say statutes only. Don't claim a source you can't show (`docs/corpus_statute_list.md`) |
| 4 | **800-token** chunks, **100-token** overlap | Final § 4.1, Fig 4.4 | 800 **characters**, 100 **characters** | Correct the unit |
| 5 | Refuse below **0.7** | Final FR-AI-03, § 4.1, Fig 4.5 | **0.65**, tuned on the 78 real lawyer questions (2026-09-20) | State 0.65 and why |
| 6 | Embeddings: "multilingual sentence-transformer"; FAISS IndexFlatIP, L2-normalised | Final § 4.1 | **Matches**: `paraphrase-multilingual-MiniLM-L12-v2`, 384-dim, IndexFlatIP. Unstated limit: the model reads only the first 128 tokens of each chunk | Optionally add the model name |
| 7 | Embeddings reference their PostgreSQL record | Final § 3.2 | References live in a JSON sidecar file next to the FAISS index. The `legal_corpus` table is legacy and unread | Correct |
| 8 | RBAC is a **FastAPI dependency reading the role claim** | Final § 4.1 | The dependency loads the user (and checks the token version); **role and ownership checks are in the services**. The old `rbac.py` dependency was dead code and was removed | Say service-level checks |
| 9 | Status values enforced by a **CHECK constraint** | Final § 4.1 | A PostgreSQL **ENUM** type plus a transition table in `case_service.py` | Correct the mechanism |
| 10 | **Blob storage / S3, signed URLs** | Final § 3.2, UT-DOC-001; Mid § 3.3 | Local disk (`backend/uploads/`), generated file names, no download endpoint | Say local storage; S3 is future work |
| 11 | **SHA-256 deduplication** | Final § 4.1 | The hash is computed and stored, but **not used to deduplicate** | Say "integrity hash", or implement dedup |
| 12 | "Metadata written only after upload completes, so no orphan blob" | Final § 4.1 | True since October. Before that, rejected uploads stayed on disk (fixed) | OK as is |
| 13 | **Encrypted storage** of sensitive files | Final § 1.4.8; Mid SEC-3 | Passwords are bcrypt-hashed. **Uploaded files are stored unencrypted on disk**. Database encryption at rest is Supabase's, not verified by us | Say passwords hashed, files access-controlled; or implement encryption |
| 14 | Summaries by **BERT**, with a `confidenceScore` | Proposal § 2.3; Final UT-DOC-003 | Summaries come from the **LLM**. No confidence score | Correct |
| 15 | *(not mentioned)* | Final report | A **fine-tuned DistilBERT legal NER model** (parties, dates, references; F1 0.811 val / 0.784 test on Supreme Court text) is in document analysis | **Add it**: it's your strongest answer to "lack of AI" |
| 16 | Domain model: Deadline, SimulationScenario/Attempt, Notification, LegalStatute; `Document.docType` CONTRACT/FIR/…; `ocrText`; `firmName`, `opponent` | Final Fig 3.4; Mid ERD | None of these exist. The schema has 14 tables (`docs/database-schema.md`). `document_type` has only `other`; extracted text is one column | Mark as planned, or update the diagram |
| 17 | Class diagram: ChatService/RAGEngine, SimulationService, NotificationService, EmailService, StorageService, EncryptionService, one repository per entity | Final Fig 3.6 | Services that exist: AuthService, CaseService, LegalChatService, ResearchService, ContractService, OCRService. Only UserRepository. No simulation, notification or storage services | Redraw, or mark future classes |
| 18 | Architecture: **Layered + Microservices / API gateway** | Mid § 3.1; Proposal § 2.3 | One FastAPI app, layered (as the **Final** report correctly says) | Final is right; don't repeat the Mid claim |
| 19 | UC-04: chat history limited to the last 50 exchanges; answers in ≤15 s | Final Table 2.4 | No 50 cap. The model sees ≤10 messages / 2,000 tokens. Answers take 9–27 s | Correct |
| 20 | UC-05: "analysis queued for retry if the NLP engine is down"; summary 5–10%; confidence >0.8 | Final Table 2.5 | No queue (503 error). No measured summary ratio and no confidence | Correct |
| 21 | UC-06: ≤10 results in 2 s with court and year; "view similar cases"; "suggest refined queries" | Final Table 2.6 | 10 results by default; ~3 s; court/year empty for statutes; no similar cases or query suggestions | Correct |
| 22 | UC-03: client "receives a notification"; non-existent client "prompted to invite" | Final Table 2.3 | No notification. A missing client gets 404 "ask them to sign up first" | Correct |
| 23 | UC-01: login completes within 1 s | Final Table 2.1 | Login measured at about 6 s (new database connection to Singapore) | Correct, or move the database |
| 24 | **Unit test tables 4.2–4.5** (12 tests) | Final § 4.3 | See § 3. **They don't match the code**: UT-AUTH-001 says a 24 h token (actual 60 min); UT-AUTH-003 expects 404 `UserNotFound` (actual 401, deliberately, to avoid revealing accounts); UT-CASE-002/003 test `assignCase` to a lawyer (no such function); UT-DOC-001 tests S3; UT-DOC-003 tests BERT with a confidence score; UT-CHAT-001 tests `startChatSession` (sessions start on the first message); UT-CHAT-003 expects `outOfScope: true` and "family law topics" (the actual refusal has no flag) | Replace with the real suite (213 tests, `docs/TEST_PLAN.md`) |

---

## 3. Automated test inventory

These counts come from pytest's own collection on 2026-10-05: **213
tests**. "HTTP" means the test goes through FastAPI's `TestClient` against
the real app. "Unit" means it calls a service or function directly
(in-memory SQLite, model calls stubbed).

| Module | Total | Unit | HTTP | Files |
|---|---:|---:|---:|---|
| Auth (login, lockout, signup, OTP, refresh, logout revocation, pending-signup, 409, email domain) | 23 | 17 | 6 | `test_auth_service`, `test_signup_pending`, `test_logout_revocation`, `test_email_validator`, part of `test_quality_pass_fixes` |
| Case management (state machine, RBAC, auto-assign, timeline) | 10 | 10 | 0 | `test_case_service`, part of `test_quality_pass_fixes` |
| AI chat (language, refusal, history budget, citation checker) | 49 | 49 | 0 | `test_chat_language`, `test_chat_history_budget`, `test_citation_check`, part of `test_quality_pass_fixes` |
| Retrieval helpers (contents-list section lookup) | 14 | 14 | 0 | `test_section_lookup` |
| Research (title mapping, trimming, index stats) | 14 | 14 | 0 | `test_research_service`, `test_index_stats` |
| Documents / upload (path safety, cleanup, extraction warning, capabilities) | 37 | 14 | 23 | `test_upload_paths`, `test_upload_cleanup`, `test_upload_extraction` |
| Document analysis (no-text 422, summary sections) | 10 | 10 | 0 | `test_analyze_no_text`, `test_summary_sections` |
| Legal NER (decoding, post-processing, the real model) | 25 | 25 | 0 | `test_ner` |
| OCR / text extraction | 4 | 4 | 0 | `test_ocr_service` |
| Contracts (placeholder scan, compliance, optional body) | 13 | 10 | 3 | `test_contract_placeholders` |
| Platform (health, API docs gating, DB retry/503) | 14 | 4 | 10 | `test_health`, `test_api_docs`, `test_db_unavailable` |
| **Total** | **213** | **171** | **42** | |

Other kinds of testing:
- **Frontend tests:** none.
- **Load and performance tests:** none.
- **Security scan (ZAP):** none.
- **Usability study:** none.
- **End-to-end checks:** the October QA pass ran 113 API checks (107
  passed; the 6 failures were fixed with tests) and 62 page loads.

### Not covered by any automated test
- **Case endpoints over HTTP:** cases are tested at the service level only.
  The HTTP behaviour was checked live, not by a test.
- **Password reset, forgot-password and resend-OTP:** checked live in the
  October QA run; no test.
- **Chat end to end:** a real retrieval plus an answer. Only refusals and
  prompts are tested (model calls are stubbed), so retrieval quality has no
  test. The gold set is pending.
- **Chat history endpoint privacy:** checked live only.
- **Research search over HTTP** (FAISS + rewrite) and save-to-case.
- **Document analysis happy path** (LLM summary + NER together); only the
  422 path and the parts are tested.
- **Contract drafting** (the LLM draft); only compliance is tested.
- **The frontend:** all pages and flows.
- **Every performance and security NFR:** PER-*, SEC-02, SEC-05.

---

## 4. Requirement table for the panel

Use the "What to say" column for anything not fully done.

| Requirement | Status | Evidence | What to say to the panel |
|---|---|---|---|
| FR-CM01 Create case | Implemented and tested | UT-CASE-001; live 201 | "Done. The 1 s target fails only because our free database is in Singapore; it's a hosting issue, not code." |
| FR-CM02 Assign clients | Implemented and tested | Live cross-role checks (403/404) | "Done, by email. Co-counsel sharing is future work." |
| FR-CM03 Upload to case | Implemented and tested | `test_upload_*` (37 tests) | "Done for PDF, DOCX and TXT. Images need OCR installed on the server." |
| FR-CM04 Hearings | **Not implemented** | Only a `hearing_scheduled` status | "We track hearing *status*; dated hearing records and reminders are scheduled with notifications in FYP-2." |
| FR-CM05 Timeline | Implemented and tested | Timeline tests; live | "Done, including automatic status changes." |
| FR-CM06 State machine | Implemented and tested | UT-CASE-003; every transition live | "Done; illegal moves return 409 and are audited." |
| FR-CM07 Client read-only | Implemented and tested | UT-CASE-004/005; live 403 | "Done." |
| FR-AI-01 English + Urdu | Implemented, metric unverified | `test_chat_language`; live | "Works, with Urdu refusals too. We haven't run the 100-question accuracy test yet; it's in our evaluation plan." |
| FR-AI-02 Top-5 retrieval | Implemented, metric unverified | `RAG_TOP_K=5` | "Implemented. Recall@5 needs a labelled set; our 26-question gold set is drafted (show `retrieval_gold_set_draft.md`)." |
| FR-AI-03 Refusal threshold | **Changed (0.65, not 0.7)** | Tuned on 78 real lawyer questions | "We tuned it on real lawyer questions: 0.7 refused valid questions, and 0.65 keeps off-topic ones out." |
| FR-AI-04 Citations to statute or judgment | **Changed (statutes only)** | `[n]` citations; checker (29 tests) | "Every answer cites its statute passage. We removed judgments because our library has none and we won't let the model invent case citations; the checker strips them." |
| FR-AI-05 50-exchange history | Partly | All messages stored; model sees 2,000 tokens | "History is kept in full; we cap what we send to the model to stay within the provider's rate limit." |
| FR-DOC-01 Accepted formats | Implemented and tested | 415 tests | "Done." |
| FR-DOC-02 Summary | Implemented, metric unverified | Live on a real petition | "Done, by the LLM; ROUGE evaluation is planned." |
| FR-DOC-03 Key clauses | Partly | Summary sections + NER | "Clauses and risks come from the summary; parties and dates come from our own fine-tuned NER model (F1 0.81). The contract-specific clause labels aren't measured yet." |
| FR-DOC-04 Missing clauses | Partly / changed | Template check in Contracts | "Template-based missing-clause checks run on contracts drafted in the app; for uploaded documents we flag risks from the analysis." |
| FR-RES-01 Semantic search | **Changed (statutes only)** | 900 documents / 53,739 passages; 48/78 above threshold | "Semantic search over about 900 Pakistani statutes. We dropped judgments: we couldn't document a clean, licensed judgment source." Check the reason with the team before using it. |
| FR-RES-02 Filters | **Changed (removed)** | Statutes have no court/year | "Court and year filters only make sense for judgments; we removed them rather than show filters that do nothing." |
| FR-RES-03 ≤2 s search | Not met, not load-tested | ~3 s measured | "Search runs a query-rewrite step first to improve precision; that costs about a second. No load test yet." |
| FR-RES-04 Similar cases | **Not implemented** | No judgments | "This depends on a judgment corpus, which we de-scoped; it's future work." |
| FR-CON-01 Templates | Partly | 3 templates; no PDF export | "Three templates done; PDF export is pending." |
| FR-CON-02 Clause suggestions | **Not implemented** | — | "Drafts are generated with every required clause included; interactive suggestions are planned." |
| FR-CON-03 Compliance report | Implemented and tested | 13 tests; 3 live drafts | "Done, deterministic: no AI in the check, plus an unfilled-placeholder check." |
| FR-CON-04 Versions + diff | Partly | Versions stored; only v1; no diff | "Version storage is in place; editing and diff are the next step." |
| Contract editing (needed by FR-CON-04 and the Mid report's "review and modify drafts") | **Implemented 2026-10-06** (no diff yet) | "Edit draft" saves the next version and re-runs the compliance and placeholder checks; lawyers only; 10 tests (`a6f5fdb`) | "Lawyers can edit a draft; each save is a new version with the compliance check re-run. A side-by-side diff is the next step." |
| FR-OCR-01 Scanned files | Partly | Code present; Tesseract not installed | "The OCR pipeline is built; the demo machine doesn't have Tesseract installed, so we demonstrate with digital PDFs. The app tells the user when OCR isn't available." |
| FR-OCR-02 OCR accuracy | Not verified | — | "Not benchmarked yet; needs OCR installed." |
| FR-OCR-03 Keep scan + text | Implemented and tested | File + `extracted_text` | "Done." |
| FR-OCR-04 Text to analysis | Implemented, latency unverified | Analysis reads extracted text | "Done; timing for scanned files isn't measured yet." |
| FR-PS-01–04 Practice simulator | **Not implemented** | No code | "Planned for iteration 4 (Oct–Nov), as in our proposal; it's being built now, for students and interns." |
| FR-NOT-01–03 Notifications | **Not implemented** | No code | "De-scoped this iteration to deliver contracts and document analysis; scheduled with hearings in FYP-2." |
| REL-04 Graceful AI failure | Met | Sept audit | "Shown: with the AI down, cases, uploads and search still work." |
| USE-03 Responsive | Met | 62 page loads, 0 overflow | "Checked on desktop and phone for all three roles." |
| PER-01 / PER-05 Speed | **Not met** | 3–8 s per call | "Our free database is in Singapore (0.2–0.4 s per query). A nearer region or paid tier fixes it; the code isn't the bottleneck." |
| SEC-01 / SEC-06 | Met | bcrypt 12; JWT 60 min/7 d | "Done; logout also revokes every token." |
| SEC-04 Audit logging | Partly | Uploads and chat not audited | "Auth, status and assignment actions are audited; uploads and AI queries are stored but not yet in the audit log." |
| SEC-05 OWASP | Not scanned | Path-traversal found and fixed | "No ZAP scan yet; our own testing found and fixed an upload path-traversal bug." |
| Scope | Changed | Family-law case types; general statute library | "Case management is built for family-law matters; the AI library covers Pakistani statute law generally." |
| Final Report § 4.2–4.3 | Out of date | § 2 of this report | "The FYP-1 report described the planned stack; we've since moved to Groq, removed Celery, and our test suite is now 213 automated tests." |
