"""Post-generation citation grounding for the legal chat.

The retrieval index is statute text only, so the answer the LLM writes may
only cite what the retrieved passages actually contain. After the answer
comes back, `check_citations()`:

  * removes the sentence (or table cell) around any case-law citation —
    law-report cites like "PLD 2005 SC 1234" or names like "X v. Y" —
    unless that exact citation appears in a passage;
  * marks each Section / Article reference whose number is not found in
    the passages "(unverified)" and lists them in a closing note;
  * drops [n] source markers that point past the passages supplied —
    after first rewriting the model's own "【n】" / "【n†L1-L3】" citation
    format to "[n]" (`normalize_markers`), so every marker is validated.

Deterministic regex/string matching, no LLM call. It verifies that a cited
number EXISTS in the retrieved text, not that the answer describes it
correctly — see the limitations in the Sept 2026 citation-fix notes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Normalisation. Every mapping is one character -> one character, so match
# offsets in the normalised text are valid offsets in the original answer.
# ---------------------------------------------------------------------------

_NORM = str.maketrans({
    " ": " ", " ": " ", " ": " ", " ": " ",
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-",
    "‘": "'", "’": "'",
    "*": " ", "_": " ", "`": " ",
    **{chr(0x06F0 + i): str(i) for i in range(10)},  # Urdu digits
    **{chr(0x0660 + i): str(i) for i in range(10)},  # Arabic-Indic digits
})


def _norm(text: str) -> str:
    return text.translate(_NORM)


def _squash(text: str) -> str:
    """Lowercase alphanumerics only — makes OCR-split titles comparable
    ("ORDINAN CE" -> "ordinance", "WAR DS" -> "wards")."""
    return re.sub(r"[^0-9a-z]", "", text.lower())


# ---------------------------------------------------------------------------
# Statute names
# ---------------------------------------------------------------------------

# Words too generic to identify a statute.
_STOP = {"the", "of", "and", "for", "in", "on", "a", "an", "to", "no",
         "pakistan", "west", "islamic", "republic", "federal"}

_ALIASES: dict[str, list[str]] = {
    "ppc": ["penal", "code"],
    "crpc": ["criminal", "procedure"],
    "cpc": ["civil", "procedure"],
    "mflo": ["muslim", "family", "laws"],
    "mfl": ["muslim", "family", "laws"],
    "dmma": ["dissolution", "muslim", "marriages"],
    "qso": ["shahadat"],
    "fca": ["family", "courts"],
    "gwa": ["guardians", "wards"],
}
_ALIAS_RE = (
    r"(?:P\.?\s?P\.?\s?C\.?|Cr\.?\s?P\.?\s?C\.?|C\.?\s?P\.?\s?C\.?"
    r"|MFLO|MFL|DMMA|QSO|FCA|GWA)(?![A-Za-z])"
)
_STATUTE_WORD = r"(?:Act|Ordinance|Code|Order|Constitution|Rules|Regulations)"
# "Muslim Family Laws Ordinance, 1961" / "Constitution" / "the Ordinance"
_TITLE_RE = (
    r"(?:[A-Z][\w'-]*\s+(?:(?:of|and|for|the|in|on|&)\s+)*){0,10}"
    rf"{_STATUTE_WORD}\b(?:\s*\([A-Za-z. ]{{2,12}}\))?(?:\s*,?\s*\(?\d{{4}}\)?)?"
)


def _statute_words(name: str) -> list[str]:
    alias = _squash(name)
    if alias in _ALIASES:
        return _ALIASES[alias]
    words: list[str] = []
    for w in re.findall(r"[a-z]+", name.lower()):
        if w in _ALIASES:
            words.extend(_ALIASES[w])
        elif len(w) > 1 and w not in _STOP:
            words.append(w)
    return words


def _owner_matches(words: list[str], owner_squashed: str) -> bool:
    return bool(words) and all(w in owner_squashed for w in words)


# ---------------------------------------------------------------------------
# Section / Article references
# ---------------------------------------------------------------------------

_KEYWORD = (
    r"(?<![\w/])(?i:sections?|secs?\.?|ss\.|s\.|u/s\.?|articles?|arts?\.)"
    r"|§§?|دفعات|دفعہ|آرٹیکل"
)
_NUM = r"\d{1,4}(?:\s?-\s?[A-Z](?![A-Za-z])|[A-Z](?![A-Za-z]))?"
_SUB = r"(?:\s*\((?:\d{1,3}|[a-z]{1,4})\))*"
_SEP = r"\s*(?:,|and|or|&|/|to|-)\s*"
_REF_RE = re.compile(rf"(?:{_KEYWORD})\s*({_NUM}{_SUB}(?:{_SEP}{_NUM}{_SUB})*)")
# "302 PPC", "PPC 302"
# never read a year as a section number ("MFLO 1961")
_NOT_YEAR = r"(?!(?:18|19|20)\d\d(?!\d))"
_ALIAS_NUM_RE = re.compile(
    rf"(?<![\w.]){_NOT_YEAR}({_NUM})\s*,?\s*({_ALIAS_RE})"
    rf"|(?<![\w])({_ALIAS_RE})\s*,?\s*{_NOT_YEAR}({_NUM})(?![\d])"
)
# PDF-style numbered headings in passages: "9. Maintenance", "3[25-A. Transfer"
_HEADING_RE = re.compile(
    rf"(?:^|(?<=[\s.;:\[\]|\-]))({_NUM})\s?\.\s*(?=[A-Z\"'(])"
)


def _canon(num: str) -> str:
    return re.sub(r"[\s-]", "", num).upper()


def _expand(listing: str) -> list[str]:
    """'8-10' -> 8,9,10 ; '7(1) and 8' -> 7,8 ; '489-F' -> 489F."""
    listing = re.sub(r"\((?:\d{1,3}|[a-z]{1,4})\)", "", listing)
    out: list[str] = []
    pos = 0
    for m in re.finditer(_NUM, listing):
        num = _canon(m.group(0))
        sep = listing[pos:m.start()]
        if out and re.fullmatch(r"\s*(?:-|to)\s*", sep) and out[-1].isdigit() and num.isdigit():
            a, b = int(out[-1]), int(num)
            if 0 < b - a <= 30:
                out.extend(str(n) for n in range(a + 1, b + 1))
                pos = m.end()
                continue
        out.append(num)
        pos = m.end()
    return out


def _after_hint(text: str, end: int) -> tuple[str | None, int]:
    """Statute named right after a reference: 'of the X Act', ' PPC'."""
    tail = text[end:end + 160]
    m = re.match(rf"\s*,?\s*(?:of\s+(?:the\s+)?)?({_ALIAS_RE})", tail)
    if m:
        return m.group(1), end + m.end()
    m = re.match(rf"\s*,?\s*(?:of\s+(?:the\s+)?)?({_TITLE_RE})", tail)
    if m:
        return m.group(1), end + m.end()
    return None, end


def _before_hint(text: str, start: int) -> str | None:
    """Statute named right before: 'MFLO s. 7', 'the X Ordinance, 1961, Section 9'."""
    head = text[max(0, start - 120):start]
    head = re.split(r"[.!?]\s|\n|\|", head)[-1]
    m = re.search(rf"({_ALIAS_RE})\s*[,:\-]?\s*$", head)
    if m:
        return m.group(1)
    m = re.search(rf"({_TITLE_RE})\s*[,(:\-]?\s*$", head)
    if m:
        return m.group(1)
    return None


@dataclass
class _Ref:
    start: int
    end: int           # end of the reference itself (where a flag goes)
    label: str         # original text, e.g. "Section 9"
    numbers: list[str]
    statute: str | None


def _find_refs(text: str) -> list[_Ref]:
    norm = _norm(text)
    refs: list[_Ref] = []
    for m in _REF_RE.finditer(norm):
        statute, _ = _after_hint(norm, m.end())
        statute = statute or _before_hint(norm, m.start())
        if statute is None and refs and re.fullmatch(
                r"\s*(?:,|and|&|or)\s*", norm[refs[-1].end:m.start()]):
            statute = refs[-1].statute  # "Sec. 7 & Sec. 12" share one Act
        refs.append(_Ref(m.start(), m.end(), text[m.start():m.end()].strip(),
                         _expand(m.group(1)), statute))
    taken = [(r.start, r.end) for r in refs]
    for m in _ALIAS_NUM_RE.finditer(norm):
        if any(s <= m.start() < e for s, e in taken):
            continue
        num = m.group(1) or m.group(4)
        alias = m.group(2) or m.group(3)
        refs.append(_Ref(m.start(), m.end(), text[m.start():m.end()].strip(),
                         [_canon(num)], alias))
    refs.sort(key=lambda r: r.start)
    return refs


def _passage_index(passages: list[dict]) -> list[tuple[str, str]]:
    """(section number, squashed owning-statute name) for every provision
    number that appears in the passages."""
    entries: list[tuple[str, str]] = []
    for p in passages:
        source = _squash(p.get("source") or "")
        text = _norm(p.get("text") or "")
        for m in _REF_RE.finditer(text):
            statute, _ = _after_hint(text, m.end())
            statute = statute or _before_hint(text, m.start())
            words = _statute_words(statute) if statute else []
            owner = "".join(words) if words else source
            for n in _expand(m.group(1)):
                entries.append((n, owner))
        for m in _ALIAS_NUM_RE.finditer(text):
            num = m.group(1) or m.group(4)
            alias = m.group(2) or m.group(3)
            entries.append((_canon(num), "".join(_statute_words(alias))))
        for m in _HEADING_RE.finditer(text):
            entries.append((_canon(m.group(1)), source))
    return entries


def _grounded(num: str, statute: str | None, index: list[tuple[str, str]]) -> bool:
    # A generic name ("the Act") yields no words: number-only matching.
    words = _statute_words(statute) if statute else []
    return any(n == num and (not words or _owner_matches(words, owner))
               for n, owner in index)


# ---------------------------------------------------------------------------
# Case-law citations
# ---------------------------------------------------------------------------

_REPORTER_RE = re.compile(
    r"\b(?:PLD|PLJ|NLR|KLR)\s*\(?\d{4}\)?(?:\s+(?:SC|FSC|Lah|Kar|Pesh|Quetta|Isl|"
    r"[A-Z][a-z]+\.?)(?:\s+\([^)]*\))?)?(?:\s+\d{1,5})?"
    r"|\b\d{4}\s+(?:SCMR|MLD|CLC|YLR|PCr\.?\s?LJ|P\.?\s?Cr\.?\s?L\.?\s?J\.?|PLC|CLD|PTD|SCJ|MLR|CLJ)\b"
    r"(?:\s+(?:\([^)]*\)\s+)?\d{1,5})?"
)
_CASE_NAME_RE = re.compile(
    r"\b(?!(?:See|In|Cf|Also|And|The)\b)[A-Z][\w'.-]*(?:\s+(?:[A-Z][\w'.-]*|bin|binte|ul|ud|al)){0,5}"
    r"\s+(?:v\.?|vs\.?|versus)\s+"
    r"[A-Z][\w'.-]*(?:\s+(?:[A-Z][\w'.-]*|bin|binte|ul|ud|al)){0,5}"
)
_ABBREV = {"mst", "v", "vs", "s", "ss", "sec", "secs", "art", "arts", "no", "nos",
           "mr", "mrs", "ms", "dr", "st", "ltd", "co", "sc", "lah", "kar", "pesh",
           "cr", "e.g", "eg", "i.e", "ie", "cf", "u/s", "viz", "pp", "p"}


def _is_sentence_end(text: str, dot: int) -> bool:
    if text[dot] in "!?":
        return True
    token = re.search(r"([\w./]+)$", text[:dot])
    word = (token.group(1) if token else "").lower().rstrip(".")
    return not (len(word) == 1 or word in _ABBREV)


def _sentence_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Sentence around [start, end) inside its line, bounded by line breaks,
    <br> and sentence terminators (not abbreviations like 'Mst.' / 'v.')."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line_end = len(text) if line_end == -1 else line_end
    left = line_start
    for m in re.finditer(r"[.!?](?=\s)|<br\s*/?>", text[line_start:start]):
        pos = line_start + m.start()
        if m.group(0).startswith("<") or _is_sentence_end(text, pos):
            left = line_start + m.end()
    right = line_end
    for m in re.finditer(r"[.!?](?=\s|$)|<br\s*/?>", text[end:line_end]):
        pos = end + m.start()
        if m.group(0).startswith("<"):
            right = pos
            break
        if _is_sentence_end(text, pos):
            right = pos + 1
            break
    while left < right and text[left] in " \t":
        left += 1
    if not text[line_start:left].strip():
        # sentence opens the line: keep a list marker ("- ", "1. ") in place
        lm = re.match(r"(?:[-*+]\s+|\d+[.)]\s+|#+\s+|>\s*)", text[left:right])
        if lm:
            left += lm.end()
    return left, right


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_MARKERS = {
    "en": {
        "case": "[case citation removed — not in LegalEase's statute library]",
        "flag": "(unverified)",
        "note": ("Note: the following references were not found in the statute "
                 "text retrieved for this answer, so they are unverified. Check "
                 "them against the statute before relying on them: "),
    },
    "ur": {
        "case": "[مقدمے کا حوالہ حذف کر دیا گیا — LegalEase کی قانونی لائبریری میں موجود نہیں]",
        "flag": "(غیر مصدقہ)",
        "note": ("نوٹ: درج ذیل حوالہ جات اس جواب کے لیے حاصل کیے گئے قانونی متن میں "
                 "نہیں ملے، اس لیے غیر مصدقہ ہیں۔ ان پر انحصار سے پہلے متعلقہ قانون "
                 "سے تصدیق کر لیں: "),
    },
}


@dataclass
class CitationCheck:
    text: str
    verified: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    removed_case_citations: list[str] = field(default_factory=list)
    removed_markers: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (f"{len(self.verified)} verified, {len(self.unverified)} unverified, "
                f"{len(self.removed_case_citations)} case citations removed, "
                f"{len(self.removed_markers)} bad [n] markers removed")


def _remove_case_citations(text: str, passages_norm: str, marker: str,
                           removed: list[str]) -> str:
    norm = _norm(text)
    hits: list[tuple[int, int]] = []
    for rx in (_REPORTER_RE, _CASE_NAME_RE):
        for m in rx.finditer(norm):
            cite = re.sub(r"\s+", " ", m.group(0)).strip()
            if cite in passages_norm:
                continue
            hits.append((m.start(), m.end()))
            removed.append(cite)
    if not hits:
        return text

    spans: list[tuple[int, int]] = []
    for start, end in hits:
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", start)
        line_end = len(text) if line_end == -1 else line_end
        line = text[line_start:line_end]
        if line.lstrip().startswith("|") and "|" in text[start:line_end]:
            # Table row: drop the whole cell. If the citation sits in the
            # row's first cell, the row is about the judgment, so blank it.
            cells = [m.start() for m in re.finditer(r"\|", line)]
            rel = start - line_start
            idx = max(i for i, c in enumerate(cells) if c <= rel)
            if idx == 0:
                spans.append((line_start + cells[0] + 1, line_start + cells[-1]))
            else:
                spans.append((line_start + cells[idx] + 1, line_start + cells[idx + 1]))
        else:
            spans.append(_sentence_span(text, start, end))

    spans.sort()
    merged: list[list[int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out, pos = [], 0
    for s, e in merged:
        chunk = text[s:e]
        replacement = marker
        if "|" in chunk:  # blanked table row: keep the column count
            replacement = f" {marker} " + "| " * chunk.count("|")
        elif text[s - 1:s] == "|" or text[e:e + 1] == "|":
            replacement = f" {marker} "
        out.append(text[pos:s])
        out.append(replacement)
        pos = e
    out.append(text[pos:])
    result = "".join(out)
    esc = re.escape(marker)
    return re.sub(rf"{esc}(?:\s*{esc})+", marker, result)


# The model (gpt-oss) sometimes cites in its own format — "【5】",
# "【5†L1-L3】", "【4, 5】" — instead of the "[n]" the prompt asks for. 18% of
# stored answers did (Sept 2026). Rewriting to "[n]" before the checks means
# those markers are range-checked like any other and the UI can link them.
_FULLWIDTH_MARKER = re.compile(r"【\s*(\d{1,2}(?:\s*,\s*\d{1,2})*)\s*(?:†[^】]*)?】")


def normalize_markers(text: str) -> str:
    """Rewrite "【5†L1-L3】" to "[5]" and "【4, 5】" to "[4][5]"; other text unchanged."""
    return _FULLWIDTH_MARKER.sub(
        lambda m: "".join(f"[{n.strip()}]" for n in m.group(1).split(",")), text)


def check_citations(answer: str, passages: list[dict], lang: str = "en") -> CitationCheck:
    """`passages` are the retrieved records (need `source` and `text`), in
    the same order they were numbered [1..n] in the prompt."""
    words = _MARKERS["ur" if lang == "ur" else "en"]
    passages_norm = re.sub(r"\s+", " ", _norm(" ".join(p.get("text") or "" for p in passages)))
    answer = normalize_markers(answer)
    result = CitationCheck(text=answer)

    # 1) Case-law citations
    text = _remove_case_citations(answer, passages_norm, words["case"],
                                  result.removed_case_citations)

    # 2) [n] markers beyond the passages supplied
    n_passages = len(passages)

    def _marker(m: re.Match) -> str:
        n = int(m.group(1))
        if 1 <= n <= n_passages:
            return m.group(0)
        result.removed_markers.append(m.group(0).strip())
        return ""

    text = re.sub(r"\s?\[(\d{1,2})\](?!\()", _marker, text)

    # 3) Section / Article references
    index = _passage_index(passages)
    inserts: list[tuple[int, str]] = []
    seen_unverified: dict[str, None] = {}
    for ref in _find_refs(text):
        missing = [n for n in ref.numbers if not _grounded(n, ref.statute, index)]
        tag = f"{ref.label}" + (f" ({ref.statute.strip()})" if ref.statute else "")
        if not missing:
            result.verified.append(tag)
            continue
        flag = words["flag"] if len(missing) == len(ref.numbers) else \
            f"{words['flag'][:-1]}: {', '.join(missing)})"
        inserts.append((ref.end, f" {flag}"))
        seen_unverified[tag] = None
    for pos, s in sorted(inserts, reverse=True):
        text = text[:pos] + s + text[pos:]
    result.unverified = list(seen_unverified)
    if result.unverified:
        text = text.rstrip() + "\n\n" + words["note"] + "; ".join(result.unverified) + "."

    result.text = text
    return result
