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
    "5. Use [] or null when the document says nothing on a point."
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
  "weak_points": [{"text": "a gap or weakness the document records", "evidence": "..."}],
  "risks": [{"text": "something that could go wrong for a party relying on this document", "evidence": "..."}],
  "open_questions": [{"text": "a fact or point the document leaves unresolved", "evidence": "..."}]
}"""


# --------------------------------------------------------------------------- tokens and excerpt

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


_FINDING = re.compile(
    r"^\s*\d{1,3}\s*\.|\b(?:we are of the (?:view|opinion)|held|finding|in view of|accordingly|therefore|allowed|"
    r"dismissed|set aside|convicted|acquitted|granted|refused|it is ordered)\b", re.I | re.M)


def _blocks(text: str) -> list[str]:
    """Paragraph-sized blocks: split at blank lines, tiny pieces joined to the next."""
    raw = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    out: list[str] = []
    buf = ""
    for b in raw:
        buf = f"{buf}\n{b}" if buf else b
        if len(buf) >= 300:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out


def excerpt(text: str, entity_texts: list[str], budget: int | None = None) -> tuple[str, dict]:
    """The text to send: all of it when it fits; else the head (30% of the
    budget), the tail (15%) and the middle paragraphs with the most NER
    entities and numbered findings, in document order, gaps marked "[…]"."""
    budget = budget or settings.REASONING_INPUT_TOKENS
    total = tokens(text)
    if total <= budget:
        return text, {"partial": False, "note": None, "tokens_analysed": total, "tokens_total": total}
    blocks = _blocks(text)
    cost = [tokens(b) for b in blocks]
    keep: set[int] = set()
    used = 0
    for i in range(len(blocks)):                                   # head
        if used + cost[i] > budget * 0.30:
            break
        keep.add(i)
        used += cost[i]
    tail_used = 0
    for i in range(len(blocks) - 1, -1, -1):                       # tail
        if i in keep or tail_used + cost[i] > budget * 0.15:
            break
        keep.add(i)
        tail_used += cost[i]
    used += tail_used
    ends = set(keep)
    ents = [e.lower() for e in entity_texts if len(e) >= 4]

    def score(i: int) -> int:
        low = blocks[i].lower()
        return sum(1 for e in ents if e in low) + 2 * len(_FINDING.findall(blocks[i]))
    for i in sorted((i for i in range(len(blocks)) if i not in keep), key=lambda i: (-score(i), i)):
        if score(i) == 0 or used + cost[i] > budget:
            continue
        keep.add(i)
        used += cost[i]
    if not keep:                                                    # one huge block: its start
        cut = text[: int(budget * 3.5)]
        return cut, {"partial": True, "tokens_analysed": tokens(cut), "tokens_total": total,
                     "note": f"Only the first part of this long document was analysed (about "
                             f"{100 * tokens(cut) // total}% of it)."}
    parts, last = [], -1
    for i in sorted(keep):
        if last >= 0 and i != last + 1:
            parts.append("[…]")
        parts.append(blocks[i])
        last = i
    out = "\n\n".join(parts)
    middle = len(keep - ends)
    return out, {"partial": True, "tokens_analysed": tokens(out), "tokens_total": total,
                 "note": (f"Only part of this long document was analysed (about {100 * tokens(out) // total}% of "
                          f"it): the beginning, the end and {max(middle, 0)} paragraphs in between that name "
                          "parties, dates or references or record findings. Items can only come from those parts.")}


# --------------------------------------------------------------------------- the call

def prompt_for(doc_text: str, hint: str) -> str:
    return f"{SCHEMA}\n\nDocument type hint from the uploader: {hint}\n\n--- DOCUMENT ---\n{doc_text}\n--- END ---"


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
    try:
        hits = judgment_search.search(issue, top_k=2, min_score=settings.REASONING_RELATED_MIN)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Related cases failed: {e}")
        return []
    return [{"doc_id": h["doc_id"], "display_name": h["display_name"], "court": h["court"], "year": h["year"],
             "paragraph": h["paragraph"], "score": h["score"]} for h in hits]


def check(data: dict, doc_text: str, ner_texts: list[str]) -> dict:
    """Run checks (a)-(d) over the model's JSON; returns the reasoning object."""
    doc_norm = norm(doc_text)
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
                 "weak_points": many(data.get("weak_points")), "risks": many(data.get("risks")),
                 "open_questions": many(data.get("open_questions"))}
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
            key = (status.get("kb_title") or norm(str(raw.get("act"))), n)     # "PPC" = "Pakistan Penal Code"
            if key in seen:
                kept -= 1
                returned -= 1
                continue
            seen.add(key)
            item.update({"act": str(raw.get("act") or "").strip(), "section": n, **status})
            out["statutes_cited"].append(item)
    for issue in out["issues"]:
        cases = related_cases(issue["text"])
        if cases:
            issue["related_cases"] = cases
    st = Counter(s["status"] for s in out["statutes_cited"])
    out["counts"] = {"returned": returned, "kept": kept, "dropped": sum(dropped.values()),
                     "dropped_reasons": dict(dropped), "flagged": flagged,
                     "statutes": {k: st.get(k, 0) for k in ("verified", "not_found", "not_checked")}}
    out["related_cases_note"] = ("Related cases come from LegalEase's judgments library by similarity to each "
                                 "issue. They are not cited in this document.") if settings.JUDGMENTS_V2 else None
    out["disclaimer"] = DISCLAIMER
    return out


# --------------------------------------------------------------------------- entry point

def analyse(text: str, ner_texts: list[str], *, hint: str = "", ai=None,
            sleep: Callable[[float], None] = time.sleep) -> tuple[dict | None, str | None]:
    """(reasoning, None) or (None, plain-language reason)."""
    from app.ai.client import RateLimitedError, get_ai_client
    ai = ai or get_ai_client()
    doc, coverage = excerpt(text, ner_texts)
    prompt = prompt_for(doc, hint)
    try:
        raw = call_model(ai, prompt, sleep=sleep)
    except RateLimitedError as e:
        if e.retry_after and e.retry_after > 120:
            return None, ("The AI service's daily limit has been reached, so the reasoning step was skipped. "
                          "The summary and entities are complete. Try the reasoning again tomorrow.")
        return None, ("The AI service is busy (its limit is 8,000 tokens a minute), so the reasoning step was "
                      "skipped. The summary and entities are complete. Try Analyse again in a minute.")
    except AIServiceUnavailable:
        return None, ("The AI service didn't respond, so the reasoning step was skipped. The summary and "
                      "entities are complete.")
    try:
        data = parse_json(raw)
    except ValueError as e:
        logger.warning(f"Reasoning reply was not JSON: {e}: {raw[:200]!r}")
        return None, ("The AI reply wasn't in the expected format, so the reasoning step was skipped. The "
                      "summary and entities are complete.")
    out = check(data, text, ner_texts)
    out["coverage"] = coverage
    out["prompt_tokens_estimate"] = tokens(SYSTEM) + tokens(prompt)
    logger.info(f"Reasoning: kept {out['counts']['kept']} of {out['counts']['returned']} items, dropped "
                f"{out['counts']['dropped']} {out['counts']['dropped_reasons']}; statutes {out['counts']['statutes']}")
    return out, None
