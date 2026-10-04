"""Uploads are stored under a generated name; the client's filename is kept
only for display. In the Oct 2026 audit an upload named "../../escape.txt"
was stored as "uploads/<hex>_../../escape.txt" and landed outside its
generated name; each extra "../" climbs one more folder."""

import re
from pathlib import Path

import pytest

from app.api.v1 import documents as documents_api
from app.api.v1.documents import _display_name, _storage_path
from app.core.config import settings
from app.core.exceptions import ValidationFailed
from app.core.security import hash_password
from app.models.document import Document
from app.models.enums import UserRole
from app.models.user import User

GENERATED = re.compile(r"^[0-9a-f]{32}\.[a-z0-9]{1,10}$")


@pytest.mark.parametrize("raw, shown", [
    ("../../escape.txt", "escape.txt"),
    ("..\\..\\escape.txt", "escape.txt"),
    ("/etc/passwd.txt", "passwd.txt"),
    ("C:\\Windows\\System32\\drivers.txt", "drivers.txt"),
    ("\\\\server\\share\\note.txt", "note.txt"),
    ("na\x00me.txt", "name.txt"),
    ("tab\there.txt", "tabhere.txt"),
    ("..", "upload"),
    ("", "upload"),
    (None, "upload"),
    ("report.final.docx", "report.final.docx"),
])
def test_display_name_keeps_only_a_safe_last_component(raw, shown):
    assert _display_name(raw) == shown


def test_very_long_name_is_cut_to_the_column_and_keeps_its_extension():
    shown = _display_name("x" * 400 + ".pdf")
    assert len(shown) == 255
    assert shown.endswith(".pdf")


def test_storage_path_is_generated_and_inside_the_folder(tmp_path):
    p = _storage_path(tmp_path, "txt")
    assert p.parent == tmp_path.resolve()
    assert GENERATED.match(p.name)


def test_storage_path_refuses_anything_that_would_leave_the_folder(tmp_path):
    with pytest.raises(ValidationFailed):
        _storage_path(tmp_path, "txt/../../../x")


# ---- over HTTP ---------------------------------------------------------------

@pytest.fixture
def auth(client, db_session):
    db_session.add(User(email="paths@gmail.com", password_hash=hash_password("TestPass123"),
                        full_name="Paths", role=UserRole.LAWYER, is_active=True, is_verified=True))
    db_session.commit()
    r = client.post("/api/v1/auth/login", json={"email": "paths@gmail.com", "password": "TestPass123"})
    return {"Authorization": "Bearer " + r.json()["tokens"]["access_token"]}


@pytest.fixture
def upload_dir(monkeypatch, tmp_path):
    folder = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(folder))

    class TextOCR:
        def extract(self, path):
            return Path(path).read_text(encoding="utf-8", errors="replace")

    monkeypatch.setattr(documents_api, "get_ocr_service", lambda: TextOCR())
    return folder


@pytest.mark.parametrize("name", [
    "../../escape.txt",
    "..\\..\\escape.txt",
    "../../../../../../tmp/escape.txt",
    "/etc/escape.txt",
    "C:\\Windows\\escape.txt",
    "x" * 300 + ".txt",
])
def test_upload_never_writes_outside_the_upload_folder(client, auth, upload_dir, db_session, name):
    r = client.post("/api/v1/documents/upload", headers=auth,
                    files={"file": (name, b"The tenant shall pay rent.", "text/plain")})
    assert r.status_code == 201, r.text
    body = r.json()
    assert "/" not in body["filename"] and "\\" not in body["filename"]
    assert len(body["filename"]) <= 255

    stored = Path(db_session.get(Document, __import__("uuid").UUID(body["id"])).storage_path)
    assert stored.parent == upload_dir.resolve()
    assert GENERATED.match(stored.name)
    assert stored.read_bytes() == b"The tenant shall pay rent."
    # nothing was written anywhere else under the test's temp folder
    others = [p for p in upload_dir.parent.rglob("*") if p.is_file() and p.parent != upload_dir]
    assert others == []


def test_null_byte_in_name_never_reaches_storage(client, auth, upload_dir):
    # The HTTP client percent-encodes a NUL ("lease%00.txt"); a raw NUL is
    # covered by test_display_name_keeps_only_a_safe_last_component.
    r = client.post("/api/v1/documents/upload", headers=auth,
                    files={"file": ("lease\x00.txt", b"text", "text/plain")})
    assert r.status_code == 201, r.text
    assert "\x00" not in r.json()["filename"]
    assert [GENERATED.match(p.name) is not None for p in upload_dir.iterdir()] == [True]
