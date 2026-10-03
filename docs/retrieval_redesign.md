# Retrieval redesign: section-based statute chunks

Status: **design only, not implemented.** Written 2026-10-03. Every number
below was measured offline with the local embedding model against the
current index; no Groq tokens were used. Statute and section judgements are
the developer's assessment, not a lawyer's.

Supersedes item 1 of "Future work — statute corpus and retrieval" in
[`data/README.md`](../data/README.md), and makes the contents-list lookup
(`backend/app/ai/section_lookup.py`) unnecessary.

---

## 1. Why: what goes wrong today

Two test cases from the October 2026 audit:

| Question (audit) | Gold section | Where it ranks today |
|---|---|---|
| "What are the essential elements of a valid contract under the Contract Act, 1872?" | Contract Act s. 10, "What agreements are contracts" | chunk 27099: **rank 4,366**, score 0.444. Top 5 are the Futures Market Act, Capital Territory Trust Act, IMF Act, Transfer of Property Act and CDA Ordinance. The live answer was built from a Transfer of Property passage that mentions ss. 11–12. |
| "What is the punishment for qatl-i-amd under the Pakistan Penal Code?" | PPC s. 302, "Punishment of qatl-i-amd" | CSV copy: rank 5 (0.741), right on the edge. PDF copy: rank 149 (0.641, below the 0.65 threshold). |

Five causes, found in the code and the data:

1. **The embedding model reads only 128 tokens.**
   - `paraphrase-multilingual-MiniLM-L12-v2` has `max_seq_length` 128.
   - An 800-character chunk is about 196 tokens (median), so **99% of chunks
     are truncated** and the model sees about 65% of each one on average.
   - Chunk 27099 is cut off at "…and are not hereby expressly". The back
     third of every chunk is invisible to search.
2. **Chunks ignore section boundaries.**
   - Section 10 sits in the middle of chunk 27099, after the end of s. 9 and
     before the start of s. 11.
   - The section number and heading carry almost no weight in the
     embedding.
