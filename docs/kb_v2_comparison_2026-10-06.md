# Knowledge base v2: retrieval before/after (2026-10-06)

Retrieval only, no model calls. Raw question (no LLM rewrite), top 5, threshold 0.65 (unchanged). **OFF** = live v1 index (53739 chunks). **ON** = `KB_V2`: faiss_v2 (11281 section chunks) first, then v1 without the v1 chunks of any law v2 holds, merged by score. A `~` section on a v1 hit is inferred from text overlap with the kb records (v1 has no section field); "(contents/other)" = a v1 chunk of that law that matches no single section (a contents list, or text spanning sections).

A gold hit = an accepted section in the top 5 **and** at or above 0.65 (it would reach the model). Accept-either: G04 s.7 or s.9; G20 Art.17 or Art.79; G07/G10 FCA s.5 or the FCA Schedule.

## Summary

| | OFF | ON |
|---|---:|---:|
| Gold hit-rate at top 5, passing 0.65 | 7/26 (27%) | 14/26 (54%) |
| Gold in top 5 at any score | 9/26 | 18/26 |
| Off-topic questions passing 0.65 (would be answered) | 1/15 O14 | 1/15 O14 |
| Family CR-01..CR-08 with an expected section in top 5 (passing) | 0/7 | 1/7 |

**Got worse** (gold found OFF but lower or missing ON): G05 (rank 1 → 3).

Gold hits lost at the threshold: G04, G05.

## Findings

**What improved** (gold hit-rate 7/26 → 14/26):
- **Seven gold sections now reach the model that didn't before:**
  - PPC s.302, s.500, s.379 and s.376 (G02, G15, G16, G19);
  - MFLO s.7 (G06);
  - Guardians and Wards s.25 (G09, rank 3);
  - Constitution Art. 10A (G21);
  - plus CrPC s.154 (G18, rank 2) and Contract Act s.73 (G23, rank 2).
- **Scores at the old hits went up:** G01 0.822 → 0.884; G24 0.793 → 0.872 (now rank 1).

**What got worse, honestly:**
- **G04 (talaq while pregnant).** MFLO s.7 is still rank 1, but at 0.558 instead of 0.693, so it now
  falls under 0.65 and the question would be refused. The v1 chunk that scored 0.693 was a single
  800-character chunk holding s.7's sub-sections together. The v2 windows are 120 tokens each, and none
  holds "pregnant" + "talaq" + "effective" as compactly.
- **G05 (second wife without permission).** MFLO s.6 drops from rank 1 (0.691) to rank 3 (0.618, under
  0.65). Divorce Act 1869 s.28 and Special Marriage Act 1872 s.7 outrank it.
- **The pattern behind G05:** the minority-community family statutes are now cleanly sectioned:
  - the Divorce Act 1869;
  - the Parsi Marriage and Divorce Act;
  - the Married Women's Property Act;
  - the Special Marriage Act.

  As a result, they win general family questions:
  - G05, G10 and G12;
  - CR-02, CR-04 and CR-07, where the top hits are Divorce Act / Parsi Act / Married Women's
    Property Act sections.

  This is the same crowding the family side index handled with its "minority" tier (searched only
  when the question names a community).
- **G07, G12:** the gold section is found, but under 0.65. G07 is 0.549 OFF and 0.516 ON, so neither
  passes.

**Still missing in both** (gold not in the ON top 50 unless noted):
- G03 Contract s.10 (rank 38);
- G08 MFLO s.4 (rank 16);
- G10 FCA s.5;
- G13 PPC s.300 (s.299 ranks 1);
- G20 QSO Art.17/79 (rank 6);
- G22 Constitution Art.199;
- G25 SRA s.42;
- G26 Contract s.11.

**FCA Schedule: no, it still doesn't reach the top 5. It isn't even in the top 50** for CR-02, CR-04,
CR-07, G07 or G10. Measured directly, the Schedule's first chunk scores:
- 0.458 for CR-04 ("restitution of conjugal rights"), against a 50th-place score of 0.623;
- 0.448 for CR-02 (dowry);
- 0.601 for G10.

The cause is that the chunk is a **list of nine matters**, and a list embeds as "a list of family
matters", not as any one item. A test vector made of the item alone ("Restitution of conjugal
rights.") scores 0.890 against CR-04, while the cleaned full list scores 0.411. So OCR isn't the
problem; list-shaped text is. **Proposed fix (not done):** chunk list-type schedules one item per
chunk ("West Pakistan Family Courts Act, 1964 - Schedule Part I item 4: Restitution of conjugal
rights"). That's still one window from one section, within the 120-token rule.

**Off-topic:** unchanged at 1/15 passing. O14 ("murder under the Indian Penal Code") passes in both,
at 0.742 OFF and 0.783 ON (PPC s.302). It's genuinely close to Pakistani law (question 4 in the gold
set draft).

