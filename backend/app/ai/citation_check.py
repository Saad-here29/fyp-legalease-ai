"""Post-generation citation grounding for the legal chat.

The retrieval index is statute text only, so the answer the LLM writes may
only cite what the retrieved passages actually contain. After the answer
comes back, `check_citations()`:

  * removes the sentence (or table cell) around any case-law citation —
    law-report cites like "PLD 2005 SC 1234" or names like "X v. Y" —
    unless that exact citation appears in a passage;
  * lists each Section / Article reference whose number is not found in
    the passages in a closing note (kb-v2 C13: the answer body itself is
    never marked);
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
        # A knowledge-base (kb-v2) record holds one section; its number is in
        # the record, not in the text ("Section 302" was flagged unverified
        # even when the s.302 record itself was retrieved).
        if p.get("section") and re.match(r"\d", str(p["section"])):
            entries.append((_canon(str(p["section"])), source))
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
# Judgments retrieved for the answer (kb-v2 C2)
# ---------------------------------------------------------------------------

# "Civil Petition No. 1234 of 2022", "C.P. 1234/2022", "CIVIL PETITIONS NO.4657 TO 4659 OF 2022"
_CASE_NO_RE = re.compile(
    r"(?i:(?:\b(?:civil|criminal|crl\.?|constitutional|const\.?|jail|family|writ|review|human\s+rights)\s+)?"
    r"\b(?:petitions?|appeals?|revisions?|references?|case|suit|c\.\s?p\.?\s?l\.?\s?a\.?|c\.\s?p\.?|c\.\s?a\.?"
    r"|crl\.\s?[ap]\.?|w\.\s?p\.?)\s*(?:nos?\.?\s*)?)"
    r"(\d{1,6})(?:-[A-Z])?(?:\s*(?i:to|-|&|,|and)\s*\d{1,6})*\s*(?i:of|/)\s*((?:19|20)\d\d)\b")
_PARA_RE = re.compile(r"(?i:\bpara(?:graph)?s?\.?)\s*(?:(?i:no)\.?\s*)?(\d{1,3})((?:\s*(?:,|and|&)\s*\d{1,3})*)")
# Words that don't identify a party.
_CASE_STOP = {"mst", "v", "vs", "versus", "and", "others", "other", "another", "the", "of", "through", "ltd",
              "petitioner", "petitioners", "respondent", "respondents", "appellant", "appellants", "in", "both",
              "etc", "pvt", "sh", "syed", "mr", "mrs", "ms", "dr", "its", "by"}


@dataclass
class _Case:
    name: str                    # as shown to the model (display name)
    words: set[str]              # party words of the case name and the shown name
    numbers: set[str]            # case number digits
    year: str | None             # case number year
    paragraph: int


def _case_words(name: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", (name or "").lower()) if len(w) > 1 and w not in _CASE_STOP]


def _as_case(j: dict) -> _Case:
    num = j.get("case_number") or ""
    years = re.findall(r"(?:19|20)\d\d(?!\d)", num)
    digits = set(re.findall(r"\d{1,6}", num)) - set(years[-1:])
    return _Case(name=j.get("display_name") or j.get("case_name") or num,
                 words=set(_case_words(j.get("case_name") or "")) | set(_case_words(j.get("display_name") or "")),
                 numbers=digits, year=years[-1] if years else None, paragraph=int(j.get("paragraph") or 0))


def _case_for(m: re.Match, rx: re.Pattern, cases: list[_Case]) -> _Case | None:
    """The retrieved case a case-name or case-number mention refers to."""
    if rx is _CASE_NO_RE:
        num, year = m.group(1), m.group(2)
        return next((c for c in cases if c.year == year and num in c.numbers), None)
    words = _case_words(m.group(0))
    if len(set(words)) < 2:
        return None
    return next((c for c in cases if all(w in c.words for w in words)), None)


def _case_paragraph_problems(text: str, cases: list[_Case]) -> list[tuple[str, int]]:
    """[(note item, flag position)] for each "para N" given for a retrieved
    case (the nearest case mention on the same line, preferring one before
    it) that isn't the paragraph retrieved for it. A paragraph with no
    retrieved case named on its line is left alone."""
    norm = _norm(text)
    mentions = []
    for rx in (_CASE_NAME_RE, _CASE_NO_RE):
        for m in rx.finditer(norm):
            c = _case_for(m, rx, cases)
            if c is not None:
                mentions.append((m.start(), m.end(), c))
    problems = []
    for m in _PARA_RE.finditer(norm):
        line_start = norm.rfind("\n", 0, m.start()) + 1
        line_end = norm.find("\n", m.end())
        line_end = len(norm) if line_end == -1 else line_end
        near = [(m.start() - e if e <= m.start() else s - m.end() + 1000, c)
                for s, e, c in mentions if line_start <= s < line_end and (e <= m.start() or s >= m.end())]
        if not near:
            continue
        case = min(near, key=lambda x: x[0])[1]
        nums = [int(m.group(1))] + [int(x) for x in re.findall(r"\d{1,3}", m.group(2) or "")]
        wrong = [n for n in nums if n != case.paragraph]
        if wrong:
            problems.append((f"{case.name}, para {', '.join(map(str, wrong))}: not the paragraph retrieved "
                             f"(para {case.paragraph})", m.end()))
    return problems


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_MARKERS = {
    "en": {
        "case": "[case citation removed — not in LegalEase's statute library]",
        "case_not_retrieved": "[case citation removed — not among the cases retrieved for this answer]",
        "flag": "(unverified)",
        "note": ("Note: the following references were not found in the statute "
                 "text retrieved for this answer, so they are unverified. Check "
                 "them against the statute before relying on them: "),
        "note_cases": ("Note: the following references were not found in the statute "
                       "text or the case paragraphs retrieved for this answer, so they are "
                       "unverified. Check them before relying on them: "),
    },
    "ur": {
        "case": "[مقدمے کا حوالہ حذف کر دیا گیا — LegalEase کی قانونی لائبریری میں موجود نہیں]",
        "case_not_retrieved": "[مقدمے کا حوالہ حذف کر دیا گیا — اس جواب کے لیے حاصل کیے گئے مقدمات میں شامل نہیں]",
        "flag": "(غیر مصدقہ)",
        "note": ("نوٹ: درج ذیل حوالہ جات اس جواب کے لیے حاصل کیے گئے قانونی متن میں "
                 "نہیں ملے، اس لیے غیر مصدقہ ہیں۔ ان پر انحصار سے پہلے متعلقہ قانون "
                 "سے تصدیق کر لیں: "),
        "note_cases": ("نوٹ: درج ذیل حوالہ جات اس جواب کے لیے حاصل کیے گئے قانونی متن یا مقدمات کے "
                       "پیراگراف میں نہیں ملے، اس لیے غیر مصدقہ ہیں۔ ان پر انحصار سے پہلے تصدیق کر لیں: "),
    },
}


@dataclass
class CitationCheck:
    text: str
    verified: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    removed_case_citations: list[str] = field(default_factory=list)
    removed_markers: list[str] = field(default_factory=list)
    cases_verified: list[str] = field(default_factory=list)    # judgments named and retrieved (kb-v2 C2)

    def summary(self) -> str:
        out = (f"{len(self.verified)} verified, {len(self.unverified)} unverified, "
               f"{len(self.removed_case_citations)} case citations removed, "
               f"{len(self.removed_markers)} bad [n] markers removed")
        return out + (f", {len(self.cases_verified)} retrieved cases cited" if self.cases_verified else "")


def _remove_case_citations(text: str, passages_norm: str, marker: str,
                           removed: list[str], cases: list[_Case] | None = None,
                           kept: list[str] | None = None) -> str:
    """`cases` (judgments retrieved for this answer, kb-v2 C2): a case name
    or case number matching one of them stays; any other is removed."""
    norm = _norm(text)
    hits: list[tuple[int, int]] = []
    patterns = (_REPORTER_RE, _CASE_NAME_RE) if cases is None else (_REPORTER_RE, _CASE_NAME_RE, _CASE_NO_RE)
    for rx in patterns:
        for m in rx.finditer(norm):
            cite = re.sub(r"\s+", " ", m.group(0)).strip()
            if cite in passages_norm:
                continue
            if cases is not None and rx is not _REPORTER_RE and _case_for(m, rx, cases) is not None:
                if kept is not None:
                    kept.append(cite)
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


_GROUPED_MARKER = re.compile(r"\[(\d{1,2}(?:\s*(?:,|[-–—])\s*\d{1,2})+)\](?!\()")


def _expand_group(group: str) -> str:
    out: list[int] = []
    for part in group.split(","):
        bounds = [int(x) for x in re.split(r"\s*[-–—]\s*", part.strip()) if x]
        if len(bounds) == 2 and 0 < bounds[1] - bounds[0] <= 10:
            out.extend(range(bounds[0], bounds[1] + 1))
        else:
            out.extend(bounds)
    return "".join(f"[{n}]" for n in out)


def normalize_markers(text: str) -> str:
    """Rewrite "【5†L1-L3】" to "[5]", "【4, 5】" and "[4, 5]" to "[4][5]", and
    "[1-3]" to "[1][2][3]", so every cited source is counted; other text unchanged."""
    text = _FULLWIDTH_MARKER.sub(
        lambda m: "".join(f"[{n.strip()}]" for n in m.group(1).split(",")), text)
    return _GROUPED_MARKER.sub(lambda m: _expand_group(m.group(1)), text)


# ---------------------------------------------------------------------------
# Acts named in the answer (kb-v2 B7)
# ---------------------------------------------------------------------------

_ACT_WORD = r"(?:[A-Z][A-Za-z'\-]*|\((?:[A-Z][A-Za-z]*\s?)+\))"
_ACT_NAME_RE = re.compile(
    rf"\b({_ACT_WORD}(?:\s+(?:{_ACT_WORD}|of|and|the|for|on|in|to|e))*\s+(?:Act|Ordinance|Order|Code))\b"
    r"(?:,?\s*(\d{4}))?")
_ACT_ABBR_RE = re.compile(r"(?<![\w.])(PPC|CrPC|Cr\.\s?P\.\s?C\.?|CPC|MFLO|QSO|DMMA)(?![\w])")
_LEAD_WORDS = re.compile(
    r"^(?:(?:The|Under|According|To|In|Per|As|By|Section|Sections|Article|Articles|This|That|Both|Unlike|Also|"
    r"And|Of|While|From|With|See|If|When|Whereas|Similarly|Moreover|However|Here|Note)\s+)+", re.I)
_ABBR_TITLE = {"ppc": "Pakistan Penal Code", "crpc": "Code of Criminal Procedure", "cpc": "Code of Civil Procedure",
               "mflo": "Muslim Family Laws Ordinance", "qso": "Qanun-e-Shahadat Order",
               "dmma": "Dissolution of Muslim Marriages Act"}


def _named_acts(text: str) -> list[tuple[int, int, str]]:
    """(start, end, name) of each Act / Ordinance / Order / Code named in the text."""
    out = []
    for m in _ACT_NAME_RE.finditer(text):
        name = m.group(1)
        lead = _LEAD_WORDS.match(name)
        start = m.start(1) + (lead.end() if lead else 0)
        name = text[start:m.end(1)]
        if len(name.split()) < 2:              # "Act", "the Code": too generic
            continue
        out.append((start, m.end(), name + (f", {m.group(2)}" if m.group(2) else "")))
    taken = [(s, e) for s, e, _ in out]
    for m in _ACT_ABBR_RE.finditer(text):
        if not any(s <= m.start() < e for s, e in taken):
            key = re.sub(r"[^a-z]", "", m.group(1).lower())
            out.append((m.start(), m.end(), _ABBR_TITLE.get(key, m.group(1))))
    return sorted(out)


def _matches_source(name: str, source: str) -> bool:
    """The Act named is that source. Both ways round, so a name with extra
    words ("the application of the Muslim Family Laws Ordinance") still
    matches the source "Muslim Family Laws Ordinance, 1961"."""
    words, src_words = _statute_words(name), _statute_words(source)
    return _owner_matches(words, _squash(source)) or _owner_matches(src_words, "".join(words))


def _act_problems(text: str, passages: list[dict], passages_norm: str) -> list[tuple[str, int]]:
    """[(note item, position for the inline flag)] for (a) Acts named but not
    retrieved and (b) [n] markers whose source isn't the Act named in their sentence."""
    sources = [p.get("source") or "" for p in passages]
    texts_squashed = _squash(passages_norm)
    acts = _named_acts(_norm(text))
    problems: list[tuple[str, int]] = []
    seen: set[str] = set()
    for _start, end, name in acts:
        words = _statute_words(name)
        if not words or any(_matches_source(name, s) for s in sources) or _owner_matches(words, texts_squashed):
            continue
        if name not in seen:
            seen.add(name)
            problems.append((f"Act named but not found in the retrieved text: {name}", end))
    for m in re.finditer(r"\[(\d{1,2})\](?!\()", text):
        n = int(m.group(1))
        if not 1 <= n <= len(sources):
            continue
        left, right = _sentence_span(text, m.start(), m.end())
        named = [name for s, e, name in acts if left <= s < right and _statute_words(name)]
        cited_text = _squash(_norm(passages[n - 1].get("text") or ""))
        # fine if [n] is that Act, or its text mentions the Act ("s.3: the Arbitration Act shall not apply")
        if named and not any(_matches_source(name, sources[n - 1])
                             or _owner_matches(_statute_words(name), cited_text) for name in named):
            problems.append((f"[{n}] cites {sources[n - 1]}, but the sentence names {' / '.join(dict.fromkeys(named))}",
                             m.end()))
    return problems