3. **The cleaner destroys line structure and glues words.**
   - In `scripts/clean_statute_corpus.py`, `_fix_letter_spacing()` turns every
     `\n` into a space and then deletes all spaces.
   - Every line break inside the 109 letter-spaced documents (the Contract
     Act among them) therefore joins two words: "freeconsent", "arenot",
     "1872CONTENTSSECTIONS:".
   - Line structure is exactly what section splitting needs. The raw text
     has it: each body heading starts its own line ("10. What agreements are
     contracts. All agreements…").
4. **Contents-list chunks are under-detected.**
   - `is_toc()` looks for `\bCONTENTS\b`, which fails on the glued
     "CONTENTSSECTIONS".
   - In the Contract Act, 19 of 237 chunks (8%) are contents list, and
     `is_toc()` flags **none** of them. The README's figure of 1,445
     contents chunks is therefore a lower bound.
5. **Statutes are indexed twice.**
   - The PPC has a CSV copy ("Pakistan Penal Code", 601 chunks) and a PDF
     copy ("THE PAKISTAN PENAL CODE", 713 chunks). The MFLO likewise has a
     CSV copy and an OCR-titled PDF copy ("…ORDINAN CE, 1961").
   - Duplicates take top-5 slots from other statutes.

### What section chunks would do (measured)

The method:
- Build a section chunk with a header.
- Embed it with the current model.
- Compare its score with today's index for the same query.

**Caveat:** the "rewrite-style" query below was written by hand in the
style of the live rewrite. Real rewrites aren't logged, so section 6 freezes
them.

| Query | Today | Section chunk with header | Section chunk, no header |
|---|---|---|---|
| s. 302, raw question | rank 5 (0.741) | **0.871, rank ~1** | 0.786, rank ~1 |
| s. 302, rewrite-style | rank 7 (0.752) | **0.873, rank ~1** | 0.813, rank ~1 |
| s. 10, raw question | rank 4,366 (0.444) | **0.661, rank ~4** | 0.548, rank ~231 |
| s. 10, rewrite-style | rank 8,973 (0.431) | 0.598, rank ~35 | 0.618, rank ~10 |

A second check section-chunked the whole Contract Act from the raw text,
using the header format in section 3:
- **Raw question:** s. 10 scores 0.690. That beats today's best global
  score (0.672), so it would rank about 1st.
- **Rewrite-style query:** s. 10 scores 0.633. That is about 4th globally,
  but **under the 0.65 threshold**. Ranked above it are ss. 19, 23 and 11,
  which are relevant neighbours: consent, lawful consideration,
  competence.

**Conclusion:** section chunks fix s. 302 outright and make s. 10 reachable.
s. 10 also needs three things:
- the raw question searched alongside the rewrite (section 5.2);
- a threshold recalibrated on the new index (section 6.5);
- the evaluation to confirm both.

---

## 2. Scope

**In scope:** the 901 statute documents. That is 894 PDF-derived
(`pakistan_code_pdf_data.json`) plus 7 CSV section tables
(`Datatset For FAISS.csv`). All 53,739 current chunks are `statute` type;
there are no judgments in the index.

**Not in scope:**
- the query-rewrite prompt (its rejected change is documented in
  `data/README.md`);
- the chat prompt;
- OCR word splits inside text ("pronoun ced", "effec tive"). These are
  reported per statute but not auto-corrected.

---

## 3. Section-based chunking

### 3.1 Pipeline (replaces `chunk_text()` for statutes)

1. **Reflow without losing lines** (the cleaner fix). For letter-spaced
   documents:
   - keep `\n` as a line break;
   - drop the intra-word spaces;
   - map `\xa0` to a space.

   For all documents:
   - keep line breaks through cleaning;
   - collapse them only when building chunk text.

   Fixture test: the Contract Act's s. 10 must read "free consent" and "are
   not".
2. **Split each statute into regions.** A statute has a title, a contents
   list, the body, and schedules.
   - **Contents list:** the block from `CONTENTS`/`SECTIONS:` up to the
     first body heading. In the Contract Act, contents entries read
     `10.What agreements…` (no space after the dot) while body headings read
     `10. What agreements…`, a useful extra signal.
   - **Schedules:** start at a line `THE … SCHEDULE`.
3. **Find body headings.** These are line-start patterns:
   - PDF: `^\s*(\d{1,3}[A-Z]{0,2})\s?\.\s+["“'‘(]?[A-Z]…`, plus amendment
     brackets such as `3[25-A. Transfer…`;
   - CSV: the `Section` / `Heading` columns directly (no parsing).

   Coverage today: **634 of 894 PDF documents have 10 or more line-start
   headings** and 211 have 3 to 9. Only 49 have 2 or fewer, and those fall
   back to windowed chunks (section 3.4).
4. **Validate headings against the contents list** (section 4). Accept a
   heading only if:
   - its number appears in the statute's contents inventory, or there is no
     inventory;
   - numbering doesn't jump backwards by more than a small tolerance.

   This rejects numbered list items inside sections and schedules.

   Quoted headings must parse too: `13. "Consent" defined.` was missed by
   the first prototype, which found 152 of the Contract Act's sections;
   s. 12 to s. 18 were lost to quotes.
5. **Section record:**
   `{section_uid, statute_id, number, heading, chapter, text, char_span}`.
   - Section text runs from its heading to the next accepted heading.
   - Footnote and amendment markers are stripped ("1[Pakistan]" becomes
     "Pakistan", "113[:] 113 114[" is removed), with fixture tests.
   - Sections that only say `[Omitted]` / `Omitted by …` are kept in the
     registry but not embedded.

### 3.2 The chunk header

```
The Contract Act, 1872 — s. 10. What agreements are contracts.
All agreements are contracts if they are made by the free consent of …
```

- **Format:** `{canonical statute title} — s. {number}. {heading}.`, then a
  newline, then the body.
- **Chapter:** stored in metadata, not in the header. Every header token
  costs one of the 128 the model reads, so the header must stay at about
  20 tokens or fewer (measured per window at build time).
- **Canonical title:** from the statute registry (section 4.2), never the
  OCR-damaged one, so "ORDINAN CE" never appears in a header.

The header is what moved s. 10 from rank 4,366 to about 4 and s. 302 from
0.741 to 0.871. It names the statute and the provision in the text the model
actually reads.

### 3.3 Long sections: windows under one parent

- **Size of the problem:** sections are often longer than 128 tokens. In the
  Contract Act the median is 176 tokens, p90 is 536, and 91 of 152 parsed
  sections are over 128. Some CSV sections run to 30,118 characters.
- **Split rule:** split the *embedded text* into windows of about 100 body
  tokens plus the header, measured with the model's own tokenizer.
- **Boundaries:** prefer subsection boundaries (`(1)`, `(2)`, `(a)`), then
  sentence ends, and never mid-word.
- **Overlap:** one sentence.
- **Window record:** each vector stores `section_uid`, `part k/n` and its
  character span.
- **Small to big:** match on the window, give the model the section. If the
  section is 1,500 characters or less, the passage is the header plus the
  whole section. If longer, it is the header, the matched window and its
  neighbours, up to 1,500 characters.

### 3.4 Fallbacks

The 49 documents with 2 or fewer headings, schedules, and preambles get
fixed windows:
- about 100 tokens each;
- one sentence of overlap;
- header `{title} — {region}` (e.g. "— Schedule", "— Preamble").

They are still searchable, just not as sections.

### 3.5 One copy per statute (de-duplication)

- **Keep one copy.** Where a statute exists twice (the PPC, MFLO, CrPC and
  QSO each have a CSV copy and a PDF copy, plus OCR-variant titles), keep
  exactly one per section number.
- **How to choose:** pick the copy with better coverage against the
  contents inventory and fewer OCR splits, as a per-statute decision
  recorded in the build report.
- **The PPC:** the CSV has 502 rows, but the PPC has many lettered sections
  (`302`, `311`, `337-A`…). Coverage decides, and missing sections can be
  filled from the other copy.

---

## 4. Contents-list chunks

**Today:** the contents list is chunked and embedded like any other text. It
has two effects:
- it crowds the top 5, because its section titles match many questions;
- it makes the TOC-guided lookup necessary at all.

**New handling:**

1. **Not embedded.** Contents lists are removed from the vector index
   entirely. No contents chunk can reach the top 5, so `section_lookup.py`
   (the contents-list follower) is deleted once the evaluation confirms
   that.
2. **Used as an oracle.** Each statute's contents list is parsed into an
   inventory: `(number, heading, chapter)`. It is used at build time to:
   - validate body headings (section 3.1, step 4);
   - recover a heading the body's OCR damaged (body "7. Tala q.—" becomes
     contents "7. Talaq");
   - assign chapters;
   - report per-statute coverage: body sections found vs. contents
     entries. A statute below 90% coverage is listed in the build report
     for a manual look.
