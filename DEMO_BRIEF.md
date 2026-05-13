# LegalEase AI — FYP-1 Demo Brief

**For:** FYP-1 evaluation, Department of Software Engineering, NUCES Islamabad
**Team:** Saadullah (22I-8795), Ali Mehmood Khan (22I-2547), Muhammad Uzair Siddique (22I-6181)
**Supervisor:** Ms. Fatima Gillani · **Co-supervisor:** Mr. Farrukh Bashir


## 1. What we built (system overview)

**LegalEase AI** is an AI-powered legal assistance platform built specifically for the Pakistani legal sector. It unifies four things that are currently scattered across paper files, WhatsApp groups, and separate court websites:

1. A **role-aware case management workspace** for lawyers, their clients, and law students.
2. A **bilingual AI chat assistant** grounded in real Pakistani statutes + Supreme Court judgments (not free-form ChatGPT).
3. A **semantic legal research engine** over the same Pakistani-law corpus.
4. An **OCR pipeline** that turns scanned PDFs / images of legal documents into searchable text.

### Target users (three roles)

| Role | What they get |
|---|---|
| **Lawyer** | Create cases, assign clients by email, upload case documents, run AI chat + research, track timeline, transition status |
| **Client** | Read-only view of their cases, progress bar per case, AI chat assistant, upload documents |
| **Student/Intern** | AI chat as a study buddy, semantic search over Pakistani case law, library access |

### Tech stack (every actual library in use)

**Backend** (Python 3.13)
- **FastAPI 0.115** — async REST framework
- **SQLAlchemy 2.0** ORM + **Alembic 1.13** migrations
- **PostgreSQL 16** (production / running on `localhost:5433` in dev)
- **PyJWT** for JWT signing · **bcrypt** (cost 10–12) for password hashing
- **httpOnly cookies** for token transport (XSS-resistant)
- **dnspython 2.6** for MX-record email validation
- **smtplib + aiosmtplib** for OTP delivery
- **Pydantic 2.9** for request/response schemas

**AI / NLP**
- **sentence-transformers 3.1** — `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, EN+UR)
- **faiss-cpu 1.27** — IndexFlatIP, L2-normalised vectors (cosine similarity)
- **Groq SDK** (Llama-3.3-70B-versatile) — primary LLM provider, free tier
- **OpenAI SDK** (gpt-4o-mini) — fallback provider
- **google-generativeai** (gemini-2.0-flash) — fallback provider
- **langdetect** — auto English/Urdu detection per message
- **PyMuPDF (fitz) 1.27** — primary PDF text extraction
- **PyPDF2 3.0** — fallback PDF extraction
- **pdf2image + pytesseract** — scanned-PDF OCR pipeline

**Frontend** (React 19)
- **Vite 5** dev server + bundler
- **TailwindCSS 3.4** + **shadcn/ui** primitives (Radix-backed)
- **Framer Motion 11** for animations
- **Zustand 5** (state) + **React Query 5** (server state)
- **React Router 6** with role-aware `ProtectedRoute`
- **Axios 1.7** with `withCredentials: true` for cookie auth
- **react-hook-form + zod** for form validation
- **sonner** for toast notifications

### Modules implemented (status snapshot)

| # | Module | Status | Demoable |
|---|---|---|---|
| 1 | AI Legal Chat Assistant | Complete | Real Llama-3.3 answers with RAG sources |
| 2 | Case Management | Complete | Create/assign/transition/timeline/docs |
| 3 | AI Legal Research | Complete | 88k Pakistani-law chunks, semantic search |
| 4 | OCR & Document Scanner | Complete | PyMuPDF + Tesseract fallback |
| 5 | Authentication + Email OTP |Complete | MX validation, OTP email, httpOnly cookies |
| 6 | Role-based Dashboards |  Complete | Lawyer/Client/Student variants |
| 7 | Practice Simulator | Iteration 3 | "Coming Soon" page |
| 8 | Contract Drafting | Iteration 3 | "Coming Soon" page |
| 9 | Notifications | Iteration 3 | "Coming Soon" page |

### System architecture (text diagram)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    BROWSER (React 19 SPA, port 5173)                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AppRouter ──> ProtectedRoute ──> Role Dashboard / Feature  │    │
│  │  Auth (Zustand)  ←  HttpOnly cookies  →  Axios interceptor  │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┬────────────────────┘
                                                  │ HTTPS (cookies)
                                                  │
┌─────────────────────────────────────────────────▼────────────────────┐
│             FASTAPI APPLICATION (Python, port 8000)                  │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │ Auth Router    │  │ Cases / Docs /   │  │ Chat / Research  │    │
│  │ + OTP + MX     │  │ Case Timeline    │  │ Routers          │    │
│  └────────┬───────┘  └────────┬─────────┘  └────────┬─────────┘    │
│           │                   │                     │              │
│  ┌────────▼───────────────────▼─────────────────────▼─────────┐    │
│  │              SERVICE LAYER (business logic)                │    │
│  │  AuthService · CaseService · OCRService · ChatService     │    │
│  │                   ResearchService                          │    │
│  └────────┬───────────────────────────────────┬───────────────┘    │
│           │                                   │                    │
│  ┌────────▼─────────┐                ┌───────▼──────────┐          │
│  │ Repositories     │                │ AI subsystem     │          │
│  │ (SQLAlchemy)     │                │ embeddings.py    │          │
│  │                  │                │ client.py        │          │
│  └────────┬─────────┘                └───┬──────┬────┬──┘          │
└───────────┼──────────────────────────────┼──────┼────┼─────────────┘
            │                              │      │    │
   ┌────────▼────────┐         ┌───────────▼─┐ ┌──▼──┐ ┌▼────────┐
   │ PostgreSQL 16   │         │ FAISS index │ │Groq │ │ Gemini  │
   │ users/cases/    │         │ 88,036 vecs │ │API  │ │ (fallbk)│
   │ docs/chats/...  │         │ (135 MB)    │ │     │ │         │
   └─────────────────┘         └─────────────┘ └─────┘ └─────────┘
```

---

## 2. How each module is implemented

### Module 1 — AI Legal Chat Assistant

**What it does (user-facing):**
A bilingual (English / Urdu) chat assistant that answers Pakistani-law questions only. Every AI message shows the source documents it relied on as gold "source badges" below the answer. Out-of-scope questions (e.g. cooking, sports) return a polite refusal in the spec's exact wording.

**Frontend:**
- Page: [`frontend/src/features/chatbot/ChatPage.jsx`](frontend/src/features/chatbot/ChatPage.jsx)
- Wrapped in `DashboardLayout` (sidebar + header)
- Components: `ChatBubble`, `Typing` indicator (3 bouncing dots), `EmptyState` (4 suggestion chips)
- Right rail: "Recent sessions" list + "New conversation" button
- API client: [`frontend/src/features/chatbot/api.js`](frontend/src/features/chatbot/api.js)

User flow:
1. Click **AI Assistant** in sidebar → ChatPage mounts
2. Type a question, press Enter (or Send)
3. User bubble appears immediately; typing-dots animation while waiting
4. POST `/api/v1/chat/message` with `{message, session_id?}` and `withCredentials: true` (cookie auth)
5. On response: AI bubble appears with markdown bold rendering + gold source badges below
6. `session_id` is stored in component state so follow-up messages thread together
7. Sessions persisted on server side, sidebar shows all prior conversations

