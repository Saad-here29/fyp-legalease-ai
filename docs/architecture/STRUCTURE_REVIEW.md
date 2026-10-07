# Structure review: repository vs the reference layout (kb-v2 C12, 2026-10-08)

Rollback point: tag `kb-v2-pre-structure-2026-10-08` (`git reset --hard kb-v2-pre-structure-2026-10-08`).

**Actions:**
- **MOVE:** `git mv`, with every reference updated in the same commit.
- **KEEP:** stays as it is.
- **REPORT-ONLY:** a difference that is listed but not changed. These are areas the rules
  protect: `backend/app` packages, `backend/storage`, `frontend/src`, `.env` files and migrations.

## Root

| Reference | Here | Action |
|---|---|---|
| `README.md` | Present | KEEP; folder map updated to the final tree |
| `.gitignore` | Present | KEEP; new line for the stray backend file (see `backend/` below) |
| `.env.example` at the root | `backend/.env.example` and `frontend/.env.example`, one per app | REPORT-ONLY: `.env` files are not moved |
| `backend/`, `frontend/`, `scripts/`, `docs/`, `_to_review/` | Present | KEEP |
| — | `.editorconfig` | KEEP: a standard editor config file |
| — | `ai-services/`: the original corpus builder (`build_corpus.py`, which builds the fallback index) and the NER training notebook | KEEP: code and docs name these paths, and its git-ignored `ner_training/trained_model/` can't move with `git mv` |
| — | `data/`: only `README.md` in git; `data/raw` and `data/processed` are git-ignored data that the scripts read by path | KEEP |

## backend/

| Reference | Here | Action |
|---|---|---|
| `app/main.py` | Present | KEEP |
| `app/api/` (routes) | `app/api/v1/`: auth, cases, chat, research, documents, contracts, kb | REPORT-ONLY: the same routes, under a version folder |
| `app/core/`: config (flags), security, database | `core/`: config, security, cookies, exceptions, logging. The database code is in `app/db/` | REPORT-ONLY |
| `app/models/`, `app/schemas/` | Present | KEEP |
| `app/services/`: one per module (chat, research, document analysis, drafting) | `legal_chat_service`, `research_service`, `contract_service`, `case_service`, `auth_service`, `ocr_service`, `base` | REPORT-ONLY: **no document analysis service**. Analysis is in `api/v1/documents.py` with `ai/` |
| `app/ai/`: LLM client, embeddings, reasoning, citation checks | `client`, `embeddings`, `reasoning`, `citation_check`, plus `ner`, `summary_sections`, `section_lookup`, `query_rewrite`, `family_index`, `contract_templates`, `model_loading` | REPORT-ONLY: more modules than the reference |
| `app/kb/`: sectioner, records, index_v2, lexical, judgments, scope, query hints, repealed status | `sectioner`, `records`, `index_v2`, `lexical`, `judgments`, `scope`, `query_hints`, plus `judgment_search`, `judgment_catalog`, `catalog`, `exact_lookup`, `scraped`, `category_overrides.json` | REPORT-ONLY: **no separate repealed-status module**. Status is a record field, and `catalog.py` marks repealed sources |
| `app/scraping/`: fetcher, parsers, staging, weekly run | `fetcher`, `parse`, `stage`, `kb_run`, `runner`, `report`, `stats` | REPORT-ONLY: the weekly run is `scripts/scraping/run_weekly.py` |
| `app/tests/unit/`, `app/tests/integration/` | `unit/`, `fixtures/`, top-level `test_health.py` and `test_api_docs.py`. `integration/` exists on disk but is empty and not in git | REPORT-ONLY |
| — | `app/db/`, `app/repositories/`, `app/middlewares/`, `app/utils/` | REPORT-ONLY: extra packages |
| `alembic/` | Present | KEEP |
| `requirements.txt` | Present, plus `requirements-dev.txt` | KEEP |
| `storage/kb/`: records, records_all, judgments, scraped, vector_cache*, indexes/ | `storage/kb/` has those folders, but its FAISS indexes and metadata sit at the top of `kb/`, not in `indexes/`. Also `storage/faiss/` (the fallback index), `storage/models/` (NER), `kb/colab/`, `kb/raw/` | REPORT-ONLY: storage is never moved |
| — | `backend/faiss_judgments_meta.json`: untracked, byte-identical to `storage/kb/faiss_judgments_dev_meta.json`, and no code reads or writes this path (the configured paths are under `storage/kb/`) | MOVE on disk to `_to_review/backend/` (it isn't in git, so a plain move). It stays git-ignored, so the 784 KB of data doesn't enter git |

## frontend/

| Reference | Here | Action |
|---|---|---|
| `src/pages/`, `components/`, `api/`, `hooks/` | `src/features/` (screens grouped by feature), `components/`, `api/`, `routes/`, `store/`, `lib/`, `constants/`, `layouts/`; no `hooks/` | REPORT-ONLY: `frontend/src` is not moved |

## scripts/

| File | Reference place | Action |
|---|---|---|
| `start_demo.ps1` | `scripts/` | KEEP (same path) |
| `setup.ps1`, `README.md` | Not in the reference | KEEP: the first-time setup entry point and the scripts index |
| `kb/*` (18 files), `scraping/*` (7 files) | Already in place | KEEP |
| `scrape_laws.py` | `scripts/scraping/` | MOVE |
| `eval_chat_quality.py`, `eval_research_retrieval.py` | `scripts/kb/` (`eval_*`) | MOVE |
| `clean_statute_corpus.py` | `scripts/kb/` (corpus preparation) | MOVE |

## docs/

The reference has `README.md` plus `architecture/`, `evaluation/`, `runbooks/` and `archive/`. The
loose files at the top of `docs/` move into those folders:

| From | To | Action |
|---|---|---|
| `knowledge_base_spec.md`, `scraping.md`, `database-schema.md`, `retrieval_redesign.md`, `corpus_statute_list.md`, `STYLE_GUIDE.md`, `design_reference/` | `architecture/` | MOVE |
| `reports/` diagrams (13 PNGs, `Class.pdf`) | `architecture/diagrams/` | MOVE |
| `eval/c8_*` | `evaluation/c8/` | MOVE |
| `eval/chat_quality/` | `evaluation/chat_quality/` | MOVE |
| `query_hints_eval_2026-10-07.md`, `kb_v2_comparison_*` (2), `kb_v2_live_check_*` (2), `kb_coverage_2026-10-06.md`, `kb_phase_b1_2026-10-06.md`, `chat_baseline_2026-10-06.md`, `chat_review_family_law_2026-10-05.md`, `chat_quality_steps_2026-10.md`, `retrieval_gold_set_draft.md`, `ner_training_results.md`, `demo_examples.md`, `demo/` | `evaluation/` | MOVE |
| `DEMO_RUNBOOK.md` | `runbooks/demo-runbook.md` | MOVE |
| `reports/` FYP report PDFs (3) | `archive/fyp-reports/` | MOVE |
| `TIDY_PLAN.md` (the C11 record) | `archive/` | MOVE |
| `architecture/`, `evaluation/`, `runbooks/`, `archive/` | Already in place | KEEP |

The "only what code names stays put" rule from C11 doesn't apply here, because C12 updates every
reference. That includes comments in code, test paths, the output paths of report-writing scripts
and the description text in `c8_questions.json` (the questions themselves are unchanged). The
replay JSONs in `chat_quality/` record the absolute main-folder paths of their runs. That's
provenance, so it isn't rewritten.
