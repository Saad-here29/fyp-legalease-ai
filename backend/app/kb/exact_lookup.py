"""Exact section lookup (kb-v2 B7).

When a question names a section or article AND a law we hold ("murder under
Section 302 of the Pakistan Penal Code", "u/s 154 CrPC", "Article 10A of the
Constitution"), the record for that section is fetched directly from the kb
records and put first in the retrieved passages, marked as an exact match.
Semantic search fills the remaining slots. Deterministic (regex + title
match); nothing happens when no law is named, when the law is a foreign one
("Indian Penal Code"), or when that law has no such section.
"""

from __future__ import annotations

import re

from app.kb import catalog
from app.kb.index_v2 import passage

MAX_EXACT = 2

# "section 302", "sec. 302", "s. 302", "u/s 302", "ss. 302 and 304", "article 10A", "Art. 25", "302-A"
# The suffix is case-sensitive: "302-A", "10A", but not the "of" in "302 of".
_NUM = r"(\d{1,3}(?-i:\s?-?\s?[A-Z]{1,2}(?![A-Za-z]))?)"
_REF = re.compile(r"\b(?:u/s|sections?|secs?\.?|ss?\.|articles?|arts?\.?)\s*" + _NUM, re.I)
# A bare "302 PPC" / "PPC 302" form.
_BARE = re.compile(r"\b" + _NUM + r"\s*(?=PPC|CrPC|Cr\.?P\.?C\.?|CPC|C\.P\.C\.?|QSO)|"
                   r"(?<=PPC|CPC|QSO)\s*" + _NUM + r"\b")

# Aliases for the core laws people abbreviate; every other law matches on its title.
ALIASES = {
    "Pakistan Penal Code, 1860": [r"pakistan\s+penal\s+code", r"\bp\.?\s?p\.?\s?c\b\.?"],
    "Code of Criminal Procedure, 1898": [r"criminal\s+procedure", r"\bcr\.?\s?p\.?\s?c\b\.?"],
    "Code of Civil Procedure, 1908": [r"civil\s+procedure", r"\bc\.?\s?p\.?\s?c\b\.?"],
    "Constitution of the Islamic Republic of Pakistan, 1973": [r"\bconstitution\b"],
    "Qanun-e-Shahadat Order, 1984": [r"qanun[\s-]*e[\s-]*shahadat", r"\bq\.?\s?s\.?\s?o\b\.?", r"evidence\s+order"],
    "Contract Act, 1872": [r"contract\s+act"],
    "Guardians and Wards Act, 1890": [r"guardians?\s+(?:and|&)\s+wards?"],
    "West Pakistan Family Courts Act, 1964": [r"family\s+courts?\s+act"],
    "Muslim Family Laws Ordinance, 1961": [r"muslim\s+family\s+laws?\s+ordinance", r"\bmflo\b"],
    "Dissolution of Muslim Marriages Act, 1939": [r"dissolution\s+of\s+muslim\s+marriages?", r"\bdmma\b"],
    "West Pakistan Muslim Personal Law (Shariat) Application Act, 1962": [r"shariat\s+(?:application\s+)?act"],
}
# Questions about another country's law never trigger a lookup.
FOREIGN = re.compile(
    r"\b(?:indian?|india's|bangladesh\w*|nigeria\w*|thailand|thai|california\w*|u\.?s\.?a?\b|united\s+states|"
    r"american|america|uk\b|united\s+kingdom|british|england|english\s+law|canad\w+|australia\w*|uae|dubai|"
    r"saudi|malaysia\w*|sri\s+lanka\w*|nepal\w*|afghan\w*|iran\w*|philippines?|filipino)", re.I)
_STOP_TITLE_WORDS = {"the", "act", "of", "and", "ordinance", "order", "code", "west", "pakistan", "for", "in", "on"}


def canon(num: str) -> str:
    return re.sub(r"[\s-]", "", num or "").upper()


def _title_pattern(title: str) -> str | None:
    """Distinctive words of a law's title ('Specific Relief Act, 1877' ->
    'specific relief act'), or None if too generic to match on its own."""
    stem = re.sub(r",?\s*\d{4}$", "", title).lower()
    words = re.findall(r"[a-z]+", stem)
    if len([w for w in words if w not in _STOP_TITLE_WORDS]) < 2:
        return None
    return r"\s+".join(re.escape(w) for w in words if w != "the")


