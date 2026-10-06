"""Generic parsing driven by a source's config (scripts/scraping/sources.json).

A source config describes how to walk from listing pages to documents:
  listing_urls        pages that list documents
  item_xpath          on a listing page: one element per document (usually <a>)
  title_xpath         (optional) relative to the item: where the title text is
  item_is_pdf         true if the item link points straight at the PDF
  pdf_xpath           otherwise, on the document page: the PDF link (href/src)
No per-site code unless a site needs it.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import unquote, urljoin

from lxml import html as lxml_html


@dataclass
class Item:
    title: str
    url: str        # the document's page (or the PDF itself when item_is_pdf)


def _text(el) -> str:
    return " ".join((el.text_content() if hasattr(el, "text_content") else str(el)).split())


def parse_listing(content: bytes, base_url: str, cfg: dict) -> list[Item]:
    doc = lxml_html.fromstring(content)
    items: list[Item] = []
    seen: set[str] = set()
    for el in doc.xpath(cfg["item_xpath"]):
        href = el.get("href")
        if not href:
            continue
        url = urljoin(base_url, href.strip())
        if url in seen:
            continue
        seen.add(url)
        title = ""
        if cfg.get("title_xpath"):
            found = el.xpath(cfg["title_xpath"])
            title = _text(found[0]) if found else ""
        title = title or _text(el)
        items.append(Item(title=title, url=url))
    return items


def find_pdf_url(content: bytes, base_url: str, cfg: dict) -> str | None:
    """The PDF link on a document page. Viewer iframes like
    ".../ViewerJS/#../pdffiles/x.pdf" are resolved to the PDF itself."""
    doc = lxml_html.fromstring(content)
    for val in doc.xpath(cfg["pdf_xpath"]):
        raw = str(val).strip()
        if "#" in raw and ".pdf" in raw.split("#", 1)[1].lower():
            viewer, frag = raw.split("#", 1)
            return urljoin(urljoin(base_url, viewer), frag)
        if ".pdf" in raw.lower():
            return urljoin(base_url, raw)
    return None


def pdf_text(content: bytes) -> str:
    """Text of a PDF (PyMuPDF). Empty for scanned PDFs with no text layer."""
    import pymupdf
    with pymupdf.open(stream=content, filetype="pdf") as d:
        return "\n".join(p.get_text() for p in d).strip()


def normalise_text(text: str) -> str:
    """For hashing: whitespace and watermark-style noise don't count as a change."""
    return re.sub(r"\s+", " ", text or "").strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalise_text(text).encode("utf-8")).hexdigest()


_LEAD = re.compile(r"^\s*(?:\d+\s+)?(?:the\s+)?", re.I)


def normalise_title(title: str) -> str:
    """'1 THE LAW RE FORMS ORDINANCE, 1972' and 'Law Reforms Ordinance, 1972'
    compare equal: drop a leading number and 'the', keep letters and digits."""
    t = _LEAD.sub("", unquote(title or "")).lower()
    return re.sub(r"[^a-z0-9]", "", t)
