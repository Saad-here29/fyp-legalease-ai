"""Reasoning layer for Document Analysis (kb-v2 C4, settings.REASONING_V2).

After text extraction and the existing NER + summary, ONE extra model call
returns a strict JSON brief: document type, issues, arguments by party, the
court's reasoning (in order), holding or outcome, statutes cited, strong and
weak points, risks and open questions. Every item must carry "evidence", a
short verbatim quote from the document.

Then deterministic checks, no second model call:
  (a) each evidence quote must be found in the document text (whitespace,
      case, punctuation and OCR hyphen splits normalised); an item whose
      quote isn't found is dropped and counted;
  (b) dates, case numbers, FIR numbers and section numbers an item mentions
      must exist in the document text or the NER output (else the item is
      dropped); a person's name that isn't there is flagged;
  (c) each statute cited is looked up in the knowledge-base records (exact
      Act + section, app/kb/exact_lookup.py): verified (with the record's
      link), not found (we hold the Act, not that section) or not checked
      (we don't hold the Act);
  (d) with JUDGMENTS_V2 on, each issue gets up to 2 related past judgments
      (score >= REASONING_RELATED_MIN): context, never claims about this
      document.

Long documents are not cut blindly: the head, the tail and the paragraphs
holding NER entities or numbered findings are kept, to fit
REASONING_INPUT_TOKENS, and the output says only part was analysed.

A failed call, a 429 that outlasts the back-off, or a reply that isn't JSON
gives reasoning = None with a plain-language reason; the rest of the
analysis is unaffected.
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from collections.abc import Callable
from functools import lru_cache

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailable
from app.core.logging import logger

DISCLAIMER = "AI-assisted analysis; verify against the original"
LIST_FIELDS = ("issues", "court_reasoning", "strong_points", "weak_points", "risks", "open_questions")
MIN_QUOTE_WORDS = 3

SYSTEM = (
    "You are a careful Pakistani legal analyst preparing a brief for a lawyer. Reply with ONE JSON object and "
    "nothing else.\n"
    "RULES:\n"
    "1. Use only the document below. No outside law, no facts, cases or sections that are not in it.\n"
    "2. Every item needs \"evidence\": an exact quotation copied word for word from the document (5 to 40 "
    "words) that supports the item. If you cannot quote the document for an item, leave the item out.\n"
    "3. Keep each \"text\" to one short sentence in plain English.\n"
    "4. Never invent parties, dates, case numbers, FIR numbers or section numbers.\n"
    "5. Use [] or null when the document says nothing on a point.\n"
    "6. Weak points, risks and open questions are about THIS document's own gaps: events with no date, amounts "
    "or dates that don't match each other, annexures referred to but not numbered or attached, blanks left to "
    "fill, facts asserted without the document saying how they are known. No generic checklist items. Never say "
    "something is missing, absent or not stated unless you have read the whole text you were given and it is "
    "really not there.\n"
    "7. You may be given one part of a longer document: report only what this part says."
)

SCHEMA = """Return JSON with exactly these keys:
{
  "document_type": {"text": "what the document is, e.g. order granting bail", "evidence": "..."},
  "issues": [{"text": "a legal question the document decides or raises", "evidence": "..."}],
  "arguments": {"<party as the document names it: petitioner, appellant, state, respondent, complainant>":
                [{"text": "an argument made for that party", "evidence": "..."}]},
  "court_reasoning": [{"text": "one step of the court's reasoning, in the order the court gives it", "evidence": "..."}],
  "holding_or_outcome": {"text": "what was decided", "evidence": "..."},
  "statutes_cited": [{"act": "the Act as named in the document", "section": "one section number", "evidence": "..."}],
  "strong_points": [{"text": "a point in the document that supports the outcome", "evidence": "..."}],
  "weak_points": [{"text": "a gap or weakness in this document itself (undated event, amounts that don't match, annexure not numbered, blank)", "evidence": "..."}],
  "risks": [{"text": "something in this document that could go wrong for a party relying on it", "evidence": "..."}],
  "open_questions": [{"text": "a fact this document leaves unresolved", "evidence": "..."}]
}"""


# --------------------------------------------------------------------------- tokens

@lru_cache(maxsize=1)
def _encoder():
    try:
        import tiktoken
        return tiktoken.get_encoding("o200k_base")
    except Exception:  # noqa: BLE001 — offline: estimate instead
        return None


def tokens(text: str) -> int:
    enc = _encoder()
    return len(enc.encode(text)) if enc is not None else int(len(text) / 3.5) + 1


# --------------------------------------------------------------------------- C10: whole-document coverage

_UNIT_START = re.compile(r"^\s*(?:\(?\d{1,3}[.)]\s|[A-Z][A-Z .,'()/&-]{3,80}$)")
_PRIORITY = re.compile(
    r"\bpray(?:ed|er|s)?\b|\brelief\b|\bwherefore\b|it is,? therefore|\bit is (?:hereby )?ordered\b|\bdecree[ds]?\b|"
    r"\bdismissed\b|\ballowed\b|\bset aside\b|\bheld\b|"
    r"\b(?:Act|Ordinance|Order|Regulations?|Code|Rules)\s*,?\s*(?:18|19|20)\d\d\b", re.I)


def units(text: str) -> list[str]:
    """Paragraph-sized pieces of the document, in order: a new piece starts at a
    blank line, a numbered paragraph ("12.", "(3)") or a heading line in
    capitals ("PRAYER"), so PDF text without blank lines still splits."""
    out, cur = [], []
    for line in (text or "").splitlines():
        if cur and (not line.strip() or _UNIT_START.match(line)):
            out.append("\n".join(cur))
            cur = []
        if line.strip():
            cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


def _split_big(unit: str, budget: int) -> list[str]:
    """A piece over the budget, split at sentence ends."""
    if tokens(unit) <= budget:
        return [unit]
    parts, cur = [], ""
    for sent in re.split(r"(?<=[.;:])\s+", unit):
        if cur and tokens(cur + " " + sent) > budget:
            parts.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        parts.append(cur)
    return parts


def plan(text: str, budget: int | None = None, max_calls: int | None = None) -> tuple[list[str], dict]:
    """The parts of the document to send, one per model call, and the coverage.
    Up to max_calls parts of at most `budget` tokens cover the whole text (about
    12,000 words with the defaults). A longer document keeps its first and last
    parts and the parts with the prayer/relief, statute references and operative
    words, in document order; coverage then says what share was sent."""
    budget = budget or settings.REASONING_INPUT_TOKENS
    max_calls = max_calls or settings.REASONING_MAX_CALLS
    total = tokens(text)
    if total <= budget:
        return [text], {"partial": False, "note": None, "parts": 1, "parts_total": 1,
                        "tokens_analysed": total, "tokens_total": total, "percent": 100}
    segs, cur = [], []
    for u in (p for unit in units(text) for p in _split_big(unit, budget)):
        if cur and tokens("\n".join(cur + [u])) > budget:
            segs.append("\n".join(cur))
            cur = []
        cur.append(u)
    if cur:
        segs.append("\n".join(cur))
    chosen = list(range(len(segs)))
    if len(segs) > max_calls:
        score = {i: len(_PRIORITY.findall(s)) for i, s in enumerate(segs)}
        must = {0, len(segs) - 1}
        rest = sorted((i for i in range(len(segs)) if i not in must), key=lambda i: (-score[i], i))
        chosen = sorted(must | set(rest[: max_calls - len(must)]))
    sent = sum(tokens(segs[i]) for i in chosen)
    pct = round(100 * sent / total) if total else 100
    partial = len(chosen) < len(segs)
    return [segs[i] for i in chosen], {
        "partial": partial, "parts": len(chosen), "parts_total": len(segs),
        "tokens_analysed": sent, "tokens_total": total, "percent": pct,
        "note": (f"Only part of this long document was analysed: about {pct}% of it, in {len(chosen)} of "
                 f"{len(segs)} parts (the beginning, the end, and the parts with the prayer or relief, statute "
                 "references and orders). Items can only come from those parts.") if partial else None}


class Pacer:
    """Keeps model calls under REASONING_TPM tokens in any 60 s (Groq: 8,000 a
    minute counts prompt + reply cap). spend(cost) waits until the call fits."""

    def __init__(self, tpm: int, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.tpm, self.clock, self.sleep = tpm, clock, sleep
        self.log: list[tuple[float, int]] = []
        self.waited = 0.0

    def spend(self, cost: int) -> None:
        while True:
            now = self.clock()
            self.log = [(t, c) for t, c in self.log if now - t < 60]
            if not self.log or sum(c for _t, c in self.log) + cost <= self.tpm:
                break
            wait = 60 - (now - self.log[0][0]) + 0.5
            logger.info(f"Reasoning: waiting {wait:.0f} s for the per-minute token limit")
            self.sleep(wait)
            self.waited += wait
            if self.clock() - now < wait / 2:
                self.log.pop(0)            # the clock didn't move (a stand-in clock): count the wait as done
        self.log.append((self.clock(), cost))


def merge(replies: list[dict]) -> dict:
    """One brief from the replies for each part, in document order: lists
    joined (the same text once), arguments joined per party, the first document
    type and the last holding (the operative part comes last)."""
    out: dict = {"document_type": None, "holding_or_outcome": None, "arguments": {}, "statutes_cited": []}
    for f in LIST_FIELDS:
        out[f] = []
    seen: set[tuple[str, str]] = set()

    def add(dst: list, items) -> None:
        for it in items if isinstance(items, list) else []:
            if not isinstance(it, dict):
                continue
            key = (str(it.get("text") or it.get("act")), str(it.get("section") or it.get("evidence")))
            if key not in seen:
                seen.add(key)
                dst.append(it)
    for r in replies:
        if out["document_type"] is None and isinstance(r.get("document_type"), dict):
            out["document_type"] = r["document_type"]
        if isinstance(r.get("holding_or_outcome"), dict):
            out["holding_or_outcome"] = r["holding_or_outcome"]
        for f in LIST_FIELDS:
            add(out[f], r.get(f))
        add(out["statutes_cited"], r.get("statutes_cited"))
        for party, items in (r.get("arguments") or {}).items() if isinstance(r.get("arguments"), dict) else []:
            add(out["arguments"].setdefault(str(party).strip().lower(), []), items)
    return out


# --------------------------------------------------------------------------- C10: statutes found in the text

_STATUTE_NAME = re.compile(
    r"\b((?:Code|Constitution)\s+of\s+(?:the\s+)?(?:[A-Z][\w'’\-]*\s*(?:(?:of|and)\s+(?=[A-Z]))?){1,6}?"
    r"|(?:[A-Z][\w'’\-().]*\s+(?:(?:of|and|the|for|on|in|to|&)\s+)*){0,9}(?:Act|Ordinance|Order|Regulations?|Code|Rules))"
    r"\s*,?\s*(?:\(\s*[IVXLC]+\s+of\s+(?:18|19|20)\d\d\s*\)\s*,?\s*)?((?:18|19|20)\d\d)\b")
# "First Schedule to the Limitation Act" -> "Limitation Act"; "Code of Civil Procedure" stays whole.
_LEADING_REF = re.compile(r"^(?:Article|Order|Rule|Section|Schedule|First|Second|Third|Part|Chapter|Clause)\b.*?"
                          r"\b(?:of|to|under|in)\s+(?:the\s+)?(?=[A-Z])")
_SECTION_BEFORE = re.compile(r"\b(?:sections?|s\.|ss\.)\s*(\d{1,4}[A-Z]?(?:\s*\(\d+\))?)\s*(?:of|under)\s+(?:the\s+)?$",
                             re.I)


def statutes_in_text(text: str) -> list[dict]:
    """Every statute the document names with its year ("Specific Relief Act,
    1877"), with the section when one is named right before it ("section 42 of
    the ..."), read with a pattern from the full text; the quote is the words
    found."""
    flat = " ".join((text or "").split())
    out, seen = [], set()
    for m in _STATUTE_NAME.finditer(flat):
        name = _LEADING_REF.sub("", m.group(1)).strip()
        name = re.sub(r"^(?:The|the)\s+", "", name)
        if len(name.split()) < 2 or re.match(r"(?:Article|Order|Rule|Section|Schedule|First|Second)\b", name):
            continue
        title = f"{name}, {m.group(2)}"
        sec = _SECTION_BEFORE.search(flat[max(0, m.start() - 60):m.start()])
        section = re.sub(r"\s*\(\d+\)", "", sec.group(1)) if sec else None
        key = (title.lower(), section)
        if key in seen:
            continue
        seen.add(key)
        start = max(0, m.start() - (len(sec.group(0)) if sec else 0))
        out.append({"act": title, "section": section, "evidence": flat[start:m.end()].strip()})
    return out


def law_status(act: str) -> dict:
    """An Act named without a section: is the law in the knowledge base?"""
    from app.kb import catalog, exact_lookup
    try:
        for title, pats in exact_lookup._laws().items():
            if any(p.search(act) for p in pats) and (not re.search(r"\d{4}", title)
                                                     or re.search(r"\d{4}", title).group(0) in act):
                law = next((v for v in catalog.data()["laws"].values() if v["title"] == title), None)
                return {"status": "law_held", "kb_title": title, "kb_law_id": law["doc_id"] if law else None}
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Law lookup failed for {act}: {e}")
    return {"status": "not_checked", "note": "this Act isn't in the LegalEase knowledge base"}


# --------------------------------------------------------------------------- C10: "X is missing" claims

_ABSENCE = re.compile(
    r"\b(?:no|missing|absence of|absent|lacks?|lacking|without (?:a|an|any)|"
    r"(?:does|do|did) not (?:contain|include|mention|state|specify|provide|attach|annex|seek|claim|pray for)|"
    r"fails? to (?:mention|state|include|specify|annex|attach|seek|claim))\s+"
    r"(?:(?:any|a|an|the|clear|specific|proper|explicit|formal|express)\s+)*"
    r"([a-z][a-z'\-]+(?:\s+(?:for|of|on|to)\s+(?:the\s+)?[a-z][a-z'\-]+)?"
    # "no date is given for the recovery memo": the date is the recovery memo's
    r"(?:\s+(?:is|are|was|were)\s+(?:not\s+)?(?:given|mentioned|stated|specified|shown|provided)\s+(?:for|of|about)"
    r"\s+(?:the\s+)?[a-z][a-z'\-]+(?:\s+[a-z][a-z'\-]+)?)?)"
    r"|\b([a-z][a-z'\-]+(?:\s+[a-z][a-z'\-]+)?)\s+(?:is|are)\s+(?:missing|absent|not (?:mentioned|stated|specified|"
    r"included|attached|annexed|given|sought|claimed))", re.I)
_ABSENCE_STOP = {"for", "of", "on", "to", "the", "any", "mention", "reference", "details", "detail", "statement",
                 "clause", "clauses", "standard", "explicit", "clear", "specific", "proper", "formal", "express",
                 "is", "are", "was", "were", "not", "given", "mentioned", "stated", "specified", "shown", "provided",
                 "about", "and", "or", "in"}
_NEAR = 40                     # the words of one "no X" claim must be found within this many words of each other


def _doc_words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", (text or "").lower())


def _same_word(w: str, d: str) -> bool:
    return d.startswith(w[:6]) if len(w) >= 6 else d == w or d == w + "s" or w == d + "s"


def _found_together(words: list[str], doc_words: list[str]) -> bool:
    spots = [[i for i, d in enumerate(doc_words) if _same_word(w, d)] for w in words]
    if not all(spots):
        return False
    return any(all(any(abs(j - i) <= _NEAR for j in other) for other in spots[1:]) for i in spots[0])


def absence_contradicted(point: str, doc_words: list[str]) -> list[str]:
    """The things a "no X" / "X is missing" point says are absent but the
    document does contain (each word of X found near the others, plural or
    verb forms matched on the first six letters); [] when none."""
    found = []
    for m in _ABSENCE.finditer(point or ""):
        phrase = (m.group(1) or m.group(2) or "").lower()
        words = [w for w in re.findall(r"[a-z]+", phrase) if w not in _ABSENCE_STOP and len(w) >= 3]
        if words and _found_together(words, doc_words):
            found.append(phrase)
    return found


def drop_contradicted_absences(points: list[str], doc_text: str) -> tuple[list[str], list[str]]:
    """(kept, removed) review points: removed ones say something is missing
    that the document contains ("no prayer for costs" in a document asking for
    dismissal "with costs")."""
    words = _doc_words(doc_text)
    kept, removed = [], []
    for p in points:
        (removed if absence_contradicted(p, words) else kept).append(p)
    return kept, removed


# --------------------------------------------------------------------------- the call

def prompt_for(doc_text: str, hint: str, part: tuple[int, int] | None = None) -> str:
    where = (f"This is part {part[0]} of {part[1]} of the document, in order. If this part holds the prayer or "
             "relief sought, include it as an argument of the party asking for it.\n\n") if part and part[1] > 1 else ""
    return (f"{SCHEMA}\n\n{where}Document type hint from the uploader: {hint}\n\n--- DOCUMENT ---\n{doc_text}\n"
            "--- END ---")


def parse_json(raw: str) -> dict:
    s = (raw or "").strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    a, b = s.find("{"), s.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("no JSON object in the reply")
    data = json.loads(s[a:b + 1])
    if not isinstance(data, dict):
        raise ValueError("the reply is not a JSON object")
    return data


def call_model(ai, prompt: str, *, sleep: Callable[[float], None] = time.sleep) -> str:
    """One JSON completion, retried with back-off on 429 (the provider's
    retry-after when given, else 5 s, 10 s, 20 s) up to REASONING_MAX_WAIT s."""
    from app.ai.client import RateLimitedError
    waited, backoff = 0.0, [5.0, 10.0, 20.0]
    attempt = 0
    while True:
        try:
            return ai.complete_json(prompt, SYSTEM, max_tokens=settings.REASONING_MAX_TOKENS)
        except RateLimitedError as e:
            wait = e.retry_after if e.retry_after is not None else backoff[min(attempt, len(backoff) - 1)]
            if wait > 120:
                raise RateLimitedError("daily limit", wait) from e
            if waited + wait > settings.REASONING_MAX_WAIT:
                raise
            logger.info(f"Reasoning: rate limited, waiting {wait:.0f} s (attempt {attempt + 1})")
            sleep(wait)
            waited += wait
            attempt += 1


# --------------------------------------------------------------------------- checks

def norm(s: str) -> str:
    """Lowercase letters and digits only; a hyphen between letters (with or
    without a line break after it, "life-\\nthreatening") is dropped."""
    s = (s or "").replace("­", "").lower()
    s = re.sub(r"(?<=[a-z])-\s*(?=[a-z])", "", s)
    return " ".join(re.sub(r"[^0-9a-z]+", " ", s).split())


def quote_found(quote: str, doc_norm: str) -> bool:
    """The quote (or each "…"-separated part, in order) is in the document.
    Compared without spaces, so a word split or joined differently by the PDF
    ("life- threatening", "lifethreatening", "life threatening") still
    matches; the quote must still have at least MIN_QUOTE_WORDS words."""
    parts = [norm(p) for p in re.split(r"\.\.\.|…", quote or "")]
    parts = [p for p in parts if p]
    if not parts or sum(len(p.split()) for p in parts) < MIN_QUOTE_WORDS:
        return False
    hay = doc_norm.replace(" ", "")
    pos = 0
    for p in parts:
        i = hay.find(p.replace(" ", ""), pos)
        if i < 0:
            return False
        pos = i + len(p.replace(" ", ""))
    return True


_MONTHS = {m: i + 1 for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct",
                                            "nov", "dec"))}
_NUMERIC_DATE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b")
_DAY_MONTH = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")
_MONTH_DAY = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")


def _y(y: str) -> int:
    n = int(y)
    return n + 2000 if n < 100 else n


def dates_in(text: str) -> set[tuple[int, int, int]]:
    out = set()
    for d, m, y in _NUMERIC_DATE.findall(text or ""):
        out.add((_y(y), int(m), int(d)))
    for d, mon, y in _DAY_MONTH.findall(text or ""):
        if mon[:3].lower() in _MONTHS:
            out.add((int(y), _MONTHS[mon[:3].lower()], int(d)))
    for mon, d, y in _MONTH_DAY.findall(text or ""):
        if mon[:3].lower() in _MONTHS:
            out.add((int(y), _MONTHS[mon[:3].lower()], int(d)))
    return out


# "Criminal Petition No.187-P of 2026", "Crl.P. 187-P/2026", "Cr.MB No.1862-P/26", "187-P/2026"
_CASE_NO = re.compile(r"\b(?:No\.?\s*)?(\d{1,6}(?:-[A-Z]{1,2})?)\s*(?:/|\bof\b)\s*(\d{4}|\d{2})\b")
_FIR = re.compile(r"\bF\.?\s?I\.?\s?R\.?\s*(?:No\.?)?\s*(\d{1,6})", re.I)
_SECTIONS = re.compile(r"\b(?:sections?|secs?\.?|s\.|u/s\.?)\s*(\d{1,4}[A-Z]?(?:\s*(?:/|,|and|&)\s*\d{1,4}[A-Z]?)*)",
                       re.I)
_NAME = re.compile(r"\b(?:Mst\.\s|Mr\.\s|Syed\s)?([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,3})\b")
_LEADING = {"whether", "the", "a", "an", "in", "on", "at", "for", "if", "when", "his", "her", "their", "counsel",
            "according", "as", "after", "before", "since", "while", "that", "this", "both", "all", "no", "did", "does",
            "was", "is", "who", "why", "how", "what", "can", "could", "should", "would", "may", "although", "but"}
_NOT_NAMES = {"supreme", "court", "high", "pakistan", "state", "petitioner", "respondent", "appellant", "complainant",
              "trial", "medical", "board", "standing", "police", "station", "district", "learned", "counsel",
              "the", "criminal", "petition", "appeal", "civil", "code", "penal", "procedure", "act", "order",
              "ordinance", "khyber", "pakhtunkhwa", "punjab", "sindh", "balochistan", "islamabad", "peshawar",
              "lahore", "karachi", "quetta", "federal", "shariat", "government", "judge", "justice", "under",
              "section", "this", "that", "both", "courts", "below", "further", "inquiry", "bail"}


def mention_problems(item_text: str, doc_text: str, doc_norm: str, ner_texts: list[str]) -> tuple[list, list]:
    """(missing references -> drop, unknown names -> flag) in an item's text."""
    raw = " ".join((doc_text or "").split())
    ner_norm = norm(" | ".join(ner_texts))
    doc_dates = dates_in(raw) | dates_in(" ".join(ner_texts))
    missing, names = [], []
    for m in _NUMERIC_DATE.finditer(item_text):
        if dates_in(m.group(0)) - doc_dates:
            missing.append(m.group(0))
    for rx in (_DAY_MONTH, _MONTH_DAY):
        for m in rx.finditer(item_text):
            if dates_in(m.group(0)) and dates_in(m.group(0)) - doc_dates:
                missing.append(m.group(0))
    for m in _CASE_NO.finditer(item_text):
        num, year = m.group(1), m.group(2)
        if _NUMERIC_DATE.search(m.group(0)):
            continue
        pat = re.escape(num) + r".{0,25}?\b(?:\d{2})?" + re.escape(year[-2:]) + r"\b"
        if not re.search(pat, raw, re.I) and not re.search(pat, " ".join(ner_texts), re.I):
            missing.append(m.group(0).strip())
    for m in _FIR.finditer(item_text):
        if not re.search(r"F\.?\s?I\.?\s?R\.?.{0,12}?\b" + re.escape(m.group(1)) + r"\b", raw, re.I):
            missing.append(m.group(0).strip())
    for m in _SECTIONS.finditer(item_text):
        for n in re.findall(r"\d{1,4}[A-Z]?", m.group(1)):
            if not re.search(r"(?<![\d])" + re.escape(n) + r"(?![\d])", raw):
                missing.append(f"section {n}")
    for m in _NAME.finditer(item_text):
        words = m.group(1).split()
        while words and words[0].lower() in _LEADING:          # "Whether Imran Ahmed" -> "Imran Ahmed"
            words.pop(0)
        if len(words) < 2 or any(w.lower() in _NOT_NAMES for w in words):
            continue
        name = " ".join(words)
        n = norm(name)
        if n.replace(" ", "") not in doc_norm.replace(" ", "") and n not in ner_norm:
            names.append(name)
    return missing, names


def statute_status(act: str, section: str) -> dict:
    """(c): the knowledge-base record for this Act and section, if we hold it."""
    from app.kb import catalog, exact_lookup
    try:
        refs = exact_lookup.find_refs(f"section {section} of the {act}")
        if not refs:
            return {"status": "not_checked", "note": "this Act isn't in the LegalEase knowledge base"}
        title, sec = refs[0]
        rid = exact_lookup._section_index().get(title, {}).get(sec)
        if not rid:
            return {"status": "not_found", "kb_title": title,
                    "note": f"no section {section} found in our copy of the {title}"}
        rec = catalog.data()["records"][rid]
        return {"status": "verified", "kb_title": title, "kb_record_id": rid, "kb_law_id": rec.get("_law"),
                "heading": rec.get("heading")}
    except Exception as e:  # noqa: BLE001 — a lookup problem must not sink the brief
        logger.warning(f"Statute lookup failed for {act} s.{section}: {e}")
        return {"status": "not_checked", "note": "the knowledge base couldn't be checked"}


def related_cases(issue: str) -> list[dict]:
    """(d): up to 2 past judgments for an issue (JUDGMENTS_V2 only)."""
    if not settings.JUDGMENTS_V2:
        return []
    from app.kb import judgment_search
    from app.kb import judgments as jd
    try:
        hits = judgment_search.search(issue, top_k=6,
                                      min_score=max(settings.REASONING_RELATED_MIN, settings.JUDGMENTS_CHAT_MIN))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Related cases failed: {e}")
        return []
    out = []
    for h in hits:
        name, court = (h.get("display_name") or "").strip(), (h.get("court") or "").strip()
        para = h.get("paragraph_text") or h.get("text") or ""
        if jd.name_is_weak(h.get("case_name")) and not h.get("case_number"):
            continue                                   # no case name: "Judgment (Supreme Court of Pakistan)"
        if court and (name.count(court) > 1 or name == court):
            continue                                   # the court's name repeated as the title
        if (h.get("paragraph") or 0) <= 1 and len(_HEADER.findall(para[:400])) >= 2:
            continue                                   # a heading / parties paragraph, not reasoning
        if not judgment_search.readable(para):
            continue
        bits = ", ".join(str(x) for x in (court, h.get("year")) if x)
        title = name if not bits or f"({bits})" in name else f"{name} ({bits})"
        out.append({"doc_id": h["doc_id"], "display_name": name, "title": title, "court": court or None,
                    "year": h.get("year"), "paragraph": h["paragraph"], "score": h["score"]})
        if len(out) == 2:
            break
    return out


_HEADER = re.compile(r"\bIN THE (?:SUPREME|HIGH|FEDERAL|LAHORE|SINDH|PESHAWAR|ISLAMABAD|BALOCHISTAN)\b|\bPRESENT\b|"
                     r"\bVersus\b|\bPetitioners?\b|\bRespondents?\b|\bAppellants?\b|\bCORAM\b|Date of hearing", re.I)


def _act_key(act: str) -> str:
    """"Specific Relief Act, 1877" and "Specific Relief Act" compare equal."""
    return norm(re.sub(r",?\s*\(?(?:18|19|20)\d\d\)?", "", act or ""))


def check(data: dict, doc_text: str, ner_texts: list[str]) -> dict:
    """Run checks (a)-(d) over the model's JSON; returns the reasoning object."""
    doc_norm = norm(doc_text)
    doc_words = _doc_words(doc_text)
    dropped: Counter = Counter()
    returned = kept = flagged = 0

    def one(raw, *, kind: str = "item") -> dict | None:
        nonlocal returned, kept, flagged
        if not isinstance(raw, dict):
            return None
        returned += 1
        text = str(raw.get("text") or "").strip()
        evidence = str(raw.get("evidence") or "").strip()
        if kind == "statute":
            text = f"{raw.get('act') or ''} s.{raw.get('section') or ''}".strip()
        if not text or not evidence:
            dropped["no evidence quote"] += 1
            return None
        if not quote_found(evidence, doc_norm):
            dropped["quote not found in the document"] += 1
            return None
        missing, names = ([], []) if kind == "statute" else mention_problems(text, doc_text, doc_norm, ner_texts)
        if missing:
            dropped["mentions a date, number or section not in the document"] += 1
            return None
        if kind == "review" and absence_contradicted(text, doc_words):
            dropped["says something is missing that the document contains"] += 1
            return None
        out = {"text": text, "evidence": evidence, "verified": not names}
        if names:
            out["flags"] = [f"name not found in the document: {n}" for n in names]
            flagged += 1
        kept += 1
        return out

    def many(raw, kind: str = "item") -> list[dict]:
        return [x for x in (one(r, kind=kind) for r in (raw if isinstance(raw, list) else [])) if x]

    out: dict = {"document_type": one(data.get("document_type")),
                 "issues": many(data.get("issues")),
                 "arguments": {}, "court_reasoning": many(data.get("court_reasoning")),
                 "holding_or_outcome": one(data.get("holding_or_outcome")),
                 "statutes_cited": [], "strong_points": many(data.get("strong_points")),
                 "weak_points": many(data.get("weak_points"), "review"), "risks": many(data.get("risks"), "review"),
                 "open_questions": many(data.get("open_questions"), "review")}
    args = data.get("arguments")
    if isinstance(args, dict):
        for party, items in args.items():
            got = many(items)
            if got:
                out["arguments"][str(party).strip().lower()] = got
    for i, step in enumerate(out["court_reasoning"], 1):
        step["step"] = i
    # statutes: one item per section ("302/324/34 PPC" -> three), each looked up in the KB
    seen = set()
    for raw in data.get("statutes_cited") if isinstance(data.get("statutes_cited"), list) else []:
        if not isinstance(raw, dict):
            continue
        sections = re.findall(r"\d{1,4}[A-Z]?(?:-[A-Z])?", str(raw.get("section") or "")) or [None]
        for n in sections:
            item = one({**raw, "section": n}, kind="statute")
            if item is None or not n:
                continue
            status = statute_status(str(raw.get("act") or ""), n)
            key = (status.get("kb_title") or _act_key(str(raw.get("act"))), n)     # "PPC" = "Pakistan Penal Code"
            if key in seen:
                kept -= 1
                returned -= 1
                continue
            seen.add(key)
            item.update({"act": str(raw.get("act") or "").strip(), "section": n, **status})
            out["statutes_cited"].append(item)
    # kb-v2 C10: every statute the document names (pattern over the full text), even if the model missed it
    named = {s.get("kb_title") or _act_key(s["act"]) for s in out["statutes_cited"]}
    from_text = 0
    for st in statutes_in_text(doc_text):
        status = statute_status(st["act"], st["section"]) if st["section"] else law_status(st["act"])
        name_key = status.get("kb_title") or _act_key(st["act"])
        if (name_key, st["section"]) in seen or (not st["section"] and name_key in named):
            continue
        seen.add((name_key, st["section"]))
        named.add(name_key)
        from_text += 1
        out["statutes_cited"].append({"text": st["act"] + (f" s.{st['section']}" if st["section"] else ""),
                                      "evidence": st["evidence"], "verified": True, "found_in_text": True,
                                      "act": st["act"], "section": st["section"], **status})
    for issue in out["issues"]:
        cases = related_cases(issue["text"])
        if cases:
            issue["related_cases"] = cases
    st = Counter(s["status"] for s in out["statutes_cited"])
    out["counts"] = {"returned": returned, "kept": kept, "dropped": sum(dropped.values()),
                     "dropped_reasons": dict(dropped), "flagged": flagged, "statutes_from_text": from_text,
                     "statutes": {k: st.get(k, 0) for k in ("verified", "law_held", "not_found", "not_checked")}}
    out["related_cases_note"] = ("Related cases come from LegalEase's judgments library by similarity to each "
                                 "issue. They are not cited in this document.") if settings.JUDGMENTS_V2 else None
    out["disclaimer"] = DISCLAIMER
    return out


# --------------------------------------------------------------------------- entry point

def analyse(text: str, ner_texts: list[str], *, hint: str = "", ai=None,
            sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
            prior_tokens: int = 0) -> tuple[dict | None, str | None]:
    """(reasoning, None) or (None, plain-language reason).

    kb-v2 C10: the document is split into parts (plan) and each part is a model
    call, paced to stay under REASONING_TPM tokens a minute (prior_tokens: what
    the summary call just used), each retried on 429. The replies are merged and
    checked against the FULL text. If a later call fails, the parts already done
    are kept and the coverage says so."""
    from app.ai.client import RateLimitedError, get_ai_client
    ai = ai or get_ai_client()
    parts, coverage = plan(text)
    pacer = Pacer(settings.REASONING_TPM, clock=clock, sleep=sleep)
    if prior_tokens:
        pacer.log.append((clock(), prior_tokens))
    replies, prompt_tokens, stopped = [], 0, None
    for i, part in enumerate(parts, 1):
        prompt = prompt_for(part, hint, (i, len(parts)))
        cost = tokens(SYSTEM) + tokens(prompt)
        pacer.spend(cost + settings.REASONING_MAX_TOKENS)
        try:
            raw = call_model(ai, prompt, sleep=sleep)
            replies.append(parse_json(raw))
            prompt_tokens += cost
        except RateLimitedError as e:
            if not replies:
                if e.retry_after and e.retry_after > 120:
                    return None, ("The AI service's daily limit has been reached, so the reasoning step was "
                                  "skipped. The summary and entities are complete. Try the reasoning again tomorrow.")
                return None, ("The AI service is busy (its limit is 8,000 tokens a minute), so the reasoning step "
                              "was skipped. The summary and entities are complete. Try Analyse again in a minute.")
            stopped = "the AI service's rate limit"
            break
        except AIServiceUnavailable:
            if not replies:
                return None, ("The AI service didn't respond, so the reasoning step was skipped. The summary and "
                              "entities are complete.")
            stopped = "the AI service didn't respond"
            break
        except ValueError as e:
            logger.warning(f"Reasoning reply {i} was not JSON: {e}")
            if not replies and i == len(parts):
                return None, ("The AI reply wasn't in the expected format, so the reasoning step was skipped. The "
                              "summary and entities are complete.")
    if not replies:
        return None, ("The AI reply wasn't in the expected format, so the reasoning step was skipped. The "
                      "summary and entities are complete.")
    if len(replies) < len(parts):
        done = sum(tokens(parts[j]) for j in range(len(replies)))
        pct = round(100 * done / max(1, coverage["tokens_total"]))
        coverage = {**coverage, "partial": True, "tokens_analysed": done, "percent": pct,
                    "note": f"Only part of this document was analysed: about {pct}% of it ({len(replies)} of "
                            f"{len(parts)} parts){'; ' + stopped + ' stopped the rest' if stopped else ''}."}
    out = check(merge(replies), text, ner_texts)
    out["coverage"] = {**coverage, "calls": len(replies), "waited_seconds": round(pacer.waited)}
    out["prompt_tokens_estimate"] = prompt_tokens
    logger.info(f"Reasoning: {len(replies)} call(s), {coverage.get('percent')}% of the text; kept "
                f"{out['counts']['kept']} of {out['counts']['returned']} items, dropped {out['counts']['dropped']} "
                f"{out['counts']['dropped_reasons']}; statutes {out['counts']['statutes']}")
    return out, None
