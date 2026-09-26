# Legal corpus data

Nothing under `data/` is committed to git — `data/raw/` and
`data/processed/` are both gitignored (see root `.gitignore`). Everything
here is regenerable from the two scripts below; only the scripts themselves
are tracked.

## Where the raw data came from

`data/raw/` holds the source material the corpus is built from:

- `statutes/Datatset For FAISS.csv` — a section-level table (Book / Chapter /
  Section / Heading / Definition) covering the Pakistan Penal Code, Code of
  Criminal Procedure 1898, Qanun-e-Shahadat Order 1984, Transfer of Property
  Act, Limitation Act 1908, Muslim Family Laws Ordinance 1961, and the
  Police Order 2002.
- `statutes/pakistan_code_pdf_data.json` — OCR/text-extracted Pakistan Code
  statute PDFs (one entry per document), covering a much broader set of
  Acts and Ordinances beyond the six above.
- `qa_eval/Legal_QA_dataset_From_lawyers.csv` — real lawyer-authored
  Query/Response pairs, used as a realistic evaluation set for retrieval
  quality (see `data/processed/qa_eval/retrieval_eval_results.json` for the
  latest run against it).
- `qa_eval/combined_legal_dataset.csv` — a separate, larger reference/eval
  set. Kept distinct from the lawyer QA set, never merged into it.
- `ner_courtroom/{LHC,SCP}/` — Lahore High Court / Supreme Court of Pakistan
  judgment text for a separate NER training task, not part of the statute
  corpus pipeline below. Known limitations of this data, to address in any
  future retraining (details and evidence in
  [`docs/ner_training_results.md`](../docs/ner_training_results.md#future-work--retraining-checklist)):
  - **Case-number capitalisation gap.** SCP writes a judgment's own case
    number in capitals ("CIVIL APPEAL NO.1074 OF 2009", labelled `caseno`
    333 times); mixed-case "Criminal Petition No. …" appears only 9 times
    and never as `caseno`. The trained model therefore mislabels a
    mixed-case heading's own number (seen on a real 2026 order). A
    post-processing rule currently compensates; the lasting fix is
    mixed-case / lower-case augmentation of the training sentences.
  - **Same labels spelled differently by source:** LHC `caseNo.` /
    `refCase` / `refCourt` vs SCP `caseno` / `refcase` / `refcourt`.
  - **Classes too small to learn:** `FIRno` (12 training examples),
    `mutationNo.` (5), `witnessName` (18).

If you're setting this up fresh and don't have `data/raw/` populated, ask
whoever last had it (it's not published anywhere else yet) — everything
past this point assumes it's already in place.

## Regenerating the processed corpus + FAISS index

Two commands, run from the project root with the backend venv active
(`ai-services/corpus_builder/build_corpus.py` needs `faiss`,
`sentence-transformers`, and `numpy` from `backend/venv`):

```bash
# 1. Clean + merge the raw statute sources, clean the QA eval set.
#    Writes data/processed/statutes/legal_statutes_corpus.json (901 docs)
#    and data/processed/qa_eval/Legal_QA_dataset_From_lawyers_clean.csv.
python scripts/clean_statute_corpus.py

# 2. Chunk + embed the merged corpus and build the FAISS index.
#    Writes backend/storage/faiss/legal_corpus.faiss + legal_corpus_meta.json.
python ai-services/corpus_builder/build_corpus.py
```

Step 2 is resumable — it checkpoints embedded batches under
`backend/storage/faiss/_checkpoint/` as it goes, so if it's interrupted
partway through, just re-run the same command and it picks up where it
left off rather than starting over.

Full provenance/decisions made while cleaning the raw statute data (which
rows got relabeled, which got dropped, title-extraction method, etc.) are
documented in `data/processed/statutes/README.md` once step 1 has run.
