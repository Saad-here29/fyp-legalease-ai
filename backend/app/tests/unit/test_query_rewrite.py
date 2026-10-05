"""Query rewrite v2: temperature 0, no statute names added, every rewrite logged."""

import pytest

from app.ai import client as client_mod
from app.ai import query_rewrite
from app.ai.query_rewrite import strip_unasked_statutes


# Rewrites recorded in the 2026-10-05 legal review (the model added the Act).
@pytest.mark.parametrize("question, rewrite, expected", [
    (
        "What is a suit for restitution of conjugal rights?",
        "petition for restitution of conjugal rights under Muslim Family Laws Ordinance",
        "petition for restitution of conjugal rights",
    ),
    (
        "A wife claims that her dowry articles remain in the husband's possession "
        "after separation. What remedy may be available?",
        "dowry articles possession after separation remedy under Muslim Family Laws Ordinance",
        "dowry articles possession after separation remedy",
    ),
    (
        "Can a family-law advocate knowingly present false facts before the court?",
        "advocate false statements to court professional misconduct under Legal "
        "Practitioners and Bar Councils Act",
        "advocate false statements to court professional misconduct",
    ),
    (
        "What is the punishment for theft?",
        "theft punishment PPC section 379",
        "theft punishment section 379",
    ),
    (
        "Which court hears a suit for dower?",
        "jurisdiction for dower suit under the West Pakistan Family Courts Act, 1964",
        "jurisdiction for dower suit",
    ),
])
def test_added_statute_is_removed(question, rewrite, expected):
    assert strip_unasked_statutes(question, rewrite) == expected


@pytest.mark.parametrize("question, rewrite", [
    ("What is murder under Section 302 of the Pakistan Penal Code?",
     "murder qatl-i-amd Section 302 Pakistan Penal Code"),
    ("What are the essential elements of a valid contract under the Contract Act, 1872?",
     "essential elements valid contract Contract Act 1872"),
    ("What does the MFLO say about polygamy?", "polygamy permission MFLO"),
    ("Explain bail under the Code of Criminal Procedure",
     "bail non-bailable offence Code of Criminal Procedure"),
])
def test_statute_named_in_question_is_kept(question, rewrite):
    assert strip_unasked_statutes(question, rewrite) == rewrite


def test_terms_of_art_are_not_statutes():
    rewrite = "talaq notice to Chairman Union Council arbitration khula hizanat"
    assert strip_unasked_statutes("How does a husband divorce?", rewrite) == rewrite


def test_never_returns_empty():
    assert strip_unasked_statutes("x", "Muslim Family Laws Ordinance") == "Muslim Family Laws Ordinance"


class _FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def rewrite_search_query(self, query, *, v2=False):
        self.calls.append(v2)
        return self.reply


def test_rewrite_for_search_v2_strips_and_logs(monkeypatch):
    fake = _FakeClient("restitution of conjugal rights under Muslim Family Laws Ordinance")
    monkeypatch.setattr(query_rewrite, "get_ai_client", lambda: fake)
    logged = []
    monkeypatch.setattr(query_rewrite.logger, "info", logged.append)

    out = query_rewrite.rewrite_for_search("What is restitution of conjugal rights?", v2=True)

    assert out == "restitution of conjugal rights"
    assert fake.calls == [True]
    assert len(logged) == 1
    line = logged[0]
    assert "Query rewrite v2" in line and " ms)" in line
    assert "What is restitution of conjugal rights?" in line and "'restitution of conjugal rights'" in line
    assert "statute removed" in line


def test_rewrite_for_search_v1_is_unchanged(monkeypatch):
    fake = _FakeClient("talaq under Muslim Family Laws Ordinance")
    monkeypatch.setattr(query_rewrite, "get_ai_client", lambda: fake)
    monkeypatch.setattr(query_rewrite.logger, "info", lambda *_: None)
    out = query_rewrite.rewrite_for_search("How do I divorce?", v2=False)
    assert out == "talaq under Muslim Family Laws Ordinance"
    assert fake.calls == [False]


def test_rewrite_for_search_defaults_to_setting(monkeypatch):
    fake = _FakeClient("q")
    monkeypatch.setattr(query_rewrite, "get_ai_client", lambda: fake)
    monkeypatch.setattr(query_rewrite.logger, "info", lambda *_: None)
    monkeypatch.setattr(query_rewrite.settings, "REWRITE_V2", True)
    query_rewrite.rewrite_for_search("question")
    monkeypatch.setattr(query_rewrite.settings, "REWRITE_V2", False)
    query_rewrite.rewrite_for_search("question")
    assert fake.calls == [True, False]


@pytest.mark.parametrize("v2, prompt, temperature", [
    (True, client_mod.REWRITE_PROMPT_V2, 0.0),
    (False, client_mod.REWRITE_PROMPT_V1, 0.3),
])
def test_client_rewrite_prompt_and_temperature(monkeypatch, v2, prompt, temperature):
    c = client_mod.AIClient.__new__(client_mod.AIClient)
    c.provider, c._groq, c._openai, c._gemini = "groq", object(), None, None
    seen = {}

    def fake_provider(prov, history, system, max_tokens, reasoning_effort, temp):
        seen.update(system=system, temperature=temp, max_tokens=max_tokens)
        return " rewritten "

    monkeypatch.setattr(c, "_chat_with_provider", fake_provider)
    assert c.rewrite_search_query("q", v2=v2) == "rewritten"
    assert seen == {"system": prompt, "temperature": temperature,
                    "max_tokens": client_mod.REWRITE_MAX_TOKENS}


def test_v2_prompt_names_no_statute():
    assert "(Muslim Family Laws Ordinance)" in client_mod.REWRITE_PROMPT_V1
    assert "Muslim Family Laws Ordinance" not in client_mod.REWRITE_PROMPT_V2
    assert "Never add the name of an Act" in client_mod.REWRITE_PROMPT_V2
