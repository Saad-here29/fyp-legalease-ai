"""OCR module — Tesseract-based text extraction for scanned PDFs and images.

Runs inside the Celery worker (app.tasks.ocr_tasks) so the API thread is never
blocked. Targets FR-OCR-02: >=90% accuracy on English print, >=80% on Urdu.
"""
