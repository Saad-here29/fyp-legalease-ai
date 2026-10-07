"""Synthetic documents and a stand-in model for the Document Analysis tests (kb-v2 C10).

written_statement(words): a defendant's written statement with numbered
paragraphs, four statutes named in different places, and the prayer at the
end ("... the suit ... be dismissed with costs"). Nothing in it comes from a
real case.

SegmentModel: answers like the real model would, from ONLY the document text it
is sent: it lists the statutes it can see, the prayer if it can see it, and,
like the model did on the real document, claims "No prayer for costs" when the
prayer isn't in its part of the text.
"""

from __future__ import annotations

import json
import re

STATUTES = [("Code of Civil Procedure, 1908", "Order VII Rule 11 of the Code of Civil Procedure, 1908"),
            ("Specific Relief Act, 1877", "section 42 of the Specific Relief Act, 1877"),
            ("Limitation Act, 1908", "Article 120 of the First Schedule to the Limitation Act, 1908"),
            ("Transfer of Property Act, 1882", "section 54 of the Transfer of Property Act, 1882")]
PRAYER = ("It is, therefore, most respectfully prayed that the suit of the plaintiff may kindly be dismissed "
          "with costs throughout, being false, frivolous and barred by law.")

_FILLER = ("The contents of this paragraph are denied as incorrect and misconceived, and the plaintiff is put to "
           "strict proof of each allegation made therein, as the record maintained by the defendant shows that "
           "the transaction was carried out in the ordinary course of business and with the knowledge of all "
           "concerned. ")


def pdf_layout(text: str, width: int = 90) -> str:
    """As text comes out of a PDF: lines wrapped at ~90 characters, single line
    breaks, no blank lines between paragraphs."""
    import textwrap
    return "\n".join(line for block in text.split("\n") for line in (textwrap.wrap(block, width) or [""]) if line)


def written_statement(words: int = 3800, pdf: bool = True) -> str:
    head = ("IN THE COURT OF THE SENIOR CIVIL JUDGE, LAHORE\nCivil Suit No. 412 of 2024\n"
            "Muhammad Aslam ... Plaintiff\nVersus\nRashid Mehmood ... Defendant\n\n"
            "WRITTEN STATEMENT ON BEHALF OF THE DEFENDANT\n\nPRELIMINARY OBJECTIONS\n\n")
    paras, n = [], 1
    body_words = words - len(head.split()) - len(PRAYER.split()) - 20
    n_paras = max(8, body_words // len((_FILLER * 2).split()))
    # paragraph number -> statute, spread through the document (10%, 35%, 60%, 85%)
    statute_at = {max(1, round(n_paras * f)): i for i, f in enumerate((0.10, 0.35, 0.60, 0.85))}
    while sum(len(p.split()) for p in paras) < body_words:
        text = f"{n}. " + (_FILLER * 2)
        if n in statute_at:
            name, cite = STATUTES[statute_at[n]]
            text += f"The suit is not maintainable under {cite}, and the plaintiff has no cause of action. "
        if n == 8:
            text += "The sale was made on 12.03.2019 for a consideration of Rs. 2,500,000/-. "
        paras.append(text.strip())
        n += 1
    text = head + "\n\n".join(paras) + "\n\nPRAYER\n\n" + PRAYER + "\n\nDefendant\nThrough Counsel\n"
    return pdf_layout(text) if pdf else text


def _segment(prompt: str) -> str:
    m = re.search(r"--- DOCUMENT ---\n(.*)\n--- END ---", prompt, re.S)
    return " ".join((m.group(1) if m else prompt).split())          # wrapped lines read as one


class SegmentModel:
    """A stand-in for the JSON model call; records each prompt it is sent."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete_json(self, prompt: str, system: str, max_tokens: int) -> str:
        self.prompts.append(prompt)
        seg = _segment(prompt)
        statutes = []
        for name, cite in STATUTES:
            if cite in seg:
                num = re.search(r"(?:section|Article|Rule)\s+(\d+)", cite).group(1)
                statutes.append({"act": name, "section": num, "evidence": cite})
        out = {"document_type": None, "issues": [], "arguments": {}, "court_reasoning": [],
               "holding_or_outcome": None, "statutes_cited": statutes, "strong_points": [], "weak_points": [],
               "risks": [], "open_questions": []}
        if "most respectfully prayed" in seg:
            out["arguments"]["defendant"] = [{"text": "The defendant asks for the suit to be dismissed with costs.",
                                              "evidence": "the suit of the plaintiff may kindly be dismissed with costs"}]
        else:
            out["weak_points"].append({"text": "No prayer for costs is made in the written statement.",
                                       "evidence": "the plaintiff is put to strict proof of each allegation made "
                                                   "therein"})
        if "WRITTEN STATEMENT ON BEHALF" in seg:
            out["document_type"] = {"text": "Written statement of the defendant",
                                    "evidence": "WRITTEN STATEMENT ON BEHALF OF THE DEFENDANT"}
        return json.dumps(out)