3. **Kept in the statute registry, not the index.** Each statute gets a
   registry entry (`statutes.json`) with:
   - canonical title, aliases and year;
   - the source it came from;
   - the section inventory and coverage.

   "What does the MFLO cover?" style questions can be answered from the
   registry later if wanted. Nothing in the current UI needs it.
4. **Detection that doesn't depend on spacing.**
   - Contents regions are found structurally: the block before the first
     accepted body heading that matches `CONTENTS|SECTIONS:` after
     squashing spaces.
   - The `is_toc()` heuristic is kept only as a build-time sanity check (0
     contents windows should survive).

---

## 5. Index and runtime changes

### 5.1 Files (a schema change, so a new directory)

`backend/storage/faiss_v2/`:

| File | Contents |
|---|---|
| `manifest.json` | `schema_version: 2`, model name, dim, `max_seq_length`, chunker version, SHA-256 of `sections.jsonl`, counts, build date |
| `statutes.json` | registry: `statute_id`, canonical title, aliases (incl. OCR variants, "PPC", "MFLO", "QSO", "CrPC"), year, chosen source, inventory, coverage |
| `sections.jsonl` | one line per section: `section_uid`, `statute_id`, number, heading, chapter, full text |
| `legal_corpus.faiss` | `IndexFlatIP` over L2-normalised vectors, as today |
| `legal_corpus_meta.json` | per vector: `section_uid`, `part`, `n_parts`, `char_span` (no duplicated full text) |

Size estimates:
- The PDF corpus is 37.7M characters, about 9.2M tokens. There are at most
  about 54,000 line-start headings, and fewer real sections.
