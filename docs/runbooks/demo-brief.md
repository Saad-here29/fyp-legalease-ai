# LegalEase AI — Demo Brief

**For:** FYP evaluation, Department of Software Engineering, NUCES (FAST) Islamabad
**Team:** Saadullah (22I-8795), Ali Mehmood Khan (22I-2547), Muhammad Uzair Siddique (22I-6181)
**Supervisor:** Ms. Fatima Gillani · **Co-supervisor:** Mr. Farrukh Bashir

> **Updated October 2026** to match the code. It replaces the FYP-1 brief,
> which described an older system. Corrections that matter for the demo:
> - **The search library holds Pakistani statutes only:** about 900 documents
>   and 53,739 passages. It has **no court judgments or case law**. The FYP-1
>   brief's "2,809 Supreme Court judgments" and "88,036 chunks" are no longer
>   true.
> - **Contract drafting and document analysis are built.** The Practice
>   Simulator and Notifications are **not** (their placeholder pages were
>   removed).
> - **The language model is Groq `openai/gpt-oss-120b`.** It was Llama 3.3.
> - **One model *was* fine-tuned:** the legal NER model used in document
>   analysis.
>
> Every number below was measured on this codebase. Where something is an
> estimate or a known weakness, it says so.

> **How to start the demo: `docs/runbooks/demo-runbook.md`** (branch `kb-v2`). It has
> the exact commands for the primary setup: the `LegalEase` folder (branch `master`),
> with `KB_V2=true` set at launch. It also has the one-minute fallback to
> master from the main folder, and how to confirm which one is running
> (`/health` shows `"kb_v2": true`). The live check of that setup, with
> its recommendation, is `docs/evaluation/kb_v2_live_check_2026-10-06.md`. The
> **60-second Knowledge Base path** is in § 7, "Knowledge Base in 60
> seconds" (kb-v2 only).
>
> **Since kb-v2 B6 (2026-10-07):** the Research category filter keeps the
> core laws:
> - **PPC, CrPC:** Criminal Laws;
> - **QSO:** Law of Evidence;
> - **MFLO, the Family Courts Act, the Shariat Act:** Family Laws;
> - **the Constitution:** Constitutional Law.
>
> These categories are hand-assigned and labelled as such. So the live
> check's advice to avoid the filter no longer applies. Near-empty
> "[Omitted]"/"Rep. by …" sections no longer appear as sources. Details are
> in `docs/runbooks/demo-runbook.md` § "Changes in kb-v2 B6".

---

## 1. What we built

LegalEase AI is a web platform for the Pakistani legal sector. It brings
together:

1. **Case management** for lawyers and their clients: a case lifecycle,
   documents, and an activity timeline.
2. **An AI legal chat assistant** that answers from Pakistani statutes,
   cites the passages it used, and refuses questions outside Pakistani law.
   It works in English and Urdu.
3. **Legal research:** semantic search over the same statute library, with
   an AI analysis of any passage on request.
4. **Document analysis:** upload a document, read its text, and get an AI
   summary with clauses and risks, plus parties, dates and references found
   by our fine-tuned legal NER model.
5. **Contract drafting and compliance:** draft an NDA, employment or
   service agreement from a template. A deterministic checklist then
   confirms the required clauses are present and that no `[address]`-style
   blanks are left.

### Users (three roles)

| Role | What they can do |
|---|---|
| **Lawyer** | Create cases, link clients by email, move cases through their status, upload and analyse documents, draft contracts and run compliance, chat, research, save research to a case |
| **Client** | See their own cases (read-only), the timeline and documents, upload documents, view contracts linked to their case, chat, research |
| **Student** | Chat and research (no case or contract access) |

### Tech stack (what the code actually uses)

- **Backend:**
  - Python 3.11, FastAPI 0.115, SQLAlchemy 2.0 and Alembic;
  - PostgreSQL hosted on Supabase;
  - PyJWT (HS256) and bcrypt (cost 12);
  - pydantic-settings, loguru.
- **AI:**
  - `sentence-transformers` with `paraphrase-multilingual-MiniLM-L12-v2`
    (384-dimensional, English and Urdu);
  - `faiss-cpu` 1.15 (`IndexFlatIP`, cosine similarity);
  - Groq `openai/gpt-oss-120b` through the OpenAI-compatible client, with
    OpenAI and Gemini as optional fallbacks;
  - `transformers` and PyTorch (CPU) for the fine-tuned DistilBERT NER
    model;
  - `langdetect` for English/Urdu detection.