def _laws() -> dict[str, list[str]]:
    """Law title -> patterns that name it in a question (cached per catalog version)."""
    d = catalog.data()
    cached = d.get("_law_patterns")
    if cached and cached[0] == d.get("key"):
        return cached[1]
    out: dict[str, list[str]] = {}
    for law in d["laws"].values():
        t = law["title"]
        pats = list(ALIASES.get(t, []))
        tp = _title_pattern(t)
        if tp:
            pats.append(tp)
        if pats:
            out[t] = [re.compile(p, re.I) for p in pats]
    d["_law_patterns"] = (d.get("key"), out)
    return out


def _section_index() -> dict[str, dict[str, str]]:
    d = catalog.data()
    key = d.get("key")
    cached = d.get("_exact_index")
    if cached and cached[0] == key:
        return cached[1]
    idx: dict[str, dict[str, str]] = {}
    for rid, r in d["records"].items():
        if r.get("section"):
            idx.setdefault(r["title"], {}).setdefault(canon(r["section"]), rid)
    d["_exact_index"] = (key, idx)
    return idx


def _owner(q: str, pos: int, hints: list[tuple[int, int, str]]) -> str:
    """The law a section number belongs to: "302 of the PPC" (the law right
    after it), else "PPC section 302" (right before it), else the nearest."""
    end = pos + len(re.match(r"\S+\s*\S*", q[pos:]).group(0))
    after = [h for h in hints if h[0] >= pos and re.fullmatch(
        r"\s*(?:,|\(|(?:of|under|in)(?:\s+the)?)?\s*", q[end:h[0]])]
    if after:
        return min(after, key=lambda h: h[0])[2]
    before = [h for h in hints if h[1] <= pos and re.fullmatch(r"\s*(?:'s)?\s*,?\s*", q[h[1]:pos])]
    if before:
        return max(before, key=lambda h: h[1])[2]
    return min(hints, key=lambda h: min(abs(h[0] - pos), abs(h[1] - pos)))[2]


def find_refs(question: str) -> list[tuple[str, str]]:
    """[(law title, canonical section)] named in the question, nearest law
    hint to each number; [] for foreign-law questions."""
    q = question or ""
    if FOREIGN.search(q):
        return []
    hints: list[tuple[int, int, str]] = []
    for title, pats in _laws().items():
        for p in pats:
            for m in p.finditer(q):
                hints.append((m.start(), m.end(), title))
    if not hints:
        return []
    nums = [(m.start(), m.group(1)) for m in _REF.finditer(q)]
    nums += [(m.start(), m.group(1) or m.group(2)) for m in _BARE.finditer(q)]
    out: list[tuple[str, str]] = []
    for pos, num in sorted(nums):
        if not num:
            continue
        title = _owner(q, pos, hints)
        ref = (title, canon(num))
        if ref not in out:
            out.append(ref)
    return out


def exact_passages(question: str) -> list[dict]:
    """The named sections' records as retrieval hits (first, marked exact)."""
    index = _section_index()
    records = catalog.data()["records"]
    hits = []
    for title, sec in find_refs(question):
        rid = index.get(title, {}).get(sec)
        if not rid:
            continue                          # that law has no such section: nothing special
        r = records[rid]
        hits.append({
            "source": r["title"], "source_type": "statute", "chunk_id": rid, "doc_id": rid,
            "text": passage({"start": 0}, r["text"]),
            "section": r.get("section"), "heading": r.get("heading"),
            "source_tier": r.get("source_tier"), "source_url": r.get("source_url"),
            "category": r.get("category"), "year": r.get("year"), "jurisdiction": r.get("jurisdiction"),
            "audience": r.get("audience") or "general", "kb": "v2",
            "exact_match": True, "relevance": 1.0,
        })
        if len(hits) == MAX_EXACT:
            break
    return hits


def merge(exact: list[dict], semantic: list[dict], top_k: int) -> list[dict]:
    """Exact matches first, then semantic results that aren't the same record."""
    ids = {h["doc_id"] for h in exact}
    rest = [p for p in semantic if p.get("doc_id") not in ids]
    return exact + rest[: max(0, top_k - len(exact))]