- With 100-token windows that comes to **roughly 90k–110k vectors**
  (384-dim, about 150–170 MB) with the current model.
- With a 512-token model (section 6.3, arm B) it is about 45k–55k vectors.

The current index stays in `storage/faiss/`. It is both the baseline arm
and the rollback.

### 5.2 `embeddings.py`

- **Loading:** load v2 when `manifest.schema_version == 2`, and keep v1
  loading until the switch is final. Paths come from config, so rollback is
  a `.env` change.
- **Search:** over-fetch (`top_k × 4`), group windows by `section_uid`, keep
  each section's best score, and return **section-level** records:
  - `statute`, `section`, `heading` and `relevance`;
  - passage text built as in section 3.3.
- **Dual query (no extra Groq):** embed both the user's raw question and the
  rewrite, search both, and take the max score per section.
  - Measured on s. 10: the raw question scored 0.690 against the
    rewrite-style 0.633.
  - It also keeps working when the rewrite drifts (the rewrite has invented
    statutes and section numbers before; see `data/README.md`).
  - Cost: one extra local embedding (about 20 ms).
- **Explicit references:** a question that names a section ("section 7 of
  the MFLO", "s. 302 PPC") is fetched directly from the registry.
  - Only the user's own text is used, never the rewrite, which invents
    section numbers.
  - The statute name is matched against registry aliases.
  - This replaces the contents-list lookup's one useful job.
- **`index_stats()`:** documents means statutes in the registry.

### 5.3 Chat and research

- **Context block:** `[n] Source: The Contract Act, 1872 — s. 10 (What
  agreements are contracts)`, followed by the passage.
- **Context budget:**
  - The total is capped at **7,200 characters**, today's maximum (5 × 800
    plus up to 4 × 800 from the lookup). That keeps a request within Groq's
    8,000 tokens per minute alongside the 2,000-token reply.
  - With longer passages that may mean 4 passages instead of 5. The
    evaluation reports it.
- **Citations payload:**
  - adds `section` and `heading`;
  - the chat's source list and the Research results show "s. 10 — What
    agreements are contracts" instead of a raw chunk excerpt.

### 5.4 Citation checker (`backend/app/ai/citation_check.py`)

**Today:** `_passage_index()` infers which sections a passage contains by
scanning its text ("Section N —", "N. Heading", "302 PPC"). It works, but it
counts a mere cross-reference ("…specified in Section 304") the same as the
section itself, and it uses the OCR title as the owner.

**Changes:**

1. **Structured grounding first.** Passages carry
   `(statute_id, section number)`. The index gets `(number, owner)` for
   every passage, with the owner set to the registry's canonical title plus
   its aliases. That makes "s. 10 of the Contract Act" grounded by
   construction rather than by regex, and fixes owner matching for
   OCR-titled statutes.
2. **Cross-references stay allowed but are flagged.** Numbers found by text
   scan inside a passage that is *another* section become "mentioned"
   entries.
   - A citation grounded only by a mention is kept, since the passage does
     state it, but is logged as `grounded_by_mention`.
   - The evaluation reports how often that happens before deciding whether
     to be stricter.
3. **Subsections:** "s. 7(5)" is grounded when s. 7 is present (already true
   via `_canon`). A test pins it down with the MFLO s. 7(5) pregnancy rule.
4. **The header doesn't double count:** the header line is excluded from the
   text scan, because the structured entry already covers it.
5. **Tests:**
   - the existing citation tests keep passing with the old passage shape;
   - new fixtures use v2 passages (s. 10, s. 302, s. 7(5), and a
     cross-reference to s. 304 that must come out as "mentioned").

---

## 6. Evaluation plan

### 6.1 Questions and gold labels

- **The 78 lawyer questions**
  (`data/processed/qa_eval/Legal_QA_dataset_From_lawyers_clean.csv`).
  - Only 6 lawyer responses cite a section and 10 name an Act with a year,
    so gold labels must be added.
  - For each question, the developer records `in_library` (yes, no or
    foreign) and the acceptable `statute + sections`, marked as the
    developer's assessment.
  - Stored as `data/processed/qa_eval/gold_labels.json`.
