# LegalEase AI architecture (one page)

This describes what the code does today (branch `kb-v2`, 2026-10-08). For detail, see
[system-overview.md](system-overview.md), [knowledge_base_spec.md](knowledge_base_spec.md) and
[scraping.md](scraping.md).

## Components

| Component | Where | What it does |
|---|---|---|
| Frontend | `frontend/src/` | React 19 + Vite. One folder per feature in `features/`: auth, dashboard, case-management, chatbot, legal-research, knowledge-base, document-analysis, contract-drafting. It reaches the API through `api/` with Axios and cookies |
| API | `backend/app/main.py`, `app/api/v1/` | FastAPI routers for auth, cases, chat, research, documents, contracts and kb. `GET /health` reports the search mode and index sizes |
| Services | `app/services/` | Business rules and role checks: `legal_chat_service`, `research_service`, `case_service`, `contract_service`, `auth_service`, `ocr_service`. Document analysis runs in `api/v1/documents.py` with `ai/` |
| Knowledge base | `app/kb/` | Section records (`records`, `sectioner`), the law catalogue (`catalog`), FAISS + BM25 hybrid search (`index_v2`, `lexical`), exact section lookup (`exact_lookup`), query hints (`query_hints`), scope checks (`scope`), judgments (`judgments`, `judgment_search`, `judgment_catalog`), scraped laws (`scraped`) |
| AI layer | `app/ai/` | LLM client for Groq (`client`), embeddings and the original index (`embeddings`), query rewrite (`query_rewrite`), citation checker (`citation_check`), document reasoning (`reasoning`), legal NER (`ner`), summary sections, contract templates |
| Scraping | `app/scraping/`, `scripts/scraping/` | Fetches law sources, parses and stages them (with quarantine), keeps an update log, and indexes them (`scrape_laws.py`, `run_weekly.py`) |

## Chat pipeline (`LegalChatService.send`, `app/services/legal_chat_service.py`)

1. **Save the question.** Short database write: the session is created or loaded, recent history
   is trimmed to a token budget by `trim_history`, the language is detected with
   `_detect_language`, and the user message is committed. No transaction stays open during the AI
   work.
2. **Scope gate.** With `KB_V2`, `scope.foreign_only` refuses questions about another country's
   law before any retrieval.
3. **Search query.** `query_rewrite.rewrite_for_search` rewrites the question for search, using one
   model call.
4. **Retrieve passages.** `retrieve_passages` calls `embeddings.search`, which works in this order:
   1. adds the query hint terms (`query_hints.expand`);
   2. searches `index_v2.search` (vector + BM25, merged by rank) with `KB_V2`, otherwise the
      original FAISS index; with `SCRAPED_V2`, `scraped.merged_search` adds the scraped laws;
   3. keeps passages above the similarity threshold;
   4. replaces contents-list chunks with the sections they point to (`section_lookup`);
   5. puts directly named sections first (`exact_lookup.exact_passages`);
   6. swaps each section for its full text (`expand_sections`).
5. **Refuse when nothing passes.** No passages means a fixed out-of-scope reply, with no model call.
6. **Judgments.** With `JUDGMENTS_V2`, `retrieve_judgments` adds up to `JUDGMENTS_CHAT_K` case
   paragraphs above `JUDGMENTS_CHAT_MIN`, as context only.
7. **Answer and check.** `compose_answer` works in three steps:
   1. builds the prompt with `build_system_prompt` (numbered passages, plus the repealed-law rule
      when needed);
   2. calls the model (`ai.chat`);
   3. runs `check_citations` (in `ai/citation_check.py`), which removes citation markers that point
      to no passage and flags sections, figures and legal consequences the passages don't contain.
8. **Save and return the reply.** `_reply` stores the AI message with its citations and returns
   the answer, the numbered citations, the case law (with `JUDGMENTS_V2`) and the answer flags. If
   the model refused (`scope.is_refusal`), no sources are attached.

## Data stores

| Store | Holds |
|---|---|
| PostgreSQL (Supabase), via SQLAlchemy and Alembic | Users, cases, participants, documents and analyses, chat sessions and messages, contracts and versions, activity log. The scraping tables' migration exists but isn't applied |
| `backend/storage/kb/` (not in git) | Section records (`records/`, `records_all/`), judgments, scraped originals, the FAISS indexes `faiss_v2`, `faiss_v2_all`, `faiss_judgments`, `faiss_scraped` and `faiss_scraped_judgments` with their metadata, vector caches, `query_hints.json`, `category_map.json`, Colab export |
| `backend/storage/faiss/` (not in git) | The original statute index (`legal_corpus.faiss`), the fallback when the flags are off |
| `backend/storage/models/` (not in git) | The fine-tuned legal NER model |
| `backend/uploads/` (not in git) | Uploaded documents under generated names |

## Feature flags (`app/core/config.py`)

All four are off by default. `scripts/start_demo.ps1` turns them on; `-Safe` turns them off.

| Flag | On | Off |
|---|---|---|
| `KB_V2` | Search uses the section-level knowledge base (`faiss_v2_all` when present, otherwise `faiss_v2`) with hybrid BM25 + vector search, query hints, exact section lookup, section expansion and the foreign-law gate | The original FAISS index only |
| `JUDGMENTS_V2` | Chat and Research add judgment paragraphs from `faiss_judgments`, and Document Analysis lists related cases | No judgments |
| `SCRAPED_V2` | Search also covers the scraped Pakistan Code and KP Code laws (repealed laws are left out unless a filter asks for them). With `JUDGMENTS_V2` too, it covers the scraped Federal Shariat Court judgments | Scraped data isn't searched |
| `REASONING_V2` | Document Analysis adds the checked reasoning view (whole document in paced parts, statutes found in the text, contradicted "missing" points removed) | Summary, clauses, review points and entities only |
