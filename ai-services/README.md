# AI services

Offline tools that produce the two large model files the backend loads.
Neither output is in git.

| Tool | Produces | Used by |
|---|---|---|
| `corpus_builder/build_corpus.py` | `backend/storage/faiss/legal_corpus.faiss` + `legal_corpus_meta.json` (the statute search index) | Chat and Legal Research |
| `ner_training/ner_training_colab.ipynb` | The fine-tuned legal NER model, copied to `backend/storage/models/legal_ner/` | Document analysis (parties, dates, references) |

## Rebuilding the search index

1. **Clean the data** (needs the raw data under `data/raw/`; see
   [`data/README.md`](../data/README.md)). From the project root:
   ```powershell
   backend\venv\Scripts\python scripts\clean_statute_corpus.py
   ```
2. **Build the index:**
   ```powershell
   backend\venv\Scripts\python ai-services\corpus_builder\build_corpus.py
   ```
   - It chunks every document into 800-character passages (100 overlap).
   - It embeds them with `paraphrase-multilingual-MiniLM-L12-v2` and
     writes a FAISS `IndexFlatIP`.
   - It's resumable, with checkpoints in
     `backend/storage/faiss/_checkpoint/`.
   - On a laptop CPU it takes hours (about 10 passages a second). Embedding
     on a Colab GPU takes minutes; the Colab plan is in
     [`docs/retrieval_redesign.md`](../docs/retrieval_redesign.md).
3. **Restart the backend**, which loads the index on first use.

The current index has 53,739 passages from about 900 statute documents. Its
known limits, and the section-based redesign that addresses them, are in
`data/README.md` and `docs/retrieval_redesign.md`.

## Retraining the NER model

Open `ner_training/ner_training_colab.ipynb` in Google Colab with a GPU
runtime. It fine-tunes DistilBERT on the Lahore High Court and Supreme Court
judgment annotations. The data, settings and results are in
[`docs/ner_training_results.md`](../docs/ner_training_results.md):
entity-level F1 is 0.811 on validation and 0.784 on the held-out test set.
Copy the saved model folder to `backend/storage/models/legal_ner/`.
