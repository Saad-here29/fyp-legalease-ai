# Knowledge base v2: specification (Phase A, extended in B1)

Branch `kb-v2`. This defines the records, sources and storage for the next
knowledge base. Nothing here changes the live app:
- the live FAISS index (`backend/storage/faiss/legal_corpus.*`) and its
  metadata stay as they are;
- chat and research keep reading them until a v2 index is built, verified
  and deliberately switched to (a later phase);
- no model calls are involved in Phase A.

## a) Statute section record

**One JSON object per section of an Act,** stored as JSON Lines (one record
per line).

| Field | Type | Meaning |
|---|---|---|
| `doc_id` | string | Stable id: `<source>/<act-slug>/<section>`, e.g. `pakistan-code/dissolution-of-muslim-marriages-act-1939/s2` |
| `title` | string | The Act's title as the source gives it, without status notes |
| `section` | string or null | Section number as printed: `"2"`, `"10A"`, `"Schedule"`; null only for an unsectioned window |
| `heading` | string or null | The section heading; null for a schedule, preamble or unsectioned window |
| `text` | string | The section text, cleaned: footnotes, page headers and watermarks removed; amendment brackets like `3[(iia) …]` kept as text without the footnote marker |
| `source_type` | `"statute"` | Always `statute` for this record type |
| `jurisdiction` | enum | `Pakistan` (federal), `Punjab`, `Sindh`, `KP`, `Balochistan`, `ICT` |
| `category` | string or null | The Pakistan Code category, e.g. `"Family Laws"` (from `category_map.json`); null if the source has no categories or the Act isn't listed in one |
| `year` | integer | Year of the Act, from the title (the listing's act number can disagree: see the coverage report) |
| `act_number` | string or null | As listed, e.g. `"VIII of 1939"` |
| `source` | string | Publisher, e.g. `"Pakistan Code"`, `"KP Code"` |
| `source_tier` | 1, 2 or 3 | See (c) |
| `source_url` | string or null | The page the Act was fetched from; null if unknown |
| `original_file` | string or null | Path of the saved original under `backend/storage/kb/raw/` (PDF or HTML); null if we hold no original |
| `scraped_at` | ISO 8601 UTC or null | When the original was fetched; null if unknown |
| `content_hash` | string | SHA-256 of the whitespace-normalised `text` (the scraper's `content_hash`), for change detection |
| `status` | enum | `current`, `under_review` or `repealed`, from the source's annotation (e.g. "(Repealed by Act XIV of 2015)", "(Under Review)") |
| `sectioned` | boolean (optional) | `false` for an unsectioned law's windowed chunk (see below) |
| `provenance_note` | string (optional) | Anything a reader must know about where the text came from, e.g. "original source URL to be confirmed" |

**Records built from what we already hold (Phase B1).**
- **Laws from our corpus:**
  - `source` is "LegalEase corpus (Pakistan Code-derived; original download provenance not recorded)";
  - `source_tier` is 1 only if the title matched a Pakistan Code category listing in `category_map.json`, otherwise 2;
  - `category`, `act_number` and `status` come from that listing when it matched (null / `current` otherwise);
  - `source_url`, `original_file` and `scraped_at` are null, because we don't know them;
  - `doc_id` starts with `legalease-corpus/`.
- **User-supplied files:**
  - `source` is "user-supplied PDF", `source_url` null, `status` `under_review`;
  - a `provenance_note` until the original source is confirmed;
  - `original_file` points at the copy in `raw/`.
- **Section ids:** `section` is the number as printed ("2", "10A"). A
  Schedule is its own record (`"Schedule"`, or `"Schedule 1"`, `"Schedule 2"`
  …), and a preamble may be a record (`"Preamble"`, heading null). The
  Constitution's articles are stored the same way, in `section`.
- **Unsectioned laws:** if the splitter finds fewer than 90% of the sections
  the table of contents (or the numbering) implies, the law isn't forced into
  sections. It's kept as ~1,200-character windows with `section` and
  `heading` null, `sectioned: false`, and `doc_id` ending `/w1`, `/w2` ….

**Rules:**
- **Superseded versions:** a section whose `content_hash` changes gets a new
  record, and the old one is kept in an archive file (see (d)), not
  overwritten.
- **Repealed Acts** keep their records with `status: "repealed"`. Retrieval
  excludes them unless the question asks about the old law.

**Example,** a real section of an Act we hold. The values come from the
Pakistan Code listing and our corpus text, fetched 2026-10-06. The
`original_file` path and `scraped_at` show the planned layout; this Act's PDF
has not been downloaded in Phase A.

```json
{
  "doc_id": "pakistan-code/dissolution-of-muslim-marriages-act-1939/s2",
  "title": "Dissolution of Muslim Marriages Act, 1939",
  "section": "2",
  "heading": "Grounds for decree for dissolution of marriage",
  "text": "A woman married under Muslim Law shall be entitled to obtain a decree for dissolution of her marriage on any one or more of the following grounds, namely:— (i) that the whereabouts of the husband have not been known for a period of four years; (ii) that the husband has neglected or has failed to provide for her maintenance for a period of two years; (iia) that the husband has taken an additional wife in contravention of the provisions of the Muslim Family Laws Ordinance, 1961; …",
  "source_type": "statute",
  "jurisdiction": "Pakistan",
  "category": "Family Laws",
  "year": 1939,
  "act_number": "VIII of 1939",
  "source": "Pakistan Code",
  "source_tier": 1,
  "source_url": "https://pakistancode.gov.pk/english/UY2FqaJw1-apaUY2Fqa-cJaW-sg-jjjjjjjjjjjjj",
  "original_file": "backend/storage/kb/raw/pakistan-code/dissolution-of-muslim-marriages-act-1939.pdf",
  "scraped_at": "2026-10-06T00:00:00Z",
  "content_hash": "3086066f42378f0b90ef99b434dbfb07225b88d02616fbe7aabe428d0c029fb9",
  "status": "current"
}
```

The example text is shortened (`…`); a real record holds the whole section.
The hash shown is of exactly this example text.

## a2) Index chunks (rule fixed now; nothing is embedded yet)

A record is what we store; a **chunk** is what gets embedded. The embedding
model (`paraphrase-multilingual-MiniLM-L12-v2`) reads at most **128 tokens**
and silently ignores the rest. So:

- **Size:** each chunk is a window of **at most 120 tokens**, taken from **one**
  section record (never across two sections).
- **Counting:** tokens are counted with **the embedding model's own
  tokenizer** (`SentenceTransformer(EMBEDDING_MODEL_NAME).tokenizer`), not by
  words or characters. Its 2 special tokens (start and end) bring the total to
  at most 122, inside the 128 limit, so no text is ever cut off unseen.
- **Prefix:** every chunk starts with `"<Title> - s.<N> <Heading>:"`, e.g.
  `"Dissolution of Muslim Marriages Act, 1939 - s.2 Grounds for decree for
  dissolution of marriage:"`. **The prefix counts inside the 120.** A
  schedule uses `"<Title> - Schedule 1:"`; an unsectioned window uses
  `"<Title>:"`.
- **Windows:** the section text is split on token boundaries into windows of
  `120 − prefix tokens`, with an overlap of about 20 tokens, so a sentence cut
  at one edge is whole in the next window.
- **Mapping:** each chunk keeps its record's `doc_id` plus a window number, so
  a hit is always cited as the whole section, not the fragment.

## b) Judgment record

**One JSON object per judgment,** stored as JSON Lines. **Judgments are not
ingested into the index while the app is "statutes only".** This record
fixes the shape for later; scraped judgments stay staged.

| Field | Type | Meaning |
|---|---|---|
| `case_name` | string | e.g. `"Nadar Khan v. The State"` |
| `court` | string | e.g. `"Federal Shariat Court"`, `"Supreme Court of Pakistan"` |
| `year` | integer | Year of decision |
| `citation` | string or null | Neutral or official citation (e.g. "Crl.P. 187-P/2026"). Commercial law-report citations (PLD, SCMR…) are not copied from third parties |
| `topics` | list of strings | Subject tags, e.g. `["bail", "medical grounds"]`. Set by a reviewer, or by a later classifier with review |
| `source_type` | `"case_law"` | Always `case_law` |
| `source_url` | string | The court's own page or PDF |
| `source_tier` | 1 or 2 | Official court websites are Tier 1 |

Also stored for provenance, as in (a): `original_file`, `scraped_at`,
`content_hash`, and `text` (kept out of git).

### b2) Judgment records from the team's dataset (Phase C1)

**Where they live:**
- **Code:** `backend/app/kb/judgments.py`.
- **Records:** `backend/storage/kb/judgments/records/<source>.jsonl`
  (git-ignored).
- **Index:** a separate one, `backend/storage/kb/faiss_judgments.*`. It is
  not searched by the app yet.

**Fields.** All metadata comes from rules on the first pages. A field the
rules can't find is null (or an empty list), never guessed.

| Field | Type | Meaning |
|---|---|---|
| `doc_id` | string | `judgment/<source>/<first 16 hex of the file's SHA-256>` |
| `case_name` | string or null | "Petitioner v. Respondent", from the parties block or a "versus" line |
| `court` | string or null | Matched against the known courts (Supreme Court of Pakistan, Federal Shariat Court, the five High Courts, Family Court) **in the heading only** (first 800 characters, letters only, so OCR spacing like "S UPREME COURT" still matches); a lower court named later in the text is never taken as the court |
| `year` | integer or null | From "Date of hearing / decision / judgment", else the case number's year |
| `judges` | list of strings | Names from the "Present / Coram / Bench" block, else the signatures at the end; up to 5 |
| `case_number` | string or null | e.g. "Civil Petition No. 1234 of 2022", "Crl.P. 187-P/2026". For the parquet dataset, when the rules find none, it is taken from the row's file id (e.g. `C.A.10_2021.pdf`) and `case_number_from` says so |
| `citation` | string or null | **Neutral or court citation only** (e.g. "2024 SCP 15"). Publisher citations (PLD, SCMR, YLR…) are never stored as the citation; any seen are listed in `report_citations_seen` |
| `topics` | list of strings | Rule-based keywords, each needing at least 2 mentions in the text: family, dower, khula, talaq, dissolution, nikah, custody, guardianship, maintenance, bail, murder, contract, property, constitutional. `custody` and `maintenance` match only the family sense (custody of a minor / hizanat; maintenance of a wife or minor / nafqa), not criminal custody |
| `paragraphs` | list of `{n, text}` | The judgment's own numbered paragraphs (`n` = its number; `0` = the heading, parties and bench). Without numbering: blank-line blocks numbered 1, 2, … |
| `source_type` | `"case_law"` | Always |
| `source` | string | The dataset's name, as given to the inventory script |
| `source_tier` | `2` | A team-supplied dataset, not fetched from a court website |
| `source_url` | null | Unknown for the supplied files |
| `original_file` | string | The file's path (or `archive.zip!member`). **Large files are not copied into the repository** |
| `file_sha256` | string | SHA-256 of the original file's bytes |
| `content_hash` | string | SHA-256 of the whitespace-normalised text |
| `provenance_note` | string | Always "dataset supplied by the team; original source and licence to be confirmed" |
| `status` | `"staged"` | Not shown to users until reviewed |
| `quality` | object | `chars`, `near_empty`, `needs_ocr`, `law_report`, `exclude` (the reason, or null) |

**Reading the datasets** (`scripts/kb/inventory_judgments.py`, read-only,
nothing copied): folders, `.zip` archives (read member by member) and
`.parquet` files. From a parquet only the text and metadata columns are read
(`text` / `judgment` / `content` / `body`, `case_details`, `citation_number`);
its embedding column is never loaded. The row's file id (e.g.
`C.A.10_2021.pdf`) becomes part of `original_file` and fills `case_number`
and `year` when the rules find none (`case_number_from: "dataset file id"`).

**Topics** are rule-based keywords with at least 2 mentions. The family
topics count only the family sense: `custody` is custody of a minor or child
(or *hizanat*), not custody of an accused; `maintenance` is maintenance of a
wife or minor (*nafqa*), not maintenance of a building or of law and order.

**Excluded from the index (kept in the records with the reason):**
- **Near-empty:** under 1,500 characters.
- **Needs OCR:** most pages have no text layer.
- **Duplicates:** the same text, or the same case number (its digits) and
  year. Only when neither copy has a case number: the same case name and year.
- **Law-report copies:** a publisher's citation (PLD, SCMR, YLR…) in the
  first 300 characters plus headnotes (including the "(a) … ---" style).
  A whole source can be marked with `inventory_judgments.py --law-reports`.
  These are listed separately, not indexed.

**Pilot** (`scripts/kb/build_index_judgments.py --pilot 400`): duplicates
*across* sources are removed first (same case number and year; the copy with
the most metadata is kept), then family-law judgments, then a round-robin by
year that prefers judges not yet in the pilot.

**Cross-source overlap.** The two team datasets largely hold the same
Supreme Court judgments: 1,073 of the parquet's 1,317 numbered judgments
match a judgment in the txt archive by case number and year. Within one
dataset these are excluded as duplicates; across datasets they are merged
when the pilot is chosen and in the Knowledge Base list (C2), so a case is
never shown or indexed twice. 2,554 distinct usable judgments remain of
3,739 usable records.

**Chunks.** Windows of at most 120 tokens (the embedding model's tokenizer)
from **one paragraph**, with the prefix
`"<case_name> (<court>, <year>) - para <N>:"` counted inside the 120. A hit
cites the judgment and the paragraph number.

### b3) Judgments in the app (Phase C2, `JUDGMENTS_V2`)

Off by default; set at launch (`$env:JUDGMENTS_V2 = "true"`). Off, the app
is exactly as before: no judgment endpoints (404), Research is statute-only,
Chat's prompt and replies are unchanged.

| Setting | Default | Meaning |
|---|---|---|
| `JUDGMENTS_V2` | `false` | The switch |
| `JUDGMENTS_INDEX_PATH` | `./storage/kb/faiss_judgments.faiss` | The index the app searches. Metadata: `<stem>_meta.json` next to it (or `JUDGMENTS_METADATA_PATH`). Separate from the builder's `KB_JUDGMENTS_INDEX_PATH`, so a dev copy can be searched while a build runs |
| `JUDGMENTS_MIN_SCORE` | `0.50` | Research: a judgment is listed if its best paragraph reaches this |
| `JUDGMENTS_TOP_K` | `5` | Judgments per Research search |
| `JUDGMENTS_CHAT_K` | `3` | Judgment paragraphs given to the chat model |
| `JUDGMENTS_SHOW_MIN` | `0.55` | Chat: weaker paragraphs are neither shown nor sent to the model |

**Index loading** (`app/kb/judgment_search.py`): reloaded when the index or
metadata file's modified time or size changes. While a file is missing,
unreadable, or the two don't match (vector count differs from chunk count:
a build still writing), search returns nothing and the rest of the app works.
`/health` reports `judgments_v2`, `judgment_chunks` and `judgments` (None
when off, 0 while the index isn't usable).

**Search:** embed the query, keep the **best paragraph per judgment**, drop
those under the minimum score, top K. A hit carries `doc_id`, the display
name, court, year, case number, paragraph number, the matched text and the
score.

**Display name.** The case name, unless it is weak: missing, under 8
characters, containing "…", opening with "(" or a footnote number, starting
with "Petitioner", or carrying a law-report citation (then the rules picked
up a precedent the judgment cites). A weak name is replaced by
`"<case number> (<court>, <year>)"` (or `"Judgment (<court>, <year>)"` with
no number). The same name is used in the prefix shown to the model; the
indexed chunk text keeps its original prefix, so vectors already built stay
valid. Across the 2,554 listed judgments, 1,227 use the case-number name and
172 have neither name nor number.

**Endpoints** (read-only, any signed-in user, from
`storage/kb/judgments/records/*.jsonl`, never the database):
- `GET /api/v1/kb/judgments`: counts (listed, in the index, excluded by
  reason), courts, years, topics, and a paginated list (`q` over name, case
  number and judges; `court`, `year`, `topic`, `indexed`, `page`,
  `page_size` up to 100).
- `GET /api/v1/kb/judgments/{doc_id}`: metadata, numbered paragraphs,
  provenance note, status, whether it is in the index.

The original file's path and the file and content hashes are never returned.

**Research** takes `scope`: `statutes` (default), `judgments` or `all`.
Judgments use `year_from`, `year_to` and `court`; category, jurisdiction and
tier are statute-only (ignored for judgments, hidden on the page). Under
`all`, statutes come first, then "Past relevant cases"; the court filter
applies to judgments only.

**Chat.** Only after the statute scope gate has passed (decided by statute
scores alone; thresholds unchanged), up to `JUDGMENTS_CHAT_K` paragraphs
scoring at least `JUDGMENTS_SHOW_MIN` are added to the prompt after the
statute authorities, as **"Reported cases (context only)"**, each with name,
court, year, paragraph number and text (up to 1,200 characters), with rules:
cite a case only as "Case name (Court, year), para N"; state only what that
paragraph says; never invent a holding; never use a case in place of a
statute.

**Grounding check** (`app/ai/citation_check.py`, `judgments=`): a case the
answer names must match a retrieved judgment, by its party names or its case
number and year; otherwise the sentence is removed ("not among the cases
retrieved for this answer"). A paragraph number given for a retrieved case
must be the one retrieved; otherwise it is marked "(unverified)" and listed
in the closing note. Publisher citations (PLD, SCMR…) are always removed.
The judgments are stored with the reply's citations as `kind: "case_law"`
(not numbered and not counted for the weak-match note) and returned as
`case_law`, shown under Sources as "Case law" with a link to the judgment.

### b4) Scraped laws and judgments (Phase C3, `SCRAPED_V2`)

**Sources:** the three verified ones in `scripts/scraping/sources.json`:
Pakistan Code (cap 120; the Acts its category listings name that we don't
hold come first), Khyber Pakhtunkhwa Code (cap 60) and Federal Shariat Court
leading judgments (cap 100). Same politeness as before: the identified
User-Agent (`LegalEase-FYP`, i228795@nu.edu.pk), 2 s between requests,
robots.txt respected. No database: everything is a file under
`backend/storage/kb/scraped/` (git-ignored).

| Path | What |
|---|---|
| `originals/<source>/<sha16>.pdf|html` | Every listing page, law page and PDF, byte for byte |
| `originals/manifest.jsonl` | Per file: source, URL (and the URL requested, if redirected), role, fetch date, SHA-256, size, path |
| `records/statutes/<slug>.jsonl` | Section records (§ a) |
| `records/judgments/<source>.jsonl` | Judgment records (§ b2) |
| `quarantine/<source>/<id>.json` | Rejected items: reason, URL, title, a text sample, the original's path |
| `state.json` | Per URL: text hash, outcome, fetch date, listing metadata |
| `update_log.jsonl` | One line per source per run (`scrape`), per rebuild (`index`), per `--reparse` |

**Statute records** use the § a schema plus `document_type` (Act,
Ordinance, Order…) and `amendments` (amending laws named in the text's
footnotes, e.g. "Subs. by the … Act, 2016"). Title: the law's own short
title ("This Act may be called …") when its text gives a clean one,
otherwise the tidied listing title (a KP listing title can name another
document). Year: the title's. `jurisdiction` Pakistan or KP; `source_tier`
1; `source_url` the law's page; `scraped_at` the fetch date;
`original_file` the saved PDF; `status` `under_review` (staged, not
reviewed) or `repealed` when the listing says so; `provenance_note`
"Downloaded from the … website (URL) on DATE; staged, not yet reviewed. N
of M sections found."

**Judgment records** use § b2 with `court` "Federal Shariat Court",
`source_tier` 1, `source_url` the PDF on the court's site, a real
provenance note, `fetched_at` and `scraped: true`. When the parties can't
be read cleanly ("PETITIONER v. 1"), the court's own listing title is the
case name ("Khulla (Shariat Petition No.16-I of 2022 …)").

**Validation and quarantine** (never indexed): no text layer on most pages;
near-empty text (statutes under 300 non-space characters, judgments under
1,500); garbled text (letters under 55% of characters, or over 35% of words
single letters); a statute with no recognisable sections (none found, or
under half of those its numbering implies); a missing title or year; a
law-report copy; the same text twice in one run. **Already held** (skipped,
logged): a core law (by title), or text identical to an item staged in an
earlier run. **Unchanged**: same URL, same text hash as last time.

**Index:** `faiss_scraped.*` (statute sections) and
`faiss_scraped_judgments.*`, built by `scripts/kb/build_index_scraped.py`
with the faiss_v2 pattern (vector cache by chunk text, saved every 1,000,
`--budget`); the build refuses the paths of faiss_v2, faiss_judgments and
the old index. A scraped Act that the old index also holds (same normalised
title, or the category map's match for the scraped page) has its old-index
passages left out of search (manifest `excluded_v1_sources`), as the core
laws' are.

**With `SCRAPED_V2` on:** Research and Chat also search faiss_scraped,
merged by score; scraped judgments join the judgment search (with
`JUDGMENTS_V2` on too); the Knowledge Base lists scraped laws and judgments
with a "Scraped" badge, source link, fetch date and status, and shows
"Sources and updates" from `GET /api/v1/kb/updates`; Research's "Sources
checked" line reads the update log (each source's latest check), not the
database. Off: none of this, and "Sources checked" reads the database as
before.

### b5) Document Analysis reasoning (Phase C4, `REASONING_V2`)

Response of `POST /documents/{id}/analyze` with the flag on: two more keys,
`reasoning` (or null) and `reasoning_error` (a plain-language reason when
null). Saved with the analysis as an extra `reasoning` key inside
`document_analysis.identified_clauses` (no migration). Off: neither key, and
the saved row is unchanged. Code: `backend/app/ai/reasoning.py`.

`reasoning`: `document_type`, `issues[]` (each may carry `related_cases`),
`arguments{party: []}`, `court_reasoning[]` (with `step`),
`holding_or_outcome`, `statutes_cited[]` (`act`, `section`, `status`
verified / not_found / not_checked, `kb_record_id`, `kb_law_id`, `heading`),
`strong_points[]`, `weak_points[]`, `risks[]`, `open_questions[]`; every
item has `text`, `evidence` (verbatim quote), `verified`, optional `flags`.
Plus `counts` (returned, kept, dropped, dropped_reasons, flagged, statutes),
`coverage` (partial, note, tokens), `related_cases_note`, `disclaimer`
("AI-assisted analysis; verify against the original").

### b6) Query hints and the consequence rule (Phase C5)

**Query hints** (`backend/storage/kb/query_hints.json`, committed;
`app/kb/query_hints.py`): with `KB_V2` and `QUERY_HINTS` on, a question
containing a trigger (whole word or phrase) and none of its "unless" words gets
the hint's search terms appended before embedding. No hints for a question
naming another country's law. Terms name Acts, sections and procedural words,
never conclusions (a test bans words like void, entitled, must). Evaluated in
`docs/query_hints_eval_2026-10-07.md`: 25/36 -> 30/36 in the top 5, none
worse, no off-topic question lifted past 0.65.

**Consequence rule** (with `KB_V2` on): the chat prompt says not to call
anything void, invalid, illegal, unlawful, unenforceable or punishable, or give
a penalty, unless a passage says so; when a passage only requires something,
say what it requires and stop. The citation check flags any such term the
passages don't contain, and any penalty figure ("2 years") they don't state.

### b7) Every law at section level (Phase C7)

**Corpus:** the old index was built from `data/processed/statutes/legal_statutes_corpus.json`
(main folder, read-only): 901 documents (894 Pakistan Code PDF texts, 7 section tables),
37,392,219 characters.

**Sectioning** (`scripts/kb/build_records_all.py`, same sectioner and record builder as the core laws):
kept when the law has a title, a year, at least one numbered section and at least 70% of the
sections its numbering or contents list implies. Result: **825 laws, 23,879 section records**
in `backend/storage/kb/records_all/` (git-ignored; `_report.json` lists every document with its
outcome). Skipped: 40 copies of the 35 core laws, 6 laws held as scraped laws, 3 second corpus
copies. Left in the old index only (27): 17 below 70% (e.g. Railways Act, 1890: 97 of 148), 8 with
no numbered sections (e.g. Police Order, 2002; Industrial Relations Act, 2008), 2 with no year.
Title: the Pakistan Code listing's clean title when the category map matched the copy, else the
law's own short title, else the tidied corpus title. Jurisdiction from the title (Punjab, Sindh,
KP, Balochistan, ICT; otherwise Pakistan); community laws (Hindu, Sikh) gated as in B3; category
from the listing (463 laws) or the overrides; source "LegalEase corpus (Pakistan Code-derived; …)",
tier 1 when listed, status from the listing; provenance names the corpus title and the detection.

**Index:** `faiss_v2_all.*` = the 35 core laws + records_all: 27,056 records, **99,055 chunks**
(<=120 tokens with the prefix), of which 87,362 still need a vector (the core laws' and a 500-chunk
test batch are cached): about **91 minutes** on the laptop at 16 chunks/s, a few minutes on a Colab
GPU (`scripts/kb/colab_embed.py`). faiss_v2 is never touched: search uses faiss_v2_all only when both
its files exist (the builder writes them only when every chunk has a vector), and leaves out the
old-index passages of all 860 laws it holds (`excluded_v1_sources`). `/health` reports `v2_index`
("all" or "core") and that index's chunk count; the Knowledge Base page shows the laws by set.

**Colab round trip** (checked on 500 chunks, CPU): the export's keys are the builder's
`vector_key`; the script's `.npz` files load in `VectorCache` unchanged; vectors are float32,
normalised, and identical to the app's `embed()` (cosine 1.000000); with the file in the cache the
builder's to-embed count dropped by exactly 500.

### b8) Accuracy pass (Phase C8)

- **Hybrid retrieval** (`app/kb/lexical.py`, `HYBRID_SEARCH`): BM25 over each section's heading (x3),
  title, text and its own number ("sec302"), with a glossary of statutory terms of art (qatl/murder,
  talaq/divorce, mehr/dower ...), fused with the vector ranking by reciprocal rank fusion; relevance
  stays the cosine score, and a section found only by its words needs 0.40.
- **Query hints** carry `exact_sections` ([law, section], resolved against the records when loaded)
  as a third ranking; triggers are word sets, never a question's phrase (a test checks no three-word
  sequence of a hint is in any evaluation question).
- **Chat:** full section text (<=700 tokens, top 4); after the 0.65 gate passes, sections in the
  hybrid top 5 down to 0.55 join (`CHAT_SUPPORT_MIN`); refusals carry no sources or cases; a
  foreign-law question not naming Pakistan is refused before retrieval.
- **Repealed laws:** status from the Pakistan Code title; left out of Chat and Research by default
  (`include_repealed`), labelled when named.
- **Colab steps (all three indexes):** `python ../scripts/kb/export_for_colab.py` writes
  `backend/storage/kb/colab/chunks_for_colab.jsonl`; embed it with `scripts/kb/colab_embed.py` on a
  Colab GPU; copy the `.npz` files into `storage/kb/vector_cache/`, `vector_cache_scraped/` and
  `vector_cache_scraped_judgments/`; then run `build_index_v2_all.py --budget 0` and
  `build_index_scraped.py --budget 0`.
- Results by set: `docs/eval/c8_report.md`.

## Final numbers and what is not done (2026-10-07)

| What | Number | From |
|---|---:|---|
| Core laws (section records) | 35 laws, 3,177 records | `backend/storage/kb/records/*.jsonl` |
| Core index (faiss_v2) | 11,193 chunks | `faiss_v2_meta.json` |
| Scraped laws (pilot, caps 10) | 20 laws (Pakistan Code 10, KP Code 10), 589 records | `storage/kb/scraped/records/statutes/` |
| Scraped index (faiss_scraped) | 2,400 chunks; 6 old-index copies replaced | `faiss_scraped_meta.json` |
| Judgments indexed (pilot) | 400 judgments, 64,322 chunks (complete, 2026-10-07) | `faiss_judgments_meta.json` |
| Judgments listed (Knowledge Base) | 2,554 distinct usable (3,739 usable records, 486 excluded) | `storage/kb/judgments/records/` |
| Scraped FSC judgments | 10 judgments, 5,593 chunks | `faiss_scraped_judgments_meta.json` |
| Scraping sources (last run) | Pakistan Code, KP Code, Federal Shariat Court: 10 fetched each, 30 new, 0 quarantined, 0 errors | `storage/kb/scraped/update_log.jsonl` |
| Query hints | 7 (talaq, khula, dower, maintenance, custody, inheritance, nikah registration) | `storage/kb/query_hints.json` |
| Retrieval, 36 questions, top 5 | 25/36 without hints, 30/36 with; none worse | `docs/query_hints_eval_2026-10-07.md` |
| Backend tests | 603 passing | `pytest app/tests` |

**Not done:**

- **Scraping:** only the 10/10/10 pilot has been fetched; the full run (caps 120 / 60 / 100) and the weekly task
  (`register_weekly_task.ps1`) are ready but not run or registered. Supreme Court and Lahore High Court
  block crawlers; the other courts and provincial codes need their own parsers. Migration a3c5e7f90b12 is
  still not applied (file staging only).
- **Judgments:** 400 of the 2,554 distinct usable judgments are indexed (the pilot). The dataset's source and
  licence are unconfirmed, so all judgments are staged, not reviewed. 1,227 are shown by case number because
  their party names weren't read cleanly; 172 have neither name nor number. The Supreme Court PDF archive
  (`archive__4__1.zip`) was not found.
- **Retrieval:** G03, G13, G20, G22, G25 and G26 still miss their section in the top 5 (contract formation,
  the qatl-i-amd definition, QSO attestation, writ jurisdiction, declaratory suits, minors' contracts). Query
  hints cover family law only, in English only.
- **Grounding:** the quote check (reasoning) and the consequence check (chat) work on words: they prove a
  quote or a term is in the source, not that the conclusion drawn from it is right, nor who a penalty
  applies to (MFLO s.5(4) punishes the person who fails to report a marriage, not the spouses).
- **Reasoning layer:** tested with a mocked model only; no live Groq run yet. With the summary in the same
  minute, Groq's 8,000 tokens/minute often means one 429 and a back-off. The saved reasoning (inside
  `identified_clauses`) isn't shown again after the page is left.
- **Browser:** the C2–C5 screens (Judgments tab, Research switch, Case law sources, Sources and updates,
  Reasoning tab) passed lint and build but haven't been clicked through end to end.

## c) Source whitelist and tiers

| Tier | Sources | Ingested? |
|---|---|---|
| **1** | Pakistan Code (pakistancode.gov.pk); National Assembly (na.gov.pk); official provincial legislation portals (Punjab Code, Punjab Laws, Sindh Laws, KP Code, Balochistan Code); official court websites (Supreme Court, High Courts, Federal Shariat Court) | Yes, once a source is verified in `scripts/scraping/sources.json` and its robots.txt allows it |
| **2** | Official ministries and commissions: Ministry of Law and Justice, Law and Justice Commission of Pakistan, Senate of Pakistan | Yes, for documents the Tier 1 sources don't carry |
| **3** | Secondary commentary: blogs, law-firm articles, unofficial compilations, commercial publishers | **No.** Never ingested |

**Ranking:**
- When two passages match about equally, the Tier 1 passage ranks first.
  The exact boost is set and measured in a later phase.
- A Tier 2 copy of an Act that Tier 1 also carries is not ingested twice.

**Pakistan Code notice, required in the UI.** Wherever the app shows
Pakistan Code text (chat sources, research results, the research detail
page), it must show the site's own notice:

> The content on the Pakistan Code website is for information purposes only and is under review. If in doubt, refer to the original source, i.e. the relevant Gazette notification(s), which is authoritative.

The Gazette, not the website, is the authoritative text.

## d) Storage layout (additive)

```
backend/storage/
├── faiss/                         EXISTING, unchanged: the live v1 index
│   ├── legal_corpus.faiss
│   └── legal_corpus_meta.json
└── kb/                            NEW (kb-v2)
    ├── category_map.json          Pakistan Code categories -> Acts -> corpus matches (committed)
    ├── raw/                       original files exactly as fetched (gitignored)
    │   ├── pakistancode_categories/   category listing pages (Phase A)
    │   └── <source>/<act-slug>.pdf    Act PDFs (a later phase)
    ├── records/                   JSONL, one file per law (gitignored)
    │   ├── <act-slug>.jsonl       one statute section record per line
    │   ├── judgments.jsonl        staged only; not indexed
    │   └── archive/               superseded records, by date
    ├── faiss_v2.faiss             NEW index (Phase B2); never overwrites legal_corpus.faiss
    └── faiss_v2_meta.json         per chunk: record id + section fields; section texts; build manifest
```

Search uses it only with `KB_V2=true` (default false). It searches v2 first,
then v1 without the v1 chunks of any law v2 holds. Results are in the v1
shape, plus `section`, `heading`, `source_tier` and `source_url`.

**Rules:**
- **The old index is never written to.** v2 is a separate file name. Switching
  the app to it is a configuration change (`FAISS_INDEX_PATH`), made only
  after the offline evaluation passes.
- **Scraped text stays out of git:** `raw/` and `records/` are ignored, and
  only `category_map.json` is committed (titles and URLs, no law text).
- **Provenance:** every record carries `source_url`, `original_file` and
  `scraped_at`.
