# Family-law chat review: 8 questions (2026-10-05)

This is the Phase A diagnosis: nothing has been fixed. It covers the eight
questions from the legal-review chat session of 2026-10-05 (chat session
`cfffa61b…`, started 10:57 UTC), saved here as regression cases, with:
- the retrieval diagnosis for each question;
- where the supporting statute text sits in the index;
- the unsupported sentences in answers Q3, Q6 and Q8;
- a design, **not built**, for a family-law filter and a low-confidence note.

**How it was measured:**
- **Live index:** `backend/storage/faiss/legal_corpus.faiss`, 53,739 chunks.
- **Model:** `paraphrase-multilingual-MiniLM-L12-v2`.
- **Threshold:** `RAG_SIMILARITY_THRESHOLD` = 0.65, `RAG_TOP_K` = 5.
- **Rewrites:** regenerated once with the app's own `rewrite_search_query()`.
  That's 8 Groq calls, **3,544 tokens** (2,810 prompt, 734 completion). They
  are cached, and everything else ran offline.
- **Scripts:** `diagnose_review.py`, `show_chunks.py`, `design_checks.py`
  (kept outside the repo).

---

## 1. Test cases

"Expected support" is the statute text a correct answer should rest on,
taken from the review checklist. "Result" is our assessment against that
text, not a legal opinion.

