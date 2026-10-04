"""Only accepted uploads stay on disk. In the Oct 2026 quality pass the
upload handler wrote the file first and checked type and size afterwards,
so a rejected .exe and a 22 MB file were left in uploads/ with no document
row (R2). Type is now checked before writing, size while streaming, and the
file is removed if anything after the write fails."""

from types import SimpleNamespace

import pytest

from app.api.v1 import documents as documents_api
from app.core.config import settings
from app.core.security import hash_password
from app.models.document import Document
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture
def auth(client, db_session):
    db_session.add(User(email="cleanup@gmail.com", password_hash=hash_password("TestPass123"),
                        full_name="Cleanup", role=UserRole.LAWYER, is_active=True, is_verified=True))
    db_session.commit()
    r = client.post("/api/v1/auth/login", json={"email": "cleanup@gmail.com", "password": "TestPass123"})
    return {"Authorization": "Bearer " + r.json()["tokens"]["access_token"]}


@pytest.fixture
def upload_dir(monkeypatch, tmp_path):
    folder = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(folder))
    monkeypatch.setattr(settings, "DOC_MAX_SIZE_MB", 1)
    calls = {"extract": lambda path: "text"}

    class OCR:
        def extract(self, path):
            return calls["extract"](path)

    monkeypatch.setattr(documents_api, "get_ocr_service", lambda: OCR())
    return SimpleNamespace(folder=folder, calls=calls)


def _files(folder):
    return sorted(p.name for p in folder.iterdir()) if folder.exists() else []


def _upload(client, auth, name, data):
    return client.post("/api/v1/documents/upload", headers=auth, files={"file": (name, data, "application/octet-stream")})


@pytest.mark.parametrize("name", ["evil.exe", "script.js", "no_extension", "archive.zip"])
def test_unsupported_type_is_refused_before_anything_is_written(client, auth, upload_dir, name):
    r = _upload(client, auth, name, b"MZ" + b"0" * 100)
    assert r.status_code == 415
    assert _files(upload_dir.folder) == []


def test_oversized_upload_is_refused_and_its_partial_file_removed(client, auth, upload_dir, db_session):
    r = _upload(client, auth, "big.txt", b"a" * (2 * 1024 * 1024))  # limit set to 1 MB
    assert r.status_code == 413
    assert _files(upload_dir.folder) == []
    assert db_session.query(Document).count() == 0


def test_file_at_the_limit_is_kept(client, auth, upload_dir):
    r = _upload(client, auth, "edge.txt", b"a" * (1024 * 1024))
    assert r.status_code == 201, r.text
    assert len(_files(upload_dir.folder)) == 1


def test_failure_after_the_write_removes_the_file(client, auth, upload_dir, db_session):
    def broken(_path):
        raise RuntimeError("extractor crashed")

    upload_dir.calls["extract"] = broken
    with pytest.raises(RuntimeError):
        _upload(client, auth, "lease.txt", b"The tenant shall pay rent.")
    assert _files(upload_dir.folder) == []
    assert db_session.query(Document).count() == 0


def test_accepted_upload_keeps_exactly_one_file_with_a_row(client, auth, upload_dir, db_session):
    r = _upload(client, auth, "lease.txt", b"The tenant shall pay rent.")
    assert r.status_code == 201
    assert len(_files(upload_dir.folder)) == 1
    assert db_session.query(Document).count() == 1
