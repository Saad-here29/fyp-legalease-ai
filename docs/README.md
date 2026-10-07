# Documentation index

The project overview, setup and how to run it are in the root [README](../README.md).

## architecture/

| Doc | Purpose |
|---|---|
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | One page: components, the chat pipeline step by step, data stores, feature flags |
| [system-overview.md](architecture/system-overview.md) | Layers, backend modules, the AI pipeline and cross-cutting concerns in more detail |
| [knowledge_base_spec.md](architecture/knowledge_base_spec.md) | Knowledge base design: section records, indexes, judgments, hybrid search, document reasoning, Colab steps (phases B1–C10) |
| [scraping.md](architecture/scraping.md) | Law-update scraper: sources, staging, quarantine, update log, weekly run |
| [database-schema.md](architecture/database-schema.md) | Tables, case status rules and migrations |
| [api-reference.md](architecture/api-reference.md) | Every endpoint, authentication, the error format and status codes |
| [retrieval_redesign.md](architecture/retrieval_redesign.md) | The section-based retrieval design that the knowledge base grew from |
| [corpus_statute_list.md](architecture/corpus_statute_list.md) | Every document in the original statute corpus |
| [STYLE_GUIDE.md](architecture/STYLE_GUIDE.md) | Design system v1: tokens, type, components (source: `design_reference/`) |
| `diagrams/` | ERD, use case, class, domain, sequence, activity, state and architecture diagrams from the FYP reports |
| [STRUCTURE_REVIEW.md](architecture/STRUCTURE_REVIEW.md) | How the repository compares with the reference layout, and what was moved (2026-10-08) |

## evaluation/

| Doc | Purpose |
|---|---|
| [test-plan.md](evaluation/test-plan.md) | Test levels, strategy and the test inventory |
| [manual-test-cases.md](evaluation/manual-test-cases.md) | Manual (black-box) test cases per feature |
| [c8/c8_report.md](evaluation/c8/c8_report.md) | C8 accuracy pass on the gold, live and unseen question sets. Questions (`c8_questions.json`) and results are in `c8/` |
| `chat_quality/` | Chat quality replay and rewrite results (JSON) |
| [query_hints_eval_2026-10-07.md](evaluation/query_hints_eval_2026-10-07.md) | Query hints: retrieval before and after |
| [kb_v2_comparison_2026-10-06.md](evaluation/kb_v2_comparison_2026-10-06.md) | Original vs new search index, side by side |
| [kb_v2_comparison_2026-10-06_b3.md](evaluation/kb_v2_comparison_2026-10-06_b3.md) | The same comparison after phase B3 |
| [kb_v2_live_check_2026-10-06.md](evaluation/kb_v2_live_check_2026-10-06.md) | Live chat check of the new index |
| [kb_v2_live_check_2026-10-07_b7.md](evaluation/kb_v2_live_check_2026-10-07_b7.md) | Live check after phase B7 |
| [kb_coverage_2026-10-06.md](evaluation/kb_coverage_2026-10-06.md) | Coverage of the Pakistan Code by the knowledge base |
| [kb_phase_b1_2026-10-06.md](evaluation/kb_phase_b1_2026-10-06.md) | Phase B1 report: section records |
| [chat_baseline_2026-10-06.md](evaluation/chat_baseline_2026-10-06.md) | Retrieval baseline on the original index |
| [chat_review_family_law_2026-10-05.md](evaluation/chat_review_family_law_2026-10-05.md) | Family-law chat review |
| [chat_quality_steps_2026-10.md](evaluation/chat_quality_steps_2026-10.md) | Chat quality flags and their measured effect |
| [retrieval_gold_set_draft.md](evaluation/retrieval_gold_set_draft.md) | Draft gold questions for retrieval |
| [ner_training_results.md](evaluation/ner_training_results.md) | Legal NER model: data, training and results |
| [demo_examples.md](evaluation/demo_examples.md) | A real document analysed end to end. The document and the recorded responses are in `demo/` |

## runbooks/

| Doc | Purpose |
|---|---|
| [demo-runbook.md](runbooks/demo-runbook.md) | Starting the demo, the feature flags, safe mode and what to show |
| [demo-brief.md](runbooks/demo-brief.md) | Demo script, talking points and likely questions |
| [scraping-demo-script.md](runbooks/scraping-demo-script.md) | The 90-second scraping dry-run demo |
| [development-guide.md](runbooks/development-guide.md) | Day-to-day development: running, testing, conventions |
| [deployment.md](runbooks/deployment.md) | What a production deployment would need |
| [../data/README.md](../data/README.md) | Corpus sources and how to rebuild them |
| [../scripts/README.md](../scripts/README.md) | Every script, by folder |

## archive/

Historical notes kept for reference. They describe earlier states of the project.

| Doc | Purpose |
|---|---|
| `fyp-reports/` | FYP proposal, mid-term report and final report (PDF) |
| [PROJECT_CONTEXT.md](archive/PROJECT_CONTEXT.md) | Working notes for AI coding sessions, as of 2026-10-06 (before kb-v2) |
| [TIDY_PLAN.md](archive/TIDY_PLAN.md) | The 2026-10-08 docs tidy-up: inventory and decisions |
| [folder-structure.md](archive/folder-structure.md) | The old folder map (replaced by the README's layout) |
| [fyp2_mid_gap_report.md](archive/fyp2_mid_gap_report.md) | FYP-2 mid requirements gap report |
| [kb_v2_comparison_2026-10-06_b6.md](archive/kb_v2_comparison_2026-10-06_b6.md) | Search comparison after phase B6 |
| [kb_v2_comparison_2026-10-07_b7.md](archive/kb_v2_comparison_2026-10-07_b7.md) | Search comparison after phase B7 |
| [retrieval_statute_chunking.md](archive/retrieval_statute_chunking.md) | Which statutes split into sections (before kb-v2) |
| [strict_grounding_comparison_2026-10-06.md](archive/strict_grounding_comparison_2026-10-06.md) | Strict grounding: old vs new answers |
| [scraping_demo.md](archive/scraping_demo.md) | Demo for the old `scraping` branch |
| [scraping_merge_checklist.md](archive/scraping_merge_checklist.md) | Merge checklist for the old `scraping` branch |

Files set aside for the team to decide on are in [`../_to_review/`](../_to_review/README.md).