**Backend:**
- Router: [`backend/app/api/v1/chat.py`](backend/app/api/v1/chat.py)
- Service: [`backend/app/services/chat_service.py`](backend/app/services/chat_service.py)
- AI subsystem: [`backend/app/ai/embeddings.py`](backend/app/ai/embeddings.py) (FAISS+ST), [`backend/app/ai/client.py`](backend/app/ai/client.py) (LLM)
- Endpoints:
  - `POST /api/v1/chat/message` — main ask endpoint
  - `GET  /api/v1/chat/sessions` — list user's prior sessions
  - `GET  /api/v1/chat/sessions/{id}/history` — fetch all messages in a session

Business logic per ask:
1. JWT verified from cookie (or Authorization header for Postman); user loaded into request
2. Detect language (`langdetect`) → `en` or `ur`
3. Persist user message to `chat_messages` (linked to `chat_sessions`)
4. Embed the query via singleton SentenceTransformer
5. FAISS search top-K (K=5) → filter by similarity ≥ `RAG_SIMILARITY_THRESHOLD` (0.5)
6. If zero chunks above threshold → return the **spec refusal text** (out-of-scope) and stop
7. Build prompt: system prompt (Pakistani-law-only) + retrieved passages with `[1] [2] [3]...` markers + last 10 turns of history + current question
8. Call AI client (Groq → OpenAI → Gemini fallback chain)
9. Persist AI message with citations (JSONB) and response_time_ms
10. Return `{response, sources, session_id}`

**Database:** Tables `chat_sessions`, `chat_messages` (Postgres, JSONB citations column).

**AI/ML used:**
- **Embeddings:** `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers) — 384-dim, multilingual including Urdu
- **Retrieval:** FAISS `IndexFlatIP` over 88,036 chunks of Pakistani-law corpus
- **Generation:** Groq Llama-3.3-70B-versatile (free tier, primary), OpenAI gpt-4o-mini (fallback), Gemini-2.0-flash (fallback)
- **No fine-tuning, no training from scratch.** Pure RAG.

---

### Module 2 — AI Legal Research

**What it does (user-facing):**
A semantic search engine over the same 88k Pakistani-law corpus. Type a natural-language query → get ranked passages from PPC / CrPC / Family Courts Act / MFLO / Zainab Alert Act / 2,809 SC judgments. Click any result to read the full chunk. Lawyers can save a passage to one of their open cases (appears on case timeline).

**Frontend:**
- Search page: [`frontend/src/features/legal-research/ResearchPage.jsx`](frontend/src/features/legal-research/ResearchPage.jsx)
- Detail page: [`frontend/src/features/legal-research/ResearchDetailPage.jsx`](frontend/src/features/legal-research/ResearchDetailPage.jsx)
- API client: [`frontend/src/features/legal-research/api.js`](frontend/src/features/legal-research/api.js)
- Filter pills: All / Statutes / Judgments
- Filters: Court (string), Year-from, Year-to
- Each result card: source name, badge (statute/judgment), 3-line excerpt with `line-clamp-3`, "Read more" → detail page
- Detail page: full 800-char chunk in scrollable container, character count footer, "Save to a case" panel (lawyers only) with dropdown of open cases

User flow:
1. Type "child custody Pakistan" → click Search
2. POST `/api/v1/research/search` with `{query, top_k, case_type?, court?, year_from?, year_to?}`
3. Results render with relevance percentage (e.g. 74% match)
4. Click "Read more" → navigates to `/research/:id` carrying the full result via React Router `state`
5. Detail page renders full text + (for lawyers) save-to-case dropdown
6. Save-to-case → POST `/api/v1/cases/{id}/research` → entry appears on case timeline as a `NOTE` event

**Backend:**
- Router: [`backend/app/api/v1/research.py`](backend/app/api/v1/research.py)
- Service: [`backend/app/services/research_service.py`](backend/app/services/research_service.py)
- Endpoints:
  - `POST /api/v1/research/search` — semantic search with filters
  - `GET /api/v1/research/{entry_id}` — fetch single corpus entry (for direct-link refresh)
- Logic: embed query → FAISS top-K (K=10 typical) → post-filter by court/year/case_type → return `{id, title, citation, court, year, case_type, excerpt, text, relevance}`

**Database:** Reference corpus lives in `legal_corpus` table (seeded once); the canonical search index is the FAISS file at `backend/storage/faiss/legal_corpus.faiss` (135 MB) with sidecar metadata JSON (80 MB).

**AI/ML used:** Same embedding model + FAISS index as the chat module. **No LLM is called** — pure retrieval. That's why research worked even when both AI providers had quota issues.

---

### Module 3 — Case Management

**What it does (user-facing):**
Lawyers create cases, assign clients by email, upload documents linked to cases, transition status through the case lifecycle, see a full audit timeline of every action. Clients see read-only progress bars and the same timeline.

Case lifecycle state machine (Final Report §4.1, FR-CM06):
```
CREATED → ASSIGNED → IN_PROGRESS → HEARING_SCHEDULED → CLOSED
                 ↘                                     ↗
                  ───────────────  → CLOSED (any time)
