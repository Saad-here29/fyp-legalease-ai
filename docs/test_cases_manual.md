# Manual Test Cases — LegalEase AI

These are manual (black-box) test cases for every implemented feature, drafted
2026-10-05 for the FYP-2 mid evaluation. Requirement IDs follow the FYP-1
Final Report (see `docs/fyp2_mid_gap_report.md`).

**How to read "Actual" and "Status":**
- **Pass (Oct QA):** recorded in the October 2026 quality pass (2026-10-04;
  113 API checks and 62 page loads; `docs/TEST_PLAN.md` § 9).
- **Pass (Sept audit):** recorded in the September pre-demo audit and demo
  script (`PROJECT_CONTEXT.md`).
- **To run:** not yet executed as a manual case. Run it before the panel and
  fill in both columns.

Cases marked † call the LLM (Groq) and use the shared daily token budget.
Run them sparingly.

**Setup:**
- Backend: `uvicorn app.main:app` on `:8000`.
- Frontend: `npm run dev` on `:5173`.
- Accounts: one lawyer, one client, one student, and a second lawyer
  ("outsider"), all verified.

## 1. Authentication (FR-AUTH / SEC)

| ID | Module | Requirement | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| MT-AUTH-01 | Auth | Sign-up (lawyer) | Sign up as a lawyer with bar details → read the OTP from the server log → enter it | Account verified; redirected to the lawyer dashboard | Verified and logged in | Pass (Oct QA) |
| MT-AUTH-02 | Auth | Sign-up (client, student) | Repeat MT-AUTH-01 for client and student | Each lands on its own dashboard | Client and student: signup 202, verify 200, /me role correct | Pass (2026-10-05) |
| MT-AUTH-03 | Auth | Duplicate email | Sign up again with a verified account's email | 409, "account already exists" with hint | 409 `already_exists`, hint "Try signing in or use a different email."; UI shows both | Pass (2026-10-05) |
| MT-AUTH-04 | Auth | Re-sign-up while pending | Sign up, don't verify, sign up again with the same email | A new code is sent; no duplicate account | Second signup 202; one row; new code issued; name unchanged | Pass (2026-10-05) |
| MT-AUTH-05 | Auth | Wrong / expired OTP | Enter a wrong code; then a code older than 10 min | Rejected with a clear message | Wrong code rejected (Oct QA); correct code 11 min old → 422 "Verification code has expired." + resend hint | Pass (2026-10-05) |
| MT-AUTH-06 | Auth | Login | Log in with valid credentials | Dashboard for the user's role | Logged in (about 6 s) | Pass (Oct QA) |
| MT-AUTH-07 | Auth | Wrong password / unknown email | Log in with a wrong password; then with an unknown email | Both 401 with the same message (no account enumeration) | Both 401 "Invalid email or password." | Pass (2026-10-05) |
| MT-AUTH-08 | Auth | Lockout (5 attempts) | Enter a wrong password 5 times, then the right one | Account temporarily locked | Locked after 5; reset unlocks | Pass (Oct QA) |
| MT-AUTH-09 | Auth | Forgot / reset password | Forgot password → code from log → new password → log in | Old password fails, new one works | Reset worked and unlocked the account | Pass (Oct QA) |
| MT-AUTH-10 | Auth | Logout revokes tokens (SEC-06) | Log in, copy the access token, log out, call `/auth/me` with the old token | 401 | 401 | Pass (Oct QA) |
| MT-AUTH-11 | Auth | Session refresh | Stay idle past 60 min with the tab open, then act | Session silently refreshed (7-day refresh token) | API level: expired access token 401 → refresh (cookie) 200 → /me 200. Not waited 60 min in a browser | Pass (2026-10-05, API level) |
| MT-AUTH-12 | Auth | Protected routes | Log out, open `/cases` directly | Redirected to login | Signed out, /cases → /login | Pass (2026-10-05) |

## 2. Case management (FR-CM01–07)