# kb-v2 C13: only consequences that name something specific are checked.
# Generic words (offence, illegal, penalty, punishable, punishment, liable)
# are not: an answer may call theft an offence without the passage saying
# "offence" in those words.
_CONSEQUENCE = re.compile(
    r"\b(null and void|voidable|void|invalid|nullity|forfeit(?:ed|ure)?|imprisonment for life|life imprisonment|"
    r"(?:punish(?:able|ed|ment)?|sentenced?|penalty|liable)\s+(?:with\s+|to\s+|of\s+)?death|"
    r"death (?:penalty|sentence))\b", re.I)
_CONSEQUENCE_IN_SOURCE = {
    "void": r"\bvoid\b|\bnullity\b", "voidable": r"\bvoidable\b", "invalid": r"\binvalid",
    "forfeit": r"\bforfeit", "life": r"imprisonment\s+for\s+life|life\s+imprisonment", "death": r"\bdeath\b",
}
# A sentence that states a penalty or other consequence: its periods and amounts are checked.
_CONSEQUENCE_CONTEXT = re.compile(
    r"\b(?:punish\w*|imprison\w*|fine[sd]?|penalt\w*|sentence[sd]?|liable|forfeit\w*|jail|detention|"
    r"compensation|extend(?:s|ed|ing)?)\b", re.I)


