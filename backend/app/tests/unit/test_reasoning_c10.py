"""kb-v2 C10: Document Analysis accuracy, on synthetic text with a stand-in model (no Groq)."""

import json
import sys
from pathlib import Path

import pytest

from app.ai import reasoning
from app.ai.client import RateLimitedError
from app.ai.summary_sections import extract_clauses_and_risks
from app.core.config import settings
from app.core.exceptions import AIServiceUnavailable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures" / "reasoning"))
from synthetic import PRAYER, STATUTES, SegmentModel, written_statement  # noqa: E402


class Clock:
    """A clock that moves only when the code sleeps."""

    def __init__(self):
        self.t, self.sleeps = 0.0, []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(round(s, 1))
        self.t += s


@pytest.fixture(autouse=True)
def plain(monkeypatch):
    monkeypatch.setattr(settings, "JUDGMENTS_V2", False)
    monkeypatch.setattr(settings, "REASONING_INPUT_TOKENS", 5000)
    monkeypatch.setattr(settings, "REASONING_MAX_CALLS", 5)
    monkeypatch.setattr(settings, "REASONING_TPM", 7500)


# --------------------------------------------------------------------------- coverage

def test_pdf_text_without_blank_lines_splits_into_paragraphs():
    doc = written_statement(1200)
    assert "\n\n" not in doc
    pieces = reasoning.units(doc)
    assert len(pieces) > 8 and pieces[-2].startswith("PRAYER") is False or any(p.startswith("PRAYER") for p in pieces)
    assert any(p.startswith("3. ") for p in pieces)


def test_whole_document_is_planned_up_to_the_call_limit():
    short, cov = reasoning.plan(written_statement(3800))
    assert len(short) == 1 and cov["partial"] is False and cov["percent"] == 100 and cov["note"] is None
    parts, cov = reasoning.plan(written_statement(12000))
    assert len(parts) == 3 and cov["partial"] is False and cov["percent"] == 100
    assert all(reasoning.tokens(p) <= 5000 for p in parts)
    assert " ".join(" ".join(parts).split()) == " ".join(written_statement(12000).split())     # nothing left out


def test_a_very_long_document_keeps_the_prayer_and_ends_and_says_how_much(monkeypatch):
    monkeypatch.setattr(settings, "REASONING_MAX_CALLS", 3)
    doc = written_statement(20000)
    parts, cov = reasoning.plan(doc)
    assert len(parts) == 3 and cov["partial"] is True and 0 < cov["percent"] < 100
    assert f"about {cov['percent']}% of it" in cov["note"]
    flat = [" ".join(p.split()) for p in parts]
    assert flat[0].startswith("IN THE COURT") and "dismissed with costs" in flat[-1]


def test_pacer_waits_for_the_minute_and_counts_the_summary():
    clock = Clock()
    p = reasoning.Pacer(7500, clock=clock, sleep=clock.sleep)
    p.log.append((clock(), 6000))                 # the summary call just now
    p.spend(5000)
    assert clock.sleeps == [60.5] and p.waited == 60.5
    p.spend(2000)                                 # fits in the same minute
    assert clock.sleeps == [60.5]
    stuck = reasoning.Pacer(7500, clock=lambda: 0.0, sleep=lambda s: None)
    stuck.spend(6000)
    stuck.spend(6000)                             # a clock that never moves must not hang
    assert stuck.waited > 0


def test_merge_joins_parts_in_order():
    a = {"document_type": {"text": "Written statement", "evidence": "x"}, "issues": [{"text": "i1", "evidence": "e"}],
         "arguments": {"Defendant": [{"text": "a1", "evidence": "e"}]}, "holding_or_outcome": None,
         "statutes_cited": [{"act": "X Act", "section": "1", "evidence": "e"}]}
    b = {"document_type": {"text": "other", "evidence": "y"}, "issues": [{"text": "i1", "evidence": "e"},
                                                                         {"text": "i2", "evidence": "e"}],
         "arguments": {"defendant": [{"text": "a2", "evidence": "e"}]}, "holding_or_outcome": {"text": "h", "evidence": "e"},
         "statutes_cited": [{"act": "X Act", "section": "1", "evidence": "e"}]}
    m = reasoning.merge([a, b])
    assert m["document_type"]["text"] == "Written statement" and m["holding_or_outcome"]["text"] == "h"
    assert [i["text"] for i in m["issues"]] == ["i1", "i2"] and len(m["statutes_cited"]) == 1
    assert [x["text"] for x in m["arguments"]["defendant"]] == ["a1", "a2"]


# --------------------------------------------------------------------------- statutes from the text

def test_statutes_named_in_the_text():
    found = {(s["act"], s["section"]) for s in reasoning.statutes_in_text(written_statement(3800))}
    assert found == {("Code of Civil Procedure, 1908", None), ("Specific Relief Act, 1877", "42"),
                     ("Limitation Act, 1908", None), ("Transfer of Property Act, 1882", "54")}
    more = reasoning.statutes_in_text("under the Stamp Act (II of 1899), 1899 and the Constitution of the Islamic "
                                      "Republic of Pakistan, 1973; see section 7 of the Muslim Family Laws "
                                      "Ordinance, 1961.")
    assert {(s["act"], s["section"]) for s in more} >= {("Constitution of the Islamic Republic of Pakistan, 1973", None),
                                                         ("Muslim Family Laws Ordinance, 1961", "7")}
    assert reasoning.statutes_in_text("The First Schedule applies. No Act is named here.") == []


# --------------------------------------------------------------------------- absence claims

DOC = ("The defendant prays that the suit be dismissed with costs. Jurisdiction lies with this Court. The hearing "
       "date is 3 May. " + "Nothing further is said here. " * 20 + "The recovery memo was prepared.")


