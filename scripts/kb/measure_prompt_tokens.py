"""kb-v2 C8: prompt tokens per chat answer, section expansion off vs on. No LLM.

For every evaluation question (26 gold, live, 40 unseen), retrieve the passages
as Chat does (raw question, no rewrite), build the exact system prompt
(compose_answer with a stand-in model that only records it) and count its tokens
(o200k, or the conservative estimate offline). Reports mean and max, and the
total per answer with the 2,000-token reply reserve, against Groq's 8,000
tokens a minute.

    cd backend
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python ../scripts/kb/measure_prompt_tokens.py
"""

from __future__ import annotations

import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

from eval_c8 import sets  # noqa: E402

from app.ai import embeddings  # noqa: E402
from app.ai.client import CHAT_MAX_TOKENS  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services import legal_chat_service as chat  # noqa: E402


class Recorder:
    def __init__(self):
        self.system = ""

    def chat(self, history, system=None):
        self.system = system
        return "Short answer: ok [1]."


def measure(expand: bool) -> list[int]:
    settings.SECTION_EXPANSION = expand
    out = []
    for qs in sets().values():
        for _qid, q, _acc in qs:
            passages = chat.retrieve_passages(q, q)
            if not passages:
                continue
            ai = Recorder()
            chat.compose_answer(ai, passages, [{"role": "user", "content": q}], "en")
            out.append(chat.count_tokens(ai.system) + chat.count_tokens(q))
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    settings.KB_V2, settings.QUERY_HINTS, settings.SCRAPED_V2, settings.JUDGMENTS_V2 = True, True, True, False
    embeddings.build_or_load()
    exact = chat._encoder() is not None
    for label, flag in (("expansion off", False), ("expansion on", True)):
        t = measure(flag)
        print(f"{label}: {len(t)} answered questions | prompt mean {st.mean(t):.0f}, max {max(t)} tokens | "
              f"with the {CHAT_MAX_TOKENS}-token reply: mean {st.mean(t) + CHAT_MAX_TOKENS:.0f}, "
              f"max {max(t) + CHAT_MAX_TOKENS} (Groq limit 8,000/min) | tokenizer: {'o200k' if exact else 'estimate'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