def _consequence_key(term: str) -> str:
    t = term.lower()
    if "death" in t:
        return "death"
    if "life" in t:
        return "life"
    if t.startswith("forfeit"):
        return "forfeit"
    if t in ("null and void", "nullity", "void"):
        return "void"
    return t


def _mask_titles(text: str) -> str:
    """The text with every statute title it names blanked, keeping offsets,
    so words inside a title ("Illegal Dispossession Act") are never read as claims."""
    out = list(text)
    for start, end, _name in _named_acts(_norm(text)):
        out[start:end] = " " * (end - start)
    return "".join(out)


def _consequence_problems(text: str, passages: list[dict],
                          reported: set[tuple[int, str]] | None = None,
                          case_texts: list[str] | None = None) -> list[tuple[str, int]]:
    """[(note item, position)] for each specific consequence the answer states
    (void, voidable, invalid, forfeiture, death, imprisonment for life) that no
    retrieved passage states, and each period or amount in a sentence stating
    a consequence that the retrieved text doesn't contain in any equivalent
    form ("twenty-five million rupees" = "Rs. 2,50,00,000"). `reported`:
    figures already listed by another check, skipped here."""
    src = " ".join(_norm(t) for t in [p.get("text") or "" for p in passages] + list(case_texts or [])).lower()
    src_figures = _figures(src)
    masked = _norm(_mask_titles(text))
    out: list[tuple[str, int]] = []
    for m in _CONSEQUENCE.finditer(masked):
        if not re.search(_CONSEQUENCE_IN_SOURCE[_consequence_key(m.group(1))], src):
            out.append((f"Legal consequence not stated in the retrieved text: \"{m.group(1)}\"", m.end()))
    seen: set[tuple[int, str]] = set(reported or ())
    spans: list[tuple[int, int]] = []
    for m in _CONSEQUENCE_CONTEXT.finditer(masked):
        span = _sentence_span(masked, m.start(), m.end())
        if span in spans:
            continue
        spans.append(span)
        for fig in sorted(_figures(masked[span[0]:span[1]].lower())):
            if fig in src_figures or fig in seen:
                continue
            seen.add(fig)
            out.append((f"Figure not in the retrieved text: {_show_figure(fig)}", span[1]))
    return out