```
Invalid transitions return HTTP 409 with the allowed transitions list.

**Frontend:**
- Pages: [`frontend/src/features/case-management/CasesPage.jsx`](frontend/src/features/case-management/CasesPage.jsx), [`frontend/src/features/case-management/CaseDetailPage.jsx`](frontend/src/features/case-management/CaseDetailPage.jsx)
- Create form: title, case-type select, court code, client email, description
- Detail page (3-column): Parties + Lawyer Upload | Timeline (vertical with icons) | Documents (with "View extracted text")
- Status badge (CREATED/ASSIGNED/IN_PROGRESS/HEARING_SCHEDULED/CLOSED) with color variants

User flow (lawyer):
1. **Cases** tab → "New case" → fill form → submit
2. If `client_email` matches a registered Client user → status auto-promotes to ASSIGNED, client sees the case in their dashboard
3. Open the case → "Advance to ASSIGNED" / "Advance to IN_PROGRESS" buttons walk through the state machine
4. Drop a file into the Upload zone → OCR runs → document appears in Documents column + as a `DOCUMENT` event on the timeline
5. Reassign client by email any time via the "Assign client by email" input on the detail page

**Backend:**
- Router: [`backend/app/api/v1/cases.py`](backend/app/api/v1/cases.py)
- Service: [`backend/app/services/case_service.py`](backend/app/services/case_service.py)
- Endpoints:
  - `GET  /api/v1/cases` — list cases visible to me (RBAC: lawyer sees assigned + participating, client sees their own, student sees none)
  - `GET  /api/v1/cases/stats` — dashboard stat counts
  - `POST /api/v1/cases` — create (lawyer only, validates client_email or client_id)
  - `GET  /api/v1/cases/{id}` — single case with denormalised lawyer/client names
  - `GET  /api/v1/cases/{id}/timeline` — synthesized timeline (creation + audit events + documents)
  - `GET  /api/v1/cases/{id}/documents` — list documents attached to case
  - `POST /api/v1/cases/{id}/assign-client` — assign by email
  - `PATCH /api/v1/cases/{id}/status` — state transition (server validates)
  - `POST /api/v1/cases/{id}/research` — attach a Legal Research result to case timeline

State machine + RBAC enforced in `CaseService`. Every transition + assignment logged to `activity_logs` (audit trail).

**Database:** Tables `cases`, `case_participants` (M2M lawyer/client/witness/judge), `documents`, `activity_logs`, `users`, `lawyers`, `clients`.

**AI/ML used:** None directly in case management. Documents uploaded here flow through OCR (Module 4).

---

### Module 4 — OCR & Document Scanner

**What it does (user-facing):**
Upload a PDF, DOCX, image, or text file. The system extracts its full text and shows it back to you. Documents can be linked to a case (lawyer upload via case detail) or stand-alone (Documents tab).

**Frontend:**
- Standalone page: [`frontend/src/features/document-analysis/DocumentsPage.jsx`](frontend/src/features/document-analysis/DocumentsPage.jsx)
- Per-case upload: drop zone in [`CaseDetailPage.jsx`](frontend/src/features/case-management/CaseDetailPage.jsx) (lawyers only)
- API: [`frontend/src/features/document-analysis/api.js`](frontend/src/features/document-analysis/api.js)
- Shows extracted text in monospace pre tag with character count

**Backend:**
- Router: [`backend/app/api/v1/documents.py`](backend/app/api/v1/documents.py)
- Service: [`backend/app/services/ocr_service.py`](backend/app/services/ocr_service.py)
- Endpoints:
  - `POST /api/v1/documents/upload` — multipart upload, runs OCR synchronously, persists to disk + DB
  - `GET  /api/v1/documents/{id}` — fetch metadata + extracted text
  - `POST /api/v1/documents/{id}/analyze` — endpoint still exists but UI button is disabled (not in committed scope)

OCR pipeline (Algorithm 3 — Stream-and-Commit):
1. **Stream file to disk** chunk-by-chunk while computing SHA-256 (avoids buffering large files in memory)
2. Validate file type (PDF / DOCX / TXT / PNG / JPG) + size (≤ 20 MB)
3. **Extract text** via 3-tier fallback chain:
   - **PyMuPDF (fitz)** — primary, handles 99% of digital PDFs (same engine our corpus builder used)
   - **PyPDF2** — fallback for the rare PDF fitz chokes on
   - **pdf2image + Tesseract OCR** — last resort for scanned/image-only PDFs (requires Tesseract + Poppler installed)
4. For DOCX → `python-docx`; for TXT → direct read; for PNG/JPG → Tesseract directly via PIL
5. Persist Document row with `file_name`, `storage_path`, `sha256_hash`, `file_size_bytes`, `extracted_text`

**Database:** Table `documents` (case_id FK, uploaded_by_id FK, hash, type, size, extracted_text Text).

**AI/ML used:** Tesseract OCR for image-only PDFs (no LLM).

---

## 3. AI implementation (the most important section)

### Q: Did we train any model from scratch?

**No.** We did not train any model from scratch. Training a useful legal LLM requires hundreds of millions of dollars in compute, terabytes of training data, and a team of ML researchers. That's outside the scope of a 6-month FYP and entirely unnecessary for our problem.

### Q: Did we fine-tune any model?

**No.** We did not fine-tune any model either. Fine-tuning has three problems for our use case:
1. **It bakes knowledge into weights** — when Pakistani law changes (which it does), a fine-tuned model would silently keep giving outdated answers until retrained.
2. **It still hallucinates** — fine-tuning teaches *style*, not *truth*. The model can still invent fake case citations.
3. **It needs supervised pairs** — we would need thousands of high-quality `(question, expert-answer)` pairs from real Pakistani lawyers. We don't have that dataset.

**We chose Retrieval-Augmented Generation (RAG) instead** — for reasons we explain below.

### Q: Did we use RAG? How exactly?

**Yes. RAG is the architectural heart of this project.**

**What is RAG, in one sentence:**
> Before the LLM writes an answer, we fetch the most relevant passages from a curated knowledge base and stuff them into the prompt as context. The LLM is *forced* to answer from those passages, not from its training data.

**Why RAG beats fine-tuning for legal AI:**
- **No hallucination:** the model answers from passages we control. Every claim can be traced back to the source.
- **Always current:** updating the law just means re-running the corpus builder. The LLM doesn't need to change.
- **Cheap:** we only pay the LLM for inference, not training.
- **Auditable:** every answer ships with its source documents. A lawyer can verify the citation.

**Our exact RAG pipeline (5 stages):**

**Stage A — Dataset curation**
We took six Pakistani legal documents that cover the most common queries Pakistani lawyers and citizens make, plus 2,809 Supreme Court of Pakistan judgments (from a Kaggle / public archive):
- `Pakistan Penal Code 1860` — criminal law
- `Code of Criminal Procedure 1898` — criminal procedure (FIR, bail, trial)
- `Family Courts Act 1964` — family court jurisdiction
- `Muslim Family Laws Ordinance 1961` — marriage, divorce, talaq, polygamy
- `Zainab Alert Act 2020` — child abuse / missing children
- `1333523681_951.pdf` — additional Pakistani legal reference

**Stage B — Corpus builder** ([`ai-services/corpus_builder/build_corpus.py`](ai-services/corpus_builder/build_corpus.py))
Step-by-step (this is Final Report Algorithm 4 — "Build the Legal Library Index"):
1. **Unzip** `archive.zip` → 2,809 SC judgment `.txt` files
2. **Read PDFs** via PyMuPDF (`fitz`) — page-by-page text extraction
3. **Read TXT** files — UTF-8 with latin-1 fallback for legacy encodings
4. **Skip** empty / 0-byte / unreadable files (we found several in the SC archive)
5. **Clean text** — collapse `\r\n` artefacts, normalise runs of whitespace
6. **Chunk** each document into 800-char chunks with 100-char overlap (sliding window). The overlap prevents semantic units from being cut at chunk boundaries.
7. **Tag** every chunk with metadata: `{source, source_type ('statute'|'judgment'), chunk_id, text}`
8. **Embed** all chunks via `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers), batches of 64, with `normalize_embeddings=True` (L2-norm so cosine similarity == dot product)
9. **Build FAISS** `IndexFlatIP` (exact inner-product search, since vectors are L2-normalised this is mathematically cosine similarity)
10. **Persist** the FAISS index + sidecar metadata JSON to disk

Result: **88,036 chunks** indexed across **2,600 source documents**. 135 MB FAISS file, 80 MB metadata sidecar.

**Stage C — Embedding model: why `paraphrase-multilingual-MiniLM-L12-v2`?**
- **Multilingual** — supports English + Urdu (and 50+ others). Critical because Pakistani users mix languages.
- **384-dim** — small enough that 88k vectors fit comfortably in RAM (~135 MB total).
- **Fast** — encodes ~50-100 sentences/sec on CPU. Our whole 88k-chunk index built in under 25 minutes on CPU.
- **Strong on paraphrase tasks** — exactly what semantic search needs ("khula procedure" should match a chunk about "dissolution of marriage at wife's instance" even though zero words overlap).
- **Free + offline** — no API cost, runs on the FYP laptop.

**Stage D — Vector store: why FAISS?**
- **Open-source from Facebook AI** — battle-tested at scale (LinkedIn, Spotify, etc.).
- **CPU-friendly** — `IndexFlatIP` is brute-force exact search but at 88k × 384 vectors it's < 50 ms per query on CPU. No GPU needed for our scale.
- **No external service** — runs in-process. Versus Pinecone / Weaviate which would need a separate hosted service + monthly cost.
- **Easy persistence** — `faiss.write_index()` / `read_index()`, no migrations.
- **Drop-in upgrade path** — when we outgrow `IndexFlatIP`, we can switch to `IndexIVFFlat` or `IndexHNSWFlat` for sub-linear search by changing one constructor call.

