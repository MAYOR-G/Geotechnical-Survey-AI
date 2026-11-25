from pathlib import Path
import re
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_THIS_FILE = Path(__file__).resolve()
API_DIR = _THIS_FILE.parents[2]


def _resolve_env_file() -> str:
    candidates = [API_DIR / ".env"]
    if len(_THIS_FILE.parents) > 4:
        candidates.insert(0, _THIS_FILE.parents[4] / ".env")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
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
    SUPABASE_POOLER_HOST: str = "aws-0-eu-central-1.pooler.supabase.com"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_DRAFTING_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_FAST_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_TIER1_MODEL: str = "google/gemini-2.5-flash"
    OPENROUTER_TIER2_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    TAVILY_API_KEY: str = ""

    STORAGE_ROOT: Path = API_DIR / "storage"

    @model_validator(mode="after")
    def _normalize_database_url(self) -> "Settings":
        # 1. Prevent relative SQLite split-brain regardless of current working directory
        sqlite_rel_prefix = "sqlite+aiosqlite:///./"
        if self.DATABASE_URL.startswith(sqlite_rel_prefix):
            rel_part = self.DATABASE_URL[len(sqlite_rel_prefix) :]
            abs_db = (API_DIR / rel_part).resolve()
            self.DATABASE_URL = f"sqlite+aiosqlite:///{abs_db}"
            return self

        # 2. Auto-upgrade standard postgres:// or postgresql:// URLs to asyncpg
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = "postgresql+asyncpg://" + self.DATABASE_URL[len("postgres://") :]
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = "postgresql+asyncpg://" + self.DATABASE_URL[len("postgresql://") :]

        # 3. Auto-upgrade IPv6-only Supabase Direct URL (db.<ref>.supabase.co) to IPv4 Session Pooler
        #    so IPv4-only container hosts like Render never fail with [Errno 101] Network is unreachable
        direct_match = re.match(
            r"^(postgresql\+asyncpg://)postgres:([^@]+)@db\.([a-z0-9]+)\.supabase\.co(?::\d+)?(/.*)$",
            self.DATABASE_URL,
        )
        if direct_match:
            scheme, password, project_ref, path_part = direct_match.groups()
            pooler_host = (self.SUPABASE_POOLER_HOST or "aws-0-eu-central-1.pooler.supabase.com").strip()
            self.DATABASE_URL = f"{scheme}postgres.{project_ref}:{password}@{pooler_host}:5432{path_part}"

        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip().rstrip("/") for o in self.ALLOWED_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
settings.STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
for sub in ("branding-assets", "equipment-gallery", "project-inputs", "compiled-exports"):
    (settings.STORAGE_ROOT / sub).mkdir(parents=True, exist_ok=True)
