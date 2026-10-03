"""Uploads say when no text came out. In the Oct 2026 audit PNG, JPG and
scanned-PDF uploads silently stored 0 characters (Tesseract is not
installed) and the upload strip still advertised PNG/JPG."""

import pytest

from app.api.v1 import documents as documents_api
from app.core.config import settings
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture
def auth(client, db_session):
    db_session.add(User(email="uploads@gmail.com", password_hash=hash_password("TestPass123"),
                        full_name="Uploader", role=UserRole.LAWYER, is_active=True, is_verified=True))
    db_session.commit()
    r = client.post("/api/v1/auth/login", json={"email": "uploads@gmail.com", "password": "TestPass123"})
    return {"Authorization": "Bearer " + r.json()["tokens"]["access_token"]}


@pytest.fixture
def ocr(monkeypatch, tmp_path):
    """Store uploads in a temp dir; let each test set the OCR state and the
    text the extractor returns."""
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    state = {"available": False, "text": ""}

    class FakeOCR:
        def extract(self, _path):
            return state["text"]

    monkeypatch.setattr(documents_api, "get_ocr_service", lambda: FakeOCR())
    monkeypatch.setattr(documents_api, "ocr_available", lambda: state["available"])
    return state


def _upload(client, auth, name):
    r = client.post("/api/v1/documents/upload", headers=auth, files={"file": (name, b"bytes", "application/octet-stream")})
    assert r.status_code == 201, r.text
    return r.json()


def test_text_upload_has_no_warning(client, auth, ocr):
    ocr["text"] = "The tenant shall pay rent monthly."
    body = _upload(client, auth, "lease.txt")
    assert body["text_extracted"] is True
    assert body["extraction_warning"] is None


def test_image_without_ocr_says_ocr_is_not_installed(client, auth, ocr):
    body = _upload(client, auth, "photo.png")
    assert body["text_extracted"] is False
    assert "OCR" in body["extraction_warning"] and "image" in body["extraction_warning"]


def test_scanned_pdf_without_ocr_says_so(client, auth, ocr):
    body = _upload(client, auth, "scan.pdf")
    assert body["text_extracted"] is False
    assert "scanned" in body["extraction_warning"]


@pytest.mark.parametrize("text", ["", "  \n "])
def test_empty_file_with_ocr_still_gets_a_warning(client, auth, ocr, text):
    ocr["available"], ocr["text"] = True, text
    body = _upload(client, auth, "blank.png")
    assert body["text_extracted"] is False
    assert body["extraction_warning"] == "No text could be extracted from this file, so it cannot be analysed."


def test_capabilities_omit_images_without_ocr(client, auth, ocr):
    r = client.get("/api/v1/documents/capabilities", headers=auth)
    assert r.status_code == 200
    assert r.json() == {"ocr_available": False, "accepted_types": ["PDF", "DOCX", "TXT"]}


def test_capabilities_list_images_with_ocr(client, auth, ocr):
    ocr["available"] = True
    assert client.get("/api/v1/documents/capabilities", headers=auth).json()["accepted_types"] == \
        ["PDF", "DOCX", "TXT", "PNG", "JPG"]


def test_capabilities_require_sign_in(client):
    assert client.get("/api/v1/documents/capabilities").status_code == 401
