# Repository tidy-up plan (kb-v2 C11, 2026-10-08)

Rollback point: tag `kb-v2-pre-tidy-2026-10-08` (`git reset --hard kb-v2-pre-tidy-2026-10-08`).

**Rules followed:**
- Nothing is deleted. Files that look unneeded go to `_to_review/`, keeping their path.
- Code, tests, scripts, configs and `backend/storage` are not moved or edited.
- A document named by code, a test, a script or a config file (even in a comment)
  stays where it is, because that reference can't be edited under these rules.
- A document named only by other documents may move; those links are updated
  in the same commit.

**Decisions:** KEEP (stays where it is), MOVE (kept, new folder), MERGE (content
goes into another kept doc; the original is archived), ARCHIVE (to
`docs/archive/`), REVIEW (to `_to_review/`).

**"Named by"** lists the files that mention this one by name, other than
itself. In this column, *docs* means Markdown files only, which can be updated.

## Repository root

| File | What it is | Named by | Decision |
|---|---|---|---|
| `README.md` | Project overview (out of date: "statutes only", "317 tests") | many docs | KEEP, rewritten for the supervisor |
| `.editorconfig`, `.gitignore` | Editor and git settings | — | KEEP |
| `DEMO_BRIEF.md` | Demo script and likely questions (updated 2026-10-07) | docs only | MOVE → `docs/runbooks/demo-brief.md` |
| `PROJECT_CONTEXT.md` | Notes pasted into AI coding sessions; status as of 2026-10-06, before kb-v2 | docs only | ARCHIVE → `docs/archive/PROJECT_CONTEXT.md` |
| `ai-services/` | Corpus builder code and NER training notebook | code, docs | KEEP (code folder) |
| `data/` | Only `README.md` in git (the data itself is git-ignored) | `.gitignore`, docs | KEEP |
| `backend/`, `frontend/`, `scripts/` | Code | — | KEEP (not touched) |
| `backend/faiss_judgments_meta.json` | Untracked stray file next to the backend (not in git) | — | LEAVE: untracked, can't be moved with `git mv`, and may be written by a running process |

## docs/: kept where they are because code, tests or scripts name them

| File | What it is | Named by | Decision |
|---|---|---|---|
| `DEMO_RUNBOOK.md` | How to start, switch modes and present | `backend/app/main.py`, `test_health.py` | KEEP |
| `knowledge_base_spec.md` | Knowledge base design (phases B1–C10) | `app/api/v1/kb.py`, `app/kb/*.py`, `scripts/kb/write_b1_report.py` | KEEP |
| `scraping.md` | Law-update scraping design and operation | 36 files in `app/scraping`, models, migration | KEEP |
| `database-schema.md` | Tables, case status rules, migrations | `app/models/*.py` | KEEP |
| `STYLE_GUIDE.md` | Design system v1 | frontend source comments | KEEP |
| `design_reference/LegalEase AI Design System.pdf` | Source design | frontend source comments, `.gitignore` | KEEP |
| `retrieval_redesign.md` | Section-based retrieval design | `legal_chat_service.py` | KEEP |
| `retrieval_gold_set_draft.md` | Gold questions draft | `scripts/eval_chat_quality.py` | KEEP |
| `chat_review_family_law_2026-10-05.md` | 78-question chat review | `ai/client.py`, `family_index.py`, `legal_chat_service.py`, script | KEEP |
| `chat_quality_steps_2026-10.md` | Chat quality flags and results | `core/config.py`, `.env.example` | KEEP |
| `chat_baseline_2026-10-06.md` | Chat baseline before kb-v2 | `scripts/kb/compare_kb_v2.py` | KEEP |
| `corpus_statute_list.md` | Every document in the old search library | `AuthShell.jsx`, `category_map.json`, scripts | KEEP |
| `ner_training_results.md` | Legal NER training and results | `ai/ner.py`, `config.py`, `test_ner.py`, `requirements.txt` | KEEP |
| `demo_examples.md` | A real document analysed end to end | `ai/ner.py`, `test_ner.py` | KEEP |
| `demo/crl_p_187_p_2026/` (PDF and 2 JSON) | The demo document and recorded responses | `test_reasoning_c4.py` (PDF), `demo_examples.md` | KEEP |
| `kb_coverage_2026-10-06.md` | Knowledge base coverage report | `app/kb/catalog.py`, script | KEEP |
| `kb_phase_b1_2026-10-06.md` | Phase B1 report | `scripts/kb/write_b1_report.py` | KEEP |
| `kb_v2_comparison_2026-10-06.md` | Old vs new search comparison | `scripts/kb/build_records.py`, `compare_kb_v2.py` | KEEP |
| `kb_v2_comparison_2026-10-06_b3.md` | The same, after B3 | `scripts/kb/build_records.py` | KEEP |
| `kb_v2_live_check_2026-10-06.md` | Live chat check | `docs/eval/c8_questions.json` (evaluation data, not edited) | KEEP |
| `kb_v2_live_check_2026-10-07_b7.md` | Live check after B7 | `docs/eval/c8_questions.json` | KEEP |
| `query_hints_eval_2026-10-07.md` | Query hints evaluation | `scripts/kb/eval_query_hints.py` | KEEP |
| `eval/c8_questions.json` | C8 evaluation questions | `test_c8_hybrid.py`, `scripts/kb/eval_c8.py` | KEEP, so `docs/eval/` stays (linked from the index) |
| `eval/c8_report.md` | C8 evaluation report | docs | KEEP (kept with its data) |
| `eval/c8_results_*.json` (6) | C8 result files | `scripts/kb/eval_c8.py` writes here | KEEP |
| `eval/chat_quality/*.json` (9) | Chat quality replay and rewrite results | `scripts/eval_chat_quality.py` | KEEP |

