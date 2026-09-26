# Legal NER model — training results

Named Entity Recognition model for Pakistani court judgments: it tags case
numbers, courts, parties, dates, amounts and cited cases in judgment text.
Trained on Google Colab (GPU) on 2026-09-26; results independently
re-scored on the project machine the same day.

- **Training notebook:** [`ai-services/ner_training/ner_training_colab.ipynb`](../ai-services/ner_training/ner_training_colab.ipynb)
- **Training data:** `data/raw/ner_courtroom_data.zip` (LHC + SCP CoNLL files; gitignored, see [`data/README.md`](../data/README.md))
- **Trained model:** `backend/storage/models/legal_ner/` (gitignored — 539 MB; see [Model files](#model-files))
- **Status:** trained, validated, and **integrated into Document Analysis** (`POST /documents/{id}/analyze`) — see [Backend integration](#backend-integration).

## Headline results

| Evaluation set | Sentences | Precision | Recall | **F1** | Accuracy | Macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| Combined LHC + SCP validation | 5,089 | 0.779 | 0.846 | **0.811** | 0.982 | 0.602 |
| SCP test (held out) | 4,402 | 0.736 | 0.838 | **0.784** | 0.980 | 0.522 |

- **F1 / precision / recall** are entity-level (`seqeval`): an entity counts
  as correct only if its full span *and* its type match. This is the strict
  standard NER measure.
- **Accuracy** is token-level and includes the `O` ("not an entity") tokens,
  which are the vast majority — that is why it is 0.98 while F1 is 0.81.
  F1 is the number to quote.
- **Macro F1** is the plain average across entity types; the headline F1 is
  weighted by how many entities each type has, so the frequent, strong types
  dominate it.
- **Which number is the honest one:** the validation set was used during
  training to pick the best epoch, so its score is slightly optimistic.
  The SCP test set was never seen during training — **0.784 is the fairest
  single measure of real performance.** LHC ships no test split, so there is
  no held-out LHC score.

The validation numbers above are the ones reported from the Colab run; they
were **reproduced exactly** (to 3 decimal places, every entity type) by
re-running the evaluation locally against the downloaded model.

## Per-entity results

| Entity | What it tags | Val F1 | Test F1 | Train examples | Val / test examples |
|---|---|---:|---:|---:|---:|
| `date` | Dates | **0.976** | **0.953** | 3,383 | 780 / 642 |
| `money` | Monetary amounts | **0.951** | **0.884** | 405 | 89 / 106 |
| `Approved` | "Approved for reporting" marker | **0.931** | **0.967** | 109 | 27 / 30 |
| `caseno` | Case number (SCP style) | **0.890** | **0.812** | 1,063 | 197 / 263 |
| `per` | Person names | **0.885** | **0.854** | 4,256 | 974 / 1,020 |
| `refcase` | Cited case (SCP style) | 0.803 | 0.774 | 1,640 | 451 / 463 |
| `org` | Organisations | 0.786 | 0.714 | 2,259 | 1,048 / 372 |
| `ref` | Statutory references | 0.761 | 0.784 | 3,541 | 993 / 835 |
| `appealcourt` | Court appealed from | 0.757 | 0.643 | 321 | 82 / 82 |
| `loc` | Locations | 0.722 | 0.626 | 1,597 | 374 / 269 |
| `appealcaseno` | Case number appealed from | 0.687 | 0.632 | 501 | 135 / 149 |
| `caseNo.` | Case number (LHC style) | 0.486 | — | 127 | 20 / 0 |
| `resp` | Respondent | 0.481 | 0.373 | 347 | 56 / 86 |
| `refcourt` | Cited court (SCP style) | 0.462 | 0.381 | 212 | 59 / 63 |
| `refCourt` | Cited court (LHC style) | 0.432 | — | 441 | 34 / 0 |
| `refCase` | Cited case (LHC style) | 0.378 | — | 217 | 26 / 0 |
| `Misc.name` | Other names (LHC) | 0.056 | — | 270 | 28 / 0 |
| `FIRno` | FIR number | 0.000 | 0.000 | 12 | 5 / 6 |
| `mutationNo.` | Land mutation number | 0.000 | — | 5 | 1 / 0 |
| `witnessName` | Witness name | not scored | not scored | 18 | 0 / 0 |

"Train examples" counts entity occurrences across LHC + SCP training files.
"—" means the type does not occur in that evaluation set.

## Why some entity types are weak

There are three different causes, and they need different fixes.

**1. Genuinely too few examples** — `FIRno` (12 training examples),
`mutationNo.` (5) and `witnessName` (18). A model cannot learn a category
from a handful of examples. Their evaluation scores are also unreliable in
either direction: `FIRno` is scored on 5–6 instances and `mutationNo.` on a
single one. `witnessName` never appears in any evaluation set, so it is
never scored at all.

**2. The same concept is labelled two different ways.** The two sources
were annotated with different spellings of the same labels:

| Concept | LHC label | SCP label |
|---|---|---|
| Case number | `caseNo.` | `caseno` |
| Cited case | `refCase` | `refcase` |
| Cited court | `refCourt` | `refcourt` |

Because label names are case-sensitive, the model treats each pair as two
unrelated classes and has to guess which dataset's convention a sentence
follows. This — not a shortage of data — is the main reason `refCourt` is
weak: it has 441 training examples. It also shows up on the SCP test set as
pure false positives: the model predicts the LHC-only labels (`caseNo.`,
`refCase`, `refCourt`, `Misc.name`) on SCP text where they never occur,
which is part of why test precision (0.736) is lower than validation.

**3. Hard or inconsistently defined categories.** `Misc.name` (0.056)
has 270 training examples, so its low score is not about quantity — it is a
catch-all for names that are not a person, organisation or court, which
gives the model no consistent pattern to learn. `resp` (respondent, 0.48 /
0.37) and the cited-court types overlap heavily with `per`, `org` and court
names, so the model often gets the span right but the type wrong.

**Likely fix for a retrain:** merge each duplicate pair into one label
(e.g. `refCourt` + `refcourt` → `refcourt`) before training. This is a
data-preparation change in the notebook's label-loading step; it would give
those classes 300–650 training examples each under one name and remove the
cross-dataset false positives. `Misc.name`, `mutationNo.` and
`witnessName` could reasonably be dropped (mapped to `O`) rather than
learned badly.

## Training setup

| Setting | Value |
|---|---|
| Base model | `distilbert-base-multilingual-cased` (6 layers, 768 hidden, 134.8M parameters) |
| Task head | Token classification, 41 labels (`O` + B-/I- for 20 entity types) |
| Training data | LHC train (3,599 sentences) + SCP train (17,088 sentences), combined |
| Validation data | LHC valid (416) + SCP valid (4,673), combined |
| Test data | SCP test (4,402) — LHC has no test split |
| Epochs / learning rate | 3 / 2e-5, weight decay 0.01 |
| Batch size | 16 |
| Max sequence length | 256 subword tokens (longer sentences truncated) |
| Model selection | Best epoch by validation entity-level F1 |
| Labelling | Label on the first subword of each word; other subwords ignored |
| Metric | `seqeval` entity-level precision / recall / F1 |
| Framework | Hugging Face `transformers` 5.16.1 (Colab) |

A handful of malformed lines in the source files (1–2 per file, e.g. two
rows run together) are skipped rather than guessed at.

## Model files

The Colab download `ner_model_output.zip` (500,740,367 bytes) extracts to six
files; the backend loads them from `backend/storage/models/legal_ner/`
(`NER_MODEL_PATH`):

| File | Size | Contents |
|---|---:|---|
| `model.safetensors` | 539,074,796 B | Weights — 102 tensors, float32, classifier head `[41 × 768]` |
| `config.json` | 2,424 B | `DistilBertForTokenClassification` config with the 41-label `id2label` map |
| `label_list.json` | 599 B | The 41 labels, in id order — identical to `config.json`'s map |
| `tokenizer.json` | 2,919,460 B | Fast tokenizer (119,547-token multilingual vocabulary) |
| `tokenizer_config.json` | 352 B | Tokenizer settings (cased, max length 512) |
| `training_args.bin` | 5,201 B | Hugging Face training arguments (not needed for inference) |

The model directory is gitignored (the weights exceed GitHub's 100 MB file
limit). It is reproducible by re-running the notebook; keep a copy of the
zip outside the repo (e.g. Google Drive) so it doesn't have to be retrained.

Verified on the project machine: the files load with the backend's installed
`transformers` 4.57.6 / `torch` 2.14 (CPU) and produce correct predictions,
e.g. on an SCP test sentence:

> CIVIL APPEAL NO.1074 OF 2009 (Against the judgment dated 20.3.2009 of the
> Lahore High Court, Lahore passed in W.P.No. 11983/2005) …

→ `caseno` "CIVIL APPEAL NO. 1074 OF 2009" (0.97), `date` "20.3.2009" (0.91),
`appealcourt` "Lahore High Court, Lahore" (0.96), `appealcaseno`
"W.P.No. 11983/2005" (0.96).

## Backend integration

Built 2026-09-26 into `POST /documents/{id}/analyze`.

**Code:** `backend/app/ai/ner.py` (loading, chunking, tagging, clean-up),
`backend/app/ai/summary_sections.py` (clauses/risks from the LLM summary),
`backend/app/api/v1/documents.py` (endpoint). Config: `NER_MODEL_PATH`
(default `./storage/models/legal_ner`), `NER_ENABLED` (default `true`).
Migration `c41e7d2b9a10` adds `document_analysis.extracted_entities` (JSONB).

**How it runs**

- **Loading.** The app's startup starts a background thread that loads the
  model (the server answers requests immediately; the model is ready ~18 s
  after startup, mostly the first `transformers` import). An analyze request
  arriving earlier waits for it. If the weights folder is missing or
  `NER_ENABLED=false`, analysis still returns the LLM summary with
  `ner_available: false`.
- **Tokenizer fix.** `model_input_names = ["input_ids", "attention_mask"]` —
  the transformers-5 tokenizer otherwise sends `token_type_ids`, which
  DistilBERT rejects.
- **Word splitting matches the training data.** Text is split on whitespace
  with punctuation at word edges split off (`W.P.No.` → `W.P.No` `.`) and
  internal punctuation kept (`30.7.1983`, `NO.1074`). Each word takes the
  label of its first subword, then B-/I- tags are joined into entities. (The
  Hugging Face pipeline's grouping was tried first and replaced: it splits
  words at every dot, so `30.7.1983` came back as two dates. Switching
  raised entity precision on the live judgment test from 0.780 to 0.843 and
  recall from 0.845 to 0.893.)
- **Long documents.** The first 30,000 characters are split into sentences
  and packed into chunks of ≤ 200 subword tokens (oversized sentences are
  split on word boundaries); every entity keeps its offset in the original
  text, so the returned text is exactly as written in the document.
- **Clean-up.** Duplicate LHC/SCP labels merged (`caseNo.`→`caseno`,
  `refCase`→`refcase`, `refCourt`→`refcourt`); `Misc.name`, `FIRno`,
  `mutationNo.` and `witnessName` dropped; predictions below 0.5 confidence
  dropped; repeats de-duplicated with a mention count.
- **Two correction rules** (added 2026-09-26 after the real-document review
  in [demo_examples.md](demo_examples.md#iteration--errors-found--investigated--fixed)):
  a person entity that crosses a line break is trimmed of a 2–3 letter
  all-caps abbreviation on either side (`KP⏎Tahir Khan` → `Tahir Khan`),
  and a case number in the document's heading is labelled as the
  document's own case (`caseno`). The second rule corrects a training-data
  bias: SCP only ever writes a judgment's own number in capitals.
- **In the request.** NER (CPU) runs in a worker thread while the LLM summary
  call (network) is in flight, with no database connection open during
  either.

**Response fields**

| Field | Source |
|---|---|
| `parties` | NER `per` + `org` + `resp`, most-mentioned first |
| `dates` | NER `date`, document order |
| `references` | NER `caseno`, `appealcaseno`, `refcase`, `ref`, `refcourt`, `appealcourt` |
| `entities` | All kept NER entities grouped by type, with `count` and `score` |
| `ner_available` | `false` when the model isn't loaded |
| `key_clauses`, `risks` | Parsed from sections 4 and 5 of the **LLM** summary (`clauses_and_risks_source: "llm_summary"`) — not NER output |

**Worked example for the report/demo:** an unseen 2026 Supreme Court bail
order run through the web app, with the full output and a line-by-line
review — [demo_examples.md](demo_examples.md#example-1--document-analysis-on-an-unseen-supreme-court-order).

**Live results (real HTTP, 2026-09-26)**

*Supreme Court judgment* — the first complete judgment in the held-out SCP
test split, rebuilt as a `.txt` upload (147,851 characters; the backend reads
the first 30,000, which contain 84 unique gold entities after the same
merge/drop rules):

- HTTP 200 in 9.2 s (NER and LLM in parallel); no connection held
  idle-in-transaction.
- Unique entities: 89 predicted, 75 matching gold exactly →
  **precision 0.843, recall 0.893** (one document — indicative, not a
  replacement for the test-set numbers above).
- Dates 21/21, case numbers, appeal court and appeal case numbers all exact.
  Most misses are boundary differences (`Khalid Abbas Khan` vs gold
  `Mr. Khalid Abbas Khan`) or long statutory references split or merged
  differently from the annotation.
- `parties` includes the judges and the court itself (`MIAN SAQIB NISAR`,
  `SUPREME COURT OF PAKISTAN`): the model's `per`/`org` types mean "person"
  and "organisation", not litigant.

*Out-of-domain document* — `audit_test.pdf`, a student report on
Pakistan's IT/telecom sector, not a legal document. HTTP 200 in 7.8 s.
Performance is poor, as expected for a model trained only on judgments:

- **References are wrong:** the two "cited cases" are the title line
  (`National University of Computer and Emerging Sciences Saadullah
  22I-8795`) and the report title (`IT & Telecom Sector Pakistan (FY 2026`).
- **No person found** — the author's name was swallowed into the bogus
  reference above.
- **Mislabels:** `Ufone` (a telecom operator) tagged as a location.
- **Dates mostly missed:** only `FY 2026`.
- **Partial transfer of general types:** organisations (`PTA`, `NTC`,
  `National CERT`), cities and some amounts (`Rs 837`, `Rs 285`,
  `US$ 509.6`) were found.

The LLM-derived `key_clauses`/`risks` were sensible for both documents.

**Known limitations**

- The model is trained on court judgments only; on contracts, reports and
  other documents expect the out-of-domain behaviour above.
- Only the first 30,000 characters are tagged (the LLM summary reads the
  first 20,000 — see below).
- `parties` = people and organisations named, not strictly the litigants.
- The clause/risk parser handles the LLM's bullets, numbered lists and
  tables; a bullet with its own sub-bullets comes back as separate items.
- CPU cost: ~7 s of tagging for a 30,000-character document; the model adds
  ~0.6 GB of RAM to the backend process.

**Groq request-size limit (found during this testing).** Groq's on-demand
tier caps a request at 8,000 tokens per minute including the reserved reply.
After the chat reply cap was raised to 2,000 tokens, a summary request with
30,000 characters of text (~6,500 tokens) was rejected with HTTP 413 and the
endpoint returned 503 for any document over ~22,000 characters. The summary
input is now capped at 20,000 characters (`SUMMARY_MAX_CHARS` in
`app/ai/client.py`). Several analyses inside one minute can still hit the
per-minute limit on the free tier.
