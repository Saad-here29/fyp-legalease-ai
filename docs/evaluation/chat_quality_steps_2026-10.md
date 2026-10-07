# Chat quality steps: offline evaluation (2026-10-05)

This evaluates the four approved steps from
`docs/evaluation/chat_review_family_law_2026-10-05.md` § 5. Every step is **built and
switched off**; nothing has shipped. The flags are in `backend/.env`:

| Flag | Step |
|---|---|
| `REWRITE_V2` | 1. Rewrite at temperature 0 that never adds a statute name, with every rewrite logged |
| `STRICT_GROUNDING` | 2. Every claim tied to a numbered passage; no analogy; nothing from memory |
| `LOW_CONFIDENCE_NOTE` | 3. Note on answers whose best passage scores between 0.65 and 0.70 |
| `FAMILY_INDEX` | 4. Family-law side index, plus the page's "Family law" switch |

**Ship rule:**
1. the 8 review questions improve;
2. nothing that works today gets worse;
3. off-topic questions stay refused.

**Method:**
- **Recording:** rewrites were recorded once per setup with the backend's own
  code (`scripts/kb/eval_chat_quality.py record`). That was the only Groq use.
- **Replay:** everything else was replayed offline through the chat's own
  `retrieve_passages()`. Raw data: `docs/evaluation/chat_quality/`.
- **Question sets:** the 8 review questions (R1–R8), the 78 lawyer questions
  (L01–L78), and the 15 off-topic questions (O01–O15).
- **Recordings:** no recording failed and no rewrite fell back silently, so
  **n = 8 / 78 / 15 on every side**. (The "66 of 78" seen earlier was a
  snapshot while the run was still going.)

## Summary

| Step | 8 review questions | 78 lawyer questions | Off-topic | Verdict |
|---|---|---|---|---|
| 1. Rewrite v2 | **Worse**: 3 lose ground, 1 gains | **Worse**: 17 answered → refused (8 of them used a relevant statute); 5 refused → answered (1 plausible) | Unchanged (O14 answered, as today) | **Fails; stays off** |
| 2. Strict prompt | Not measured (see § 5) | Not measured | n/a: refusal happens before the model | **Off; waiting for your go on the ~15k run** |
| 3. Low-confidence note | Note on R5 and R6 (in the session it would have flagged Q6 and Q8) | 32 of 51 answers fall in the range; 56% of those are off-target, against 16% above 0.70 | n/a | **Meets the rule** (it changes no retrieval) |
| 4. Family index on v1 rewrites | **Mixed**: R2 and R5 improve, R3 gets worse | Same 51 answered; 24 change statutes: about 9 better, 4 worse, the rest noise either way | Unchanged | **Fails rule 2; stays off** |
| 1 + 4 together | R4 and R5 now find the supporting section (s.9(1a), s.5); R2 and R3 refused; R8 off-target (QSO) | Same 17 losses as step 1 | Unchanged | **Fails; stays off** |

