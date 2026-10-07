"""Application settings loaded from environment via pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ===== App =====
    APP_NAME: str = "LegalEase AI"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # ===== Security =====
    SECRET_KEY: str = Field(default="change-me", min_length=8)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # ===== CORS =====
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() in {"development", "dev", "local"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ===== Database =====
    DATABASE_URL: str = "postgresql+psycopg2://legalease:legalease_dev_pw@localhost:5432/legalease"
    DATABASE_ECHO: bool = False


    # ===== Groq (primary) =====
    # The prompts and the rewrite's reasoning_effort setting are tuned for
    # gpt-oss; it is also what backend/.env runs.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # ===== OpenAI =====
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDINGS_MODEL: str = "text-embedding-3-small"

    # ===== Gemini =====
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    # ===== Sentence Transformers =====
    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION: int = 384

    # ===== FAISS =====
    FAISS_INDEX_PATH: str = "./storage/faiss/legal_corpus.faiss"
    FAISS_METADATA_PATH: str = "./storage/faiss/legal_corpus_meta.json"

    # ===== Legal NER (Document Analysis) =====
    # Fine-tuned DistilBERT from ai-services/ner_training/ (weights gitignored;
    # see docs/ner_training_results.md). Missing folder -> NER is skipped and
    # /documents/{id}/analyze still returns the LLM summary.
    NER_MODEL_PATH: str = "./storage/models/legal_ner"
    NER_ENABLED: bool = True

    # ===== Tesseract =====
    TESSERACT_CMD: str = ""
    TESSERACT_LANG: str = "eng+urd"

    # ===== Storage =====
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    DOC_MAX_SIZE_MB: int = 20

    # ===== Email =====
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@legalease.ai"
    SMTP_TLS: bool = True

    # ===== RAG =====
    RAG_TOP_K: int = 5
    # Tuned down from 0.7 based on a 78-question real-world eval: at 0.7,
    # only ~1-25% of genuine questions passed (see
    # data/processed/qa_eval/retrieval_eval_results.json); 0.65 lets most
    # real questions through while still refusing the weakest matches.
    RAG_SIMILARITY_THRESHOLD: float = 0.65
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 100

    # ===== Chat quality steps (Oct 2026) =====
    # Each step is shipped only if the offline evaluation shows it helps;
    # otherwise it stays built but off. Results:
    # docs/chat_quality_steps_2026-10.md
    # Query rewrite at temperature 0, no statute names added.
    REWRITE_V2: bool = False
    # Answer prompt: every claim tied to a numbered passage, no analogy,
    # no consequences from memory, say what the passages don't cover.
    STRICT_GROUNDING: bool = False
    # Note on answers whose best passage scores in [threshold, upper).
    LOW_CONFIDENCE_NOTE: bool = True  # on since 2026-10-06 (approved after the 78-question check)
    LOW_CONFIDENCE_UPPER: float = 0.70
    # Family-law side index (core family statutes re-embedded in windows).
    FAMILY_INDEX: bool = False
    FAMILY_THRESHOLD: float = 0.65
    # Knowledge base v2: section-aware index searched before the v1 index
    # (app/kb/index_v2.py). Off: search is exactly the v1 search.
    KB_V2: bool = False
    # Similarity threshold used only when KB_V2 is on (RAG_SIMILARITY_THRESHOLD otherwise).
    KB_V2_THRESHOLD: float = 0.65
    # KB_V2 scope gate: a question with clear legal terms (and no foreign country)
    # that reaches no passage at the threshold may use passages down to this score
    # (shown with the weak-match note). Off-topic questions top out at 0.597.
    KB_V2_SCOPE_RESCUE_FLOOR: float = 0.60
    KB_DIR: str = "./storage/kb"            # records/, raw/, category_map.json (read-only at runtime)
    KB_V2_INDEX_PATH: str = "./storage/kb/faiss_v2.faiss"
    KB_V2_METADATA_PATH: str = "./storage/kb/faiss_v2_meta.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