def _stated_in_section(fig: tuple[int, str], refs: list[_Ref],
                       by_section: list[tuple[str, str, set[tuple[int, str]]]]) -> bool:
    """`fig` is in a retrieved section record one of `refs` names (same number, same Act if one is named)."""
    for ref in refs:
        words = _statute_words(ref.statute) if ref.statute else []
        if any(sec in ref.numbers and (not words or _owner_matches(words, owner)) and fig in figs
               for sec, owner, figs in by_section):
            return True
    return False


def _attribution_problems(text: str, passages: list[dict],
                          case_texts: list[str] | None = None) -> tuple[list[tuple[str, int]], set[tuple[int, str]]]:
    """kb-v2 C13: a period or amount the answer gives in a sentence naming
    "section N" must appear in a retrieved passage whose own section is N
    (the record's section, not a number mentioned inside its text). Returns
    (note items, the figures listed). Only for section records (kb-v2)."""
    by_section: list[tuple[str, str, set[tuple[int, str]]]] = []
    for p in passages:
        sec = str(p.get("section") or "")
        if re.match(r"\d", sec):
            by_section.append((_canon(sec), _squash(p.get("source") or ""), _figures(_norm(p.get("text") or ""))))
    if not by_section:
        return [], set()
    masked = _mask_titles(text)
    case_figs = set().union(*(_figures(_norm(t).lower()) for t in case_texts or [""]))
    all_refs = _find_refs(masked)
    # kb-v2 C20: a figure counts as stated if ANY section cited in the same paragraph (sections cited
    # together: "ss. 302 and 308") or a retrieved case paragraph states it, not only one section.
    paragraphs = [(m.start(), m.end()) for m in re.finditer(r"(?s).+?(?=\n\s*\n|\Z)", masked)]
    sentences: dict[tuple[int, int], list[_Ref]] = {}
    for ref in all_refs:
        sentences.setdefault(_sentence_span(masked, ref.start, ref.end), []).append(ref)
    out: list[tuple[str, int]] = []
    listed: set[tuple[int, str]] = set()
    for (left, right), refs in sentences.items():
        figs = _figures(_norm(masked[left:right]).lower())
        if not figs:
            continue
        para = next(((a, b) for a, b in paragraphs if a <= left < b), (left, right))
        together = [r for r in all_refs if para[0] <= r.start < para[1]] or refs
        nums = list(dict.fromkeys(n for r in refs for n in r.numbers))
        for fig in sorted(figs):
            if fig in case_figs:
                continue
            if fig not in listed and not _stated_in_section(fig, together, by_section):
                listed.add(fig)
                out.append((f"{_show_figure(fig)} is given for section {', '.join(nums)}, but that section's "
                            "retrieved text doesn't state it", right))
    return out, listed


