"""Chat-quality steps 2-4 (Oct 2026): strict grounding prompt, low-confidence
flag, family-law side index and its fallback. Offline: no model calls."""

import datetime
import uuid

import pytest
from pydantic import ValidationError

from app.ai import family_index
from app.api.v1.chat import ChatMessageRequest
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.chat import ChatMessageRead
from app.services import legal_chat_service as chat

# ---- step 2: strict grounding prompt -----------------------------------------

def test_strict_rules_only_when_on(monkeypatch):
    monkeypatch.setattr(chat.settings, "STRICT_GROUNDING", False)
    assert "GROUNDING RULES" not in chat.build_system_prompt("[1] x", "en")
    monkeypatch.setattr(chat.settings, "STRICT_GROUNDING", True)
    prompt = chat.build_system_prompt("[1] x", "en")
    assert "GROUNDING RULES" in prompt
    # Rules come before the passages and the language instruction.
    assert prompt.index("GROUNDING RULES") < prompt.index("[1] x") < prompt.index("LANGUAGE:")


def test_strict_argument_overrides_setting(monkeypatch):
    monkeypatch.setattr(chat.settings, "STRICT_GROUNDING", False)
    assert "GROUNDING RULES" in chat.build_system_prompt("[1] x", "ur", strict=True)


@pytest.mark.parametrize("phrase", ["[n]", "No reasoning by analogy",
                                    "from your own knowledge", "say so"])
def test_strict_rules_cover_the_review_findings(phrase):
    assert phrase in chat.STRICT_GROUNDING_RULES


# ---- step 3: low-confidence flag ----------------------------------------------

@pytest.mark.parametrize("on, scores, expected", [
    (True, [0.6509], "low"),
    (True, [0.6834, 0.6529, 0.6501], "low"),
    (True, [0.66, 0.70], "normal"),       # the best passage decides; 0.70 is outside
    (False, [0.6509], "normal"),          # switched off: never low
])
def test_confidence(monkeypatch, on, scores, expected):
    monkeypatch.setattr(chat.settings, "LOW_CONFIDENCE_NOTE", on)
    monkeypatch.setattr(chat.settings, "LOW_CONFIDENCE_UPPER", 0.70)
    flags = chat.answer_flags([{"relevance": s} for s in scores])
    assert flags["confidence"] == expected


def test_refusal_has_no_confidence():
    assert chat.answer_flags(None) == {"confidence": None, "family_scope": False}
    assert chat.answer_flags([]) == {"confidence": None, "family_scope": False}


def test_history_shows_the_same_flags(monkeypatch):
    monkeypatch.setattr(chat.settings, "LOW_CONFIDENCE_NOTE", True)
    m = ChatMessageRead(id=uuid.uuid4(), sender_type="ai", content="x",
                        citations=[{"relevance": 0.66, "family": True}],
                        created_at=datetime.datetime.now())
    dumped = m.model_dump()
    assert dumped["confidence"] == "low" and dumped["family_scope"] is True


# ---- step 4: family-law side index -------------------------------------------

@pytest.mark.parametrize("source, tier", [
    ("THE MUSLIM FAMILY LAWS ORDINAN CE, 1961", "core"),
    ("Muslim Family Laws Ordinance, 1961", "core"),
    ("THE WEST PAKISTAN FAMILY COURTS ACT, 1964", "core"),
    ("THE GUARDIANS AND WAR DS ACT, 1890", "core"),
    ("THE DOWRY AND BRIDAL GIFTS (RESTRICTION) ACT, 1976", "core"),
    ("THE DIVORCE ACT,1869", "minority"),
    ("THE HINDU MARRIAGE ACT, 2017", "minority"),
    ("THE MARRIED WOMEN'S PROPERTY ACT, 1874", "minority"),
    ("THE QANUNESHAHADAT , 1984", None),          # excluded: FCA s.17
    ("THE CODE OF CIVIL PROCEDURE, 1908", None),  # excluded: FCA s.17
    ("THE PAKISTAN PENAL CODE", None),
])
def test_allowlist(source, tier):
    assert family_index.tier_of(source) == tier


@pytest.mark.parametrize("text, family", [
    ("What is a suit for restitution of conjugal rights?", True),
    ("Why is the Nikah Nama important in a dower dispute?", True),
    ("dahej possession after separation remedy", True),
    ("بیوی کو جہیز واپس کیسے ملے گا؟", True),
    ("What is the punishment for theft?", False),
    ("Give me a recipe for chocolate cake.", False),
    ("Can an advocate present false facts before the court?", False),
])
def test_family_question(text, family):
    assert family_index.is_family_question(text) is family


def test_community_named():
    assert family_index.names_community("Can a Christian wife seek judicial separation?")
    assert family_index.names_community("ہندو شادی کی رجسٹریشن")
    assert not family_index.names_community("Can a wife seek khula?")


class _Tok:
    """Whitespace tokenizer with character offsets, like a fast HF tokenizer."""

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=True):
        offs, pos = [], 0
        for w in text.split(" "):
            offs.append((pos, pos + len(w)))
            pos += len(w) + 1
        return {"offset_mapping": offs}


