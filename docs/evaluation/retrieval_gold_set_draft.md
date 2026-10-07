# Retrieval gold set: DRAFT for review

Status: **draft. Not used until you have checked it.** Companion to
[`retrieval_redesign.md`](../architecture/retrieval_redesign.md), section 7.

The expected sections are the developer's assessment, not a lawyer's.
Please correct any statute or section, and add or drop questions.

**Checked so far:**
- Every expected section was confirmed present in the corpus (2026-10-04).
- The headings were matched in the current index's text. G25 and G26 were
  checked by hand: the Specific Relief Act heading is "Discretion of Court
  as to declaration of status or right", and Contract Act s. 11 sits inside
  the glued s. 10 chunk.

**The "Today" column:**
- **live** marks results seen in a live chat during an audit.
- **raw** marks results measured offline with the user's question
  embedded as typed.
- Other rows were not measured: on 2026-10-04 Windows Application Control
  began blocking PyTorch and FAISS on this machine, so the embedding model
  can't run locally. They will be filled in by the baseline replay (A0).

**What "reaches the model" means:** the gold section's text is among the
passages sent to the chat model (top 5, at or above the threshold).

## Gold questions (26)

| ID | Question | Expected statute | Expected section(s) | Acceptable support | Today |
|---|---|---|---|---|---|
| **G01** | On what grounds can a Muslim woman obtain a decree for the dissolution of her marriage? | Dissolution of Muslim Marriages Act, 1939 | s. 2 | — | **failure**: live, not retrieved (rewrite drifted to MFLO / Family Courts Act); raw rank 1 (0.822) |
| **G02** | What is the punishment for qatl-i-amd under the Pakistan Penal Code? | Pakistan Penal Code | s. 302 | s. 300, s. 299 | **failure**: live, not retrieved; raw rank 5 (0.741, borderline) |
| **G03** | What are the essential elements of a valid contract under the Contract Act, 1872? | Contract Act, 1872 | s. 10 | ss. 11, 13, 14, 23 | **failure**: live, not retrieved; raw rank 4,366 (0.444) |
| **G04** | If a husband pronounces talaq while his wife is pregnant, when does the talaq take effect, and can she claim maintenance during that period? | Muslim Family Laws Ordinance, 1961 | s. 7 (sub-s. 5) and s. 9 | — | **failure**: live, refused; raw best MFLO chunk 0.693 |
| G05 | Can a husband marry a second wife without the permission of the Arbitration Council? | MFLO, 1961 | s. 6 | — | not measured |
| G06 | What is the procedure for talaq under the Muslim Family Laws Ordinance? | MFLO, 1961 | s. 7 | — | **works**: live (Sept 2026 audit, answered from both MFLO copies) |
| G07 | What can a wife do if her husband does not pay her maintenance? | MFLO, 1961 | s. 9 | Family Courts Act s. 5 | not measured |
| G08 | Can a grandchild inherit from the grandfather if the grandchild's father died before the grandfather? | MFLO, 1961 | s. 4 | — | not measured (README: rank 57 under the live rewrite) |
| G09 | How can a mother get custody of her minor child under the Guardians and Wards Act? | Guardians and Wards Act, 1890 | s. 25 | s. 17 | not measured |
| G10 | Which court hears suits for dissolution of marriage, dower and maintenance? | West Pakistan Family Courts Act, 1964 | s. 5 | Schedule | not measured |
| G11 | What happens at the pre-trial stage of a case in a Family Court? | West Pakistan Family Courts Act, 1964 | s. 10 | — | not measured |
| G12 | Can a wife get her marriage dissolved if her husband has not maintained her for two years? | DMMA, 1939 | s. 2 (clause ii) | — | not measured |
| G13 | How does the Pakistan Penal Code define qatl-i-amd? | PPC | s. 300 | — | not measured |
| G14 | What is the punishment for cheating and dishonestly inducing delivery of property? | PPC | s. 420 | s. 415 | not measured |
| G15 | What is the punishment for defamation under the Pakistan Penal Code? | PPC | s. 500 | s. 499 | not measured |
| G16 | What is the punishment for theft? | PPC | s. 379 | s. 378 | not measured (README: contents lookup fetched wrong sections) |
| G17 | When can bail be granted in a non-bailable offence? | Code of Criminal Procedure, 1898 | s. 497 | — | not measured |
| G18 | How is a First Information Report recorded for a cognizable offence? | CrPC, 1898 | s. 154 | — | not measured |
| G19 | What is the punishment for rape under the Pakistan Penal Code? | PPC | s. 376 | s. 375 | not measured |
| G20 | How many witnesses are required to attest a document creating a financial obligation? | Qanun-e-Shahadat Order, 1984 | **Art.** 17 | — | not measured |
| G21 | Is the right to a fair trial a fundamental right in Pakistan? | Constitution of Pakistan | **Art.** 10A | — | not measured |
| G22 | What is the writ jurisdiction of a High Court? | Constitution of Pakistan | **Art.** 199 | — | not measured |
| G23 | What compensation can be claimed for breach of contract? | Contract Act, 1872 | s. 73 | s. 74 | not measured |
| G24 | How is a sale of immovable property made under the Transfer of Property Act? | Transfer of Property Act, 1882 | s. 54 | — | not measured |
| G25 | Can a person file a suit for a declaration of their title to property? | Specific Relief Act, 1877 | s. 42 | — | not measured (a lawyer answer in the 78-question set cites it) |
| G26 | Can a minor enter into a valid contract? | Contract Act, 1872 | s. 11 | s. 10 | not measured |