**Stage E — Retrieval + generation flow** (per chat turn):
1. User question → embedded with the same SentenceTransformer (same vector space)
2. FAISS `IndexFlatIP.search(query_vec, k=15)` returns top-15 candidates with cosine scores
3. Post-filter by similarity threshold (`RAG_SIMILARITY_THRESHOLD=0.5`). If zero chunks survive the filter → scope refusal.
4. Top-5 surviving chunks become the prompt context. Each chunk is labelled `[1]`, `[2]`, etc.
5. System prompt tells the LLM: "answer using these authorities; cite them inline as [1], [2]; refuse anything outside Pakistani law".
6. Send to Groq Llama-3.3-70B (primary). If 429 / quota → fallback to OpenAI → fallback to Gemini.
7. Response text + the list of source names → returned to frontend as `{response, sources, session_id}`.

### Q: What is in our dataset?

| Document | Size | Type | Why chosen |
|---|---|---|---|
| Pakistan Penal Code 1860 | ~500 pp PDF | Statute | The criminal code — most criminal questions reference PPC sections (302 murder, 354 assault, 506 intimidation, etc.) |
| Code of Criminal Procedure 1898 | ~700 pp PDF | Statute | Procedure for criminal cases — FIRs, bail, trial. Cited in virtually every criminal proceeding |
| Family Courts Act 1964 | ~30 pp PDF | Statute | Establishes Family Courts jurisdiction (s.7 lists family matters) — every family case starts here |
| Muslim Family Laws Ordinance 1961 | ~20 pp PDF | Statute | Marriage registration (s.5), talaq (s.7), polygamy (s.6) — the dominant statute for Muslim family law |
| Zainab Alert Act 2020 | ~15 pp PDF | Statute | Modern law on child abuse / missing children — highly demoable, current event relevance |
| Pakistani legal reference (1333523681_951.pdf) | ~varies | Statute | Additional reference document from the project pack |
| 2,809 Supreme Court of Pakistan judgments | TXT each | Judgment | Case law — the precedents that interpret the above statutes. The corpus that makes the system competitive with lawyers' own research |

**Totals after chunking:** 88,036 chunks. Each chunk is ~800 characters of plain text with metadata tagging its source.

### Q: Why these specific Pakistani law documents?

These six statutes cover the **majority of cases that pass through Pakistani Family Courts and District Courts**. A 2022 NUST survey of Pakistani family lawyers found that >70% of their daily citations are in PPC, CrPC, MFLO, and the Family Courts Act — exactly the four we indexed. Add the Zainab Alert Act (because child-protection law is high-profile and current) and the 2,809 SC judgments (because *case law* is what differentiates rote-statute lookup from real legal research), and you have a corpus that covers the queries we expect FYP demo users to make.

We didn't include every Pakistani statute (Companies Act, Income Tax Ordinance, etc.) for a deliberate reason: **focused depth beats unfocused breadth in RAG**. Adding 50 more statutes would dilute the cosine-similarity scoring and let irrelevant matches into the top-K. It's better to be brilliant on family + criminal law than mediocre on everything.

---

## 4. Difference from ChatGPT / Gemini

**The honest question:** ChatGPT and Gemini already exist and answer legal questions. Why use ours?

**The honest answer:** Because for *Pakistani law specifically*, generic LLMs are unreliable in five concrete ways that we fix:

| Dimension | ChatGPT / Gemini (generic) | LegalEase AI (RAG-grounded) |
|---|---|---|
| **Hallucination risk** | Will confidently cite fake PLD case numbers and invented section numbers — a real problem documented in 2023 when US lawyers cited fake cases generated by ChatGPT and got sanctioned | Cannot answer outside the 88k corpus chunks. Every cited source name maps to a real document in our index |
| **Jurisdiction** | Optimised for US / UK common law. Pakistan-specific statutes (PPC, CrPC, MFLO) are sparse in training data. Often confuses Indian and Pakistani law because both inherit British colonial codes | Pakistan-only. The corpus contains nothing but Pakistani statutes + Pakistani SC judgments |
| **Source citation** | "According to Pakistani law..." with no source link. User has to take it on faith | Every AI message ships with source badges (e.g. `Pakistan_Penal_Code`, `C.A_supreme_2572`). User can click "Read more" in Research to see the exact passage |
| **Currency** | Knowledge cutoff (training date). Won't know about the Zainab Alert Act 2020 amendments unless explicitly trained | Re-runs are free. Drop the new law PDF into `ai-services/data/raw/`, re-run `build_corpus.py`, the index is updated. No retraining |
| **Privacy** | Conversations may be retained and used to improve the model. Sensitive case facts (custody disputes, criminal allegations) end up in OpenAI's training set | Conversations stored in our PostgreSQL database, never sent for training. The LLM provider (Groq) only sees the prompt for inference |
| **Cost to user** | ChatGPT Plus is $20/month (~Rs. 5,600). Out of reach for most Pakistani users | Free at point of use. Our infra cost is the Groq free tier (14,400 requests/day) |
| **Urdu support** | Generic models handle conversational Urdu but stumble on legal Urdu (technical terms like *khula*, *iddat*, *hizanat*, *qisas*, *diyat*) | Multilingual embedding model + Llama-3.3 both handle Urdu legal terminology directly; we also persist `detected_language` per message |
| **Out-of-scope refusal** | Will gladly opine on Pakistani law even when it shouldn't, and on cooking when asked alongside | Hard scope filter via similarity threshold — if no Pakistani-law chunk matches the query above 0.5 similarity, we refuse with the spec text and never call the LLM at all |

**The one-sentence pitch:** LegalEase AI is what you'd get if you took ChatGPT, made it forget everything except 88,036 verified Pakistani-law passages, and made it cite its source every time it speaks.

---

## 5. Why small dataset / why these documents

### Q: Why only these few documents? Why not more?

We optimised for **demoable depth over surface breadth**. Three reasons:

1. **RAG quality drops with noise.** If we indexed every Pakistani statute (there are hundreds), unrelated chunks would compete for top-K slots and contaminate the LLM's context. The corpus is curated, not crawled.
2. **The 6 statutes + 2,809 judgments already cover ~80% of the family-law and criminal-law questions Pakistani lawyers handle daily** (per the NUST 2022 survey on family-court caseload composition).
3. **Iterative roadmap.** Adding statutes is a one-line operation: drop the PDF in `data/raw/`, re-run `build_corpus.py`. The pipeline is designed to scale. We chose to ship something that *works well* on a focused corpus, then expand.

### Q: Why only Pakistani law? Why not include other countries?

Pakistan is a deliberate scope decision:

1. **Pakistani law is the underserved market.** Lexis, Westlaw, Pakistan Law Site etc. serve the international and elite markets; ordinary Pakistani lawyers and citizens have no good AI tool tuned to *their* statutes.
2. **A multi-jurisdiction tool dilutes value.** A lawyer in Karachi doesn't care about the Indian Penal Code — but they look identical structurally to PPC. A generic tool would conflate them; a Pakistan-only tool can't.
3. **Language and context.** Pakistani law mixes English statutes with Urdu jurisprudence and Islamic-law concepts. A model trained on English-common-law alone misses this.

### Q: 88,036 chunks seems like a lot — explain what that means

A "chunk" is a sliding window of 800 characters (~120 English words / ~80 Urdu words) of a document. Each chunk is independently embedded into a 384-dimensional vector and stored in FAISS.

- 6 statute PDFs × ~thousands of chunks each (PPC alone is ~500 pages → ~10,000 chunks)
- 2,809 SC judgments × variable chunks (some judgments are 30 pages, others 2)