# Number words, matched on text with the spaces removed so that OCR splits
# ("one thous and rupees") and joined words read the same (kb-v2 C8). C13:
# compound numbers ("one hundred and twenty"), ranges ("ten to twenty-five
# years" = 10 and 25 years), scale words (thousand, lakh, crore, million,
# billion) and "Rs."/"rupees" before or after an amount.
_UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen".split())}
_TENS = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
_SCALES = {"hundred": 100, "thousand": 1000, "lakh": 100000, "lac": 100000, "crore": 10000000,
           "million": 1000000, "billion": 1000000000}
_WORDS_LONGEST = sorted([*_UNITS, *_TENS, *_SCALES], key=len, reverse=True)
_NUMBER_WORD = "|".join(_WORDS_LONGEST)
_AMOUNT = r"(?:\d+(?:\.\d+)?|" + _NUMBER_WORD + r"|and)+"
_CUR = "\u20a8"                     # "₨": stands for a whole-word Rs / Rs. / PKR / rupee(s) (kb-v2 C20)
_UNIT = r"(years?|months?|weeks?|days?|" + _CUR + r")"
_RANGE = re.compile(r"(" + _AMOUNT + r"?)(?:to|or)(" + _AMOUNT + r"?)" + _UNIT)
_FIGURE = re.compile(r"(" + _AMOUNT + r"?)" + _UNIT)
_RS = re.compile(_CUR + r"(?!and)(" + _AMOUNT + r")")
# Currency only as a whole word: never the "rs" of "under s. 302" or "offenders".
_CURRENCY_WORD = re.compile(r"(?<![a-z])(?:rs\.?|pkr|rupees?)(?![a-z])")
# A thousands-grouped number, western "1,000,000" or Pakistani "2,50,00,000".
_GROUPED = re.compile(r"(?<![\d,])\d{1,3}(?:(?:,\d{2})*,\d{3}|(?:,\d{3})+)(?![\d]|,\d)")
_NUMBER_FOLLOWERS = r"(?:years?|months?|weeks?|days?|hundred|thousand|lakhs?|lacs?|crores?|million|billion|to|or|and)\b"


