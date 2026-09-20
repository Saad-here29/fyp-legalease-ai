"""AI Legal Research service — semantic search over Pakistani legal corpus.

Backed by sentence-transformers embeddings + FAISS IndexFlatIP for cosine
similarity. The index is built by `ai-services/corpus_builder/build_corpus.py`
and persisted to disk; this service loads it on first request.

The metadata format is the corpus_builder format:
    { source, source_type, chunk_id, text }
Legacy seed format (`title`, `content`, ...) also still works via the
record_* helpers in app.ai.embeddings.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.ai import embeddings
from app.ai.client import get_ai_client
from app.ai.query_rewrite import rewrite_for_search
from app.schemas.research import ResearchResult, StructuredAnalysis


# Map raw corpus filenames → human-readable titles. Anything matching a
# known statute is renamed; SC judgments (`C.A_supreme (N)`) are reformatted
# into "Supreme Court of Pakistan — Civil Appeal No. N" with the raw source
# kept as a subtitle (so the demo looks professional without fabricating
# case names we don't actually have).
_STATUTE_TITLES: dict[str, str] = {
    "Pakistan_Penal_Code": "Pakistan Penal Code 1860",
    "Code_of_Criminal_Procedure_1898": "Code of Criminal Procedure 1898",
    "Family_Courts_Act_1964": "Family Courts Act 1964",
    "Muslim_Family_Laws_Ordinance_1961": "Muslim Family Laws Ordinance 1961",
    "Zainab_Alert_Act_2020": "Zainab Alert, Response and Recovery Act 2019",
    "Pakistani_Legal_Reference": "Pakistani Legal Reference",
}

_SC_RE = re.compile(r"^C\.?A_supreme\s*\(?(\d+)\)?$", re.IGNORECASE)


def _friendly_title(source: str) -> str:
    """Convert the raw corpus source key into a presentable title."""
    if source in _STATUTE_TITLES:
        return _STATUTE_TITLES[source]
    m = _SC_RE.match(source.strip())
    if m:
        return f"Supreme Court of Pakistan — Civil Appeal No. {m.group(1)}"
    # Fallback: replace underscores with spaces, title-case it
    return source.replace("_", " ").strip()


def _trim_to_sentence(text: str, *, max_len: int = 800) -> str:
    """Trim leading partial-word fragments so the excerpt starts at a clean
    sentence or capitalised word boundary. Chunks are sliding-window cuts,
    so they often start mid-sentence — that looks bad in the UI.

    If the text already starts cleanly (capital letter or Urdu char),
    we leave it alone so we don't drop the first sentence of a clean passage."""
    if not text:
        return ""
    s = text.lstrip()
    # Already starts cleanly? Don't touch it.
    if s and (s[0].isupper() or 0x600 <= ord(s[0]) <= 0x6FF):
        return s

    # Otherwise advance past the leading fragment to the next sentence start
    boundary = re.search(r"[.!?]\s+[A-Z؀-ۿ]", s)
    if boundary and boundary.start() < max_len // 2:
        s = s[boundary.start() + 1 :].lstrip()
    # Strip any remaining non-alpha prefix like ", a, where..."
    s = re.sub(r"^[^A-Z؀-ۿ]+", "", s, count=1)
    return s.strip() or text.strip()


class ResearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        query: str,
        top_k: int = 10,
        court: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        case_type: str | None = None,
    ) -> list[ResearchResult]:
        embeddings.build_or_load(self.db)
        search_query = rewrite_for_search(query)
        hits = embeddings.search(
            search_query,
            top_k=top_k,
            filters={
                "court": court,
                "year_from": year_from,
                "year_to": year_to,
                "case_type": case_type,
            },
        )

        results: list[ResearchResult] = []
        for h in hits:
            raw_text = embeddings.record_text(h)
            text = _trim_to_sentence(raw_text)
            excerpt = text[:280] + ("..." if len(text) > 280 else "")
            source = embeddings.record_source(h)
            kind = embeddings.record_kind(h)
            title = _friendly_title(source)
            # URL-safe id: prefer existing uuid, else "source__chunkN".
            raw_id = h.get("id")
            stable_id = (
                str(raw_id)
                if raw_id
                else f"{source}__chunk{h.get('chunk_id', 0)}"
            )
            # Use the raw source as the citation for SC judgments (so the
            # user sees both the friendly name *and* the corpus origin).
            citation = h.get("section_number") or ""
            if not citation and source not in _STATUTE_TITLES:
                citation = f"From: {source} (LegalEase corpus)"
            elif source in _STATUTE_TITLES and h.get("section_number"):
                citation = h.get("section_number")
            results.append(
                ResearchResult(
                    id=stable_id,
                    title=title,
                    citation=citation,
                    court=h.get("court") or ("Supreme Court of Pakistan" if _SC_RE.match(source) else None),
                    year=h.get("year"),
                    case_type=kind,
                    excerpt=excerpt,
                    text=text,
                    relevance=round(h.get("relevance", 0.0), 4),
                )
            )
        return results

    def structured_analysis(
        self,
        text: str,
        *,
        source: str | None = None,
        user_query: str | None = None,
    ) -> StructuredAnalysis:
        """Run a single LLM pass to convert a raw legal passage into a
        structured breakdown (Issue / Findings / Judgment / Legal Basis /
        Relevance). Used by the Research detail page."""
        ai = get_ai_client()
        relevance_hint = (
            f"\nThe user is researching: \"{user_query}\""
            if user_query
            else ""
        )
        prompt = (
            "Analyse the following Pakistani legal passage and produce a "
            "structured breakdown. Return exactly these five labelled sections, "
            "each 1-3 sentences, in plain language. Do NOT add any preamble. "
            "Do NOT use AI self-references.\n\n"
            "Issue: <the legal question or point of law>\n"
            "Findings: <what the court or statute holds on this point>\n"
            "Judgment: <the operative ruling or rule that emerges>\n"
            "Legal Basis: <statutes / sections / earlier cases relied on>\n"
            "Relevance: <how this applies to the user's research>"
            f"{relevance_hint}\n\n"
            f"SOURCE: {source or 'Pakistani legal corpus'}\n"
            f"PASSAGE:\n{text[:6000]}"
        )
        history = [{"role": "user", "content": prompt}]
        raw = ai.chat(history)
        return self._parse_structured(raw)

    @staticmethod
    def _parse_structured(raw: str) -> StructuredAnalysis:
        """Best-effort parse of the labelled LLM output. Each label is
        searched case-insensitively; if a section is missing we fall back to
        a sensible placeholder so the UI doesn't break."""
        import re
        sections = {
            "issue": "",
            "findings": "",
            "judgment": "",
            "legal_basis": "",
            "relevance": "",
        }
        labels = [
            ("issue", r"issue"),
            ("findings", r"findings?"),
            ("judgment", r"judgment|judgement|ruling"),
            ("legal_basis", r"legal\s*basis|basis"),
            ("relevance", r"relevance"),
        ]
        # Build a single regex that splits on labelled headers
        pattern = re.compile(
            r"^\s*\**\s*(issue|findings?|judgment|judgement|ruling|legal\s*basis|basis|relevance)\s*\**\s*[:\-]\s*",
            re.IGNORECASE | re.MULTILINE,
        )
        parts = pattern.split(raw)
        # parts = [pre, label1, body1, label2, body2, ...]
        if len(parts) >= 3:
            for i in range(1, len(parts), 2):
                label = parts[i].lower().strip()
                body = parts[i + 1].strip() if i + 1 < len(parts) else ""
                for key, rx in labels:
                    if re.fullmatch(rx, label, re.IGNORECASE):
                        sections[key] = body
                        break

        # Fallback — if parsing produced nothing useful, dump the raw into Issue
        if not any(sections.values()):
            sections["issue"] = raw.strip()

        return StructuredAnalysis(
            issue=sections["issue"] or "—",
            findings=sections["findings"] or "—",
            judgment=sections["judgment"] or "—",
            legal_basis=sections["legal_basis"] or "—",
            relevance=sections["relevance"] or "—",
            raw=raw.strip(),
        )