- **The audit's five chat questions**, with gold:

| # | Question | Gold |
|---|---|---|
| 1 | Grounds on which a Muslim woman can obtain a decree for dissolution | Dissolution of Muslim Marriages Act 1939, s. 2 |
| 2 | Punishment for qatl-i-amd | PPC s. 302 (s. 300 acceptable support) |
| 3 | Essential elements of a valid contract | Contract Act s. 10 (ss. 11, 13–14, 23 acceptable support) |
| 4 | Capital of Australia | out of scope: must be refused |
| 5 | Talaq pronounced while the wife is pregnant; maintenance in that period | MFLO s. 7 (sub-s. 5) and s. 9 |

### 6.2 Frozen rewrites (one capture, then zero Groq)

- **Why freeze them:** the live rewrite is non-deterministic and not logged,
  so arms can't be compared fairly on fresh rewrites.
- **The capture:** one run of the current `rewrite_search_query()` over the
  83 questions, saved as `qa_eval/frozen_rewrites.json` with
  `{question, rewrite, model, prompt_sha256, date}`.
- **Cost:** about 83 calls at about 500 tokens each, so **about 40k Groq
  tokens**, roughly 20% of the 200k daily budget.
  - It is the only Groq spend in this plan.
  - It runs only with the user's go-ahead, paced for the 8k tokens per
    minute cap.
- **Zero-Groq arm:** every arm also runs on the raw questions, which needs
  no capture at all.

### 6.3 Arms

Every arm is replayed locally on the same frozen rewrites. The harness
imports the backend's retrieval functions directly; it does not go through
HTTP or call the LLM.

| Arm | Index | Retrieval |
|---|---|---|
| A0 | current index | current pipeline incl. contents-list lookup (baseline) |
| A1 | v2 section chunks, MiniLM | rewrite only |
| A2 | v2, MiniLM | rewrite + raw question (max per section) |
| A3 | v2, MiniLM | A2 + explicit-reference fetch |
| B | v2 section chunks, a 512-token multilingual model (`intfloat/multilingual-e5-base`, 768-dim), larger windows | best of A2/A3 |

**Why arm B:** it attacks cause 1 directly, since it reads 4× more text per
vector. It costs more RAM and query time on the CPU server, and it needs
`query:` / `passage:` prefixes.

**Choosing between A and B:** MiniLM is kept unless B wins clearly on the
metrics below.

### 6.4 Metrics (per arm, raw and rewritten queries reported separately)

- **Gold hit@k:** the gold section is among the passages that would reach
  the model (after threshold, de-duplication and context budget). Reported
  as hit@5 and MRR.
- **Answerable rate:** split into in-library and out-of-library or foreign
  questions.
- **False-answer rate:** out-of-scope and foreign questions that get
  passages above the threshold. Australia, the Nigerian CAC question and
  the Thailand contract question must stay refused.
- **Contents-list windows in the top 5:** target 0.
- **Duplicate-statute slots in the top 5:** target 0.
- **Context size per question:** characters, against the 7,200 budget.
- **Citation grounding on stored answers:** re-run the checker over saved
  answers with v2 passages. This is offline; no new generation.

### 6.5 Threshold recalibration

Headers raise scores (s. 302 went from 0.741 to 0.871), so 0.65 no longer
means what it did.

- **Method:** on the new index, sweep the threshold from 0.55 to 0.80.
- **Plot:** in-library gold hit@5 against the out-of-scope false-answer
  rate.
- **Pick:** the highest threshold that keeps false answers at 0 on the
  labelled out-of-scope set.
- **Report:** s. 10's 0.633 (rewrite-style) shows why this matters.

### 6.6 Acceptance criteria (proposed)

1. s. 10 and s. 302 reach the model for audit questions 3 and 2, under both
   the raw and the frozen-rewrite query.
2. Questions 1 and 5 retrieve DMMA s. 2 and MFLO s. 7.
3. Question 4 is refused.
4. In-library gold hit@5 improves by at least 15 points over A0.
5. No new false answers on out-of-scope or foreign questions.
6. No contents-list windows reach the top 5.
7. Context stays within 7,200 characters.
8. After that, **one live check** of the five audit questions (about
   25k Groq tokens, with approval) confirms the answers cite the gold
   sections.