**Does 0.65 still fit?**
- **The gap still holds:** off-topic top-1 scores ON are 0.286–0.597 (except O14), and the gold
  sections that are found median 0.787.
- **But some real questions sit just under 0.65:** four found gold sections score 0.516–0.639
  (G04, G05, G07, G12).
- **Lowering the threshold to about 0.60** would admit them, and no off-topic question except O14
  scores above 0.597 (O10, the exchange rate). That margin is thin, so it needs the 78-question set
  before any change. Not changed here.

## Score distribution with KB_V2 ON (does 0.65 still fit?)

| Set | Top-1 score |
|---|---|
| Gold questions (26) | min 0.516 · median 0.769 · max 0.918 |
| The gold section's own score (where found, 18) | min 0.516 · median 0.787 · max 0.918 |
| Off-topic (15) | min 0.286 · median 0.472 · max 0.783 |

- Gold top-1, sorted: 0.516, 0.558, 0.588, 0.633, 0.639, 0.658, 0.674, 0.675, 0.682, 0.700, 0.730, 0.761, 0.762, 0.776, 0.783, 0.784, 0.796, 0.796, 0.812, 0.835, 0.845, 0.848, 0.872, 0.884, 0.890, 0.918
- Off-topic top-1, sorted: 0.286, 0.291, 0.342, 0.384, 0.413, 0.430, 0.433, 0.472, 0.494, 0.525, 0.539, 0.540, 0.593, 0.597, 0.783

Gold sections found ON but scoring under 0.65 (refused): G04, G05, G07, G12. In the 0.65-0.70 weak band: G09, G11, G18. Highest off-topic top-1 ON: 0.783 (O14).

## FCA Schedule (dower, restitution, dowry, personal property)

