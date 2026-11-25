from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default="default")
    default_contractor_name: Mapped[str] = mapped_column(String(255), default="")
    default_contractor_logo_url: Mapped[str] = mapped_column(Text, default="")
    author_name: Mapped[str] = mapped_column(String(255), default="")
    author_email: Mapped[str] = mapped_column(String(255), default="")
    author_designation: Mapped[str] = mapped_column(String(255), default="")
    author_signature_url: Mapped[str] = mapped_column(Text, default="")
    style_guide_json: Mapped[dict] = mapped_column(JSON, default=dict)
    openrouter_api_key_override: Mapped[str] = mapped_column(Text, default="")
    tavily_api_key_override: Mapped[str] = mapped_column(Text, default="")
    drafting_model: Mapped[str] = mapped_column(
        String(120), default="anthropic/claude-3.5-sonnet"
    )
    fast_model: Mapped[str] = mapped_column(
        String(120), default="google/gemini-2.5-flash"
    )
    enable_passcode_gate: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