| ID | Question | Expected support | Answer received | Result |
|---|---|---|---|---|
| CR-01 | Why is the Nikah Nama important in a dower dispute? | MFLO s.10 (dower payable on demand where the nikahnama is silent); MFLO s.5 (registration, nikahnama form) | Refused as out of scope | **Fail**: in-scope question refused |
| CR-02 | A wife claims that her dowry articles remain in the husband's possession after separation. What remedy may be available? | FCA Schedule Part I item 8 (Dowry), item 9 (Personal property and belongings of a wife); FCA s.5; Dowry and Bridal Gifts (Restriction) Act 1976 | Refused as out of scope | **Fail**: in-scope question refused |
| CR-03 | Can a spouse lawfully retain the other's personal property merely because the marriage has ended? | FCA Schedule item 9; FCA s.5 | Answered from MFLO s.9 (maintenance), the MFLO's 2021 succession sub-sections (widow's share), DMMA s.2, FCA ss.24–25; a Companies Act passage was also retrieved | **Fail**: Schedule item 9 not found; several claims unsupported (§ 4) |
| CR-04 | What is a suit for restitution of conjugal rights? | FCA Schedule item 4; FCA s.9(1a) | Said the library has no provision on restitution of conjugal rights | **Fail**: the provision exists in the index but wasn't retrieved |
| CR-05 | Why is territorial jurisdiction important in a Family Court case? | Family Court Rules 1965, r.6 (place of suing); FCA s.5 | Refused as out of scope | **Fail**. Note: the Rules are **not in the corpus** |
| CR-06 | Can a family-law advocate knowingly present false facts before the court merely to secure relief for the client? | Legal Practitioners and Bar Councils Act 1973 (misconduct); PPC false-evidence provisions | Answered from false-statement provisions of the Succession Act 1925 (probate petitions) and the Pakistan Air Force Act 1953 s.57; the Sindh Incumbered Estates Act was also retrieved | **Fail**: wrong statutes; most claims unsupported (§ 4) |
| CR-07 | A wife files a suit seeking dissolution of marriage, unpaid dower, maintenance and recovery of dowry articles. The husband denies all allegations … What should the court determine? | FCA Schedule items 1, 2, 3, 8; FCA s.5; DMMA s.2 | Refused as out of scope | **Fail**: in-scope question refused |
| CR-08 | If a wife claims unpaid dower, who must establish the relevant facts? | MFLO s.10; FCA s.17 (the QSO doesn't apply to Family Court proceedings) | Answered from Qanun-e-Shahadat Art. 18 only | **Fail**: the burden-of-proof conclusion isn't in the retrieved passage (§ 4) |

The verbatim answers are in Appendix A. Response times were 1.3–4.6 s.

---

## 2. Search diagnosis per question

### 2.1 Summary

| Q | Session outcome | Raw question: passing 0.65 | Re-run rewrite: passing 0.65 | Did the rewrite change the topic? |
|---|---|---|---|---|
| Q1 | Refused | 0/5 | 0/5 | **Drifted**: "Nikah Nama … mahr" pulled in the *Quaid-e-Azam's Mazar Ordinance* (top score 0.61) |
| Q2 | Refused | 0/5 | 5/5 | **Steered**: it added "under Muslim Family Laws Ordinance", but dowry isn't in the MFLO |
| Q3 | Answered (6 passages) | 3/5 | 5/5 | **Changed**: "retain personal property" became "movable property after dissolution (talaq) under MFLO" |
| Q4 | Answered (6 passages) | 5/5 | 5/5 | **Steered**: "under Muslim Family Laws Ordinance" dropped the raw query's restitution passages (CPC s.32, Divorce Act); the MFLO has no restitution provision |
| Q5 | Refused | 0/5 | 1/5 | No: topic kept |
| Q6 | Answered (3 passages) | 0/5 | 5/5 | Re-run: no (it added the LPBCA, which is correct). The session's rewrite must have differed (see 2.2) |
| Q7 | Refused | 5/5 (all off-target) | 0/5 | **Changed**: "dissolution" became "khula"; the denial and desertion issues were dropped |
| Q8 | Answered (1 passage) | 0/5 | 0/5 | No: topic kept |

### 2.2 The rewrite is not repeatable

Rewrites run at temperature 0.3 and the rewritten query isn't logged, so
the session's own rewrites can't be recovered. Comparing the passages stored
with each answer against the re-run:
- **Q4:** identical top 5 and scores, so it was the same rewrite.
- **Q3, Q6, Q8:** different passages, so it was a different rewrite.
  - Q8 passed with one passage at 0.6509 in the session; the re-run's best
    is 0.6400, so **today the same question would be refused**.
- **Q2, Q5:** refused in the session; the re-run would answer them (5/5 and
  1/5 passing).

Whether a question is answered or refused currently depends on the rewrite's
sampling.

### 2.3 What the 0.65 threshold did

- **It refused in-scope questions** (Q1, Q2, Q5, Q7). In each case the
  relevant family-law text exists but scores 0.44–0.63 (see § 3).
- **It let off-target passages through**:
  - Companies Act 2017 at 0.6829 (Q3);
  - Hindu Marriage Act 2017 at 0.6689 (Q4);
  - Sindh Incumbered Estates Act at 0.6834 and Pakistan Air Force Act at
    0.6501 (Q6);
  - Married Women's Property Act, Specific Relief Act and Divorce Act 1869
    at 0.66–0.73 (raw Q7, all off-target).
- In this sample, then, the score doesn't separate relevant from irrelevant
  between about 0.60 and 0.70.

### 2.4 Top 5 per question

✗ marks a passage below 0.65. Scores are cosine similarities.

#### Q1

Re-run rewrite: *Nikah Nama relevance in mahr (dower) dispute*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.4919 ✗ | i For Official Use ESTACODE (EDITION -2021 | 0.6080 ✗ | THE QUAIDIAZAM´S MAZAR (PROTECTION AND MAINTENANCE)ORDINANCE, 1971 |
| 2 | 0.4813 ✗ | THE BENAMI TRANSACTIONS (PROHIBITION) ACT, 2017 | 0.5616 ✗ | THE ZAKAT AND USHR ORDINANCE, 1980 |
| 3 | 0.4789 ✗ | THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 | 0.5386 ✗ | THE QUAID -I-AZAM’S MAZAR (PROTECTION AND MAINTENANCE) ORDINANCE, 1971 |
| 4 | 0.4785 ✗ | i For Official Use ESTACODE (EDITION -2021 | 0.5379 ✗ | THE QUAID -I-AZAM’S MAZAR (PROTECTION AND MAINTENANCE) ORDINANCE, 1971 |
| 5 | 0.4772 ✗ | THE COMPANIES ACT, 2017 | 0.5372 ✗ | THE QUAID -I-AZAM’S MAZAR (PROTECTION AND MAINTENANCE) ORDINANCE, 1971 |

Passing 0.65: raw 0/5, rewritten 0/5.

#### Q2

Re-run rewrite: *dowry articles possession after separation remedy under Muslim Family Laws Ordinance*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.6428 ✗ | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.7207 | THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 |
| 2 | 0.6233 ✗ | THE DIVORCE ACT,1869 | 0.7165 | Muslim Family Laws Ordinance, 1961 |
| 3 | 0.6092 ✗ | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.7021 | THE CHILD MARRIAGE RESTRAINT ACT, 1929 |
| 4 | 0.6035 ✗ | THE DIVORCE ACT,1869 | 0.6985 | THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 |
| 5 | 0.6007 ✗ | THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 | 0.6802 | THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 |

Passing 0.65: raw 0/5, rewritten 5/5.

#### Q3

Re-run rewrite: *possession of spouse’s movable property after dissolution of marriage (talaq) under Muslim Family Laws Ordinance*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.6872 | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.7609 | THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 |
| 2 | 0.6735 | THE CAPITAL TERRITORY TRUST ACT, 2020 | 0.7512 | Muslim Family Laws Ordinance, 1961 |
| 3 | 0.6593 | THE TRUSTS ACT, 1882 | 0.7208 | THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 |
| 4 | 0.6435 ✗ | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.7100 | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 |
| 5 | 0.6363 ✗ | THE SUCCESSION ACT, 1925 | 0.7010 | THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 |

Passing 0.65: raw 3/5, rewritten 5/5. Section lookup (contents list) would add: Muslim Family Laws Ordinance, 1961 \| 5. Registration of marriage s; Muslim Family Laws Ordinance, 1961 \| 8. Dissolution of marriage otherwise than by talaq; THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 \| 2. Grounds for decree for dissolution of marriage.

#### Q4

Re-run rewrite: *petition for restitution of conjugal rights under Muslim Family Laws Ordinance*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.7517 | THE CODE OF CIVIL PROCEDURE, 1908 | 0.7261 | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 |
| 2 | 0.7402 | THE DIVORCE ACT,1869 | 0.7124 | Muslim Family Laws Ordinance, 1961 |
| 3 | 0.7086 | THE PARSI MARRIAGE AND DIVORCE ACT, 1936 | 0.7101 | THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 |
| 4 | 0.7028 | THE CODE OF CIVIL PROCEDURE, 1908 | 0.6925 | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 |
| 5 | 0.6987 | THE DIVORCE ACT,1869 | 0.6689 | THE HINDU MARRIAGE ACT, 2017 |

Passing 0.65: raw 5/5, rewritten 5/5. Section lookup (contents list) would add: THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 \| 5. Rights to dower not to be affected.

#### Q5

Re-run rewrite: *importance of territorial jurisdiction in Family Court proceedings*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.6235 ✗ | THE INSOLVANCY (KARACHI DIVISION) ACT,1909 | 0.6717 | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 |
| 2 | 0.6211 ✗ | THE CODE OF CIVIL PROCEDURE, 1908 | 0.6491 ✗ | THE INSOLVANCY (KARACHI DIVISION) ACT,1909 |
| 3 | 0.6128 ✗ | THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 | 0.6458 ✗ | THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 |
| 4 | 0.6046 ✗ | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 | 0.6302 ✗ | THE CODE OF CIVIL PROCEDURE, 1908 |
| 5 | 0.5946 ✗ | THE GUARDIANS AND WAR DS ACT, 1890 | 0.6286 ✗ | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 |

Passing 0.65: raw 0/5, rewritten 1/5.

#### Q6

Re-run rewrite: *advocate false statements to court professional misconduct under Legal Practitioners and Bar Councils Act*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.6215 ✗ | THE QANUNESHAHADAT , 1984 | 0.6841 | Legal Practitioners & Bar Councils Act, 1973 |
| 2 | 0.6100 ✗ | THE QANUNESHAHADAT , 1984 | 0.6766 | THE PAKISTAN PENAL CODE |
| 3 | 0.6032 ✗ | Pakistan Penal Code | 0.6694 | THE PROTECTION OF PORTS (SPECIAL MEASURES) ACT, 1948 |
| 4 | 0.6025 ✗ | THE QANUNESHAHADAT , 1984 | 0.6599 | Legal Practitioners & Bar Councils Act, 1973 |
| 5 | 0.5893 ✗ | Qanun-e-Shahadat Order, 1984 | 0.6581 | THE INCOME TAX ORDINANCE, 2001 |

Passing 0.65: raw 0/5, rewritten 5/5.

#### Q7

Re-run rewrite: *khula maintenance mehr recovery dowry articles court determination*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.7267 | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.5419 ✗ | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 |
| 2 | 0.6806 | THE SPECIFIC RELIEF ACT, 1877 | 0.5366 ✗ | THE COOPERA TIVE FARMING ACT , 1976 |
| 3 | 0.6750 | THE DIVORCE ACT,1869 | 0.5348 ✗ | GOVERNMENT OF PAKISTAN REVENUE DIVISION FEDERA L BOARD OF REVENUE ***** THE CUSTOMS ACT, 1969 |
| 4 | 0.6587 | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.5335 ✗ | THE PAKISTAN ARMY ACT, 1952 |
| 5 | 0.6569 | THE DIVORCE ACT,1869 | 0.5309 ✗ | THE COURTFEES ACT, 1870 |

Passing 0.65: raw 5/5, rewritten 0/5.

#### Q8

Re-run rewrite: *burden of proof unpaid mehr wife must establish facts*

| # | Raw: score | Raw: source | Rewritten: score | Rewritten: source |
|---|---:|---|---:|---|
| 1 | 0.6212 ✗ | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.6400 ✗ | THE QANUNESHAHADAT , 1984 |
| 2 | 0.5828 ✗ | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 0.5914 ✗ | THE QANUNESHAHADAT , 1984 |
| 3 | 0.5696 ✗ | THE QANUNESHAHADAT , 1984 | 0.5914 ✗ | THE QANUNESHAHADAT , 1984 |
| 4 | 0.5496 ✗ | THE QANUNESHAHADAT , 1984 | 0.5875 ✗ | Qanun-e-Shahadat Order, 1984 |
| 5 | 0.5448 ✗ | Qanun-e-Shahadat Order, 1984 | 0.5864 ✗ | Qanun-e-Shahadat Order, 1984 |

Passing 0.65: raw 0/5, rewritten 0/5.


---

## 3. Is the supporting text in the index, and where does it rank?

### 3.1 Presence

| Statute / provision | In the index? | Chunk(s) |
|---|---|---|
| West Pakistan Family Courts Act 1964 | **Yes**, 43 chunks | Schedule Part I: #49943 (items 1–8, starting at token 130) and #49944 (items 7–9) |
| — Schedule item 4, *Restitution of conjugal rights* | **Yes** | #49943 |
| — Schedule item 2, *Dower* | **Yes** | #49943 |
| — Schedule item 8, *Dowry* | **Yes** | #49943, #49944 |
| — Schedule item 9, *Personal property and belongings of a wife* | **Yes** | #49944 |
| — s.9(1a), husband's claim for restitution in the written statement | **Yes** | #49917 |
| — s.5, jurisdiction (subject matter, by Schedule) | **Yes** | #49910 |
| — s.17, QSO and CPC (except ss.10–11) don't apply | **Yes** | #49933 |
| MFLO 1961 s.5 (registration, nikahnama form) | **Yes**, both copies | #826, #827, #49602, #49603 |
| MFLO 1961 s.10 (dower payable on demand) | **Yes**, both copies | #835, #49613 |
| Legal Practitioners and Bar Councils Act 1973 | **Yes**, 218 chunks (18 mention misconduct) | e.g. #13071, #13080 |
| Dowry and Bridal Gifts (Restriction) Act 1976 | **Yes**, 12 chunks (+1 contents list) | — |
| **Territorial jurisdiction of Family Courts** (West Pakistan Family Court Rules 1965, r.6) | **No. The Family Court Rules 1965 are not in the corpus** (no source name matches) | — |
| Territorial jurisdiction, general (CPC s.20) | Yes, but FCA s.17 excludes the CPC (except ss.10–11) from Family Court proceedings | #19813 |
| Muslim Personal Law (Shariat) Application Act 1962 | **Not found** by source name | — |

### 3.2 Rank of the supporting text

Each cell shows the best rank among 53,739 chunks: **raw question / re-run
rewrite (rewrite score)**. A passage must be in the top 5 *and* score ≥0.65
to be used.

| Provision | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 |
|---|---|---|---|---|---|---|---|---|
| FCA Schedule items 1–8 (#49943: dower, maintenance, restitution) | 20,041 / 12,333 (0.26) | 11,842 / 4,638 (0.35) | 11,159 / 4,858 (0.32) | 11,388 / 3,883 (0.38) | 5,690 / 3,999 (0.41) | 24,331 / 26,555 (0.29) | 16,568 / 19,602 (0.29) | 34,303 / 23,638 (0.18) |
| FCA Schedule items 7–9 (#49944: dowry, personal property of wife) | 26,400 / 13,244 (0.26) | 145 / 23 (0.63) | 835 / 36 (0.61) | 11,914 / 123 (0.54) | 623 / 417 (0.51) | 2,919 / 37,188 (0.23) | 235 / 131 (0.47) | 1,930 / 1,619 (0.32) |
| FCA s.9(1a) restitution claim (#49917) | 9,997 / 15,856 (0.25) | 4,149 / 6,271 (0.33) | 25,726 / 19,711 (0.23) | 6,106 / 10,977 (0.32) | 4,185 / 1,992 (0.44) | 6,881 / 8,000 (0.39) | 4,411 / 1,480 (0.40) | 1,978 / 4,023 (0.28) |
| FCA s.5 jurisdiction (#49910) | 45 / 24 (0.48) | 7,329 / 90 (0.56) | 4,282 / 72 (0.57) | 1,041 / 13 (0.65) | 16 / 5 (0.63) | 2,560 / 13,035 (0.36) | 5,161 / 2,934 (0.38) | 16,944 / 11,440 (0.23) |
| MFLO s.5 registration / nikahnama (best of 4) | 9 / 61 (0.44) | 525 / 25 (0.62) | 733 / 19 (0.64) | 9,617 / 24 (0.63) | 4,258 / 3,151 (0.42) | 8,343 / 39,461 (0.22) | 1,446 / 27 (0.50) | 7,058 / 2,245 (0.31) |
| MFLO s.10 dower (best of 2) | 19 / 8 (0.51) | 1,102 / 7 (0.67) | 2,299 / 21 (0.64) | 12,446 / 53 (0.58) | 7,933 / 5,062 (0.40) | 12,716 / 35,672 (0.24) | 2,189 / 33 (0.50) | 2,674 / 3,120 (0.29) |
| Dowry and Bridal Gifts Act (best of 12) | 1,291 / 1,100 (0.36) | 50 / 39 (0.60) | 12 / 18 (0.65) | 2,022 / 155 (0.53) | 820 / 1,122 (0.47) | 3,842 / 4,833 (0.43) | 157 / 1,420 (0.41) | 561 / 674 (0.36) |
| LPBCA, any section (best of 217) | 1,408 / 601 (0.38) | 2,893 / 845 (0.43) | 6,414 / 943 (0.41) | 420 / 495 (0.47) | 337 / 145 (0.55) | 371 / 1 (0.68) | 1,424 / 1,130 (0.41) | 1,566 / 2,426 (0.31) |
| LPBCA, misconduct (best of 18) | 3,283 / 3,882 (0.31) | 7,050 / 5,905 (0.33) | 9,937 / 3,330 (0.35) | 545 / 1,547 (0.42) | 3,631 / 3,120 (0.42) | 779 / 4 (0.66) | 1,424 / 2,839 (0.38) | 7,369 / 13,713 (0.22) |
| CPC s.20 place of suing (#19813) | 4,989 / 11,657 (0.26) | 448 / 4,038 (0.35) | 339 / 1,874 (0.38) | 377 / 9,381 (0.33) | 306 / 747 (0.49) | 1,829 / 2,730 (0.46) | 152 / 4,171 (0.37) | 2,575 / 11,673 (0.23) |
| QSO burden of proof (best of 18) | 301 / 339 (0.40) | 268 / 221 (0.51) | 863 / 188 (0.52) | 1,124 / 96 (0.55) | 2,484 / 3,734 (0.41) | 5 / 881 (0.51) | 239 / 2,021 (0.40) | 35 / 4 (0.59) |

**Read with 3.3:**
- #49943 (Schedule items 1–8, including restitution and dower) and
  #49917 (s.9(1a)) rank **1,480 or worse** for every question and query.
- #49944 (items 7–9) gets as close as rank 23 (Q2, 0.63), but never into
  the top 5.

### 3.3 Root cause: the Schedule is invisible to the embedding model

`paraphrase-multilingual-MiniLM-L12-v2` reads **at most 128 tokens**. Chunks
are 800 characters, which is about 160–230 tokens, and in a sample of every
50th chunk, **99% (1,064 of 1,075) are longer than the window**. Text past
token 128 isn't embedded at all.

| Chunk | Where the target text starts | Embedded? |
|---|---|---|
| #49943 FCA Schedule | "SCHEDULE" at token 130; *Dower* 158; *Restitution* 167; *Dowry* 215 | **No**. The vector represents s.26 (rule-making power) |
| #49917 FCA s.9(1a) | "restitution of conjugal" at token 149 | **No** |
| #49944 FCA Schedule items 7–9 | token 0 | Yes (ranks 23 for Q2 and 36 for Q3, at 0.61–0.63) |
| #49613 MFLO s.10 | token 55 | Yes |
| #835 MFLO s.10 | token 27 | Yes |

This is why Q4 got "the library has no provision on restitution of conjugal
rights": the provision is stored, but no query can reach it. It also
affects the whole corpus, not just family law.

### 3.4 Other causes found

1. **The rewrite injects statute names.** "… under Muslim Family Laws
   Ordinance" (Q2, Q3, Q4) points the search at the MFLO even when the
   provision is in the FCA Schedule or the Dowry Act.
2. **The rewrite is sampled** (temperature 0.3) and **not logged** (§ 2.2).
3. **Minority personal-law statutes crowd out Muslim family law** for
   generic wording: the Divorce Act 1869, the Married Women's Property Act
   1874, the Hindu Marriage Act 2017 and the Parsi Marriage and Divorce Act
   appear in Q2, Q3, Q4 and Q7.
4. **Contents-list chunks rank high.** Section lookup then adds sections by
   heading match, e.g. DMMA s.5 "Rights to dower not to be affected" for
   Q4, which is unrelated to restitution.
5. **Q8's answer relies on the QSO**, which FCA s.17 excludes from Family
   Court proceedings (save as the Act provides).

---

## 4. Answer sentences not supported by any retrieved passage

Each answer was checked against the full text of every passage retrieved
with it (Appendix B):
- **Supported**: the passage says it.
- **Unsupported**: no retrieved passage says it.
- **Misattributed**: the passage exists but says something narrower or
  different.

The citation check passed all three answers: it only checks that a cited
*section number* appears in the passages, not that the claim does. That's
why the label was renamed (§ 6).

### Q3: personal property after the marriage ends

Retrieved:
- [1] MFLO s.9, maintenance (#833);
- [2] MFLO, 2021 succession sub-sections (5)–(7), widow's and widower's shares (#49600);
- [3] Companies Act 2017, a single-member company's shares on death
  (#28993);
- [4] FCA ss.24–25, unregistered marriage, Guardians and Wards Act
  (#49938);
- [5]–[6] DMMA s.2 (#52631, #52632).

| Sentence (abridged) | Verdict |
|---|---|
| "a spouse may not lawfully keep the other's personal property simply because the marriage has ended" | **Unsupported**. No passage addresses keeping personal property |
| "can seek a maintenance order, a share of movable property, or other relief through the family court or an Arbitration Council" | Maintenance / Arbitration Council: supported [1]. **Share of movable property: misattributed** ([2] is a widow's share on the husband's death). Family-court relief: **unsupported** |
| "the wife may apply to the Chairman to constitute an Arbitration Council … certificate specifying the amount of maintenance [1]" | Supported [1] |
| "This remedy is available irrespective of whether the marriage has been dissolved" | **Unsupported** |
| "it obliges the husband to provide for the wife's needs rather than retain her personal belongings" | **Unsupported** |
| "a widow (or, by analogy, a wife after separation) is entitled to her share in the corpus of her husband's movable property [2]" | Widow: supported [2]. **"By analogy, a wife after separation": unsupported** (the model's own extension) |
| "This statutory right prevents the husband from lawfully retaining the wife's personal property after the marital relationship ends" | **Unsupported** |
| "a decree of dissolution … such as the husband's failure to provide maintenance for two years [6]" | Supported [6] |
| "Once a decree is granted, the family court has jurisdiction to enforce the wife's rights to maintenance and property [4]" | **Misattributed**: [4] is about unregistered marriages and the Guardians and Wards Act |
| "FCA designates Family Courts as the appropriate forum for … maintenance, and property disputes arising from the dissolution [4]" | **Misattributed**. Substantially true per Schedule items 3, 8 and 9, but that text wasn't retrieved (§ 3.3) |
| "The court can order the return of personal property … and enforce maintenance certificates issued by an Arbitration Council" | **Unsupported** |
| Remedies list: Arbitration Council [1] / share of movable property [2] / DMMA [6] then Family Court enforcement [4] | [1] and [6] supported; **[2] misattributed; [4] misattributed** |
| "statutory mechanisms exist to compel the return of such property" | **Unsupported** (it's true per Schedule item 9, which wasn't retrieved) |

### Q6: advocate presenting false facts

Retrieved:
- [1] Sindh Incumbered Estates Act 1896, the provision before s.7, false
  evidence in an incumbered-estates inquiry (#29919);
- [2] Succession Act 1925, the provision before s.283, false statements in
  probate / administration proceedings (#16110);
- [3] Pakistan Air Force Act 1953, s.57 and the end of the preceding section,
  false documents by persons subject to that Act (#30644).

The LPBCA wasn't retrieved in the session.

| Sentence (abridged) | Verdict |
|---|---|
| "a family-law advocate who knowingly presents false facts … commits an offence under the PPC" | **Unsupported**. [1] and [2] deem false evidence an offence only within their own proceedings |
| "may also be punished under statutes that penalise false declarations" | **Unsupported**: [3] applies only to persons subject to the Air Force Act |
| "in addition to facing professional discipline" | **Unsupported** (no LPBCA passage) |
| "The Succession Act expressly provides that a person who knowingly makes a false statement … deemed … section 193 PPC [2]" | Textually supported [2], but **misattributed in scope**: it's limited to statements in probate and administration proceedings |
| "This provision applies to any person who, in a legal proceeding, deliberately furnishes false information, which would include a family-law advocate" | **Unsupported** |
| "The Pakistan Air Force Act … contains a general offence of falsifying official documents" | **Misattributed**: s.57 covers "any person subject to this Act" |
| quote of s.57(a), "shall, on conviction by court-martial, be liable to suffer short imprisonment" [3] | Textually supported [3]; irrelevant to advocates |
| "The spirit of this provision reflects the broader legal principle …" | **Unsupported** |
| "the same criminal provisions apply to advocates" | **Unsupported** |
| "breaches the duty of candour and honesty owed to the tribunal" | **Unsupported** |
| "Prosecuted under section 193 PPC for giving false evidence" | **Unsupported** as applied to advocates (s.193 appears only via [2]) |
| "disciplinary action by the relevant Bar Council or Supreme Court Bar Association … suspension or disbarment" | **Unsupported** (no LPBCA passage). Flag for lawyer review: a bar *association* isn't the disciplinary body |
| All of "Implications for the client" (set aside, costs, referral for prosecution) | **Unsupported** |
| Conclusion: "criminal offence (section 193 PPC as reflected in the Succession Act) … false declaration (as per the Pakistan Air Force Act)" | **Misattributed** |

### Q8: burden of proof for unpaid dower

Retrieved: [1] Qanun-e-Shahadat Art. 18, evidence may be given of facts in
issue and relevant facts (#2255).

| Sentence (abridged) | Verdict |
|---|---|
| "The wife, as the plaintiff, must prove the existence and non-payment of the dower; the burden … rests on her" | **Unsupported**. Art. 18 says nothing about who bears the burden. Flag for lawyer review: whether the burden of proving *payment* falls on the husband |
| "a party may present evidence of 'facts in issue' and of 'relevant facts' in any suit or proceeding [1]" | Supported [1] |
| "The party who asserts a particular fact bears the responsibility to prove it" | **Unsupported**: that's the content of the burden-of-proof articles, which weren't retrieved (re-run rank 4, score 0.59) |
| "the claim of non-payment is a fact in issue. Consequently, the wife must produce admissible evidence (marriage contract, receipts, witnesses …)" | **Unsupported** |
| "The husband's denial … does not shift the burden … the initial burden … remains with the wife" | **Unsupported** |
| Conclusion "… as required by the evidentiary rules governing facts in issue" | **Unsupported** beyond Art. 18 |
| *(Omitted)* MFLO s.10: dower payable on demand where the nikahnama is silent | Not retrieved (rank 3,120) |
| *(Omitted)* FCA s.17: the QSO doesn't apply before a Family Court | Not retrieved |

---

## 5. Design (not built, awaiting approval)

### 5.1 Family-law retrieval filter

**Statutes it allows.** Source names are matched after normalisation
(lower-case, letters and digits only), so both MFLO copies match. All the
counts below are measured on the live index.

| Tier | Statutes | Chunks | When used |
|---|---|---:|---|
| Core | MFLO 1961 (both copies); West Pakistan Family Courts Act 1964; Dissolution of Muslim Marriages Act 1939; Dowry and Bridal Gifts (Restriction) Act 1976; Guardians and Wards Act 1890; Child Marriage Restraint Act 1929; Majority Act 1875 | 200 | Always, in family scope |
| Minority personal law | Christian Marriage Act 1872; Divorce Act 1869; Hindu Marriage Act 2017; Hindu Married Women's Right to Separate Residence and Maintenance Act 1946; Parsi Marriage and Divorce Act 1936; Married Women's Property Act 1874 | 291 | Only when the question names the community (Christian, Hindu, Parsi, …); otherwise they crowd out Muslim family law (§ 3.4) |
| Excluded | Qanun-e-Shahadat, CPC (except ss.10–11) | — | FCA s.17 excludes them from Family Court proceedings. Answering from them is what went wrong in Q8 |
| Missing (to add to the corpus) | West Pakistan Family Court Rules 1965 (place of suing, r.6); Muslim Personal Law (Shariat) Application Act 1962 | — | Needs source PDFs. Without the Rules, Q5 can only be answered from FCA s.5 |

**How it's applied to the existing index.** The main 53,739-vector index
and the old index are **not rebuilt or modified**.

1. **Select.** At index load, pick the chunk ids whose source matches the
   allowlist (200 core chunks, plus 291 when a minority tier is triggered).
2. **Re-embed in windows.** This is required, because a filter alone
   wouldn't reach the Schedule (§ 3.3). Each selected chunk is embedded as
   overlapping windows of ≤120 tokens (stride about 60), so text past token
   128 gets a vector. That's an estimated 600–1,000 vectors for the core
   tier. They're kept in a small in-memory `IndexFlatIP`, or cached next to
   the main index as `family_windows.faiss`/`.json`. A chunk's score is the
   best of its windows. The LLM still sees the whole chunk.
3. **When family scope is on.** One of these needs your decision:
   - **(a) Automatic** when the chat is linked to a case (all case types are
     family) or the question or rewrite contains a family term of art:
     nikah/nikahnama, talaq, khula, dower/mahr/haq mehr, dowry/jahez,
     maintenance/nafaqa, custody/hizanat, guardian, conjugal, iddat, Family
     Court.
   - **(b)** A "Family law" toggle in chat and research.
   - **(c) Both** (recommended): automatic, with a visible chip the user
     can switch off.
4. **Search order.** Search the family window index first. If its best
   score is below the family threshold, fall back to the existing full
   search. That keeps questions like Q6 (advocates' conduct, LPBCA)
   answerable.
5. **Threshold.** Window vectors score differently from whole-chunk
   vectors, so the family threshold must be tuned on the gold set, not
   copied from 0.65. Tuning cost: offline, no Groq calls if the cached
   rewrites are reused.

**Expected effect on the eight cases** (to be verified after building, not
claimed now):
- Q2, Q3, Q4 and Q7 can reach Schedule items 2/3/4/8/9 and FCA s.9(1a).
- Q1 can reach MFLO s.10.
- Q5 reaches FCA s.5 only (the Rules are missing).
- Q6 falls back to the full index (LPBCA).
- Q8 should at least stop resting on the QSO.

**Related fixes, needed for the filter to be stable (approval asked
separately):**
- Rewrite at temperature 0, and log the rewritten query.
- Stop the rewrite naming a statute ("under …"), since it steers away from
  the right Act.

### 5.2 Low-confidence note

- **Rule.** If the best passage actually sent to the model scores in
  **[0.65, 0.70)**, the answer is still given, with a note.
  - In this session that band catches Q6 (best 0.6834) and Q8 (0.6509),
    the two weakest answers, and none of the others.
  - The upper bound should be confirmed on the 78-question set before it's
    fixed. That's offline, using stored scores.
- **Backend.**
  - `send()` already has the scores, so it computes `confidence: "low" |
    "normal"` and returns it.
  - Citations already store `relevance`, so the history endpoint can
    derive the same value. **No database change.**
  - Optionally, one prompt line when low: "State what the passages do and
    do not cover." That adds about 15 prompt tokens.
- **Frontend.** An amber note above the answer, shown in English or Urdu by
  answer language:
  > *Weak match: the closest passages only partly match your question.
  > Check the cited sections before relying on this answer.*

  The "No unverified section references" label is separate and stays.
- **Not a fix on its own.** Q3 and Q4 scored above 0.70 and were still
  wrong. The note only flags the band where retrieval is least reliable.

### 5.3 Decisions needed

1. Family-scope trigger: (a), (b) or (c) (recommended: c).
2. Whether minority personal law should be keyword-gated (recommended) or
   always included.
3. Window embedding for the family tier (recommended; the filter alone
   can't reach the Schedule).
4. Whether to source the Family Court Rules 1965 and the Shariat
   Application Act 1962 for the corpus.
5. Low-confidence band [0.65, 0.70), to be confirmed on the 78 questions.
6. Rewrite at temperature 0 with logging, and no statute names injected.

---

## 6. Label change (done)

"Checked against source" is now **"No unverified section references"**
everywhere it appeared. The check only confirms that cited section
*numbers* appear in the retrieved passages (§ 4).

| File | Occurrences |
|---|---:|
| `frontend/src/features/chatbot/ChatPage.jsx` | 1 |
| `frontend/src/features/landing/LandingPage.jsx` | 3 |
| `docs/architecture/STYLE_GUIDE.md` | 1 |

No test or other document contained the old label. Lint is clean, the build
passes, and all 213 backend tests pass.

---

## Appendix A: answers received (verbatim)

### CR-01

**Question:** Why is the Nikah Nama important in a dower dispute?

**Answer** (1701 ms):

> I can only answer questions about Pakistani law and legal matters. This question appears to be outside my scope. Please ask about Pakistani statutes, court procedures, or legal matters.

### CR-02

**Question:** A wife claims that her dowry articles remain in the husband's possession after separation. What remedy may be available?

**Answer** (1305 ms):

> I can only answer questions about Pakistani law and legal matters. This question appears to be outside my scope. Please ask about Pakistani statutes, court procedures, or legal matters.

### CR-03

**Question:** Can a spouse lawfully retain the other's personal property merely because the marriage has ended?

**Answer** (3545 ms):

> Short answer: Under Pakistani statutes a spouse may not lawfully keep the other’s personal property simply because the marriage has ended; the aggrieved party can seek a maintenance order, a share of movable property, or other relief through the family court or an Arbitration Council.  
>
> **Detailed breakdown**
>
> 1. **Maintenance and arbitration** – If a husband fails to maintain his wife adequately, the wife may apply to the Chairman to constitute an Arbitration Council, which can issue a certificate specifying the amount of maintenance the husband must pay [1]. This remedy is available irrespective of whether the marriage has been dissolved, and it obliges the husband to provide for the wife’s needs rather than retain her personal belongings.
>
> 2. **Share in movable property** – The Muslim Family Laws Ordinance, 1961 provides that a widow (or, by analogy, a wife after separation) is entitled to her share in the corpus of her husband’s movable property [2]. This statutory right prevents the husband from lawfully retaining the wife’s personal property after the marital relationship ends.
>
> 3. **Dissolution of marriage** – The Dissolution of Muslim Marriages Act, 1939 allows a woman to obtain a decree of dissolution on various grounds, such as the husband’s failure to provide maintenance for two years [6]. Once a decree is granted, the family court has jurisdiction to enforce the wife’s rights to maintenance and property under the relevant statutes [4].
>
> 4. **Family court jurisdiction** – The West Pakistan Family Courts Act, 1964 designates Family Courts as the appropriate forum for matters relating to marriage, maintenance, and property disputes arising from the dissolution of a marriage [4]. The court can order the return of personal property to its rightful owner and enforce maintenance certificates issued by an Arbitration Council.
>
> 5. **Remedies available** – Accordingly, a spouse whose personal property is being retained can:
>    - File an application with the Arbitration Council for a maintenance certificate (per [1]).
>    - Seek a share of the husband’s movable property as provided in the Muslim Family Laws Ordinance [2].
>    - Initiate dissolution proceedings under the Dissolution of Muslim Marriages Act [6] and, after obtaining a decree, approach the Family Court for enforcement of property rights [4].
>
> **Conclusion** – Pakistani law does not permit a spouse to keep the other’s personal property merely because the marriage has ended; statutory mechanisms exist to compel the return of such property and to provide financial support. If further procedural guidance is needed, the relevant family court rules and the prescribed forms for arbitration applications should be consulted.

### CR-04

**Question:** What is a suit for restitution of conjugal rights?

**Answer** (4641 ms):

> Short answer: LegalEase’s statute library does not contain a specific provision describing a “suit for restitution of conjugal rights,” but the closest relevant authority is the West Pakistan Family Courts Act, 1964, which gives Family Courts jurisdiction over marriage‑related matters.  
>
> **Detailed breakdown**
>
> - The passages provided from the West Pakistan Family Courts Act, 1964 set out the general jurisdiction of Family Courts over matrimonial disputes, maintenance, and related procedures [1][4]. The Act does not contain a separate section that defines or regulates a suit for restitution of conjugal rights.
>
> - Because the statute library does not include a specific provision on restitution of conjugal rights, the exact nature, filing requirements, and remedies of such a suit cannot be detailed from the available texts.
>
> - However, where a marital dispute arises—including issues of marital co‑habitation or the enforcement of marital duties—the Family Court is the designated forum under the Act [1][4]. Parties may approach the Family Court for relief that the statute contemplates (e.g., maintenance, arbitration, dissolution), and the Court would apply the procedural rules prescribed for family matters.
>
> **Conclusion**  
> The specific concept of a “suit for restitution of conjugal rights” is not covered in the statutes currently available in LegalEase’s library; the nearest applicable provision is the general jurisdiction of Family Courts over marriage‑related cases under the West Pakistan Family Courts Act, 1964. For precise procedural guidance, one would need to consult the full text of the relevant family law statutes or rules that expressly address restitution of conjugal rights.

### CR-05

**Question:** Why is territorial jurisdiction important in a Family Court case?

**Answer** (1290 ms):

> I can only answer questions about Pakistani law and legal matters. This question appears to be outside my scope. Please ask about Pakistani statutes, court procedures, or legal matters.

### CR-06

**Question:** Can a family-law advocate knowingly present false facts before the court merely to secure relief for the client?

**Answer** (3287 ms):

> Short answer: No – a family‑law advocate who knowingly presents false facts before a court commits an offence under the Pakistan Penal Code and may also be punished under statutes that penalise false declarations, in addition to facing professional discipline.  
>
> **Detailed breakdown**
>
> 1. **Criminal liability for false statements** – The *Succession Act, 1925* expressly provides that a person who knowingly makes a false statement, or who knows that a statement is false, “shall be deemed to have committed an offence under section 193 of the Pakistan Penal Code (XLV of 1860)” [2]. This provision applies to any person who, in a legal proceeding, deliberately furnishes false information, which would include a family‑law advocate.
>
> 2. **Punishment for false declarations** – The *Pakistan Air Force Act, 1953* (which, although drafted for a specific service, contains a general offence of falsifying official documents) states that any person who “knowingly makes… any false or fraudulent statement” in a report, return, list, certificate, book or other document “shall, on conviction by court‑martial, be liable to suffer short imprisonment” [3]. The spirit of this provision reflects the broader legal principle that knowingly presenting false facts in any official document or testimony is punishable.
>
> 3. **Professional consequences** – While the statutes above do not name the legal profession, the same criminal provisions apply to advocates. An advocate who deliberately misleads the court breaches the duty of candour and honesty owed to the tribunal and to the administration of justice. Consequently, the advocate may be:
>    - Prosecuted under section 193 of the Pakistan Penal Code for giving false evidence, and/or under any applicable penal provision for falsification.
>    - Subject to disciplinary action by the relevant Bar Council or Supreme Court Bar Association, which can impose suspension or disbarment for professional misconduct.
>
> 4. **Implications for the client** – Relief obtained on the basis of false facts is vulnerable to being set aside. If the falsehood is discovered, the court may dismiss the claim, award costs against the advocate’s client, and refer the matter for criminal prosecution of the advocate.
>
> **Conclusion** – Under Pakistani law, knowingly presenting false facts before a family court is a criminal offence (section 193 PPC as reflected in the *Succession Act*) and is punishable as a false declaration (as per the *Pakistan Air Force Act*), and it also exposes the advocate to severe professional sanctions.

### CR-07

**Question:** A wife files a suit seeking dissolution of marriage, unpaid dower, maintenance and recovery of dowry articles. The husband denies all allegations and claims that the wife left the matrimonial home without justification. What should the court determine?

**Answer** (1420 ms):

> I can only answer questions about Pakistani law and legal matters. This question appears to be outside my scope. Please ask about Pakistani statutes, court procedures, or legal matters.

### CR-08

**Question:** If a wife claims unpaid dower, who must establish the relevant facts?

**Answer** (2716 ms):

> Short answer: The wife, as the plaintiff, must prove the existence and non‑payment of the dower; the burden of establishing those facts rests on her.  
>
> **Detailed breakdown**
>
> 1. **Burden of proof in civil suits** – Under the law of evidence, a party may present evidence of “facts in issue” and of “relevant facts” in any suit or proceeding [1]. The party who asserts a particular fact bears the responsibility to prove it.
>
> 2. **Application to a dower claim** – In a suit where the wife alleges that the husband has failed to pay the dower (mahr), the claim of non‑payment is a *fact in issue*. Consequently, the wife must produce admissible evidence (e.g., the marriage contract, receipts, witnesses to the dower agreement, or any written acknowledgment) to establish that the dower was stipulated and remains unpaid.
>
> 3. **Effect of the husband’s denial** – The husband’s denial that the dower is unpaid does not shift the burden; it merely constitutes a defence. He may adduce his own evidence to rebut the wife’s claim, but the initial burden of proving the unpaid dower remains with the wife.  
>
> **Conclusion** – In a Pakistani family‑law suit for unpaid dower, the wife must establish the relevant facts concerning the dower’s amount, the obligation to pay, and the failure to do so, as required by the evidentiary rules governing facts in issue.


## Appendix B: passages stored with each answer

### CR-03

**[1] Muslim Family Laws Ordinance, 1961**, relevance 0.7634, chunk #833

> applicable, apply. Chapter I — Muslim Family Laws Ordinance 1969 Section 9 — Maintenance (1) If any husband fails to maintain his wife adequately, or where there are more wives than one, fails to maintain them equitably, the wi fe, or all or any of the wives, may in addition to seeking any other legal remedy available apply to the Chairman who shall constitute an Arbitration Council to determine the matter, and the Arbitration Council may issue a certificate specifying the amount which shall be paid as maintenance by the husband. (2) A husband or wife may, in the prescribed manner, within the prescribed period, and on payment of the prescribed fee, prefer an application for revision of the certificate, to the Collector concerned a nd his decision shall be final and shall not be called in

**[2] THE MUSLIM FAMILY LAWS ORDINAN CE, 1961**, relevance 0.7034, chunk #49600

> become entitled to her due share in the corpus of immovable property. (5) A widow is entitled to her share in the corpus of movable property of her deceased husband provide d that the provisions of sub -sections (2) and (3) shall mutatis mutandis apply. 1Subs. by the Muslim Family Laws (Amdt.) Ordinance, 1961 (XXI of 1961), s. 2, for “having jurisdiction in the area concerned”. 2Renumbered as sub -section (1) and added new sub -sections from (2) to (8) by Act, XXVIII of 2021, s. 2. Page 4 of 7 (6) Fiqah -e-Jafri recognizes right of a husband to get his share from the property left by his deceased wife, either movable or immovable, as follows: ⸺ (a) one-half share, if there is no child left behind; and (b) one-fourth share of the property, if there is child left behind. (7) In case of disp

**[3] THE COMPANIES ACT, 2017**, relevance 0.6829, chunk #28993

> e respons ible to.— Page 319 of 401 (a) transfer the shares to the legal heirs of the deceased subject to succession to be determined under the Islamic law of inheritance and in case of a non-Muslim memb ers, as per their respective law; and (b) manage the affairs of the compa ny as a trustee, till such time the title of shares are transferred: Provid ed that where the transfer by virtue of the above provision is made to more than one legal heir, the compa ny shall cease to be a single member compa ny and comply with the provisions of section 47 of the Act. CHA NGE OF STATUS 10. The compa ny may convert itself from single memb er private company to a private compa ny in accordance with the provisions of section 47. MEETIN GS, VOTES AND ELECTI ON OF DIRECTORS 11. All the requirements of the

**[4] THE WEST PAKISTAN FAMILY COURTS ACT, 1964**, relevance 0.6705, chunk #49938

> ny proceedings before a Family Court it is brought to the notice of the Court that a marriage solemnized under the Muslim Law after the coming into force of the Muslim Family Laws Ordinance, 1961, has not been registered in accordance with the provisions of the said Ordinance and the rules framed thereunder, the Court shall commu nicate such fact in writing to the Union Council for the area where the marriage was solemnized. 25. Family Court deemed to be a District Court for purposes of Guardians and Wards Act, 1890.―A Family Court shall be deemed to be a District Court for the purposes of the Guardians and Wards Act, 1890, and notwithstanding anything contained in this Act, shall, in dealing with matters specified in that Act, follow the procedure prescribed in that Act. 3[25-A. Transfer

**[5] THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939**, relevance 0.7205, chunk #52631

> tie. WHEREAS it is expedient to consolidate and clarify the provisions of Muslim law relating to suits for dissolution of marriage by women married under Muslim law and to remove doubts as to the effect of the renunciation of Islam by a married Muslim woman on her marriage tie; It is hereby enacted as follows:__ 1. Short title and extent.__(1) This Act may be called the Dissolution of Muslim Marriages Act, 1939. 2[(2) It extends to the whole of Pakistan.] 2. Grounds for decree for dissolution of marriage. A woman married under Muslim Law shall be entitled to obtain a decree for dissolution of her marriage on any one or more of the following grounds, namely:__ (i) that the whereabouts of the husband have not been known for a period of four years; (ii) that the husband has neglected or has

**[6] THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939**, relevance 0.7205, chunk #52632

> husband have not been known for a period of four years; (ii) that the husband has neglected or has failed to provide for her maintenance for a period of two years; 3[(iia) that the husband has taken an additional wife in contravention of the provisions of the Muslim Family Laws Ordinance, 1961;] 1For Statement of Objects and Reasons, see Gazette of India, 1936, Pt. V, 154; for Report of Select Committee, see ibid., 1939, Pt. V, p. 1. It has also been extended to Phulera in the Excluded Area of Upper Tanawal to the extent the Act is applicable in the N. W. F. P., and also extended to the Excluded Area of Upper Tanawal (N.W.F.P) other than Phulera with effect from such date and subject to such modifications as may be notified, see N.W.F.P. (Upper Tananwal) (Excluded Area) Laws Regulation, 1

### CR-04

**[1] THE WEST PAKISTAN FAMILY COURTS ACT, 1964**, relevance 0.7261, chunk #49938

> ny proceedings before a Family Court it is brought to the notice of the Court that a marriage solemnized under the Muslim Law after the coming into force of the Muslim Family Laws Ordinance, 1961, has not been registered in accordance with the provisions of the said Ordinance and the rules framed thereunder, the Court shall commu nicate such fact in writing to the Union Council for the area where the marriage was solemnized. 25. Family Court deemed to be a District Court for purposes of Guardians and Wards Act, 1890.―A Family Court shall be deemed to be a District Court for the purposes of the Guardians and Wards Act, 1890, and notwithstanding anything contained in this Act, shall, in dealing with matters specified in that Act, follow the procedure prescribed in that Act. 3[25-A. Transfer

**[2] Muslim Family Laws Ordinance, 1961**, relevance 0.7124, chunk #833

> applicable, apply. Chapter I — Muslim Family Laws Ordinance 1969 Section 9 — Maintenance (1) If any husband fails to maintain his wife adequately, or where there are more wives than one, fails to maintain them equitably, the wi fe, or all or any of the wives, may in addition to seeking any other legal remedy available apply to the Chairman who shall constitute an Arbitration Council to determine the matter, and the Arbitration Council may issue a certificate specifying the amount which shall be paid as maintenance by the husband. (2) A husband or wife may, in the prescribed manner, within the prescribed period, and on payment of the prescribed fee, prefer an application for revision of the certificate, to the Collector concerned a nd his decision shall be final and shall not be called in

**[3] THE WEST PAKISTAN FAMILY COURTS ACT, 1964**, relevance 0.6925, chunk #49937

> decree, if and when passed.] 22. Bar on the issue of injunctions by Family Court.― A Family Court shall not have the power to issue an injunction to, or stay any proceedings pending before, a Chairman or an Arbitration Council. 23. Validity of marriag es regist ered under the Muslim Family Laws Ordinance, 1961, not to be questioned by Family Courts.― A Family Court shall not question the validity of any marriage registered in accordance with the provisions of the Muslim Family Laws Ordinance, 1961, nor shall any evidenc e in regard thereto be admissible before such Court. 24. Family Courts to inform Union Councils of cases not registered under the Muslim Family Laws Ordinance, 1961.― If in any proceedings before a Family Court it is brought to the notice of the Court that a marriage solemn

**[4] THE HINDU MARRIAGE ACT, 2017**, relevance 0.6689, chunk #29484

> eguard the legitimate, rights and interests of minorities; AND W HEREAS it is expedient to have a consolidated law providing for solemnization of marriages by Hindu families and the matters connected therewith and incidental thereto; AND W HEREAS the Provincial Assemblies of Balochistan, Khyber 'Pakhtunkhwa and Punjab have pa ssed Resolutions under Article 144 of the Constitution of the Islamic Republic of Pakistan to the effect that MajliseShoora (Parliament) may, by law, regulate solemnization of marriages by Hindu families and for matters connected therewith and incidental thereto; It is hereby enacted as follows: — 1. Short title, extent, application and commencement. —(1) This Act may be called the Hindu Marriage Act, 2017. (2) It extends to the Islamabad Capital Territory and the Pro

**[5] THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939**, relevance 0.7101, chunk #52638

> ect of conversion to another faith. The renunciation of Islam by a married Muslim woman or her conversion to a faith other than Islam shall not by itself operate to dissolve her marriage: Provided that after such renunciation, or conversion, the woman shall be entitled to obtain a decree for the dissolution of her marriage on any of the grounds mentioned in section 2: Provided further that the provisions of this section shall not apply to a woman converted to Islam from some other faith who reembraces her former faith. 5. Rights to dower not to be affected. Nothing contained in this Act shall affect any right which a married woman may have under Muslim law to her dower or any part thereof on the dissolution of her marriage. 6. [Repeal of s. 5 o f Act, XXVI of 1937.] Rep. by the Repealing a

**[6] THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939**, relevance 0.7101, chunk #52639

> the dissolution of her marriage. 6. [Repeal of s. 5 o f Act, XXVI of 1937.] Rep. by the Repealing and Amendment Act, 1942 (XXV of 1942), s. 2 and First Sch. ______________ Page 4 of 5Page 5 of 5

### CR-06

**[1] THE SINDH INCUMBERED ESTATES ACT, 1896**, relevance 0.6834, chunk #29919

> does not know or believe to be true, such person shall be deemed to haveintentionally given false evidence within the meaning of the Pakistan Penal Code (XLV of 1860).7. Report of inquiry and proceedings thereon.__(1) The officer so appointed, after makinginquiry, shall submit a report of the proceedings to the Commissioner. (2) On receipt of such report, the Commissioner may—(a) direct a further inquiry; or(b) dismiss the application; or,1Subs. by the Central Laws (Statute Reform) Ordinance, 1960 (21 of 1960), s. 3 and 2nd Sch. (with effect from the 14th October, 1955), for "the Provinces and the Capital of theFederation”, which had been subs. by A. O.,1949, Arts. 3 (2) and 4, for “British India”. 2Subsection (2) ins. by the Sindh Incumbered Estates (Amdt.) Act, 1906 (2 of 1906), s.3. Pag

**[2] THE SUCCESSION ACT, 1925**, relevance 0.6529, chunk #16110

> s to be false, such person shall be deemed to have committed an offence under section 193 of the Pakistan Penal Code (XLV of 1860). 283. Powers of District Judge.___(1) In all cases the District Judge or District Delegate may, if he thinks proper,___ (a) examine the petitioner in person, upon oath; (b) require further evidence of the due execution of the will or the right of the petitioner to the letters of administration, as the case may be; (c) issue citations calling upon all persons claiming to have any interest in the estate of the deceased to come and see the proceedings before the grant of probate or letters of administration. (2) The citation shall be fixed up in some conspicuous part of the courthouse, and also in the office of the Collector of the district and otherwise published

**[3] THE PAKISTAN AIR FORCE ACT, 1953**, relevance 0.6501, chunk #30644

> ent to be false, or knowingly and wilfully suppresses any material facts ; shall, on conviction by court-martial, be liable to suffer short imprisonment. 57. Falsifying official document and f alse declaration. Any person subject to this Act, who commits any of the following offences, that is to say : ___ (a) in any report, return, list, certificate, book or other document made or signed by him, or of the contents of which it is his duty to asc ertain the accuracy, knowingly makes, or is privyto the making of, any false or fraudulent statement ; or (b) in any document of the description mentioned in clause (a) knowingly makes, or is privy to the making of, any omission, with intent to defraud ; or (c) knowingly and with intent to injure any person or knowingly and with intent Page 34 of 78

### CR-08

**[1] THE QANUNESHAHADAT , 1984**, relevance 0.6509, chunk #2255

> timony of one man or one woman or such other evidence as the circumstances of the case may warrant. ___________ CHAPTER III OF THE RELEVANCY OF FACTS 18. Evidence may be given of facts in issue and relevant facts. — Evidence may be given in any suit or proceeding of the existence or nonexistence of every fact in issue and of such other facts as are hereinafter declared to be relevant, and of others. Explanation . — This Article shall not enable any person to give evidence of a fact which he is disentitled to prove by any provision of the law for the time being in force relating to Civil Procedure. Illustrations (a) A is tried for the murder of B by beating him with a club with the intention of causing his death. At A’ s trial the following facts are in issue — A’s beating B with the club;

