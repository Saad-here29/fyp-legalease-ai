# API Reference

The live OpenAPI schema is at `http://localhost:8000/docs` (Swagger) and
`/redoc`. **They are served only when `APP_ENV` is `development`, `dev` or
`local`.** The endpoint tables below were generated from that schema
(October 2026).

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

- **How you get tokens:** `POST /auth/login` returns an access token
  (60 minutes) and a refresh token (7 days). It also sets them as
  **HttpOnly** cookies, `le_access` and `le_refresh` (SameSite=Lax; Secure
  outside development).
- **Using them:** browsers send the cookies automatically. Other clients
  send the access token as a header:

  ```
  Authorization: Bearer <access_token>
  ```
- **Refreshing:** `POST /auth/refresh` rotates the pair. It reads the
  refresh cookie, or `{"refresh_token": "..."}` in the body.
- **Signing out:** `POST /auth/logout` increments the user's token version,
  so **every** access and refresh token issued before it stops working, on
  all devices.
- **Roles are enforced in the services**, not only by route: lawyers,
  clients and students see different data, and a disallowed action returns
  403 (or 404 where existence shouldn't be revealed).

## Errors

Every error has the same shape. `hint` says what to do next:

```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Invalid email or password.",
    "hint": "Double-check your email and password."
  }
}
```

Request-validation errors from FastAPI itself (wrong field types, missing
fields) use FastAPI's standard `{"detail": [...]}` shape, with status 422.

## Status codes

| Code | When | `error.code` |
|---|---|---|
| 200 / 201 / 202 | OK; created; signup accepted (code sent) | |
| 401 | Not signed in, bad or expired token, or a token revoked by logout | `not_authenticated`, `invalid_credentials` |
| 403 | Signed in, but the role or owner may not do this | `not_authorized` |
| 404 | Not found (or not visible to you) | `not_found` |
| 409 | Email, licence, CNIC or university ID already registered; illegal case-status change | `already_exists`, `illegal_state_transition` |
| 413 | Upload over 20 MB | `file_too_large` |
| 415 | Unsupported file type | `unsupported_media_type` |
| 422 | Invalid input, e.g. analysing a document with no text | `validation_failed` |
| 423 | Account locked (5 failed logins) or email not yet verified | `account_locked` |
| 503 | Database unreachable after one retry; AI provider unavailable | `db_unavailable`, `ai_unavailable` |

## Endpoints

The "Sign-in" column says whether a valid access token is needed.

### auth

| Method | Path | Purpose | Sign-in |
|---|---|---|---|
| POST | `/auth/signup` | Alias of /register for backward compatibility | no |
| POST | `/auth/register` | Validate email + create pending account + send OTP | no |
| POST | `/auth/resend-otp` | Re-send the verification code | no |
| POST | `/auth/verify-otp` | Alias of /verify-email | no |
| POST | `/auth/verify-email` | Verify the OTP and activate the account. User is then asked to sign in. | no |
| POST | `/auth/login` | Authenticate and issue JWT pair (UC-01) | no |
| POST | `/auth/refresh` | Rotate the access + refresh token pair | no |
| POST | `/auth/logout` | Logout — revoke all tokens and clear auth cookies | yes |
| GET | `/auth/me` | Return the authenticated user's profile | yes |
| POST | `/auth/forgot-password` | Email a 6-digit password-reset code | no |
| POST | `/auth/reset-password` | Verify the reset OTP and set a new password | no |

### cases

| Method | Path | Purpose | Sign-in |
|---|---|---|---|
| GET | `/cases` | List cases visible to me | yes |
| POST | `/cases` | Create a new case (UC-02) — lawyers only. Provide client_email to auto-link an existing client. | yes |
| GET | `/cases/stats` | My case stats — total / active / in-hearing / closed | yes |
| GET | `/cases/{case_id}` | Fetch a single case with lawyer/client names and doc count | yes |
| GET | `/cases/{case_id}/timeline` | Activity timeline for a case — visible to lawyer and client | yes |
| GET | `/cases/{case_id}/documents` | List documents attached to this case | yes |
| POST | `/cases/{case_id}/assign-client` | Assign a registered client to a case by email (UC-03) | yes |
| PATCH | `/cases/{case_id}/status` | Transition a case to a new status (FR-CM06) | yes |
| POST | `/cases/{case_id}/research` | Save a Legal Research result as a note on this case | yes |

### documents

| Method | Path | Purpose | Sign-in |
|---|---|---|---|
| GET | `/documents/capabilities` | Which file types can have their text extracted on this server | yes |
| POST | `/documents/upload` | Upload a legal document, run OCR, and persist metadata (UC-05) | yes |
| POST | `/documents/{document_id}/attach` | Link an existing uploaded document to a case (lawyers only) | yes |
| GET | `/documents/{document_id}` | Fetch a single document's metadata + extracted text | yes |
| POST | `/documents/{document_id}/analyze` | LLM summary + clauses/risks, and legal NER (parties, dates, references) | yes |

### chat

| Method | Path | Purpose | Sign-in |
|---|---|---|---|
| GET | `/chat/sessions` | List my chat sessions | yes |
| GET | `/chat/sessions/{session_id}/history` | Full message history for a chat session | yes |
| POST | `/chat/message` | Ask the AI legal assistant (UC-04) — RAG-grounded, Pakistani-law-only scope | yes |

### research

| Method | Path | Purpose | Sign-in |
|---|---|---|---|
| GET | `/research/stats` | Size of the searchable library (passages and source statutes) | no |
| POST | `/research/search` | Semantic search over the legal library (UC-06) | yes |
| POST | `/research/analyze` | Run a structured legal breakdown (Issue / Findings / Judgment / Legal Basis / Relevance) on a passage | yes |

### contracts

| Method | Path | Purpose | Sign-in |
|---|---|---|---|
| GET | `/contracts` | List contracts visible to me | yes |
| POST | `/contracts/draft` | Draft a new contract from a template + filled fields — lawyers only | yes |
| GET | `/contracts/{contract_id}` | Fetch a contract with its latest version | yes |
| GET | `/contracts/{contract_id}/versions` | Full version history for a contract | yes |
| POST | `/contracts/{contract_id}/check-compliance` | Run the required-clauses checklist against a version's text — deterministic, no LLM call | yes |

### system

| Method | Path | Purpose | Sign-in |
|---|---|---|---|
| GET | `/` | Root | no |
| GET | `/health` | Health | no |

### Notes

- **`/auth/signup` and `/auth/verify-otp`** are aliases of `/auth/register`
  and `/auth/verify-email`. The frontend uses the aliases.
- **`/auth/register` for a still-unverified email** only re-sends a code.
  It never changes that pending account's password, name or role.
- **`/documents/upload`:**
  - accepts PDF, DOCX and TXT, plus PNG/JPG when OCR is installed (see
    `/documents/capabilities`);
  - files are stored under generated names;
  - if no text could be extracted, the response's `extraction_warning` says
    why.
- **`/chat/message` and `/research/search`** each make one small model call
  to rewrite the query. `/chat/message`, `/research/analyze`,
  `/documents/{id}/analyze` and `/contracts/draft` call the language model
  (Groq); everything else doesn't.
