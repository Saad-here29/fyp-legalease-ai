"""Split a statute's text into one record per section (kb-v2, offline).

Two input shapes occur in the corpus:

* ``statute_section_table`` (CSV-derived): lines like
  ``Chapter I — Preliminary`` / ``Section 9 — Maintenance`` / text.
* ``statute_pdf`` (Pakistan Code PDF text, whitespace-flattened): a CONTENTS
  table, then the body with ``9. Maintenance.—(1) ...``, page markers
  ``Page 3 of 7``, per-page footnotes ``1Subs. by ...`` and amendment markers
  ``3[(iia) ...]``, then optional SCHEDULEs. Older extractions are glued
  ("CONTENTSSECTIONS:1.Short title.2.Definitions", "Page2of6622." = page 2
  of 66 + section 22, "42. Definitions" = footnote 4 + section 2). The
  Constitution prints the heading before the number ("Maintenance 9.") and
  has running headers ("CONSTITUTION OF PAKISTAN 15") instead of "Page N of M".

For PDF text the table of contents is the ground truth: every listed section
is searched for in the body, in order. ``detection`` = found / listed. A TOC
line that covers a range ("266-336. [Omitted.]") counts as one entry and is
usually not found. Callers treat a law below 90 % as "unsectioned" and keep
it as windowed chunks.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

DASH = r"(?:—|⸺|―|–|_{2,}|:-|-{2})"
PAGE = re.compile(r"\s*Page\s*\d+\s*of\s*\d+(?!\d)\s*")
FOOTNOTE_WORDS = (
    "For|Subs|Ins|Add|Omit|The\\s|Cl\\.|Section|Proviso|Re-?num|S\\.|Sub-|Sub\\s|See|Now|This\\s|Rep|Amend|"
    "Words|Para|Art|Item|Entry|Vide|Original|Declared|Brought|Renum|Ord|Sic|Comma|Semi|Full|Figure|"
    "Numeral|Clause|Deleted|Modified|Extended|Applied|Published|Gaz|Came|Inserted|Substituted|Explanation"
)
FOOTNOTE_START = re.compile(r"(?:(?<=[\s.;:\]\)_])|^)1\s?(?=(?:" + FOOTNOTE_WORDS + "))")
MARKER = re.compile(r"(?<![\w(./-])\d{1,2}\s?(?=\[)")          # "3[(iia) ..." -> "[(iia) ..."
TRAILING_MARKER = re.compile(r"(?<=\])\d{1,2}(?![\w.])")       # "[:]1" -> "[:]"
HEADING_NOISE = re.compile(
    r"\[?\b(?:CHAPTER|PART)\s+(?:[IVXLC]+[A-Z]?\b|\d{1,2}[A-Z]?\.?)(?:\s*[–—-])?(?:\s+(?:[A-Z][A-Z,'’\-]+|OF|AND|THE))*")
BODY_START = re.compile(r"(?:ACT|ORDINANCE|ORDER|REGULATION)\s+No\.?\s|An\s+(?:Act|Ordinance)\s+to\b|WHEREAS",
                        re.I)
SCHEDULE = re.compile(
    r"(?:THE\s+)?(?:(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+)?SCHEDULE"
    r"(?:\s*[–—-]?\s*([IVX]+(?=\b|[A-Z][a-z])|\d+\b))?")          # glued: "SCHEDULE IAd valorem fees"
ORDINAL = {w: i for i, w in enumerate(
    ("FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH", "EIGHTH", "NINTH", "TENTH"), 1)}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
SHORT_WORDS = {"a", "i", "an", "as", "at", "be", "by", "do", "go", "he", "if", "in", "is", "it", "me", "my", "no",
               "of", "on", "or", "so", "to", "up", "us", "we"}
CSV_SECTION = re.compile(r"^Section\s+(\d+[A-Z]{0,3})\s*[—–-]\s*(.*)$")
CSV_CHAPTER = re.compile(r"^Chapter\s+\S+\s*[—–-]")


@dataclass
class Section:
    section: str | None
    heading: str | None
    text: str


@dataclass
class Result:
    sections: list[Section]
    expected: int                   # sections the TOC / numbering implies
    found: int                      # of those, located in the body
    missing: list[str] = field(default_factory=list)
    method: str = ""

    @property
    def detection(self) -> float:
        return self.found / self.expected if self.expected else 0.0


# --------------------------------------------------------------------------- cleaning

def page_marker(text: str) -> re.Pattern:
    """'Page N of M' for this document. In glued text 'Page2of6622.' is page 2
    of 66 followed by section 22, so M is fixed to the document's page total
    (the most common M among unambiguous markers)."""
    clean = Counter(m.group(1) for m in re.finditer(r"Page\s*\d+\s*of\s*(\d+)(?=\s|$)", text))
    if not clean:
        return PAGE
    return re.compile(r"\s*Page\s*\d+\s*of\s*" + clean.most_common(1)[0][0] + r"\s*")


def page_spans(text: str) -> list[tuple[int, int]]:
    """Page breaks: 'Page N of M' markers, or else a running header such as
    'CONSTITUTION OF PAKISTAN 15' (an ALL-CAPS phrase + the page number, seen
    at least 5 times). Header page numbers must rise by 1-3, which splits a
    glued '1525A.' into page 15 + '25A.'."""
    spans = [(m.start(), m.end()) for m in page_marker(text).finditer(text)]
    if spans:
        return spans
    phrases = Counter(re.findall(r"\b([A-Z][A-Z ]{8,60}[A-Z]) \d", text))
    if not phrases or phrases.most_common(1)[0][1] < 5:
        return []
    phrase = phrases.most_common(1)[0][0]
    last = 0
    for m in re.finditer(re.escape(phrase) + r" (\d+)", text):
        digits = m.group(1)
        for n in range(1, len(digits) + 1):
            v = int(digits[:n])
            if last < v <= last + 3:
                spans.append((m.start(), m.start(1) + n))
                last = v
                break
    return spans


def remove_spans(text: str, spans: list[tuple[int, int]], offset: int = 0) -> str:
    out, pos = [], 0
    for s, e in spans:
        s, e = s - offset, e - offset
        if e <= 0 or s >= len(text):
            continue
        out.append(text[pos:max(s, 0)])
        out.append(" ")
        pos = max(e, 0)
    out.append(text[pos:])
    return "".join(out)


def strip_footnotes(text: str, spans: list[tuple[int, int]] | None = None) -> str:
    """Remove each page's footnote block: from the last '1<footnote word>' on a
    page up to that page's break (or the end of the text). Without page
    breaks nothing is cut (a footnote can't be told from the body)."""
    spans = page_spans(text) if spans is None else spans
    if not spans:
        return re.sub(r"\s+", " ", text).strip()
    out, pos = [], 0
    bounds = spans + [(len(text), len(text))]
    for start, end in bounds:
        seg = text[pos:start]
        last = None
        for m in FOOTNOTE_START.finditer(seg):
            last = m
        if last is not None:
            seg = seg[:last.start()]
        out.append(seg)
        out.append(" ")
        pos = end
    return re.sub(r"\s+", " ", "".join(out)).strip()


def clean_body(text: str) -> str:
    text = re.sub(r"_{3,}", " ", text)
    text = re.sub(r"\b(?:RGN Date:|Uploaded on|Update\s?d till|Last Amended on)\s*[\d][\d .\-]*", " ", text)
    text = MARKER.sub("", text)
    text = TRAILING_MARKER.sub("", text)
    text = re.sub(r"\s+([,.;:)\]])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def build_vocab(texts) -> Counter:
    vocab: Counter = Counter()
    for t in texts:
        vocab.update(w.lower() for w in re.findall(r"[A-Za-z]+", t))
    return vocab


def join_ocr_splits(text: str, vocab: Counter | None, min_count: int = 10) -> str:
    """Conservative OCR repair: 'wi fe' -> 'wife', 'Coun cil' -> 'Council'.
    Two adjacent alphabetic tokens are joined only when the joined word is
    common in the corpus (>= min_count) AND more common than each piece, so
    real word pairs ('a gain', 'the rein', 'in to') are left alone. A trailing
    1-2 letter fragment that isn't a word ('declare d', 'wish es') is judged
    on the first piece only, since 'd' and 'es' are common as clause labels."""
    if not vocab:
        return text

    def repl(m: re.Match) -> str:
        a, b = m.group(1), m.group(2)
        j = (a + b).lower()
        cj = vocab.get(j, 0)
        suffix = len(b) <= 2 and b.lower() not in SHORT_WORDS and not (
            b.lower() == "s" and m.string[m.end() + 1:m.end() + 2] == ".")      # "s. 5" is "section 5"
        if cj >= min_count and vocab.get(a.lower(), 0) < cj and (suffix or vocab.get(b.lower(), 0) < cj):
            return a
        return m.group(0)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"(?<![A-Za-z])([A-Za-z]+) (?=([A-Za-z]+)(?![A-Za-z]))", repl, text)
    return text


# --------------------------------------------------------------------------- numbering

def num_key(num: str) -> tuple[int, str]:
    m = re.match(r"(\d+)\s?([A-Z]*)", num)
    return (int(m.group(1)), m.group(2)) if m else (0, "")


def parse_toc(toc: str) -> list[tuple[str, str]]:
    """Section numbers and headings from a flattened CONTENTS block (page breaks
    already removed), keeping only a monotone sequence (so '10. Article 9 to
    apply' doesn't add a '9'). Dot leaders and page numbers are dropped."""
    toc = HEADING_NOISE.sub(" ", PAGE.sub(" ", toc))
    toc = re.sub(r"(?:\s*\.){4,}\s*\d{1,4}\b", ". ", toc)          # "Equality of citizens ....... 15"
    toc = re.sub(r"\b(?:SECTIONS?|ARTICLES?|CONTENTS|PREAMBLE)\b\s*[.:]?", " ", toc)
    # Candidates may overlap: in glued text ("section 38 Jurisdiction" is
    # "section 3" + "8 Jurisdiction") a number can start right after a digit or
    # letter; such a "glued" candidate is accepted only as the very next number.
    cands = list(re.finditer(r"(?=((\d{1,3}(?:\s?[A-Z]{1,2}(?=\.))?)\s?\.?\s*)[\[A-Z\"“'‘(])", toc))
    keys = [num_key(m.group(2)) for m in cands]
    picked, last = [], (0, "")
    for i, m in enumerate(cands):
        if picked and m.start() < picked[-1].end(1):
            continue
        k = keys[i]
        glued = m.start() > 0 and toc[m.start() - 1].isalnum()
        if glued and toc[m.start() - 1].isdigit() and re.match(r"(?:THE\s+)?[A-Z]{3,}\b", toc[m.end(1):]):
            continue                    # "XXVI of 1937. THE DISSOLUTION ..." is a year, not section 7
        if not k > last:
            continue
        near = k[0] <= last[0] + (1 if glued else 5)
        # A bigger jump (a run of sections the TOC prints as one line, or a
        # number we failed to read) is accepted only if its successor follows.
        nxt = [keys[j] for j in range(i + 1, min(i + 8, len(keys)))]
        follows = [n for n in (k[0] + 1, k[0] + 2) if any(x[0] == n for x in nxt)]
        lettered = any(x[0] == k[0] and x[1] > k[1] for x in nxt)
        # ... or, after an unreadable range ("266336.[Omitted.]" is 266-336),
        # any jump if the next two numbers follow.
        confirmed = not glued and ((k[0] <= last[0] + 60 and (follows[:1] == [k[0] + 1] or lettered))
                                   or len(follows) == 2)
        if near or confirmed:
            picked.append(m)
            last = k
    out = []
    for i, m in enumerate(picked):
        end = picked[i + 1].start() if i + 1 < len(picked) else len(toc)
        head = toc[m.end(1):end]
        # drop a running title after the last entry ("... Repeal. THE ACT, 1962" or "Savings THE WEST PAKISTAN ...")
        head = re.split(r"\.\s+(?=(?:THE\s+)?[A-Z]{3,}\b)|\s+(?=(?:THE\s+)?[A-Z]{3,}(?:\s+[A-Z(),]{2,}){2,})", head)[0]
        head = re.sub(r"\s+\.", ".", head).strip(" .")
        head = re.split(r"\.\s+(?=[A-Z])", head)[0]      # drop a sub-heading listed after it
        out.append((m.group(2).replace(" ", ""), head))
    return out


def _num_pat(num: str, strict: bool = False) -> str:
    """Not strict (the heading confirms the match): any prefix is allowed,
    since a footnote marker is often glued on ("42. Definitions" is footnote 4
    + section 2). strict (number alone): it must not follow a letter or digit."""
    digits = str(num_key(num)[0])
    behind = r"(?<![A-Za-z0-9,/-])" if strict else ""
    return behind + re.escape(digits) + r"\s?" + re.escape(num[len(digits):])


def _text_start(body: str, start: int, head: str) -> int:
    """Where a section's text begins: after '[bracketed heading]', else after
    the heading's dash, else after its first full stop."""
    m = re.match(r"\d{1,3}\s?[A-Z]{0,3}\s?\.?\s*", body[start:])
    i = start + (m.end() if m else 0)
    if body.startswith("[", i):
        close = body.find("]", i, i + 300)
        if close > 0:
            return close + 1 + (len(re.match(r"\s*\.?", body[close + 1:]).group(0)))
    # The dash must sit at the heading's end, not later in the text ("(1) The
    # following enactments are hereby repealed:__").
    d = re.search(r"\.?\s*" + DASH, body[i: i + len(head) + 25])
    if d:
        return i + d.end()
    p = re.search(r"[.:]\s", body[i: i + len(head) + 80])
    return i + (p.end() if p else 0)


def _fuzzy(head: str, n: int = 14) -> str:
    letters = re.sub(r"[^a-z]", "", head.lower())[:n]
    return r"[^a-z]{0,3}".join(re.escape(c) for c in letters)


# --------------------------------------------------------------------------- splitters

def split_section_table(text: str) -> Result:
    sections: list[Section] = []
    cur: Section | None = None
    for line in text.splitlines():
        line = line.strip()
        m = CSV_SECTION.match(line)
        if m:
            cur = Section(m.group(1), m.group(2).strip(" .") or None, "")
            sections.append(cur)
        elif CSV_CHAPTER.match(line) or not line:
            continue
        elif cur is not None:
            cur.text = (cur.text + " " + line).strip()
    nums = [num_key(s.section) for s in sections]
    ints = sorted({k[0] for k in nums})
    expected_ints = set(range(1, ints[-1] + 1)) if ints else set()
    missing = sorted(expected_ints - set(ints))
    lettered = {k for k in nums if k[1]}
    expected = len(expected_ints) + len(lettered)
    found = len(expected_ints & set(ints)) + len(lettered)
    return Result(sections, expected, found, [str(i) for i in missing], "section_table")


def _locate(body: str, toc: list[tuple[str, str]], heading_first: bool):
    """Find each TOC entry in the body, in order. Returns (starts, missing,
    number found with their heading), starts = [(record start, text start, num, heading)].

    heading_first=False: '9. Maintenance.—(1) ...' (Acts and Ordinances).
    heading_first=True:  'Maintenance 9. (1) ...' (the Constitution prints the
    article heading as a margin note before the number)."""
    hits: dict[int, tuple[int, int]] = {}
    pos = 0
    confirmed = 0
    # Pass 1: number + the TOC heading's first letters, in order.
    for i, (num, head) in enumerate(toc):
        fz = _fuzzy(head)
        if not fz:
            continue
        if heading_first:
            pat = fz + r".{0,%d}?" % (len(head) + 10) + r"(?<![0-9])" + _num_pat(num) + r"\s?\.(?!\d)\s*"
        else:
            pat = _num_pat(num) + r"\s?\.?\s*\[?\s*" + fz
        m = re.compile(pat, re.I).search(body, pos)
        if m:
            hits[i] = (m.start(), m.end() if heading_first else _text_start(body, m.start(), head))
            pos = m.end()
            confirmed += 1
    # Pass 2: a missed section whose body heading differs from the TOC
    # ("12. Omitted" vs "12. [Amendment of ...] Omitted by ..."): accept the
    # bare number + capital/bracket, but only between its found neighbours.
    for i, (num, head) in enumerate(toc):
        if i in hits:
            continue
        lo = max((hits[j][0] for j in hits if j < i), default=0)
        hi = min((hits[j][0] for j in hits if j > i), default=len(body))
        m = re.compile(_num_pat(num, strict=True) + r"\s?\.\s*(?=[\[A-Z(])").search(body, lo + 1, hi)
        if m:
            hits[i] = (m.start(), m.end() if heading_first else _text_start(body, m.start(), head))
    starts = sorted((hits[i][0], hits[i][1], num, head) for i, (num, head) in enumerate(toc) if i in hits)
    missing = [num for i, (num, _h) in enumerate(toc) if i not in hits]
    return starts, missing, confirmed


def split_pdf(text: str, vocab: Counter | None = None) -> Result:
    text = re.sub(r"\s+", " ", text)
    spans = page_spans(text)
    m_c = re.search(r"CONTENTS", text[:20000])
    toc_start = m_c.end() if m_c else 0
    m_b = BODY_START.search(text, toc_start)
    toc_end = m_b.start() if m_b and m_c else 0
    toc = parse_toc(remove_spans(text[toc_start:toc_end], spans, toc_start)) if m_c else []

    body = strip_footnotes(text[toc_end:], [(s - toc_end, e - toc_end) for s, e in spans if s >= toc_end])
    starts: list[tuple[int, int, str, str]] = []      # (start, text_start, num, heading)
    missing: list[str] = []
    if toc:
        # Keep the layout that finds more sections; on a tie, the one whose
        # headings confirmed more of them.
        best = max(((*_locate(body, toc, hf), hf) for hf in (False, True)), key=lambda b: (len(b[0]), b[2]))
        starts, missing, _confirmed, heading_first = best
        expected, method = len(toc), "pdf_toc_heading_first" if heading_first else "pdf_toc"
    else:
        # No CONTENTS: accept "N. Heading.—" in increasing order.
        last = (0, "")
        for m in re.finditer(r"(?<![\w.,/-])(\d{1,3}[A-Z]{0,3})\s?\.\s*\[?\s*([A-Z][^—⸺―]{1,150}?)\s?\.?\s*" + DASH, body):
            k = num_key(m.group(1))
            if k > last and k[0] <= last[0] + 5:
                starts.append((m.start(), m.end(), m.group(1), m.group(2).strip(" .")))
                last = k
        ints = [num_key(s[2])[0] for s in starts]
        lettered = sum(1 for s in starts if num_key(s[2])[1])
        expected = max(ints) + lettered if ints else 0
        missing =[str(i) for i in sorted(set(range(1, max(ints) + 1)) - set(ints))] if ints else []
        method = "pdf_numbering"

    sections: list[Section] = []
    end_of_sections = len(body)
    sched: list[re.Match] = []
    if starts:
        sched = list(SCHEDULE.finditer(body, starts[-1][1]))
        if sched:
            end_of_sections = sched[0].start()
    for i, (_s, ts, num, head) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else end_of_sections
        body_text = _clean(HEADING_NOISE.sub(" ", body[ts:end]), vocab)
        if not body_text:                 # two entries matched at one place: not really found
            missing.append(num)
            continue
        sections.append(Section(num, _clean(head, vocab), body_text))
    # A new schedule starts only at the next number (FIRST, then SECOND ...);
    # repeats ("FIRST SCHEDULE—contd." page headers) and stray numbers inside
    # forms stay part of the current schedule.
    heads: list[tuple[int, int, int | None]] = []          # (start, text start, number)
    for m in sched:
        n = ORDINAL.get(m.group(1) or "") or ROMAN.get(m.group(2) or "") or (
            int(m.group(2)) if (m.group(2) or "").isdigit() else None)
        prev = heads[-1][2] if heads else None
        if not heads or (n is not None and prev is not None and n == prev + 1):
            heads.append((m.start(), m.end(), n))
    for i, (_s, ts, n) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(body)
        label = "Schedule" if len(heads) == 1 and not n else f"Schedule {n or i + 1}"
        sections.append(Section(label, None, _clean(body[ts:end], vocab)))
    found = sum(1 for s in sections if s.section and s.section[0].isdigit())
    return Result(sections, expected, found, missing, method)


def _clean(s: str, vocab: Counter | None) -> str:
    if not s:
        return s
    s = re.sub(r"(?<=[.;:\]])\s?\d{1,2}$", "", s.strip())     # a footnote marker glued to the next number
    s = re.sub(r"\s*\d{0,2}\[$", "", s)                        # "2[" opening the next section's amendment
    return join_ocr_splits(clean_body(s), vocab).strip(" .:")


def windows(text: str, size: int = 1200) -> list[str]:
    """Fallback for unsectioned laws: ~size-character windows cut at whitespace."""
    text = re.sub(r"\s+", " ", text).strip()
    out, pos = [], 0
    while pos < len(text):
        end = min(len(text), pos + size)
        if end < len(text):
            sp = text.rfind(" ", pos + size // 2, end)
            end = sp if sp > 0 else end
        out.append(text[pos:end].strip())
        pos = end
    return [w for w in out if w]


def split(text: str, source_type: str, vocab: Counter | None = None) -> Result:
    if source_type == "statute_section_table":
        return split_section_table(text)
    return split_pdf(text, vocab)
