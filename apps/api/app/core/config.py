from pathlib import Path
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[4] / ".env"
API_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV) if ROOT_ENV.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Geotechnical Survey AI Studio API"
    NEXT_PUBLIC_APP_ENV: str = "development"

    ENABLE_PASSCODE_GATE: bool = False
    APP_PASSCODE_HASH: str = ""
    SESSION_SECRET_KEY: str = "geotech-survey-ai-cupertino-studio-secret-key-2026"
    ALLOWED_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    DATABASE_URL: str = f"sqlite+aiosqlite:///{API_DIR / 'geotech_studio.db'}"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_DRAFTING_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_FAST_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_TIER1_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_TIER2_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    TAVILY_API_KEY: str = ""

    STORAGE_ROOT: Path = API_DIR / "storage"

    @model_validator(mode="after")
    def _normalize_sqlite_url(self) -> "Settings":
        # Prevent relative SQLite split-brain regardless of current working directory
        prefix = "sqlite+aiosqlite:///./"
        if self.DATABASE_URL.startswith(prefix):
            rel_part = self.DATABASE_URL[len(prefix) :]
            abs_db = (API_DIR / rel_part).resolve()
            self.DATABASE_URL = f"sqlite+aiosqlite:///{abs_db}"
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
settings.STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
for sub in ("branding-assets", "equipment-gallery", "project-inputs", "compiled-exports"):
    (settings.STORAGE_ROOT / sub).mkdir(parents=True, exist_ok=True)
