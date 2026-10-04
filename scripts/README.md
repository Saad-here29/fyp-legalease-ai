# Scripts

Run from the project root with the backend virtual environment. These
scripts use `requests` and the other packages in
`backend/requirements-dev.txt`.

| Script | What it does |
|---|---|
| `clean_statute_corpus.py` | Cleans and merges the two raw statute sources in `data/raw/statutes/` into `data/processed/statutes/legal_statutes_corpus.json`, and cleans the 78-question lawyer QA set. Step 1 of rebuilding the search index (`ai-services/README.md`) |
| `eval_research_retrieval.py` | Sends the 78 lawyer questions to `/research/search` on a **running** backend and reports how many top results pass the similarity threshold. Writes `data/processed/qa_eval/retrieval_eval_results.json` |
| `setup.ps1` | One-time Windows setup: backend `venv`, `pip install -r requirements-dev.txt`, `npm install`, and `.env` files copied from the examples |

## Known issues with `eval_research_retrieval.py`

- **Model use:** every question costs one Groq call (the query rewrite),
  about 400 tokens.
- **Stale threshold:** it uses `THRESHOLD = 0.7`, but the app uses 0.65.
- **Brittle self-signup:** it signs in as `researcheval@example.com`. If that
  account doesn't exist, it signs up and looks for the code in a hardcoded
  old log path (`backend_groq2.log`), which no longer exists. Create the
  account by hand first, or change the path.

The planned replacement records the query rewrites once and replays them
offline against old and new indexes; see `docs/retrieval_redesign.md`,
section 7.
