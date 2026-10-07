# Knowledge base v2: retrieval before/after after Phase B3 (schedule items, community gating) (2026-10-06)

Retrieval only, no model calls. Raw question (no LLM rewrite), top 5, threshold 0.65 (unchanged). **OFF** = live v1 index (53739 chunks). **ON** = `KB_V2`: faiss_v2 (11289 section chunks) first, then v1 without the v1 chunks of any law v2 holds, merged by score. A `~` section on a v1 hit is inferred from text overlap with the kb records (v1 has no section field); "(contents/other)" = a v1 chunk of that law that matches no single section (a contents list, or text spanning sections).

A gold hit = an accepted section in the top 5 **and** at or above 0.65 (it would reach the model). Accept-either: G04 s.7 or s.9; G20 Art.17 or Art.79; G07/G10 FCA s.5 or the FCA Schedule.

## Summary

| | OFF | ON |
|---|---:|---:|
| Gold hit-rate at top 5, passing 0.65 | 7/26 (27%) | 14/26 (54%) |
| Gold in top 5 at any score | 9/26 | 18/26 |
| Off-topic questions passing 0.65 (would be answered) | 1/15 O14 | 1/15 O14 |
| Family CR-01..CR-08 with an expected section in top 5 (passing) | 0/7 | 1/7 |

**Got worse** (gold found OFF but lower or missing ON): none.

Gold hits lost at the threshold: G04, G05.

## Findings (Phase B3)

**What B3 changed.**
- **Schedule items:** the Family Courts Act Schedule is now 9 item records plus Part II. It's the only
  Schedule among the 35 laws that passes the "reliably numbered list" test. The others are:
  - forms (Christian, Special Marriage, Succession, Divorce Act);
  - tables (Limitation, Court-Fees, CrPC Schedule II);
  - repeal notes;
  - the CPC Rules;
  - Constitution lists whose numbering restarts or has gaps.

  They stay as they were.
- **Community gating:** the community-specific laws are now searched only when the question names the
  community or the Act.
- **Rebuild:** incremental. 10 new chunks were embedded and 11,279 vectors reused, in 48 s.

**Gold hit-rate: unchanged at 14/26** (OFF 7/26). Gating fixed the ranking but not the scores:
- **G05:** MFLO s.6 is back to rank 1 (Divorce Act / Special Marriage Act no longer outrank it). But it
  scores 0.618, still under 0.65.
- **G12:** DMMA s.2 is now rank 2, at 0.604.
- **G10:** FCA s.7 (institution of suits) is now rank 1 at 0.750. The gold s.5/Schedule still isn't in
  the top 50.

**Still worse than OFF.** Both are rank 1 in both runs but fail the threshold under ON:
- **G04:** passed OFF at 0.693; ON scores 0.558.
- **G05:** passed OFF at 0.691; ON scores 0.618.

In both, the v1 chunk that passed was an 800-character block holding several sub-sections together;
the 120-token section windows score lower. Nothing else lost rank.

**Not worse by the gold measure, but the top hit is now noise:**
- **CR-08:** with the Married Women's Property Act gated out, the top hits are v1 chunks of unrelated
  Acts (Chartered Accountants Ordinance 0.530). It's refused in both runs (OFF 0.621), so the outcome
  is unchanged.
- **CR-03:** it's still the Trusts Acts (v1) on top.

**FCA Schedule items in the top 5:**
- **CR-04:** yes. "Schedule item 4: Restitution of conjugal rights" is rank 4 at 0.696, so it reaches
  the model.
- **CR-02, CR-07:** no. The items rank 14 and 24 in the top 50 (rank 50 is the limit).
- **G07, G10:** no, not in the top 50.

Reason: a one-word item ("Dowry", "Dower") gives the embedding very little to match a long question.
The window carries the prefix "West Pakistan Family Courts Act, 1964 - Schedule item 8 Dowry: Dowry",
which is short.

**Off-topic:** still 1/15 at 0.65 (O14, Indian Penal Code, 0.783). O13 ("divorce in California")
dropped from 0.525 to 0.409, because the Christian divorce law is no longer offered for it.

**Threshold recommendation: keep KB_V2_THRESHOLD at 0.65 (default unchanged).**
- **0.62:** gives no gold gain over 0.65 (14/26 both). It answers 10 more of the 78 lawyer questions.
- **0.60:** gains 2 gold (G05, G12) and still lets only O14 through among the off-topic set. But the
  margin is 0.003: O10 (exchange rate) scores 0.597 and O12 (Thailand contract) 0.593. It would also
  answer 24 more of the 78 lawyer questions (35 vs 11).
