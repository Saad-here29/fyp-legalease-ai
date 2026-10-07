# Scripts

Run from the project root with the backend virtual environment. These
scripts use `requests` and the other packages in
`backend/requirements-dev.txt`.

| Script | What it does |
|---|---|
| `start_demo.ps1` | One command for the demo: frees ports 8000 and 5173, starts the backend and frontend with the four flags on (`-Safe`: off), checks `/health` |
| `setup.ps1` | One-time Windows setup: backend `venv`, `pip install -r requirements-dev.txt`, `npm install`, and `.env` files copied from the examples |

**`kb/`: building and evaluating the knowledge base**

| Script | What it does |
|---|---|
| `kb/clean_statute_corpus.py` | Cleans and merges the two raw statute sources in `data/raw/statutes/` into `data/processed/statutes/legal_statutes_corpus.json`, and cleans the 78-question lawyer QA set. Step 1 of rebuilding the original search index (`ai-services/README.md`) |
| `kb/build_category_map.py` | The Pakistan Code category map |
| `kb/build_records.py`, `kb/build_shariat_act.py` | Section records for the 35 core laws |
| `kb/build_records_all.py` | Section records for every other law in the statute corpus |
| `kb/build_index_v2.py`, `kb/build_index_v2_all.py` | The core-laws and all-laws FAISS indexes (incremental) |
| `kb/inventory_judgments.py`, `kb/build_index_judgments.py` | Judgment records and the judgments index |
| `kb/build_index_scraped.py` | The scraped laws and judgments indexes |
| `kb/export_for_colab.py`, `kb/colab_embed.py` | Export the chunks still to embed, and embed them on a Colab GPU |
| `kb/compare_kb_v2.py`, `kb/compare_user_pdfs.py` | Old vs new retrieval comparison, and user-supplied PDFs vs the corpus |
| `kb/eval_c8.py`, `kb/eval_query_hints.py`, `kb/measure_prompt_tokens.py` | Offline retrieval evaluations and prompt-size measurement (no model calls) |
| `kb/eval_chat_quality.py` | Offline evaluation of the chat quality steps |
| `kb/eval_research_retrieval.py` | Sends the 78 lawyer questions to `/research/search` on a **running** backend and reports how many top results pass the similarity threshold. Writes `data/processed/qa_eval/retrieval_eval_results.json` |
| `kb/write_b1_report.py`, `kb/write_coverage_doc.py` | Write the B1 and coverage reports in `docs/evaluation/` |

**`scraping/`: law updates**

| Script | What it does |
|---|---|
| `scraping/scrape_laws.py` | Scrapes the law sources, stages new or changed laws, writes the update log |
| `scraping/run_weekly.py`, `scraping/register_weekly_task.ps1` | The weekly update (scrape, validate, stage, embed, log), and registering it as a Windows scheduled task (not registered) |
| `scraping/sources.json`, `scraping/source_checks.json` | The sources and the results of checking them |
| `scraping/check_sources.py`, `scraping/count_listing.py`, `scraping/list_staged.py` | Check candidate sources, count a listing, list staged documents |

## `eval_research_retrieval.py`

```powershell
backend\venv\Scripts\python scripts\kb\eval_research_retrieval.py              # all 78; writes the results file
backend\venv\Scripts\python scripts\kb\eval_research_retrieval.py --limit 5    # quick check; writes nothing
backend\venv\Scripts\python scripts\kb\eval_research_retrieval.py --out my.json
```

- **Authentication:**
  - With `LEGALEASE_TOKEN` set, it uses that access token.
  - Otherwise it creates a throwaway `eval.<time>@example.com` student
    account, reading the signup code from the database, and deletes the
    account and its rows when it finishes, even after an error.
- **Settings:**
  - `LEGALEASE_API` overrides the API URL (default
    `http://127.0.0.1:8000/api/v1`);
  - the pass threshold is the app's `RAG_SIMILARITY_THRESHOLD`.
- **Cost:** every question costs one Groq call (the query rewrite), about
  400 tokens, so a full run is about 31k.

The planned replacement records the query rewrites once and replays them
offline against old and new indexes; see `docs/retrieval_redesign.md`,
section 7.
