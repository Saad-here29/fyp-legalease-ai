"""Unit tests for OCRService — covers UT-OCR-001 from Final Report § 4.3
Table 4.4. Tests are deliberately format-focused (TXT + small PDF) so they
do not require Tesseract or Poppler to be installed in CI.
"""

import tempfile
from pathlib import Path

import pytest

from app.core.exceptions import UnsupportedMediaType
from app.services.ocr_service import OCRService


@pytest.fixture
def ocr():
    return OCRService()


# ============================================================
# UT-OCR-001a: TXT extraction returns the file content verbatim
# ============================================================
def test_txt_extraction_returns_content(ocr):
    content = "Section 302 PPC: Punishment for qatl-i-amd is death as qisas."
    with tempfile.NamedTemporaryFile(
        suffix=".txt", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(content)
        path = Path(f.name)
    try:
        text = ocr.extract(path)
        assert content in text
    finally:
        path.unlink(missing_ok=True)


# ============================================================
# UT-OCR-001b: Unicode (Urdu) text extraction preserves the script
# ============================================================
def test_urdu_text_extraction(ocr):
    content = "خلع کا قانون: عورت کو شوہر سے علیحدگی کا حق حاصل ہے۔"
    with tempfile.NamedTemporaryFile(
        suffix=".txt", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(content)
        path = Path(f.name)
    try:
        text = ocr.extract(path)
        assert "خلع" in text
        assert "علیحدگی" in text
    finally:
        path.unlink(missing_ok=True)


# ============================================================
# UT-OCR-002: unsupported file type raises with a clear hint
# ============================================================
def test_unsupported_format_raises(ocr):
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        path = Path(f.name)
    try:
        with pytest.raises(UnsupportedMediaType):
            ocr.extract(path)
    finally:
        path.unlink(missing_ok=True)


# ============================================================
# UT-OCR-003: missing file returns empty (no crash)
# ============================================================
def test_pdf_pipeline_returns_empty_for_missing_file(ocr):
    # Non-existent path — fitz / PyPDF2 will both fail and we should
    # gracefully return "" rather than crash the request handler.
    text = ocr.extract(Path("/this/does/not/exist.pdf"))
    assert text == ""
