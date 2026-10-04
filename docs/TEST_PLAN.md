# LegalEase AI — Test Plan

**Project:** LegalEase AI, an AI-powered online lawyer management and
legal assistance platform.
**Scope:** auth, case management, AI chat, legal research, document
analysis (with OCR/text extraction), and contract drafting and compliance.
**Reference:** Final Report § 4.3 (Test Strategy), Tables 4.2–4.5.
**Updated:** October 2026: 210 automated backend tests, 85% line coverage.

---

## 1. Objectives

| Goal | How it's verified |
|---|---|
| Authentication: signup, OTP, login, lockout, token revocation, password reset | Unit and HTTP tests (in-memory SQLite) |
| Access control and the case state machine | Unit tests against `CaseService`; HTTP checks with real accounts (§ 9) |
| Upload safety: generated storage names, type and size checks, cleanup | HTTP tests with a temporary upload folder |
| Text extraction and the "no text" path | Unit tests (`OCRService`); HTTP tests with a stubbed extractor |
| Chat: language, refusal, history budget, citation checker | Offline unit tests (the model is stubbed; no Groq calls) |
| Retrieval helpers: section lookup, index stats, title mapping, chunk trimming | Pure-Python unit tests |
| Contracts: required clauses, unfilled placeholders | Unit tests |
| Legal NER: entity grouping, post-processing, the real model | Unit tests (some load the model from `backend/storage/models/legal_ner`) |
| Database failure handling | Retry and 503 tests with a failing session |
| Production settings | API docs hidden outside development |

---

## 2. Test levels

### 2.1 Automated backend tests (`backend/app/tests/`)

```bash
cd backend
pytest                               # all 210, with coverage (pyproject addopts)
pytest -o addopts="" -q              # without coverage, faster
```

- **Database:** each test gets a fresh in-memory SQLite database
  (`conftest.py`).
- **Model calls:** none. Every test that would reach Groq stubs the client,
  and some tests fail on purpose if the model is called.
- **HTTP tests:** these use FastAPI's `TestClient` against the real app.

### 2.2 End-to-end checks against a running system

These ran in the October 2026 quality pass, over real HTTP with fresh
accounts. Results are in § 9.

### 2.3 Manual UI checks

Every page is checked at desktop (1280 px) and phone (390 px) width in a
real browser, for each role. Results are in § 9.

---

## 3. Test inventory