- **Those 24, by my reading (developer judgment, not a lawyer's):** about 6 have a plausibly relevant
  top passage:
  - L01, DMMA;
  - L11, PPC s.361;
  - L14, MFLO s.7;
  - L30, FCA Schedule item 1, khula;
  - L52, MFLO s.7;
  - L73, PPC s.209.
- **The rest** have an unrelated Act on top (bank, sales tax, copyright, companies ordinance,
  ESTACODE, trusts) or are about foreign situations (Nigeria, the Philippines, Thailand, Doha).
- **Net:** lowering the threshold would mostly add weak or wrong answers. The better next step is
  raising the right sections' scores (G04/G05: windows that keep a section's sub-sections together;
  short schedule items), then re-checking.

## Threshold under KB_V2 (KB_V2_THRESHOLD; default left at 0.65)

Same raw-question retrieval, KB_V2 ON. **Answered** = the top passage scores at or above the threshold (otherwise the chat refuses). The 78 lawyer questions have no section labels, so for them only answered/refused is measured, not correctness; several are foreign-law questions (e.g. the Nigerian CAC one) that *should* be refused.

| Threshold | Lawyer questions answered / refused | Gold answered from the right section (top 5) | Off-topic that would pass |
|---|---|---|---|
| OFF (v1) at 0.65, for reference | 7 / 71 | 7/26 | 1/15 O14 |
| ON at 0.60 | 35 / 43 | 16/26 | 1/15 O14 |
| ON at 0.62 | 21 / 57 | 14/26 | 1/15 O14 |
| ON at 0.65 | 11 / 67 | 14/26 | 1/15 O14 |

## Score distribution with KB_V2 ON (does 0.65 still fit?)

| Set | Top-1 score |
|---|---|
| Gold questions (26) | min 0.516 · median 0.761 · max 0.918 |
| The gold section's own score (where found, 18) | min 0.516 · median 0.787 · max 0.918 |
| Off-topic (15) | min 0.286 · median 0.433 · max 0.783 |

- Gold top-1, sorted: 0.516, 0.558, 0.588, 0.608, 0.618, 0.658, 0.674, 0.675, 0.682, 0.700, 0.730, 0.750, 0.761, 0.762, 0.783, 0.784, 0.796, 0.796, 0.812, 0.835, 0.845, 0.848, 0.872, 0.884, 0.890, 0.918
- Off-topic top-1, sorted: 0.286, 0.291, 0.342, 0.384, 0.409, 0.413, 0.430, 0.433, 0.472, 0.494, 0.539, 0.540, 0.593, 0.597, 0.783

Gold sections found ON but scoring under 0.65 (refused): G04, G05, G07, G12. In the 0.65-0.70 weak band: G09, G11, G18. Highest off-topic top-1 ON: 0.783 (O14).

## FCA Schedule (dower, restitution, dowry, personal property)

| ID | Schedule rank OFF (top 5) | Schedule rank ON (top 5) | Score ON | Schedule rank ON, top 50 |
|---|---|---|---|---|
| CR-01 | – | – | – | > 50 |
| CR-02 | – | – | – | 14 |
| CR-03 | – | – | – | 21 |
| CR-04 | – | 4 (Schedule item 4) | 0.696 | 4 |
| CR-05 | – | – | – | 26 |
| CR-06 | – | – | – | > 50 |
| CR-07 | – | – | – | 24 |
| CR-08 | – | – | – | > 50 |
| G07 | – | – | – | > 50 |
| G10 | – | – | – | > 50 |

## Per question (top 3)

