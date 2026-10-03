# Retrieval redesign: section-based statute chunks

Status: **design only. No code changed, no Groq tokens used.** Written
2026-10-03.

Every number here was measured offline:
- with the local embedding model (`paraphrase-multilingual-MiniLM-L12-v2`);
- against the current index (`backend/storage/faiss/`, 53,739 chunks from
  901 statute documents).

Statute and section judgements are the developer's assessment, not a
lawyer's.

This expands option (e), "chunk by section", in
[`data/README.md`](../data/README.md) ("Future work — statute corpus and
retrieval"). It also accounts for the experiments recorded there as
rejected. Section 8 checks the design against each of them.

---

## 0. Measured starting point

### 0.1 The known failures, re-measured offline

"Raw" means the user's question embedded as-is. "Rewrite-style" means a
query written by hand in the style of the live rewrite. Real rewrites aren't
logged, which is why section 7 records them.

| Test case | Query | Gold chunk today | Same section as a chunk with a header (proposed) |
|---|---|---|---|
| **PPC s. 302** | raw | rank 5, 0.741 (CSV copy); rank 149, 0.641 (PDF copy) | **0.871, rank ~1** |
| | rewrite-style | rank 7, 0.752 | **0.873, rank ~1** |
| **Contract Act s. 10** | raw | **rank 4,366**, 0.444 | 0.661, rank ~4 (header + section); **0.690, rank ~1** when the whole Act is section-chunked |
| | rewrite-style | rank 8,973, 0.431 | 0.633, rank ~4, **but below the 0.65 threshold** |
| **DMMA s. 2** (dissolution grounds) | raw | **rank 1, 0.822**: found today | 0.870, rank ~1 |
| | rewrite-style | rank 2, 0.843 | 0.858, rank ~2 |
| **MFLO s. 7(5)** (talaq during pregnancy; audit question 5) | raw | rank 2, 0.541 (best MFLO chunk 0.693) | whole s. 7 with header: **0.504**; the window holding sub-s. (5) with header: **0.751, rank ~1** |

How the "proposed" column was measured:
- Each section chunk was embedded and its score compared with today's index
  for the same query.
- The Contract Act row was also tested by section-chunking the whole Act
  from the raw text (152 sections parsed).
- These are estimates of rank. The real ranks come from the rebuilt index
  (section 7).

### 0.2 Two kinds of failure

The live audit retrieved:

| Audit question | Retrieved live | Outcome |
|---|---|---|
| Dissolution grounds | MFLO, Family Courts Act, Child Marriage Restraint Act (**no DMMA**) | "not detailed in the passages" |
| Compound talaq / pregnancy | nothing above 0.65 | refused |
| Qatl-i-amd punishment | PPC chapter text, CrPC, Hadd Order (no s. 302) | "library does not contain" |
| Valid contract | Transfer of Property, Futures Market, Capital Territory Trust, CDA, IMF Acts | answered from TPA ss. 11–12 |

1. **Chunking failures (s. 302, s. 10).** The right text exists but is
   diluted in an 800-character window, or truncated out of it. Section
   chunks with headers fix these.
2. **Rewrite failures (DMMA s. 2, MFLO s. 7).** The raw question finds the
   right statute today: DMMA s. 2 ranks 1st, and the MFLO scores 0.693, above
   the threshold. The live rewrite moved the search away. **Section
   chunking alone does not fix this.** It needs the raw question searched
   alongside the rewrite (section 4.3).

### 0.3 Root causes found in the code and data

1. **The model reads 128 tokens.**
   - `max_seq_length` is 128.
   - An 800-character chunk is about 196 tokens (median), so **99% of chunks
     are truncated**, and the model sees about 65% of each.
   - Chunk 27099 (s. 10) is cut off at "…and are not hereby expressly".
   - MFLO s. 7 as a whole scores 0.504 because sub-s. (5) is past the
     128-token cut.
2. **Chunks ignore section boundaries.** s. 10 sits mid-chunk between the
   end of s. 9 and the start of s. 11.
3. **The cleaner glues words and destroys line structure.**
   - In `scripts/clean_statute_corpus.py`, `_fix_letter_spacing()` turns
     `\n` into a space and then deletes all spaces.
   - Every line break in the 109 letter-spaced documents therefore joins
     two words: "freeconsent", "arenot", "1872CONTENTSSECTIONS:".
   - The raw text has each section heading on its own line, which is
     exactly what section detection needs.
4. **Contents lists go undetected.** `is_toc()` needs `\bCONTENTS\b`, which
   fails on glued text. 19 of the Contract Act's 237 chunks (8%) are its
   contents list, and none are flagged. The README's 1,445 is a lower
   bound.
5. **Statutes are indexed twice.**
   - PPC: a CSV copy (601 chunks) and a PDF copy (713 chunks).
   - MFLO: a CSV copy and "…ORDINAN CE, 1961".

---

## 1. Section detection

### 1.1 Prerequisite: fix the reflow

The letter-spaced reflow must keep `\n` as a line break, then:
- drop intra-word spaces;
- map `\xa0` to a space;
- keep line breaks through all cleaning;
- collapse them only when writing chunk text.

Fixture tests: Contract Act s. 10 reads "free consent … and are not", and
its heading starts a line.

### 1.2 Two sources, two detectors

**CSV section tables** (7 statutes: PPC, CrPC, QSO, Transfer of Property
Act, Limitation Act, MFLO, Police Order):
- Sections come straight from the `Section` / `Heading` / `Defination`
  columns, so no parsing is needed.
- The cleaning rules already in the script (CrPC year relabelling,
  dropped rows) still apply.

**PDF-derived text** (894 documents):

1. **Regions.** Each statute has a title, a contents list, a preamble, the
   body and schedules.
   - Contents list: from `CONTENTS` / `SECTIONS:` (matched after squashing
     spaces) to the first accepted body heading.
   - Schedules: from a line `THE … SCHEDULE`.
2. **Body headings:** line-start matches of
   `^\s*(\d{1,3}[A-Z]{0,2})\s?\.\s+["“'‘(]?[A-Z]…`. This includes:
   - quoted headings: `13. "Consent" defined.` (the prototype missed s. 12
     to s. 18 by not allowing quotes);
   - lettered sections: `19A.`, `25-A.`;
   - amendment brackets: `3[25-A. Transfer…`.
3. **Telling contents entries from body headings.**
   - Contents entries carry no running text.
   - In letter-spaced statutes they also lack the space after the dot
     (`10.What agreements…` vs body `10. What agreements…`).
   - The region split above is the primary rule.

Coverage measured on the 894 raw PDF documents:

| Line-start numbered headings per document | Documents |
|---|---|
| 10 or more | **634** |
| 3 to 9 | 211 |
| 1 to 2 | 47 |
| none | 2 |

838 of 894 have a CONTENTS or SECTIONS header in their first 3,000
characters.

### 1.3 OCR-damaged headings

| Damage | Example | Handling |
|---|---|---|
| Letter-spacing | `1 0 . W h a t` | fixed by the reflow (section 1.1) |
| A word split by a stray space | `7. Tala q.—`, `pronoun ced` | Match the heading against the contents inventory (section 3) with a space-insensitive comparison. **Display the contents spelling** ("Talaq"). Body text is not auto-corrected (README: a dictionary fix risks legal terms). The build report counts split words per statute. |
| Number damage | `1O.` (letter O), `l1.`, a missing dot | Accept only if the corrected number is the next expected entry in the contents inventory. Otherwise not a heading. |
| Heading missing from the body | an inventory entry with no body match | The text stays with the previous section, and the gap is listed in the build report (no guessing). |
| Unreadable gazette scans | 3 documents with mojibake titles | fallback (section 1.4), flagged |

**Validation:**
- A heading is accepted only if its number appears in the statute's
  contents inventory (when one exists).
- Numbering may not run backwards by more than a small tolerance. This
  rejects numbered items inside sections and schedules.
- Per statute, the build report shows **body sections found ÷ contents
  entries**. Below 90% means a manual look before embedding.

### 1.4 Statutes without clear section headings

Covered here:
- the 49 documents with 2 or fewer headings;
- the 56 with no contents list, when their headings fail order checks;
- schedules and preambles of every statute.

They get **fixed windows:**
- about 100 tokens each;
- one sentence of overlap;
- header `{canonical title} — {region}` (e.g. "— Schedule", "— Part 3 of
  12").

They remain searchable. Citations to them can't be section-grounded, so
the checker treats them as today.

### 1.5 One copy per statute

Where a statute exists twice (PPC, CrPC, QSO and MFLO as CSV and PDF, plus
OCR-titled duplicates), **index one copy per section number**:
- choose the copy with the higher inventory coverage and fewer OCR splits;
- fill sections missing from it from the other copy;
- record each choice in the build report.

The PPC is the clear test. Its CSV has 502 rows, and the PDF copy holds
lettered sections the CSV may lack.

---

## 2. Chunk header and long sections

### 2.1 Header

```
The Contract Act, 1872 — s. 10. What agreements are contracts.
All agreements are contracts if they are made by the free consent of …
```

`{canonical statute title} — s. {number}. {heading}.`, then a newline, then
the body.

- **Canonical title:** from the statute registry (section 4.1), never the
  OCR title.
- **Chapter:** kept in metadata, not in the header. Each header token costs
  one of the 128 the model reads.
- **Budget:** the header must be **30 tokens or fewer**, and the build fails
  if one exceeds it. A typical header is 15–20 tokens.

**Effect** (section 0.1):
- s. 302: 0.786 without the header, 0.871 with it;
- s. 10, raw question: 0.548 without, 0.661 with.

One case went the other way: s. 10 with a keyword-style query scored 0.618
without the header and 0.598 with it. The evaluation measures the header
across all questions (arms in section 7.4).

### 2.2 Split rule for long sections

- **Size of the problem:** sections often exceed the 128-token window. In
  the Contract Act the median is 176 tokens and p90 is 536; 91 of 152
  sections are over 128; one CSV section is 30,118 characters.
- **Rule:**
  1. Measure each section with the model's own tokenizer.
  2. If header + body is 128 tokens or fewer, it is one window.
  3. Otherwise split the body into windows of **about 100 body tokens**,
     each prefixed with the same header.
  4. Split at subsection or clause boundaries first (`(1)`, `(2)`, `(a)`,
     `Explanation.—`, `Provided that`), then sentence ends, never
     mid-word.
  5. Overlap is one sentence. Each window records `part k/n` and its
     character span.

**Evidence:** the window holding MFLO s. 7(5) scores 0.751 (rank ~1) where
the whole of s. 7 scores 0.504. Embedding a long section as one unit loses
its later subsections to truncation.

**What the model sees (small to big):** the search matches a window, but
the chat model gets the section:
- the header plus the whole section if it is 1,500 characters or less;
- otherwise the header plus the matched window and its neighbours, up to
  1,500 characters.

**Context budget:** the total is capped at **7,200 characters**, today's
maximum (5 chunks × 800 plus up to 4 lookup chunks × 800). That keeps each
request inside Groq's 8,000 tokens per minute with the 2,000-token reply.

---

## 3. Contents-list chunks

1. **Removed from the vector index.** No contents window can reach the top
   5. Demoting them was rejected before because other chunks took the slot.
   Here the section text itself becomes retrievable, so that objection no
   longer applies.
2. **Used as a build-time oracle.** Each contents list is parsed into an
   inventory of `(number, heading, chapter)` and used to:
   - validate headings and repair OCR-damaged ones (section 1.3);
   - assign chapters;
   - measure coverage per statute.
3. **Kept in the statute registry** (`statutes.json`), not the index. That
   leaves "what does this Act cover" answerable later without polluting
   search.
4. **Detection by structure**, not by `\bCONTENTS\b` on glued text. The old
   `is_toc()` stays only as a build check: zero surviving windows may look
   like contents.

---

## 4. Index metadata and citation checker

### 4.1 New files in `backend/storage/faiss_v2/`

**The current `storage/faiss/` is not touched.**

| File | Contents |
|---|---|
| `manifest.json` | `schema_version: 2`, model, dim, `max_seq_length`, chunker version, SHA-256 of inputs, counts, build date |
| `statutes.json` | `statute_id`, canonical title, **aliases** (OCR variants, "PPC", "MFLO", "CrPC", "QSO"…), year, chosen source, contents inventory, coverage |
| `sections.jsonl` | `section_uid`, `statute_id`, number, heading, chapter, full text |
| `legal_corpus.faiss` | `IndexFlatIP` over L2-normalised vectors (as today) |
| `legal_corpus_meta.json` | per vector: `section_uid`, `part`, `n_parts`, `char_span` (no duplicated text) |

**Size:**
- The PDF corpus is 37.7M characters, about 9.2M tokens, with at most about
  54,000 line-start headings (fewer real sections).
- With the current model that comes to about **90k–110k vectors**, roughly
  150–170 MB.
- With a 512-token model (arm B, section 7.4) it is about 45k–55k
  vectors.

### 4.2 Runtime (`embeddings.py`, chat, research)

**Loading:**
- `embeddings.py` loads v2 when `manifest.schema_version == 2` and keeps v1
  loading.
- Switching index is a `.env` change of `FAISS_INDEX_PATH` /
  `FAISS_METADATA_PATH`.

**Search:**
- Over-fetch `top_k × 4` windows and group them by `section_uid`, keeping
  each section's best score.
- Return section-level records: `statute`, `section`, `heading`,
  `relevance` and passage text (section 2.2).

**Dual query (the fix for rewrite failures):**
- Embed both the user's raw question and the rewrite, search both, and keep
  the max score per section.
- It costs one extra local embedding (tens of milliseconds) and no Groq
  tokens.
- It would have kept DMMA s. 2 (0.822 raw) for the dissolution question.

**Explicit references:**
- A question naming a section ("s. 7 MFLO", "section 302 of the PPC") is
  fetched directly from the registry.
- Only the **user's own text** is used, never the rewrite, which invents
  section numbers (see README).

**Display:**
- The context block reads `[n] Source: The Contract Act, 1872 — s. 10 (What
  agreements are contracts)`.
- The citations payload adds `section` and `heading`, and the Research
  results show "s. 10 — What agreements are contracts".
- `index_stats()` counts statutes from the registry.

### 4.3 Citation checker (`backend/app/ai/citation_check.py`)

**Today:** `_passage_index()` infers which sections a passage holds by
scanning its text ("Section N —", "N. Heading", "302 PPC"), and uses the
passage's OCR title as the owner. A cross-reference ("…specified in
Section 304") counts the same as the section itself.

**Changes:**

1. **Structured grounding.**
   - Each v2 passage contributes `(number, owner)` from its metadata.
   - The owner is the registry's canonical title plus all its aliases, so
     "s. 10 of the Contract Act" and "302 PPC" ground by construction.
   - OCR titles like "ORDINAN CE" stop mattering.
2. **"Mentioned" entries.**
   - Text-scan matches inside a passage that is *another* section become
     `mentioned`.
   - A citation grounded only by a mention is kept, since the passage does
     state it, but is logged.
   - The evaluation counts these before any decision to be stricter.
3. **Header excluded from the text scan**, because the structured entry
   already covers it.
4. **Subsections:** "s. 7(5)" is grounded by s. 7 (already true via
   `_canon`), pinned by a test.
5. **Old shape kept working:** v1 passages (no structured fields) still use
   the current text scan, so the old index keeps working during the
   comparison.
6. **Tests:** fixtures for s. 10, s. 302, s. 7(5), a s. 304 cross-reference
   that must come out `mentioned`, and an OCR-titled owner.

---

## 5. The TOC-guided section lookup: goes, after measurement

`backend/app/ai/section_lookup.py` exists only because a contents chunk
outranks the section text it lists. With contents removed from the index
(section 3) it can never fire on v2: it starts from a retrieved contents
chunk.

Its one useful job, following an explicit "section N" in the question, is
taken over by the registry fetch (section 4.2). That fetch is deterministic
and doesn't need a contents chunk to reach the top 5.

**Decision:**
- Keep it while the v1 index is live (arm A0 in section 7 includes it).
- Delete it when v2 is switched on, if the evaluation shows no question
  that A0 answered **via** the lookup regresses on v2.

The lookup logs `via_toc`, so those questions can be identified in the
replay.

---

## 6. Colab embedding plan (no local rebuild)

**Why not locally:** this machine embeds about **10 chunks per second** on
the CPU (measured: 512 chunks in 53 s). Today's 53,739 chunks therefore
take about 1.5 hours, and the ~110k v2 windows about 3 hours. **No
embedding is done locally.** The only local model use is the 200-vector
parity check in step 5.

**Steps:**

1. **Local, CPU, no model (minutes):**
   - run cleaner v2 and the section builder;
   - write `sections.jsonl`, `statutes.json`, `windows.jsonl` (the exact
     text to embed per vector) and the build report;
   - run the parser fixture tests;
   - review the build report by hand: coverage, de-duplication choices,
     fallbacks, header lengths.
2. **Upload** `windows.jsonl` (statute text only, about 50–70 MB) to Google
   Drive.
   - No `.env`, keys or user data go up.
   - The raw datasets aren't published anywhere (see `data/README.md`), so
     they stay in the user's own Drive.
3. **Notebook on a T4 GPU runtime:**
   - pin the backend's versions:
     `sentence-transformers==3.1.1 transformers==4.57.6 faiss-cpu==1.15.0
     numpy==2.4.6`;
   - `encode(batch_size=256, normalize_embeddings=True)`, fp32;
   - checkpoint `vectors_part_*.npy` to Drive every ~10k vectors (Colab
     disconnects);
   - print the measured throughput and ETA after the first 2k vectors;
   - build `IndexFlatIP`;
   - write the index, the per-vector metadata and `manifest.json`.
   - Arm B is the same notebook with the model name and window size
     changed, written to its own folder.
4. **Download** to `backend/storage/faiss_v2/` (and `faiss_v2b/` for arm B).
5. **Parity checks, local:**
   - re-embed 200 random windows on the CPU, requiring cosine ≥ 0.999
     against the Colab vectors;
   - vector count = window count;
   - every `section_uid` resolves;
   - each sampled vector's nearest neighbour is itself;
   - manifest hash = local `sections.jsonl` hash.

**Time estimates.** These are estimates: the notebook measures the real
rate on its first batches.

| Step | MiniLM, ~110k windows of ≤128 tokens | Arm B, 512-token model, ~50k windows |
|---|---|---|
| Runtime start + `pip install` | 3–5 min | 3–5 min |
| Upload `windows.jsonl` / model download | 2–4 min | 3–5 min |
| Embedding on a T4 | **2–4 min** (assumes ~500–1,000 windows/s) | **5–10 min** (assumes ~100–200/s) |
| Build index, write files | about 1 min | about 1 min |
| Download index (~150–170 MB / ~150 MB) | 2–5 min | 2–5 min |
| **Total session** | **about 10–20 min** | **about 15–25 min** |
| Local parity check (200 vectors on CPU) | about 20 s | about 1 min |

Compare roughly 3 hours for the same embedding on this machine's CPU.

---

## 7. Evaluation plan (no Groq tokens after one recording)

### 7.1 Questions

- **The 78 lawyer questions** in
  `data/processed/qa_eval/Legal_QA_dataset_From_lawyers_clean.csv`.
- **The five chat questions from the last audit:**

| # | Question | Gold (developer's assessment) |
|---|---|---|
| A1 | On what grounds can a Muslim woman obtain a decree for the dissolution of her marriage? | DMMA 1939 s. 2 |
| A2 | What is the punishment for qatl-i-amd under the Pakistan Penal Code? | **PPC s. 302** (s. 300 acceptable support) |
| A3 | What are the essential elements of a valid contract under the Contract Act, 1872? | **Contract Act s. 10** (ss. 11, 13–14, 23 acceptable support) |
| A4 | What is the capital of Australia and how many people live there? | out of scope: must be refused |
| A5 | If a husband pronounces talaq while his wife is pregnant… can she claim maintenance? | MFLO s. 7 (sub-s. 5) and s. 9 |

**Gold labels for the 78:**
- Only 6 lawyer answers cite a section and 10 name an Act with a year.
- So, for each question, the developer records `in_library` (yes, no or
  foreign) and the acceptable `statute + sections`, marked as the
  developer's assessment.
- Stored in `data/processed/qa_eval/gold_labels.json`.
- Questions with no confident label are kept but only scored on
  answerability.

### 7.2 Recording the rewrites (the only Groq use)

**Why record:** the rewrite is a model call, non-deterministic, and not
logged. Both indexes must be fed the **same** rewrites.

**How:** add a `--record-rewrites` mode to `scripts/eval_research_retrieval.py`.
- It calls the backend's `AIClient.rewrite_search_query()` directly, not
  through HTTP: `/research/search` doesn't return the rewrite, and would
  also embed and search for no reason.
- It writes `data/processed/qa_eval/frozen_rewrites.json`:
  `{question, rewrite, model, prompt_sha256, finish_reason, date}`.
- **Silent fallbacks:** on any failure the rewrite function returns the
  original question unchanged. The recorder flags `rewrite == question` and
  empty or cut-off outputs, and retries those once.

**Cost, measured offline with the o200k tokenizer:**
- System prompt 265 tokens; questions median 61 and max 159 tokens.
- Per call: prompt about 344 tokens (median), 444 (max). With the 150
  `max_tokens` that Groq's per-minute check also reserves, at most 594.
- 83 calls: about 28,600 prompt tokens plus about 5,000 output, so **about
  34k tokens**, roughly 17% of the 200k daily budget.

**Pacing:** stay under about 6,500 reserved tokens per minute, which is 10
calls a minute at worst. The 83 calls take **about 8–10 minutes**. The
recorder sleeps between calls and stops on HTTP 429.

**Approval:** runs once, with your go-ahead, on a day with enough budget
left.

### 7.3 Replay (zero Groq)

- **What it is:** a `--replay frozen_rewrites.json --index {v1|v2}` mode.
  It runs retrieval in-process using the backend's own `embeddings.search`
  (and, for A0, `section_lookup`), with no HTTP and no LLM.
- **Two query sets per arm:**
  - **rewrite:** the recorded rewrites, as the app would search;
  - **raw:** the questions as written, with no recording needed.
- **What it records per question:** each passage that would reach the model
  after the threshold, de-duplication and context budget, with its statute,
  section, score and rank.
- **Fixes to the script itself:**
  - its `THRESHOLD = 0.7` is stale (the app uses 0.65), so read it from
    settings;
  - it only looks at the top-1 score, so look at the full passage set.

### 7.4 Arms

| Arm | Index | Retrieval |
|---|---|---|
| **A0** | current v1 | rewrite only + contents-list lookup (today's app) |
| A1 | v2 section windows, MiniLM | rewrite only |
| A2 | v2, MiniLM | **rewrite + raw question** (max per section) |
| A3 | v2, MiniLM | A2 + explicit-reference fetch |
| A1-nh | v2 windows **without headers** | as A2 (tests the header) |
| B | v2, `intfloat/multilingual-e5-base` (512 tokens, 768-dim, larger windows) | as A3 |

**Arm B:** it reads 4× more text per vector, which attacks root cause 1.
The cost is more RAM and slower query embedding on the CPU server. MiniLM
stays unless B wins clearly.

### 7.5 Per-question report (not just means)

For every question and every arm, one row:

```
#  question (60 chars) | gold | A0: rank/score/reached? | A1 | A2 | A3 | B | verdict
```

- **Verdicts:** **gained** (gold reached the model in this arm but not in
  A0), **lost** (the reverse), **same**, **newly answerable**, **newly
  refused**.
- **Lists:**
  - every gained and every lost question in full, with the passages each
    arm sent;
  - every out-of-scope or foreign question that becomes answerable, as a
    **false answer**. The known traps are Australia (A4), the Nigerian CAC
    question and the Thailand contract question, which must stay refused.
- **Summaries, after the per-question tables:**
  - gold hit@5 and MRR, answerable rate in and out of library, false-answer
    count;
  - contents windows in the top 5 (target 0) and duplicate-statute slots
    (target 0);
  - context characters (budget 7,200);
  - questions A0 answered via the contents-list lookup (`via_toc`), to
    decide section 5;
  - citation-checker counts: the checker re-run offline on **stored** answers
    against v2 passages, counting `mentioned`-only groundings.
- **Test cases called out separately:** PPC s. 302 (A2), Contract Act s. 10
  (A3), and DMMA s. 2 / MFLO s. 7(5) as the rewrite-failure pair. Each shows
  rank and score under raw and frozen-rewrite queries for every arm.

### 7.6 Threshold recalibration

Headers raise scores (s. 302 went from 0.741 to 0.871), so 0.65 means
something different on v2.

- **Sweep:** 0.55 to 0.80 on v2.
- **Plot:** in-library gold hit@5 against out-of-scope false answers.
- **Pick:** the highest threshold with zero false answers on the labelled
  out-of-scope set.
- **Why it matters:** s. 10 under a rewrite-style query scores 0.633.

### 7.7 Acceptance (proposed)

- s. 302 and s. 10 reach the model for A2 and A3 under the frozen rewrite.
- DMMA s. 2 and MFLO s. 7 reach it for A1 and A5.
- A4 is refused.
- No question in the "lost" list without an explanation the developer
  accepts.
- No new false answers; no contents windows in the top 5.
- Context within 7,200 characters.

**Only then:** one live check of the five audit questions (about 25k Groq
tokens, with approval) before switching `.env` to v2.

### 7.8 Keep the old index

- `backend/storage/faiss/` stays as it is until v2 has been measured and
  accepted.
- After the switch it stays for at least one demo cycle as the rollback, a
  `.env` change away.
- The frozen rewrites and gold labels stay too, so any future index can be
  replayed against both.

---

## 8. Checked against the rejected experiments (README)

| Rejected | Why it doesn't apply here |
|---|---|
| Demote or drop contents chunks | Other chunks took the slot because the section text wasn't retrievable. Here the section text is its own short, headed chunk (s. 302 at 0.871). |
| Take more chunks from the matched statute | Not used. Retrieval is per section, with statute context in the header. |
| BM25 + embedding fusion | Not used. |
| Rewrite names the governing statute | Not used. The rewrite prompt is unchanged, and **dual query** lowers dependence on the rewrite instead. |
| Look up a statute's contents list whenever the rewrite names it | Not used. The explicit-reference fetch uses only numbers the **user** wrote. Generic title words ("punishment") are never matched. |

---

## 9. Risks

- **Heading false positives** from numbered items in sections and
  schedules. Mitigated by inventory validation and order checks, and
  counted in the build report.
- **Sections lost to OCR damage.** Text stays with the previous section and
  the gap is reported, but a lost heading means that section is retrieved
  only under its neighbour's header.
- **Wrong de-duplication choice** (CSV vs PDF wording). One copy per
  statute, the choice recorded, the other copy kept for filling gaps.
- **Header crowding** of the 128-token window for long statute titles.
  Measured, with the build failing past 30 tokens.
- **The score distribution shifts.** Every threshold needs recalibrating
  (section 7.6), and the Research page's displayed scores change.
- **Passage size vs passage count** within the 7,200-character budget. The
  model may get 4 complete sections instead of 5 fragments.
- **Arm B's runtime cost**: about 1 GB more RAM, and slower CPU query
  embedding on the server.
- **One recorded rewrite per question** is a single sample of a
  non-deterministic process. A question can pass on the frozen rewrite and
  fail on a different live one.

---

## 10. What can't be measured offline

1. **Answer quality.** Offline replay shows which passages *would* reach
   the model, not what it would write. Whether it now cites s. 10 and
   s. 302 correctly, stops saying "the library does not contain", and keeps
   refusals honest needs the live check (section 7.7).
2. **Live rewrite variance.** Only one recorded sample per question; the
   distribution of live rewrites (the cause of the DMMA and MFLO misses) is
   not measured. Dual query reduces the exposure but can't be proven
   offline beyond those samples.
3. **Groq token use per request.** The prompt size can be computed offline
   from the context characters. Whether real requests stay under 8,000
   tokens per minute, with reasoning tokens and the reply, needs live
   calls.
4. **Citation checking on new answers.** The checker can be re-run only on
   stored answers against v2 passages. Its behaviour on answers written
   *from* v2 passages needs new generations.
5. **Server latency and memory**, especially for arm B and for loading a
   ~150 MB index next to the NER model. They're measurable on this machine
   but not representative of a deployment.
6. **Legal correctness of gold labels.** They are the developer's
   assessment. Whether s. 10 is "the" answer to the essential-elements
   question, or DMMA s. 2 the complete answer on dissolution grounds, is a
   lawyer's call.
7. **Urdu questions.** The eval set is English. The multilingual model's
   behaviour on Urdu queries against headed English chunks isn't covered.
   Adding a few Urdu questions to the gold set would cover it offline,
   apart from the rewrite recording.
