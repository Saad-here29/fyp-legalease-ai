# Scripts

Run from the project root with the backend virtual environment. These
scripts use `requests` and the other packages in
`backend/requirements-dev.txt`.

| Script | What it does |
|---|---|
| `clean_statute_corpus.py` | Cleans and merges the two raw statute sources in `data/raw/statutes/` into `data/processed/statutes/legal_statutes_corpus.json`, and cleans the 78-question lawyer QA set. Step 1 of rebuilding the search index (`ai-services/README.md`) |
| `eval_research_retrieval.py` | Sends the 78 lawyer questions to `/research/search` on a **running** backend and reports how many top results pass the similarity threshold. Writes `data/processed/qa_eval/retrieval_eval_results.json` |
| `setup.ps1` | One-time Windows setup: backend `venv`, `pip install -r requirements-dev.txt`, `npm install`, and `.env` files copied from the examples |

## `eval_research_retrieval.py`

```powershell
backend\venv\Scripts\python scripts\eval_research_retrieval.py              # all 78; writes the results file
backend\venv\Scripts\python scripts\eval_research_retrieval.py --limit 5    # quick check; writes nothing
backend\venv\Scripts\python scripts\eval_research_retrieval.py --out my.json
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
