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

## Future work — statute corpus and retrieval

Known limitations of the statute corpus, found by measurement on
2026-09-26, to address the next time the corpus is rebuilt.

1. **Chunk by section, not by 800 characters (the proper fix).** The
   builder (`ai-services/corpus_builder/build_corpus.py`) cuts fixed
   800-character windows with 100-character overlap that ignore section
   boundaries. A section's text is therefore split across chunks that also
   carry the neighbouring sections, and the embedding barely registers a
   section number. Measured on the Muslim Family Laws Ordinance: for "legal
   restrictions on polygamy" the best chunk holding Section 6 ranked **42nd**
   (similarity 0.609, below the 0.65 cut-off) and for "What is Section 6 of
   MFLO?" **534th**, while the statute's table-of-contents chunk ranked 3rd.
   Chunk [827], for example, is mostly the end of Section 5 with Section 6's
   heading near its end. **Fix:** split each statute at its section headings
   ("Section 6 — Polygamy" in CSV-derived text, "6. Polygamy.—" in
   PDF-derived text) and prefix every chunk with the statute name and the
   section heading, splitting only sections that are genuinely long. Needs a
   re-chunk and a full FAISS rebuild (the last rebuild took hours on the dev
   machine), then a re-run of the retrieval evaluation.
2. **Table-of-contents chunks crowd the top 5.** 1,445 chunks (2.7%, in 745
   of the 900 documents) are contents lists — statute name plus every
   section title — and take ~8% of top-5 slots; one reaches the top 5 for
   about a third of real eval questions. Mitigated today by the TOC-guided
   section lookup (`backend/app/ai/section_lookup.py`, used by the chat),
   which follows a retrieved contents list to the sections the question
   names. It only helps when a contents chunk makes the top 5, so it
   becomes unnecessary once (1) is done.
3. **Some statutes are indexed twice**, once under an OCR-damaged title
   (e.g. "Muslim Family Laws Ordinance, 1961" and "THE MUSLIM FAMILY LAWS
   ORDINAN CE, 1961", from the CSV and PDF sources). This doubles their
   share of results and shows OCR titles to users. De-duplicate at the
   cleaning step (`scripts/clean_statute_corpus.py`), keeping the cleaner
   copy, and repair OCR-split words in titles.
4. **No year or court metadata.** Statute records carry only source, type,
   chunk id and text, so year/court search filters can't work (they were
   removed from the Research page). Adding each statute's enactment year
   would make a year filter meaningful.

### Investigated and rejected (2026-09-26)

Tried while chasing the TOC / split-section problem above. Recorded with
the evidence so they aren't re-investigated from scratch. Statute and
section judgements below are the developer's assessment, not a lawyer's.

**Earlier options, simulated on "restrictions on polygamy", "What is
Section 6 of MFLO?" and "procedure for talaq under Section 7" — none put
the section text in front of the model (0 of 3 each):**

- *Demote or drop table-of-contents chunks* — other statutes scoring above
  0.65 simply took the freed slot.
- *Take more chunks from the statute whose contents chunk was retrieved* —
  it added that statute's Section 5 and definitions chunks, not 6 or 7.
- *Fuse a BM25 keyword ranking with the embedding search (reciprocal rank
  fusion)* — BM25 alone ranked the Section 7 text 3rd, but fusion still
  left it out of the top 5.

**Change 1 — a query-rewrite prompt that names the governing statute.**
The rewrite (`AIClient.rewrite_search_query`) was told to include the
governing statute's name ("and the section number only if you are sure").

