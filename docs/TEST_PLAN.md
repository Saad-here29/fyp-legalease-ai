# LegalEase AI — Test Plan

**Project:** LegalEase AI — AI-Powered Online Lawyer Management and Legal Assistance Platform
**Iteration:** FYP-1 (committed scope: Auth, Case Management, AI Chat, AI Research, OCR)
**Reference:** Final Report § 4.3 (Test Strategy) — Tables 4.2 / 4.3 / 4.4 / 4.5

---

## 1. Objectives

This test plan verifies that the LegalEase AI platform meets the functional and non-functional requirements defined in the SRS for iteration-1 + iteration-2 modules. It covers:

| Goal | How verified |
|---|---|
| Correctness of authentication, RBAC, and the case lifecycle state machine | Unit tests against `AuthService`, `CaseService` (in-memory SQLite, isolated per test) |
| OCR pipeline behaviour across file formats | Unit tests against `OCRService` with temp files |
| Research / retrieval helpers (title mapping, chunk trimming) | Pure-Python unit tests against `ResearchService` helpers |
| Email validation (MX-record gate) | Unit tests using `ALWAYS_VALID_DOMAINS` to keep tests offline |
| End-to-end API surface (health, swagger, smoke) | Functional curl smoke tests against the live FastAPI server |
| Provider failover (Groq → OpenAI → Gemini) | Live smoke verified during demo prep |

---

## 2. Test Levels

### 2.1 Unit Tests (`backend/app/tests/unit/`)

Run with:

```bash
cd backend
./venv/Scripts/python -m pytest app/tests --no-cov -q
```

All tests use the `db_session` fixture from `conftest.py` — a fresh in-memory SQLite engine per test for full isolation.

### 2.2 Integration / Smoke Tests (`backend/app/tests/test_health.py` + curl)

