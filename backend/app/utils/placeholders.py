"""Unfilled template placeholders in generated contract text.

The drafting prompt says "do not leave placeholders", but when a detail
was never supplied (an address, a signing date) the model still writes
"[address]" or "[date]" (Oct 2026 audit). Deterministic, no AI call.

Flagged: bracketed words ("[address]", "[Name of Employer]"), blank
brackets ("[ ]", "[____]", "[●]"), "{{field}}" and "<<field>>".
Not flagged: markdown links "[text](url)", numbered or lettered markers
("[1]", "[a]", "[ii]"), and underscore lines; those are the intentional
blanks of a signature block, to be filled in by hand.
"""

import re

_BRACKETED = re.compile(r"\[([^\[\]\n]{0,60})\](?!\()")
_TEMPLATED = re.compile(r"\{\{[^{}\n]{1,60}\}\}|<<[^<>\n]{1,60}>>")
_BLANK = re.compile(r"[\s_.…●•\-]*")
_ROMAN = re.compile(r"[ivxlcdm]+", re.IGNORECASE)


def _is_placeholder(inner: str) -> bool:
    inner = inner.strip()
    if _BLANK.fullmatch(inner):
        return True
    letters = sum(ch.isalpha() for ch in inner)
    return letters >= 2 and not _ROMAN.fullmatch(inner)


def find_unfilled_placeholders(text: str) -> list[str]:
    """Distinct placeholders, in order of first appearance."""
    found: list[tuple[int, str]] = []
    for m in _BRACKETED.finditer(text):
        if _is_placeholder(m.group(1)):
            found.append((m.start(), m.group(0)))
    found += [(m.start(), m.group(0)) for m in _TEMPLATED.finditer(text)]
    seen: dict[str, None] = {}
    for _, p in sorted(found):
        seen.setdefault(p, None)
    return list(seen)
