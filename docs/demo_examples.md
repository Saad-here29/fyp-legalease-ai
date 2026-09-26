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
| Full API response | [`demo/crl_p_187_p_2026/analysis_response.json`](demo/crl_p_187_p_2026/analysis_response.json) |

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
| | `KP Tahir Khan` | Partial — "KP" belongs to the line above ("AAG KP") |
| People — staff | `Hamid/*` | Correct under the dataset's convention (stenographer initials are tagged as a person in the SCP data) |
| Places | `Lund Khwar, District Mardan`, `Islamabad` | Correct |
| | `Lund`, `Police Station` | Fragments of the police-station name "PS Lund Khawar, Mardan" |
| Errors | `Khawar Mardan` tagged as a **person** | Wrong — part of the police-station name |
| | `Criminal Petition No.187-P of 2026` as *case appealed from* | Wrong type — it is this case's own number |
| | `FIR No.360/22` as *case appealed from* | Wrong type — it is the FIR number (the FIR type was dropped from the model's output because it scored 0 F1 in training) |
| Missed | The respondent, "The State through AG, Khyber Pakhtunkhwa"; the "Standing Medical Board" | Not extracted |

**Tally (33 unique entities):** 26 correct, 3 partial boundaries, 4 wrong;
2 notable misses. That is in line with the model's held-out test F1 of
0.784 and the 0.843 precision measured on a rebuilt SCP judgment (see
[ner_training_results.md](ner_training_results.md)).

What the response lists at the top of the panel:

- **Parties (16):** Saadullah, Aqeel Ahmed Abbasi, Zardali Khan, SUPREME
  COURT OF PAKISTAN, Jamal Khan Mandokhail, Naeem Akhter, Nadar Khan,
  Mr. Shabbir Hussain Gigyani, Mr. Altaf Khan, KP Tahir Khan, Khawar
  Mardan, Mr. Zulfiqar Ahmed Bhutta, Syed Rifaqat Hussain Shah, Siraj,
  Zafar Khan, Hamid/*
- **Dates (4):** 10.07.2026, 21.09.2026, 11.04.2022, 21st Sept, 2026
- **References (7):** Criminal Petition No.187-P of 2026, Peshawar High
  Court, Peshawar, Cr.MB No.1862-P/26, Cr.MB. No.1862-P/2026, FIR
  No.360/22, sections 302/324/34 PPC, Trial Court

"Parties" means every person or organisation named — judges, counsel and
victims included — not only the litigants. That is how the model's
person/organisation types work, and it should be described that way in
the demo.

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
- **Known weak spots, stated up front:** boundary errors on names that run
  across line breaks (`KP Tahir Khan`), place names mistaken for people
  (`Khawar Mardan`), and no role information (who is the petitioner vs
  counsel). These match the weak categories in the training evaluation.

### Reproducing the demo

1. Start the backend (with the NER weights in
   `backend/storage/models/legal_ner/`) and the frontend.
2. Log in, open **Documents**, upload `docs/demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf`.
3. Click **Analyse**. The entities will match the table above exactly, since
   NER is deterministic. The summary will be worded differently on each run,
   because the language model is not deterministic, so re-check it before
   quoting it live.
