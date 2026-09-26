"""TOC-guided section lookup for statute retrieval.

Problem (measured 2026-09-26): the corpus is cut into fixed
800-character windows that ignore section boundaries, so a section's text
is split across chunks that also carry the neighbouring sections, and the
embedding barely registers a section number. For "legal restrictions on
polygamy" the best chunk holding MFLO s.6 ranked 42nd (score 0.609, below
the 0.65 cut-off), while the statute's table-of-contents chunk — statute
name plus every section title — ranked 3rd. The model then answered from
the contents list: "the library doesn't contain this".

Demoting TOC chunks, taking more chunks from the same statute, or fusing a
BM25 keyword ranking all failed to surface the section text in simulation.
What works: treat a retrieved TOC chunk as a map of its statute. Parse its
"6. Polygamy" entries, pick the ones the question points at (an explicit
section number, or a title word the question uses), and fetch the chunk
that carries that section's heading plus the one after it. Some statutes
are indexed twice (once under an OCR-damaged title); all copies are
searched, and the first copy with the heading is used.

The proper long-term fix is section-based chunking (data/README.md, "Future
work — statute corpus and retrieval").
"""

from __future__ import annotations

import re
from functools import lru_cache

MAX_SECTIONS = 2        # TOC entries followed per question
MAX_EXTRA_CHUNKS = 4    # passages added in total (2 sections x 2 chunks)

_ENTRY = re.compile(r"(?:^|\s)(\d{1,3}[A-Z]?)\s?\.\s+([A-Z][^.]{2,80}?)\s?\.")
# Inside a chunk already known to be a contents list, some statutes number
# entries without a dot ("1 Short title and extent. 2 Grounds for decree ...").
_TOC_ENTRY = re.compile(r"(?:^|\s)(\d{1,3}[A-Z]?)\s?\.?\s+([A-Z][^.]{2,80}?)\s?\.")
_SECTION_REF = re.compile(r"\b(?:sections?|secs?\.?|s\.)\s*(\d{1,3}[A-Z]?)\b", re.I)
_WORD = re.compile(r"[a-z]{5,}")
# Words that appear in questions/rewrites and in many titles without
# identifying a section.
_STOP = {
    "section", "sections", "under", "which", "about", "their", "there", "other",
    "procedure", "provisions", "ordinance", "muslim", "family", "pakistan",
    "pakistani", "legal", "what", "where", "short", "title", "extent",
    "application", "commencement", "definition", "definitions", "rules",
    "power", "powers", "omitted", "amendment", "repeal", "savings",
}


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower()).removeprefix("the")


def is_toc(text: str) -> bool:
    """A contents list: an explicit CONTENTS / SECTIONS: header, or many
    short numbered headings with almost no running prose."""
    if re.search(r"\bCONTENTS\b|\bSECTIONS\s*:", text):
        return True
    heads = _ENTRY.findall(text)
    prose = len(re.findall(r"\b(shall|may|means|is|are)\b", text))
    return len(heads) >= 8 and prose <= 3


def toc_entries(text: str) -> list[tuple[str, str]]:
    """Numbered entries of a contents list. The dotless pattern is only a
    fallback — applied to dotted lists it also reads page headers ("Page 1
    of 7 THE MUSLIM FAMILY LAWS ...") as entries. Numbers right after "of"
    and all-capitals titles are page headers either way, so they're skipped."""
    def clean(pattern):
        out = []
        for m in pattern.finditer(text):
            number, title = m.group(1), m.group(2).strip()
            if text[max(0, m.start(1) - 3):m.start(1)].strip().lower() == "of":
                continue
            letters = re.sub(r"[^A-Za-z]", "", title)
            if letters.isupper() and len(letters) > 3:
                continue
            out.append((number, title))
        return out
    entries = clean(_ENTRY)
    return entries if len(entries) >= 3 else clean(_TOC_ENTRY)


def pick_entries(question: str, entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Entries the user's OWN question points at: explicit section numbers
    first, then entries whose title shares a word stem (first 6 letters) with
    a question word — "polygamous" ~ "Polygamy".

    Nothing is taken from the search rewrite. It invents section numbers
    (seen on the eval set: "Companies Act 2017 (Section 2)", "Transfer of
    Property Act Section 62") and adds statute names whose words collide with
    unrelated section titles ("Transfer of Property Act" ~ "Certain transfers
    void")."""
    numbers = {n.upper() for n in _SECTION_REF.findall(question)}
    by_number = [e for e in entries if e[0].upper() in numbers]
    if by_number:
        return by_number[:MAX_SECTIONS]
    words = {w[:6] for w in _WORD.findall(question.lower()) if w not in _STOP}
    by_title = [
        e for e in entries
        if words & {w[:6] for w in _WORD.findall(e[1].lower()) if w not in _STOP}
    ]
    return by_title[:MAX_SECTIONS]


def _heading_pattern(number: str, title: str) -> re.Pattern:
    """CSV chunks: "Section 7 — Talaq"; PDF chunks: "7. Talaq.—", which OCR
    sometimes splits inside the word ("7. Tala q.—") — so letters of the
    title's first word may have a space between them."""
    first = re.sub(r"[^A-Za-z]", "", title.split()[0]) if title.split() else ""
    word = r"\s?".join(map(re.escape, first)) if first else ""
    num = re.escape(number)
    return re.compile(
        rf"\bSection\s+{num}\s*[—–-]|(?<![\d.]){num}\s?\.\s*{word}",
        re.I,
    )


@lru_cache(maxsize=1)
def _chunks_by_statute(meta_id: int, n: int) -> dict[str, list[int]]:
    # keyed on the metadata list's identity + length so a reloaded index
    # gets a fresh map
    from app.ai import embeddings
    out: dict[str, list[int]] = {}
    for i, m in enumerate(embeddings._META):
        out.setdefault(squash(embeddings.record_source(m)), []).append(i)
    return out


def section_passages(question: str, retrieved: list[dict]) -> list[dict]:
    """Extra passages for the sections a retrieved TOC chunk maps the
    question to. Each returned record is an index metadata dict plus
    `relevance` (the TOC chunk's score) and `via_toc` (its section)."""
    from app.ai import embeddings

    meta = embeddings._META
    if not meta:
        return []
    statutes = _chunks_by_statute(id(meta), len(meta))
    have = {embeddings.record_text(r) for r in retrieved}
    extra: list[dict] = []
    for toc in [r for r in retrieved if is_toc(embeddings.record_text(r))]:
        key = squash(embeddings.record_source(toc))
        ids = statutes.get(key, [])
        for number, title in pick_entries(question, toc_entries(embeddings.record_text(toc))):
            head = _heading_pattern(number, title)
            for i in ids:
                text = embeddings.record_text(meta[i])
                if is_toc(text) or not head.search(text):
                    continue
                for j in (i, i + 1):   # heading chunk + the chunk it runs into
                    if j not in ids:
                        continue
                    t = embeddings.record_text(meta[j])
                    if t not in have and not is_toc(t):
                        have.add(t)
                        extra.append({**meta[j], "relevance": toc["relevance"],
                                      "via_toc": f"{number}. {title}"})
                break   # one copy of the statute is enough
    return extra[:MAX_EXTRA_CHUNKS]