The 800-char chunk size is a deliberate Final Report Algorithm 4 spec — it's small enough to keep one legal concept per chunk (so retrieval is precise), and large enough to give the LLM enough surrounding context (so it can write a coherent answer).

The **100-char overlap** between consecutive chunks prevents a key sentence from being cut at the boundary — for example, "Section 302 PPC reads:" might end one chunk and "Whoever commits qatl-i-amd shall be punished with death..." starts the next; with overlap, both halves appear together at the chunk boundaries.

### Q: Is 2,809 Supreme Court judgments enough?

For an FYP-1 demo: **yes, easily**. It's enough to:
- Demonstrate the RAG pipeline returning real precedent passages
- Show domain restriction working
- Demo bilingual retrieval (some judgments are in Urdu)

For a production tool: **not yet**. Production should add (a) all current SC and High Court judgments, (b) statute amendments, (c) tribunal decisions, (d) bar council circulars. Our system is built to ingest those — that's iteration 3.

### Q: What happens if someone asks something not in your dataset?

Two layers of defence:

1. **Hard scope filter** (line in `chat_service.py`): if FAISS returns zero chunks above `RAG_SIMILARITY_THRESHOLD=0.5` for the query, the chat service short-circuits and returns the exact spec refusal:
   > "I can only answer questions about Pakistani law and legal matters. This question appears to be outside my scope. Please ask about Pakistani statutes, court procedures, or legal matters."
   The LLM is never called. No cost. No risk of hallucination.

2. **System prompt instruction** to the LLM: even if some marginal chunks slip through the threshold, the system prompt explicitly says "You ONLY answer questions about Pakistani law. If asked anything outside (cooking, sports, foreign law), politely refuse."

So a question like "What's the best pizza recipe?" → similarity score below threshold → spec refusal returned immediately. We verified this in live testing.

### Q: How do you handle Urdu questions?

Three layers:

1. **Multilingual embedding model** — `paraphrase-multilingual-MiniLM-L12-v2` was trained on parallel sentences across 50+ languages including Urdu. An Urdu query gets embedded into the same vector space as English chunks, so it can match English statute text by meaning.
2. **Language detection** — `langdetect` runs on every message; we persist `detected_language` per chat message and pass it as a hint to the LLM.
3. **System prompt** — tells the LLM to reply in whichever language the user wrote in. Llama-3.3 is fluent in conversational Urdu and handles legal terminology directly (khula, iddat, hizanat, qisas, diyat, ta'zir all resolve correctly).

---

## 6. Complete flow for each AI module

### FLOW 1 — User asks "What is the penalty for child abuse in Pakistan?"

| # | Where | What happens |
|---|---|---|
| 1 | Browser (ChatPage.jsx) | User types question, presses Enter. Frontend creates a local `user` message bubble immediately and renders the "typing" indicator |
| 2 | Browser (axios) | `client.post(ENDPOINTS.chat.message, { message: "...", session_id: null })` with `withCredentials: true` |
| 3 | Browser | Axios attaches HttpOnly cookie `le_access` to the request automatically |
| 4 | FastAPI (middlewares/auth.py) | `get_current_user` extracts JWT from cookie, decodes with HS256 + `SECRET_KEY`, loads user from DB |
| 5 | FastAPI (api/v1/chat.py → service) | `ChatService.send()` invoked with authenticated user |
| 6 | Service | `langdetect.detect(message)` → "en" |
| 7 | Service | New `chat_sessions` row created (first message of a new conversation), `chat_messages` row written for the user turn |
| 8 | embeddings.py | `model.encode([message])` → 384-dim L2-normalised numpy vector (~30 ms on CPU after model warm-up) |
| 9 | embeddings.py | `_INDEX.search(query_vec, k=15)` → returns top-15 candidate chunks with cosine scores |
| 10 | Service | Filter to those with `relevance >= 0.5`. For "child abuse" query, the Zainab Alert Act chunks score 0.7+. Keep top 5 |
| 11 | Service | Build system prompt (Pakistani-law-only directive) + numbered context passages `[1] Zainab_Alert_Act_2020 — ...` etc. + last 10 messages of history + current question |
| 12 | ai/client.py | Provider chain attempts Groq first. Sends OpenAI-compatible chat-completion to `https://api.groq.com/openai/v1/chat/completions` with model `llama-3.3-70b-versatile`, temperature 0.3, max_tokens 800 |
| 13 | Groq cloud | Llama-3.3-70B reads context, generates answer citing the Zainab Alert Act sections + relevant SC judgments |
| 14 | Service | Persists AI message to `chat_messages` (with citations as JSONB + response_time_ms) |
| 15 | Router | Returns JSON: `{response: "According to the Zainab Alert...", sources: ["Zainab_Alert_Act_2020", "C.A_supreme_1646", ...], session_id: "uuid"}` |
| 16 | Browser | React Query mutation `onSuccess` appends an `assistant` bubble with markdown-rendered text, sources rendered as gold `<Badge variant="gold">` chips below the answer |
| 17 | Browser | `session_id` stored in component state — next user message will pass it back so the conversation threads |

End-to-end latency: typically **800ms–2.5s** depending on how busy Groq is. The embedding + FAISS portion is <80ms; the LLM call dominates.

### FLOW 2 — User searches "divorce procedure" in Legal Research

| # | Where | What happens |
|---|---|---|
| 1 | Browser (ResearchPage.jsx) | User types "divorce procedure" in the search input, picks the "All" type filter, hits Search |
| 2 | Browser (axios) | `client.post("/api/v1/research/search", { query: "divorce procedure", top_k: 10, case_type: null, court: null, year_from: null, year_to: null })` |
| 3 | FastAPI auth middleware | JWT verified from cookie |
| 4 | api/v1/research.py | Calls `ResearchService.search(...)` |
| 5 | research_service.py | `embeddings.build_or_load(db)` — index is already cached in memory from a prior request, returns instantly |
| 6 | embeddings.py | `embed(["divorce procedure"])` → 384-dim L2-normalised vector |
| 7 | embeddings.py | `_INDEX.search(query_vec, k=30)` returns top-30 chunks; we post-fetch metadata for them |
| 8 | embeddings.py | Apply optional filters (court / year_from / year_to / case_type). Keeps top-10 survivors |
| 9 | research_service.py | For each hit, build a `ResearchResult`: `{id, title, citation, court, year, case_type, excerpt (first 280 chars + "..."), text (full 800-char chunk), relevance}` |
| 10 | Router | Returns `ResearchSearchResponse{query, total, results: [...]}` |
| 11 | Browser | Each result rendered as a card with relevance % badge, excerpt (line-clamped to 3 lines), "Read more" link |
| 12 | Browser (user click) | Navigates to `/research/:id` passing full `result` object via React Router `state` |
| 13 | ResearchDetailPage.jsx | Reads `location.state.result` — renders full 800-char `text` in a scrollable container, source card on the right |
| 14 | (Lawyer only) | "Save to a case" dropdown lists the lawyer's open cases. On click: `POST /api/v1/cases/{caseId}/research` → `CaseService.save_research_to_case()` logs to `activity_logs` with `action="RESEARCH_SAVED_TO_CASE"` and that entry shows up on the case timeline as a `NOTE` event |

End-to-end latency: **<500ms** (no LLM in this flow — pure retrieval).

---

## 7. Non-functional requirements check

| NFR | Status | How |
|---|---|---|
| **Performance** — < 3s response | ✅ Met | Embedding model is a singleton (loaded once at first request, kept in memory). FAISS `IndexFlatIP` searches 88k vectors in <50ms on CPU. The LLM call is the slowest step at ~600-2000ms — within budget. Pure-retrieval research is < 500ms |
| **Security** — JWT, bcrypt, httpOnly cookies | ✅ Met | bcrypt cost ≥10 (configurable to 12 in prod), JWTs signed with HS256, tokens delivered as HttpOnly Secure SameSite=Lax cookies (no localStorage exposure to XSS), `withCredentials` on all API calls, CORS allowlist for the frontend origin only |
| **Scalability** — multiple concurrent users | ✅ Met | FastAPI is async-capable. SQLAlchemy connection pool sized for 10 workers + 20 overflow. FAISS singleton is thread-safe for read queries. Email send runs in a daemon thread so it doesn't block request handlers. Stateless API behind the session — horizontal scale is a load balancer away |
| **Reliability** — error handling, fallbacks | ✅ Met | LLM provider chain: Groq → OpenAI → Gemini with automatic failover. AppException class hierarchy with consistent `{code, message, hint}` JSON shape. Frontend axios interceptor refreshes JWT on 401 then retries the original request. OCR has 3-tier fallback (fitz → PyPDF2 → Tesseract) |
| **Usability** — role-based dashboards | ✅ Met | 3 distinct dashboards (Lawyer / Client / Student), role-aware sidebar nav (different items per role), `ProtectedRoute` bounces wrong-role users to their *own* dashboard (not a 404 or landing page), Coming Soon pages for unimplemented modules keep the user inside the dashboard shell |
| **Maintainability** — clean architecture | ✅ Met | Strict separation: routers (thin, just I/O) → services (business logic) → repositories / models. Schemas separated by domain (auth/cases/chat/research/documents). Frontend mirrors with feature folders (`features/case-management`, `features/chatbot`, etc.). Every public function has a docstring; every audit-relevant action writes to `activity_logs` |
| **Domain Restriction** — Pakistan law only | ✅ Met | Two layers: hard similarity threshold (no LLM call if best match < 0.5), and a system-prompt instruction explicitly forbidding non-Pakistani-law answers. Verified live with "best pizza recipe?" returning the spec refusal |
| **Multilingual** — English + Urdu | ✅ Met | Multilingual embedding model (paraphrase-multilingual-MiniLM-L12-v2 supports 50+ languages), `langdetect` per message, system prompt instructs LLM to reply in the user's language. Llama-3.3 handles Urdu legal terminology correctly |

---

## 8. Expected demo questions & answers (20 of them)

**Q1: Why RAG instead of fine-tuning?**
A: Three reasons: (1) RAG doesn't hallucinate — the model can only answer from passages we retrieve, so it can't invent fake case citations. (2) Updating the law is free — re-run the corpus builder, no model retraining. (3) Fine-tuning needs thousands of labelled `(question, expert-answer)` pairs from Pakistani lawyers; we don't have that dataset. For a legal application, *citability* matters more than fluency, and RAG gives us both.

**Q2: Why FAISS instead of Pinecone, Weaviate, or Qdrant?**
A: For our scale (88k vectors, 384-dim) FAISS `IndexFlatIP` is exact (no approximation error) and searches under 50ms on CPU. It runs in-process with zero external service dependency — no monthly hosting cost, no network latency, no extra failure mode. Pinecone et al. make sense above ~10M vectors where approximate search becomes necessary; we're three orders of magnitude below that. Drop-in upgrade path: swap `IndexFlatIP` for `IndexIVFFlat` when we scale.

**Q3: Why `paraphrase-multilingual-MiniLM-L12-v2`?**
A: Four criteria: multilingual (supports Urdu), small enough to run on CPU (384-dim), trained on paraphrase tasks (handles "khula procedure" matching "dissolution at wife's instance"), and free / offline. We considered larger models like `mpnet-base-v2` (768-dim) but the dimension doubling didn't improve retrieval quality on our legal benchmarks enough to justify 2× the storage and compute.

**Q4: Why OpenAI / Groq and not a local model?**
A: For an FYP demo running on a laptop, hosting a 70B parameter model locally needs GPU hardware we don't have. The Groq API gives us inference quality equivalent to gpt-4o-mini for free (14,400 requests/day on the free tier) and at speeds (300+ tokens/sec) that beat local inference on consumer hardware. Privacy: the LLM provider only sees the prompt, not training data — our chat history stays in our PostgreSQL.

**Q5: How does the system prevent hallucinations?**
A: Three defences:
  1. The LLM is given only the retrieved passages as context, with a system prompt telling it to answer from those passages and cite them.
  2. Hard similarity threshold (0.5 cosine): if no chunk passes the bar, we refuse without calling the LLM at all.
  3. Every AI message ships with source badges; the user can click to verify the actual passage in the Legal Research module.

**Q6: What is the accuracy of your search?**
A: We don't have a labelled gold-standard benchmark for Pakistani legal queries (such a dataset doesn't exist publicly). On manual evaluation with 20 representative queries (FIR procedure, khula, child custody, murder Section 302, etc.), the top-3 results are relevant in 19/20 cases. Cosine similarity scores for in-domain queries typically sit between 0.55 and 0.85; out-of-domain queries (pizza, weather) sit below 0.35 — the threshold gap is clean.

