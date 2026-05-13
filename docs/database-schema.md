# Database Schema

> Full ERD is in `Documents and Reports/ERD.pdf`. This file is a quick
> reference and a record of design decisions.

## Engine

PostgreSQL 16 with SQLAlchemy 2.x ORM and Alembic migrations.

## Conventions

- All primary keys are UUID (`gen_random_uuid()`).
- All tables have `created_at` and `updated_at` timestamps (TimestampMixin).
- Enums are stored as PostgreSQL native ENUM types.
- AI outputs (clauses, risk flags, rubric criteria) are JSONB.
- File contents are NEVER stored in PostgreSQL — only `storage_path` + `sha256_hash`.

## Tables (per Final Report § 3.2)

### Identity
- `users` — UUID PK, email UNIQUE, password_hash, phone, role ENUM, is_active
- `lawyers` — extends users with bar license details
- `clients` — extends users with address
- `students` — extends users with university details

### Case domain
- `cases` — title, description, case_type ENUM, status ENUM, assigned_lawyer_id, client_id
- `case_participants` — case_id, user_id, role_in_case (LAWYER/CLIENT/WITNESS/JUDGE)
- `documents` — case_id, file_name, storage_path, sha256_hash, file_type, summary_text, extracted_text
- `document_analysis` — document_id, summary, identified_clauses JSONB, risk_flags JSONB, confidence_score
- `deadlines` — case_id, title, due_date, reminder_date, status ENUM

### AI domain
- `legal_corpus` — title, number, jurisdiction, content, embedding_vector
- `chat_sessions` — user_id, case_id, started_at, ended_at, total_messages, summary
- `chat_messages` — session_id, sender_type ENUM, content, response_time_ms

### Practice domain
- `simulation_scenarios` — title, difficulty ENUM, content JSONB
- `simulation_attempts` — student_id, scenario_id, started_at, completed_at, student_response, feedback_report, score, rubric_criteria JSONB

### Cross-cutting
- `notifications` — user_id, notif_type, message, is_read, scheduled_at
- `activity_logs` — user_id, action, entity_type, entity_id, old_values JSONB, new_values JSONB, ip_address, user_agent

## State Machines

### Case status

```
CREATED → ASSIGNED → IN_PROGRESS → HEARING_SCHEDULED ⇄ IN_PROGRESS
                                                     ↘ CLOSED
                                  → CLOSED
```

Invalid transitions raise HTTP 409 (`illegal_state_transition`).

## Migrations

```bash
# After editing models:
alembic revision --autogenerate -m "describe what changed"

# Apply:
alembic upgrade head

# Roll back:
alembic downgrade -1
```