## docs/: moved into the new folders (named only by Markdown files)

| File | What it is | Named by | Decision |
|---|---|---|---|
| `README.md` | Docs index | `README.md` and others | KEEP, rewritten as a full table |
| `architecture.md` | Layers, modules, AI pipeline | docs only | MOVE → `architecture/system-overview.md` |
| `api-reference.md` | Every endpoint | docs only | MOVE → `architecture/api-reference.md` |
| `folder-structure.md` | Folder map (out of date: no `kb/`, `scraping/`) | docs only | MERGE into the README's folder map; original → `archive/folder-structure.md` |
| `TEST_PLAN.md` | Test levels and inventory | docs only | MOVE → `evaluation/test-plan.md` |
| `test_cases_manual.md` | Manual test cases (FYP-2 mid) | none | MOVE → `evaluation/manual-test-cases.md` |
| `development-guide.md` | Day-to-day development | docs only | MOVE → `runbooks/development-guide.md` |
| `deployment.md` | What a deployment needs | docs only | MOVE → `runbooks/deployment.md` |
| `SCRAPING_DEMO_SCRIPT.md` | Scraping dry-run demo (2026-10-07, kb-v2) | none | MOVE → `runbooks/scraping-demo-script.md` |

## docs/: archived (historical)

| File | What it is | Named by | Decision |
|---|---|---|---|
| `fyp2_mid_gap_report.md` | FYP-2 mid gap report | docs only | ARCHIVE |
| `kb_v2_comparison_2026-10-06_b6.md` | Comparison after B6 | docs only | ARCHIVE |
| `kb_v2_comparison_2026-10-07_b7.md` | Comparison after B7 | none | ARCHIVE |
| `retrieval_statute_chunking.md` | Which statutes split into sections (pre-kb-v2) | docs only | ARCHIVE |
| `strict_grounding_comparison_2026-10-06.md` | Strict grounding A/B | docs only | ARCHIVE |
| `scraping_demo.md` | Demo for the old `scraping` branch and worktree | none | ARCHIVE |
| `scraping_merge_checklist.md` | Merge checklist for the old `scraping` branch | none | ARCHIVE |

## docs/reports/: FYP reports and design diagrams

| File | What it is | Named by | Decision |
|---|---|---|---|
| `FYP Final Report.pdf`, `FYP-1-MidReport-S26-057-D-LegalEase.pdf` | Submitted reports | none | KEEP |
| `FYP1-ProposalDocument-S26-057-D-LegalEase (1).pdf` | Proposal (browser download name) | none | KEEP, renamed without " (1)" |
| `ERD.png` | Entity-relationship diagram | `database-schema.md` | KEEP |
| 17 other diagrams (`Activity Diagram.png`, `Algorithm 1.png`, `Algorithm1.png`–`Algorithm5.png`, `Architecture Diagram.png`, `Box and Line Diagram.png`, `Class.pdf`, `DomainModel.png`, `SD *.png` (3), `State Transition Diagram for Case Life Cycle.png`, `Use Case.png`) | Report figures | none (`Algorithm 1` in `auth.py` means the report section) | KEEP (`Algorithm 1.png` and `Algorithm1.png` differ, so they aren't duplicates) |
| `Claude.md` | A prompt for rebuilding the project as MERN/Node/Mongo, which doesn't match this stack | `PROJECT_CONTEXT.md` (archived) | REVIEW → `_to_review/docs/reports/Claude.md` |

## Result (checked 2026-10-08, 02:15)

- **Changes since the tag:** `git diff kb-v2-pre-tidy-2026-10-08` shows only renames and Markdown
  edits. No code, test, script, config or storage file changed.
- **Links:** every relative Markdown link resolves. The only unresolved names are paths to
  git-ignored data (`data/raw`, `data/processed`, `backend/venv`, caches) and history inside
  archived notes. There were more of these before the tidy-up.
- **`scripts/start_demo.ps1`:** unchanged. The paths it uses (`backend/`, `frontend/`,
  `backend/app/main.py`, the venv's Python) all exist.
- **Tests:** 673 of 679 pass.
  - `test_case_fields.py::test_stats_list_upcoming_hearings` fails between midnight and 5 am
    Pakistan time: the test uses the local date and the service uses the UTC date.
  - 5 knowledge base tests in `test_kb_b3.py` and `test_kb_index_v2.py` now return results from
    the real `backend/storage/kb` indexes. Those indexes were rewritten at 01:41–01:43 by a process
    outside this tidy-up. The same tests passed at 00:56 with the same code.
- **Ruff:** `ruff check app` reports 21 findings (E402, B904, SIM102, N806), the same as at the tag,
  because the code is unchanged.
