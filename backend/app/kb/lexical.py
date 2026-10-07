"""Lexical (BM25) search over section records, for hybrid retrieval (kb-v2 C8).

Vector search alone misses exact legal terms: "res judicata" is the heading of
CPC s.11, "murder" is "qatl-i-amd" in the PPC. This module scores the
question's words against each section's heading (weighted x3), title and text
with BM25, and index_v2.search fuses that ranking with the vector ranking by
reciprocal rank fusion.

Tokens: lowercase words (light plural stemming), stop words dropped, and the
section's own number as a token ("sec302", "sec25a") so "Section 302" in a
question matches the s.302 record. TERMS adds the standard equivalents between
Pakistani statutory terms of art and their English words (in both
directions); it is a general glossary, not tuned to any test question.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

STOP = set("""a an the of and or to in on at for by with from as is are was were be been being this that these those
which who whom whose what when where why how can could may might shall should will would do does did not no any all
each every some such under into upon than then there their its it his her him he she they them my our your you i we
if about after before between during within without against per s sec section sections article articles art act
ordinance order code pakistan law laws legal""".split())

# Pakistani statutory terms of art <-> English (a glossary; applied to the question only).
TERMS = {
    "murder": ["qatl", "amd"], "qatl": ["murder"], "manslaughter": ["qatl", "khata"],
    "divorce": ["talaq"], "talaq": ["divorce"], "khula": ["dissolution"],
    "dower": ["mehr", "mahr"], "mehr": ["dower"], "mahr": ["dower"],
    "maintenance": ["nafqa", "nafaqa"], "nafqa": ["maintenance"], "nafaqa": ["maintenance"],
    "custody": ["hizanat"], "hizanat": ["custody"],
    "gift": ["hiba"], "hiba": ["gift"], "will": ["wasiyat"], "wasiyat": ["will"],
    "adultery": ["zina"], "zina": ["adultery"], "slander": ["qazf"], "qazf": ["slander"],
    "retaliation": ["qisas"], "qisas": ["retaliation"], "compensation": ["diyat", "arsh", "daman"],
    "diyat": ["compensation"], "endowment": ["waqf"], "waqf": ["endowment"],
}

_WORD = re.compile(r"[a-z]+|\d+[a-z]?")
_SECTION_REF = re.compile(r"\b(?:sections?|secs?\.?|s\.|u/s|articles?|arts?\.?)\s*(\d{1,4}(?:-?[A-Za-z]{1,2})?)(?![A-Za-z])",
                          re.I)


def stem(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def tokens(text: str) -> list[str]:
    return [stem(w) for w in _WORD.findall((text or "").lower().replace("-", " ")) if w not in STOP]


def query_tokens(question: str) -> list[str]:
    base = tokens(question)
    extra = [stem(t) for w in base for t in TERMS.get(w, [])]
    nums = [sec_token(n) for n in _SECTION_REF.findall(question or "")]
    return base + extra + nums


class BM25:
    """BM25 over documents given as weighted fields."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.ids: list[str] = []
        self.tf: list[Counter] = []
        self.df: Counter = Counter()
        self.lens: list[int] = []
        self.post: dict[str, list[int]] = defaultdict(list)

    def add(self, doc_id: str, fields: list[tuple[str, int]], extra: list[str] = ()) -> None:
        tf: Counter = Counter()
        for text, weight in fields:
            for t in tokens(text):
                tf[t] += weight
        for t in extra:
            tf[t] += 3
        i = len(self.ids)
        self.ids.append(doc_id)
        self.tf.append(tf)
        self.lens.append(sum(tf.values()))
        for t in tf:
            self.df[t] += 1
            self.post[t].append(i)

    def search(self, q_tokens: list[str], top: int = 30) -> list[tuple[str, float]]:
        if not self.ids:
            return []
        n, avg = len(self.ids), sum(self.lens) / len(self.ids)
        scores: dict[int, float] = defaultdict(float)
        for t in set(q_tokens):
            if t not in self.df:
                continue
            idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
            for i in self.post[t]:
                f = self.tf[i][t]
                scores[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.lens[i] / avg))
        best = sorted(scores.items(), key=lambda x: -x[1])[:top]
        return [(self.ids[i], s) for i, s in best]


def sec_token(number: str) -> str:
    """"302" -> "sec302", "25-A" -> "sec25a"."""
    return "sec" + re.sub(r"[\s-]", "", number).lower()


def section_token(section: str | None) -> list[str]:
    if not section or not re.match(r"\d", str(section)):
        return []
    return [sec_token(str(section))]


def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal rank fusion: sum of 1 / (k + rank) over the rankings an item appears in."""
    out: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for r, key in enumerate(ranking, 1):
            out[key] += 1.0 / (k + r)
    return out
