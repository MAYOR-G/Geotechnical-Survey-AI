import uuid
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ClarificationItem(Base):
    __tablename__ = "clarification_items"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"clar-{uuid.uuid4().hex[:10]}"
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    category: Mapped[str] = mapped_column(String(64), default="missing_data")
    question_text: Mapped[str] = mapped_column(Text)
    context_reference: Mapped[str] = mapped_column(String(255), default="")
    suggested_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    omit_section: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="clarifications")


class QaAlert(Base):
    __tablename__ = "qa_alerts"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"qa-{uuid.uuid4().hex[:10]}"
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    severity: Mapped[str] = mapped_column(String(32), default="warning")
    section_id: Mapped[str] = mapped_column(String(64), default="")
    field_label: Mapped[str] = mapped_column(String(255), default="")
    source_value: Mapped[str] = mapped_column(String(255), default="")
    draft_value: Mapped[str] = mapped_column(String(255), default="")
    message: Mapped[str] = mapped_column(Text)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="qa_alerts")