- **Documents:** PyMuPDF and PyPDF2 for PDFs, `python-docx`; Tesseract OCR
  (English + Urdu) for scanned PDFs and images, installed on the demo machine.
- **Frontend:**
  - React 19 and Vite 5;
  - Tailwind CSS with our own design system (Newsreader and IBM Plex Sans;
    `docs/architecture/STYLE_GUIDE.md`);
  - React Router 6, TanStack Query 5, Zustand 5, Axios;
  - react-hook-form with zod; sonner for toasts; react-markdown for AI
    output.

### Module status

| Module | Status | Notes |
|---|---|---|
| Authentication | Built | Signup with a 6-digit email code (10 min), MX check on the email domain, lockout after 5 wrong passwords, password reset, sign-out revokes all tokens |
| Case management | Built | 5-state lifecycle, timeline, documents |
| AI legal chat | Built | Statute-grounded answers with `[n]` citations, a "Short answer" box, refusals in English and Urdu |
| Legal research | Built | Search, then passage detail, then optional AI analysis, then save to a case |
| Document analysis | Built | Text extraction, AI summary, clauses, risks, NER entities |
| Contract drafting and compliance | Built | 3 templates, versions, required-clause and placeholder checks |
| Dashboards | Built | Lawyer, client and student |
| Practice Simulator | **Not built** | No page |
| Notifications | **Not built** | No page |

### Architecture

```
Browser — React 19 SPA (Vite, port 5173)
  AppRouter → ProtectedRoute (role check) → page
  Axios: HttpOnly cookies (le_access / le_refresh), refresh on 401
        │ /api/v1
FastAPI (port 8000)
  routers (api/v1)  →  services (business rules, role checks, audit log)
  ai/: embeddings + FAISS search, query rewrite, citation checker,
       contract templates, legal NER
        │                       │                     │
  PostgreSQL (Supabase)    FAISS index on disk     Groq API
  14 tables                 53,739 vectors          openai/gpt-oss-120b
                            (83 MB + 49 MB meta)
```

---

## 2. How each module works

### AI legal chat — `features/chatbot`, `api/v1/chat.py`, `services/legal_chat_service.py`

Per question:

1. **Rewrite:** the question is rewritten into a short search query in the
   terminology statutes use. This is a small model call, about 400 tokens.
2. **Search:** the rewrite is embedded and FAISS returns the top 5 passages.
   Passages scoring below **0.65** cosine similarity are dropped.
3. **Section lookup:** if a statute's contents list is retrieved, it is
   followed to the sections the user's own question names.
4. **Refusal:** if no passage is left, the chat refuses **without calling
   the model**, in the language of the question.
