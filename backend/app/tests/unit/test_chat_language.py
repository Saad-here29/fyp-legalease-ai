"""The chat answers in the language of the question. In the Oct 2026 audit
an English question ("What are the essential elements of a valid contract
under the Contract Act, 1872?") was answered in Urdu: the detected language
never reached the model, and the prompt's only concrete short-answer label
was the Urdu one. The prompt now carries an explicit per-question
instruction. Offline — no model calls."""

import pytest

from app.services.legal_chat_service import (
    LANGUAGE_INSTRUCTION,
    SYSTEM_PROMPT,
    _detect_language,
    build_system_prompt,
)

URDU_LABEL = "مختصر جواب"
CONTEXT = "[1] Source: Contract Act, 1872\nSection 10 — What agreements are contracts."


def test_base_prompt_has_no_language_specific_label():
    assert URDU_LABEL not in SYSTEM_PROMPT
    assert "Short answer:" not in SYSTEM_PROMPT


def test_english_question_gets_an_english_only_instruction():
    prompt = build_system_prompt(CONTEXT, "en")
    assert prompt.rstrip().endswith(LANGUAGE_INSTRUCTION["en"])
    assert "Answer in the language of the question" in prompt
    assert "entire answer in English" in prompt
    assert '"Short answer:"' in prompt
    assert URDU_LABEL not in prompt  # nothing in an English prompt invites Urdu


def test_urdu_question_gets_the_urdu_instruction():
    prompt = build_system_prompt(CONTEXT, "ur")
    assert prompt.rstrip().endswith(LANGUAGE_INSTRUCTION["ur"])
    assert "Answer in the language of the question" in prompt
    assert URDU_LABEL in prompt
    assert '"Short answer:"' not in prompt


def test_unknown_language_falls_back_to_english():
    assert build_system_prompt(CONTEXT, "fr").rstrip().endswith(LANGUAGE_INSTRUCTION["en"])


def test_prompt_keeps_the_authorities_block():
    prompt = build_system_prompt(CONTEXT, "en")
    assert "--- Relevant Pakistani legal authorities (cite by [n]) ---" in prompt
    assert CONTEXT in prompt


@pytest.mark.parametrize("question", [
    "What are the essential elements of a valid contract under the Contract Act, 1872?",
    "What is the punishment for qatl-i-amd under the Pakistan Penal Code?",
    "On what grounds can a Muslim woman obtain a decree for the dissolution of her marriage?",
])
def test_audit_questions_are_detected_as_english(question):
    assert _detect_language(question) == "en"


def test_urdu_question_is_detected_as_urdu():
    assert _detect_language("خلع کیا ہے اور عورت عدالت سے خلع کیسے لے سکتی ہے؟") == "ur"