| ID | Module | Requirement | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| MT-CM-01 | Cases | FR-CM01 create | Lawyer: Cases → New case → title, type (Divorce), description → Create | Case appears with status ASSIGNED (auto from CREATED) | 201; status assigned | Pass (Oct QA) |
| MT-CM-02 | Cases | FR-CM01 validation | Submit an invalid case type (API); then an empty title (UI) | 422; inline error; no case created | Invalid type 422 (now with message + hint); empty title: Create button stays disabled below 3 characters, no request; no inline message | Pass (2026-10-05); no inline message |
| MT-CM-03 | Cases | FR-CM02 link client | Open the case → add client by email | Client linked; timeline shows it | Linked | Pass (Oct QA) |
| MT-CM-04 | Cases | FR-CM02 unknown client | Add a client email that has no account | 404 "ask them to sign up first" | 404 | Pass (Oct QA) |
| MT-CM-05 | Cases | FR-CM02 isolation | Outsider lawyer and student open the case URL / API | 403 or 404; case not listed | Blocked | Pass (Oct QA) |
| MT-CM-06 | Cases | FR-CM06 valid transitions | Move ASSIGNED → IN_PROGRESS → HEARING_SCHEDULED → IN_PROGRESS → CLOSED | Each move succeeds and appears on the timeline | All valid moves succeeded | Pass (Oct QA) |
| MT-CM-07 | Cases | FR-CM06 invalid transition | From CLOSED try any other status | 409 with hint | 409 | Pass (Oct QA) |
| MT-CM-08 | Cases | FR-CM05 timeline | Open a case with documents, research and status changes | All events in time order with actor names | Shown | Pass (Oct QA) |
| MT-CM-09 | Cases | FR-CM07 client read-only | Log in as the linked client, open the case | Can view; no edit, status or upload controls; write API calls 403 | Read-only; writes 403 | Pass (Oct QA) |
| MT-CM-10 | Cases | FR-CM07 client list | Client opens Cases | Only their own cases listed | Only own cases | Pass (Sept audit) |
| MT-CM-11 | Cases | General case types | Create a civil and a criminal case | Created with that type; family types still listed | civil and criminal cases created live; existing 10 cases unchanged by the migration (same hash before/after) | Pass (2026-10-06) |
| MT-CM-12 | Cases | Case number, court, parties, next hearing | Create with all fields; change the hearing date; open as the client | Fields saved and shown; hearing change on the timeline; client reads, cannot edit | Fields shown on list, detail and both dashboards; timeline "Next hearing: 2026-10-20" → "2026-10-27"; client PATCH 403. Detail endpoint dropped the fields: fixed `ccf90e1` | Pass (2026-10-06) after fix |

## 3. Documents and analysis (FR-CM03, FR-DOC-01–04, FR-OCR-03)

| ID | Module | Requirement | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| MT-DOC-01 | Documents | FR-DOC-01 PDF upload | Upload a digital PDF to a case | Listed with its original name; text extracted | Demo judgment PDF: 201, original name kept, 6,856 characters, 1.1 s | Pass (2026-10-05) |
| MT-DOC-02 | Documents | FR-DOC-01 TXT, DOCX | Upload a .txt, then a .docx | Both accepted, text extracted | TXT (Oct QA); DOCX 201, text extracted | Pass (2026-10-05) |
| MT-DOC-03 | Documents | FR-DOC-01 rejected types | Upload .exe (then .js, .zip) | 415 with the list of allowed types; nothing left on disk | .exe → 415 live; .js/.zip covered by `test_upload_cleanup.py` | Pass (Oct QA) |
| MT-DOC-04 | Documents | Size limit | Upload a file over 20 MB | 413; nothing left on disk | 21 MB file → 413 | Pass (Oct QA) |
| MT-DOC-05 | Documents | Path safety | Upload a file named `..\..\evil.pdf` (via API) | Stored under a generated name; display name sanitised | Display name `evil.pdf`; stored as a generated name inside the upload folder | Pass (2026-10-05) |
| MT-DOC-06 | Documents | Scanned PDF (OCR) | Upload a scanned (image-only) PDF | Text extracted by OCR; no warning | 4-page scanned judgment: 6,650 characters, 0.9% character errors, 11.5 s; no warning; Analyse enabled | Pass (2026-10-05) |
| MT-DOC-07 | Documents | Images (OCR) | Upload a PNG and a JPG | Text extracted; PNG/JPG listed in the upload strip | PNG 1.6%, JPG 0.6% character errors, about 3 s each; strip lists PDF, DOCX, TXT, PNG, JPG | Pass (2026-10-05) |
| MT-DOC-12 | Documents | Urdu OCR | Upload a scanned Urdu page (Naskh font) | Urdu text extracted, shown right to left | 262 characters, 1.5% character errors (5.8% before the per-page Urdu re-read, fixed `2d530fa`); RTL display fixed `3e47b16`. Nastaliq not tested | Pass (2026-10-05) |
| MT-DOC-13 † | Analysis | Analyse an OCR'd image | Upload a PNG and a JPG of a judgment page, Analyse | Summary and entities from the OCR text | PNG 10 s, JPG 16 s: summaries correct; NER parties include OCR misreads ("Aqeel Anmed Abbasi") | Pass (2026-10-06) |
| MT-DOC-08 † | Analysis | FR-DOC-02/03/04 | Analyse the Crl.P. 187-P/2026 petition | Summary, key clauses, risks, parties, dates, references (NER) | Full analysis, about 8 s | Pass (Sept audit) |
| MT-DOC-09 | Analysis | No text to analyse | Analyse a document with no extracted text | 422 with hint, no AI call | 422 | Pass (Oct QA) |
| MT-DOC-10 | Documents | RBAC | Outsider lawyer tries to view/analyse the document | 403/404 | Blocked | Pass (Oct QA) |
| MT-DOC-11 | Documents | FR-OCR-03 storage | After MT-DOC-01, check that the file and its text are kept | File on disk under a generated name; text in the database | File on disk under generated name; 6,856 characters in the database; SHA-256 stored | Pass (2026-10-05) |

