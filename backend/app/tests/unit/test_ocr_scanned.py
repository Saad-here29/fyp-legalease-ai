"""Scanned PDFs without Poppler (pages rendered by PyMuPDF), and the Urdu
re-read. The last test runs real Tesseract and is skipped where it isn't
installed."""

import sys

import pymupdf
import pytest
from PIL import Image

from app.services import ocr_service
from app.services.ocr_service import OCRService, mostly_urdu


def _image_only_pdf(path, lines):
    """A PDF whose pages are pictures of text: no selectable text at all."""
    src = pymupdf.open()
    page = src.new_page(width=595, height=842)
    for i, line in enumerate(lines):
        page.insert_text((60, 90 + 28 * i), line, fontsize=16)
    png = page.get_pixmap(dpi=200).tobytes("png")
    src.close()
    out = pymupdf.open()
    out.new_page(width=595, height=842).insert_image(pymupdf.Rect(0, 0, 595, 842), stream=png)
    out.save(str(path))
    out.close()


@pytest.mark.parametrize("text, urdu", [
    ("مسلم عائلی قوانین آرڈیننس، ۱۹۶۱", True),
    ("دفعہ ۷۔ طلاق Section 7", True),
    ("SUPREME COURT OF PAKISTAN (Appellate Jurisdiction)", False),
    ("Section 7 talaq دفعہ", False),
    ("", False),
    ("1961 — 7.", False),
])
def test_mostly_urdu(text, urdu):
    assert mostly_urdu(text) is urdu


class _FakeTesseract:
    def __init__(self, first):
        self.first = first
        self.calls = []

    def image_to_string(self, img, lang):
        self.calls.append(lang)
        return self.first if len(self.calls) == 1 else "urdu-only reading"


@pytest.mark.parametrize("first, expected_calls, result", [
    ("مسلم عائلی Gul قوانین wold", ["eng+urd", "urd"], "urdu-only reading"),
    ("SUPREME COURT OF PAKISTAN", ["eng+urd"], "SUPREME COURT OF PAKISTAN"),
])
def test_urdu_page_is_read_again_with_urdu_alone(monkeypatch, first, expected_calls, result):
    fake = _FakeTesseract(first)
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    monkeypatch.setattr(ocr_service.settings, "TESSERACT_LANG", "eng+urd")
    assert ocr_service._ocr_image(object()) == result
    assert fake.calls == expected_calls


def test_no_reread_when_urdu_is_the_only_language(monkeypatch):
    fake = _FakeTesseract("مسلم عائلی قوانین")
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    monkeypatch.setattr(ocr_service.settings, "TESSERACT_LANG", "urd")
    ocr_service._ocr_image(object())
    assert fake.calls == ["urd"]


def test_scanned_pdf_pages_render_without_poppler(tmp_path, monkeypatch):
    # pdf2image (which needs Poppler) must not be needed.
    monkeypatch.setitem(sys.modules, "pdf2image", None)
    pdf = tmp_path / "scan.pdf"
    _image_only_pdf(pdf, ["Restitution of conjugal rights"])
    pages = ocr_service._render_pdf_pages(pdf)
    assert len(pages) == 1 and isinstance(pages[0], Image.Image)
    assert pages[0].width >= 2400  # rendered at OCR_DPI (300), A4 width ~2480 px


@pytest.mark.skipif(not ocr_service.ocr_available(), reason="Tesseract not installed")
def test_real_ocr_of_an_image_only_pdf(tmp_path):
    pdf = tmp_path / "scan.pdf"
    _image_only_pdf(pdf, ["SCHEDULE", "4. Restitution of conjugal rights.", "8. Dowry."])
    with pymupdf.open(str(pdf)) as d:
        assert d[0].get_text().strip() == ""  # really image-only
    text = OCRService().extract(pdf)
    assert "Restitution of conjugal rights" in text
    assert "Dowry" in text