---

## 7. Colab embedding plan

The last full rebuild took hours on the development machine's CPU. On a
Colab T4 GPU, embedding should take minutes. That is an estimate, to be
measured on the first run.

1. **Locally, no GPU:**
   - run cleaner v2 and the section builder;
   - write `sections.jsonl`, `statutes.json`, `windows.jsonl` (the text to
     embed per vector) and the build report (coverage, de-duplication
     choices, fallbacks);
   - run the parser fixture tests;
   - review the report by hand before embedding anything.
2. **Upload `windows.jsonl` to Google Drive.**
   - It contains statute text only: no `.env`, no keys, no user data.
   - The raw datasets are not published elsewhere (see `data/README.md`),
     so they stay in the user's own Drive.
3. **Notebook:**
   - GPU runtime; pin the backend's versions:
     `sentence-transformers==3.1.1 transformers==4.57.6 faiss-cpu==1.15.0
     numpy==2.4.6`;
   - load the model by name;
   - `encode(batch_size=256, normalize_embeddings=True)` in fp32;
   - checkpoint `vectors_part_*.npy` to Drive every ~10k vectors (Colab
     disconnects);
   - build `IndexFlatIP`;
   - write the index, the per-vector metadata and `manifest.json` (model,
     dim, `max_seq_length`, input SHA-256, counts).
   - Arm B is the same notebook with the model name and window size
     changed, written to its own folder.
4. **Download** into `backend/storage/faiss_v2/` (the current index is not
   touched).
5. **Parity checks locally:**
   - Re-embed 200 random windows on the CPU and require cosine ≥ 0.999
     against Colab's vectors (GPU vs CPU numerics).
   - Vector count = window count.
   - Every `section_uid` resolves.
   - Each sampled vector's nearest neighbour is itself.
   - Manifest hash = local `sections.jsonl` hash.
6. **Evaluate** (section 6). **Switch** by pointing `FAISS_INDEX_PATH` /
   `FAISS_METADATA_PATH` at `faiss_v2`. **Rollback** is the same change in
   reverse.

---

## 8. Work breakdown (for when implementation is approved)

1. **Cleaner fix (line-preserving reflow).**
   - Re-run the cleaner.
   - Fixture tests: "free consent", s. 10 heading on its own line.
2. **Section builder.**
   - Regions, headings, contents oracle, de-duplication, windows, fallbacks.
   - Build report.
   - Parser fixtures: s. 10, CSV s. 302, `19A`, quoted headings, `3[25-A.`,
     contents entries not read as body, OCR-split heading recovered from
     contents.
3. **Gold labels for the 83 questions** (developer's assessment).
4. **Frozen-rewrite capture** (~40k tokens, needs approval).
5. **Colab embedding** (A index, then B) and the parity checks.
6. **Offline evaluation harness and report.**
7. **Runtime changes:**
   - `embeddings.py` v2, dual query, explicit-reference fetch;
   - context budget;
   - citations payload;
   - citation checker (structured grounding, "mentioned" entries);
   - delete `section_lookup.py`.
8. **Live check** of the five audit questions (~25k tokens, with approval).
9. **Docs:** update `data/README.md`, PROJECT_CONTEXT.md and the corpus
   statute list.

---

## 9. Risks

- **Heading false positives** (numbered list items, schedules). Mitigated by
  contents-oracle validation and order checks; measured in the build
  report.
- **Statutes with no contents list** (56 of 894 lack a CONTENTS or SECTIONS
  header in the first 3,000 characters). They get order-check-only
  validation and are listed for review.
- **128-token budget.** A long statute title plus heading can eat a large
  share of a window. The header length is measured per window, and the
  build fails if any header exceeds 30 tokens.
- **The score distribution shifts.** Every threshold and score cut-off
  needs recalibrating (section 6.5). The Research page's displayed scores
  will also change.
- **Bigger context per passage.** This is bounded by the 7,200-character
  budget, which may trade passage count for passage completeness. The
  evaluation shows the effect.
- **CSV vs PDF wording differences** for the same section: one copy is
  chosen per statute and the choice is recorded.
