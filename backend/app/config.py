"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    demo_mode: bool = True
    database_url: str = "sqlite:///./scam_shield.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    region_default: str = "uk-example"
    public_app_url: str = "http://localhost:5173"

    # LLM provider: "auto" picks Unorouter when UNOROUTER_API_KEY is set, else Groq.
    llm_provider: str = "auto"  # auto | unorouter | groq

    # Unorouter (OpenAI-compatible gateway; required by the hackathon brief)
    unorouter_api_key: str = ""
    unorouter_base_url: str = "https://api.unorouter.com/v1"
    unorouter_chat_model: str = "gemini-2.5-flash"
    unorouter_fast_model: str = "gemini-2.5-flash:free"
    unorouter_vision_model: str = "gemini-2.5-flash"
    unorouter_stt_model: str = "whisper-large-v3-turbo:free"

    groq_api_key: str = ""
    groq_chat_model: str = ""
    groq_fast_model: str = ""
    groq_vision_model: str = ""
    groq_stt_model: str = ""
    groq_tts_model: str = "canopylabs/orpheus-v1-english"
    groq_tts_voice_caller: str = "troy"
    groq_tts_voice_victim: str = "hannah"

    enable_prompt_guard: bool = False
    groq_prompt_guard_model: str = ""

    store_inputs: bool = False
    store_transcripts: bool = False
    min_reports_to_show: int = 3

    email_backend: str = "console"  # console | smtp | resend
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"
    resend_api_key: str = ""
    resend_from: str = "Scam Shield <noreply@example.com>"

    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@example.com"

    # Only set true when running behind a reverse proxy that sets X-Forwarded-For.
    trust_proxy_headers: bool = False

    rate_limit_per_minute: int = 60
    rate_limit_llm_per_minute: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


DEFAULT_JWT_SECRET = "change-me-in-production-use-long-random-string"


def validate_settings(settings: Settings) -> None:
    """Refuse unsafe production config. DEMO_MODE stays zero-config for judges."""
    if settings.demo_mode:
        return
    if settings.jwt_secret == DEFAULT_JWT_SECRET or len(settings.jwt_secret) < 32:
        raise RuntimeError(
            "JWT_SECRET must be set to a random string of 32+ characters when DEMO_MODE=false."
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