## 4. AI legal chat (FR-AI-01–05)

| ID | Module | Requirement | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| MT-AI-01 † | Chat | FR-AI-02/04 statute answer | Ask "What is the procedure for talaq in Pakistan?" | Short answer box, cited answer with `[n]` markers, numbered sources (MFLO) | Cited answer | Pass (Sept audit) |
| MT-AI-02 † | Chat | FR-AI-04 section answer | Ask "What is the punishment for theft?" | Cites PPC s. 379 | Cited s. 379 | Pass (Sept audit) |
| MT-AI-03 † | Chat | FR-AI-03 refusal | Ask "How do I make a cricket bat?" | Polite refusal; no sources; no invented law | Refused | Pass (Sept audit) |
| MT-AI-04 † | Chat | FR-AI-01 Urdu | Ask a legal question in Urdu script | Answer in Urdu, with citations | Urdu answer starting مختصر جواب, citing MFLO and the Family Courts Act; 31 s. It says the passages lack the full text of s.7 (the known retrieval gap) | Pass (2026-10-06) |
| MT-AI-05 † | Chat | FR-AI-01 Urdu refusal | Ask an off-topic question in Urdu | Refusal in Urdu | Urdu off-topic question refused in Urdu, no sources | Pass (2026-10-06) |
| MT-AI-06 † | Chat | FR-AI-04 no case law | Ask for "leading Supreme Court judgments on bail" | Answer from statutes only; no invented case citations | "LegalEase's statute library does not contain Supreme Court judgments…"; CrPC passages cited; no case citations (PLD/SCMR etc.) | Pass (2026-10-06) |
| MT-AI-07 † | Chat | FR-AI-05 follow-up | Ask a question, then "what about the appeal?" | Follow-up understood from context | Not run: a follow-up answer costs about 8k tokens, past this run's Groq cap | to run |
| MT-AI-08 | Chat | FR-AI-05 history | Reload the page, reopen the session | Every earlier message shown in order | History endpoint returns question then answer, in order (API level) | Pass (2026-10-06, API level) |
| MT-AI-09 | Chat | Session privacy | Another user requests the session's history via the API | 404 | 404 | Pass (Oct QA) |
| MT-AI-10 | Chat | REL-04 AI down | Use an invalid Groq key (or exhausted budget), ask a question | 503 "AI unavailable" message; rest of app works | 503; app usable | Pass (Sept audit) |

## 5. Legal research (FR-RES-01–03)

| ID | Module | Requirement | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| MT-RES-01 † | Research | FR-RES-01 search | Search "bail in non-bailable offences" | CrPC s. 497 among top results, with titles and scores | s. 497 found | Pass (Sept audit) |
| MT-RES-02 † | Research | Result detail | Open a result | Full passage, statute title and section | to run | to run |
| MT-RES-03 † | Research | Save to case | Save a result to a case | Appears on the case timeline | Saved CrPC result to the case: 201; appears on the case timeline as "Research saved" | Pass (2026-10-06) |
| MT-RES-04 † | Research | Off-topic search | Search a non-legal phrase | "No relevant results" rather than weak matches | Was: 10 weak passages, no warning. Fixed `e822fc5`: results kept, note "No strong match…" (best 0.43) | Pass (2026-10-06) after fix |
| MT-RES-05 | Research | Empty query | Submit an empty search | Validation message, no request | Search button disabled; submitting sends no request | Pass (2026-10-05) |
| MT-RES-06 † | Research | FR-RES-03 latency | Time five searches | Record the times (target ≤2 s; about 3 s expected) | "bail in a non-bailable offence": 1.8 s including the rewrite (one timed search; Groq cap) | Pass (2026-10-06), 1 sample |

## 6. Contracts (FR-CON-01, 03, 04)