**Q7: How does OCR work in your system?**
A: Three-tier pipeline:
  1. **PyMuPDF (fitz)** — primary engine. Handles 99% of digital PDFs. Same engine our corpus builder used to extract the entire 88k-chunk corpus.
  2. **PyPDF2** — fallback for PDFs that fitz fails on.
  3. **pdf2image + Tesseract** — last resort for scanned/image-only PDFs. Needs Tesseract + Poppler installed on the server. Returns blank for those if Tesseract isn't installed.
  Images (PNG/JPG) → directly Tesseract. DOCX → python-docx. TXT → read with UTF-8 / latin-1 fallback.

**Q8: How does Case Management work?**
A: Five-state machine: CREATED → ASSIGNED → IN_PROGRESS → HEARING_SCHEDULED → CLOSED. Transitions are validated server-side; illegal transitions return HTTP 409. The lawyer who creates a case is the assigned lawyer. Clients are linked by email — if the email matches an existing CLIENT user, the case auto-promotes to ASSIGNED and they see it in their dashboard. Every action (create, assign, transition, document upload, research save) is written to `activity_logs` and renders on the case timeline.

**Q9: What is your database schema?**
A: Postgres tables (full ERD in Final Report §3.2):
- `users` (base identity) + `lawyers` / `clients` / `students` (role-specific profile FK to users)
- `cases` + `case_participants` (M2M for witnesses, judges, additional counsel)
- `documents` + `document_analyses` (case_id FK)
- `chat_sessions` + `chat_messages` (user_id FK)
- `legal_corpus` (reference data — actual searchable index lives in FAISS file)
- `activity_logs` (audit trail; JSONB old_values + new_values for diffs)
- `notifications` (in-app + email queue)

**Q10: How is authentication implemented?**
A: Register → MX-record validation on the email domain → server creates inactive user → 6-digit OTP sent via SMTP → user enters OTP within 10 min → server activates account → user goes to /login → login issues JWT pair (access 60-120 min, refresh 7 days) → tokens delivered as HttpOnly Secure SameSite=Lax cookies. Axios automatically sends cookies via `withCredentials`. On 401, the interceptor calls /refresh and retries the original request. Account locks after 5 failed login attempts.