| ID | OFF top 3 | ON top 3 | Gold rank OFF → ON |
|---|---|---|---|
| **G01** On what grounds can a Muslim woman obtain a decree for the dissolution… | 1. Dissolution of Muslim Marriages Act, 1939 s.2 ~ (0.822)<br>2. Dissolution of Muslim Marriages Act, 1939 (contents/other) (0.796)<br>3. Dissolution of Muslim Marriages Act, 1939 s.4 ~ (0.774) | 1. Dissolution of Muslim Marriages Act, 1939 s.2 (0.884)<br>2. Dissolution of Muslim Marriages Act, 1939 s.4 (0.818)<br>3. Dissolution of Muslim Marriages Act, 1939 s.5 (0.812) | 1 → 1 |
| **G02** What is the punishment for qatl-i-amd under the Pakistan Penal Code? | 1. Code of Criminal Procedure, 1898 s.345 ~ (0.776)<br>2. Pakistan Penal Code, 1860 s.304 ~ (0.751)<br>3. Code of Criminal Procedure, 1898 s.565 ~ (0.746) | 1. Pakistan Penal Code, 1860 s.302 (0.890)<br>2. Pakistan Penal Code, 1860 s.303 (0.864)<br>3. Pakistan Penal Code, 1860 s.308 (0.863) | 5 → 1 |
| **G03** What are the essential elements of a valid contract under the Contract… | 1. THE FUTURES MARKET ACT, 2016 (0.672)<br>2. THE CAPITAL TERRITORY TRUST ACT, 2020 (0.668)<br>3. THE INTERNATIONAL MONETARY FUND AND BANK ACT, 1950 (0.663) | 1. Contract Act, 1872 s.1 (0.762)<br>2. Contract Act, 1872 s.23 (0.748)<br>3. Contract Act, 1872 s.68 (0.718) | ✗ → ✗ (ON top 50: 38) |
| **G04** If a husband pronounces talaq while his wife is pregnant, when does th… | 1. Muslim Family Laws Ordinance, 1961 s.7 ~ (0.693)<br>2. Muslim Family Laws Ordinance, 1961 s.7 ~ (0.541)<br>3. Muslim Family Laws Ordinance, 1961 s.7 ~ (0.529) | 1. Muslim Family Laws Ordinance, 1961 s.7 (0.558)<br>2. THE WEST PAKISTAN MATERNITY BENEFIT ORDINANCE, 1958 (0.459)<br>3. Pakistan Penal Code, 1860 s.314 (0.442) | 1 → 1 |
| **G05** Can a husband marry a second wife without the permission of the Arbitr… | 1. Muslim Family Laws Ordinance, 1961 s.6 ~ (0.691)<br>2. Muslim Family Laws Ordinance, 1961 s.6 ~ (0.669)<br>3. Specific Relief Act, 1877 s.43 ~ (0.644) | 1. Muslim Family Laws Ordinance, 1961 s.6 (0.618)<br>2. Child Marriage Restraint Act, 1929 s.12 (0.605)<br>3. THE TRUSTS ACT, 1882 (0.585) | 1 → 1 |
| **G06** What is the procedure for talaq under the Muslim Family Laws Ordinance… | 1. Muslim Family Laws Ordinance, 1961 s.2 ~ (0.687)<br>2. Muslim Family Laws Ordinance, 1961 (contents/other) (0.665)<br>3. Muslim Family Laws Ordinance, 1961 s.11 ~ (0.654) | 1. Muslim Family Laws Ordinance, 1961 s.7 (0.784)<br>2. Muslim Family Laws Ordinance, 1961 s.4 (0.733)<br>3. Muslim Family Laws Ordinance, 1961 s.3 (0.726) | ✗ → 1 |
| **G07** What can a wife do if her husband does not pay her maintenance? | 1. Muslim Family Laws Ordinance, 1961 s.9 ~ (0.549)<br>2. Married Women's Property Act, 1874 s.8 ~ (0.543)<br>3. Muslim Family Laws Ordinance, 1961 s.9 ~ (0.526) | 1. Muslim Family Laws Ordinance, 1961 s.9 (0.516)<br>2. ISLAMABAD CAPITAL TERRITORY SENIOR CITIZENS ACT, 2021 (0.469)<br>3. i For Official Use ESTACODE (EDITION -2021 (0.464) | 1 → 1 |
| **G08** Can a grandchild inherit from the grandfather if the grandchild's fath… | 1. Succession Act, 1925 s.38 ~ (0.674)<br>2. Succession Act, 1925 s.40 ~ (0.614)<br>3. Succession Act, 1925 Schedule 2 ~ (0.607) | 1. Succession Act, 1925 s.53 (0.658)<br>2. Succession Act, 1925 s.48 (0.641)<br>3. Succession Act, 1925 s.40 (0.636) | ✗ → ✗ (ON top 50: 16) |
| **G09** How can a mother get custody of her minor child under the Guardians an… | 1. Hindu Widows' Re-marriage Act, 1856 s.3 ~ (0.684)<br>2. THE ISLAMABAD CAPITAL TERRITORY PROHIBITION OF CORPORAL PUNISHMENT ACT, 2021 (0.648)<br>3. THE ISLAMABAD CAPITAL TERRITORY CHILD PROTECTION ACT, 2018 (0.646) | 1. Guardians and Wards Act, 1890 s.21 (0.730)<br>2. Guardians and Wards Act, 1890 s.12 (0.688)<br>3. Guardians and Wards Act, 1890 s.25 (0.687) | ✗ → 3 |
| **G10** Which court hears suits for dissolution of marriage, dower and mainten… | 1. Parsi Marriage and Divorce Act, 1936 (contents/other) (0.729)<br>2. Parsi Marriage and Divorce Act, 1936 s.34 ~ (0.722)<br>3. Divorce Act, 1869 s.39 ~ (0.693) | 1. West Pakistan Family Courts Act, 1964 s.7 (0.750)<br>2. West Pakistan Family Courts Act, 1964 s.10 (0.655)<br>3. Succession Act, 1925 s.295 (0.651) | ✗ → ✗ (ON top 50: > 50) |
| **G11** What happens at the pre-trial stage of a case in a Family Court? | 1. West Pakistan Family Courts Act, 1964 s.9 ~ (0.633)<br>2. West Pakistan Family Courts Act, 1964 s.10 ~ (0.629)<br>3. THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 (0.617) | 1. West Pakistan Family Courts Act, 1964 s.10 (0.700)<br>2. West Pakistan Family Courts Act, 1964 s.9 (0.671)<br>3. THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 (0.617) | 2 → 1 |
| **G12** Can a wife get her marriage dissolved if her husband has not maintaine… | 1. Parsi Marriage and Divorce Act, 1936 s.31 ~ (0.678)<br>2. Pakistan Penal Code, 1860 s.494 ~ (0.613)<br>3. Divorce Act, 1869 s.10 ~ (0.612) | 1. Pakistan Penal Code, 1860 s.494 (0.608)<br>2. Dissolution of Muslim Marriages Act, 1939 s.2 (0.604)<br>3. THE HINDU MARRIAGE ACT, 2017 (0.595) | ✗ → 2 |
| **G13** How does the Pakistan Penal Code define qatl-i-amd? | 1. THE COMPANIES ACT, 2017 (0.690)<br>2. THE PROHIBITION (ENFORCEMENT OF HADD) ORDER (4 OF 1979 (0.681)<br>3. Pakistan Penal Code, 1860 s.75 ~ (0.673) | 1. Pakistan Penal Code, 1860 s.299 (0.812)<br>2. Pakistan Penal Code, 1860 s.302 (0.782)<br>3. Pakistan Penal Code, 1860 s.324 (0.769) | ✗ → ✗ (ON top 50: > 50) |
| **G14** What is the punishment for cheating and dishonestly inducing delivery … | 1. Pakistan Penal Code, 1860 s.420 ~ (0.869)<br>2. Pakistan Penal Code, 1860 (contents/other) (0.741)<br>3. Pakistan Penal Code, 1860 s.415 ~ (0.717) | 1. Pakistan Penal Code, 1860 s.420 (0.761)<br>2. Pakistan Penal Code, 1860 s.421 (0.719)<br>3. Pakistan Penal Code, 1860 s.414 (0.711) | 1 → 1 |
| **G15** What is the punishment for defamation under the Pakistan Penal Code? | 1. THE PAKISTAN ARMY ACT, 1952 (0.755)<br>2. Code of Criminal Procedure, 1898 Schedule 5 ~ (0.735)<br>3. Pakistan Penal Code, 1860 s.295A ~ (0.728) | 1. Pakistan Penal Code, 1860 s.500 (0.845)<br>2. Pakistan Penal Code, 1860 s.499 (0.824)<br>3. Pakistan Penal Code, 1860 s.284 (0.782) | ✗ → 1 |
| **G16** What is the punishment for theft? | 1. Pakistan Penal Code, 1860 s.380 ~ (0.819)<br>2. Pakistan Penal Code, 1860 (contents/other) (0.808)<br>3. ANTI -MONEY LAUNDERING ACT, 2010 (0.771) | 1. Pakistan Penal Code, 1860 s.379 (0.835)<br>2. Pakistan Penal Code, 1860 s.382 (0.792)<br>3. ANTI -MONEY LAUNDERING ACT, 2010 (0.771) | ✗ → 1 |
| **G17** When can bail be granted in a non-bailable offence? | 1. Code of Criminal Procedure, 1898 s.497 ~ (0.817)<br>2. Code of Criminal Procedure, 1898 s.497 ~ (0.800)<br>3. Code of Criminal Procedure, 1898 (contents/other) (0.761) | 1. Code of Criminal Procedure, 1898 s.497 (0.796)<br>2. Code of Criminal Procedure, 1898 s.496 (0.776)<br>3. Code of Criminal Procedure, 1898 s.498A (0.729) | 1 → 1 |
| **G18** How is a First Information Report recorded for a cognizable offence? | 1. THE POLICE ACT 1861 (0.682)<br>2. Code of Criminal Procedure, 1898 s.190 ~ (0.672)<br>3. Code of Criminal Procedure, 1898 s.265C ~ (0.664) | 1. THE POLICE ACT 1861 (0.682)<br>2. Code of Criminal Procedure, 1898 s.154 (0.656)<br>3. Code of Criminal Procedure, 1898 s.241A (0.645) | ✗ → 2 |
| **G19** What is the punishment for rape under the Pakistan Penal Code? | 1. Pakistan Penal Code, 1860 (contents/other) (0.753)<br>2. Code of Criminal Procedure, 1898 s.234 ~ (0.740)<br>3. Code of Criminal Procedure, 1898 s.565 ~ (0.739) | 1. Pakistan Penal Code, 1860 s.376 (0.918)<br>2. Pakistan Penal Code, 1860 s.374 (0.845)<br>3. Pakistan Penal Code, 1860 s.375 (0.814) | ✗ → 1 |
| **G20** How many witnesses are required to attest a document creating a financ… | 1. THE DRUG REGULATORY AUTHORITY OF PAKISTAN ACT, 2012 (0.675)<br>2. THE INCOME TAX ORDINANCE, 2001 (0.672)<br>3. THE PAKISTAN AIR FORCE ACT, 1953 (0.671) | 1. THE DRUG REGULATORY AUTHORITY OF PAKISTAN ACT, 2012 (0.675)<br>2. THE INCOME TAX ORDINANCE, 2001 (0.672)<br>3. THE PAKISTAN AIR FORCE ACT, 1953 (0.671) | ✗ → ✗ (ON top 50: 6) |
| **G21** Is the right to a fair trial a fundamental right in Pakistan? | 1. THE INVESTIGATION FOR FAIR TRIAL ACT, 2013 (0.742)<br>2. THE MUTUAL LEGAL ASSISTANCE (CRIMINAL MATTERS) ACT, 2020 (0.698)<br>3. THE INLAND MECHANICALLY PROPELLED VESSELS ACT, 1917 (0.655) | 1. Constitution of the Islamic Republic of Pakistan, 1973 s.10A (0.848)<br>2. THE INVESTIGATION FOR FAIR TRIAL ACT, 2013 (0.742)<br>3. THE MUTUAL LEGAL ASSISTANCE (CRIMINAL MATTERS) ACT, 2020 (0.698) | ✗ → 1 |
| **G22** What is the writ jurisdiction of a High Court? | 1. THE BANKING COMPANIES ORDINANCE, 1962 (0.783)<br>2. THE MAINTENANCE ORDERS ENFORCEMENT ACT, 1921 (0.776)<br>3. Code of Civil Procedure, 1908 s.23 ~ (0.761) | 1. THE BANKING COMPANIES ORDINANCE, 1962 (0.783)<br>2. THE MAINTENANCE ORDERS ENFORCEMENT ACT, 1921 (0.776)<br>3. Code of Civil Procedure, 1908 s.116 (0.757) | ✗ → ✗ (ON top 50: > 50) |
| **G23** What compensation can be claimed for breach of contract? | 1. Specific Relief Act, 1877 s.19 ~ (0.783)<br>2. THE WEST PAKISTAN MATERNITY BENEFIT ORDINANCE, 1958 (0.703)<br>3. Specific Relief Act, 1877 s.19 ~ (0.702) | 1. Contract Act, 1872 s.74 (0.796)<br>2. Contract Act, 1872 s.73 (0.791)<br>3. Specific Relief Act, 1877 s.19 (0.778) | ✗ → 2 |
| **G24** How is a sale of immovable property made under the Transfer of Propert… | 1. Transfer of Property Act, 1882 s.41 ~ (0.793)<br>2. Transfer of Property Act, 1882 s.54 ~ (0.786)<br>3. Transfer of Property Act, 1882 s.49 ~ (0.786) | 1. Transfer of Property Act, 1882 s.54 (0.872)<br>2. Transfer of Property Act, 1882 s.55 (0.840)<br>3. Transfer of Property Act, 1882 s.100 (0.819) | 2 → 1 |
| **G25** Can a person file a suit for a declaration of their title to property? | 1. Qanun-e-Shahadat Order, 1984 s.13 ~ (0.693)<br>2. Code of Civil Procedure, 1908 Schedule 1 ~ (0.683)<br>3. Specific Relief Act, 1877 s.25 ~ (0.677) | 1. THE CAPITAL TERRITORY TRUST ACT, 2020 (0.674)<br>2. THE CAPITAL TERRITORY TRUST ACT, 2020 (0.653)<br>3. THE COMPANIES ACT, 2017 (0.636) | ✗ → ✗ (ON top 50: > 50) |
| **G26** Can a minor enter into a valid contract? | 1. THE LIMITED LIABILITY PARTNERSHIP ACT, 2017 (0.588)<br>2. UNDER PROOF READING Page 1 of 24 THE PARTNERSHIP ACT, 1932 (0.586)<br>3. THE PAKISTAN AIR FORCE ACT, 1953 (0.582) | 1. THE LIMITED LIABILITY PARTNERSHIP ACT, 2017 (0.588)<br>2. UNDER PROOF READING Page 1 of 24 THE PARTNERSHIP ACT, 1932 (0.586)<br>3. THE PAKISTAN AIR FORCE ACT, 1953 (0.582) | ✗ → ✗ (ON top 50: > 50) |
| **O01** What is the capital of Australia and how many people live there? | 1. Code of Civil Procedure, 1908 (contents/other) (0.508)<br>2. Code of Civil Procedure, 1908 s.47 ~ (0.471)<br>3. THE CAPITAL OF THE REPUBLIC (DETERMINATION OF AREA) ORDINANCE,1963 (0.413) | 1. THE CAPITAL OF THE REPUBLIC (DETERMINATION OF AREA) ORDINANCE,1963 (0.413)<br>2. THE SUITS VALUATION ACT, 1887 (0.372)<br>3. THE KARACH PORT TRUST ACT, 1886 (0.369) | – |
| **O02** What is the weather forecast for Lahore tomorrow? | 1. THE CAPITAL OF THE REPUBLIC (DETERMINATION OF AREA) ORDINANCE,1963 (0.472)<br>2. i For Official Use ESTACODE (EDITION -2021 (0.471)<br>3. THE CAPITAL DEVELOPMENT AUTHORITY ORDINANCE, 1960 (0.456) | 1. THE CAPITAL OF THE REPUBLIC (DETERMINATION OF AREA) ORDINANCE,1963 (0.472)<br>2. i For Official Use ESTACODE (EDITION -2021 (0.471)<br>3. THE CAPITAL DEVELOPMENT AUTHORITY ORDINANCE, 1960 (0.456) | – |
| **O03** Give me a recipe for chocolate cake. | 1. Sales Tax Act, 1990 (0.286)<br>2. THE ISLAMABAD CAPITAL TERRITORY LOCAL GOVERNMENT ACT, 2015 (0.231)<br>3. THE PAKISTAN HALAL AUTHORITY ACT, 2016 (0.230) | 1. Sales Tax Act, 1990 (0.286)<br>2. THE ISLAMABAD CAPITAL TERRITORY LOCAL GOVERNMENT ACT, 2015 (0.231)<br>3. THE PAKISTAN HALAL AUTHORITY ACT, 2016 (0.230) | – |
| **O04** Who won the Cricket World Cup in 1992? | 1. THE PORTS ACT, 1908 (0.342)<br>2. THE ARCHIV AL MA T ERIAL (PRESER V A TI ON AND EXPOR T CONTROL) ACT ,1975 (0.342)<br>3. THE PAKISTAN COINAGE ACT, 1906 (0.337) | 1. THE PORTS ACT, 1908 (0.342)<br>2. THE ARCHIV AL MA T ERIAL (PRESER V A TI ON AND EXPOR T CONTROL) ACT ,1975 (0.342)<br>3. THE PAKISTAN COINAGE ACT, 1906 (0.337) | – |
| **O05** How do I reset my Wi-Fi router? | 1. THE PAKISTAN TELECO MM UNICATION (RE-ORGANIZATION) ACT , 1996 (0.291)<br>2. THE CARRIAGE BY AIR ACT, 2012 (0.289)<br>3. THE NATIONAL HIGHWAY AUTHORITY ACT , 1991 (0.273) | 1. THE PAKISTAN TELECO MM UNICATION (RE-ORGANIZATION) ACT , 1996 (0.291)<br>2. THE CARRIAGE BY AIR ACT, 2012 (0.289)<br>3. THE NATIONAL HIGHWAY AUTHORITY ACT , 1991 (0.273) | – |
| **O06** What is the best smartphone under 50,000 rupees? | 1. Sales Tax Act, 1990 (0.539)<br>2. The Federal Excise Act, 2005 (0.379)<br>3. THE INCOME TAX ORDINANCE, 2001 (0.361) | 1. Sales Tax Act, 1990 (0.539)<br>2. The Federal Excise Act, 2005 (0.379)<br>3. THE INCOME TAX ORDINANCE, 2001 (0.361) | – |
| **O07** Explain how photosynthesis works. | 1. THE PA KISTAN CLIMATE CHANGE ACT, 2017 (0.494)<br>2. THE PAKISTAN ATOMIC ENERGY COMMISSION ORDINANCE, 1965 (0.390)<br>3. THE CHEMICAL WEAPONS CONVENTION IMPLEMENTATION ORDINANCE, 2000 (0.388) | 1. THE PA KISTAN CLIMATE CHANGE ACT, 2017 (0.494)<br>2. THE PAKISTAN ATOMIC ENERGY COMMISSION ORDINANCE, 1965 (0.390)<br>3. THE CHEMICAL WEAPONS CONVENTION IMPLEMENTATION ORDINANCE, 2000 (0.388) | – |
| **O08** Write a poem about the monsoon. | 1. THE COPYRIGHT ORDINANCE, 1962 (0.433)<br>2. THE MANOEUVRES, FIELD FIRING AND ARTILLERY PRACTICE ACT, 1938 (0.384)<br>3. administrator888bc6d1009f9fb0809dd695f28e21b5 (0.373) | 1. THE COPYRIGHT ORDINANCE, 1962 (0.433)<br>2. THE MANOEUVRES, FIELD FIRING AND ARTILLERY PRACTICE ACT, 1938 (0.384)<br>3. administrator888bc6d1009f9fb0809dd695f28e21b5 (0.373) | – |
| **O09** How many calories are in a plate of biryani? | 1. THE STANDARDS OF WEIGHT ACT, 1939 (0.384)<br>2. GOVERNMENT OF PAKISTAN REVENUE DIVISION FEDERA L BOARD OF REVENUE ***** THE CUSTOMS ACT, 1969 (0.354)<br>3. Divorce Act, 1869 Schedule ~ (0.345) | 1. THE STANDARDS OF WEIGHT ACT, 1939 (0.384)<br>2. GOVERNMENT OF PAKISTAN REVENUE DIVISION FEDERA L BOARD OF REVENUE ***** THE CUSTOMS ACT, 1969 (0.354)<br>3. i For Official Use ESTACODE (EDITION -2021 (0.342) | – |
| **O10** What is the exchange rate of the US dollar today? | 1. THE NEGOTIABLE INSTRUMENTS ACT, 1881 (0.597)<br>2. THE FOREIGN EXCHANGE (TEMPORARY RESTRICTIONS) ACT, 1998 (0.566)<br>3. FOREIGN ASSETS (DECLARATION AND REPATRIATION) ACT, 2018 (0.529) | 1. THE NEGOTIABLE INSTRUMENTS ACT, 1881 (0.597)<br>2. THE FOREIGN EXCHANGE (TEMPORARY RESTRICTIONS) ACT, 1998 (0.566)<br>3. FOREIGN ASSETS (DECLARATION AND REPATRIATION) ACT, 2018 (0.529) | – |
| **O11** How do I register a company with the Corporate Affairs Commission in N… | 1. THE PAKISTAN INSURANCE CORPORATION ACT, 1952 (0.540)<br>2. [As Amended Up-to-Date Till 2012 (0.540)<br>3. THE COMP ANIES ORDINANCE, 1984 (0.540) | 1. THE PAKISTAN INSURANCE CORPORATION ACT, 1952 (0.540)<br>2. [As Amended Up-to-Date Till 2012 (0.540)<br>3. THE COMP ANIES ORDINANCE, 1984 (0.540) | – |
| **O12** Is a verbal contract enforceable in Thailand? | 1. THE ARBITRATION (INTERNATIONAL INVESTMENT DISPUTES) ACT, 2011 (0.593)<br>2. Limitation Act, 1908 s.11 ~ (0.581)<br>3. THE ESSO UNDERT AKINGS (VESTING) ACT, 1976 (0.571) | 1. THE ARBITRATION (INTERNATIONAL INVESTMENT DISPUTES) ACT, 2011 (0.593)<br>2. Contract Act, 1872 s.2 (0.576)<br>3. THE ESSO UNDERT AKINGS (VESTING) ACT, 1976 (0.571) | – |
| **O13** How do I file for divorce in California? | 1. Divorce Act, 1869 s.29 ~ (0.467)<br>2. Parsi Marriage and Divorce Act, 1936 s.34 ~ (0.446)<br>3. Parsi Marriage and Divorce Act, 1936 (contents/other) (0.437) | 1. Court-Fees Act, 1870 Schedule 2 (0.409)<br>2. THE BIRTHS, DEATHS AND MARRIAGES REGISTRATION ACT, 1886 (0.392)<br>3. THE ISLAMABAD CAPITAL TERRITORY DOMESTIC WORKERS ACT, 2022 (0.383) | – |
| **O14** What is the punishment for murder under the Indian Penal Code? | 1. Pakistan Penal Code, 1860 s.109 ~ (0.742)<br>2. Code of Criminal Procedure, 1898 s.34 ~ (0.728)<br>3. THE CREDIT BUREAUS ACT, 2015 (0.727) | 1. Pakistan Penal Code, 1860 s.115 (0.783)<br>2. Pakistan Penal Code, 1860 s.109 (0.781)<br>3. Pakistan Penal Code, 1860 s.108 (0.775) | – |
| **O15** How do I apply for a UK student visa? | 1. THE PAKISTAN MEDICAL COMMISSION ACT, 2020 (0.430)<br>2. THE FEDERAL UNIVERSITIES ORDINANCE, 2002 (0.396)<br>3. i For Official Use ESTACODE (EDITION -2021 (0.393) | 1. THE PAKISTAN MEDICAL COMMISSION ACT, 2020 (0.430)<br>2. THE FEDERAL UNIVERSITIES ORDINANCE, 2002 (0.396)<br>3. i For Official Use ESTACODE (EDITION -2021 (0.393) | – |
| **CR-01** Why is the Nikah Nama important in a dower dispute? | 1. i For Official Use ESTACODE (EDITION -2021 (0.492)<br>2. THE BENAMI TRANSACTIONS (PROHIBITION) ACT, 2017 (0.481)<br>3. Muslim Family Laws Ordinance, 1961 s.4 ~ (0.479) | 1. i For Official Use ESTACODE (EDITION -2021 (0.492)<br>2. Muslim Family Laws Ordinance, 1961 s.10 (0.487)<br>3. THE BENAMI TRANSACTIONS (PROHIBITION) ACT, 2017 (0.481) | ✗ → 2 |
| **CR-02** A wife claims that her dowry articles remain in the husband's possessi… | 1. Married Women's Property Act, 1874 s.8 ~ (0.643)<br>2. Divorce Act, 1869 s.27 ~ (0.623)<br>3. Married Women's Property Act, 1874 (contents/other) (0.609) | 1. West Pakistan Family Courts Act, 1964 s.7 (0.588)<br>2. Muslim Family Laws Ordinance, 1961 s.9 (0.582)<br>3. Succession Act, 1925 s.15 (0.560) | ✗ → ✗ (ON top 50: 14) |
| **CR-03** Can a spouse lawfully retain the other's personal property merely beca… | 1. Married Women's Property Act, 1874 s.8 ~ (0.687)<br>2. THE CAPITAL TERRITORY TRUST ACT, 2020 (0.673)<br>3. THE TRUSTS ACT, 1882 (0.659) | 1. THE CAPITAL TERRITORY TRUST ACT, 2020 (0.673)<br>2. THE TRUSTS ACT, 1882 (0.659)<br>3. THE INSOLVANCY (KARACHI DIVISION) ACT,1909 (0.628) | ✗ → ✗ (ON top 50: 21) |
| **CR-04** What is a suit for restitution of conjugal rights? | 1. Code of Civil Procedure, 1908 Schedule 1 ~ (0.752)<br>2. Divorce Act, 1869 s.32 ~ (0.740)<br>3. Parsi Marriage and Divorce Act, 1936 s.38 ~ (0.709) | 1. West Pakistan Family Courts Act, 1964 s.9 (0.745)<br>2. Guardians and Wards Act, 1890 s.45 (0.704)<br>3. Specific Relief Act, 1877 s.35 (0.700) | ✗ → 1 |
| **CR-05** Why is territorial jurisdiction important in a Family Court case? | 1. THE INSOLVANCY (KARACHI DIVISION) ACT,1909 (0.624)<br>2. Code of Civil Procedure, 1908 s.16 ~ (0.621)<br>3. THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 (0.613) | 1. West Pakistan Family Courts Act, 1964 s.25 (0.643)<br>2. THE INSOLVANCY (KARACHI DIVISION) ACT,1909 (0.624)<br>3. West Pakistan Family Courts Act, 1964 s.5 (0.620) | ✗ → 3 |
| **CR-06** Can a family-law advocate knowingly present false facts before the cou… | 1. Qanun-e-Shahadat Order, 1984 (contents/other) (0.622)<br>2. Qanun-e-Shahadat Order, 1984 s.47 ~ (0.610)<br>3. Pakistan Penal Code, 1860 s.191 ~ (0.603) | 1. West Pakistan Family Courts Act, 1964 s.11 (0.644)<br>2. Qanun-e-Shahadat Order, 1984 s.47 (0.622)<br>3. Qanun-e-Shahadat Order, 1984 s.113 (0.594) | – |
| **CR-07** A wife files a suit seeking dissolution of marriage, unpaid dower, mai… | 1. Married Women's Property Act, 1874 s.8 ~ (0.727)<br>2. Specific Relief Act, 1877 s.43 ~ (0.681)<br>3. Divorce Act, 1869 s.25 ~ (0.675) | 1. West Pakistan Family Courts Act, 1964 s.7 (0.683)<br>2. Succession Act, 1925 s.16 (0.656)<br>3. Code of Criminal Procedure, 1898 s.199 (0.645) | ✗ → ✗ (ON top 50: 15) |
| **CR-08** If a wife claims unpaid dower, who must establish the relevant facts? | 1. Married Women's Property Act, 1874 s.8 ~ (0.621)<br>2. Married Women's Property Act, 1874 s.9 ~ (0.583)<br>3. Qanun-e-Shahadat Order, 1984 s.18 ~ (0.570) | 1. THE CHARTERED ACCOUNTANTS ORDINANCE, 1961 (0.530)<br>2. THE COMP ANIES ORDINANCE, 1984 (0.522)<br>3. THE MOTOR VEHICLES ACT, 1939 (0.506) | ✗ → ✗ (ON top 50: > 50) |