5. **Prompt:** system rules (Pakistani law only, cite `[n]`, open with a
   short answer), the numbered passages, a language instruction ("answer in
   the language of the question"), and up to 2,000 tokens of conversation
   history.
6. **Answer:** generated by Groq `openai/gpt-oss-120b`.
7. **Citation checker:**
   - a section number not found in the retrieved passages is marked
     "(unverified)";
   - case-law citations (e.g. "PLD 1967 SC 97") are removed, because the
     library holds no case law.
8. **Saved** to `chat_sessions` and `chat_messages`. The UI shows the short
   answer, the answer and the numbered sources.

### Legal research — `features/legal-research`, `api/v1/research.py`

- **Search:**
  - the query is rewritten (the same small model call as in chat), then
    searched in FAISS;
  - results show the statute, an excerpt and a match percentage.
- **Passage page:** the full passage (one 800-character excerpt, not the
  whole Act). **Analyse with AI** is optional: issue, what the statute
  provides, operative rule, legal basis and relevance.
- **Save to case** (lawyers only): the passage is added to the case
  timeline.

### Case management — `features/case-management`, `services/case_service.py`

- **Lifecycle:**

  ```
  created → assigned → in_progress ⇄ hearing_scheduled → closed
     ↘──────────────→ in_progress            (closed is final; any state → closed)
  ```

  Illegal moves return **409**.
- **Linking a client by email** moves a new case to `assigned`
  automatically, and the timeline records it as automatic.
- **Timeline:** creation, client links, status changes, documents and saved
  research, each with who did it and when.
- **Access:** clients see only their own cases, read-only; students see
  none. Closed cases accept no new documents.

### Document analysis — `features/document-analysis`, `api/v1/documents.py`

- **Upload:**
  - PDF, DOCX or TXT, up to 20 MB;
  - PNG/JPG and scanned PDFs are read with OCR (Tesseract, English + Urdu);
  - files are stored under a generated name;
  - if no text comes out, the response says why.
- **Analyse:** sends the document text to the model.
  - The model returns a summary; clauses and risks are taken from its
    sections.
  - In parallel, the fine-tuned NER model finds parties, dates, references
    and other entities.
  - A document with no text is refused with **422**, without calling the
    model.

### Contracts — `features/contract-drafting`, `services/contract_service.py`

- **Templates:** Non-Disclosure Agreement, Employment Agreement, Service
  Agreement.
- **Drafting** (lawyers only) fills a template's fields and calls the model
  for the full text, which is stored as version 1.
- **Compliance check** (no model call):
  - each required clause must have one of its keywords in the text;
  - the text must contain no unfilled placeholders (`[address]`, `[date]`,
    `{{field}}`);
  - signature lines are not counted as placeholders.
- **Access:** a client of the linked case can view the contract; other
  users can't.

---

## 3. AI implementation

### Did we train a model from scratch?
No.

### Did we fine-tune a model?
**Yes, one: the legal NER model**, `backend/storage/models/legal_ner`.
- **What:** DistilBERT fine-tuned on Lahore High Court and Supreme Court of
  Pakistan judgment text (the training data's provenance is in
  `docs/evaluation/ner_training_results.md`).
- **Results (entity-level):** F1 **0.811** on the combined validation set
  and **0.784** on the held-out Supreme Court test set.
- **Where it's used:** document analysis only, to find parties, dates,
  references and other entities.

The **language model is not fine-tuned**. Answers come from retrieval
(RAG), for three reasons:
- the law can be updated by rebuilding the index, without retraining;
- every answer can cite the passage it relied on;
- we have no large set of expert question-and-answer pairs to fine-tune on.

### What is in the search library?
- **About 900 Pakistani legal documents**, chunked into **53,739** passages of
  800 characters with 100-character overlap. Statutes, ordinances and
  orders only, with **no judgments**. The full list is in
  `docs/architecture/corpus_statute_list.md`.
- **Two raw sources:**
  - a section-level table covering 7 statutes (PPC, CrPC, QSO, Transfer of
    Property Act, Limitation Act, MFLO, Police Order);
  - text extracted from statute PDFs.

  **Where those two datasets came from is not recorded.** Say so if asked.
- **Known content issues** (`data/README.md`):
  - some statutes are indexed twice under OCR-variant titles;
  - ESTACODE, a civil-service manual rather than a statute, is the largest
    single item.

### How good is the retrieval?
- **Lawyer questions:** on the 78 real lawyer questions in our evaluation
  set, the best passage scores at or above the 0.65 threshold for **48 of
  78 (62%)**. That measures whether the chat would answer, not whether the
  answer is right.
- **Measured weaknesses:**
  - "khula" questions;
  - some sections the search misses, e.g. PPC s. 302 for "punishment for
    qatl-i-amd" and Contract Act s. 10 for "elements of a valid contract".
- **Root cause:** fixed 800-character chunks ignore section boundaries, and
  the embedding model reads only the first 128 tokens of each.
- **The fix is designed, not built:** section-based chunking, in
  `docs/architecture/retrieval_redesign.md`.

### How do you stop hallucination?
1. The model is given only the retrieved passages and must cite them as
   `[n]`.
2. If nothing passes the 0.65 threshold, the chat refuses without calling
   the model.
3. The citation checker:
   - marks any section number that isn't in the retrieved passages
     "(unverified)";
   - removes case-law citations.

### How do you handle Urdu?
- **Search:** the multilingual embedding model puts Urdu questions in the
  same vector space as the English statute text.
- **Answer language:**
  - the language is detected per question;
  - the prompt tells the model to answer in that language, with the Urdu
    short-answer label;
  - refusals have an Urdu version too.
- **Limit:** retrieval for Urdu questions is weaker than for English. Test
  any Urdu demo question beforehand.

---

## 4. Difference from ChatGPT / Gemini

| | General chatbot | LegalEase AI |
|---|---|---|
| Sources | Answers from training data; can invent sections or case citations | Answers only from retrieved Pakistani statute passages, cited `[n]`; unverifiable sections flagged, case citations removed |
| Scope | Answers anything | Refuses non-legal and out-of-library questions without calling the model |
| Jurisdiction | Can mix up Indian and Pakistani law | Library holds Pakistani law only |
| Workflow | Chat only | Cases, documents, contracts and research in one place, with role-based access |

Be honest about the limits. The library is smaller than a commercial
database, and holds no case law.

---

## 5. Non-functional requirements (measured)

| Requirement | Status |
|---|---|
| **Security** | bcrypt (cost 12); JWT access 60 min and refresh 7 days, in HttpOnly SameSite cookies; sign-out revokes all of a user's tokens; lockout after 5 failed logins; OTP on signup; uploads stored under generated names, type-checked before writing, size-capped while streaming; API docs served only in development |
| **Reliability** | A failed database connection is retried once, then a clear 503; text-less documents refused before any model call; chat history capped at 2,000 tokens so requests stay under Groq's 8,000 tokens a minute |
| **Performance** | **Weak spot:** the database is on Supabase in Singapore. Each query takes 0.2–0.4 s and a new connection about 4 s, so API calls take about 3–8 s. Chat answers took 9–27 s in testing, document analysis about 8 s, contract drafting about 7 s |
| **Usability** | Design system v1 on every page, at desktop and phone width; role-specific dashboards; a 404 page for unknown addresses |
| **Tests** | 306 backend tests (unit and HTTP); no frontend tests; full live run 2026-10-06 (`docs/evaluation/test-plan.md` § 13) |

---

## 6. Groq limits (plan the demo around them)

The free tier allows **200,000 tokens per day**, **8,000 per minute** and
**1,000 requests per day**, shared by every AI feature.
- **Cost per use:** a chat answer uses about 5,000 tokens; the daily
  allowance is roughly 35–40 answers.
- **Before the demo:** don't test heavily the day before. Use a separate,
  unused Groq account's key, or a paid tier.
- **During the demo:** keep AI calls about a minute apart.
- **If the budget runs out:** cases, document upload and research search
  keep working; AI answers show an error.

Details are in `docs/archive/PROJECT_CONTEXT.md`.

---

## 7. Demo script (features verified to work)

1. **Sign in** as a pre-verified lawyer. SMTP isn't configured, so signup
   codes appear only in the backend window.
2. **Cases:**
   - **New case** "Nadar Khan v. The State — bail": type Criminal, case
     number Crl.P. 187-P/2026, court, petitioner and respondent, next
     hearing date. Then link the client by email. It becomes Assigned
     automatically, and the timeline says so.
   - Open the case: the **Case details** panel shows the number, court,
     parties and next hearing (in red when upcoming). **Edit** a hearing
     date and the timeline records it. The dashboard lists it under
     **Upcoming hearings**.
   - **Mark as in progress.**
3. **Documents:**
   - Upload `docs/evaluation/demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf`.
   - **Analyse document** (about 8 s): summary, clauses, risks, parties and
     dates.
   - **Save to case.**
4. **AI Chat**, about a minute apart:
   - "What is the procedure for talaq under the Muslim Family Laws
     Ordinance?"
   - "What is the punishment for theft under the Pakistan Penal Code?"
   - "Can you recommend a good cricket bat?" (refused)
5. **Research:**
   - Search "bail in a non-bailable offence" and open the Cr.P.C. s. 497
     result.
   - **Analyse with AI.**
6. **Contracts:**
   - Draft an NDA with full addresses for both parties.
   - **Check compliance:** all clauses present, no unfilled placeholders.
   - Show the version history.
7. **Client view:** sign out, sign in as the client, and show the dashboard
   and the read-only case.

**Avoid:**
- khula or inheritance questions (retrieval gap);
- PPC s. 302 and Contract Act s. 10 questions (known misses).

### Knowledge Base in 60 seconds (branch `kb-v2` only, not in the mock tag)

1. **Knowledge Base** in the sidebar: the stat strip (35 laws, ~3,177
   section records, 499 of 526 listed Pakistan Code Acts held; 176 more are
   counted by the site but not listed).
2. Open **Guardians and Wards Act, 1890**: its metadata, the source label
   ("LegalEase corpus (Pakistan Code-derived)") and the Pakistan Code
   notice. Never call it official text: the Gazette is authoritative.
3. Click **s.17 Matters to be considered by the Court in appointing
   guardian**: the stored record appears as JSON (title, section, heading,
   text, source, tier, content hash, status).
4. **Download JSON**: the law's records as one file.

Say: every passage the chat or research shows can be traced to one of these
records, with where it came from.

### Starting the system

> **For the 2026-10-07 demo, use `docs/runbooks/demo-runbook.md` instead.** The
> commands below are the master setup, which is now the fallback.

Use two separate windows, so neither server is stopped when another tool
exits:

```powershell
# Window 1 — backend
cd backend
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
venv\Scripts\uvicorn.exe app.main:app --port 8000

# Window 2 — frontend
cd frontend
npm run dev
```

Open `http://localhost:5173`. Setup from scratch is in the root
`README.md`.

---

## 8. Likely questions

**Why RAG and not fine-tuning the language model?**
- Answers must cite the law they rely on.
- The law changes, so the index needs rebuilding without retraining.
- We have no large expert question-and-answer set.

We did fine-tune where we had labelled data: the NER model.

**Why FAISS and not a hosted vector database?**
- At 53,739 vectors × 384 dimensions, exact `IndexFlatIP` search runs
  in-process on the CPU.
- There's no extra service to host or pay for.
- Larger indexes can switch to an approximate FAISS index type.

**Why this embedding model?**
- It's multilingual (English and Urdu), small enough for the CPU, and free.
- Its limit is that it reads only 128 tokens of each chunk. The retrieval
  redesign handles that.

**What happens when the question isn't covered?**
The chat refuses without calling the model, in the question's language.

**What are the limitations?**
- The statute-only library, with retrieval gaps.
- OCR is good on clean printed scans (about 1% character errors); handwriting
  and Nastaliq-heavy Urdu are untested.
- Groq's free-tier limits.
- Database latency from the Singapore region.
- No frontend tests.
- The Practice Simulator and Notifications aren't built.

**What would you do next?**
1. Build the section-based retrieval redesign.
2. Configure SMTP for real OTP emails.
3. Move the database closer to the users.
5. Add frontend tests.
6. Build notifications for hearings and deadlines.

---

## Before the mock presentation (state on 2026-10-06)

**Scope:**
- The chatbot covers general Pakistani law (the supervisor's decision).
- Cases come in general types (civil, criminal, commercial, property,
  service) and family types (divorce, custody, inheritance, maintenance).
- No family-only mode is shown.

**Switched on:** OCR (English + Urdu), NER, token revocation, case fields,
and the research weak-match note.

**Switched off,** and why:
- the rewrite change (it cost answers on the lawyer questions);
- the stricter prompt (not measured);
- the low-confidence note (ready, awaiting approval);
- the family index (scope);
- email (SMTP not set; signup codes appear in the backend window).

**Say if asked:**
- Research always lists its closest passages. When none is a strong match,
  the page says so rather than hiding them.
- First page loads can take 6–10 s: Vite compiles each page on first visit,
  and the database is in Singapore.

---

## Demo start checklist (one page)

**1. Start the servers, each in its own terminal, and leave both open.**

For the 2026-10-07 demo, start them as in `docs/runbooks/demo-runbook.md` (kb-v2,
`KB_V2=true`). Then check http://localhost:8000/health shows `"kb_v2":true`.
The commands below are the master fallback.

```powershell
# Terminal 1: backend (http://localhost:8000)
cd backend
venv\Scripts\activate
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
uvicorn app.main:app --port 8000

# Terminal 2: frontend (http://localhost:5173)
cd frontend
npm run dev
```

Wait for the backend to log `Application startup complete`, then check that
http://localhost:8000/health shows `{"status":"ok"}`.

**2. Warm up, about 10 minutes before.** The dev server compiles each page
on its first visit (6–10 s), so open every page once. `vite preview` (the
production build) isn't used: login didn't go through in an automated test
on 2026-10-06, and it wasn't investigated further.

1. **As the lawyer:**
   - `/login` → sign in;
   - `/lawyer/dashboard`;
   - `/cases`, then open one case and click its Timeline and Documents tabs;
   - `/documents`;
   - `/chatbot`;
   - `/research`;
   - `/contracts`, then open one contract.
2. **One chat question,** to load the AI models and check Groq: *"What is the
   punishment for theft under the Pakistan Penal Code?"* (best match 0.85).
   Expect a cited answer with s.379. Start a new conversation afterwards.
3. **Sign out, then as the client:** `/client/dashboard`, then open their
   case.
4. **Sign out,** and sign back in as the lawyer.

**3. Demo order.**
1. **Lawyer dashboard:** open cases and upcoming hearings.
2. **New case:** type Criminal, "Nadar Khan v. The State — bail", number
   Crl.P. 187-P/2026, Supreme Court of Pakistan, petitioner and respondent,
   next hearing. Link the client by email (it becomes Assigned
   automatically), then **Mark as in progress**.
3. **Case → Add document:** upload
   `docs/evaluation/demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf`. Then **Documents →
   Analyse** (about 8 s).
4. **AI Chat,** one question a minute:
   1. *"On what grounds can a Muslim wife obtain a decree for dissolution
      of marriage?"* (Dissolution of Muslim Marriages Act s.2; best match
      0.84–0.90). It replaced the talaq question, which scored 0.679 live on
      2026-10-06 and would show the "Weak match" note;
   2. *"What is the punishment for theft under the Pakistan Penal Code?"*
      (PPC s.379);
   3. *"Can you recommend a good cricket bat?"* (refused, on purpose).
5. **Research:** *"bail in a non-bailable offence"* (CrPC s.497 first). Open
   it and **Save to case**.
6. **Contracts:** an NDA for the case, then the compliance check.
7. **Case timeline:** everything above in order.
8. **Sign out,** then sign in as the client: they see their case
   read-only.
9. **Optional:** a scanned page (PNG/JPG) in Documents shows OCR.

**4. If a question is refused, or shows the "Weak match" note,** say:
- "The assistant only answers from the Pakistani statute text it can find.
  When no passage is close enough, it refuses rather than guess. That's the
  design, not an error."
- Then rephrase it with the legal term (e.g. "talaq notice to the Chairman
  under section 7"), or use the theft question, which always finds PPC
  s.379.
- The "Weak match" note appears when the best passage only just passes
  (0.65–0.70). The talaq question scored 0.679 live on 2026-10-06, so it
  shows the note; that's why the demo uses the dissolution question.

**5. If the AI is slow or returns "unavailable":** Groq's free tier allows
8,000 tokens a minute and 200k a day. Wait a minute and ask again. Cases,
documents and research keep working without it.

---

## Cold-start rehearsal (run it once before the mock)

Start from nothing running: close every terminal, then time the whole run.

1. **Terminal 1, backend:**
   `cd backend` → `venv\Scripts\activate` → `set HF_HUB_OFFLINE=1` →
   `set TRANSFORMERS_OFFLINE=1` → `uvicorn app.main:app --port 8000`.
   Wait for `Application startup complete`.
2. **Terminal 2, frontend:** `cd frontend` → `npm run dev`. Wait for
   `Local: http://localhost:5173/`.
3. **Health checks:**
   - http://localhost:8000/health shows `{"status":"ok"}`;
   - http://localhost:5173 shows the landing page;
   - signing in works, which confirms the database (first sign-in can
     take about 5 s).
4. **Warm-up pages** (each compiles on its first visit):
   - as the lawyer: dashboard, Cases, one case with its Timeline and
     Documents tabs, Documents, AI Chat, Research, Contracts and one
     contract;
   - as the client: dashboard and their case.
5. **One chat question:** *"What is the punishment for theft under the
   Pakistan Penal Code?"* Expect a cited answer with s.379 and no
   weak-match note. Then start a new conversation.
6. **Demo order:**
   1. dashboard;
   2. new criminal case with number, court, parties and hearing; link the
      client; mark as in progress;
   3. upload and analyse Crl.P. 187-P;
   4. chat, one question a minute: DMMA grounds, theft, cricket bat
      (refused);
   5. Research: "bail in a non-bailable offence", then Save to case;
   6. NDA, compliance check, Edit draft (save as version 2), check again;
   7. case timeline;
   8. sign out, then the client view.
7. **If a panelist's question is refused:** "It only answers from the
   Pakistani statute text it can find. When nothing is close enough, it
   refuses rather than guess." Then rephrase it with the legal term, or
   offer the theft or DMMA question.
8. **If the weak-match note shows:** "The closest passage only just passed
   the relevance threshold, so the page warns the reader to check the
   cited sections. It flags uncertainty instead of hiding it."

---

## Frozen state for the mock (2026-10-07)

- **Tag:** `mock-2026-10-07`
- **Commit:** `ad9935d871d9c99c07ab27367e8858a9ef5a0ebb`
- Created 2026-10-06; the working tree was clean and everything was pushed
  to `origin/main`.
- This note was committed after the tag, so it's one docs-only commit on
  top of it.

**To return to this state if something breaks later:**

```powershell
git fetch --tags
git switch --detach mock-2026-10-07        # look at it, or run it as it was
git switch -c fix-from-mock mock-2026-10-07  # or branch from it to fix something
```

The database isn't versioned by the tag. Its schema matches migration
`e7b3c9d14a02` (`alembic current`).