- *Why it was tried:* the orphaned-grandchild question ("My father died
  before my grandfather…") is refused because its rewrite doesn't name the
  Muslim Family Laws Ordinance; with the statute named, the Section 4 chunk
  moves from rank 57 to rank 3 (0.702) and the question is answered.
- *Eval (48 of the 78 eval questions with clean results; the rest were
  lost to the Groq daily token limit):* answerable (≥1 passage ≥ 0.65) rose
  from 29 (60%) to 38 (79%), mean top-1 similarity 0.648 → 0.675; 11
  questions went refused → answerable, 2 answerable → refused. Of the 11,
  about 7 were genuine gains (defamation → PPC §499/500; fraud → PPC §415
  where the current prompt wrote the *Indian* "IPC"; sexual assault → PPC
  §376; easement → found the Easements Act; land documents → Registration
  Act; khula revocation; the orphaned grandchild).
- *Why rejected — false confidence:*
  - **Foreign questions stopped being refused.** A Nigerian company-
    registration question ("CAC") and a Thailand contract question — both
    refused before — became answerable from Pakistani statutes.
  - **It names statutes that don't exist.** It named a statute in 42 of 48
    rewrites (current prompt: 16), with 14 names not in the library; about
    10 don't exist as named: "Guardianship Act 1925", "Guardianship and
    Wills Act 1890", "Employment Ordinance 1961", "Khyber Pakhtunkhwa
    Companies Act 2017", "Prescription Act 1900", "Punjab Motor Vehicles
    Ordinance 1914", "Registration of Births and Deaths Act 1961", "West
    Pakistan Rent Restriction Ordinance 1979", "West Pakistan Landlord and
    Tenant Act 1920", "West Pakistan Premises Rent Control Ordinance 1961".
    (The current prompt does this too — "Guardianship Act 1991", "Tenancy
    Act 1965" — but about three times less often.)
  - **It invents section numbers:** "Companies Act 2017 (Section 2)",
    "Transfer of Property Act 1882 Section 62" (a mortgage section) for an
    easement question.
  - Its longer outputs hit the 150-token rewrite cap twice.
  - A wrong name never reaches the user directly (the answer is still
    grounded and citation-checked); the harm is turning honest refusals
    into confident answers from the wrong law.
- *To revisit:* forbid section numbers in the rewrite, forbid adding a
  Pakistani statute when the question concerns another country, raise the
  rewrite cap to ~200 tokens, then re-run the full 78-question comparison
  (≈80k Groq tokens — plan it around the daily limit) and re-check every
  newly answerable question by hand.

**Change 2 — look up a statute's contents list directly whenever the
rewrite names that statute** (instead of only when its contents chunk
happens to reach the top 5).

- *Topic questions, replayed on 16 real rewrites:* section text reached
  the model 8/16 today vs 10/16 with the change. Gained: "How long does a
  talaq notice take to become effective?" (2/2, via Section 7's 90-day
  rule). Still failing: "Can my husband marry a second wife without my
  permission?" (0/2 — the question never says "polygamy").
- *Why rejected — wrong sections:* on the eval set it fired on 24 rewrites
  and about 10 fetched irrelevant or wrong sections, which would be put in
  front of the model:
  - PPC §298C (Qadiani group) and §301/302 for a **fraud** question;
  - PPC §338D (confirmation of death sentence) for a sentencing question;
  - PPC §319 (punishment for qatl-i-khata) and §327 for "What is the
    punishment for stealing a car?" — almost every PPC title contains
    "Punishment";
  - Sale of Goods Act §6 for a burglary; Industrial Relations Act §11–12
    for unpaid wages; Companies Act "§2 Definitions" from a section number
    the rewrite invented; MFLO §5 (marriage registration) for several
    family questions.
  About 9 triggers were relevant (Guardians and Wards Act §25 for custody,
  7 times; MFLO §8 for khula/dissolution, 3 times).
- *Causes:* generic words in section titles ("punishment", "registration",
  "marriage", "goods"); section numbers invented by the rewrite (the live
  lookup now takes numbers only from the user's question); and the PPC's
  contents list spans many chunks whose entries parse badly ("319.
  Punishment for q atlikhata 320").
- *Verdict:* not worth tightening further — section-based chunking (1)
  removes the need for any contents-list lookup.
