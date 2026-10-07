# kb-v2 C8: accuracy pass (2026-10-07)

Questions: `docs/evaluation/c8/c8_questions.json`, committed (2ddb964) **before** any C8 run and not edited since.
Three sets, reported separately: the 26 gold questions, the 5 live-test questions (as asked in the
live checks: murder s.302, khula/dissolution, khula procedure, talaq procedure, registration), and 40
unseen questions (criminal, family, contract, property, constitution, civil procedure).

Measured offline (no LLM): demo configuration (`KB_V2`, hints and scraped laws on), raw question.
**Top 5** = an expected Act + section in the top 5 of search (Research). **Reaches the model** = the
expected section is among the passages Chat sends the model (`retrieve_passages`: the 0.65 gate,
exact section lookup, section expansion), i.e. what an answer can be grounded on.

## Results

| Set | Top 5: before C8 | Top 5: after | Reaches the model: before | after |
|---|---:|---:|---:|---:|
| 26 gold | 20/26 | **21/26** | 18/26 | **19/26** |
| 5 live | 4/5 | **5/5** | 5/5 | **5/5** |
| 40 unseen | 24/40 | **31/40** | 24/40 | **29/40** |

"Before" = the C8 search changes switched off (`eval_c8.py --off hybrid,hint_sections`); the
retrieval-only baseline run before any change gave the same top-5 counts (20 / 4 / 24).

Step by step (top 5; reaches the model where measured):

| Step | Gold | Live | Unseen | Kept? |
|---|---|---|---|---|
| Baseline | 20 | 4 | 24 | |
| Hybrid retrieval (BM25 + vectors, RRF) | 21 | 5 | 31 | yes: no set worse |
| Hint exact sections, word-set triggers | 21 | 5 | 31 | yes: counts equal, G12/L2 up, G09 down within the top 5 |
| Section expansion, reference checker, cases, refusals, repealed | 21 | 5 | 31 | retrieval unchanged |
| Supporting sections after the gate (reaches the model) | 18 -> 19 | 5 -> 5 | 25 -> 29 | yes: none lost |
| Trial: keep hybrid order when merging scraped laws | 21 | 5 | 31 (reaches 29 -> 28, U24 lost) | **reverted** (helped gold/live ranks, hurt unseen) |
| Trial: lexical cosine floor 0.40 -> 0.30 | no change | no change | no change | not adopted |

Tokens per chat answer (65 answered questions, o200k): prompt mean 1,201 -> 1,321 with section
expansion, max 1,900 -> 2,801; with the 2,000-token reply at most 4,801 per answer (Groq 8,000 a
minute), before the ~400-token rewrite and, with judgments on, ~900 for the cases block.

## Still failing

Not in the top 5 (gold): G03 essential elements of a contract (Contract Act s.10), G13 definition of
qatl-i-amd (PPC s.300; s.299/s.302 rank first), G22 writ jurisdiction (Constitution Art.199), G25
declaratory suit (Specific Relief Act s.42), G26 minor's contract (Contract Act s.11).
In the top 5 but below the gate (gold): G05 (MFLO s.6, 0.618), G20 (QSO Art.17, 0.649).

Not in the top 5 (unseen): U09 pre-arrest bail (CrPC s.498), U18 definition of contract (Contract
Act s.2), U25 mortgage and U26 lease (**TPA ss.58 and 105 are missing from our records**), U27
compulsory registration (Registration Act s.17), U35 torture (Constitution Art.14), U36 res judicata
(CPC s.11: BM25 ranks it first, but the merge with scraped laws re-sorts by score; the fix for that
was reverted, see above), U37 place of suing (CPC s.16), U39 review (CPC s.114).
In the top 5 but not sent: U29 (Specific Relief Act s.9), U31 (the "25A" record holds Article 25's
text: a sectioning error, so even the hit is the wrong article).

## Other C8 items

- **Section expansion:** the model gets each retrieved section's full text (<=700 tokens, top 4,
  deduplicated), not a fragment.
- **Reference checker:** figures compared in any form (OCR splits "thous and", number words,
  "Rs. 5,000"); the model's own headings ignored; real mismatches still flagged (tests).
- **Cases:** no para 0, no mostly-Arabic or presentation-form paragraphs, Chat floor 0.58, family
  questions get only family-topic judgments; prompt: a case only in its own words.
- **Refusals:** a foreign-law question not mentioning Pakistan is refused before retrieval; a model
  refusal carries no sources or case law.
- **Repealed laws:** status read from the Pakistan Code title ("(Repealed by ...)", "(Repeal by ...)").
  The listing's `action=active/inactive` parameter returns the same list (checked live), so it can't
  be used. A repealing Act's own name ("Federal Court (Repeal) Act") is not repealed: 16 scraped and
  21 corpus laws had been marked repealed wrongly. Now: 32 of 724 scraped laws repealed; none of the 35
  core laws. Repealed laws are left out of Chat and Research unless Research asks
  ("Include repealed laws"); a named repealed section is still fetched, labelled, and the answer must
  say so.
- **Scraping coverage:** KP Code full alphabetical listing (paged) added and checked live: **572 laws**
  (K 261, W 90, P 50, F 30, C 27, S 17, A 12, E 11, R 10, B 8, other letters 1-6; 11 titles start
  with "["); Pakistan Code listing **1,037 laws** (A 53, B 17, C 106, D 42, E 52, F 48, G 21, H 20,
  I 75, J 4, K 12, L 32, M 51, N 75, O 16, P 195, Q 3, R 39, S 64, T 30, U 7, V 7, W 66, Z 2); its
  default cap is now 800.
