# Demo examples

Worked examples of LegalEase AI running on real documents, with the exact
output the system produced — for the FYP report and the panel demo.

## Example 1 — Document Analysis on an unseen Supreme Court order

**Supreme Court of Pakistan, Criminal Petition No. 187-P of 2026**
(*Nadar Khan v. The State*): a post-arrest bail order in a murder case
(sections 302/324/34 PPC), decided 21 September 2026. The Court converted
the petition into an appeal and granted bail on grounds of further inquiry
and the petitioner's age and illness.

| | |
|---|---|
| File | [`demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf`](demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf) — 19,650 bytes, 4 pages |
| SHA-256 | `91e45f1adccde11836e0dba2643a475a0d82fcc7962d563948a4c459e9635d9a` |
| Run | Uploaded and analysed through the web app (Documents → Analyse) on 2026-09-26, twice; both runs produced identical entities |
| Text extracted | 6,856 characters (digital PDF, no OCR needed) |
| Full API response | Original run: [`analysis_response.json`](demo/crl_p_187_p_2026/analysis_response.json) · After the two fixes below: [`analysis_response_after_fixes.json`](demo/crl_p_187_p_2026/analysis_response_after_fixes.json) |

**Why it counts as unseen.** The NER model was trained on the LHC and SCP
courtroom datasets. This order is dated September 2026, and none of its
distinctive strings — `Nadar`, `187-P`, `Mandokhail`, `Gigyani`, `Lund` —
occur anywhere in the training, validation or test files. The model has
never seen this document or its parties.

**How the result was checked.** There are no gold annotations for this
document; every verdict below is a manual line-by-line comparison against
the order's text (2026-09-26). The reconstructed API response was
confirmed identical to what the app returned: the NER step is
deterministic, and re-running it on the stored text reproduced the stored
entities exactly.

### Part A — Extracted entities (legal NER model)

