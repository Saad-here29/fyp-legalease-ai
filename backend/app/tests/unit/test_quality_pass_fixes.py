"""Fixes from the Oct 2026 quality pass that don't need their own file:
R5  the out-of-scope refusal is sent in the language of the question;
R8  signing up with an already-verified email is a 409, not a 422;
R4  the case timeline loads every actor's name in one query (was one per
    person). Offline: no model calls."""

import pytest
from sqlalchemy import event

from app.core.exceptions import AlreadyExists, ValidationFailed
from app.core.security import hash_password
from app.models.audit import ActivityLog
from app.models.document import Document
from app.models.enums import CaseType, DocumentType, FileType, UserRole
from app.models.user import User
from app.schemas.auth import SignupRequest
from app.schemas.cases import CaseCreate
from app.services import legal_chat_service as chat
from app.services.auth_service import AuthService
from app.services.case_service import CaseService


def _user(db, email, role, name):
    u = User(email=email, password_hash=hash_password("x"), full_name=name, role=role,
             is_active=True, is_verified=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ---- R5 -------------------------------------------------------------------

@pytest.fixture
def no_passages(monkeypatch):
    """Retrieval finds nothing, so the chat refuses without a model call."""
    class NoModel:
        def chat(self, *a, **k):
            raise AssertionError("the model must not be called for a refusal")

    monkeypatch.setattr(chat, "get_ai_client", lambda: NoModel())
    monkeypatch.setattr(chat, "rewrite_for_search", lambda q: q)
    monkeypatch.setattr(chat.embeddings, "build_or_load", lambda *a: 1)
    monkeypatch.setattr(chat.embeddings, "search", lambda *a, **k: [])


@pytest.mark.parametrize("question, lang", [
    ("Give me a recipe for chocolate cake.", "en"),
    ("مجھے چاکلیٹ کیک کی ترکیب بتائیں۔", "ur"),
])
def test_refusal_is_in_the_language_of_the_question(db_session, no_passages, question, lang):
    asker = _user(db_session, "asker@gmail.com", UserRole.CLIENT, "Asker")
    reply = chat.LegalChatService(db_session).send(asker, question)
    assert reply["response"] == chat.OUT_OF_SCOPE_REFUSAL[lang]
    assert reply["citations"] == []


def test_urdu_refusal_is_written_in_urdu():
    text = chat.OUT_OF_SCOPE_REFUSAL["ur"]
    assert sum("؀" <= ch <= "ۿ" for ch in text) > len(text) // 2
    assert chat.fixed_reply(chat.INDEX_NOT_READY, "ur") == chat.INDEX_NOT_READY["ur"]
    assert chat.fixed_reply(chat.INDEX_NOT_READY, "fr") == chat.INDEX_NOT_READY["en"]


# ---- R8 -------------------------------------------------------------------

def test_signup_with_a_verified_email_is_a_409(db_session):
    _user(db_session, "taken@gmail.com", UserRole.CLIENT, "Taken")
    with pytest.raises(AlreadyExists) as exc:
        AuthService(db_session).signup(SignupRequest(email="taken@gmail.com", password="StrongPass123",
                                                     full_name="Second", role=UserRole.CLIENT))
    assert exc.value.status_code == 409
    assert isinstance(exc.value, ValidationFailed)  # older callers still catch it


def test_signup_409_over_http(client, db_session):
    _user(db_session, "taken2@gmail.com", UserRole.CLIENT, "Taken")
    r = client.post("/api/v1/auth/register", json={"email": "taken2@gmail.com", "password": "StrongPass123",
                                                    "full_name": "Second", "role": "client"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "already_exists"


# ---- R4: timeline N+1 -------------------------------------------------------

def test_timeline_loads_actor_names_in_one_query(db_session, engine):
    lawyer = _user(db_session, "tl.lawyer@gmail.com", UserRole.LAWYER, "Lawyer One")
    client = _user(db_session, "tl.client@gmail.com", UserRole.CLIENT, "Client One")
    others = [_user(db_session, f"tl.helper{i}@gmail.com", UserRole.LAWYER, f"Helper {i}") for i in range(4)]
    svc = CaseService(db_session)
    case = svc.create(CaseCreate(title="Timeline", case_type=CaseType.DIVORCE, client_email=client.email), lawyer)
    for i, who in enumerate(others):  # activity by four more people, plus two uploaders
        db_session.add(ActivityLog(user_id=who.id, action="RESEARCH_SAVED_TO_CASE", entity_type="case",
                                   entity_id=case.id, new_values={"title": f"Note {i}"}))
    for who in (lawyer, client):
        db_session.add(Document(case_id=case.id, uploaded_by_id=who.id, file_name="a.txt", storage_path="x",
                                sha256_hash="0" * 64, file_type=FileType.TXT, file_size_bytes=1,
                                document_type=DocumentType.OTHER))
    db_session.commit()
    db_session.expire_all()  # nothing cached: count real queries

    statements = []
    listener = lambda conn, cur, stmt, *a: statements.append(stmt)  # noqa: E731
    event.listen(engine, "before_cursor_execute", listener)
    try:
        entries = svc.timeline(case.id, lawyer)
    finally:
        event.remove(engine, "before_cursor_execute", listener)

    user_selects = [s for s in statements if "FROM users" in s and "users.full_name" in s and " IN " in s]
    assert len(user_selects) == 1
    actors = {e.actor_name for e in entries}
    assert {"Lawyer One", "Client One", "Helper 0", "Helper 3"} <= actors
    # no per-person lookups: at most the access check reads users besides the batch
    per_person = [s for s in statements if "FROM users" in s and " IN " not in s]
    assert len(per_person) <= 1
