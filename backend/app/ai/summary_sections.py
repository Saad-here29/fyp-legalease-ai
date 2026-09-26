"""Pull the "Key clauses" and "Risk flags" lists out of the LLM summary.

`AIClient.summarise()` asks for five numbered sections:
    1) Summary  2) Parties  3) Key dates  4) Key clauses / obligations
    5) Risk flags or missing standard clauses
and the model answers in markdown — headings like "**4) Key clauses …**" or
"### 4. Key Clauses", with the items as bullets, numbered lines or a table.
These lists are LLM-generated (not NER output); the API labels them so.
"""

from __future__ import annotations

import re

_HEADING = re.compile(
    r"^\s*(?P<mark>#{1,6}\s*|\*\*\s*)?(?P<num>[1-9])\s*[).:]\s*(?P<title>[^\n]*)$",
    re.MULTILINE,
)
_SECTION_WORDS = ("summary", "part", "date", "clause", "obligation", "risk")
_BULLET = re.compile(r"^\s*(?:[-*+•]|\d{1,2}[.)])\s+(?P<item>.+)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _clean(s: str) -> str:
    s = re.sub(r"\s*<br\s*/?>\s*", "; ", s)
    s = s.replace("**", "").replace("__", "")
    s = re.sub(r"(?<!\w)[*_](\S[^*_]*?)[*_](?!\w)", r"\1", s)  # *italic*
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -–—:;*_")


def _section_bodies(summary: str) -> dict[int, tuple[str, str]]:
    """{section number: (heading title, body text)}"""
    # A numbered list item ("1. Security deposit ...") looks like a heading;
    # require heading markup, or a short title naming one of the sections.
    heads = [
        h for h in _HEADING.finditer(summary)
        if h.group("mark")
        or (len(h.group("title")) <= 60
            and any(w in h.group("title").lower() for w in _SECTION_WORDS))
    ]
    out: dict[int, tuple[str, str]] = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(summary)
        num = int(h.group("num"))
        if num not in out:
            out[num] = (_clean(h.group("title")), summary[h.end():end])
    return out


def _items(body: str) -> list[str]:
    """Items in document order from bullets / numbered lines / table rows.
    Plain paragraphs are used only when the section has neither — otherwise
    they are the model's intro or "Overall, …" wrap-up, not items."""
    items: list[str] = []
    paragraphs: list[str] = []
    header_pending = False        # next table row after a new table = header
    in_table = False
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            in_table = False
            continue
        if stripped.startswith("|"):
            if _TABLE_SEP.match(stripped):
                header_pending = False
                continue
            if not in_table:
                in_table, header_pending = True, True
                header = stripped
                continue
            cells = [c for c in (_clean(c) for c in stripped.strip("|").split("|")) if c]
            if cells:
                items.append(" — ".join(cells))
            continue
        in_table = False
        m = _BULLET.match(line)
        if m:
            items.append(_clean(m.group("item")))
        elif items and line.startswith(("  ", "\t")):
            items[-1] = f"{items[-1]} {_clean(stripped)}"   # wrapped bullet
        else:
            paragraphs.append(_clean(stripped))
    if header_pending:            # a lone table row with no separator: data
        cells = [c for c in (_clean(c) for c in header.strip("|").split("|")) if c]
        items.append(" — ".join(cells))
    return [i for i in (items or paragraphs) if len(i) > 2]


def extract_clauses_and_risks(summary: str) -> tuple[list[str], list[str]]:
    """Return (key_clauses, risks) from sections 4 and 5; empty lists when
    the summary doesn't follow the requested structure."""
    sections = _section_bodies(summary or "")

    def find(num: int, keyword: str) -> list[str]:
        if num in sections and keyword in sections[num][0].lower():
            return _items(sections[num][1])
        for title, body in sections.values():   # numbering drifted
            if keyword in title.lower():
                return _items(body)
        return []

    return find(4, "clause"), find(5, "risk")