| ID | Module | Requirement | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| MT-CON-01 † | Contracts | FR-CON-01 NDA | Lawyer drafts an NDA with party names and terms | Full draft with required clauses | Drafted | Pass (Sept audit) |
| MT-CON-02 † | Contracts | FR-CON-01 employment, service | Draft the other two templates | Both drafted | Drafted | Pass (Oct QA) |
| MT-CON-03 | Contracts | FR-CON-03 compliance | Run the compliance check on MT-CON-01 | Pass/fail per required clause; unfilled placeholders listed | Report shown | Pass (Sept audit) |
| MT-CON-04 | Contracts | FR-CON-03 missing clause | Remove the confidentiality clause text, re-check | That clause marked missing | Edit draft without the confidentiality clause → saved as version 2; that clause marked missing (automated: `test_contract_edit.py`, incl. HTTP). Not yet clicked through live | Pass (2026-10-06, automated) |
| MT-CON-05 | Contracts | RBAC | Client or student opens Contracts / calls the API | Not available; API 403 | Client and student can't draft | Pass (Oct QA) |
| MT-CON-06 | Contracts | FR-CON-04 versions | Open a draft's versions | Version 1 listed | Draft → compliance → versions passed | Pass (Oct QA) |

## 7. Platform and non-functional

| ID | Module | Requirement | Steps | Expected | Actual | Status |
|---|---|---|---|---|---|---|
| MT-PLT-01 | Platform | Health | Open `http://127.0.0.1:8000/health` | 200 OK | 200 | Pass (2026-10-05) |
| MT-PLT-02 | Platform | USE-03 responsive | Open every page at desktop and phone width for each role | No horizontal overflow; nav usable | 62 page loads, 0 overflow | Pass (Oct QA) |
| MT-PLT-03 | Platform | Unknown route | Open `/simulator` and `/nonsense` | Styled 404 page with a way back | 404 page | Pass (Oct QA) |
| MT-PLT-04 | Platform | USE-04 error hints | Trigger a 409, 415 and 422 | Message plus hint shown in the UI | 415 toast "Files of type .exe are not supported. Allowed: …"; 409 shows message + hint; 422 now has message + hint (was missing: fixed `00bae27`) | Pass (2026-10-05) after fix |
| MT-PLT-05 | Platform | Database down | Stop the network, load a page | 503 "database unavailable" with hint; no stack trace | Live network outage at 20:50: uploads returned 503 "database unavailable" after one retry; no stack trace; recovered when the network returned | Pass (2026-10-05, unplanned) |
| MT-PLT-06 | Platform | USE-01 clicks | Count clicks from the dashboard to a created case | ≤3 | 2 clicks: dashboard "New case", then "Create case" (plus typing the title) | Pass (2026-10-05) |
| MT-PLT-07 | Platform | PER-01 page time | Time the dashboard, case list and case detail loads | Record (target ≤2 s) | Warm loads: cases 1.0–1.2 s, case detail 1.5–1.8 s, client dashboard 1.4–1.6 s; first load of a page up to 6–10 s (Vite dev compile + Singapore DB) | Pass (2026-10-06) warm; first load slow |
| MT-PLT-08 | Platform | Desktop and phone width | Lawyer: dashboard, cases, case, chat, contract; client: dashboard, case at 1440 and 390 px | Content shown, no horizontal overflow, no family-only hint | 22/22 views pass at both widths (screenshots s5-*.png); "Timeline 0" while loading fixed `192d68e` | Pass (2026-10-06) |

## Not testable yet (not implemented)

Not built, so there are no cases for:
- FR-CM04 (hearings);
- FR-RES-04 (similar cases);
- FR-CON-02 (clause suggestions);
- FR-PS-01–04 (practice simulator);
- FR-NOT-01–03 (notifications);
- document classification;
- PDF export;
- contract diff.

**OCR (FR-OCR-01, 02, 04)** needs Tesseract and Poppler installed first. Add
cases when they are.

## Summary

"Pass" counts three cases that passed only in part (MT-AUTH-05, MT-CM-02 and
MT-DOC-02); the rest of each is still to run. Four cases are "to run (live
re-check)": the Oct QA run found a bug there, and the fix has unit tests but
hasn't been re-run live.

| Section | Cases | Pass | To run |
|---|---:|---:|---:|
| Auth | 12 | 6 | 6 |
| Cases | 10 | 10 | 0 |
| Documents and analysis | 11 | 7 | 4 |
| AI chat | 10 | 5 | 5 |
| Research | 6 | 1 | 5 |
| Contracts | 6 | 5 | 1 |
| Platform and NFR | 7 | 3 | 4 |
| **Total** | **62** | **37** | **25** |