@pytest.mark.parametrize("point, contradicted", [
    ("No prayer for dismissal, no costs.", True),
    ("The written statement does not mention jurisdiction.", True),
    ("Costs are not sought.", True),
    ("No date is given for the handing over of possession.", False),
    ("There is no annexure numbered for the sale deed.", False),
    ("The sale price differs between paragraphs 4 and 9.", False),          # not an absence claim
    ("No date is given for the recovery memo.", False),                    # "date" alone is not enough
])
def test_absence_claims(point, contradicted):
    kept, removed = reasoning.drop_contradicted_absences([point], DOC)
    assert (removed == [point]) is contradicted and (kept == [point]) is (not contradicted)


# --------------------------------------------------------------------------- end to end

def test_a_long_written_statement_is_fully_analysed():
    clock = Clock()
    m = SegmentModel()
    out, err = reasoning.analyse(written_statement(12000), [], ai=m, sleep=clock.sleep, clock=clock,
                                 prior_tokens=6300)
    assert err is None and len(m.prompts) == 3 and all("This is part" in p for p in m.prompts)
    assert out["coverage"]["partial"] is False and out["coverage"]["percent"] == 100
    assert out["coverage"]["calls"] == 3 and out["coverage"]["waited_seconds"] >= 60
    assert {s["act"] for s in out["statutes_cited"]} == {name for name, _cite in STATUTES}
    assert out["arguments"]["defendant"][0]["evidence"] in PRAYER                 # the prayer was read
    assert out["weak_points"] == []                                               # "No prayer for costs" removed
    assert out["counts"]["dropped_reasons"] == {"says something is missing that the document contains": 1}


def test_statutes_the_model_missed_are_added_from_the_text():
    class Silent:
        def complete_json(self, prompt, system, max_tokens):
            return json.dumps({"issues": []})
    out, _ = reasoning.analyse(written_statement(3800), [], ai=Silent(), sleep=lambda s: None)
    assert len(out["statutes_cited"]) == 4 and all(s["found_in_text"] for s in out["statutes_cited"])
    assert out["counts"]["statutes_from_text"] == 4
    assert all(s["status"] in ("verified", "law_held", "not_found", "not_checked") for s in out["statutes_cited"])


@pytest.mark.parametrize("failure, words", [
    (AIServiceUnavailable(message="down"), "didn't respond"),
    (RateLimitedError("busy"), "rate limit"),
])
def test_a_failure_after_the_first_part_keeps_what_was_done(monkeypatch, failure, words):
    monkeypatch.setattr(settings, "REASONING_MAX_WAIT", 0)

    class FailsSecond(SegmentModel):
        def complete_json(self, prompt, system, max_tokens):
            if self.prompts:
                self.prompts.append(prompt)
                raise failure
            return super().complete_json(prompt, system, max_tokens)
    clock = Clock()
    out, err = reasoning.analyse(written_statement(12000), [], ai=FailsSecond(), sleep=clock.sleep, clock=clock)
    assert err is None and out["coverage"]["partial"] is True and words in out["coverage"]["note"]
    assert 0 < out["coverage"]["percent"] < 100 and f"{out['coverage']['percent']}%" in out["coverage"]["note"]


# --------------------------------------------------------------------------- related cases

def test_related_cases_are_cleaned(monkeypatch):
    from app.kb import judgment_search
    seen = []

    def hit(name, case_name, number, para, text, court="Supreme Court of Pakistan"):
        return {"doc_id": f"judgment/x/{name}", "display_name": name, "case_name": case_name, "case_number": number,
                "court": court, "year": 2023, "paragraph": para, "text": text, "paragraph_text": text, "score": 0.7}

    def fake(q, top_k, min_score):
        seen.append(min_score)
        return [hit("Judgment (Supreme Court of Pakistan)", None, None, 5, "The court held that bail ..."),
                hit("Supreme Court of Pakistan (Supreme Court of Pakistan)", "Supreme Court of Pakistan", "C.P. 1",
                    5, "held"),
                hit("A v. B", "A v. B", "C.P. 2 of 2023", 1, "IN THE SUPREME COURT OF PAKISTAN PRESENT: ... Versus ..."),
                hit("Ali v. State", "Ali v. State", "Crl.P. 9 of 2023", 7, "Bail was granted because the case "
                                                                           "called for further inquiry."),
                hit("Zed v. Y", "Zed v. Y", "C.P. 3 of 2022", 4, "The court said the suit was barred.")]
    monkeypatch.setattr(judgment_search, "search", fake)
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    cases = reasoning.related_cases("bail on further inquiry")
    assert [c["display_name"] for c in cases] == ["Ali v. State", "Zed v. Y"] and seen == [0.58]
    assert cases[0]["title"] == "Ali v. State (Supreme Court of Pakistan, 2023)"


# --------------------------------------------------------------------------- summary review points

def test_points_to_review_section_is_read():
    _c, risks = extract_clauses_and_risks("1) Summary\nx\n5) Points to review\n- No prayer for costs.\n- Annexure "
                                          "C is referred to but not attached.")
    assert risks == ["No prayer for costs.", "Annexure C is referred to but not attached."]


def test_summary_prompt_only_changes_with_the_flag():
    from app.ai.client import AIClient
    seen = []
    c = AIClient.__new__(AIClient)
    c.provider = "groq"
    c.chat = lambda history, system=None: seen.append(history[0]["content"]) or "ok"
    c.summarise("text", hint="h")
    c.summarise("text", hint="h", focus_gaps=True)
    assert "5) Risk flags or missing standard clauses" in seen[0] and "Points to review" not in seen[0]
    assert "5) Points to review: gaps in THIS document only" in seen[1]
