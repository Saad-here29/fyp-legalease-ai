"""LegalEase AI — Pakistani Legal Corpus Builder.

End-to-end pipeline that turns the raw documents in `ai-services/data/raw/`
into a queryable FAISS semantic index used by the AI Chat and Legal Research
modules.

Pipeline (implements Final Report Algorithm 4 — "Build the Legal Library Index"):
    1. Unzip `archive.zip` (Supreme Court of Pakistan judgments) into
       `ai-services/data/raw/judgments/` if not already extracted.
    2. Read every PDF in `ai-services/data/raw/` using PyMuPDF (fitz).
    3. Read every .txt in `ai-services/data/raw/judgments/`.
    4. Skip empty / unreadable files. Clean whitespace artefacts.
    5. Chunk each document into 800-char chunks with 100-char overlap.
    6. Tag every chunk with metadata: source, source_type, chunk_id, text.
    7. Embed all chunks via `paraphrase-multilingual-MiniLM-L12-v2`
       (384-dim) in batches of 64.
    8. Persist a FAISS `IndexFlatIP` (cosine via L2-normalised vectors) +
       sidecar metadata JSON to the paths declared in `backend/.env`.

Run from the project root:

    cd backend
    .\venv\Scripts\python ..\ai-services\corpus_builder\build_corpus.py

Or from anywhere using the venv directly. The script is idempotent: re-running
overwrites the index. To force a clean rebuild, delete the existing index +
metadata files first.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

# Force UTF-8 stdout so unicode glyphs (✓, ✗, …) print on Windows consoles
# whose default codepage is cp1252.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

# ----- Resolve project paths -----------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
RAW_DIR = ROOT / "ai-services" / "data" / "raw"
JUDGMENTS_DIR = RAW_DIR / "judgments"
ARCHIVE_PATH = RAW_DIR / "archive.zip"


def _load_dotenv(path: Path) -> dict[str, str]:
    """Tiny .env reader — no external deps. Stops on first equals sign and
    strips surrounding quotes."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = _load_dotenv(BACKEND_DIR / ".env")

