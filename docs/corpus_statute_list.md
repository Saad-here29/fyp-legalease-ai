# Statute corpus — every statute in the search index

Generated 2026-09-28 from the live FAISS metadata (`backend/storage/faiss/legal_corpus_meta.json`, what search actually uses) and the cleaned corpus it was built from (`data/processed/statutes/legal_statutes_corpus.json`, which records the raw dataset for each statute). Nothing below is inferred beyond those two files.

## Totals

- **53,739 chunks** from **900 distinct titles** in the index (every chunk has `source_type` = `statute`; there are no judgments).
- Cleaned corpus: 901 documents, 900 distinct titles (build report: {"csv_rows_total": 1417, "csv_rows_dropped": 21, "csv_rows_relabeled_crpc": 73, "csv_rows_kept_as_police_order": 187, "csv_documents": 7, "json_entries_total": 969, "json_removed_exact_duplicates": 74, "json_removed_short_stubs": 1, "json_documents": 894, "json_title_methods": {"year": 888, "filename-fallback": 3, "keyword-cut": 3}, "qa_rows_total": 78, "qa_rows_kept": 78, "total_merged_documents": 901}).
- 893 titles from: Pakistan Code PDF text (`pakistan_code_pdf_data.json`)
- 7 titles from: Section table (`Datatset For FAISS.csv`)
- **OCR-duplicated titles:** 10 titles in 5 groups — the same statute indexed under two spellings (see below). Their chunks count twice in search results.
- **Titles that aren't statute names:** 2 boilerplate titles (extraction failed) and ESTACODE, a civil-service manual rather than a statute — see "Titles that aren't statute names".

## Provenance — what is and isn't recorded

- **Recorded:** how the raw files were cleaned and merged (`data/processed/statutes/README.md`, `scripts/kb/clean_statute_corpus.py`) and how chunks were built (`ai-services/corpus_builder/build_corpus.py`: 800-character windows, 100-character overlap).
- **Recorded:** which raw file each statute came from — the *Source* column below — taken from the `source_type` field of the cleaned corpus.
- **Not recorded:** where the two raw datasets themselves came from — who compiled `Datatset For FAISS.csv`, how and when the Pakistan Code PDFs behind `pakistan_code_pdf_data.json` were collected and text-extracted, and which edition/date of each statute they reflect. `data/README.md` only says the raw data is "not published anywhere else yet". This should be documented before relying on the corpus in the report; it is not guessed here.
- **Not recorded per chunk:** the index stores only `source` (title), `source_type` and `chunk_id` — no section numbers, years or jurisdiction.

## OCR-duplicated titles

Titles that are identical once case, spacing, punctuation and a leading "The" are ignored — the same statute from both raw files, or an OCR-damaged spelling (e.g. "ORDINAN CE"). Chunk counts show the size of each copy.

| Titles in the group | Chunks |
|---|---|
| Code of Criminal Procedure, 1898<br>THE CODE OF CRIMINAL PROCEDURE , 1898 | 774 / 1091 |
| Limitation Act, 1908<br>THE LIMITATION ACT, 1908 | 48 / 123 |
| Muslim Family Laws Ordinance, 1961<br>THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 | 15 / 23 |
| Pakistan Penal Code<br>THE PAKISTAN PENAL CODE | 601 / 713 |
| THE QUAID -I-AZAM’S MAZAR (PROTECTION AND MAINTENANCE) ORDINANCE, 1971<br>THE QUAIDIAZAM´S MAZAR (PROTECTION AND MAINTENANCE)ORDINANCE, 1971 | 8 / 8 |

Not caught by this rule: OCR glitches inside a title that has no second copy (e.g. stray mid-word spaces such as "COT TON GINNING", noted in `data/processed/statutes/README.md`), and the 3 gazette scans whose titles fell back to their filename.

## Titles that aren't statute names

**Title extraction failed — page boilerplate indexed as the title.** These are *different* statutes; the text shows which (checked by reading chunk 0):

| Title (as indexed) | Chunks | Chunk 0 begins |
|---|---|---|
| Up dated till 19.04.2023 | 15 | Up dated till 19.04.2023 THE AGRICULTURAL DEVELOPMENT BANK OF PAKISTAN (REORGANIZATION AND CONVERSION) O RDINANCE, 2002 CONTENTS 1. Short title, extent and comm… |
| Updatedtill19.04.2023 | 8 | Updatedtill19.04.2023THEPRESIDENT’SPENSIONACT,1974CONTENTS1.Shorttitleandcommencement2.Amountandconditionofpension3.Provisionofotherfacilities4.Expenditureonpen… |

**Not a statute: ESTACODE (Edition 2021)** — `i For Official Use ESTACODE (EDITION -2021` is the Establishment Division's civil-service manual, "prepared & published by Pakistan Public Administration Research Centre, Establishment Division, Cabinet Secretariat, Islamabad 2021" (its own chunk 0). It is the largest item in the index: 3,424 chunks (6.4% of all chunks). It contains rules and notifications, but it is not an Act, Ordinance, Code or Order.

> **Future work:** ESTACODE (6.4% of the index) is a civil-service manual and a
> candidate for removal at the next corpus rebuild, or for filtering at query
> time. Not changed now — retrieval and the index are frozen before the demo.

**Other titles without a statute word** (no Act / Ordinance / Order / Code / Rules / Regulations / Constitution / Law in the name) — 22 titles, listed for review; many are OCR-damaged or abbreviated names of real statutes, not necessarily wrong content:

| Title (as indexed) | Chunks |
|---|---|
| i For Official Use ESTACODE (EDITION -2021 | 3424 |
| TRAD E MAR KS ORDINANC E, 2001 | 288 |
| THE QANUNESHAHADAT , 1984 | 216 |
| administrator7e36a1a577bfe6f1ea787e750ce6ec20 | 115 |
| [As Amended Up-to-Date Till 2012 | 106 |
| THE NATIONAL DATA BASE AND REGISTRATION AUT HORITY ORDINANC E, 2000 | 101 |
| THE INST ITUTE O F SC IENCE AND TECHN OLOGY BAHAWALPUR A CT, 2018 | 91 |
| administrator888bc6d1009f9fb0809dd695f28e21b5 | 91 |
| THE PAKISTAN ELE CTRONIC MEDIA REGULATORY AUTHO RITY ORDINANC E, 2002 | 58 |
| THE WEST PAKISTAN SHOPS AND ESTABLISHMENTS ORDINAN CE, 1969 | 55 |
| THE SMALL AND MEDIUM EXTERPRISES DEVELOPMENT AUTHORITYORDINANCE, 2002 | 53 |
| THE ISLAMABAD CAPITAL TERRITOPRY FOOD SAFETY, 2021 | 51 |
| THE AGRICULTUR AL PESTICIDES ORD INANCE, 1971 | 49 |
| NATIONAL TEXTILE UNIV ERSITY ORDINANC E, 2002 | 42 |
| THE COMPULSO R Y S ER VI C E IN THE A R M E D F O R C E S O R DIN A N C E , 1971 | 27 |
| THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 | 23 |
| THE FREEDOM OF INFORMA TION ORDIN ANCE, 2002 | 22 |
| administrator0fec6f1f03ce6e45980e3fa44e70c6d2 | 14 |
| PART I] THE GAZETTE OF PAKISTAN, EXTRA., JULY 4, 2023 | 12 |
| THE N ATION AL JUDI CIAL (POLICY MAKIN G) COMM ITTEE ORDIN ANCE, 2002 | 6 |
| THE INTERNATIONAL COURT OF JUSTICE (REVIEW AND RE -CONSIDIRATION ), 2021 | 5 |
| THE ISLAMBAD CAPIT AL TERRIT ORY LOCAL GOVERNMENT ELECTIONSORDINANCE, 2002 | 3 |

## Every indexed title

Sorted alphabetically (ignoring "The" and punctuation). **⚠ OCR dup** marks a title that also appears under another spelling.

| # | Title (as indexed) | Chunks | Source | OCR dup |
|---|---|---|---|---|
| 1 | 1 NATIONAL COMMISSION FOR HUMAN RIGHTS ACT, 2012 | 44 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 2 | 1 THE ISLAMABAD CAPITAL TERRITIORY (TAX ON SERVICE S) ORDINANCE, 2001 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 3 | 1 THE LAW RE FORMS ORDINANCE, 1972 | 148 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 4 | 1 THE MARKETING OF PETROLEUM PRODUCTS (FEDERAL CONTROL) ACT, 1974 | 48 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 5 | 1 THE SYSTEM OF SARDARI (ABOLIT ION) ACT, 1976 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 6 | THE ABANDONED PROPERTIES (MANAGEMENT) ACT, 1975 | 38 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 7 | THE ABOLITION OF THE DISCRETIONARY QUOTAS IN HOUSING SCHEMES ACT, 2013 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 8 | THE ABOLITION OF THE PUNISHMENT OF WHIPPING ACT, 1996 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 9 | THE ACCEDING STATE (PROPERTY) ORDER, 1961 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 10 | THE ACCESS TO THE MEDIA (DEAF) PERSONS ACT, 2022 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 11 | THE ACTING AS AGENTS OF MOALLIMS (PROHIBITION) ORDINANCE, 1980 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 12 | administrator0fec6f1f03ce6e45980e3fa44e70c6d2 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 13 | administrator7e36a1a577bfe6f1ea787e750ce6ec20 | 115 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 14 | administrator888bc6d1009f9fb0809dd695f28e21b5 | 91 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 15 | THE ADMINISTRATOR GENERAL'S ACT, 1913 | 79 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 16 | THE ADMIRALTY JURISDICTION OF HIGH COURTS ORDINANCE, 1980 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 17 | THE AGHA KHAN UNIVERSITY EXAMINATION BOARD ORDINANCE, 2002 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 18 | THE AGRICULTUR AL PESTICIDES ORD INANCE, 1971 | 49 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 19 | THE AGRICULTURAL PRODUCE CESS ACT, 1940 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 20 | THE AGRICULTURAL PRODUCE (GRADING AND MARKETING) ACT, 1937 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 21 | THE AGRICULTURE CENSUS ACT, 1958 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 22 | THE AGRICULTURISTS LOANS ACT, 1884 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 23 | THE AIRCRAFT (REMOVAL OF DANGER TO SAFETY) ORDINANCE, 1965 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 24 | THE AIRPORTS SECURITY FORCE ACT, 1975 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 25 | THE AIR UNIVERSITY ORDINANCE, 2002 | 62 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 26 | THE AL -KARAM INTERNATIONAL INSTITUTE ACT, 2021 | 99 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 27 | THE ALLAMA IQBAL OPEN UNIVERSITY ACT, 1974 | 84 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 28 | THE ALLIED HEALTH PROFESSIONALS COUNCIL ACT, 2022 | 58 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 29 | THE ALLOPATHIC SYSTEM (PREVENTION OF MISUSE) ORDINANCE, 1962 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 30 | THE ALTERNATIVE DISPUTE RESOLUTION ACT, 2017 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 31 | ALTERNATIVE ENERGY DEVELOPMENT BOARD ACT, 2010 | 28 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 32 | THE ANAND MARRIAGE ACT, 1909 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 33 | THE ANTIDUMPING DUTIES ORDINANCE, 2000 | 128 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 34 | ANTI -MONEY LAUNDERING ACT, 2010 | 134 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 35 | THE ANTI NARCOTICS FORCE ACT, 1997 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 36 | THE ANTIQUITIES ACT, 1975 | 54 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 37 | THE ANTI -RAPE (INVESTIGATION AND TRIAL) ACT, 2021 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 38 | THE ANTI -TERRORISM ACT, 1997 | 198 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 39 | APPRENTICESHIP ACT, 2018 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 40 | THE APPRENTICESHIP ORDINANCE, 1962 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 41 | THE ARBITRATION (INTERNATIONAL INVESTMENT DISPUTES) ACT, 2011 | 70 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 42 | The Arbitration (Protocol and Convention) Act, 1937 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 43 | THE ARCHIV AL MA T ERIAL (PRESER V A TI ON AND EXPOR T CONTROL) ACT ,1975 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 44 | THE AREA STUDY CENTRES ACT, 1975 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 45 | THE ARMED FORCES CIVIL GENERAL TRANSPORT COMPANIES AND REQUISITION OF CIVIL TRANSPORT ORDINANCE, 2002 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 46 | THE ARMED FORCES (EMERGENCY DUTIES) ACT, 1947 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 47 | THE ARMS ACT, 1878 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 48 | THE ARYA MARRIAGE VALIDATION ACT, 1937 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 49 | [As Amended Up-to-Date Till 2012 | 106 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 50 | THE ASIAN DEVELOPMENT BANK ORDINANCE, 1971 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 51 | THE ASSETS DECLARATION ACT, 2019 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 52 | THE ASSOCIATED CEMENT (VESTING) ACT, 1974 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 53 | ASSOCIATED PRESS OF PAKISTAN CORPORATION ORDINANCE, 2002 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 54 | THE ASSOCIATED PRESS OF PAKISTAN (TAKING OVER) ORDINANCE, 1961 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 55 | THE AUDITOR GENERAL’S (FUNCTIONS, POWERS, TERMS AND CONDITIONS OF SERVICE) ORDINANCE, 2001 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 56 | THE AUQAF (FEDERAL CONTROL) (REPEAL) ORDINANCE, 1979 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 57 | THE BAHRIA UNIVERSITY ORDINANCE 2000 | 56 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 58 | THE BANAZIR INCOME SUPPORT PROGRAM ACT, 2010 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 59 | THE BANKERS' BOOKS EVIDENCE ACT, 1891 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 60 | THE BANKING COMPANIES ORDINANCE, 1962 | 374 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 61 | THE BANKING TRIBUNALS (VALIDATION OF ORDERS) ACT, 1994 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 62 | THE BANKS (NATIONALIZATION) ACT, 1974 | 47 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 63 | THE BANKS (TRANSFER OF ASSETS AND LIABILITIES) ACT , 1974 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 64 | THE BENAMI TRANSACTIONS (PROHIBITION) ACT, 2017 | 81 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 65 | THE BENAZIR INCOME SUPPORT PROGRAMME ACT, 2010 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 66 | THE BILLS OF LADING ACT, 1856 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 67 | THE BIRTHS, DEATHS AND MARRIAGES REGISTRATION ACT, 1886 | 49 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 68 | THE BOARD OF INVESTMENT ORDINANCE, 2001 | 46 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 69 | THE BOILERS ACT, 1923 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 70 | THE BOILERS AND PRESSURE VESSELS ORDINANCE, 2002 | 52 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 71 | THE BONDED LABOUR SYSTEM (ABOLITION) ACT,1992 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 72 | THE CANAL AND DRAINAGE ACT,1873 | 100 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 73 | THE CANTONMENTS ACT, 1924 | 501 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 74 | THE CANTONMENTS (HOUSEACCOMMODATION) ACT, 1923 | 49 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 75 | THE CANTONMENTS LOCAL GOVERNMENT (ELECTIONS) ORDINANCE, 2002 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 76 | THE CANTONMENTS ORDINANCE, 2002 | 445 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 77 | THE CANTONMENTS PURE FOOD ACT, 1966 | 55 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 78 | THE CANTONMENTS RENT RESTRICTION ACT, 1963 | 52 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 79 | THE CANTONMENTS (REQUISITIONING OF IMMOVEABLE PROPERTY)ORDINANCE, 1948 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 80 | THE CAPIT AL DEVELOPMENT AUTHORIT Y (ABA TEMENT OF ARBITRA TIONPROCEEDINGS) ACT , 1975 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 81 | THE CAPITAL DEVELOPMENT AUTHORITY ORDINANCE, 1960 | 91 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 82 | THE CAPITAL OF THE REPUBLIC (DETERMINATION OF AREA) ORDINANCE,1963 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 83 | THE CAPITAL TERRITORY LOCAL GOVERNMENT ORDINANCE, 1979 | 156 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 84 | THE CAPITAL TERRITORY TRUST ACT, 2020 | 103 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 85 | THE CARRIAGE BY AIR ACT, 2012 | 213 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 86 | THE CARRIAGE OF GOODS BY SEA ACT, 1925 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 87 | THE CASTE DISABILITIES REMOVAL ACT, 1850 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 88 | THE CATTLETRESPASS ACT, 1871 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 89 | THE CENSUS ORDINANCE , 1959 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 90 | THE CENTRAL DEPOSITORIES ACT, 1997 | 81 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 91 | THE CENTRAL EXCISE DUTY ON SUGAR (VALIDATION) ORDINANCE, 1979 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 92 | THE CENTRAL LAW OFFICERS ORDINANCE, 1970 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 93 | THE CENTRES OF EXCELLENCE ACT, 1974 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 94 | THE CHAIRMAN AND MEMBERS OF FEDERAL LAND COMMISSION (VALIDATION OF ORDERS) ORDINANCE, 1981 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 95 | THE CHAIRMAN AND SPEAKER (SALARIES, ALLOWANCES AND PRIVILEGES) ACT, 1975 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 96 | THE CHARITABLE AND RELIGIOUS TRUSTS ACT, 1920 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 97 | THE CHARITABLE ENDOWMENTS ACT, 1890 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 98 | THE CHARITABLE FUNDS (REGULATION OF COLLECTIONS) ACT, 1953 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 99 | THE CHARTERED ACCOUNTANTS ORDINANCE, 1961 | 79 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 100 | THE CHEMICAL FER TILIZERS (DEVELOP MENT SURCHARGE) ACT , 1973 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 101 | THE CHEMICAL WEAPONS CONVENTION IMPLEMENTATION ORDINANCE, 2000 | 94 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 102 | THE CHIEF ELECTION COMMISSIONER (SALARY, ALLOWANCES AND PRIVILEGES) ACT, 1975 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 103 | THE CHILD MARRIAGE RESTRAINT ACT, 1929 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 104 | THE CHILDREN (PLEDGING OF LABOUR) ACT, 1933 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 105 | CHINA PAKISTAN ECONOMIC CORRIDOR AUTHORITY ACT, 2021 | 34 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 106 | THE CHRISTIAN MARRIAGE ACT, 1872 | 101 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 107 | THE CHURCH OF SCOTLAND KIRK SESSIONS ACT, 1899 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 108 | THE CIGARETTES (PRINTING OF WARNING) ORDINANCE , 1979 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 109 | THE CIVIL AVIATION ORDINANCE, 1960 | 45 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 110 | THE CIVIL DEFENCE ACT, 1952 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 111 | THE CIVIL SERVA NTS ACT, 1973 | 38 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 112 | THE CIVIL SERVANTS (VALIDATION OF RULES) ORDINANCE, 2001 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 113 | THE CIVIL SERVICES (QUALIFICATION FOR APPOINTMENT AS HIGH COURT JUDGE) ACT, 1965 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 114 | THE CLAIMS FOR MAINTENANCE (RECOVERY ABROAD) ORDINANCE, 1959 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 115 | THE COAL MINES (FIXATION OF RATES OF WAGES) ORDINANCE, 1960 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 116 | THE COCONUT COMMITTEE ACT, 1944 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 117 | THE CODE OF CIVIL PROCEDURE, 1908 | 1190 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 118 | Code of Criminal Procedure, 1898 | 774 | Section table (`Datatset For FAISS.csv`) | ⚠ OCR dup |
| 119 | THE CODE OF CRIMINAL PROCEDURE , 1898 | 1091 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) | ⚠ OCR dup |
| 120 | THE COMMERCIAL DOCUMENTS EVIDENCE ACT, 1939 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 121 | THE COMPANIES ACT, 2017 | 1338 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 122 | THE COMPANIES (APPOINTMENT OF LEGAL ADVISERS) ACT, 1974 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 123 | THE COMP ANIES (APPOINTMENT OF TRU STEES) ACT , 1972 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 124 | THE COMP ANIES ORDINANCE, 1984 | 1320 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 125 | THE C OMPAN IES PROFIT S (WORKERS PARTICIPATION) ACT, 1968 | 41 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 126 | THE COMPETITION ACT, 2010 | 101 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 127 | THE COMPULSO R Y S ER VI C E IN THE A R M E D F O R C E S O R DIN A N C E , 1971 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 128 | THE COMPULSORY TEACHING OF THE HOLY QURAN ACT, 2017 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 129 | THE COMSA TS INSTITUTE OF INFORMA TION TECHNOLOGY ORDINANCE,2000 | 50 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 130 | THE COMSATS UNIVERSITY ISLAMABAD ACT , 2018 | 96 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 131 | THE CONCILIATION COURTS ORDINANCE, 1961 | 38 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 132 | THE CONSTITUTION OF THE ISLAMIC REPUBLIC OF PAKISTAN [As modified upto the 31st May, 2018 | 639 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 133 | THE CONTRACT ACT, 1872 | 237 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 134 | THE CONTROLLER GENERAL OF ACCOUNTS (APPOINTMENT, FUNCTIONS AND POWERS) ORDINANCE, 2001 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 135 | THE CONTROL OF EMPLOYMENT ORDINANCE, 1965 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 136 | THE CONTROL OF NARCOTIC SUBSTANCES ACT, 1997 | 166 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 137 | THE COOPERA TIVE FARMING ACT , 1976 | 63 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 138 | THE COOPERATIVE SOCIETIES ACT, 1912 | 55 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 139 | THE COOPERATIVE SOCIETIES (REPAYMENT OF LOANS) ORDINANCE, 1960 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 140 | THE COPYRIGHT ORDINANCE, 1962 | 155 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 141 | THE CORPOR ATE AND INDUSTRIAL RESTRUCT URING CORPORATION ORDINANCE, 2000 | 72 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 142 | THE CORPORATE REHABILITATION ACT, 2018 | 62 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 143 | THE CORPORATE RESTRUCTURING COMPANIES ACT, 2016 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 144 | THE CORPORATION EMPLOYEES (SPECIAL POWERS) ORDINANCE, 1978 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 145 | THE COST AND MANAGEMENT ACCOUNTANTS ACT, 1966 | 64 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 146 | THE COSTS OF LITIGATION ACT, 2017 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 147 | THE COTTON ACT, 1957 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 148 | THE COTTON CESS ACT, 1923 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 149 | THE COTTON CLOTH ACT, 1918 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 150 | THE COTTON CLOTH AND YARN (CONTRACTS) ORDINANCE, 1944 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 151 | THE COTTON GINNING AND PRESSING FACTORIES ACT, 1925 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 152 | THE COT TON GINNING CONTROL AND DEVELO PMENT (REPEAL) ORDINANCE, 1977 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 153 | THE COTTON INDUSTRY (STATISTICS) ACT, 1926 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 154 | THE COTTON STANDARDI ZATION ORDINANCE, 2002 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 155 | THE COTTON TRANSPORT ACT, 1923 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 156 | THE COUNTERVAILING DUTIES ACT, 2015 | 154 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 157 | THE COUNTER V AILI NG DUTIES ORDINANCE, 2001 | 184 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 158 | THE COURTFEES ACT, 1870 | 119 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 159 | THE COVID -19 (PREVENTION OF HOARDING) ACT, 2021 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 160 | THE CREDIT BUREAUS ACT, 2015 | 64 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 161 | THE CRIMINAL LAW AMENDMENT (SPECIAL COURT) ACT, 1976 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 162 | THE CUTCHI MEMONS ACT, 1938 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 163 | CUTTING OF TREES (PROHIBITION) ACT, 1992 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 164 | THE DANGEROUS CARGOES ACT, 1953 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 165 | THE DAR -UL-MADINA INTERNATIONAL UNIVERSITY ISLAMABAD ACT, 2013 | 77 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 166 | THE DAY CARE CENTRES ACT, 2023 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 167 | THE DECORATIONS ACT, 1975 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 168 | THE DEFAMATION ORDINANCE, 2002 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 169 | DEFENCE HOUSING AUTHORITY ISLAMABAD ACT, 2013 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 170 | THE DEFENCE SERVICES (INQUIRY) (SPECIAL PROVISIONS) ORDINANCE,1969 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 171 | THE DEGREE AWARDING STATUS TO DAWOOD COLLEGE OF ENGINEERING AND TECHNOLOGY, KARACHI ACT, 2010 | 86 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 172 | THE DEKKHAN AGRICULTURISTS RELIEF ACT, 1879 | 122 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 173 | THE DELIMITATION OF CONSTITUENCIES ACT, 1974 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 174 | THE DEPUTY CHAI RMAN A ND DEPUTY SPEAKER (SALARIE S, ALLOWANCE AND PRIVILE GES) ACT, 1975 | 28 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 175 | THE DESTRUCTION OF RECORD ACT, 1917 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 176 | THE DEVELOPMENT OF INDUSTRIES (FEDERAL CO NTROL) (REPEAL) ORDINANCE, 1979 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 177 | THE DEVELOPMENT OF INDUSTRIES (GOVERNMENT CONTROL) ACT, 1949 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 178 | THE DIPLOMATIC AND CONSULAR OFFICERS (OATHS AND FEES) ACT, 1948 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 179 | THE DIPLOMATIC AND CONSULAR PRIVILEGES ACT, 1972 | 76 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 180 | THE DIPLOMATIC IMMUNITIES (COMMON WEALTH COUNTRIESREPRESENTATIVES), ACT, 1957 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 181 | THE DIPLOMATIC IMMUNITIES (CONFERENCES WITH COMMON WEALTHCOUNTRIES) ACT, 1963 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 182 | THE DISABLED PERSONS (EMPLOYMENT AND REHABILITATION) ORDINANCE, 1981 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 183 | THE DISCONTINUANCE OF MEDICAL REIMBURSEMENT ACT , 1972 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 184 | THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 185 | THE DISTURBED AREAS (SPECIAL POWERS) ORDINANCE, 1962 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 186 | THE DIVORCE ACT,1869 | 86 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 187 | THE DOCK LABOURERS ACT, 1934 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 188 | THE DOCK WORKERS (REGULA TION OF EMPLOYMENT) ACT , 1974 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 189 | THE DORMANT FUNDS (ADMINISTRATION) ACT, 1966 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 190 | THE DOURINE ACT, 1910 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 191 | THE DOWRY AND BRIDAL GIFTS (RESTRICTION) ACT, 1976 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 192 | THE DRAMATIC PERFORMANCES ACT, 1876 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 193 | THE DRUG REGULATORY AUTHORITY OF PAKISTAN ACT, 2012 | 100 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 194 | THE DRUGS ACT, 1976 | 98 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 195 | THE DRUGS AND MEDICINES (LNDEMNITY) ACT, 1957 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 196 | THE DYSLEXIA SPECIAL MEASURES ACT, 2022 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 197 | THE EARTHQUAKE RECONSTRUC TION AND REHABILITATION AUTHORITY ACT , 2011 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 198 | THE EASEMENTS ACT, 1882 | 92 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 199 | THE EHTRAMERAMAZAN ORDINANCE, 1981 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 200 | THE ELECTION COMMISSION (SALARY, ALLOWANCES, PERKS ANDPRIVILEGES) ACT, 2016 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 201 | THE ELECTION S ACT, 2017 | 410 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 202 | THE ELECTORAL ROLLS ACT, 1974 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 203 | THE ELECTRICITY ACT, 1910 | 204 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 204 | THE ELECTRICITY CONTROL ORDINANCE, 1965 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 205 | THE ELECTRONIC TRANSACTION S ORDINANCE , 2002 | 63 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 206 | THE ELEPHANTS' PRESERVATION ACT, 1879 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 207 | THE EMIGRATION ORDINANCE, 1979 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 208 | THE EMPLOYEES ’ OLD -AGE BENEFITS ACT, 1976 | 79 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 209 | THE EMPLOYEES' SOCIAL INSURANCE ORDINANCE, 1962 | 101 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 210 | THE EMPLOYER S LIABILITY ACT, 1938 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 211 | THE EMPLOYMENT OF CHILDREN ACT, 1991 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 212 | THE EMPLOYMENT (RECORD OF SERVICES) ACT, 1951 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 213 | THE EMPOYEES COST OF LIVING (RELIEF) ACT, 1974 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 214 | THE ENEMY AGENTS ORDINANCE, 1943 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 215 | THE ENEMY PROPERTY (CONTINUANCE OF EMERGENCY PROVISIONS)ORDINANCE, 1969 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 216 | THE ENE MY PROPERTY (CONTINUAN CE OF EMERGENCY PROVI SION S) ORDINANCE, 1977 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 217 | THE ENFORCEMENT OF SHARI'AH ACT, 1991 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 218 | THE ENFORCEMENT OF WOMEN’S PROPERTY RIGHTS ACT, 2020 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 219 | THE EPIDEMIC DISEASES ACT, 1897 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 220 | THE EQUITY PARTICIPATION FUND (REPEAL) ACT, 2016 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 221 | THE ESSENTIAL PERSONNEL (REGISTRATION) ORDINANCE, 1948 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 222 | THE ESSO UNDERT AKINGS (VESTING) ACT, 1976 | 46 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 223 | THE ESTABLISHMENT OF THE FEDERAL BANK FOR COOPERATIVES ANDREGULATION OF COOPERATIVE BANKING ACT, 1977 | 105 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 224 | THE ESTABLISHMENT OF THE FEDERAL BANK FOR COOPERATIVES AND REGULATION OF COOPERATIVE BANKING (REPEAL) ACT, 2018 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 225 | THE ESTABLISHMENT OF THE OFFICE OF FEDERAL TAX OMBUDSMAN ORDINANCE, 2000 | 54 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 226 | THE ESTABLISHMENT OF THE OFFICE OF WAFAQI MOHTASIB (OMBUDSMAN) ORDER , 1983 | 50 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 227 | THE EVACUEE PROPERTY AND DISPLACED PERSONS LAWS (REPEAL) ACT,1975 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 228 | THE EVACUEE TRUST PROPERTIES (MANAGEMENT AND DISPOSAL) ACT, 1975 | 34 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 229 | THE EXCISE DUTY ON MINERALS (LABOUR WELFARE) ACT, 1967 | 34 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 230 | THE EXCISE (SPIRITS) ACT, 1863 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 231 | THE EXCLUSIVE FISHERY ZONE (REGULATION OF FISHING) ACT, 1975 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 232 | THE EXECUTION OF THE PUNISHMENT OF WHIPPING ORDINANCE, 1979 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 233 | THE EX -EMPLOYEES OF THE FORMER GOVERNMENT OF EAST PAKISTAN (APPOINTMENT TO FEDERAL POSTS) ORDINANCE, 1983 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 234 | THE EXIT FROM PAKISTAN (CONTROL) ORDINANCE, 1981 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 235 | THE EXPLOSIVES ACT, 1884 | 44 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 236 | THE EXPLOSIVE SUBSTANCES ACT, 1908 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 237 | EXPORT CONTROL ON GOODS, TECHNOLOGIES, MATERIAL AND EQUIPMENT RELATED TO NUCLEAR AND BIOLOGICAL WEAPONS AND THEIR DELIVERY SYSTEMS ACT, 2004 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 238 | THE EXPORT DEVELOPMENT FUND ACT, 1999 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 239 | THE EXPORT IMPORT BANK OF PAKISTAN ACT, 2022 | 61 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 240 | THE EXPORT PROCESSING ZONES AUTHORITY ORDINANCE, 1980 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 241 | THE EXTRADITION ACT, 1972 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 242 | THE EYE SURGERY (RESTRICTION) ORDINANCE, 1960 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 243 | THE FACTORIES ACT, 1934 | 162 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 244 | THE FATAL ACCIDENTS ACT, 1855 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 245 | THE FEDERAL BOARD OF INTERMEDIATE AND SECONDARY EDUCATION ACT, 1975 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 246 | THE FEDERAL BOARD OF REVENUE ACT, 2007 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 247 | THE FEDERAL COURT(REPEAL) ACT, 2014 | 1 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 248 | THE FEDERAL EMPLOYEES BENEVOLENT FUND AND GROUP INSURANCE ACT, 1969 | 43 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 249 | The Federal Excise Act, 2005 | 278 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 250 | THE FEDERAL GOVERNMENT EMPLOYEES HOUSING AUTHORITY ACT, 2020 | 48 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 251 | THE FEDERAL GOVERNMENT LANDS AND BUILDINGS (RECOVERY OF POSSESSION) ORDINANCE, 1965 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 252 | THE FEDERAL INVE STIGATION AGENCY ACT, 1974 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 253 | THE FEDERAL JUDIC IAL ACADE MY ACT, 1997 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 254 | THE FEDERAL MEDICAL TEACHING INSTITUTE S ACT, 2021 | 52 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 255 | THE FEDERAL MINISTERS AND MINISTERS OF STATE (SALARIE S, ALLOWANCES AND PRIVIL EGES) ACT, 1975 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 256 | THE FEDERAL OMBUDSMEN INSTITUTIONAL REFORMS ACT, 2013 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 257 | THE FEDERAL PROSECUTION SERVICE, ACT, 2023 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 258 | THE FEDERAL PUBLIC SERVICE COMMISSION ORDINANCE, 1977 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 259 | THE FEDERAL PUBLIC SERVICE COMMISSION (VALIDATION OF RULES) ACT, 2021 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 260 | THE FEDERAL SUPERVISION OF CURRICULA , TEXT -BOOKS AND MAINTENANCE OF STANDARDS OF EDUCATION ACT, 1976 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 261 | THE FEDERAL UNIVERSITIES ORDINANCE, 2002 | 98 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 262 | THE FEDERAL URDU UNIVERSITY OF ARTS, SCIENCES AND TECHNOLOGY, ISLAMABAD ORDINANCE, 2002 | 89 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 263 | THE FEE-CHAR GING EMPLOY MENT AGENCIES (REGULATION) ACT, 1976 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 264 | THE FERRIES ACT, 1878 | 39 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 265 | THE FINANCIAL INSTITUTIONS (RECOVERY OF FINANCES) ORDINANCE, 2001 | 87 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 266 | THE FINANCIAL INSTITUTIONS (SECUR ED TRANSACTIONS) ACT, 2016 | 123 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 267 | THE FISCAL RESPONSIBILIT Y AND DEBT LIMITATION ACT, 2005 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 268 | THE FISHERIES ACT, 1897 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 269 | THE FLOUR MILLING CONTROL AND D EVELO PMENT (REPEAL) ORDINANCE, 1977 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 270 | THE FLYING CLUBS (APPOINTMENT OF ADMINIS TRATORS) ORDINANCE, 1978 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 271 | FOREIGN ASSETS (DECLARATION AND REPATRIATION) ACT, 2018 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 272 | THE FOREIGN CUL TURAL ASSOCIA TIONS (REGULA TION OF FUNCTIONING)ACT , 1975 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 273 | THE FOREIGN CURRENCY ACCOUNTS (PROTECTION) ORDINANCE, 2001 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 274 | THE FOREIGNERS ACT, 1946 | 37 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 275 | THE FOREIGN EXCHANGE (PREVENTION OF PAYMENTS) ACT, 1972 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 276 | THE FOREIGN EXCHANGE REGULATION ACT, 1947 | 128 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 277 | THE FOREIGN EXCHANGE (TEMPORARY RESTRICTIONS) ACT, 1998 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 278 | THE FOREIGN INVESTMENT (PROMOTION AND PROTECTION) ACT, 2022 | 109 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 279 | THE FOREIGN PRIVATE INVESTMENT (PROMOTION AND PROTECTION) ACT, 1976 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 280 | THE FOREST ACT, 1927 | 107 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 281 | For official use only RULES OF BUSINESS 1973 | 279 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 282 | THE FOUNDATION UNIVERSITY ORDINANCE, 2002 | 54 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 283 | THE FREEDOM OF INFORMA TION ORDIN ANCE, 2002 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 284 | THE FRONTIER CORPS ORDINANCE, 1959 | 53 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 285 | THE FUNDS VESTING IN THE PRESIDENT (TRANSFER) ACT , 1973 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 286 | THE FUTURES MARKET ACT, 2016 | 268 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 287 | THE GAS INFRASTRUCTURE DEVELOPMENT CESS ACT, 2015 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 288 | THE GAS (THEFT CONTROL AND RECOVERY) ACT , 2016 | 54 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 289 | THE GENERAL CLAUSES ACT, 1897 | 88 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 290 | THE GENERAL STATISTICS (RECORGANIZATION) ACT, 2011 | 80 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 291 | THE GENEVA CONVENTION IMPLEMENTING ACT, 1936 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 292 | THE GEOGRAPHICAL INDICATIONS (REGISTRATION AND PROTECTION) ACT, 2020 | 93 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 293 | THE GLANDERS AND FARCY ACT,1899 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 294 | THE GLOBAL CLIMATE -CHANGE IMPACT STUDIES CENTRE ACT, 2013 | 28 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 295 | THE GOVERNMENT BUILDINGS ACT,1899 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 296 | THE GOVERNMENT GRANTS ACT, 1895 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 297 | THE GOVERNM ENT MAN AGEMENT OF PRIVA TE EST ATES ACT, 1892 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 298 | GOVERNMENT OF PAKISTAN REVENUE DIVISION FEDERA L BOARD OF REVENUE ***** THE CUSTOMS ACT, 1969 | 854 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 299 | THE GOVERNMENT SAVINGS BANKS ACT, 1873 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 300 | THE GOVERNMENT TENANTS (NORTHWEST FRONTIER) ACT, 1893 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 301 | THE GOVERNMENT TRADING TAXATION ACT, 1926 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 302 | THE GUARDIANS AND WAR DS ACT, 1890 | 72 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 303 | THE GUN AND COUNTRY CLUB ACT, 2023 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 304 | THE GWADAR PORT AUTHORITY ORDINANCE, 2002 | 97 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 305 | THE GWADUR (APPLICATION OF CENTRAL LAWS) ORDINANCE, 1960 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 306 | THE HACKNEYCARRIAGE ACT, 1879 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 307 | HEALTH SERVICES ACADEMY ORDINANCE, 2002 | 34 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 308 | THE HEALTH SERVICES ACAD EMY (RESTRUCTURING) ACT, 2018 | 95 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 309 | HEAV Y INDU STRIES 1[TAXILA] BOARD ACT , 1997 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 310 | THE HIGHER EDUCATION COMMISSION ORDINANCE, 2002 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 311 | THE HIGH TREASON (PUNISHMENT) ACT , 1973 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 312 | THE HINDU DISPOSITION OF PROPERTY ACT, 1916 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 313 | THE HINDU GAINS OF LEARNING ACT, 1930 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 314 | THE HINDU INHERITANCE (REMOVAL OF DISABILITIES) ACT, 1928 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 315 | THE HINDU MARRIAGE ACT, 2017 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 316 | THE HINDU MARRIAGE DISABILITIES REMOVAL ACT, 1946 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 317 | THE HINDU MARRIED WOMEN'S RIGHT TO SEPARATE RESIDENCE ANDMAINTENANCE ACT, 1946 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 318 | THE HINDU WIDOWS´ REMARRIAGE ACT, 1856 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 319 | THE HINDU WOMEN S RIGHTS TO PROPERTY ACT, 1937 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 320 | THE HOUSE BUILDING FINANCE CORPORATION ACT, 1952 | 80 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 321 | THE HOUSE BUILDING FINANCE CORPORATION (REPEAL) ACT, 2018 | 1 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 322 | THE HYDERABAD INSTITUTE OF TECHNICAL AND MANAGEMENT SCIENCE ACT, 2021 | 88 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 323 | THE HYDROCARBON DEVELOPMENT INSTITUTE OF PAKISTAN ACT, 2006 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 324 | THE HYDROGENATED VEGETABLE OIL INDUSTRY (CONTROL AND DEVELOPMENT) ACT, 1973 | 63 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 325 | THE IBADAT INTERNATIONAL UNIVERSITY ISLAMABAD ACT, 2021 | 97 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 326 | THE IC T RIGHTS OF PERSONS WITH DISABILITY ACT, 2020 | 54 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 327 | THE IDENTIFICATION OF PRISONERS ACT, 1920 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 328 | i For Official Use ESTACODE (EDITION -2021 | 3424 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 329 | THE ILLEGAL DISPOSSESSION ACT, 2005 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 330 | THE IMPORT OF GOODS (DEVELOPMENT SURCHARGE) ORDINANCE, 1984 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 331 | THE IMPORT OF GOODS (PRICE EQUALIZATION SURCHARGE) ACT, 1967 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 332 | THE IMPORTS AND EXPORTS (CONTROL) ACT, 1950 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 333 | THE INCOME TAX ORDINANCE, 2001 | 1188 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 334 | THE INDECENT ADVERTISEMENTS PROBIBITION ACT, 1963 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 335 | THE INDUS RIVER SYSTEM AUTHORITY ACT, 1992 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 336 | THE INDUSTRIAL DEVELOPMENT BANK OF PAKISTAN ORDINANCE, 1961 | 104 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 337 | THE INDUSTRIAL DEVELOPMENT BANK OF PAKISTAN (REORGANIZATION AND CONVERSION) ACT, 2011 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 338 | INDUSTRIAL RELATIONS ACT, 2008 | 169 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 339 | INDUSTRIAL RELATIONS ACT, 2012 | 173 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 340 | INDUSTRIAL RELATIONS ORDINANCE, 2002 | 169 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 341 | THE INDUSTRIAL STATISTICS ACT, 1942 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 342 | THE INJURED PERSONS (MEDICAL AID) ACT, 2004 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 343 | THE INLAND MECHANICALLY PROPELLED VESSELS ACT, 1917 | 125 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 344 | THE INSOLVANCY (KARACHI DIVISION) ACT,1909 | 196 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 345 | THE INSPECTION AGENCIES (REGISTRATION AND REGULATION) ORDINANCE, 1981 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 346 | THE INSTITUTE FOR ART AND CULTURE ACT , 2018 | 86 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 347 | THE INST ITUTE O F SC IENCE AND TECHN OLOGY BAHAWALPUR A CT, 2018 | 91 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 348 | THE INSTITUTE OF SPACE TECHNOLOGY ACT, 2010 | 87 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 349 | THE INSURANCE ORDINANCE 2000 | 423 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 350 | THE INTELLECTUAL PROPERTY ORGANIZATION OF PAKISTAN ACT, 2012 | 52 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 351 | INTER -BOARDS CO ORDINATION COMMISSION ACT, 2023 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 352 | THE INTEREST ACT, 1839 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 353 | INTER -GOVERNMENTA L COMMERCIAL TRANSACTIONS ACT, 2022 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 354 | THE INTERNATIONAL COURT OF JUSTICE (REVIEW AND RE -CONSIDIRATION ), 2021 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 355 | THE INTERNATIONAL DEVELOPMENT ASSOCIATION ORDINANCE, 1960 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 356 | THE INTERNATIONAL FINANCE CORPORATION ACT, 1956 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 357 | INTERNATIONAL INSTITUTE OF SCIENCE, ARTS AND TECHNOLOGY ACT, 2022 | 97 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 358 | THE INTERNATIONAL ISLAMIC UNIVERSITY ORDINANCE, 1985 | 114 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 359 | THE INTERNATIONAL MONETARY FUND AND BANK ACT, 1950 | 28 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 360 | THE INVESTIGATION FOR FAIR TRIAL ACT, 2013 | 48 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 361 | THE INVESTMENT CORPORATION OF PAKISTAN ORDINANCE, 1966 | 53 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 362 | THE IQBAL ACADEMY ORDINANCE, 1962 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 363 | THE ISLAMABAD CAPITAL TERRITOPRY FOOD SAFETY, 2021 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 364 | THE ISLAMABAD CAPITAL TERRITORY AGRICULTURAL PRODUCE MARKETS ORDINANCE, 2002 | 73 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 365 | THE ISLAMABAD CAPITAL TERRITORY CHARITIES REGISTRATION, REGULATION AND FACILITATION ACT, 2021 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 366 | THE ISLAMABAD CAPITAL TERRITORY CHILD PROTECTION ACT, 2018 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 367 | THE ISLAMABAD CAPITAL TERRITORY DOMESTIC WORKERS ACT, 2022 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 368 | THE ISLAMABAD CAPITAL TERRITORY LOCAL GOVERNMENT ACT, 2015 | 279 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 369 | ISLAMABAD CAPITAL TERRITORY PRIVATE EDUCATIONAL INSTITUTIONS (REGISTRATION AND REGULATION) ACT, 2013 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 370 | THE ISLAMABAD CAPITAL TERRITORY PROHIBITION OF CORPORAL PUNISHMENT ACT, 2021 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 371 | THE ISLAMABAD CAPITAL TERRITORY PROHIBITION OF INTEREST ON PRIVATE LOANS ACT, 2023 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 372 | ISLAMABAD CAPITAL TERRITORY SENIOR CITIZENS ACT, 2021 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 373 | THE ISLAMABAD CAPITAL TERRITORY SHOPS, BUSINESS AND INDUSTRIAL ESTABLISHMENTS (SECURITY) ORDINANCE, 2000 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 374 | Islamabad Capit al Territory (Tax on Services) Ordinance, 2001 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 375 | THE I SLAMABAD CAPITAL TERRITORY WAQF PROPERTIES ACT, 2020 | 41 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 376 | THE ISLAMABAD CLUB (ADMINISTRATION) ORDINANCE, 1978 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 377 | ISLAMABAD CONSUMERS PROTECTION ACT, 1995 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 378 | THE ISLAMABAD HEALTHCARE REGULATION ACT, 2018 | 73 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 379 | THE ISLAMABAD HIGH COURT ACT, 2010 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 380 | THE ISLAMABAD (PRESERVATION OF LANDSCAPE) ORDINANCE, 1966 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 381 | THE ISLAMABAD REAL ESTATE AGENTS AND MOTOR VEHICLES DEALERS (REGULATION OF BUSINESS) ORDINANC E, 1984 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 382 | THE ISLAMABAD REAL ESTATE (REGULATION AND DEVELOPMENT) ACT, 2021 | 185 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 383 | THE ISLAMABAD RENT RESTRICTION ORDINANCE, 2001 | 53 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 384 | THE ISLAMABAD SUBORDINATE JUDICIARY SERVICE TRIBUNAL ACT, 2016 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 385 | ISLAMABAD TRANSFUSION OF SAFE BLOOD ORDINANCE, 2002 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 386 | THE ISLAMABAD WILDLIFE (PROTECTION, PRESERVATION, CONSERVATIONAND MANAGEMENT) ORDINANCE, 1979 | 58 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 387 | THE ISLAMBAD CAPIT AL TERRIT ORY LOCAL GOVERNMENT ELECTIONSORDINANCE, 2002 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 388 | THE ISLAMIC DEVELOPMENT BANK ORDINANCE, 1978 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 389 | THE JAMMU AND KASHMIR (ADMINISTRATION OF PROPERTY) ORDINANCE,1961 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 390 | THE JUDICIAL OFFICERS´ PROTECTION ACT, 1850 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 391 | THE JUTE (REPEAL) ORDINANCE, 1983 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 392 | JUVENILE JUSTICE SYSTEM ACT, 2018 | 39 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 393 | THE KALAM BIBI INTERNATIONAL WOMEN INSTITUTE BANNU ACT, 2023 | 102 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 394 | THE KARACHI ELECTRICITY CONTROL ACT, 1952 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 395 | THE KARACHI ELECTRIC SUPPL Y CORP ORA TION (REMOV AL FROMSER VICE) ORDINANCE, 1999 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 396 | THE KARACHI ESSENTIAL ARTICLES (PRICE CONTROL AND ANTLHOARDING) ACT, 1953 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 397 | THE KARACHI HOTELS AND LODGINGHOUSES (CONTROL) ACT, 1950 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 398 | THE KARACHI PORT SECURITY FORCE ORDINANCE, 2002 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 399 | THE KARACHI RENT RESTRICTION ACT, 1953 | 45 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 400 | THE KARACH PORT TRUST ACT, 1886 | 235 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 401 | THE KAZIS ACT, 1880 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 402 | THE KORANGI FISHERIES HARBOUR AUTHORITY ORDINANCE, 1982 | 43 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 403 | THE LAC CESS ACT, 1930 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 404 | THE LAND ACQUISITION ACT, 1894 | 97 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 405 | THE LAND ACQUISITION (MINES) ACT, 1885 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 406 | THE LAND CONTROL (KARACHI DIVISION) ACT, 1952 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 407 | THE LAND IMPROVEMENT LOANS ACT, 1883 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 408 | THE LAND REFORMS ACT, 1977 | 39 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 409 | THE LAND REFORMS REGULATION (VALIDATION OF ORDERS) ORDINANCE,1978 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 410 | THE LANSDOWNE BRIDGE ACT, 1892 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 411 | THE [LAW AND JUSTICE COMMISSION OF PAKISTAN] ORDINANCE, 1979 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 412 | THE LAW COMMISSION ORDINANCE, 1979 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 413 | THE LAW REPORTS ACT, 1875 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 414 | THE LAWS LOCAL EXTENT ACT, 1874 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 415 | THE LAWYERS WELFARE AND PROTECTION ACT, 2023 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 416 | THE LEGAL AID AND JUSTICE AUTHORITY ACT, 2020 | 28 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 417 | Legal Practitioners & Bar Councils Act, 1973 | 218 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 418 | THE LEGAL PRACTITIONERS (FEES) ACT, 1926 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 419 | THE LEGAL REPRESENTATIVES´ SUITS ACT, 1855 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 420 | THE LEGAL TENDER (INSCRIBED NOTES) ORDINANCE, 1977 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 421 | THE LEPERS ACT, 1898 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 422 | THE LETTERS OF ADMINISTRATION AND SUCCESSION CERTIFICATES ACT, 2020 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 423 | THE LIFE INSURANCE (NATIONALISATION) ORDER , 1972 | 85 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 424 | THE LIGHT HOUSE ACT, 1927 | 34 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 425 | Limitation Act, 1908 | 48 | Section table (`Datatset For FAISS.csv`) | ⚠ OCR dup |
| 426 | THE LIMITATION ACT, 1908 | 123 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) | ⚠ OCR dup |
| 427 | THE LIMITATION (EMERGENCY AND WAR CONDITIONS) ACT, 1965 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 428 | THE LIMITED LIABILITY PARTNERSHIP ACT, 2017 | 118 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 429 | THE LISTED COMPANIES (SUBSTANTIAL ACQUISITION OF VOTING SHARES AND TAKEOVERS) ORDINANCE, 2002 | 61 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 430 | THE LITERACY ORDINANCE, 1985 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 431 | THE LOA NS FOR AGRICULTURAL, COMMERCIAL AND INDUSTRIAL PURPOSES ACT, 1973 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 432 | THE LOCAL AUTHORITIES LOANS ACT, 1914 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 433 | THE LOCAL AUTHORITIES PENSIONS AND GRATUITIES ACT, 1919 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 434 | THE MAINTENANCE ORDERS ENFORCEMENT ACT, 1921 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 435 | THE MAJORITY ACT, 1875 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 436 | THE MALARIA ERADICATION BOARD (REPEAL) ACT, 1975 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 437 | THE MANAGED CEMENT ESTABLISHMENTS (PAYMENT TO CORPORATION) ORDINANCE, 1979 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 438 | THE MANOEUVRES, FIELD FIRING AND ARTILLERY PRACTICE ACT, 1938 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 439 | THE MARINE INSURANCE ACT, 2018 | 99 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 440 | THE MARITIME SECURITY AGENCY ACT, 1994 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 441 | MARKETING OF PETROLEUM PRODUCTS (FEDERAL CONTROL) (REPEAL) ORDINANCE, 2002 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 442 | THE MARRIAGE FUNCTIONS (PROHIBITION OF OSTENTATIOUS DISPLAY AND WASTEFUL EXPENSES) ORDINANCE, 2000 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 443 | THE MARRIAGES VALIDATION ACT, 1892 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 444 | THE MARRIED WOMEN'S PROPERTY ACT, 1874 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 445 | THE MARTIAL LAW REGULATION NO. 60 (REPEAL) ACT, 1989 | 1 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 446 | The Maternity and Paternity Leave Act, 2023 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 447 | THE MEASURES OF LENGTH ACT, 1889 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 448 | THE MEDICAL AND DENTAL DEGREES ORDINANCE, 1982 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 449 | THE MEDICAL COLLEGES (GOVERNING BODIES) ORDINANCE, 1961 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 450 | THE MEDICAL OFFICERS (REGULAR IZATION OF APPOINT MENT S) ACT, 1992 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 451 | THE MEDICAL QUALIFICATIONS (INFORMATION) ORDINANCE, 1960 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 452 | THE MEDICAL TRIBUNAL ACT, 2020 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 453 | THE MEMBERS OF MAJLIS -E-SHOORA (PARLIAMENT) IMMUNITIES AND PRIVILEGES ACT, 2023 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 454 | THE MEMBERS OF PAR LIAMENT AND PROVINCIAL ASSEMBLIES (EXEMPTION OF ADV ISERS FROM DISQUALIFICATION) ACT, 1976 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 455 | THE MEMBERS OF PARLIAMENT (SALARIES AND ALLOWANCE S) ACT, 1974 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 456 | THE MEMBERS OF THE NATIONAL ASSEMBLY (EXEMPTION FROM PREVENTIVE DETENTION AND PERSONAL APPEARANCE) ORDINANCE, 1963 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 457 | THE MENTAL HEALTH ORDINANCE 2001 | 108 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 458 | THE MERCHANT SHIPPING ORDINANCE, 2001 | 887 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 459 | THE MESNE PROFITS AND IMPROVEMENTS ACT, 1855 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 460 | THE METAL TOKENS ACT, 1889 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 461 | THE MICROFINANCE INSTITUTIONS ORDINANCE, 2001 | 67 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 462 | THE MILITARY COLLEGE OF ENGINEERING, RISALPUR (DEGREE) ORDINANCE, 1962 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 463 | THE MINES ACT, 1923 | 139 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 464 | THE MINES MATERNITY BENEFIT ACT, 1941 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 465 | THE MINIMUM WAGES FOR UNSKILLED WORKERS ORDINANCE, 1969 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 466 | THE MINIMUM WAGES ORDINANCE, 1961 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 467 | THE MODARABA COMPANIES AND MODARABA (FLOATATION AND CONTROL) ORDINANCE, 1980 | 55 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 468 | THE MOTION PICTURES ORDINANCE, 1979 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 469 | THE MOTOR VEHICLES ACT, 1939 | 64 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 470 | THE MULTI -UNIT CO -OPERATIVE SOCIETIES ACT, 1942 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 471 | THE MUNICIPAL TAXATION ACT, 1881 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 472 | Muslim Family Laws Ordinance, 1961 | 15 | Section table (`Datatset For FAISS.csv`) | ⚠ OCR dup |
| 473 | THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) | ⚠ OCR dup |
| 474 | THE MUSSALMAN WAKAF ACT, 1923 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 475 | THE MUSSALMAN WAKF VALIDATING ACT, 1913 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 476 | THE MUTUAL LEGAL ASSISTANCE (CRIMINAL MATTERS) ACT, 2020 | 58 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 477 | MY UNIVERSITY ISLAMABAD ACT, 2013 | 73 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 478 | THE NATIONAL ACCOUNTABILITY ORDINANCE, 1999 | 142 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 479 | THE NATIONAL AND PROVINCIAL ASSEM BLIES (ELECTIONS T O RESER VEDSEATS) ACT , 1976 | 56 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 480 | THE NATIONAL ANTI-MONEY LAUND ERING AND COUNTER FINANCING OF TERRORISM AUTHORITY ACT, 2023 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 481 | THE NATIONAL ARCHIVES ACT, 1993 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 482 | THE NATIONAL ASSEMBLY SECRETARIAT EMPLOYEES ACT, 2018 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 483 | THE NATIONAL BANK OF PAKISTAN ORDINANCE, 1949 | 72 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 484 | THE NA TIONAL BOOK FOUNDA TION ACT , 1972 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 485 | THE NATIONAL CIVIC EDUCATION COMMISSION ACT, 2018 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 486 | THE NATIONAL COLLEGE OF ARTS INSTITUTE ACT, 2021 | 82 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 487 | THE NATIONAL COLLEGE OF ARTS ORDINANCE, 1985 | 34 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 488 | THE NATIONAL COMMAND AUTHORITY ACT, 2010 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 489 | THE NATIONAL COMMISSION FOR HUMAN DEVELOPMENT ORDINANCE, 2002 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 490 | THE NATIONAL COMMISSION FOR HUMAN RIGHTS ACT, 2012 | 46 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 491 | THE NATIONAL COMMISSION ON THE RIGHTS OF CHILD ACT, 2017 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 492 | NATIONAL COMMISSION ON THE STATUS OF WOMEN ACT , 2012 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 493 | THE NATIONAL COUNTER TERRORISM AUTHORITY ACT, 2013 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 494 | THE NATIONAL DATA BASE AND REGISTRATION AUT HORITY ORDINANC E, 2000 | 101 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 495 | THE NATIONAL DEFEN CE UNIVERSITY ACT, 2011 | 91 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 496 | THE NATIONAL DEVELOPMENT VOLUNTEER PROGRAMME (REPEAL) ORDINANCE, 1980 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 497 | THE NATIONAL DIASTER MANAGEMENT ACT, 2010 | 58 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 498 | NATIONAL DISASTER MANAGEMENT ACT, 2010 | 56 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 499 | NATIONAL EDUCATION FOUNDATION ORDINANCE 2002 | 45 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 500 | THE NATIONAL ENERGY EFFICIENCY AND CONSERVATION ACT, 2016 | 66 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 501 | THE NATIONAL FUND FOR CULTUR AL HERITAGE ACT, 1994 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 502 | THE NATIONAL GUARDS ACT, 1973 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 503 | THE NATIONAL HIGHWAY AUTHORITY ACT , 1991 | 44 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 504 | THE NATIONAL HIGHWAYS SAFETY ORDINANCE, 2000 | 199 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 505 | THE NATIONAL INFORMATION TECHNOLOGY BOARD ACT, 2022 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 506 | THE NATIONAL INSTITUTE OF CARDIOVASCULAR DISEASES (ADMINISTRATION) ORDINANCE, 1979 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 507 | THE NATIONAL INSTITUTE OF ELECTRONICS ORDINANCE, 1979 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 508 | NATIONAL INSTITUTE OF FOLK AND TRADITIONAL HERITAGE (LOK VIRSA) ORDINANCE, 2002 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 509 | THE NATIONAL INSTITUTE OF HEALTH ORDINANCE, 1980 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 510 | THE NATIONAL INSTITUTE OF HEALTH (RE - ORGANIZATION) ACT, 2021 | 62 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 511 | THE NATIONAL INSTITUTE OF OCEANOGRAPHY ACT, 2007 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 512 | THE NA TIONAL INSURANCE CORPORA TION ACT , 1976 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 513 | THE NATIONAL INSURANCE CORPORATION (REORGANIZATION) ORDINANCE, 2000 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 514 | THE NATIONAL INVESTMENT (UNIT) TRUST ORDINANCE, 1965 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 515 | THE N ATION AL JUDI CIAL (POLICY MAKIN G) COMM ITTEE ORDIN ANCE, 2002 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 516 | THE NATIONAL LOGISTICS CORPORATION ACT, 2023 | 37 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 517 | THE NATIONAL METROLOGY INSTITUTE OF PAKISTAN ACT, 2022 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 518 | THE NA TIONAL PRESS TRUST (APPOINTM ENT OF CHAIRMAN) ACT , 1972 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 519 | THE NATIONAL RAHMATUL -LIL-AALAMEEN WA KHATAMUN NABIYYIN AUTHORITY ACT, 2022 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 520 | THE NATIONAL SCHOOL OF PUBLIC POLICY ORDINANCE, 2002 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 521 | THE NATIONAL SECURITY COUNCIL ACT, 2004 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 522 | The National Skills University Islamabad Act, 2018 | 103 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 523 | THE NATIONAL SPORTS TRUST (REPEAL) ORDINANCE, 1980 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 524 | THE NATIONAL TARIFF COMMISSION ACT, 2015 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 525 | NATIONAL TEXTILE UNIV ERSITY ORDINANC E, 2002 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 526 | THE NATIONAL TRAINING ORDINANCE, 1980 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 527 | THE NATIONAL UNIVERSITY OF COMPUTER AND EMERGING SCIENCES ORDINANCE, 2000 | 50 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 528 | THE NATIONAL UNIVERSITY OF MODERN LANGUAGE'S ORDINANCE, 2000 | 52 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 529 | THE NATIONAL UNIVERSITY OF PAKISTAN ACT, 2023 | 121 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 530 | THE NATIONAL UNIVERSITY OF SCIENCE S AND TECHNOLOGY ACT, 1997 | 43 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 531 | THE NATIONAL UNIVERSITY OF TECHNOLOGY ACT, 2018 | 76 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 532 | THE NATIONAL VOCATIONAL AND TECHNICAL TRAINING COMMISSION ACT, 2011 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 533 | THE NATIONAL ZAKAT F OUNDATION (MERGER IN THE BAIT -UL-MAL) ORDINANCE, 2001 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 534 | THE NATURAL GAS (DEVELOPMENT SURCHARGE) ORDINANCE, 1967 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 535 | NATURAL GAS REGULATORY AUTHORITY ORDINANCE, 2000 | 39 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 536 | THE NAVAL ARMAMENTS ACT, 1923 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 537 | The NAYA PAKISTAN HOUSING AND DEVELOPMENT AUTHORITY ACT, 2020 | 82 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 538 | THE NEGOTIABLE INSTRUMENTS ACT, 1881 | 160 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 539 | THE NET WORK ANALYSE R STUDY CENTRE (TRANSFER TO WAPDA) ORDINANCE, 1983 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 540 | THE NEWSPAPER EMPLOYEES (CONDITIONS OF SERVICE) ACT, 1973 | 37 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 541 | THE NEWSPRINT CONTROL ORDINANCE, 1971 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 542 | THE NFC INSTITUTE OF ENGINEERING AND TECHNOLOGY MULTAN ACT, 2012 | 89 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 543 | THE NON -PERFORMING ASSETS AND REHABILITATION OF INDUSTRIAL UNDERTAKINGS (LEGAL PROCEEDINGS) ORDINANCE 2000 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 544 | THE NORTHWEST FRONTIER CONSTABULARY ACT, 1915 | 44 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 545 | THE NOTARIES ORDINANCE, 1961 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 546 | THE OATH ACT, 1873 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 547 | THE OBSTRUCTIONS IN FAIRWAYS ACT, 1881 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 548 | THE OFFENCE OF QAZF (ENFORCEMENT OF HADD) ORDINANCE, 1979 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 549 | THE OFFENCE OF ZINA (ENFORCEMENT OF HUDOOD) ORDINANCE, 1979 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 550 | THE OFFENCES AGAINST PROPERTY (ENFORCEMENT OF HUDOOD) ORDINANCE, 1979 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 551 | THE OFFENCES IN RESPECT OF BANKS (SPECIAL COURTS) ORDINANCE, 1984 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 552 | THE OFFICIAL SECRETS ACT, 1923 | 59 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 553 | THE OFFICIAL TRUSTEE'S ACT, 1913 | 37 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 554 | THE OIL AND GAS DEVELOPMENT CORPORATION (RE - ORGANIZATION) ORDINANCE, 2001 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 555 | THE OIL AND GAS REGULATORY AUTHORITY ORDINANCE, 2002 | 95 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 556 | THE OIL SEEDS COMMITTEE ACT, 1946 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 557 | THE ORGANIZATION OF THE ISLAMIC CON FERENCE (IMMUNITIES AND PRIVIL EGES) ACT, 1977 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 558 | THE PAF AIR WAR COLLEGE INSTITUTE ACT, 2021 | 88 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 559 | The Pakistan Academy of Letter s’ Act, 2013 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 560 | THE PAKISTAN AERONAUTICAL COMPLEX BOARD ORDINANCE, 2000 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 561 | THE PAKISTAN AGRICULTURAL RESEARCH COUNCIL ORDINANCE, 1981 | 38 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 562 | THE PAKISTAN AIR FORCE ACT, 1953 | 264 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 563 | THE PAKISTAN AIRPORTS AUTHORITY ACT , 2023 | 122 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 564 | THE PAKISTAN AIR SAFETY INVESTIGATION ACT, 2023 | 70 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 565 | THE PAKISTAN ANIMAL QUARANTINE (IMPORT AND EXPORT OF ANIMALS AND ANIMAL PRODUCTS) ORDINANCE, 1979 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 566 | The [Pakistan] Arms Ordinance,1965 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 567 | THE PAKISTAN ARMY ACT, 1952 | 278 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 568 | THE PAKISTAN (ARMY AND AIR FORCE) RESERVES ACT, 1950 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 569 | THE PAKISTAN ATOMIC ENERGY COMMISSION ORDINANCE, 1965 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 570 | THE PAKISTAN BAIT -UL-MAL ACT, 1991 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 571 | THE PAKISTAN BANKING AND FINANCE SERVICES COMMISSION ACT, 1992 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 572 | THE PAKISTAN BANKING (PREVENTION OF DEFAULT AND EVASION OF LIABILITIES) ORDINANCE, 1947 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 573 | THE PAKISTAN BOY SCOUTS ASSOCIATION ORDINANCE, 1959 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 574 | THE PAKISTAN BROADCASTING CORPORATION ACT, 1973 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 575 | THE PAKISTAN CITIZENSHIP ACT, 1951 | 41 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 576 | THE PAKISTAN CIVIL AVIATION AUTHORITY ORDINANCE, 1982 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 577 | THE PA KISTAN CLIMATE CHANGE ACT, 2017 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 578 | THE P AKIST AN COAST GUARDS ACT , 1973 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 579 | THE PAKISTAN COINAGE ACT, 1906 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 580 | THE PAKISTAN COLLEGE OF PHYSICIANS AND SURGEONS ORDINANCE, I962 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 581 | THE PAKISTAN COMMISSIONS OF INQUIRY ACT, 1956 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 582 | THE PAKISTAN COMMISSIONS OF INQUIRY ACT, 2017 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 583 | THE PAKISTAN COUNCIL FOR SCIENCE AND TECHNOLOGY ACT, 2017 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 584 | THE PAKISTAN COUNCIL OF ARCHITECTS AND TOWN PLANNER ORDINANCE, 1983 | 60 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 585 | THE PAKISTAN COUNCIL OF RESEARCH IN WATER RESOURCES ACT, 2007 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 586 | THE PAKISTAN CO UNCIL OF SCIENTI FIC AND INDU STRIAL RESEARCH ACT, 1973 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 587 | THE PAKISTAN CURRENCY ACT, 1950 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 588 | THE PAKISTAN ELE CTRONIC MEDIA REGULATORY AUTHO RITY ORDINANC E, 2002 | 58 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 589 | THE PAKISTAN ENGINEERING COUNC IL ACT, 1975 | 74 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 590 | THE PAKISTAN ENVIRONMENTAL PROTECTION ACT, 1997 | 83 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 591 | THE PAKISTAN ESSENTIAL SERVICES (MAINTENANCE) ACT, 1952 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 592 | THE PAKISTAN (EXCHANGE OF PRISONERS) ORDINANCE, 1948 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 593 | THE PAKISTAN FISH INSPECTION AND QUALITY CONTROL ACT, 1997 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 594 | THE PAKISTAN GEN ERAL COSMETICS ACT, 2023 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 595 | THE PAKISTAN GIRL GUIDES ASSOCIATION ORDINANCE, 1960 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 596 | THE PAKISTAN GLOBAL INSTITUTE ACT, 2023 | 80 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 597 | THE PAKISTAN HALAL AUTHORITY ACT, 2016 | 88 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 598 | THE PAKISTAN HEALTH RESEARCH COUNCIL ACT, 2016 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 599 | THE PAKISTAN HOTELS AND RE STAURANTS ACT, 1976 | 45 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 600 | THE PAKISTAN INDUSTRIAL DEVELOPMENT CORPORATION (DISSOLUTION) ORDINANCE, 1984 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 601 | THE PAKISTAN INSTITUTE FOR PARLIAMENTARY SERVICES ACT, 2008 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 602 | PAKISTAN INSTITUTE OF DEVELOPMENT ECONOMICS ACT, 2010 | 89 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 603 | THE PAKISTAN INSTITUTE OF ENGINEERING AND APPLIED SCIENCES ORDINANCE, 2000 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 604 | THE PAKISTAN INSTITUTE OF FASHION AND DESIGN ACT, 2011 | 88 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 605 | THE PAKISTAN INSTITUTE OF INTERNATIONAL AFFAIRS (ADMINISTRATION) ORDINANCE, 1980 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 606 | THE PAKISTAN INSTITUTE OF MEDICAL SCIENCES (PIMS) ACT, 2023 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 607 | THE PAKISTAN INSTITUTE OF RESEARCH AND REGISTRATION OF QUALITY ASSURANCE ACT, 2023 | 104 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 608 | THE PAKISTAN INSURANCE CORPORATION ACT, 1952 | 81 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 609 | THE PAKISTAN INSURANCE CORPORATION (RE-ORGANIZATION) ORDINANCE, 2000 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 610 | THE PAKISTAN INTERNATIONAL AIRLINE CORPORATION (SUSPENSION OFTRADE UNIONS AND EXISTING AGREEMENTS) ORDER (REPEAL) ACT, 2008 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 611 | THE PAKISTAN INTERNATIONAL AIRLINES CORPORATION ACT, 1956 | 48 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 612 | THE PAKISTAN INTERNATIONAL AIRLINES CORPORATION (CONVERSION) ACT, 2016 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 613 | THE PAKISTAN JUNIOR CADET CORPS ACT, 1953 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 614 | THE PAKISTAN MADRASAH EDUCATION (ESTABLISHMENT AND AFFILIATION OF MODEL DINI MADARIS) BOARD ORDINANCE, 2001 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 615 | THE PAKISTAN MARITIME SHIPPING (TRANSFER OF MANAGED ESTABLISHMENTS) ORDINANCE, 1980 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 616 | THE PAKISTAN MARITIME ZONES ACT, 2023 | 56 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 617 | THE PAKISTAN MEDICAL AND DENTAL COUNCIL ACT, 2022 | 119 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 618 | THE PAKISTAN MEDICAL AND DENTAL COUNCIL ORDINANCE, 1962 | 85 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 619 | THE PAKISTAN MEDICAL COMMISSION ACT, 2020 | 101 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 620 | THE PAKISTAN MILITARY ACADEMY (DEGREES AND CERTIFICATES)ORDINANCE, 1959 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 621 | THE PAKISTAN MILITARY NURSING SERVICE ACT, 1952 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 622 | THE PAKISTAN NAMES AND EMBLEMS (PREVENTION OF UNAUTHORIZEDUSE) ACT, 1957 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 623 | THE PAKISTAN NATIONAL ACCREDITATION COUNCIL ACT, 2017 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 624 | THE PAKISTAN NA TIONAL COUNCIL OF THE ARTS ACT, 1973 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 625 | THE PAKISTAN NATIONAL SERVICE ORDINANCE, 1970 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 626 | THE PAKISTAN NATIONAL SHIPPING CORPORATION ORDINANCE, 1979 | 62 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 627 | THE PAKISTAN NAVAL ACADEMY (AWARD OF DEGREES) ORDINANCE, 1965 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 628 | THE PAKISTAN NAVY (EXTENSION OF SERVICE) ACT, 1950 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 629 | THE PAKISTAN NAVY ORDINANCE, 1961 | 262 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 630 | THE PAKISTAN NUCLEAR REGULATORY AUTHORITY ORDINANCE, 2001 | 65 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 631 | THE PAKISTAN N URSING COUNCIL ACT, 1973 | 58 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 632 | THE PAKISTAN ORDINANCE FACTORIES BOARD ORDINANCE, 1961 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 633 | THE PAKISTAN ORDNANCE FACTORIES BOARD ORDINANCE, 1961 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 634 | Pakistan Penal Code | 601 | Section table (`Datatset For FAISS.csv`) | ⚠ OCR dup |
| 635 | THE PAKISTAN PENAL CODE | 713 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) | ⚠ OCR dup |
| 636 | THE PAKISTAN PLANT QUARANTINE ACT, 1976 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 637 | THE PAKISTAN POSTAL SERVICES MANAGEMENT BOARD ORDINANCE, 2002 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 638 | THE PAKISTAN RA ILWAYS POLICE ACT, 1977 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 639 | THE PAKISTAN RANGERS ORDINANCE, 1959 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 640 | THE PAKISTAN RED CRESCENT SOCIETY ACT | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 641 | THE PAKISTAN REFUGEES REHABILITATION FINANCE CORPORATION (DISSOLUTION) ORDINANCE, 1980 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 642 | THE PAKISTAN SCIENCE FOUNDATION ACT, 1973 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 643 | THE PAKISTAN SINGLE WINDOW ACT , 2021 | 53 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 644 | THE PAKISTAN SPACE AND UPPER ATMOSPHERE RESEARCH COMMISSION ORDINANCE, 1981 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 645 | THE PAKISTAN STANDARDS AND QUALITY CONTROL AUTHORITY ACT, 1996 | 46 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 646 | THE PAKISTAN STUDY CENTRES, ACT 1976 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 647 | THE PAKISTAN TELECO MM UNICATION (RE-ORGANIZATION) ACT , 1996 | 131 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 648 | THE PAKISTAN TERRITORIAL FORCE ACT, 1950 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 649 | THE PAKISTAN TOBACCO BOARD ORDINANCE, 1968 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 650 | THE PAKISTAN TO URIST GUIDES ACT, 1976 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 651 | THE PAKISTAN TRADE CONTROL OF WILD FAUNA AND FLORA ACT, 2012 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 652 | The Pakistan Veterinary Medical Council Act 1996 | 37 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 653 | THE PARSI MARRIAGE AND DIVORCE ACT, 1936 | 53 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 654 | PART I] THE GAZETTE OF PAKISTAN, EXTRA., JULY 4, 2023 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 655 | THE PARTITION ACT, 1893 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 656 | THE PASSPORTS ACT, 1974 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 657 | THE PATENTS ORDINANCE, 2000 | 189 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 658 | THE PAYASYOUEARN SCHEME ACT , 1973 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 659 | THE PAYMENT OF WAGES ACT, 1936 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 660 | THE PAYMENT SYSTEMS AND ELECTRONIC FUND TRANSFERS ACT, 2007 | 92 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 661 | THE PENSIONS ACT, 1871 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 662 | THE PETROLEUM ACT, 1934 | 50 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 663 | THE PE TROLEUM PRODUCTS PETROLEUM LEVY ORDINANCE, 1961 | 23 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 664 | THE PHARMACY ACT, 1967 | 47 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 665 | PIR R OSHAN INSTITUTE OF PROGRESSIVE SCIENCES AND TECHNOLOGIES, MIRANSHAH ACT, 2023 | 119 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 666 | THE PLANT BREEDERS´ RIGHTS ACT, 2016 | 72 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 667 | THE POISONS ACT, 1919 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 668 | THE POLICE ACT 1861 | 90 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 669 | THE POLICE ACT, 1888 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 670 | THE POLICE (INCITEMENT TO DISAFFECTION) ACT, 1922 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 671 | Police Order, 2002 | 265 | Section table (`Datatset For FAISS.csv`) |  |
| 672 | THE POPULATION WELFARE PLANNING PROGRAMME (APPOINTMENT AND TERMINATION OF SERVICE) ORDINANCE, 1981 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 673 | THE PORT AUTHORITIES LANDS AND BUILDINGS (RECOVERY OF POSSESSION) ORDINANCE, 1962 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 674 | THE PORT QASIM AUTHORITY ACT, 1973 | 96 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 675 | THE PORTS ACT, 1908 | 118 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 676 | THE POST OFFICE ACT, 1898 | 120 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 677 | THE POST OFFICE NATIONAL SAVINGS CERTIFICATES ORDINANCE, 1944 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 678 | THE POWER ALCOHOL ORDINANCE, 1959 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 679 | THE POWERSOFATTORNEY ACT, 1882 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 680 | THE PRESIDENT’S SALARY, ALLOWANCES AND PRIVILEGES ACT, 1975 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 681 | THE PRESIDENT TO HOLD ANOTHER OFFICE ACT, 2004 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 682 | PRESS COUNCIL OF PAKISTAN ORDINANCE, 2002 | 41 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 683 | PRESS NEWSPAPER, NEWS AGENCIES AND BOOKS REGISTRATION ORDINANCE,2002 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 684 | THE PREVENTION AND CONTROL OF HUMAN TRAFFICKING ORDINANCE,2002 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 685 | THE PREVENTION OF ANTINA TIONAL A CTIVITIES ACT , 1974 | 34 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 686 | THE PREVENTION OF CORRUPTION ACT, 1947 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 687 | THE PREVENTION OF CRUELTY TO ANIMALS ACT, 1890 | 33 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 688 | THE PREVENTION OF ELECTRONIC CRI MES ACT, 2016 | 103 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 689 | THE PREVENTION OF GAMBLING ACT, 1977 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 690 | THE PREVENTION OF SEDITIOUS MEETINGS ACT, 1911 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 691 | THE PREVENTION OF SMUGGLING ACT, 1977 | 73 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 692 | THE PREVENTION OF SMUGGLING OF MIGRANTS ACT, 2018 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 693 | THE PREVENTION OF TRAFFICKING IN PERSONS ACT, 2018 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 694 | THE PRICE CONTROL AND PREVENTION OF PROFITEERING AND HOARDING ACT, 1977 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 695 | THE PRIME MINISTER'S SALARY, ALL OWANCES AND PRIVILEGES ACT, 1975 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 696 | THE PRISONERS ACT, 1900 | 52 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 697 | THE PRISONS ACT, 1894 | 67 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 698 | THE PRIV A TE MILIT A R Y ORGANIZA TIONS (ABOLITION AND PROHIBITION)ACT , 1973 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 699 | THE PRIVATE POWER AND INFRASTRUCTURE BOARD ACT, 2012 | 55 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 700 | THE PRIVATE SECURITY COMPANIES ORDINANCE, 2001 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 701 | THE PRIVATISATION COMMISSION ORDINANCE, 2000 | 64 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 702 | THE PRIVY PURSES (CHARGED EXPENDITURE) ACT, 1968 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 703 | THE PROBATION OF OFFENDERS ORDINANCE, 1960 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 704 | THE PROFESSIONS TAX LIMITATION ACT, 1941 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 705 | THE PROHIBITION (ENFORCEMENT OF HADD) ORDER (4 OF 1979 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 706 | THE PROHIBITION OF SMOKING AND PROTECTION OF NON - SMOKERS HEALTH ORDINANCE, 2002 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 707 | THE PROTECTION AGAINST HARASSMENT OF WOMEN AT THE WORK PLACE ACT, 2010 | 38 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 708 | PROTECTION OF BREAST -FEEDING AND CHILD NUTRITION ORDINANCE, 2002 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 709 | THE PROTECTION OF COMMUNAL PROPERTIES OF MINORITIES ORDINANCE, 2002 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 710 | THE PROTECTION OF ECONOMIC REFORMS ACT, 1992 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 711 | THE PROTECTION OF JOURNALIST S AND MEDIA PROFESSIONALS ACT , 2021 | 43 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 712 | THE PROTECTION OF PAKISTAN ACT, 2014 | 41 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 713 | THE PROTECTION OF PORTS (SPECIAL MEASURES) ACT, 1948 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 714 | THE PROVIDENT FUNDS ACT, 1925 | 37 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 715 | THE PROVINCIAL EMPLOYEES’ SOCIAL SECURITY ORDINANCE, 1965 | 107 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 716 | THE PROVINCIAL INDUSTRIAL DEVELOPMENT CORPORATION (WESTPAKISTAN) ORDINANCE, 1962 | 46 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 717 | THE PROVINCIAL INSOLVENCY ACT, 1920 | 118 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 718 | THE PROVINCIAL SERVICE TRIBUNALS (EXTEN SION OF PROVI SIONS OF THE CON STITUTIO N) ACT, 1974 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 719 | THE PROVISIONAL COLLECTION OF TAXES ACT, 1931 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 720 | p THE UNIVERSITY OF ISLAMABAD ACT, 2021 | 90 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 721 | THE PUBLIC ACCOUNTANTS´ DEFAULT ACT, 1850 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 722 | THE PUBLICATION OF LAWS OF PAKISTAN ACT, 2016 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 723 | THE PUBLICATION OF THE HOLY QURAN (ELIMINATION OF PRINTING ERRORS) ACT, 1973 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 724 | THE PUBLIC DEBT ACT, 1944 | 43 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 725 | PUBLIC FINANCE MANAGEMENT ACT, 2019 | 61 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 726 | THE PUBLIC GAMBLING ACT, 1867 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 727 | THE PUBLIC HEALTH (EMERGENCY PROVISION) ORDINANCE, 1944 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 728 | THE PUBLIC INTEREST DISCLOSURES ACT, 2017 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 729 | THE PUBLIC INVESTMENTS (FINANCIAL SAFEGUARDS) ORDINANCE, 1960 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 730 | THE PUBLIC ORDER (MEETINGS) ORDINANCE, 1958 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 731 | THE PUBLIC ORDER (POLITICAL UNIFORMS) ORDINANCE, 1958 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 732 | THE PUBLIC PRIVATE PARTNERSHIP AUTHORITY ACT , 2017 | 65 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 733 | THE PUBLIC PROCUREMENT REGULATORY AUTHORITY ORDINANCE, 2002 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 734 | THE PUNJAB LAWS ACT, 1872 | 33 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 735 | THE QANUNESHAHADAT , 1984 | 216 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 736 | Qanun-e-Shahadat Order, 1984 | 205 | Section table (`Datatset For FAISS.csv`) |  |
| 737 | THE QUAID -E-AZAM UNIVERSITY ACT, 1973 | 95 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 738 | THE QUAID -I-AZAM’S MAZAR (PROTECTION AND MAINTENANCE) ORDINANCE, 1971 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) | ⚠ OCR dup |
| 739 | THE QUAIDIAZAM´S MAZAR (PROTECTION AND MAINTENANCE)ORDINANCE, 1971 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) | ⚠ OCR dup |
| 740 | THE RAILWAY REGULATORY AUTHORITY ORDINANCE, 2002 | 85 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 741 | THE RAILWAYS ACT, 1890 | 167 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 742 | THE RAILWAYS (LOCAL AUTHORITIES, TAXATION) ACT, 1941 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 743 | THE RAILWAY STORES (UNLAWFUL POSSESSION) ORDINANCE, 1944 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 744 | THE RAILWAYS (TRANSPORT OF GOODS) ACT, 1947 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 745 | THE RECOGNITION AND ENFORCEMENT (ARBITRATION AGREEMENT AND FOREIGN ARBITRAL AWARDS ) ACT, 2011 | 25 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 746 | THE RECUSANT WITNESSES ACT, 1853 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 747 | THE REFORMATORY SCHOOLS ACT, 1897 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 748 | THE REGIONAL DEVELOPMENT FINANCE CORPORATION AND SMALL BUSINESS FINANCE CORPORATION (AMALGAMATION AND CONVERSION) ORDINANCE 2001 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 749 | THE REGIONAL DEVELOPMENT FINANCE CORPORATION ORDINANCE, 1985 | 52 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 750 | THE REGISTERED DESIGNS ORDINANCE, 2000 | 53 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 751 | THE REGISTERED LAYOUT -DESIGNS OF INTEGRATED CIRCUITS ORDINANCE, 2000 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 752 | THE REGISTRATION ACT, 1908 | 141 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 753 | THE REGISTRATION OF FOREIGNERS ACT, 1939 | 11 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 754 | THE REGULATION OF GENERATION, TRANSMISSION AND DISTRIBUTION OF ELECTRIC POWER ACT, 1997 | 160 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 755 | THE REGULATION OF MINES AND OILFIELDS AND MINERAL DEVELOPMENT (GOVERNMENT CONTROL) ACT, 1948 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 756 | THE RELIGIOUS SOCIETIES ACT, 1880 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 757 | THE REMOVAL FROM SERVICE (SPECIAL POWERS) (REPEAL) ACT, 2010 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 758 | THE REMOV AL OF A CCUSED PERSONS ACT , 1973 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 759 | THE REQUISITIONED LAND (CONTINUANCE OF POWERS) ORDINANCE, 1969 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 760 | THE REQUI SITION ED LAND (CONTINU ANCE OF POWER S) ORDINANCE, 1977 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 761 | THE RESERVISTS (REINSTATEMENT IN CIVIL EMPLOYMENT) ORDINANCE,1965 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 762 | THE REVENUE RECOVERY ACT, 1890 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 763 | THE REVOCATION OF PRIVILE GES ACT, 1992 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 764 | THE RICE MILLING CONTROL AND DEVELOPMENT (REPEAL) ORDINANCE, 1977 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 765 | THE RIGHT OF ACCESS TO INFORMATION ACT, 2017 | 44 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 766 | THE RIGHT TO FREE AND COMPULSORY EDUCATION ACT, 2012 | 37 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 767 | THE RIOT AND CIVIL COMMOTION RISKS INSURANCE ORDINANCE, 1947 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 768 | THE RIPHAH INTERNATIONAL UNIVERSITY ORDINANCE, 2002 | 50 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 769 | THE ROAD TRANSPORT WORKERS ORDINANCE, 1961 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 770 | THE RULERS OF ACCEDING STATES (ABOLITION OF PRIVY PURSES AND PRIVILEGES) ORDER, 1972 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 771 | THE RULES AND REGULATIONS CONTINUANCE ACT, 1937 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 772 | THE SACKED EMPLOYEES (REINSTATEMENT) ACT, 2010 | 50 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 773 | THE SAFEGUARD MEASURES ORDINANCE, 2002 | 75 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 774 | THE SALE OF GOODS ACT, 1930 | 71 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 775 | Sales Tax Act, 1990 | 586 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 776 | THE SARAIS ACT, 1867 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 777 | THE SBP BAN KING SERVICES COR PORATION ORDINANCE, 2001 | 51 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 778 | THE SECRETARIAT ALLOWANCE (RESCISSION OF ORDERS, ETC.) ORDINANCE, 2000 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 779 | THE SECURITIES ACT, 1920 | 44 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 780 | THE SECURITIES AND EXCHANGE COMMISSION OF PAKISTAN ACT, 1997 | 190 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 781 | THE SECURITY OF PAKISTAN ACT, 1952 | 64 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 782 | THE SEED ACT, 1976 | 54 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 783 | THE SENA TE (ELECTION) ACT , 1975 | 111 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 784 | THESENATE SECRETARIAT SERVICES ACT, 2017 | 28 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 785 | THE SERVICE TRIBUNALS ACT, 1973 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 786 | THE SETTLEMENT COMMISSIONERS (V ALIDA TION OF ORDERS) ACT , 1972 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 787 | THE SHAHEED ZULFIQAR ALI BHUTTO MEDICAL UNIVERSITY , ISLAMABAD , ACT, 2013 | 83 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 788 | THE SHIFA TAMEER -E-MILLAT UNIVERSITY ACT, 2012 | 84 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 789 | THE SHOR T TITLES ACT , 1973 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 790 | THE SIKH GURDWARAS (SUPPLEMENTARY) ACT, 1925 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 791 | THE SIND CO-OPERATIVE SOCIETIES ACT, 1925 | 164 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 792 | THE SINDH INCUMBERED ESTATES ACT, 1896 | 49 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 793 | THE SINDH REVENUE JURISDICTION ACT, 1876 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 794 | THE SIND TEXTILE BOARD ORDINANCE, 1949 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 795 | THE SIR SYED CASE (CEN TER FOR AD VANC ED STUDIES IN ENGINEERING) INSTITUTE OF TECHNOLOG Y, ISLAMABAD ACT, 2018 | 81 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 796 | THE SMALL AND MEDIUM EXTERPRISES DEVELOPMENT AUTHORITYORDINANCE, 2002 | 53 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 797 | SMALL CLAIMS AND MINOR OFFENCES COURTS ORDINANCE, 2002 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 798 | THE SMART INSTITUTE OF SCIENCES & TECHNOLOGY ACT, 2022 | 101 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 799 | THE SOCIETIES REGISTRATION ACT, 1860 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 800 | THE SOLDIER (LITIGATION) ACT, 1925 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 801 | THE SOUTH ASIAN STRATEGIC STABILITY INSTITUTE UNIVERSITY ISLAMABAD ACT, 2013 | 74 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 802 | THE SPECIAL COURTS F OR SPEEDY TRIALS (REPEAL) ACT, 1996 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 803 | THE SPECIAL ECONOMIC ZONES ACT, 2012 | 65 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 804 | THE SPECIAL MARRIAGE ACT, 1872 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 805 | SPECIAL TECHNOLOGY ZONES AUTHORITY ACT, 2021 | 74 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 806 | THE SPECIFIC RELIEF ACT, 1877 | 117 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 807 | THE SPORTS (DEVELOPMENT AND CONTROL) ORDINANCE, 1962 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 808 | THE STAGECARRIAGES ACT, 1861 | 28 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 809 | THE STANDARDS OF WEIGHT ACT, 1939 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 810 | THE STANDARD TIME (INTERPRETATION OF REFERENCES) ORDINANCE, 1943 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 811 | THE STAPLE COTTON (EXCISE DUTY) ORDINANCE, 1978 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 812 | THE STATE BANK OF PAKISTAN ACT, 1956 | 133 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 813 | THE STATE IMMUNITY ORDINANCE, 1981 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 814 | THE STATE -OWNED ENTERPRISES (GOVERNANCE AND OPERATIONS) ACT, 2023 | 86 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 815 | THE STOCK EXCHANGE S (CORPORATISATION, DEMUTUALIZATION AND INTEGRATION) ACT, 2012 | 65 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 816 | THE SUCCESSION ACT, 1925 | 485 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 817 | THE SUGARCANE ACT, 1934 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 818 | THE SUGAR EXPORT SUBSIDY FUND ORDINANCE, 1970 | 10 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 819 | THE SUITS VALUATION ACT, 1887 | 14 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 820 | THE SUPERIOR COURTS (COURT DRESS AND MODE OF ADDRESS) ORDER (REPEAL) ACT, 2020 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 821 | THE SUPREME COUR T AND HIGH COUR T (EXTENSION OF JURISDICTION T OCER T AIN TRIBAL AREAS) ACT , 1973 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 822 | THE SUPREME COURT AND HIGH COURT (EXTENSION OF JURISDICTION TO FEDERALLY ADMINISTERED TRIBAL AREAS) ACT, 2018 | 3 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 823 | THE SUPREME COURT (NUMBER OF JUDGES) ACT, 1997 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 824 | THE SUPREME COURT (PRACTICE AND PROCEDURE) ACT, 2023 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 825 | THE SUPREME COURT (REVIEW OF JUDGMENTS AND ORDERS) ACT, 2023 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 826 | THE SURRENDER OF ILLICIT ARMS ACT, 1991 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 827 | THE SURVEY FOR DOCUMENTATION OF N ATIONAL ECONOMY ORDINANCE, 2000 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 828 | THE SURVEYING AND MAPPING ACT, 2014 | 41 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 829 | THE SYSTEM OF SARDARI (ABOLITION) ACT, 1976 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 830 | THE TEA (CONTROL OF PRICES, DISTRIBUTION AND MOVEMENT)ORDINANCE, 1960 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 831 | THE TEA ORDINANCE, 1959 | 35 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 832 | THE TEA PLANTATIONS LABOUR ORDINANCE, 1962 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 833 | THE TELEGRAPHS ACT, 1885 | 62 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 834 | THE TERRITORIAL WATERS AND MARITIME ZONES ACT, 1976 | 29 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 835 | THE TERRORI ST AFFECTED AREAS (SPECIAL COURT S) ACT , 1992 | 45 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 836 | THE TOLLS ACT, 1851 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 837 | THE TOLLS (ARMY AND AIR FORCE) ACT, 1901 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 838 | THE TORTURE AND CUSTODIAL DEATH (PREVENTION AND PUNISHMENT) ACT, 2022 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 839 | THE TRADE DEVELOPMENT AUTHORITY OF PAKISTAN ACT, 2013 | 82 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 840 | THE TRADE DISPUTE RESOLUTION ACT , 2022 | 87 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 841 | TRAD E MAR KS ORDINANC E, 2001 | 288 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 842 | THE TRADE ORGANIZATION S ACT, 2013 | 63 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 843 | THE TRAFFIC OFFENCES (SPECIAL COURTS) ORDINANCE, 1981 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 844 | THE TRAINED PARAMEDICAL STAFF FACILITY ACT, 2023 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 845 | THE TRAMWAYS ACT, 1886 | 88 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 846 | THE TRANSFER OF EVACUEE DEPOSITS ACT, 1956 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 847 | THE TRAN SFER OF EVACUEE LAND (KATCHI ABAD I) ACT, 1972 | 12 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 848 | THE TRANSFER OF OFFENDERS ORDINANCE, 2002 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 849 | THE TRANSFER OF POPULATION WELFARE PROGRAMME (FIELD ACTIVITIES) ORDINANCE, 1983 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 850 | Transfer of Property Act | 215 | Section table (`Datatset For FAISS.csv`) |  |
| 851 | THE TRANSFER OF PROPERTY ACT, 1882 | 232 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 852 | THE TRANSGENDER PERSONS (PROTECTION AND RIGHTS) ACT, 2018 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 853 | THE TRANSPLANTATION OF HUMAN ORGANS AND TISSUES ACT, 2010 | 27 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 854 | THE TRAVEL AGENCIES ACT, 1976 | 18 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 855 | THE TREASURETROVE ACT, 1878 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 856 | THE TRIBAL AREAS (RESTORATION OF JUDISDICTION) ACT, 1964 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 857 | THE TRUSTS ACT, 1882 | 124 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 858 | THE UNANI, AYURVEDIC AND HOMOEOPATHIC PRACTITIONERS ACT, 1965 | 68 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 859 | UNDER PROOF READING Page 1 of 10 THE MERCHANDISE MARKS ACT, 1889 | 40 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 860 | UNDER PROOF READING Page 1 of 11 THE CIVIL PIONEER FORCE ORDINANCE, 1965 | 33 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 861 | UNDER PROOF READING Page 1 of 24 THE PARTNERSHIP ACT, 1932 | 79 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 862 | UNDER REVIEW Page 1 of 17 s THE ARBITRATION ACT, 1940 | 61 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 863 | UNDER REVIEW Page 1 of 2 THE EX-GOVERNMENT SERVANTS (EMPLOYMENT WITH FOREIGN GOVERNMENTS) (PROHIBITION) ACT, 1966 | 5 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 864 | THE UNITED NATIONS (DECLARATION OF DEATH OF MISSING PERSONS)ACT, 1956 | 24 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 865 | THE UNITED NATIONS (PRIVILEGES AND IMMUNITIES) ACT, 1948 | 26 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 866 | THE UNITED NATIONS (SECURITY COUNCIL) ACT, 1948 | 4 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 867 | Up dated till 19.04.2023 | 15 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 868 | Updatedtill19.04.2023 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 869 | THE USURIOUS LOANS ACT, 1918 | 13 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 870 | U THE PAKISTAN SOVEREIGN WEALTH FUND ACT, 2023 | 69 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 871 | THE VACCINATION ACT, 1880 | 32 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 872 | THE VAGRANCY (KARACHI DIVISION) ACT, 1950 | 19 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 873 | THE VALIDATION OF LAWS ACT, 1975 | 36 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 874 | VIRTUAL UNIVERSITY ORDINANCE, 2002 | 70 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 875 | THE VOLUNTARY DECLARATION OF DOMESTIC ASSETS ACT, 2018 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 876 | THE VOLUNTARY SOCIAL WELFARE AGENCIES (REGISTRATION ANDCONTROL) ORDINANCE, 1961 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 877 | THE WAR INJURIES (COMPENSATION INSURANCE) ACT, 1943 | 45 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 878 | THE WAR INJURIES ORDINANCE, 1941 | 20 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 879 | THE WAR RISKS INSURANCE ORDINANCE, 1971 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 880 | THE WASTE LANDS (CLAIMS) ACT, 1863 | 31 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 881 | THE WEIGHTS AND MEASURES (INTERNATIONAL SYSTEM) ACT, 1967 | 45 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 882 | THE WEST PAKISTAN FAMILY COURTS ACT, 1964 | 43 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 883 | THE WEST PAKISTAN INDUSTRIAL DEVELOPMENT CORPORATION(TRANSFER OF PROJECTS AND COMPANIES) ACT, 1974 | 21 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 884 | The West Pakistan Juvenile Smoking (Repeal) Act, 2018 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 885 | THE WEST PAKISTAN MATERNITY BENEFIT ORDINANCE, 1958 | 22 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 886 | THE WEST PAKISTAN PROHIBITION OF SMOKING IN CINEMA HOUSES (REPEAL) ACT, 2019 | 2 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 887 | THE WEST PAKISTAN REGULATION AND CONTROL OF LOUD SPEAKERS AND SOUND AMPLIFIERS ORDINANCE, 1965 | 9 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 888 | THE WEST PAKISTAN SHOPS AND ESTABLISHMENTS ORDINAN CE, 1969 | 55 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 889 | THE WEST PAKISTAN SMALL INDUSTRIES CORPORATION (DISSOL UTION) ACT, 1972 | 7 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 890 | THE WHITE PHOSPHOROUS MATCHES PROHIBITION ACT, 1913 | 6 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 891 | THE WILD BIRDS AND ANIMALS PROTECTION ACT, 1912 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 892 | THE WIRELESS TELEGRAPHY ACT, 1933 | 16 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 893 | THE WITNESS PROTECTION, SECURITY AND BENEFIT ACT, 2017 | 17 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 894 | THE WOMEN IN DISTRESS AND DETENTION FUND ACT, 1996 | 8 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 895 | THE WOMEN'S UNIVERSITY ORDINANCE, 1985 | 81 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 896 | THE WORKERS' WELFARE FUND ORDINANCE, 1971 | 42 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 897 | THE WORKMEN'S COMPENSATION ACT, 1923 | 138 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 898 | THE WORKS OF DEFENCE ACT, 1903 | 77 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 899 | THE ZAINAB ALERT, RESPONSE AND RECOVERY ACT, 2020 | 30 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
| 900 | THE ZAKAT AND USHR ORDINANCE, 1980 | 135 | Pakistan Code PDF text (`pakistan_code_pdf_data.json`) |  |
