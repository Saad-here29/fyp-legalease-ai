# Documentation index

The project overview, setup and how to run it are in the root [README](../README.md).

Some documents stay at the top of `docs/` because code, tests or scripts name
them by path (see [TIDY_PLAN.md](archive/TIDY_PLAN.md)). They are listed here under
the section they belong to.

## Architecture and design

| Doc | Purpose |
|---|---|
| [architecture/system-overview.md](architecture/system-overview.md) | Layers, backend modules, the AI pipeline and cross-cutting concerns |
| [architecture/api-reference.md](architecture/api-reference.md) | Every endpoint, authentication, the error format and status codes |
| [database-schema.md](architecture/database-schema.md) | Tables, case status rules and migrations |
| [knowledge_base_spec.md](architecture/knowledge_base_spec.md) | Knowledge base design: section records, indexes, judgments, hybrid search, document reasoning (phases B1–C10) |
| [scraping.md](architecture/scraping.md) | Law-update scraper: sources, staging, quarantine, update log, weekly run |
| [retrieval_redesign.md](architecture/retrieval_redesign.md) | The section-based retrieval design that the knowledge base grew from |
| [ner_training_results.md](evaluation/ner_training_results.md) | Legal NER model: data, training and results |
| [corpus_statute_list.md](architecture/corpus_statute_list.md) | Every document in the original statute corpus |
| [STYLE_GUIDE.md](architecture/STYLE_GUIDE.md) | Design system v1: tokens, type, components (source: `design_reference/LegalEase AI Design System.pdf`) |

## Runbooks

| Doc | Purpose |
|---|---|
| [DEMO_RUNBOOK.md](runbooks/demo-runbook.md) | Starting the demo, the feature flags, safe mode and what to show |
| [runbooks/demo-brief.md](runbooks/demo-brief.md) | Demo script, talking points and likely questions |
| [runbooks/scraping-demo-script.md](runbooks/scraping-demo-script.md) | The 90-second scraping dry-run demo |
| [runbooks/development-guide.md](runbooks/development-guide.md) | Day-to-day development: running, testing, conventions |
| [runbooks/deployment.md](runbooks/deployment.md) | What a production deployment would need |
| [../data/README.md](../data/README.md) | Corpus sources and how to rebuild them |

The Colab embedding steps are in [knowledge_base_spec.md](architecture/knowledge_base_spec.md) (b7).

## Evaluation and testing

| Doc | Purpose |
|---|---|
| [evaluation/test-plan.md](evaluation/test-plan.md) | Test levels, strategy and the test inventory |
| [evaluation/manual-test-cases.md](evaluation/manual-test-cases.md) | Manual (black-box) test cases per feature |
| [eval/c8_report.md](evaluation/c8/c8_report.md) | C8 accuracy pass: gold, live and unseen question sets. Questions and results are in `eval/` |
| `eval/chat_quality/` | Chat quality replay and rewrite results (JSON) |
| [query_hints_eval_2026-10-07.md](evaluation/query_hints_eval_2026-10-07.md) | Query hints: retrieval before and after |
| [kb_v2_comparison_2026-10-06.md](evaluation/kb_v2_comparison_2026-10-06.md) | Old vs new search index, side by side |
| [kb_v2_comparison_2026-10-06_b3.md](evaluation/kb_v2_comparison_2026-10-06_b3.md) | The same comparison after phase B3 |
| [kb_v2_live_check_2026-10-06.md](evaluation/kb_v2_live_check_2026-10-06.md) | Live chat check of the new index |
| [kb_v2_live_check_2026-10-07_b7.md](evaluation/kb_v2_live_check_2026-10-07_b7.md) | Live check after phase B7 |
| [kb_coverage_2026-10-06.md](evaluation/kb_coverage_2026-10-06.md) | Coverage of the Pakistan Code by the knowledge base |
| [kb_phase_b1_2026-10-06.md](evaluation/kb_phase_b1_2026-10-06.md) | Phase B1 report: section records |
| [chat_baseline_2026-10-06.md](evaluation/chat_baseline_2026-10-06.md) | Retrieval baseline on the original index |
| [chat_review_family_law_2026-10-05.md](evaluation/chat_review_family_law_2026-10-05.md) | Family-law chat review |
| [chat_quality_steps_2026-10.md](evaluation/chat_quality_steps_2026-10.md) | Chat quality flags and their measured effect |
| [retrieval_gold_set_draft.md](evaluation/retrieval_gold_set_draft.md) | Draft gold questions for retrieval |
| [demo_examples.md](evaluation/demo_examples.md) | A real document analysed end to end; the files are in `demo/` |

## Reports

`reports/` holds the FYP proposal, the mid-term and final reports, and the
design diagrams (ERD, use case, class, sequence, activity, state, architecture).

## Archive

Historical notes kept for reference. They describe earlier states of the project.

| Doc | Purpose |
|---|---|
| [archive/PROJECT_CONTEXT.md](archive/PROJECT_CONTEXT.md) | Working notes for AI coding sessions, as of 2026-10-06 (before kb-v2) |
| [archive/folder-structure.md](archive/folder-structure.md) | The old folder map (replaced by the README's layout) |
| [archive/fyp2_mid_gap_report.md](archive/fyp2_mid_gap_report.md) | FYP-2 mid requirements gap report |
| [archive/kb_v2_comparison_2026-10-06_b6.md](archive/kb_v2_comparison_2026-10-06_b6.md) | Search comparison after phase B6 |
| [archive/kb_v2_comparison_2026-10-07_b7.md](archive/kb_v2_comparison_2026-10-07_b7.md) | Search comparison after phase B7 |
| [archive/retrieval_statute_chunking.md](archive/retrieval_statute_chunking.md) | Which statutes split into sections (before kb-v2) |
| [archive/strict_grounding_comparison_2026-10-06.md](archive/strict_grounding_comparison_2026-10-06.md) | Strict grounding: old vs new answers |
| [archive/scraping_demo.md](archive/scraping_demo.md) | Demo for the old `scraping` branch |
| [archive/scraping_merge_checklist.md](archive/scraping_merge_checklist.md) | Merge checklist for the old `scraping` branch |

## This tidy-up

[TIDY_PLAN.md](archive/TIDY_PLAN.md) lists every document, who names it and what was
decided for it. Files set aside for review are in `../_to_review/`.