def _words_to_number(s: str) -> int | None:
    """"fivethousand" -> 5000, "onehundredandtwenty" -> 120, "twentyfivemillion" -> 25000000,
    "5,000" -> 5000, "2.5million" -> 2500000."""
    if not s or s == "and":
        return None
    if re.fullmatch(r"\d[\d,]*(?:\.\d+)?", s):
        return int(float(s.replace(",", "")))
    m = re.fullmatch(r"(\d[\d,]*(?:\.\d+)?)(" + "|".join(_SCALES) + r")", s)
    if m:
        return int(round(float(m.group(1).replace(",", "")) * _SCALES[m.group(2)]))
    total = current = 0
    pos = 0
    while pos < len(s):
        w = next((w for w in _WORDS_LONGEST if s.startswith(w, pos)), None)
        if w is None:
            if s.startswith("and", pos):          # "one hundred and twenty"
                pos += 3
                continue
            return None
        if w in _UNITS:
            current += _UNITS[w]
        elif w in _TENS:
            current += _TENS[w]
        elif w == "hundred":
            current = (current or 1) * 100
        else:
            total += (current or 1) * _SCALES[w]
            current = 0
        pos += len(w)
    return total + current if (total or current) else None


def _unit(u: str) -> str:
    return "rupee" if u == _CUR else u.rstrip("s")


def _figures(text: str) -> set[tuple[int, str]]:
    """(amount, unit) pairs, whatever the spacing or form: "three months" and
    "3 months" -> (3, "month"); "one thous and rupees", "Rs.1,000" -> (1000, "rupee");
    "ten to twenty-five years" -> (10, "year") and (25, "year")."""
    low = re.sub(r"(\d)\s*[-–—]\s*(\d)", r"\1 to \2", (text or "").lower())        # "10-25 years"
    low = re.sub(r"\bbetween\s+(\S+(?:\s+\S+){0,4}?)\s+and\s+", r"\1 to ", low)  # "between 3 and 7 years"
    low = _GROUPED.sub(lambda m: m.group(0).replace(",", ""), low)                # "2,50,00,000", "5,000"
    low = _CURRENCY_WORD.sub(f" {_CUR} ", low)                                    # whole-word Rs / rupees only
    # kb-v2 C20: separate numbers never join once spaces are removed ("sections 306, 307, 25 years"
    # is not 30630725 years; "s. 302 twenty-five years" is not 302 + twenty-five).
    low = re.sub(r"(\d)\s*[,;]\s*(?=\d)", r"\1;", low)
    low = re.sub(r"(\d)\s+(?=\d)", r"\1;", low)
    low = re.sub(r"(\d)\s+(?=[a-z])(?!" + _NUMBER_FOLLOWERS + ")", r"\1;", low)
    compact = re.sub(r"[\s\-]+", "", low)
    out = set()
    for a, b, unit in _RANGE.findall(compact):
        for num in (a, b):
            n = _words_to_number(num)
            if n is not None:
                out.add((n, _unit(unit)))
    for num, unit in _FIGURE.findall(compact):
        n = _words_to_number(num)
        if n is not None:
            out.add((n, _unit(unit)))
    for num in _RS.findall(compact):
        n = _words_to_number(num)
        if n is not None:
            out.add((n, "rupee"))
    return out