**Mix:**
- 4 known failures (G01–G04);
- 1 known working question (G06);
- 21 others across family, criminal, evidence, constitutional and civil
  law.

Nine statutes are covered: the five core family and criminal statutes, plus
the Contract Act, QSO, Constitution, Transfer of Property Act and Specific
Relief Act.

## Off-topic and foreign questions (15): must be refused

These are used for the threshold recalibration (design section 7.6). They
are also used for the "off-topic still refused" acceptance check. The 78
lawyer questions' own foreign items (the Nigerian CAC and Thailand
questions) are added to this set when the gold labels for the 78 are
written.

| ID | Question | Kind |
|---|---|---|
| O01 | What is the capital of Australia and how many people live there? | off-topic (audit A4) |
| O02 | What is the weather forecast for Lahore tomorrow? | off-topic |
| O03 | Give me a recipe for chocolate cake. | off-topic |
| O04 | Who won the Cricket World Cup in 1992? | off-topic |
| O05 | How do I reset my Wi-Fi router? | off-topic |
| O06 | What is the best smartphone under 50,000 rupees? | off-topic |
| O07 | Explain how photosynthesis works. | off-topic |
| O08 | Write a poem about the monsoon. | off-topic |
| O09 | How many calories are in a plate of biryani? | off-topic |
| O10 | What is the exchange rate of the US dollar today? | off-topic |
| O11 | How do I register a company with the Corporate Affairs Commission in Nigeria? | foreign law |
| O12 | Is a verbal contract enforceable in Thailand? | foreign law |
| O13 | How do I file for divorce in California? | foreign law |
| O14 | What is the punishment for murder under the Indian Penal Code? | foreign law (close to G02 on purpose) |
| O15 | How do I apply for a UK student visa? | foreign / administrative |

## Questions for you

1. **G04** expects two sections, s. 7(5) for pregnancy and s. 9 for
   maintenance. Should "reaches the model" require both, or either?
2. **G20:** is Art. 17 QSO the right gold for attestation of financial
   documents? Art. 79 (proof of execution) may also count.
3. **G10/G07:** the Family Courts Act jurisdiction lives partly in its
   Schedule, which will be a fallback chunk. Is s. 5 alone acceptable as
   gold?
4. **O14** (Indian Penal Code murder) is deliberately close to G02. If it
   turns out to be answerable from the PPC, should that count as a false
   answer? The Pakistani provision is genuinely related.
