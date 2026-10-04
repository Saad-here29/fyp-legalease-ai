# Database Schema

The ORM models in `backend/app/models/` and the migrations in
`backend/alembic/versions/` are the source of truth. This page was generated
from those models (October 2026). The original design ERD is
`docs/reports/ERD.png`. It predates some changes listed below.

## Engine and conventions

- **Database:** PostgreSQL (Supabase in development), SQLAlchemy 2.x,
  Alembic migrations. Tests use in-memory SQLite.
- **Keys:** UUID primary keys on every table.
- **Timestamps:** `created_at` / `updated_at` on most tables. The
  `activity_logs`, `chat_messages` and `contract_versions` tables only add
  rows, so they have `created_at` only.
- **Enums:** stored as PostgreSQL ENUM types.
- **JSON:** JSONB for AI output and audit diffs.
- **Files:** never stored in the database, only `storage_path` (a generated
  name under `UPLOAD_DIR`) and `sha256_hash`.

## Tables (14)

### Identity
| Table | Columns |
|---|---|
| `users` | id, email (unique), password_hash, full_name, phone, role (lawyer / client / student), is_active, is_verified, otp, otp_expires_at, failed_login_count, **token_version** (increased at logout to revoke all tokens) |
| `lawyers` | id, user_id → users (unique), bar_license_no (unique), specialization, bar_year, bar_council |
| `clients` | id, user_id → users (unique), address, cnic (unique) |
| `students` | id, user_id → users (unique), university_id (unique), university_name, current_year |

Lawyer and student profile fields are optional
(migration `16e7f2d6727c`).

### Cases and documents
| Table | Columns |
|---|---|
| `cases` | id, title, description, case_type, status, court_code, filing_date, assigned_lawyer_id → users, client_id → users |
| `case_participants` | id, case_id → cases, user_id → users, role_in_case |
| `documents` | id, case_id → cases (nullable: uploaded before being attached), uploaded_by_id → users, file_name (display name), storage_path, sha256_hash, file_type, file_size_bytes, document_type, extracted_text, summary_text |
| `document_analysis` | id, document_id → documents (unique), summary, identified_clauses, risk_flags, extracted_entities (NER output), document_classification |

### AI chat
| Table | Columns |
|---|---|
| `chat_sessions` | id, user_id → users, case_id → cases, title, summary, language_hint, total_messages, started_at, ended_at |
| `chat_messages` | id, session_id → chat_sessions, sender_type (user / ai), content, citations (JSONB), response_time_ms, detected_language |

### Contracts
| Table | Columns |
|---|---|
| `contracts` | id, case_id → cases, created_by_id → users, contract_type (nda / employment / service_agreement), title, fields (JSONB) |
| `contract_versions` | id, contract_id → contracts, version_number, content, compliance_result (JSONB: clause results, unfilled placeholders, checked_at) |

### Audit and reference
| Table | Columns |
|---|---|
| `activity_logs` | id, user_id → users, action, entity_type, entity_id, old_values, new_values, ip_address, user_agent. The case timeline is built from these rows |
| `legal_corpus` | id, title, section_number, jurisdiction, document_type, court, year, content, chunk_index, token_count, indexed_at, source_url. **Legacy:** nothing reads it any more. The searchable library is the FAISS index on disk |

**Not in the schema** (in the original design, never built): deadlines,
practice-simulator scenarios and attempts, notifications. Embeddings live in
the FAISS file, not in a database column.

## Case status machine

Allowed moves (`_ALLOWED_TRANSITIONS` in `services/case_service.py`):

| From | To |
|---|---|
| `created` | `assigned`, `in_progress`, `closed` |
| `assigned` | `in_progress`, `hearing_scheduled`, `closed` |
| `in_progress` | `hearing_scheduled`, `closed` |
| `hearing_scheduled` | `in_progress`, `closed` |
| `closed` | — (final) |

- **Illegal moves** return 409 (`illegal_state_transition`).
- **Linking a client** to a `created` case moves it to `assigned`
  automatically, and the move is logged on the timeline.
- **Closed cases** accept no new documents in the UI.

## Migrations

| Revision | Change |
|---|---|
| `2b7806a018fc` | Initial schema |
| `16e7f2d6727c` | Lawyer and student role fields made optional |
| `aab3307a5ca9` | Contracts and contract versions |
| `c41e7d2b9a10` | `document_analysis.extracted_entities` |
| `d5a91c3e7f20` | `users.token_version` |

```bash
cd backend
alembic upgrade head                                  # apply
alembic revision --autogenerate -m "what changed"     # after editing models
alembic downgrade -1                                  # roll back one
```
