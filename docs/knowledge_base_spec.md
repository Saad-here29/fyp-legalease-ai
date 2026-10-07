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
| `court` | string or null | Matched against the known courts (Supreme Court of Pakistan, Federal Shariat Court, the five High Courts, Family Court) |
| `year` | integer or null | From "Date of hearing / decision / judgment", else the case number's year |
| `judges` | list of strings | Names from the "Present / Coram / Bench" block, else the signatures at the end; up to 5 |
| `case_number` | string or null | e.g. "Civil Petition No. 1234 of 2022", "Crl.P. 187-P/2026" |
| `citation` | string or null | **Neutral or court citation only** (e.g. "2024 SCP 15"). Publisher citations (PLD, SCMR, YLR…) are never stored as the citation; any seen are listed in `report_citations_seen` |
| `topics` | list of strings | Rule-based keywords, each needing at least 2 mentions in the text: family, dower, khula, talaq, dissolution, nikah, custody, guardianship, maintenance, bail, murder, contract, property, constitutional |
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

**Excluded from the index (kept in the records with the reason):**
- **Near-empty:** under 1,500 characters.
- **Needs OCR:** most pages have no text layer.
- **Duplicates:** the same text, or the same case name and year.
- **Law-report copies:** a publisher's citation (PLD, SCMR, YLR…) in the
  header plus headnotes. These are listed separately, not indexed.

**Chunks.** Windows of at most 120 tokens (the embedding model's tokenizer)
from **one paragraph**, with the prefix
`"<case_name> (<court>, <year>) - para <N>:"` counted inside the 120. A hit
cites the judgment and the paragraph number.

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