| File | Tests | Covers |
|---|---:|---|
| `test_health.py` | 2 | `/health`, root |
| `test_api_docs.py` | 5 | `/docs`, `/redoc`, `/openapi.json` only in development |
| `unit/test_auth_service.py` | 9 | UT-AUTH-001…009 (below) |
| `unit/test_signup_pending.py` | 2 | Re-registering an unverified email changes nothing but the code |
| `unit/test_logout_revocation.py` | 5 | After logout, access and refresh tokens are 401, on every device |
| `unit/test_case_service.py` | 9 | UT-CASE-001…005, automatic created → assigned on the timeline |
| `unit/test_quality_pass_fixes.py` | 6 | Urdu refusal, 409 for taken emails, timeline names in one query |
| `unit/test_upload_paths.py` | 21 | Path traversal (`../`, `..\`, absolute, UNC), null bytes, long names |
| `unit/test_upload_cleanup.py` | 8 | Rejected uploads leave no file; size cap; cleanup on failure |
| `unit/test_upload_extraction.py` | 8 | "No text" warning, upload capabilities |
| `unit/test_analyze_no_text.py` | 4 | Analysing a text-less document is 422, with no model call |
| `unit/test_ocr_service.py` | 4 | UT-OCR-001…003 |
| `unit/test_chat_language.py` | 9 | Answer in the language of the question (prompt checks) |
| `unit/test_chat_history_budget.py` | 8 | History capped at 2,000 tokens |
| `unit/test_citation_check.py` | 29 | Section citations checked against passages; case law removed |
| `unit/test_section_lookup.py` | 14 | Contents-list parsing and section lookup |
| `unit/test_research_service.py` | 11 | Title mapping, excerpt trimming |
| `unit/test_index_stats.py` | 3 | Library size reported from the index |
| `unit/test_summary_sections.py` | 6 | Clauses and risks parsed from the summary |
| `unit/test_contract_placeholders.py` | 10 | Unfilled-placeholder scan and compliance |
| `unit/test_ner.py` | 25 | Legal NER grouping and post-processing; the real model |
| `unit/test_db_unavailable.py` | 7 | One retry, then 503; other DB errors stay 500 |
| `unit/test_email_validator.py` | 5 | UT-EMAIL-001…002 |
| **Total** | **210** | |

---

## 4. Test cases — Authentication (Final Report Table 4.2)

| ID | Test | Expected | Result |
|---|---|---|---|
| UT-AUTH-001 | `test_ut_auth_001_successful_login_returns_user_and_tokens` | Access + refresh tokens, failed-count reset | ✅ |
| UT-AUTH-002 | `test_ut_auth_002_wrong_password_raises_invalid_credentials` | `InvalidCredentials`; failed count +1 | ✅ |
| UT-AUTH-003 | `test_ut_auth_003_nonexistent_user_raises_invalid_credentials` | `InvalidCredentials` (no hint whether the user exists) | ✅ |
| UT-AUTH-004 | `test_account_locks_after_five_failed_attempts` | Locked; `AccountLocked` even with the right password | ✅ |
| UT-AUTH-005 | `test_signup_creates_inactive_lawyer_pending_otp` | Inactive, unverified user with an OTP and a lawyer profile | ✅ |
| UT-AUTH-006 | `test_verify_otp_activates_account_without_auto_login` | Verified, OTP cleared, no tokens until login | ✅ |
| UT-AUTH-007 | `test_signup_rejects_duplicate_verified_email` | `AlreadyExists` (HTTP 409) | ✅ |
| UT-AUTH-008 | `test_refresh_issues_new_token_pair` | New access + refresh pair | ✅ |
| UT-AUTH-009 | `test_unverified_account_cannot_login` | `AccountLocked` with "verify your email" | ✅ |

## 5. Test cases — Case management (Final Report Table 4.3)

| ID | Test | Verifies | Result |
|---|---|---|---|
| UT-CASE-001 | `test_lawyer_creates_case_in_created_state` | A new case without a client is `created` | ✅ |
| UT-CASE-002 | `test_create_with_client_email_auto_assigns` | With `client_email` it becomes `assigned` and the client is linked | ✅ |
| UT-CASE-003 | `test_status_transitions_follow_state_machine` | Valid path; nothing leaves `closed` | ✅ |
| UT-CASE-004 | `test_client_cannot_create_case` | `NotAuthorized` for clients | ✅ |
| UT-CASE-005 | `test_client_only_sees_own_cases` | A client lists only their own cases | ✅ |

## 6. Test cases — OCR / text extraction (Final Report Table 4.4)

| ID | Test | Verifies | Result |
|---|---|---|---|
| UT-OCR-001a | `test_txt_extraction_returns_content` | TXT text returned verbatim | ✅ |
| UT-OCR-001b | `test_urdu_text_extraction` | Urdu UTF-8 preserved | ✅ |
| UT-OCR-002 | `test_unsupported_format_raises` | `.xyz` → `UnsupportedMediaType` | ✅ |
| UT-OCR-003 | `test_pdf_pipeline_returns_empty_for_missing_file` | Missing file → `""`, no crash | ✅ |

## 7. Test cases — Research helpers (Final Report Table 4.5)

| ID | Test | Verifies | Result |
|---|---|---|---|
| UT-RESEARCH-001a | `test_friendly_title_for_statutes` | Known source keys get readable titles | ✅ |
| UT-RESEARCH-001c | `test_friendly_title_unknown_source_falls_back_to_underscored` | Unknown keys fall back cleanly | ✅ |
| UT-RESEARCH-002a–c | `test_trim_*` | Excerpts start at a clean boundary; empty input handled | ✅ |

UT-RESEARCH-001b (Supreme Court judgment titles) was removed with its code
in October 2026: the library holds statutes only.

## 8. Test cases — Email validator

| ID | Test | Verifies | Result |
|---|---|---|---|
| UT-EMAIL-001a/b | `test_gmail_passes_fast_path`, `test_university_passes_fast_path` | Known domains skip the DNS lookup | ✅ |
| UT-EMAIL-002a–c | format tests | Missing `@`, no TLD, empty → rejected | ✅ |

---

## 9. End-to-end and UI results (quality pass, 2026-10-04)

**Over real HTTP with fresh accounts:** 113 checks, 107 passed. The 6 that
didn't were real findings, all fixed since:

| Finding | Fix |
|---|---|
| Upload path traversal | Generated storage names (`test_upload_paths.py`) |
| Rejected uploads left on disk | `test_upload_cleanup.py` |
| Pending signup overwrite | `test_signup_pending.py` |
| 422 for a taken email | Now 409 (`test_quality_pass_fixes.py`) |
| Urdu question got the English refusal | Urdu refusal (`test_quality_pass_fixes.py`) |
| A dead research endpoint | Removed |

The Urdu khula question itself is still refused. That's the known khula
retrieval gap, covered by the retrieval redesign.

What passed, by area:

| Area | Passed checks |
|---|---|
| Auth | Register, OTP, resend, wrong OTP, verify, cookies (HttpOnly, SameSite), `/me`, refresh, logout revokes both tokens, lockout after 5, reset unlocks, forgot-password gives the same answer for unknown emails |
| Cases | Create (assigned / created), role refusals, invalid type 422, timeline, assign errors (404/403), every valid and invalid transition, client read-only, outsider and student blocked, stats, 404/422 ids |
| Documents | Capabilities, TXT upload + attach, outsider blocked, image without OCR warns, text-less analyse is 422, .exe 415, 21 MB 413, client upload, sign-in required |
| Contracts | Missing fields 422 before any model call, client and student can't draft, draft → compliance → versions, client of the linked case can view, outsider blocked |
| Model features | Document analysis (summary + NER parties), research search ×3 and analysis, English chat in English with the short answer and valid `[n]`, off-topic refusal, private history. About 16k Groq tokens in all |

**UI:** 31 routes × 2 widths × 3 roles (62 page loads) showed no horizontal
overflow, no error alerts, and a heading on every page. After the theme
cleanup, every page renders in IBM Plex Sans on Paper, with no old fonts,
and unknown addresses show the 404 page.

---

## 10. Non-functional requirements

| Requirement | How it's checked | Result |
|---|---|---|
| Password hashing | `BCRYPT_ROUNDS=12` | ✅ |
| Auth cookies | `core/cookies.py`: HttpOnly, SameSite=Lax, Secure outside development (checked live) | ✅ |
| Session revocation | `test_logout_revocation.py`, plus a live check | ✅ |
| Account lockout | UT-AUTH-004, plus a live check | ✅ |
| Upload safety | `test_upload_paths.py`, `test_upload_cleanup.py` | ✅ |
| Scope restriction | Refusal without a model call (tests + live) | ✅ |
| English + Urdu | `test_chat_language.py`, `test_quality_pass_fixes.py`; live English check | ✅ (Urdu retrieval weaker) |
| Access control | Service-level checks; live cross-role checks | ✅ |
| Response time | Measured: API calls 3–8 s (Supabase latency), chat 9–27 s | ⚠️ Slower than the 3 s target |

---

## 11. Coverage (2026-10-04)

`pytest` with `pytest-cov`: **85% of lines** across `app/` (including the
test files themselves).

| Module | Coverage |
|---|---|
| `ai/citation_check.py` | 95% |
| `ai/ner.py` | 97% |
| `db/session.py` | 85% |
| `services/case_service.py` | 79% |
| `api/v1/documents.py` | 71% |
| `services/legal_chat_service.py` | 71% |
| `services/auth_service.py` | 64% |
| `services/research_service.py` | 61% |
| `services/contract_service.py` | 49% |
| `services/ocr_service.py` | 49% (Tesseract paths need OCR installed) |

## 12. Not tested

- **Frontend:** there are no automated frontend tests. UI is checked
  manually (§ 9).
- **Live model quality:** answer correctness isn't checked automatically.
  The retrieval evaluation and gold set are planned in
  `docs/retrieval_redesign.md`.
- **Not built, so not tested:** the Practice Simulator and Notifications.
- **Load testing:** not done.
