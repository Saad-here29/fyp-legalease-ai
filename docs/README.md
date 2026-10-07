# Documentation

## Start here
- [`../README.md`](../README.md): what LegalEase AI is, setup, and how to run it.
- [`../PROJECT_CONTEXT.md`](archive/PROJECT_CONTEXT.md): current status, decisions,
  known gaps and Groq limits.
- [`../DEMO_BRIEF.md`](runbooks/demo-brief.md): demo script and likely questions.

## How the system works
| Doc | Covers |
|---|---|
| [`architecture.md`](architecture.md) | Layers, backend modules, AI pipeline, cross-cutting concerns |
| [`api-reference.md`](api-reference.md) | Every endpoint, auth, error format, status codes |
| [`database-schema.md`](database-schema.md) | The 14 tables, case status rules, migrations |
| [`folder-structure.md`](folder-structure.md) | What each folder holds |
| [`development-guide.md`](development-guide.md) | Running, testing, conventions |
| [`deployment.md`](deployment.md) | What a production deployment needs |
| [`TEST_PLAN.md`](TEST_PLAN.md) | Test levels and the test inventory |

## Design
- [`STYLE_GUIDE.md`](STYLE_GUIDE.md): design system v1 (tokens, type,
  components). The source design is `design_reference/LegalEase AI Design System.pdf`.

## AI and data
| Doc | Covers |
|---|---|
| [`ner_training_results.md`](ner_training_results.md) | Legal NER model: data, training, results |
| [`corpus_statute_list.md`](corpus_statute_list.md) | Every document in the search library |
| [`retrieval_redesign.md`](retrieval_redesign.md) | Section-based retrieval design (approved, not built) |
| [`retrieval_gold_set_draft.md`](retrieval_gold_set_draft.md) | Draft gold questions for evaluating it (awaiting review) |
| [`retrieval_statute_chunking.md`](retrieval_statute_chunking.md) | Which statutes split into sections |
| [`../data/README.md`](../data/README.md) | Corpus sources, rebuilding, known corpus limits |

## Demo material and reports
- [`demo_examples.md`](demo_examples.md) and `demo/`: a real document analysed
  end to end.
- `reports/`: FYP proposal, mid-term and final reports, and design diagrams
  (ERD, use case, sequence and activity diagrams).