EMBEDDING_MODEL = ENV.get(
    "EMBEDDING_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2"
)
EMBEDDING_DIM = int(ENV.get("EMBEDDING_DIMENSION", "384"))
CHUNK_SIZE = int(ENV.get("RAG_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(ENV.get("RAG_CHUNK_OVERLAP", "100"))

# FAISS paths in .env are written relative to the backend/ working directory.
# Resolve them against BACKEND_DIR so this script can be run from anywhere.
def _resolve_backend_path(p: str) -> Path:
    path = Path(p)
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


FAISS_INDEX_PATH = _resolve_backend_path(
    ENV.get("FAISS_INDEX_PATH", "./storage/faiss/legal_corpus.faiss")
)
FAISS_METADATA_PATH = _resolve_backend_path(
    ENV.get("FAISS_METADATA_PATH", "./storage/faiss/legal_corpus_meta.json")
)


# ----- Friendly source name map -------------------------------------------

# Maps raw filename → human-readable display name. Unknown filenames keep
# their stem, which is fine for citations.
SOURCE_NAME_OVERRIDES: dict[str, str] = {
    "Pakistan Penal Code.pdf": "Pakistan_Penal_Code",
    "Pakistan_Penal_Code.pdf": "Pakistan_Penal_Code",
    "Code_of_criminal_procedure_1898.pdf": "Code_of_Criminal_Procedure_1898",
    # The administrator*.pdf names below were identified by inspecting the
    # documents shipped with this project: Family Courts Act 1964, Muslim
    # Family Laws Ordinance 1961, and the Zainab Alert Act 2020.
    "administratorb8b9391ce414b63eac5c68627f6704ef.pdf": "Family_Courts_Act_1964",
    "administratoreecaf3b490e2d43d2e3b50c0c068b5d7.pdf": "Muslim_Family_Laws_Ordinance_1961",
    "administratorf08eaec19066a65a1b82cb4ad49feb4d.pdf": "Zainab_Alert_Act_2020",
    "1333523681_951.pdf": "Pakistani_Legal_Reference",
}


def _display_source(filename: str) -> str:
    return SOURCE_NAME_OVERRIDES.get(filename, Path(filename).stem)


# ----- Step 1: extract archive --------------------------------------------

def ensure_judgments_extracted() -> int:
    """Unzip archive.zip into JUDGMENTS_DIR if not already extracted.
    Returns the number of .txt files found in the destination."""
    JUDGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(JUDGMENTS_DIR.rglob("*.txt"))
    if existing:
        print(f"[1/8] Judgments already extracted: {len(existing)} .txt files")
        return len(existing)

    if not ARCHIVE_PATH.exists():
        print(f"[1/8] WARNING: {ARCHIVE_PATH} not found — skipping judgments")
        return 0

    print(f"[1/8] Extracting {ARCHIVE_PATH.name}...")
    with zipfile.ZipFile(ARCHIVE_PATH) as zf:
        zf.extractall(JUDGMENTS_DIR)
    txt_files = list(JUDGMENTS_DIR.rglob("*.txt"))
    print(f"[1/8] Extracted {len(txt_files)} judgment .txt files")
    return len(txt_files)


# ----- Step 2-4: read + clean + chunk -------------------------------------

_WHITESPACE_RE = re.compile(r"[\r\n\t\f\v]+|\s{2,}")


def clean_text(text: str) -> str:
    """Collapse \\r\\n artefacts and runs of whitespace into single spaces."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    r"""Sliding-window chunking with character-level overlap.

    Final Report Algorithm 4 specifies 800-token chunks with 100-token overlap.
    We approximate at the character level (token boundaries differ across
    languages; characters give a stable, deterministic chunking that's good
    enough for retrieval recall)."""
    if not text:
        return []
    if size <= overlap:
        raise ValueError("chunk size must exceed overlap")

    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(text), step):
        chunk = text[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(text):
            break
    return chunks


def read_pdf_text(path: Path) -> str:
    """Extract text from a PDF using PyMuPDF. Returns '' on failure."""
    import fitz  # PyMuPDF — heavy import, kept local
    try:
        doc = fitz.open(str(path))
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
    except Exception as e:  # noqa: BLE001
        print(f"   ! PDF read failed for {path.name}: {e}")
        return ""


def read_txt(path: Path) -> str:
    """Read a UTF-8 text file, fall back to latin-1 on decode errors."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")
    except Exception as e:  # noqa: BLE001
        print(f"   ! TXT read failed for {path.name}: {e}")
        return ""


def collect_documents() -> list[dict]:
    """Walk raw/ and raw/judgments/ and return one dict per source document
    with keys: filename, source_type, raw_text."""
    docs: list[dict] = []

    # PDFs (statutes / reference)
    pdfs = sorted(p for p in RAW_DIR.glob("*.pdf"))
    for pdf in pdfs:
        if pdf.stat().st_size == 0:
            continue
        raw = read_pdf_text(pdf)
        if not raw or len(raw.strip()) < 50:
            print(f"   ! Skipping empty/unreadable PDF: {pdf.name}")
            continue
        docs.append(
            {
                "filename": pdf.name,
                "source_type": "statute",
                "raw_text": raw,
            }
        )

    # Judgments (.txt extracted from archive.zip)
    if JUDGMENTS_DIR.exists():
        txts = sorted(JUDGMENTS_DIR.rglob("*.txt"))
        for txt in txts:
            if txt.stat().st_size == 0:
                continue
            raw = read_txt(txt)
            if not raw or len(raw.strip()) < 50:
                continue
            docs.append(
                {
                    "filename": txt.name,
                    "source_type": "judgment",
                    "raw_text": raw,
                }
            )

    return docs


# ----- Step 5-7: chunk + embed + index ------------------------------------

def build_chunks(docs: list[dict]) -> list[dict]:
    """Convert raw documents into chunked metadata records ready for embedding."""
    records: list[dict] = []
    for doc in docs:
        cleaned = clean_text(doc["raw_text"])
        if not cleaned:
            continue
        source_name = _display_source(doc["filename"])
        for i, chunk in enumerate(chunk_text(cleaned)):
            records.append(
                {
                    "source": source_name,
                    "source_type": doc["source_type"],
                    "chunk_id": i,
                    "text": chunk,
                }
            )
    return records


def embed_and_index(records: list[dict]) -> None:
    """Embed all chunks, build a FAISS index, persist index + metadata."""
    if not records:
        print("[7/8] No records to embed — aborting.")
        return

    # Imports kept local — they're the heavy bits (~5s cold start)
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer

    print(f"[5/8] Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"[6/8] Embedding {len(records)} chunks (batch_size=64)...")
    texts = [r["text"] for r in records]

    batch_size = 64
    vectors_chunks: list = []
    t0 = time.perf_counter()
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        batch_vectors = model.encode(
            batch,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # L2-normalise so IndexFlatIP == cosine
        )
        vectors_chunks.append(batch_vectors.astype(np.float32))
        done = min(start + batch_size, len(texts))
        if done % 100 < batch_size or done == len(texts):
            elapsed = time.perf_counter() - t0
            rate = done / elapsed if elapsed > 0 else 0
            print(f"   ... embedded {done}/{len(texts)} ({rate:.1f} chunks/s)")

    vectors = np.vstack(vectors_chunks)
    assert vectors.shape == (len(records), EMBEDDING_DIM), (
        f"Expected vectors shape ({len(records)}, {EMBEDDING_DIM}) "
        f"but got {vectors.shape}. Check EMBEDDING_DIMENSION in .env."
    )

    print(f"[7/8] Building FAISS IndexFlatIP ({vectors.shape[0]} × {vectors.shape[1]})")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    print(f"   ✓ Wrote {FAISS_INDEX_PATH}")

    # Metadata sidecar — parallel array to FAISS row ids
    FAISS_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FAISS_METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    print(f"   ✓ Wrote {FAISS_METADATA_PATH}")


# ----- Main ----------------------------------------------------------------

def main() -> int:
    print("=" * 60)
    print("LegalEase AI — Pakistani Legal Corpus Builder")
    print("=" * 60)

    ensure_judgments_extracted()

    print("[2/8] Scanning raw documents...")
    docs = collect_documents()
    if not docs:
        print("ERROR: No usable documents found in ai-services/data/raw/")
        return 1
    statute_count = sum(1 for d in docs if d["source_type"] == "statute")
    judgment_count = sum(1 for d in docs if d["source_type"] == "judgment")
    print(f"   ✓ {len(docs)} documents ({statute_count} statutes, {judgment_count} judgments)")

    print(f"[3/8] Chunking @ {CHUNK_SIZE} chars / {CHUNK_OVERLAP} overlap...")
    records = build_chunks(docs)
    print(f"   ✓ Produced {len(records)} chunks")

    print("[4/8] Skipping empty files & cleaning whitespace... done")
    embed_and_index(records)

    print("=" * 60)
    print(f"[8/8] ✓ Indexed {len(records)} chunks from {len(docs)} documents")
    print(f"      Index:    {FAISS_INDEX_PATH}")
    print(f"      Metadata: {FAISS_METADATA_PATH}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
