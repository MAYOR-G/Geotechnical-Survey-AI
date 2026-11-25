from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"proj-{uuid.uuid4().hex[:10]}"
    )
    title: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str] = mapped_column(String(255), default="")
    document_type: Mapped[str] = mapped_column(
        String(64), default="Geotechnical Survey Field Report"
    )
    status: Mapped[str] = mapped_column(String(32), default="intake")
    client_name: Mapped[str] = mapped_column(String(255), default="")
    contractor_name: Mapped[str] = mapped_column(String(255), default="")
    client_ref_code: Mapped[str] = mapped_column(String(120), default="")
    contractor_ref_code: Mapped[str] = mapped_column(String(120), default="")
    revision_number: Mapped[str] = mapped_column(String(32), default="Rev 01")
    fao_text: Mapped[str] = mapped_column(String(255), default="")
    water_depth_range: Mapped[str] = mapped_column(String(120), default="")
    vessel_name: Mapped[str] = mapped_column(String(120), default="")

    header_logos_json: Mapped[list] = mapped_column(JSON, default=list)
    revision_history_json: Mapped[list] = mapped_column(JSON, default=list)
    authorization_matrix_json: Mapped[list] = mapped_column(JSON, default=list)
    document_ast_json: Mapped[dict] = mapped_column(JSON, default=dict)

    compiled_pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    compiled_docx_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    input_files: Mapped[list["ProjectInputFile"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["ProjectAttachment"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectAttachment.display_order",
    )
    clarifications: Mapped[list["ClarificationItem"]] = relationship(
        "ClarificationItem", back_populates="project", cascade="all, delete-orphan"
    )
    qa_alerts: Mapped[list["QaAlert"]] = relationship(
        "QaAlert", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectInputFile(Base):
    __tablename__ = "project_input_files"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"pin-{uuid.uuid4().hex[:10]}"
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(Text, default="")
    file_type: Mapped[str] = mapped_column(String(32), default="csv")
    parsed_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["Project"] = relationship(back_populates="input_files")


class ProjectAttachment(Base):
    __tablename__ = "project_attachments"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"att-{uuid.uuid4().hex[:10]}"
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    attachment_number: Mapped[str] = mapped_column(String(64), default="Attachment 1")
    title: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=1)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    project: Mapped["Project"] = relationship(back_populates="attachments")
