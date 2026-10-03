"""Chat history is capped at 2,000 tokens. It was sent verbatim (last 10
messages), and by the 6th turn of a session with long answers the request
went over Groq's 8,000 tokens-per-minute cap (prompt + 2,000-token reply
reserve). Offline: no model calls."""

import pytest

from app.services import legal_chat_service as chat
from app.services.legal_chat_service import HISTORY_TOKEN_BUDGET, trim_history


@pytest.fixture
def word_tokens(monkeypatch):
    """Count one token per word, so budgets are exact and tokenizer-free."""
    monkeypatch.setattr(chat, "count_tokens", lambda text: len(text.split()))


def _msg(role, words, tag):
    return {"role": role, "content": " ".join([tag] * words)}


def _conversation(answer_words):
    out = []
    for i in range(5):
        out.append(_msg("user", 100, f"q{i}"))
        out.append(_msg("assistant", answer_words, f"a{i}"))
    return out


def test_budget_is_2000_tokens():
    assert HISTORY_TOKEN_BUDGET == 2000


def test_short_history_is_kept_whole_and_in_order(word_tokens):
    history = _conversation(answer_words=200)  # 1,500 tokens in all
    assert trim_history(history) == history


def test_long_history_keeps_the_newest_messages_within_budget(word_tokens):
    history = _conversation(answer_words=800)  # 4,500 tokens in all
    kept = trim_history(history)
    assert kept == history[-4:]  # q3 a3 q4 a4 = 1,800 tokens; adding a2 would exceed 2,000
    assert sum(len(m["content"].split()) for m in kept) <= HISTORY_TOKEN_BUDGET


def test_history_stays_contiguous(word_tokens):
    # A huge message in the middle stops the walk back; the small, older
    # messages behind it are not pulled in around the gap.
    history = [_msg("user", 50, "old"), _msg("assistant", 3000, "huge"), _msg("user", 50, "new")]
    assert trim_history(history) == [history[-1]]


def test_an_oversized_newest_message_leaves_no_history(word_tokens):
    assert trim_history([_msg("user", 10, "q"), _msg("assistant", 2500, "a")]) == []


def test_empty_history(word_tokens):
    assert trim_history([]) == []


def test_fallback_estimate_when_the_tokenizer_is_unavailable(monkeypatch):
    monkeypatch.setattr(chat, "_encoder", lambda: None)
    assert chat.count_tokens("x" * 1000) == 501  # half the characters, rounded up: over-estimates


def test_real_counter_returns_a_positive_count():
    assert chat.count_tokens("Section 302 of the Pakistan Penal Code.") > 0
