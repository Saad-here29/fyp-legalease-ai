"""POST /documents/{id}/analyze must refuse a document with no extractable
text — a clear 422, and no model call (found in the Sept 2026 pre-demo
audit: a scanned PDF with OCR unavailable was sent to the LLM, which
returned a meaningless "summary")."""

import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.api.v1 import documents as documents_api
from app.core.exceptions import ValidationFailed
from app.core.security import hash_password
from app.models.document import Document
from app.models.enums import DocumentType, FileType, UserRole
from app.models.user import User


@pytest.fixture
def owner(db_session):
    u = User(
        email="uploader@gmail.com",
        password_hash=hash_password("x"),
        full_name="Uploader",
        role=UserRole.LAWYER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def _document(db_session, owner, text):
    doc = Document(
        uploaded_by_id=owner.id,
        file_name="scanned.pdf",
        storage_path="uploads/does-not-exist.pdf",
        sha256_hash="0" * 64,
        file_type=FileType.PDF,
        file_size_bytes=1234,
        document_type=DocumentType.OTHER,
        extracted_text=text,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def endpoint_db(engine, monkeypatch):
    """Point the endpoint's own SessionLocal at the test database, make OCR
    find nothing, and fail the test if the model is ever called."""
    monkeypatch.setattr(documents_api, "SessionLocal", sessionmaker(bind=engine))

    class NoText:
        def extract(self, _path):
            return ""

    monkeypatch.setattr(documents_api, "get_ocr_service", lambda: NoText())

    def model_must_not_be_called():
        raise AssertionError("the model was called for a document with no text")

    monkeypatch.setattr(documents_api, "get_ai_client", model_must_not_be_called)


@pytest.mark.parametrize("text", [None, "", "   \n\t "])
def test_analyze_refuses_document_without_text(db_session, owner, endpoint_db, text):
    doc = _document(db_session, owner, text)
    # The commit in _document() expires `owner`; reload it, as a real request's
    # freshly loaded user would be, before the endpoint closes the session.
    db_session.refresh(owner)
    with pytest.raises(ValidationFailed) as exc:
        documents_api.analyze_document(doc.id, owner, db_session)
    assert exc.value.status_code == 422
    assert "no extractable text" in exc.value.message


def test_analyze_missing_document_is_404_not_a_model_call(db_session, owner, endpoint_db):
    from app.core.exceptions import NotFound

    with pytest.raises(NotFound):
        documents_api.analyze_document(uuid.uuid4(), owner, db_session)