Health endpoint covered automatically. Live integration sanity checked via curl against a running backend:

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"smoke@gmail.com","password":"TestPass123!","full_name":"Smoke","role":"CLIENT"}'
```

### 2.3 Manual UI/UX Tests

Performed by the team in Chrome / Edge against http://localhost:5173 after `npm run dev`. Coverage matrix in § 5 below.

---

## 3. Test Cases — Authentication (Final Report Table 4.2)

Implemented in [`backend/app/tests/unit/test_auth_service.py`](backend/app/tests/unit/test_auth_service.py).

| ID | Test name | Inputs | Expected | Result |
|---|---|---|---|---|
| UT-AUTH-001 | `test_ut_auth_001_successful_login_returns_user_and_tokens` | Email + correct password on verified user | `LoginResponse` with `access_token`, `refresh_token`, role intact, failed-count reset | ✅ Pass |
| UT-AUTH-002 | `test_ut_auth_002_wrong_password_raises_invalid_credentials` | Email + wrong password | Raises `InvalidCredentials`; `failed_login_count` incremented | ✅ Pass |
| UT-AUTH-003 | `test_ut_auth_003_nonexistent_user_raises_invalid_credentials` | Email that doesn't exist | Raises `InvalidCredentials` (no info leak) | ✅ Pass |
| UT-AUTH-004 | `test_account_locks_after_five_failed_attempts` | 5× wrong password | Account `is_active=False`, raises `AccountLocked` even with right password | ✅ Pass |
| UT-AUTH-005 | `test_signup_creates_inactive_lawyer_pending_otp` | Valid lawyer signup payload | Returns `{email, message}`; User row has `is_verified=False`, `otp` set, Lawyer profile attached | ✅ Pass |
| UT-AUTH-006 | `test_verify_otp_activates_account_without_auto_login` | Signup → fetch OTP → `verify_otp(email, otp)` | Returns confirmation dict (no tokens); user becomes `is_verified=True`, OTP cleared; subsequent `login()` issues tokens | ✅ Pass |
| UT-AUTH-007 | `test_signup_rejects_duplicate_verified_email` | Signup with an already-verified email | Raises `ValidationFailed` | ✅ Pass |
| UT-AUTH-008 | `test_refresh_issues_new_token_pair` | Valid refresh token | Returns a new access + refresh pair | ✅ Pass |
| UT-AUTH-009 | `test_unverified_account_cannot_login` | Right password but `is_verified=False` | Raises `AccountLocked` with "verify your email" hint | ✅ Pass |

---

## 4. Test Cases — Case Management (Final Report Table 4.3)

Implemented in [`backend/app/tests/unit/test_case_service.py`](backend/app/tests/unit/test_case_service.py).

| ID | Test name | Verifies | Result |
|---|---|---|---|
| UT-CASE-001 | `test_lawyer_creates_case_in_created_state` | Lawyer can create a case; defaults to `CREATED` when no client supplied | ✅ Pass |
| UT-CASE-002 | `test_create_with_client_email_auto_assigns` | Case created with `client_email` auto-promotes to `ASSIGNED` and links client | ✅ Pass |
| UT-CASE-003 | `test_status_transitions_follow_state_machine` | ASSIGNED → IN_PROGRESS → HEARING_SCHEDULED → CLOSED valid; further transition from CLOSED raises `IllegalStateTransition` | ✅ Pass |
| UT-CASE-004 | `test_client_cannot_create_case` | RBAC — Client role calling `create()` raises `NotAuthorized` | ✅ Pass |
| UT-CASE-005 | `test_client_only_sees_own_cases` | `list_for_user(client)` returns only that client's cases (not other clients') | ✅ Pass |

---

## 5. Test Cases — OCR (Final Report Table 4.4)

Implemented in [`backend/app/tests/unit/test_ocr_service.py`](backend/app/tests/unit/test_ocr_service.py).

| ID | Test name | Verifies | Result |
|---|---|---|---|
| UT-OCR-001a | `test_txt_extraction_returns_content` | TXT pipeline returns full content verbatim (no Tesseract dependency) | ✅ Pass |
| UT-OCR-001b | `test_urdu_text_extraction` | Urdu UTF-8 text preserved through extraction (script + diacritics) | ✅ Pass |
| UT-OCR-002 | `test_unsupported_format_raises` | `.xyz` raises `UnsupportedMediaType` with clear hint | ✅ Pass |
| UT-OCR-003 | `test_pdf_pipeline_returns_empty_for_missing_file` | Non-existent file path returns `""` (no crash) | ✅ Pass |

---

## 6. Test Cases — Research Helpers (Final Report Table 4.5)

Implemented in [`backend/app/tests/unit/test_research_service.py`](backend/app/tests/unit/test_research_service.py).

| ID | Test name | Verifies | Result |
|---|---|---|---|
| UT-RESEARCH-001a | `test_friendly_title_for_statutes` | `Pakistan_Penal_Code` → "Pakistan Penal Code 1860" and similar mappings | ✅ Pass |
| UT-RESEARCH-001b | `test_friendly_title_for_supreme_court_judgments` | `C.A_supreme (2665)` → "Supreme Court of Pakistan — Civil Appeal No. 2665" | ✅ Pass |
| UT-RESEARCH-001c | `test_friendly_title_unknown_source_falls_back_to_underscored` | Unknown source falls back to underscore-replaced title | ✅ Pass |
| UT-RESEARCH-002a | `test_trim_advances_past_leading_fragment` | Mid-word leading fragments (`", a, where..."`) trimmed to the next clean sentence | ✅ Pass |
| UT-RESEARCH-002b | `test_trim_handles_already_clean_text` | Text already starting with a capital is left untouched (no over-trim) | ✅ Pass |
| UT-RESEARCH-002c | `test_trim_handles_empty_input` | Empty string returns empty string | ✅ Pass |

---

## 7. Test Cases — Email validator

Implemented in [`backend/app/tests/unit/test_email_validator.py`](backend/app/tests/unit/test_email_validator.py).

| ID | Test name | Verifies | Result |
|---|---|---|---|
| UT-EMAIL-001a | `test_gmail_passes_fast_path` | `@gmail.com` short-circuits MX lookup via `ALWAYS_VALID_DOMAINS` | ✅ Pass |
| UT-EMAIL-001b | `test_university_passes_fast_path` | `@fast.edu.pk` short-circuits MX lookup | ✅ Pass |
| UT-EMAIL-002a | `test_missing_at_sign_rejected` | `"notanemail"` raises `EmailValidationError` | ✅ Pass |
| UT-EMAIL-002b | `test_no_tld_rejected` | `"user@localhost"` raises (no TLD) | ✅ Pass |
| UT-EMAIL-002c | `test_empty_string_rejected` | `""` raises | ✅ Pass |

---

## 8. Test Cases — System health

Implemented in [`backend/app/tests/test_health.py`](backend/app/tests/test_health.py).

| ID | Test | Verifies | Result |
|---|---|---|---|
| INT-HEALTH-001 | `/health` returns 200 + `{"status":"ok"}` | App starts, routes register, JSON shape stable | ✅ Pass |

---

## 9. Manual UI/UX coverage matrix

Performed before each demo. Each row is a single end-to-end click-through.

| Flow | Role | Steps | Pass/Fail |
|---|---|---|---|
| Signup → OTP → Login → Dashboard | Lawyer | Fill signup form with valid `@gmail.com` → OTP page with 10:00 countdown → fetch code from `[dev] OTP` log → verify → redirect to `/login` with email prefilled → enter password → land on `/lawyer/dashboard` | ✅ |
| Signup with fake domain | Any | Use `@nonexistentdomain-zzz.com` → 422 with "This email domain does not appear to exist" | ✅ |
| Create case + assign client by email | Lawyer | Cases tab → New case → fill title + case_type + client_email of a registered Client → submit → case appears with status ASSIGNED | ✅ |
| Case state machine | Lawyer | Open a case → Advance to IN_PROGRESS → HEARING_SCHEDULED → CLOSED, see each event on timeline | ✅ |
| OCR upload | Lawyer | Documents tab → upload `Pakistan Penal Code.pdf` → see extracted text + char count | ✅ |
| OCR save-to-case | Lawyer | After upload → "Save to a case" panel → select a case → Save → case timeline shows DOCUMENT event | ✅ |
| AI Chat — in scope | Any | Ask "What is the penalty for child abuse under the Zainab Alert Act?" → Llama-3.3 answer with source badges in ~2s | ✅ |
| AI Chat — out of scope | Any | Ask "Best pizza recipe?" → returns the spec refusal text in <500ms, no LLM call | ✅ |
| AI Chat — Urdu | Any | Ask `خلع کا قانون کیا ہے؟` → Urdu answer with sources | ✅ |
| Legal Research search | Any | Search "child custody Pakistan" → 10 ranked results with relevance %, friendly source titles | ✅ |
| Research detail + auto-analysis | Any | Click "Read more" → analysis auto-fires in 2-4s → Issue / Findings / Judgment / Legal Basis / Relevance cards rendered | ✅ |
| Research save-to-case | Lawyer | On detail page → "Save to a case" dropdown → pick case → entry appears on case timeline as NOTE | ✅ |
| RBAC bounce | Lawyer logged in | Navigate to `/client/dashboard` → ProtectedRoute redirects to `/lawyer/dashboard` (own dashboard) | ✅ |
| Logout | Any | Sidebar → Sign out → cookies cleared → bounced to landing/login | ✅ |

---

## 10. Non-functional requirements verified

| NFR | Verification method | Result |
|---|---|---|
| Response time < 3s | Chat: AI bubble timestamp shows "Generated in Xs" — typically 0.8-2.5s. Research search: <500ms (no LLM). Verified live | ✅ Met |
| Auth: bcrypt cost ≥ 10 | `settings.BCRYPT_ROUNDS=10` (configurable to 12 in prod); verified in code | ✅ Met |
| Auth: HttpOnly cookies | `backend/app/core/cookies.py` sets `httponly=True, samesite=lax, secure=is_prod` | ✅ Met |
| Auth: account lockout | UT-AUTH-004 passes — 5 failed attempts → `is_active=False`, `AccountLocked` thrown | ✅ Met |
| Auth: OTP expiry | OTP rows carry `otp_expires_at = now + 10min`; UT-AUTH-006 verifies the activation path | ✅ Met |
| Scope restriction | Manual test: "Best pizza recipe?" returns the exact spec refusal — `chat_service.py` short-circuits when no chunk passes `RAG_SIMILARITY_THRESHOLD` | ✅ Met |
| Multilingual EN+UR | UT-OCR-001b verifies Urdu UTF-8 round-trip; manual chat test confirms Urdu RAG | ✅ Met |
| RBAC | UT-CASE-004 + UT-CASE-005 verify role-gating in service layer | ✅ Met |
| Audit logging | Every privileged action writes `activity_logs` row — verified by inspecting `case timeline` events | ✅ Met |

---

## 11. Coverage snapshot

```
$ python -m pytest app/tests --no-cov -q
...............................                                          [100%]
31 passed
```

Module-level coverage (most recent run with `pytest-cov`):

| Module | Coverage | Notes |
|---|---|---|
| `app/services/auth_service.py` | ~60% | Hot path covered; password-reset edge cases pending |
| `app/services/case_service.py` | ~55% | Lifecycle + RBAC covered; save_research_to_case pending |
| `app/services/research_service.py` | ~55% | Helpers fully covered; FAISS integration is smoke-tested |
| `app/services/ocr_service.py` | ~45% | Pipeline fan-out covered; Tesseract path tested manually (env-dependent) |
| `app/utils/email_validator.py` | ~65% | Fast-path + format errors covered |
| **Overall** | **~59%** | Tests prioritise business logic over framework boilerplate |

---

## 12. Out-of-scope for iteration 2

The following are intentionally not yet tested because the corresponding modules ship in iteration 3:

- Practice Simulator
- Contract Drafting & Compliance
- Notifications (in-app + email reminders)
- Hearings sub-module beyond the case status flag

Each of these renders a Coming Soon page in production and has no logic to test yet.

---

## 13. How to reproduce these results

```bash
# Backend tests
cd backend
./venv/Scripts/python -m pytest app/tests --no-cov -q

# With coverage
./venv/Scripts/python -m pytest app/tests --cov=app --cov-report=term-missing

# Live smoke check
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok"}
```

Full demo walkthrough (manual UI tests) is documented in [DEMO_BRIEF.md](../DEMO_BRIEF.md) § 9.
