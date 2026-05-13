"""OCR + document text extraction service.

Pipeline (Final Report § 4 / Algorithm 3):
    - PDF with selectable text → PyPDF2 direct extraction (fast, lossless)
    - PDF without selectable text → pdf2image → Tesseract per page
    - PNG / JPG → Tesseract directly
    - DOCX → python-docx
    - TXT → read as utf-8

Returns extracted text. The caller persists it on the Document row.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import UnsupportedMediaType
from app.core.logging import logger


def _configure_tesseract() -> bool:
    """Wire pytesseract to the local tesseract.exe. Returns True if available."""
    try:
        import pytesseract
    except ImportError:
        logger.warning("pytesseract not installed — OCR disabled")
        return False

    cmd = (settings.TESSERACT_CMD or "").strip()
    if cmd and os.path.exists(cmd):
        pytesseract.pytesseract.tesseract_cmd = cmd
        return True
    # Fall back to PATH lookup
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001
        logger.warning(
            "Tesseract executable not found. Set TESSERACT_CMD in .env to enable "
            "OCR for scanned documents."
        )
        return False


_TESS_OK = _configure_tesseract()


class OCRService:
    """Extracts text from a saved file path. Synchronous; small docs only.
    Larger docs should be queued via Celery in production."""

    def extract(self, path: Path, mime_type: str | None = None) -> str:
        suffix = path.suffix.lower().lstrip(".")
        if suffix == "pdf":
            return self._extract_pdf(path)
        if suffix == "docx":
            return self._extract_docx(path)
        if suffix == "txt":
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix in ("png", "jpg", "jpeg"):
            return self._extract_image(path)
        raise UnsupportedMediaType(
            message=f"OCR does not support .{suffix} files.",
            hint="Allowed: PDF, DOCX, TXT, PNG, JPG.",
        )

    # ----- PDF -----------------------------------------------------------

    def _extract_pdf(self, path: Path) -> str:
        """PDF text extraction pipeline (Final Report Algorithm 3):
            1. PyMuPDF (fitz) — primary. Best engine; handles most digital PDFs.
            2. PyPDF2 — fallback for the rare PDF that fitz chokes on.
            3. Tesseract via pdf2image — last resort for SCANNED PDFs (image-only).
        """
        # 1. PyMuPDF — primary. Used by the corpus builder, proven on every
        # Pakistani statute + judgment in this project.
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            try:
                text = "\n".join(page.get_text() for page in doc).strip()
            finally:
                doc.close()
            if len(text) >= 50:
                return text
        except Exception as e:  # noqa: BLE001
            logger.warning(f"PyMuPDF extraction failed for {path}: {e}")

        # 2. PyPDF2 fallback
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(path))
            text = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
            if len(text) >= 50:
                return text
        except Exception as e:  # noqa: BLE001
            logger.warning(f"PyPDF2 extraction failed for {path}: {e}")

        # 3. Tesseract OCR for scanned (image-only) PDFs
        if not _TESS_OK:
            logger.warning(
                f"PDF {path.name} has no extractable text — likely a scanned "
                "image. Install Tesseract OCR + Poppler to enable OCR."
            )
            return ""

        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError as e:
            logger.warning(f"OCR dependencies missing: {e}")
            return ""

        try:
            pages = convert_from_path(str(path))
        except Exception as e:  # noqa: BLE001
            logger.warning(
                f"pdf2image failed (Poppler missing?): {e}. "
                "Install Poppler and add to PATH to OCR scanned PDFs."
            )
            return ""

        chunks: list[str] = []
        for img in pages:
            chunks.append(
                pytesseract.image_to_string(img, lang=settings.TESSERACT_LANG)
            )
        return "\n".join(chunks).strip()

    # ----- DOCX ----------------------------------------------------------

    def _extract_docx(self, path: Path) -> str:
        try:
            import docx  # python-docx
        except ImportError:
            logger.warning("python-docx not installed")
            return ""
        d = docx.Document(str(path))
        return "\n".join(p.text for p in d.paragraphs)

    # ----- Images --------------------------------------------------------

    def _extract_image(self, path: Path) -> str:
        if not _TESS_OK:
            return ""
        import pytesseract
        from PIL import Image
        with Image.open(path) as img:
            return pytesseract.image_to_string(
                img, lang=settings.TESSERACT_LANG
            ).strip()


_singleton: OCRService | None = None


def get_ocr_service() -> OCRService:
    global _singleton
    if _singleton is None:
        _singleton = OCRService()
    return _singleton