These come from LegalEase's own fine-tuned model, not the language model.
The table is the **original run**; the two rows marked *found → fixed*
were corrected afterwards (see [Iteration](#iteration--errors-found--investigated--fixed)).

| Type | Extracted | Verdict |
|---|---|---|
| Dates | `10.07.2026` (×3), `21.09.2026`, `11.04.2022`, `21st Sept, 2026` | All 4 correct — every date in the order |
| Amount | `Rs.200,000/-` | Correct (bail bond) |
| Court appealed from | `Peshawar High Court, Peshawar` (×2) | Correct |
| Case appealed from | `Cr.MB No.1862-P/26`, `Cr.MB. No.1862-P/2026` | Correct (the High Court bail application, written two ways in the order) |
| Statutory reference | `sections 302/324/34 PPC` | Correct |
| Organisation | `SUPREME COURT OF PAKISTAN` | Correct |
| Cited court | `Trial Court` | Correct |
| Approved for reporting | `Approved` | Correct |
| People — judges | `Jamal Khan Mandokhail`, `Aqeel Ahmed Abbasi` (×2) | Correct |
| | `Naeem Akhter` | Partial — surname "Afghan" (on the next token) missed |
| People — parties & victims | `Nadar Khan` (petitioner), `Zafar Khan` (complainant), `Saadullah` (×4, deceased), `Zardali Khan` (×2, deceased), `Siraj` (co-accused) | Correct |
| People — counsel | `Mr. Shabbir Hussain Gigyani`, `Mr. Altaf Khan`, `Mr. Zulfiqar Ahmed Bhutta`, `Syed Rifaqat Hussain Shah` | Correct |
| | `KP Tahir Khan` | Partial — "KP" belongs to the line above ("AAG KP"). **Found → fixed:** now `Tahir Khan` |
| People — staff | `Hamid/*` | Correct under the dataset's convention (stenographer initials are tagged as a person in the SCP data) |
| Places | `Lund Khwar, District Mardan`, `Islamabad` | Correct |
| | `Lund`, `Police Station` | Fragments of the police-station name "PS Lund Khawar, Mardan" |
| Errors | `Khawar Mardan` tagged as a **person** | Wrong — part of the police-station name. **Investigated, not fixed** (model limitation) |
| | `Criminal Petition No.187-P of 2026` as *case appealed from* | Wrong type — it is this case's own number. **Found → fixed:** now labelled as this case's number (`caseno`) |
| | `FIR No.360/22` as *case appealed from* | Wrong type — it is the FIR number (the FIR type was dropped from the model's output because it scored 0 F1 in training) |
| Missed | The respondent, "The State through AG, Khyber Pakhtunkhwa"; the "Standing Medical Board" | Not extracted |

| Tally (33 unique entities) | Correct | Partial | Wrong | Notable misses |
|---|---:|---:|---:|---:|
| Original run | 26 | 3 | 4 | 2 |
| After the two fixes | **28** | 2 | 3 | 2 |

The original run is in line with the model's held-out test F1 of 0.784
and the 0.843 precision measured on a rebuilt SCP judgment (see
[ner_training_results.md](ner_training_results.md)).

What the response lists at the top of the panel (original run):

- **Parties (16):** Saadullah, Aqeel Ahmed Abbasi, Zardali Khan, SUPREME
  COURT OF PAKISTAN, Jamal Khan Mandokhail, Naeem Akhter, Nadar Khan,
  Mr. Shabbir Hussain Gigyani, Mr. Altaf Khan, KP Tahir Khan, Khawar
  Mardan, Mr. Zulfiqar Ahmed Bhutta, Syed Rifaqat Hussain Shah, Siraj,
  Zafar Khan, Hamid/*
- **Dates (4):** 10.07.2026, 21.09.2026, 11.04.2022, 21st Sept, 2026
- **References (7):** Criminal Petition No.187-P of 2026, Peshawar High
  Court, Peshawar, Cr.MB No.1862-P/26, Cr.MB. No.1862-P/2026, FIR
  No.360/22, sections 302/324/34 PPC, Trial Court

After the fixes the only change to these lists is `KP Tahir Khan` →
`Tahir Khan` under Parties. The case number stays in References, since it
is still a reference; only its type changes to `caseno`.

"Parties" means every person or organisation named — judges, counsel and
victims included — not only the litigants. That is how the model's
person/organisation types work, and it should be described that way in
the demo.

### Iteration — errors found → investigated → fixed

The review above found three NER errors. Each was investigated before any
change (2026-09-26); they turned out to have three different causes, so
they got three different responses.

| Error | Suspected cause | What the evidence showed | Outcome |
|---|---|---|---|
| `Khawar Mardan` tagged as a person | Chunk boundary splitting the place name | **Not a chunking issue.** The whole name sat inside one chunk, 73 characters from its end. The model's own labels changed partway through the name: `Lund` place 0.71, `Khawar` person 0.67 (2nd choice place 0.15), `Mardan` person 0.81. Tagged with only the counsel block around it, the model got it right ("Lund Khawar Mardan", place, 0.79), so this is uncertainty on a rare place name that shifts with context. Forcing valid B-/I- sequences made it worse (the whole name became a person). | **Left as a documented model limitation.** The fix is more training examples of place names like this, not code. |
| `KP Tahir Khan` | Line breaks lost during chunking | **Partly right.** Words are split on whitespace, so a line break reaches the model as a space, and the entity was literally `KP⏎Tahir Khan`. But the model also chose to tag `KP` as the start of a person (0.83). Tagging line by line fixed it but split wrapped names (`Mardan` separated from `Lund Khawar`), and this PDF wraps text down to one word per line. | **Fixed with a narrow rule:** when a person/respondent entity crosses a line break and one side is only a 2–3 letter all-caps abbreviation (KP, AAG, SI), that side is trimmed. Citations such as `PLD⏎2015` and single initials are never touched. |
| Own case number labelled *case appealed from* | A post-processing heuristic mislabelling it | **No such heuristic existed.** Post-processing only merged the LHC/SCP spellings; the model predicted `appealcaseno` itself, at low confidence (0.29). The cause is the training data: SCP writes a judgment's own number in capitals ("CIVIL APPEAL NO.1074 OF 2009", labelled `caseno` 333 times, 156 of them right after the bench list as here), and mixed-case "Criminal Petition No." appears only 9 times, never as the judgment's own number. Rewriting just that line in capitals made the model answer `caseno`. | **Fixed with a heading rule:** a case number in the document's heading (before the "Against the judgment …" line or the ORDER/JUDGMENT title, within the first 2,000 characters) is the document's own case. The lasting fix is to add mixed-case copies of training sentences in a future retrain. |

**Verification of the two fixes:**

- **Targeted errors resolved.** Re-running this order through the live API
  (fresh upload, HTTP 200, 8.4 s): `Criminal Petition No.187-P of 2026` is
  now `caseno` and `KP Tahir Khan` is now `Tahir Khan`.
- **No regressions.** Before/after entity sets were compared on three
  documents. On this order the only differences are the two targeted
  entities. On `audit_test.pdf` (19 entities) and the rebuilt SCP judgment
  used in [ner_training_results.md](ner_training_results.md) (89
  entities) the entity sets are identical.
- **Tests.** 9 new unit tests cover both rules, including the cases they
  must leave alone: citations, single initials, ordinary wrapped names,
  body text after a missing heading. 88/88 backend tests pass.

Code: `trim_line_break_abbreviation` and `relabel_own_case_number` in
`backend/app/ai/ner.py`.

### Part B — AI summary (language model)

Generated by `openai/gpt-oss-120b` via Groq from the document text. The
key clauses and risk flags below are parsed from sections 4 and 5 of this
summary.

**Plain-language summary (verbatim):**

> The Supreme Court of Pakistan heard a criminal petition filed by Nadar
> Khan, who was denied bail by the Peshawar High Court on 10 July 2026.
> Khan, 78 years old and suffering from hypertension, diabetes and ischemic
> heart disease, argued that his serious health problems and the lack of
> any weapon recovered from him warranted release on bail. The Court agreed
> that the lower courts had not properly considered the need for further
> inquiry into the FIR and the petitioner's medical condition.
> Consequently, the Supreme Court set aside the High Court's order and
> granted post-arrest bail, directing Khan to furnish a bail bond of
> Rs 200,000 with an equal-value surety to the trial court.

This is accurate: age, illnesses, grounds, outcome and bail amount all
match the order.

**Key clauses (5):**

1. Grant of bail — Petitioner is released on post‑arrest bail.
2. Bail security — Must furnish a cash bail bond of Rs 200,000 together
   with a surety of the same amount.
3. Satisfaction of trial court — Bail bonds to be accepted "to the
   satisfaction of the learned Trial Court".
4. Further inquiry — The Court notes that the facts of the FIR require
   additional investigation; the matter will continue in the trial court.
5. Medical consideration — The Court recognized the petitioner's serious
   health conditions as a factor in granting bail.

**Risk flags (6):**

1. No explicit bail conditions (e.g., surrender of passport, regular
   reporting to police, restriction on travel, prohibition on contacting
   witnesses).
2. No time‑limit or review provision for the bail.
3. No provision for medical treatment in custody or guarantee that required
   specialised care will be provided if the petitioner is later re‑arrested.
4. No forfeiture clause specifying the consequences if the bail bond or
   surety is not honoured.
5. No mention of right to appeal the bail order (though standard under
   CrPC, it is not restated).
6. Absence of a clause on the surrender of the firearm (if any) or on the
   recovery of the alleged weapon.

**Errors in the language-model output** (found on manual review — worth
knowing before the demo):

- **Wrong complainant.** The summary's parties table names *Zulfiqar Ahmed
  Bhutta* as the complainant. He is the complainant's **counsel**; the
  complainant is **Zafar Khan**. The NER model tagged both as people but
  doesn't assign roles, so it neither causes nor catches this.
- **Wrong office.** "AG, Khyber Pakhtunkhwa" is expanded to
  *Attorney*-General; for a province it is the **Advocate**-General.
- **Small embellishment.** "Cash bail bond" — the order says "bail bonds …
  with one surety", not cash.
- **Risk flags don't fit a judgment.** The summary prompt asks for "risk
  flags or missing standard clauses", which suits contracts. On a court
  order it produces generic "missing clause" items, some legally doubtful:
  an order isn't expected to restate appeal rights. These are best
  presented as "points to review", not risks the order contains.

### Talking points for the panel

- **Two independent AI components, shown separately.** The entities come
  from a model the team fine-tuned (DistilBERT on LHC + SCP judgments);
  the summary comes from a general language model. The UI labels each
  source, so a user knows which output came from which system.
- **Generalises to a new document.** A 2026 order that appears nowhere in
  the training data: all dates, the amount, the court, case numbers,
  statute and nearly every name extracted correctly.
- **The two components catch different things.** NER lists every person
  exactly as written in the order. That makes the language model's
  wrong-complainant error checkable against the source text, rather than
  having to trust the summary.
- **Errors are investigated, not just listed.** Three NER errors from this
  review were traced to their causes, and two were corrected with narrow,
  tested rules. The iteration section above is a good slide.
- **Known weak spots, stated up front:** boundary errors on names that run
  across line breaks (the `KP Tahir Khan` case is now handled by a rule),
  place names mistaken for people
  (`Khawar Mardan`), and no role information (who is the petitioner vs
  counsel). These match the weak categories in the training evaluation.

### Reproducing the demo

1. Start the backend (with the NER weights in
   `backend/storage/models/legal_ner/`) and the frontend.
2. Log in, open **Documents**, upload `docs/demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf`.
3. Click **Analyse**. The entities will match
   `analysis_response_after_fixes.json` exactly (the post-fix state), since
   NER is deterministic. The summary will be worded differently on each run,
   because the language model is not deterministic, so re-check it before
   quoting it live.
