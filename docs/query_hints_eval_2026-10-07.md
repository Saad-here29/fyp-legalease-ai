# Query hints: retrieval before/after (2026-10-07)

Offline: raw questions (no LLM rewrite), `KB_V2` on, scraped laws off, top 5. A hit = an accepted Act and section in the top 5, at any score. Hints: `backend/storage/kb/query_hints.json`; script: `scripts/kb/eval_query_hints.py`.

| Set | Before (hints off) | After (hints on) |
|---|---:|---:|
| 26 gold questions | 18/26 | 20/26 |
| 10 family-law questions | 7/10 | 10/10 |
| All 36 | 25/36 | 30/36 |

**Got worse:** none.

| ID | Question | Hints | Before | After | Change |
|---|---|---|---|---|---|
| G01 | On what grounds can a Muslim woman obtain a decree for the dissolution of her marriage? | - | #1 (0.884) | #1 (0.884) | same |
| G02 | What is the punishment for qatl-i-amd under the Pakistan Penal Code? | - | #1 (0.890) | #1 (0.890) | same |
| G03 | What are the essential elements of a valid contract under the Contract Act, 1872? | - | not in top 5 | not in top 5 | same |
| G04 | If a husband pronounces talaq while his wife is pregnant, when does the talaq take effect, and can she claim maintenance during that period? | talaq, maintenance | #1 (0.558) | #1 (0.742) | same |
| G05 | Can a husband marry a second wife without the permission of the Arbitration Council? | - | #1 (0.618) | #1 (0.618) | same |
| G06 | What is the procedure for talaq under the Muslim Family Laws Ordinance? | talaq | #1 (0.784) | #1 (0.822) | same |
| G07 | What can a wife do if her husband does not pay her maintenance? | maintenance | #1 (0.516) | #1 (0.797) | same |
| G08 | Can a grandchild inherit from the grandfather if the grandchild's father died before the grandfather? | inheritance | not in top 5 | #1 (0.818) | better |
| G09 | How can a mother get custody of her minor child under the Guardians and Wards Act? | custody | #3 (0.687) | #2 (0.773) | better |
| G10 | Which court hears suits for dissolution of marriage, dower and maintenance? | khula, dower, maintenance | not in top 5 | #4 (0.734) | better |
| G11 | What happens at the pre-trial stage of a case in a Family Court? | - | #1 (0.700) | #1 (0.700) | same |
| G12 | Can a wife get her marriage dissolved if her husband has not maintained her for two years? | - | #2 (0.604) | #2 (0.604) | same |
| G13 | How does the Pakistan Penal Code define qatl-i-amd? | - | not in top 5 | not in top 5 | same |
| G14 | What is the punishment for cheating and dishonestly inducing delivery of property? | - | #1 (0.761) | #1 (0.761) | same |
| G15 | What is the punishment for defamation under the Pakistan Penal Code? | - | #1 (0.845) | #1 (0.845) | same |
| G16 | What is the punishment for theft? | - | #1 (0.835) | #1 (0.835) | same |
| G17 | When can bail be granted in a non-bailable offence? | - | #1 (0.796) | #1 (0.796) | same |
| G18 | How is a First Information Report recorded for a cognizable offence? | - | #2 (0.656) | #2 (0.656) | same |
| G19 | What is the punishment for rape under the Pakistan Penal Code? | - | #1 (0.918) | #1 (0.918) | same |
| G20 | How many witnesses are required to attest a document creating a financial obligation? | - | not in top 5 | not in top 5 | same |
| G21 | Is the right to a fair trial a fundamental right in Pakistan? | - | #1 (0.848) | #1 (0.848) | same |
| G22 | What is the writ jurisdiction of a High Court? | - | not in top 5 | not in top 5 | same |
| G23 | What compensation can be claimed for breach of contract? | - | #2 (0.791) | #2 (0.791) | same |
| G24 | How is a sale of immovable property made under the Transfer of Property Act? | - | #1 (0.872) | #1 (0.872) | same |
| G25 | Can a person file a suit for a declaration of their title to property? | - | not in top 5 | not in top 5 | same |
| G26 | Can a minor enter into a valid contract? | - | not in top 5 | not in top 5 | same |
| F01 | How does a husband give talaq to his wife in Pakistan? | talaq | #1 (0.603) | #1 (0.747) | same |
| F02 | After a divorce, what notice has to be sent to the Union Council chairman? | talaq | not in top 5 | #1 (0.763) | better |
| F03 | Can a wife get khula through the Family Court? | khula | #3 (0.601) | #1 (0.839) | better |
| F04 | When does the husband have to pay the dower to his wife? | dower | #2 (0.537) | #1 (0.810) | better |
| F05 | Is it compulsory to register a nikah? | nikah_registration | #2 (0.569) | #1 (0.880) | better |
| F06 | What does a Nikah Registrar do? | nikah_registration | not in top 5 | #1 (0.857) | better |
| F07 | Who decides custody of a minor child after the parents separate? | custody | not in top 5 | #2 (0.795) | better |
| F08 | Can the court appoint a guardian for a minor's property? | custody | #3 (0.730) | #1 (0.819) | better |
| F09 | How is the property of a deceased Muslim divided among the heirs? | inheritance | #1 (0.796) | #1 (0.860) | same |
| F10 | Can a wife claim maintenance from her husband? | maintenance | #3 (0.588) | #1 (0.818) | better |

**Off-topic and foreign-law questions** (15): best score before / after; the chat refuses below 0.65.

| ID | Question | Hints | Before | After |
|---|---|---|---:|---:|
| O01 | What is the capital of Australia and how many people live there? | - | 0.413 | 0.413 |
| O02 | What is the weather forecast for Lahore tomorrow? | - | 0.472 | 0.472 |
| O03 | Give me a recipe for chocolate cake. | - | 0.286 | 0.286 |
| O04 | Who won the Cricket World Cup in 1992? | - | 0.342 | 0.342 |
| O05 | How do I reset my Wi-Fi router? | - | 0.291 | 0.291 |
| O06 | What is the best smartphone under 50,000 rupees? | - | 0.539 | 0.539 |
| O07 | Explain how photosynthesis works. | - | 0.494 | 0.494 |
| O08 | Write a poem about the monsoon. | - | 0.433 | 0.433 |
| O09 | How many calories are in a plate of biryani? | - | 0.384 | 0.384 |
| O10 | What is the exchange rate of the US dollar today? | - | 0.597 | 0.597 |
| O11 | How do I register a company with the Corporate Affairs Commission in Nigeria? | - | 0.540 | 0.540 |
| O12 | Is a verbal contract enforceable in Thailand? | - | 0.593 | 0.593 |
| O13 | How do I file for divorce in California? | - | 0.409 | 0.409 |
| O14 | What is the punishment for murder under the Indian Penal Code? | - | 0.783 | 0.783 |
| O15 | How do I apply for a UK student visa? | - | 0.430 | 0.430 |

Crossed 0.65 because of the hints: none.

**Still not in the top 5 with hints:** G03 (top: Contract Act, 1872 1), G13 (top: Pakistan Penal Code, 1860 299), G20 (top: THE DRUG REGULATORY AUTHORITY OF PAKISTAN ACT, 2012 ), G22 (top: THE BANKING COMPANIES ORDINANCE, 1962 ), G25 (top: THE CAPITAL TERRITORY TRUST ACT, 2020 ), G26 (top: THE LIMITED LIABILITY PARTNERSHIP ACT, 2017 ).
