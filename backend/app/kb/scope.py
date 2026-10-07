"""Scope gate helpers for chat (kb-v2 B7).

The chat refuses ("I can only answer questions about Pakistani law…") when
no retrieved passage reaches the similarity threshold. That is the whole
gate: there is no keyword list or classifier. A long legal question whose
LLM rewrite drifts can then be refused although it is plainly about
Pakistani law (e.g. "is the family court's blanket order demanding the total
return of the dower property legally sustainable under Pakistani
jurisprudence", best 0.643).

With KB_V2 on, retrieve_passages adds two fallbacks before refusing:
  1. search the user's raw question too; a passage at or above the
     threshold makes the question in scope;
  2. if the question uses clear legal terms (dower, nikah, talaq, family
     court, decree, bail, FIR, "section 9", an "... Act" ...) and names no
     foreign country, accept the best passages down to
     KB_V2_SCOPE_RESCUE_FLOOR (0.60); the answer then carries the
     weak-match note. Off-topic questions score at most 0.597 (O10) and have
     no legal terms, so they are still refused.
"""

from __future__ import annotations

import re

from app.kb.exact_lookup import FOREIGN

LEGAL_TERMS = re.compile(
    r"\b(?:dower|mahr|mehr|haq\s+mehr|nikah\s*-?\s*nama|nikah|talaq|khula|iddat|jahez|jahiz|dowry|"
    r"maintenance|nafaqa|nafqa|custody|guardians?(?:hip)?|hizanat|family\s+courts?|jurisprudence|decree|"
    r"(?:court|stay|interim|blanket|ex\s*parte)\s+orders?|orders?\s+of\s+(?:the\s+)?court|"
    r"bail|f\.?i\.?r\b|first\s+information\s+report|section\s+\d|article\s+\d|u/s|"
    r"ordinance|statutes?|penal|criminal\s+procedure|civil\s+procedure|qanun|shahadat|constitution|"
    r"high\s+court|supreme\s+court|sessions?\s+court|magistrate|judge|petition|plaint|suit|appeal|writ|"
    r"accused|offen[cs]es?|punishment|sentence|inheritance|succession|tenancy|tenant|lease|"
    r"advocate|lawyer|pakistani\s+law|law\s+of\s+pakistan|laws?\s+in\s+pakistan)\b"
    r"|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Act\b",
    re.I,
)
# "... Act" must be a capitalised name; the case-insensitive flag above would
# also match "the act", so that alternative is checked separately.
_NAMED_ACT = re.compile(r"\b[A-Z][a-z]+(?:\s+(?:[A-Z][a-z]+|of|and))*\s+Act\b")


def foreign_only(question: str) -> bool:
    """kb-v2 C8: the question is about another country's law and doesn't
    mention Pakistan ("murder under the Indian Penal Code"): refused before
    retrieval, so no sources or cases are shown."""
    q = question or ""
    return bool(FOREIGN.search(q)) and not re.search(r"\bpakistan", q, re.I)


_REFUSAL = re.compile(r"outside (?:the|my) scope|can only (?:answer|help with) questions about pakistani|"
                      r"only answer questions about pakistani law|cannot help with that|not able to help with that|"
                      r"\u062f\u0627\u0626\u0631\u06c2 \u06a9\u0627\u0631 \u0633\u06d2 \u0628\u0627\u06c1\u0631", re.I)


def is_refusal(answer: str) -> bool:
    """kb-v2 C8: a short answer that only says the question is out of scope."""
    a = answer or ""
    return len(a) < 600 and bool(_REFUSAL.search(a))


def legal_terms(question: str) -> list[str]:
    """Clear legal terms in the question ([] if it names a foreign country)."""
    q = question or ""
    if FOREIGN.search(q):
        return []
    found = [m.group(0) for m in LEGAL_TERMS.finditer(q) if not m.group(0).lower().endswith(" act")]
    found += [m.group(0) for m in _NAMED_ACT.finditer(q)]
    return found