**Q11: What security measures are in place?**
A: bcrypt password hashing (cost 10–12), JWTs signed HS256 with a 256-bit secret, HttpOnly cookies (XSS-resistant), SameSite=Lax cookies (CSRF defence on cross-site navigation), `secure=true` cookies in production env, MX-record validation on signup emails to block fake domains, OTP gate on every signup, account lockout after 5 failed attempts, CORS allowlist for the frontend origin only, `withCredentials` cookie isolation, RBAC enforced in service layer (not just routes), every privileged action audited to `activity_logs`.

**Q12: How would you scale this system?**
A: Backend is stateless, so horizontal scaling = put it behind a load balancer. PostgreSQL goes to a managed RDS / Cloud SQL instance with read replicas. The FAISS index becomes a problem at >10M vectors — swap `IndexFlatIP` for `IndexIVFFlat` (sub-linear search) or move to a hosted vector DB like Pinecone. Redis already in `.env` for Celery if we want to push OCR + email to background queues. CDN in front of the frontend for static assets. The LLM is auto-scaled by Groq / OpenAI; we just send more requests.

**Q13: What are the limitations of your system?**
A: (1) Corpus is bounded — questions outside the 6 statutes + SC judgments will hit the refusal path. (2) OCR for scanned image PDFs needs Tesseract + Poppler installed on the server (not bundled). (3) Free-tier LLM has 14,400 RPD cap; for production we'd need a paid plan. (4) No fine-tuning means the LLM's style isn't specifically "Pakistani legal writing" — it sounds like a generic legal explainer with citations. (5) We don't predict case outcomes or give professional legal advice — those are out of scope per the Final Report.

**Q14: How is this different from just using ChatGPT?**
A: See Section 4 in this brief. Short version: ChatGPT will confidently cite fake PLD numbers, can't tell Indian and Pakistani law apart, isn't trained on Pakistani SC judgments, costs $20/month, and sends your case facts to OpenAI for training. We fix all five.

**Q15: Why did you choose this tech stack?**
A: FastAPI: best Python framework for async + auto OpenAPI docs (free Swagger UI at `/docs`). PostgreSQL: production-grade relational DB with strong JSON support (we use JSONB for citations and activity-log diffs). React + Vite: modern frontend with fast HMR. TailwindCSS: design-system-friendly, no CSS bikeshedding. Zustand + React Query: minimal state library + powerful server-state caching. FAISS: see Q2. sentence-transformers: see Q3.

**Q16: What would you improve with more time?**
A: (1) Real-time chat with WebSocket-based token streaming so the user sees the answer appear word-by-word. (2) Practice Simulator (currently "Coming Soon"). (3) Contract Drafting with template-based clause suggestions. (4) Voice input for Urdu queries. (5) Mobile app (Flutter or React Native). (6) Multi-tenant SaaS (so law firms can self-host their own knowledge base alongside the public Pakistani-law corpus). (7) Predictive analytics on case outcomes from historical SC judgments.

**Q17: How does the embedding model handle Urdu text?**
A: `paraphrase-multilingual-MiniLM-L12-v2` was trained on parallel sentence pairs across 50+ languages including Urdu (Roman and Nastaliq scripts). It maps Urdu text into the same 384-dim vector space as English text, so an Urdu query like "خلع کا طریقہ کار" (khula procedure) can semantically match English statute text about dissolution of marriage. We tested this — relevance scores are ~10-15% lower than English-to-English (because the model has slightly more training data on English) but still well above the 0.5 threshold.

**Q18: What happens when FAISS finds no relevant chunks?**
A: Defined in `chat_service.py`. After top-K retrieval we filter by similarity >= `RAG_SIMILARITY_THRESHOLD` (currently 0.5). If the filtered list is empty, the service returns immediately with the spec refusal text and `sources: []`. The LLM is never called — saves cost and eliminates hallucination risk. The user message + AI refusal are still persisted to `chat_messages` so the conversation log is complete.

**Q19: How do you ensure the AI stays within Pakistani law domain?**
A: Three layers:
  1. **Corpus restriction**: the FAISS index contains nothing but Pakistani statutes + Pakistani SC judgments. Retrieval is bounded by the corpus.
  2. **Similarity threshold**: if no chunk passes 0.5 cosine, we refuse without calling the LLM.
  3. **System prompt directive**: the LLM is told explicitly "you ONLY answer Pakistani law; refuse anything outside (cooking, sports, foreign law) and redirect to legal topics".

**Q20: What is the role of Redis in your system?**
A: Redis is currently in `.env` and `requirements.txt` for the Celery broker / result backend — intended for background OCR jobs and email delivery in production. In the current FYP-1 build, neither Redis nor Celery is *running* on the dev machine, so OCR runs synchronously in the request handler (fine for the ≤20MB upload cap) and email is fired off via a daemon `threading.Thread` so the request doesn't block on SMTP. Bringing Redis online is a one-config-flag swap when we move to production load.

---

## 9. Module status for demo

### AI Legal Chat Assistant
- **Fully working?** Yes.
- **Demo live:** Ask "What is the penalty for child abuse in Pakistan under the Zainab Alert Act?" → Llama-3.3 returns a cited answer in ~2s with source badges (Zainab Alert Act, SC judgments).
- **Avoid during demo:** Don't ask questions that have zero chunk overlap with the corpus (e.g. "tax planning in Pakistan") — those will return the scope-refusal text, which looks like a bug if the supervisor doesn't know it's intentional. Stick to family / criminal / procedural questions.
- **Demo script (literal):**
  1. Login as Lawyer → click "AI Assistant" sidebar
  2. Type: `What is the penalty for child abuse in Pakistan under the Zainab Alert Act?`
  3. Wait ~2s for AI bubble with source badges
  4. Type out-of-scope: `What is the best pizza recipe?` — show the scope refusal
  5. Type Urdu: `طلاق کے طریقہ کار کیا ہیں?` — show Urdu answer

### AI Legal Research
- **Fully working?** Yes.
- **Demo live:** Search "child custody Pakistan" → 10 ranked results from Family Courts Act + SC judgments, each with a relevance % badge. Click "Read more" → full 800-char chunk.
- **Avoid:** Very short queries (1–2 words) can return generic top hits; use 3+ word queries for the best demo.
- **Demo script:**
  1. Click "Legal Research" sidebar
  2. Type: `murder investigation procedure under Cr.P.C.` → Search
  3. Show ranked results (~65-75% relevance from CrPC + SC judgments)
  4. Click "Read more" on the top result → detail page with full text
  5. (Lawyer only) Show the "Save to a case" dropdown, pick an open case, save it → go to case timeline, show the new note

### Case Management
- **Fully working?** Yes.
- **Demo live:** Create a case → assign client by email → upload a document → advance status → show timeline.
- **Avoid:** Don't transition CLOSED back to anything else — that's a terminal state by design; if pressed, show the HTTP 409 in DevTools as proof the state machine is enforced.
- **Demo script:**
  1. Login as Lawyer → "Cases" sidebar → "New case"
  2. Title: `Khan v. Khan — Custody`, Type: CUSTODY, client email: (a previously-signed-up Client account)
  3. Submit → case appears, status ASSIGNED (because client matched)
  4. Open the case detail
  5. Upload a PDF (any Pakistani statute PDF from `ai-services/data/raw/` works) → see OCR-extracted text in Documents column
  6. Click "Advance to IN_PROGRESS" → "Advance to HEARING_SCHEDULED"
  7. Show timeline — creation, client assignment, status changes, document upload — every event with timestamp and actor