| ID | Schedule rank OFF (top 5) | Schedule rank ON (top 5) | Score ON | Schedule rank ON, top 50 |
|---|---|---|---|---|
| CR-01 | – | – | – | > 50 |
| CR-02 | – | – | – | > 50 |
| CR-03 | – | – | – | > 50 |
| CR-04 | – | – | – | > 50 |
| CR-05 | – | – | – | > 50 |
| CR-06 | – | – | – | > 50 |
| CR-07 | – | – | – | > 50 |
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
| **G05** Can a husband marry a second wife without the permission of the Arbitr… | 1. Muslim Family Laws Ordinance, 1961 s.6 ~ (0.691)<br>2. Muslim Family Laws Ordinance, 1961 s.6 ~ (0.669)<br>3. Specific Relief Act, 1877 s.43 ~ (0.644) | 1. Divorce Act, 1869 s.28 (0.633)<br>2. Special Marriage Act, 1872 s.7 (0.622)<br>3. Muslim Family Laws Ordinance, 1961 s.6 (0.618) | 1 → 3 |
| **G06** What is the procedure for talaq under the Muslim Family Laws Ordinance… | 1. Muslim Family Laws Ordinance, 1961 s.2 ~ (0.687)<br>2. Muslim Family Laws Ordinance, 1961 (contents/other) (0.665)<br>3. Muslim Family Laws Ordinance, 1961 s.11 ~ (0.654) | 1. Muslim Family Laws Ordinance, 1961 s.7 (0.784)<br>2. Muslim Family Laws Ordinance, 1961 s.4 (0.733)<br>3. Muslim Family Laws Ordinance, 1961 s.3 (0.726) | ✗ → 1 |
| **G07** What can a wife do if her husband does not pay her maintenance? | 1. Muslim Family Laws Ordinance, 1961 s.9 ~ (0.549)<br>2. Married Women's Property Act, 1874 s.8 ~ (0.543)<br>3. Muslim Family Laws Ordinance, 1961 s.9 ~ (0.526) | 1. Muslim Family Laws Ordinance, 1961 s.9 (0.516)<br>2. Married Women's Property Act, 1874 s.9 (0.506)<br>3. Married Women's Property Act, 1874 s.10 (0.506) | 1 → 1 |
| **G08** Can a grandchild inherit from the grandfather if the grandchild's fath… | 1. Succession Act, 1925 s.38 ~ (0.674)<br>2. Succession Act, 1925 s.40 ~ (0.614)<br>3. Succession Act, 1925 Schedule 2 ~ (0.607) | 1. Succession Act, 1925 s.53 (0.658)<br>2. Succession Act, 1925 s.48 (0.641)<br>3. Succession Act, 1925 s.40 (0.636) | ✗ → ✗ (ON top 50: 16) |
| **G09** How can a mother get custody of her minor child under the Guardians an… | 1. Hindu Widows' Re-marriage Act, 1856 s.3 ~ (0.684)<br>2. THE ISLAMABAD CAPITAL TERRITORY PROHIBITION OF CORPORAL PUNISHMENT ACT, 2021 (0.648)<br>3. THE ISLAMABAD CAPITAL TERRITORY CHILD PROTECTION ACT, 2018 (0.646) | 1. Guardians and Wards Act, 1890 s.21 (0.730)<br>2. Guardians and Wards Act, 1890 s.12 (0.688)<br>3. Guardians and Wards Act, 1890 s.25 (0.687) | ✗ → 3 |
| **G10** Which court hears suits for dissolution of marriage, dower and mainten… | 1. Parsi Marriage and Divorce Act, 1936 (contents/other) (0.729)<br>2. Parsi Marriage and Divorce Act, 1936 s.34 ~ (0.722)<br>3. Divorce Act, 1869 s.39 ~ (0.693) | 1. Divorce Act, 1869 s.10 (0.776)<br>2. Divorce Act, 1869 s.12 (0.758)<br>3. West Pakistan Family Courts Act, 1964 s.7 (0.750) | ✗ → ✗ (ON top 50: > 50) |
| **G11** What happens at the pre-trial stage of a case in a Family Court? | 1. West Pakistan Family Courts Act, 1964 s.9 ~ (0.633)<br>2. West Pakistan Family Courts Act, 1964 s.10 ~ (0.629)<br>3. THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 (0.617) | 1. West Pakistan Family Courts Act, 1964 s.10 (0.700)<br>2. West Pakistan Family Courts Act, 1964 s.9 (0.671)<br>3. THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 (0.617) | 2 → 1 |
| **G12** Can a wife get her marriage dissolved if her husband has not maintaine… | 1. Parsi Marriage and Divorce Act, 1936 s.31 ~ (0.678)<br>2. Pakistan Penal Code, 1860 s.494 ~ (0.613)<br>3. Divorce Act, 1869 s.10 ~ (0.612) | 1. Parsi Marriage and Divorce Act, 1936 s.31 (0.639)<br>2. Divorce Act, 1869 s.10 (0.636)<br>3. Divorce Act, 1869 s.57 (0.631) | ✗ → 5 |
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
| **O13** How do I file for divorce in California? | 1. Divorce Act, 1869 s.29 ~ (0.467)<br>2. Parsi Marriage and Divorce Act, 1936 s.34 ~ (0.446)<br>3. Parsi Marriage and Divorce Act, 1936 (contents/other) (0.437) | 1. Parsi Marriage and Divorce Act, 1936 s.34 (0.525)<br>2. Parsi Marriage and Divorce Act, 1936 s.32 (0.502)<br>3. Divorce Act, 1869 s.10 (0.491) | – |
| **O14** What is the punishment for murder under the Indian Penal Code? | 1. Pakistan Penal Code, 1860 s.109 ~ (0.742)<br>2. Code of Criminal Procedure, 1898 s.34 ~ (0.728)<br>3. THE CREDIT BUREAUS ACT, 2015 (0.727) | 1. Pakistan Penal Code, 1860 s.115 (0.783)<br>2. Pakistan Penal Code, 1860 s.109 (0.781)<br>3. Pakistan Penal Code, 1860 s.108 (0.775) | – |
| **O15** How do I apply for a UK student visa? | 1. THE PAKISTAN MEDICAL COMMISSION ACT, 2020 (0.430)<br>2. THE FEDERAL UNIVERSITIES ORDINANCE, 2002 (0.396)<br>3. i For Official Use ESTACODE (EDITION -2021 (0.393) | 1. THE PAKISTAN MEDICAL COMMISSION ACT, 2020 (0.430)<br>2. THE FEDERAL UNIVERSITIES ORDINANCE, 2002 (0.396)<br>3. i For Official Use ESTACODE (EDITION -2021 (0.393) | – |
| **CR-01** Why is the Nikah Nama important in a dower dispute? | 1. i For Official Use ESTACODE (EDITION -2021 (0.492)<br>2. THE BENAMI TRANSACTIONS (PROHIBITION) ACT, 2017 (0.481)<br>3. Muslim Family Laws Ordinance, 1961 s.4 ~ (0.479) | 1. i For Official Use ESTACODE (EDITION -2021 (0.492)<br>2. Muslim Family Laws Ordinance, 1961 s.10 (0.487)<br>3. THE BENAMI TRANSACTIONS (PROHIBITION) ACT, 2017 (0.481) | ✗ → 2 |
| **CR-02** A wife claims that her dowry articles remain in the husband's possessi… | 1. Married Women's Property Act, 1874 s.8 ~ (0.643)<br>2. Divorce Act, 1869 s.27 ~ (0.623)<br>3. Married Women's Property Act, 1874 (contents/other) (0.609) | 1. Married Women's Property Act, 1874 s.8 (0.640)<br>2. Divorce Act, 1869 Schedule (0.616)<br>3. Married Women's Property Act, 1874 s.9 (0.610) | ✗ → ✗ (ON top 50: > 50) |
| **CR-03** Can a spouse lawfully retain the other's personal property merely beca… | 1. Married Women's Property Act, 1874 s.8 ~ (0.687)<br>2. THE CAPITAL TERRITORY TRUST ACT, 2020 (0.673)<br>3. THE TRUSTS ACT, 1882 (0.659) | 1. THE CAPITAL TERRITORY TRUST ACT, 2020 (0.673)<br>2. THE TRUSTS ACT, 1882 (0.659)<br>3. Married Women's Property Act, 1874 s.10 (0.644) | ✗ → ✗ (ON top 50: > 50) |
| **CR-04** What is a suit for restitution of conjugal rights? | 1. Code of Civil Procedure, 1908 Schedule 1 ~ (0.752)<br>2. Divorce Act, 1869 s.32 ~ (0.740)<br>3. Parsi Marriage and Divorce Act, 1936 s.38 ~ (0.709) | 1. Divorce Act, 1869 s.32 (0.791)<br>2. Parsi Marriage and Divorce Act, 1936 s.36 (0.778)<br>3. West Pakistan Family Courts Act, 1964 s.9 (0.745) | ✗ → 3 |
| **CR-05** Why is territorial jurisdiction important in a Family Court case? | 1. THE INSOLVANCY (KARACHI DIVISION) ACT,1909 (0.624)<br>2. Code of Civil Procedure, 1908 s.16 ~ (0.621)<br>3. THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 (0.613) | 1. West Pakistan Family Courts Act, 1964 s.25 (0.643)<br>2. THE INSOLVANCY (KARACHI DIVISION) ACT,1909 (0.624)<br>3. West Pakistan Family Courts Act, 1964 s.5 (0.620) | ✗ → 3 |
| **CR-06** Can a family-law advocate knowingly present false facts before the cou… | 1. Qanun-e-Shahadat Order, 1984 (contents/other) (0.622)<br>2. Qanun-e-Shahadat Order, 1984 s.47 ~ (0.610)<br>3. Pakistan Penal Code, 1860 s.191 ~ (0.603) | 1. West Pakistan Family Courts Act, 1964 s.11 (0.644)<br>2. Qanun-e-Shahadat Order, 1984 s.47 (0.622)<br>3. Qanun-e-Shahadat Order, 1984 s.113 (0.594) | – |
| **CR-07** A wife files a suit seeking dissolution of marriage, unpaid dower, mai… | 1. Married Women's Property Act, 1874 s.8 ~ (0.727)<br>2. Specific Relief Act, 1877 s.43 ~ (0.681)<br>3. Divorce Act, 1869 s.25 ~ (0.675) | 1. Married Women's Property Act, 1874 s.8 (0.714)<br>2. Divorce Act, 1869 s.10 (0.708)<br>3. Divorce Act, 1869 s.27 (0.706) | ✗ → ✗ (ON top 50: > 50) |
| **CR-08** If a wife claims unpaid dower, who must establish the relevant facts? | 1. Married Women's Property Act, 1874 s.8 ~ (0.621)<br>2. Married Women's Property Act, 1874 s.9 ~ (0.583)<br>3. Qanun-e-Shahadat Order, 1984 s.18 ~ (0.570) | 1. Married Women's Property Act, 1874 s.8 (0.590)<br>2. Married Women's Property Act, 1874 s.9 (0.572)<br>3. Married Women's Property Act, 1874 s.10 (0.561) | ✗ → ✗ (ON top 50: > 50) |