def test_windows_cover_the_whole_chunk(monkeypatch):
    monkeypatch.setattr(family_index, "WINDOW_TOKENS", 4)
    monkeypatch.setattr(family_index, "WINDOW_STRIDE", 2)
    text = "a b c d e f g h i"
    ws = family_index.windows(text, _Tok())
    assert ws == ["a b c d", "c d e f", "e f g h", "g h i"]
    assert all(len(w.split()) <= 4 for w in ws)
    assert family_index.windows("a b", _Tok()) == ["a b"]


@pytest.fixture
def family_on(monkeypatch):
    monkeypatch.setattr(chat.settings, "FAMILY_INDEX", True)
    monkeypatch.setattr(chat.settings, "FAMILY_THRESHOLD", 0.65)
    calls = {"family": [], "main": 0}

    def main_search(*a, **k):
        calls["main"] += 1
        return [{"source": "MAIN", "text": "main passage", "relevance": 0.7}]

    monkeypatch.setattr(chat.embeddings, "search", main_search)
    monkeypatch.setattr(chat.section_lookup, "section_passages", lambda *a: [])
    return calls


def _family_results(monkeypatch, calls, score):
    def fake(query, top_k, *, minority):
        calls["family"].append(minority)
        return [{"source": "THE WEST PAKISTAN FAMILY COURTS ACT, 1964", "text": "Schedule",
                 "relevance": score, "family_window": 3}]
    monkeypatch.setattr(chat.family_index, "search", fake)


def test_family_question_uses_the_family_index(monkeypatch, family_on):
    _family_results(monkeypatch, family_on, 0.72)
    got = chat.retrieve_passages("What is a dowry claim?", "dowry recovery")
    assert [p["source"] for p in got] == ["THE WEST PAKISTAN FAMILY COURTS ACT, 1964"]
    assert family_on["main"] == 0 and family_on["family"] == [False]


def test_falls_back_to_the_full_index(monkeypatch, family_on):
    _family_results(monkeypatch, family_on, 0.50)   # nothing passes
    got = chat.retrieve_passages("What is a dowry claim?", "dowry recovery")
    assert [p["source"] for p in got] == ["MAIN"] and family_on["main"] == 1


def test_non_family_question_skips_the_family_index(monkeypatch, family_on):
    _family_results(monkeypatch, family_on, 0.9)
    got = chat.retrieve_passages("Punishment for theft?", "theft punishment")
    assert [p["source"] for p in got] == ["MAIN"] and family_on["family"] == []


def test_user_switch_off_and_feature_off(monkeypatch, family_on):
    _family_results(monkeypatch, family_on, 0.9)
    assert chat.retrieve_passages("dowry?", "dowry", family="off")[0]["source"] == "MAIN"
    monkeypatch.setattr(chat.settings, "FAMILY_INDEX", False)
    assert chat.retrieve_passages("dowry?", "dowry")[0]["source"] == "MAIN"
    assert family_on["family"] == []


def test_minority_acts_only_when_community_named(monkeypatch, family_on):
    _family_results(monkeypatch, family_on, 0.9)
    chat.retrieve_passages("Can a Christian wife get divorce?", "christian divorce grounds")
    chat.retrieve_passages("Can a wife get khula?", "khula")
    assert family_on["family"] == [True, False]


def test_request_switch_values():
    assert ChatMessageRequest(message="q").family == "auto"
    assert ChatMessageRequest(message="q", family="off").family == "off"
    with pytest.raises(ValidationError):
        ChatMessageRequest(message="q", family="on")


def test_send_reports_flags(db_session, monkeypatch, family_on):
    """End to end through send(), with the model stubbed."""
    _family_results(monkeypatch, family_on, 0.68)
    monkeypatch.setattr(chat.settings, "LOW_CONFIDENCE_NOTE", True)
    monkeypatch.setattr(chat, "rewrite_for_search", lambda q: q)
    monkeypatch.setattr(chat.embeddings, "build_or_load", lambda *a: 1)

    class Model:
        def chat(self, history, system):
            return "Short answer: dowry is in the Schedule [1]."

    monkeypatch.setattr(chat, "get_ai_client", lambda: Model())
    u = User(email="fam@gmail.com", password_hash=hash_password("x"), full_name="F",
             role=UserRole.CLIENT, is_active=True, is_verified=True)
    db_session.add(u)
    db_session.commit()
    reply = chat.LegalChatService(db_session).send(u, "How do I recover dowry articles?")
    assert reply["family_scope"] is True and reply["confidence"] == "low"
    history = chat.LegalChatService(db_session).get_history(uuid.UUID(reply["session_id"]), u)
    ai = ChatMessageRead.model_validate(history[-1]).model_dump()
    assert ai["family_scope"] is True and ai["confidence"] == "low"


def test_options_report_the_family_switch(monkeypatch):
    from app.api.v1.chat import chat_options
    monkeypatch.setattr(chat.settings, "FAMILY_INDEX", False)
    assert chat_options(None).family_index is False
    monkeypatch.setattr(chat.settings, "FAMILY_INDEX", True)
    assert chat_options(None).family_index is True


def test_low_confidence_note_is_on_by_default():
    from app.core.config import Settings
    s = Settings(_env_file=None)
    assert s.LOW_CONFIDENCE_NOTE is True and s.LOW_CONFIDENCE_UPPER == 0.70
    # The other steps stay off until approved.
    assert not (s.REWRITE_V2 or s.STRICT_GROUNDING or s.FAMILY_INDEX)