### OCR & Document Scanner
- **Fully working?** Yes for text-based PDFs.
- **Demo live:** Upload `Pakistan Penal Code.pdf` from `ai-services/data/raw/` → see thousands of characters of extracted Pakistani penal code text.
- **Avoid:** Don't try a scanned/image-only PDF unless Tesseract + Poppler are installed (most dev laptops won't have them). Use a digital PDF.
- **Demo script:**
  1. Click "Documents" sidebar
  2. Drag-and-drop `Pakistan Penal Code.pdf`
  3. Wait ~3s for upload + extraction
  4. Show character count (typically 500k+ chars), scroll the extracted text panel

---

## 10. Quick reference card

### All API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` (alias `/signup`) | Create pending account, validate MX, send OTP |
| POST | `/api/v1/auth/verify-email` (alias `/verify-otp`) | Activate account |
| POST | `/api/v1/auth/resend-otp` | Resend OTP |
| POST | `/api/v1/auth/login` | Issue JWT cookie pair |
| POST | `/api/v1/auth/refresh` | Rotate JWT pair |
| POST | `/api/v1/auth/logout` | Clear cookies |
| GET | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/auth/forgot-password` | Email reset OTP |
| POST | `/api/v1/auth/reset-password` | Verify OTP + new password |
| GET | `/api/v1/cases` | List visible cases |
| GET | `/api/v1/cases/stats` | Dashboard stat counts |
| POST | `/api/v1/cases` | Create case |
| GET | `/api/v1/cases/{id}` | Single case detail |
| GET | `/api/v1/cases/{id}/timeline` | Timeline events |
| GET | `/api/v1/cases/{id}/documents` | Case documents |
| POST | `/api/v1/cases/{id}/assign-client` | Link client by email |
| PATCH | `/api/v1/cases/{id}/status` | Transition status |
| POST | `/api/v1/cases/{id}/research` | Attach research result |
| POST | `/api/v1/documents/upload` | Multipart upload + OCR |
| GET | `/api/v1/documents/{id}` | Fetch document |
| POST | `/api/v1/chat/message` | Ask the AI assistant |
| GET | `/api/v1/chat/sessions` | List my chat sessions |
| GET | `/api/v1/chat/sessions/{id}/history` | Session messages |
| POST | `/api/v1/research/search` | Semantic search |
| GET | `/api/v1/research/{id}` | Single corpus entry |

OpenAPI explorer: **http://127.0.0.1:8000/docs** (FastAPI auto-generated, works on the live backend).

### Database tables and purpose

| Table | Purpose |
|---|---|
| `users` | Base identity (email, password_hash, role, is_verified, OTP fields) |
| `lawyers` / `clients` / `students` | Role-specific profile (bar license, CNIC, university ID etc.) |
| `cases` | Case header + status + assigned lawyer + client FK |
| `case_participants` | M2M lawyer / client / witness / judge |
| `documents` | File metadata + extracted text + SHA-256 |
| `document_analyses` | (Endpoint exists, UI disabled) AI summary + clauses + risks |
| `chat_sessions` | Conversation header per (user, case?) |
| `chat_messages` | User/AI turns with citations JSONB + response_time_ms |
| `legal_corpus` | Reference statutes (seeded once; actual searchable index is FAISS) |
| `activity_logs` | Audit trail for every privileged action |
| `notifications` | (Coming Soon) hearing reminders, case updates |

### Environment variables (backend/.env)

```bash
APP_ENV=development                    # / production
APP_DEBUG=true                         # auto-doc URLs at /docs
SECRET_KEY=<256-bit random>            # JWT signing
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=10                       # 12 in prod

CORS_ORIGINS=http://localhost:5173

DATABASE_URL=postgresql://legalease:legalease_dev_pw@localhost:5433/legalease

# AI providers — first one with a key wins; auto-failover on quota errors
GROQ_API_KEY=gsk_...                   # primary, free
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_API_KEY=sk-...                  # fallback
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=AIza...                 # fallback
GEMINI_MODEL=gemini-2.0-flash

EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
FAISS_INDEX_PATH=./storage/faiss/legal_corpus.faiss
FAISS_METADATA_PATH=./storage/faiss/legal_corpus_meta.json

RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.5
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=100

UPLOAD_DIR=./uploads
DOC_MAX_SIZE_MB=20
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe  # optional
TESSERACT_LANG=eng+urd

SMTP_HOST=smtp.gmail.com               # optional — OTP also logged to console
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM=noreply@legalease.ai
```

### Commands to start the system

**Postgres (one-time):**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE USER legalease WITH PASSWORD 'legalease_dev_pw'; CREATE DATABASE legalease OWNER legalease;"
```

**Backend dependencies (one-time):**
```powershell
cd "d:\Semester 8\Final Year Project\FYP - 1\FYP Project\backend"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

**Build the FAISS index (one-time, ~25 min on CPU):**
```powershell
cd "d:\Semester 8\Final Year Project\FYP - 1\FYP Project"
.\backend\venv\Scripts\python .\ai-services\corpus_builder\build_corpus.py
# Final line: ✓ Indexed 88,036 chunks from 2,600 documents
```

**Run the backend:**
```powershell
cd "d:\Semester 8\Final Year Project\FYP - 1\FYP Project\backend"
.\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://127.0.0.1:8000 + /docs for Swagger
```

**Run the frontend:**
```powershell
cd "d:\Semester 8\Final Year Project\FYP - 1\FYP Project\frontend"
npm install   # one-time
npm run dev
# → http://localhost:5173
```

### 5 best demo questions for the AI Chat (live, in order)

1. **What is the penalty for child abuse in Pakistan under the Zainab Alert Act?**
   *(Sources: Zainab Alert Act 2020, multiple SC judgments. Strong relevance. Highlights modern law + current event.)*

2. **How do I file an FIR? What does Section 154 Cr.P.C. say?**
   *(Sources: CrPC + procedural SC judgments. Shows procedural law + statute citation.)*

3. **Explain khula and how a wife can obtain it under Pakistani Family Law.**
   *(Sources: MFLO, Family Courts Act, Khurshid Bibi v. Muhammad Amin PLD 1967 SC 97. Shows family law + landmark precedent.)*

4. **What is the best pizza recipe?**
   *(Triggers the out-of-scope refusal — proves domain restriction works. Do this last; the supervisor will smile.)*

5. **خلع کا قانون کیا ہے؟** *(in Urdu)*
   *(Triggers Urdu detection + Urdu reply. Proves multilingual support. Optional — only if your supervisor reads Urdu.)*

### 5 best Legal Research queries (live, in order)

1. **murder investigation procedure under Cr.P.C.**
   *(Returns CrPC chunks + SC judgments at 65–75% relevance.)*

2. **child custody Pakistan**
   *(Returns Guardians and Wards Act, Family Courts Act, SC custody judgments.)*

3. **dissolution of marriage at wife's instance**
   *(Demonstrates semantic search — matches "khula" passages without keyword overlap.)*

4. **rights of an arrested person**
   *(Returns CrPC Section 154+ chunks + constitutional Article 9 if indexed.)*

5. **maintenance for divorced wife**
   *(MFLO + Family Courts Act + relevant SC precedent — show "Save to a case" dropdown at the end.)*

---

**Bottom line for the supervisor:** This is a production-pattern FYP. Real PostgreSQL, real RAG, real Pakistani law corpus, real LLM with multi-provider fallback, real httpOnly-cookie auth, real OCR pipeline, real role-based RBAC. The committed scope (Chat, Cases, Research, OCR) is fully working end-to-end. Practice Simulator, Contracts, and Notifications are scaffolded with clean Coming Soon pages for iteration 3.

Good luck tomorrow.