def _show_figure(fig: tuple[int, str]) -> str:
    n, unit = fig
    return f"Rs {n:,}" if unit == "rupee" else f"{n} {unit}{'' if n == 1 else 's'}"


def _mask_headings(text: str) -> str:
    """The text with the model's own markdown headings ("### Penalty",
    "**Legal consequences**" alone on a line) blanked, keeping every offset."""
    return re.sub(r"(?m)^[ \t]*(?:#{1,6}[ \t].*|\*\*[^*\n]{1,80}\*\*:?[ \t]*)$", lambda m: " " * len(m.group(0)), text)


def check_citations(answer: str, passages: list[dict], lang: str = "en",
                    judgments: list[dict] | None = None, consequences: bool = False) -> CitationCheck:
    """`passages` are the retrieved records (need `source` and `text`), in
    the same order they were numbered [1..n] in the prompt.

    `judgments` (kb-v2 C2, JUDGMENTS_V2): the case paragraphs given to the
    model (display_name, case_name, case_number, paragraph). A case the
    answer names must be one of them (by party names, or case number and
    year), else its sentence is removed; a paragraph number given for one
    must be the paragraph retrieved, else it is flagged and listed in the
    note. None: exactly the statute-only check.

    `consequences` (kb-v2 C5, on with KB_V2): a specific legal consequence
    the answer states (void, invalid, forfeiture, death, imprisonment for
    life, a period or an amount) that no retrieved passage states is listed
    in the note.

    kb-v2 C13: the answer body is never marked; unverified items appear only
    in the closing note. Statute titles are never read as claims."""
    words = _MARKERS["ur" if lang == "ur" else "en"]
    passages_norm = re.sub(r"\s+", " ", _norm(" ".join(p.get("text") or "" for p in passages)))
    answer = normalize_markers(answer)
    result = CitationCheck(text=answer)
    cases = None if judgments is None else [_as_case(j) for j in judgments]

    # 1) Case-law citations
    text = _remove_case_citations(answer, passages_norm,
                                  words["case"] if cases is None else words["case_not_retrieved"],
                                  result.removed_case_citations, cases, result.cases_verified)

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
    seen_unverified: dict[str, None] = {}
    for ref in _find_refs(text):
        missing = [n for n in ref.numbers if not _grounded(n, ref.statute, index)]
        tag = f"{ref.label}" + (f" ({ref.statute.strip()})" if ref.statute else "")
        if not missing:
            result.verified.append(tag)
            continue
        seen_unverified[tag if len(missing) == len(ref.numbers) else f"{tag}: {', '.join(missing)}"] = None

    # 4) Acts named in the answer (kb-v2 B7): (a) each must be a retrieved
    #    source or appear in the retrieved text; (b) a [n] marker must point
    #    to a source matching an Act named in its own sentence.
    for item, _pos in _act_problems(_mask_headings(text) if consequences else text, passages, passages_norm):
        seen_unverified[item] = None
    # 5) Paragraph numbers given for retrieved cases (kb-v2 C2)
    if cases:
        for item, _pos in _case_paragraph_problems(text, cases):
            seen_unverified[item] = None
    # 6) Legal consequences the retrieved text doesn't state (kb-v2 C5, C13)
    if consequences:
        case_texts = [j.get("paragraph_text") or j.get("text") or "" for j in judgments or []]
        attributed, listed = _attribution_problems(_mask_headings(text), passages, case_texts)   # (kb-v2 C13, C20)
        for item, _pos in attributed + _consequence_problems(_mask_headings(text), passages, listed, case_texts):
            seen_unverified[item] = None
    result.unverified = list(seen_unverified)
    if result.unverified:
        note = words["note"] if cases is None else words["note_cases"]
        text = text.rstrip() + "\n\n" + note + "; ".join(result.unverified) + "."

    result.text = text
    return result
