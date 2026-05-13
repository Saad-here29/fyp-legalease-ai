"""Unified AI client — chat completion + summarisation.

Provider preference (first one with a configured key wins):
    1. Groq (Llama-3.3-70B) — free, fast, OpenAI-compatible. PRIMARY.
    2. OpenAI Chat Completions if OPENAI_API_KEY is set. Fallback.
    3. Google Gemini if GEMINI_API_KEY is set. Last-resort fallback.
    4. Otherwise raise AIServiceUnavailable. We never fabricate legal answers.

Groq + OpenAI share the OpenAI SDK (Groq is wire-compatible); only the
`base_url` differs. Gemini uses the dedicated google-generativeai SDK.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailable
from app.core.logging import logger


SYSTEM_PROMPT_LEGAL_CHAT = (
    "You are LegalEase — a Pakistani legal research assistant for lawyers, "
    "clients, and law students. Your output is read by legal professionals, "
    "so write like a junior counsel briefing a senior, not like a chatbot.\n\n"
    "STYLE RULES (strict):\n"
    "- NEVER use AI self-references. Banned phrases include: \"As an AI\", "
    "\"As a language model\", \"I am an AI\", \"I cannot provide legal advice\", "
    "\"I understand your concern\", \"Based on the provided context\", "
    "\"It is important to note\", \"Please consult a lawyer\" as a generic disclaimer. "
    "Do not preface answers with empathy statements or apologies.\n"
    "- Open with the legal point, not a preamble. First sentence states the rule.\n"
    "- Cite Pakistani statutes by section number and case law by PLD / SCMR / "
    "MLD citation when relevant authorities are provided in the context as [1], [2].\n"
    "- Reply in the user's language (English or Urdu). For Urdu, use natural "
    "Nastaliq script — including legal terms like khula, talaq, hizanat, nafaqah, "
    "haq mehr, qisas, diyat, ta'zir.\n"
    "- Use crisp structured formatting: short paragraphs, bold for statute "
    "names (**Section 302 PPC**), bullets for enumerations.\n"
    "- If the question is outside Pakistani law or cannot be answered from the "
    "provided authorities, say exactly: \"This question is outside the scope of "
    "Pakistani law I can answer on.\" — nothing else.\n"
    "- Never invent citations. If a section number is uncertain, omit it.\n\n"
    "DOMAIN COVERAGE: family law (Family Courts Act, MFLO, Dissolution of "
    "Muslim Marriages Act, Guardians and Wards Act), criminal law (PPC, Cr.P.C., "
    "Zainab Alert Act), civil & contract law (Contract Act 1872), property law "
    "(Transfer of Property Act, Specific Relief Act), and constitutional law "
    "(Constitution of Pakistan 1973)."
)


def _key(value: str | None) -> bool:
    v = (value or "").strip()
    return bool(v) and v != "demo" and not v.startswith("sk-...")


class AIClient:
    """Provider-agnostic chat client.

    Tries Groq first (free Llama 3.3 70B via OpenAI-compatible API), then
    OpenAI, then Gemini. Raises AIServiceUnavailable if none works.

    Attributes:
        provider: "groq" | "openai" | "gemini" | None — first one that
            successfully initialised.
    """

    def __init__(self) -> None:
        self.provider: str | None = None
        self._groq: Any = None
        self._openai: Any = None
        self._gemini: Any = None

        # 1. Groq — primary. Uses the OpenAI SDK pointed at Groq's endpoint.
        if _key(getattr(settings, "GROQ_API_KEY", "")):
            try:
                from openai import OpenAI  # lazy import
                self._groq = OpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1",
                )
                self.provider = "groq"
                logger.info(f"AI provider: Groq ({settings.GROQ_MODEL})")
            except ImportError:
                logger.warning("openai package not installed (needed for Groq)")

        # 2. OpenAI — first fallback.
        if self.provider is None and _key(settings.OPENAI_API_KEY):
            try:
                from openai import OpenAI
                self._openai = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.provider = "openai"
                logger.info(f"AI provider: OpenAI ({settings.OPENAI_MODEL})")
            except ImportError:
                logger.warning("openai package not installed")

        # 3. Gemini — last-resort fallback.
        if self.provider is None and _key(getattr(settings, "GEMINI_API_KEY", "")):
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini = genai.GenerativeModel(settings.GEMINI_MODEL)
                self.provider = "gemini"
                logger.info(f"AI provider: Gemini ({settings.GEMINI_MODEL})")
            except ImportError:
                logger.warning("google-generativeai package not installed")

        if self.provider is None:
            logger.warning(
                "No AI provider configured "
                "(set GROQ_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY)"
            )

    @property
    def enabled(self) -> bool:
        return self.provider is not None

    # -------- Public API -------------------------------------------------

    def chat(self, history: list[dict], system: str = SYSTEM_PROMPT_LEGAL_CHAT) -> str:
        """history: [{role, content}] for prior turns + latest user message."""
        if not self.enabled:
            raise AIServiceUnavailable(
                message="The AI assistant is not configured.",
                hint="Set GROQ_API_KEY (recommended), OPENAI_API_KEY, or GEMINI_API_KEY in backend/.env.",
            )

        # Try the active provider first; if it rate-limits / fails, walk
        # down the fallback chain in priority order.
        order = ["groq", "openai", "gemini"]
        order.remove(self.provider)
        order.insert(0, self.provider)

        last_err: AIServiceUnavailable | None = None
        for prov in order:
            if not self._has_provider(prov):
                continue
            try:
                if prov != self.provider:
                    logger.info(f"Falling back from {self.provider} to {prov}")
                return self._chat_with_provider(prov, history, system)
            except AIServiceUnavailable as e:
                last_err = e
                continue
        if last_err is not None:
            raise last_err
        raise AIServiceUnavailable(message="No AI provider available.")

    def _has_provider(self, name: str) -> bool:
        return {
            "groq": self._groq is not None,
            "openai": self._openai is not None,
            "gemini": self._gemini is not None,
        }.get(name, False)

    def summarise(self, text: str, hint: str = "") -> str:
        if not self.enabled:
            raise AIServiceUnavailable(
                message="AI summarisation is not configured.",
                hint="Set OPENAI_API_KEY or GEMINI_API_KEY in backend/.env.",
            )
        prompt = (
            "Summarise the following Pakistani legal document. Output sections:\n"
            "1) Summary (4-6 sentences in plain language)\n"
            "2) Parties (named individuals/entities)\n"
            "3) Key dates (in document order)\n"
            "4) Key clauses / obligations\n"
            "5) Risk flags or missing standard clauses\n\n"
            f"Document type hint: {hint}\n\n--- DOCUMENT ---\n{text[:30000]}"
        )
        history = [{"role": "user", "content": prompt}]
        sys_msg = "You are a Pakistani legal analyst. Be precise and concise."
        return self.chat(history, system=sys_msg)

    # -------- Provider implementations -----------------------------------

    def _chat_with_provider(
        self, provider: str, history: list[dict], system: str
    ) -> str:
        if provider == "groq":
            return self._chat_groq(history, system)
        if provider == "openai":
            return self._chat_openai(history, system)
        if provider == "gemini":
            return self._chat_gemini(history, system)
        raise AIServiceUnavailable(message=f"Unknown provider: {provider}")

    def _chat_groq(self, history: list[dict], system: str) -> str:
        try:
            resp = self._groq.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "system", "content": system}, *history],
                temperature=0.3,
                max_tokens=800,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Groq chat failed: {type(e).__name__}: {e}")
            raise AIServiceUnavailable(
                message="The AI service rejected this request.",
                hint=f"Groq: {type(e).__name__}. Trying fallback provider...",
            )

    def _chat_openai(self, history: list[dict], system: str) -> str:
        try:
            resp = self._openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "system", "content": system}, *history],
                temperature=0.3,
                max_tokens=800,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            logger.warning(f"OpenAI chat failed: {type(e).__name__}: {e}")
            raise AIServiceUnavailable(
                message="The AI service rejected this request.",
                hint=f"OpenAI: {type(e).__name__}. Try again or check billing.",
            )

    def _chat_gemini(self, history: list[dict], system: str) -> str:
        try:
            # Gemini takes prior turns as start_chat history and the latest
            # turn as the send_message argument. System prompt prepended to
            # the latest message.
            gemini_history = [
                {
                    "role": "user" if h["role"] == "user" else "model",
                    "parts": [h["content"]],
                }
                for h in history[:-1]
            ]
            chat_session = self._gemini.start_chat(history=gemini_history)
            last_msg = history[-1]["content"]
            full_prompt = f"{system}\n\nUser Question: {last_msg}" if system else last_msg
            response = chat_session.send_message(full_prompt)
            return response.text
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Gemini chat failed: {type(e).__name__}: {e}")
            raise AIServiceUnavailable(
                message="The AI service rejected this request.",
                hint=f"Gemini: {type(e).__name__}. Try again or check quota.",
            )


_singleton: AIClient | None = None


def get_ai_client() -> AIClient:
    global _singleton
    if _singleton is None:
        _singleton = AIClient()
    return _singleton
