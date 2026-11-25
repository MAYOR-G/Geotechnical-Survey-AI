from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ResearchThread(Base):
    __tablename__ = "research_threads"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"rth-{uuid.uuid4().hex[:10]}"
    )
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    scope: Mapped[str] = mapped_column(String(32), default="both")
    messages_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