**Off-topic:** O14 ("What is the punishment for murder under the Indian
Penal Code?") is answered **today** and in every setup, from Pakistani PPC,
CrPC and other passages. It's an existing failure; none of the steps cause
or fix it.

## 1. Step 1: rewrite v2

**What changed:**
- **Statute names:** the old rewrite added a statute name to **44 of 101**
  questions, e.g. "… under Muslim Family Laws Ordinance". The new one added
  one to **1** (O14, whose question names the Indian Penal Code itself). The
  backstop `strip_unasked_statutes()` never had to act.
- **Not deterministic:** at temperature 0, re-running the 8 review
  questions gave **4 different rewrites** (R3, R5, R6, R7). Groq's
  temperature 0 doesn't guarantee the same output, and R5 flips between
  refused and answered between the two runs. Step 1 doesn't deliver the
  repeatability it was meant to.
- **Why retrieval got worse:** the statute name was lifting scores. Without
  "Muslim Family Laws Ordinance" in the query, family passages fall below
  0.65.

**The 8 review questions, step 1 against today:**

| Q | Today (v1) | Step 1 (v2) | Change |
|---|---|---|---|
| R1 | refused | refused | = |
| R2 | off-target (MFLO, DMMA, Child Marriage Act) | refused | worse (it was off-target) |
| R3 | partial 0.76 (DMMA, MFLO, FCA) | refused | **loss** |
| R4 | partial 0.73 (DMMA, Hindu Marriage Act, MFLO) | off-target 0.78 (Divorce Act 1869, Hindu, Parsi) | **loss** |
| R5 | partial 0.67 (FCA) | refused (partial on the re-run) | **loss** |
| R6 | good 0.68 (LPBCA, PPC, plus noise) | good 0.67 (PPC only) | = |
| R7 | refused | refused | = |
| R8 | refused | off-target 0.67 (QSO, which FCA s.17 excludes) | worse |

**The 78 lawyer questions:** answered 51 → 39.
- **Lost (answered → refused):** L11, L17, L19, L23, L28, L30, L31, L32, L36,
  L52, L57, L60, L62, L64, L70, L74, L77.
  - Of those, **L30, L31, L32, L52, L60, L62, L70 and L77 used a relevant
    statute today** (DMMA, MFLO, FCA, Guardians and Wards Act).
- **Gained (refused → answered):** L18 (Companies Ordinance), L29
  (Cantonments Rent Restriction Act, plausible), L38 (Elections Act), L41
  (foreign contract: should stay refused), L63 (ICT child protection).
  - Of those, only **L29** looks relevant.

## 2. Step 4: family-law side index

**What it is:**
- **Built:** 491 chunks became 1,492 windows (598 core, 894 minority
  personal law).
- **Speed:** about 145 s to build on CPU, then cached in `backend/cache/`;
  loading from the cache takes 0.0 s. The main index wasn't touched.
- **Gating:** minority-law statutes are searched only when the question names
  the community. The QSO and CPC are excluded.
- **Fallback:** the full index is used when no family passage reaches
  `FAMILY_THRESHOLD` (0.65).

**The 8 review questions:**

| Q | Today | Step 4 on v1 rewrites | Steps 1 + 4 |
|---|---|---|---|
| R1 | refused | refused (best family match 0.51, but it is MFLO s.10/s.5) | refused (0.53, MFLO s.5 ranked first) |
| R2 | off-target | **partial 0.75** (MFLO, DMMA) | refused |
| R3 | partial | **off-target 0.77** (MFLO, DMMA; FCA lost) | refused |
| R4 | partial | partial | **good 0.71: FCA s.9(1a), restitution** |
| R5 | partial | **good 0.69: FCA s.5** | **good 0.67: FCA s.5** |
| R6 | good | good | good |
| R7 | refused | refused | refused |
| R8 | refused | refused | off-target (QSO) |

**The 78, step 4 on v1 rewrites:**
- **Answered count:** the same 51; none lost, none gained.
- **24 answers draw on different statutes.** By statute name (my reading,
  not a lawyer's):
  - **Better (about 9):** L02, L14, L30, L32, L33, L49, L62, L70, and L21
    (unrelated Acts dropped).
  - **Worse (4):**
    - L01 loses the Special Marriage Act (a non-Muslim spouse).
    - L48 loses the ICT Domestic Violence Act (the question asks for a
      protection order).
    - L52 and L56 lose DMMA grounds, or MFLO s.9, in favour of FCA footnote
      chunks.
  - **Noise either way:** L11, L15, L24, L42, L54, L55, L61, L66, L72, L76,
    L78.
- **New noise:** footnote and amendment chunks, e.g. Child Marriage Restraint
  Act #5774, #5780 and #5783 ("… omitted by the Muslim Family Laws
  Ordinance"), and the Dowry Act's forfeiture clause #12651. Their windows
  match the v1 rewrite's added "Muslim Family Laws Ordinance".

**Why the Schedule is still missed.** The FCA Schedule items-7–9 chunk
(#49944: "8. Dowry. 9. Personal property and belongings of a wife") never
reaches the top 5 for R2 or R3, even as a window. It's a bare list of
headings, and the embedding model scores it low against a question. Windows
fixed the 128-token cut-off (R4 and R5 now find their sections), but not
this. A keyword match over the family subset would catch it; that's outside
the approved design and isn't built.

**Family threshold.** Family-window scores run lower than full-chunk scores:
- **Relevant:** R1's supporting text ranks first at 0.53.
- **Off-topic:** O13 (divorce in California) peaks at 0.44.

Lowering the family threshold to about 0.50 would answer R1, R3, R7 and R8
from family statutes, but would also admit weak passages. I haven't changed
it.

## 3. Step 3: the 0.65–0.70 range check (today's setup, the 78)

**The split:** 51 of the 78 are answered. **32** have a best passage in
[0.65, 0.70) and **19** at 0.70 or above.

**Rating:** each answered question was rated "relevant statute among the
passages" or "off-target", by statute name (my reading, not a lawyer's).

| Best score | Answered | Off-target | Share |
|---|---:|---:|---:|
| 0.65–0.70 | 32 | 18 | **56%** |
| ≥ 0.70 | 19 | 3 | **16%** |

- **Off-target in the range:** L06, L15, L17, L19, L21, L22, L25, L28, L33,
  L36, L37, L39, L55, L57, L64, L65, L67, L74.
- **Relevant in the range** (these get a note they don't strictly need): L04,
  L14, L16, L23, L30, L31, L32, L40, L46, L48, L59, L62, L72, L73.
- **Off-target at 0.70 or above:** L11, L24, L66.

**Against the ship rule:**
- The note changes no retrieval and no answer, so nothing that works today
  gets worse, apart from an unneeded note on 14 relevant answers.
- Off-topic refusals are unaffected.
- On the 8, it would have flagged the session's two weakest answers (Q6 at
  0.68 and Q8 at 0.65).

## 4. What isn't measured

- **Step 2** (§ 5).
- **Answer quality for steps 1, 3 and 4:** only retrieval was replayed; no
  answers were generated.
- **Lawyer judgement:** every "relevant / off-target" call above is mine,
  from statute names, not a lawyer's.

## 5. Step 2: strict prompt, proposed run (not run)

**What it would run:** the new prompt on the **saved passages** of six saved
answers, compared with those answers:
- Q3, Q4, Q6 and Q8 from the 2026-10-05 review;
- two controls:
  - the talaq procedure answer (2026-09-26);
  - "What is murder under Section 302 of the Pakistan Penal Code?"
    (2026-09-26).

  The theft answer no longer exists; it was most likely among the test
  accounts deleted earlier, so the s.302 answer stands in for it.

**Cost:** there's no rewrite and no retrieval, so it costs no other tokens.
The inputs are frozen.

| | Tokens |
|---|---:|
| Prompt, counted exactly offline with the o200k tokenizer | **8,491** |
| Output: the saved answers total 2,361, plus the model's reasoning | **~3,500–7,000** |
| **Expected total** | **~12k–15.5k** |
| Hard ceiling (6 × the 2,000-token answer cap) | 20.5k |

**Caveat:** the control answers were written with the September prompt,
which had no language instruction yet. So for the controls, the comparison
also reflects that prompt change.

## 6. Groq usage today (recorded by this work)

| Run | Calls | Tokens |
|---|---:|---:|
| Review diagnosis, v1 rewrites of the 8 | 8 | 3,544 |
| v2 rewrites: 8 + 78 + 15 | 101 | 50,028 |
| v1 rewrites: 78 + 15 (the 8 reuse the diagnosis) | 93 | 43,109 |
| v2 re-run of the 8 (determinism check) | 8 | 3,770 |
| **Total** | **210** | **100,451** |

**What remains:** at most **99,549** of the 200k daily budget. Groq's limit
counts every request from the organisation, and other use today (the
legal-review chat itself, other team members) isn't recorded here. The
budget actually left is lower by that amount; the Groq console shows the true
figure. Groq use has stopped.

## 7. Decisions for you

1. **Step 1:** leave it off (recommended), or drop it. The statute-name
   rule works, but the names were what kept family questions above the
   threshold, and temperature 0 isn't deterministic on Groq.
2. **Step 3:** ready to ship on your go (measured, meets the rule).
3. **Step 4:** leave it off. Its next change would be either a family
   threshold below 0.65 or a keyword match over the family statutes for the
   Schedule. Both need your approval, and both would be measured the same
   way.
4. **Step 2:** go or no-go on the ~15k-token run (§ 5).

---

## Decision, 2026-10-06: STRICT_GROUNDING stays off for the mock presentation

The measurement run is in `docs/archive/strict_grounding_comparison_2026-10-06.md`
(6 answers on their saved passages; 13,006 tokens).

**Decision:** keep `STRICT_GROUNDING` off for the mock presentation on
2026-10-07.

**Why:**
- **Mixed result.** The strict prompt removed the worst unsupported claims
  (the "by analogy" widow-to-divorced-wife extension in Q3, and the Air
  Force Act and invented consequences in Q6), and Q4 now says plainly that
  restitution isn't covered. But Q8 still draws a conclusion the cited
  article doesn't support. And the talaq control turned into "the passages
  don't contain the procedure", because its saved passages only list s.7.
- **Demo questions unverified under it.** None of the questions the demo
  will use (DMMA grounds, theft under the PPC, the off-topic refusal) has
  been answered with the strict prompt on the live retrieval. Switching it
  on untested the day before could turn working answers into "not covered"
  replies.

**Still on:** the low-confidence note (`LOW_CONFIDENCE_NOTE`). **Still off:**
`REWRITE_V2` and `FAMILY_INDEX`.

**To revisit after the mock:** run the demo questions and a sample of the
78 lawyer questions with the strict prompt, then decide.
