# kb-v2 B7 live chat check (2026-10-07)

**Setup:**
- **Backend:** a separate test backend on **port 8100**, run from the
  `legalease-kb` worktree with `KB_V2=true`, against a **throwaway SQLite
  database** with one test account (`eval.b7.tester@example.com`, in the
  scratchpad DB only). The user's servers on 8000/5173 and the shared database
  were not touched.
- **Model and threshold:** Groq `openai/gpt-oss-120b`, live query rewrite,
  threshold 0.65.
- **Timing:** one minute between questions.
- **Tokens:** read from the test backend's log. **Total 19,621 of the
  20,000 cap; no 429.**

**Two code versions were run:**
- **Run A** (`a33b56d`): steps 0-3 committed. Strict grounding off, all 7
  questions.
- **Run B** (the fix found in run A, commit after `3df3773`): the prompt's
  source line now carries "s.N Heading" for knowledge-base passages, and the
  section number reaches the citation check. Q1 with strict grounding off,
  then on. The cap stopped the strict-on runs of Q2 and Q3.

## Results

| # | Question | Run | Answered / refused | Answer (summary) | Sources shown (Act - section heading) | Unverified note | Tokens |
|---|---|---|---|---|---|---|---:|
| Q1 | What is murder under Section 302 of the Pakistan Penal Code? | A, strict off | Answered | Punishments under s.302 (death as qisas, death or life as ta'zir, up to 25 years). Says the "exact wording of Section 302 is not included", because the source line didn't say [1] was s.302 | [1] **PPC - s.302 Punishment of qatl-i-amd (exact match, first)**; [4] PPC s.4; [5] PPC s.108A | "Section 302" (false: the s.302 record was retrieved) | 2,585 |
| Q1 | same | **B, strict off** | Answered | "The library … only provides the punishments prescribed for the offence" under s.302 (death as qisas; death or life imprisonment as ta'zir; up to 25 years where qisas doesn't apply). Says the definition of qatl-e-amd isn't in the passages (it's s.300, not retrieved) | [1] PPC - s.302 Punishment of qatl-i-amd (exact match) | **none** (4 references verified) | 2,528 |
| Q1 | same | **B, strict on** | Answered | Same content, shorter: s.302 sets the punishments, not a definition [1] | [1] PPC - s.302 Punishment of qatl-i-amd (exact match) | none (3 verified) | 2,681 |
| Q2 | What is the primary legislation governing Muslim marriages and divorces in Pakistan | A, strict off | Answered | The Muslim Family Laws Ordinance, 1961 is the principal statute (registration, polygamy, talaq, dissolution); overrides other law, custom or usage | [1] MFLO s.8; [2] DMMA s.5; [5] MFLO s.3 (also retrieved: MFLO s.6, s.5) | none | 1,933 |
| Q3 | Is marriage registration mandatory in Pakistan and under which provision | A, strict off | Answered | Yes, every marriage solemnised under Muslim law must be registered under the MFLO [1]. Quotes s.5's text but calls it "Section 1" | [1] MFLO - s.5 Registration of marriages | "Section 1 (MFLO); section 2; section 3": the model invented section numbers because the source line didn't carry them (fixed in run B; not re-run, cap) | 2,231 |
| Q4 | is the family court's blanket order demanding the total return of the dower property legally sustainable under Pakistani jurisprudence | A, strict off | **Answered** (was refused before B7), weak-match note | A Family Court can order return of dower property; finality and appeal depend on the FCA's procedure. A careful, general answer | FCA s.10, s.25, s.21A, Schedule item 4, s.14 | "Section 5 (Act)": FCA s.5 named but not retrieved (correct flag) | 2,644 |
| Q5 | On what grounds can a Muslim wife obtain a decree for dissolution of marriage? | A, strict off | Answered | The grounds in the DMMA 1939 s.2, listed | [2] DMMA - s.2 Grounds for decree for dissolution of marriage; [1] MFLO s.8; [3] DMMA s.5 | "Act named but not found: Application of the Muslim Family Laws Ordinance, 1961" (false; fixed in run B by matching names both ways; not re-run) | 2,917 |
| Q6 | What is the punishment for theft under the Pakistan Penal Code? | A, strict off | Answered | Up to three years, or fine, or both; aggravated forms (ss.380-382) | [1] PPC - s.379 Punishment for theft; s.382; s.380; s.381 | "Section 1 (PPC)": invented number for [1] (same cause as Q3, fixed in run B) | 1,742 |
| Q7 | Can you recommend a good cricket bat? | A, strict off | **Refused** | "I can only answer questions about Pakistani law…" | none | none | 360 |

**Total: 19,621 tokens.**
- **Run A:** 14,412.
- **Run B:** 5,209.

**Response times:**
- **Run A:** 2.4-4.5 s.
- **First question after each restart:** about 25 s (model loading; a warm server doesn't have this).

## What B7 changed, as seen live

- **Exact section lookup:** Q1 retrieved PPC s.302 first. Log: "Exact
  section lookup: user-supplied-pdf/pakistan-penal-code-1860/s302".
- **Scope gate:** the dower question (Q4) was **answered** with the
  weak-match note instead of refused. The cricket-bat question was still
  refused.
- **Reference completeness:** it caught a real gap (FCA s.5 named but not
  retrieved in Q4). It also produced one false flag (Q5), now fixed and
  covered by a test.
- **Found live and fixed:** the model didn't know which section a
  knowledge-base passage was, so it called the s.302 record "not included"
  and invented "Section 1" in Q3 and Q6. Fix: the prompt's source line reads
  "Pakistan Penal Code, 1860 - s.302 Punishment of qatl-i-amd (the section
  named in the question)", and the check receives the section. In run B, Q1
  had 0 unverified references.

## Strict grounding: recommendation **OFF** for the demo

- **On Q1 (run B), the only clean comparison the cap allowed:** both modes
  gave a correct, fully verified answer. Strict was shorter, with no gain
  in grounding.
- **Earlier comparison** (`docs/strict_grounding_comparison_2026-10-06.md`):
  strict also didn't improve on 6 questions.

So keep the current setting (off).

**Not measured:** strict on for Q2 and Q3, which the cap stopped.

## Needs a backend restart

**Yes.** The fixes are in backend code, so the running server on port 8000
needs a restart (Ctrl+C, then the same command as in
`docs/DEMO_RUNBOOK.md`). The Thinking-message wording is frontend-only; the
Vite dev server picks it up without a restart.
