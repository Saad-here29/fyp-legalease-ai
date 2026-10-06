# Knowledge base v2: specification (Phase A)

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
| `section` | string | Section number as printed: `"2"`, `"10A"`, `"Schedule"` |
| `heading` | string | The section heading |
| `text` | string | The section text, cleaned: footnotes, page headers and watermarks removed; amendment brackets like `3[(iia) …]` kept as text without the footnote marker |
| `source_type` | `"statute"` | Always `statute` for this record type |
| `jurisdiction` | enum | `Pakistan` (federal), `Punjab`, `Sindh`, `KP`, `Balochistan`, `ICT` |
| `category` | string or null | The Pakistan Code category, e.g. `"Family Laws"` (from `category_map.json`); null if the source has no categories or the Act isn't listed in one |
| `year` | integer | Year of the Act, from the title (the listing's act number can disagree: see the coverage report) |
| `act_number` | string or null | As listed, e.g. `"VIII of 1939"` |
| `source` | string | Publisher, e.g. `"Pakistan Code"`, `"KP Code"` |
| `source_tier` | 1, 2 or 3 | See (c) |
| `source_url` | string | The page the Act was fetched from |
| `original_file` | string | Path of the saved original under `backend/storage/kb/raw/` (PDF or HTML) |
| `scraped_at` | ISO 8601 UTC | When the original was fetched |
| `content_hash` | string | SHA-256 of the whitespace-normalised `text` (the scraper's `content_hash`), for change detection |
| `status` | enum | `current`, `under_review` or `repealed`, from the source's annotation (e.g. "(Repealed by Act XIV of 2015)", "(Under Review)") |

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
    ├── records/                   JSONL (gitignored)
    │   ├── statutes.jsonl         one statute section record per line
    │   ├── judgments.jsonl        staged only; not indexed
    │   └── archive/               superseded records, by date
    └── index/
        ├── faiss_v2.faiss         NEW index file; never overwrites legal_corpus.faiss
        └── faiss_v2_meta.json     records' doc_id per vector, plus the build manifest
```

**Rules:**
- **The old index is never written to.** v2 is a separate file name. Switching
  the app to it is a configuration change (`FAISS_INDEX_PATH`), made only
  after the offline evaluation passes.
- **Scraped text stays out of git:** `raw/` and `records/` are ignored, and
  only `category_map.json` is committed (titles and URLs, no law text).
- **Provenance:** every record carries `source_url`, `original_file` and
  `scraped_at`.
