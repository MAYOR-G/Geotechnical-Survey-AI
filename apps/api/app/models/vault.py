from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class VaultDocument(Base):
    __tablename__ = "vault_documents"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"vdoc-{uuid.uuid4().hex[:10]}"
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(Text, default="")
    file_type: Mapped[str] = mapped_column(String(32), default="docx")
    document_category: Mapped[str] = mapped_column(String(64), default="field_report")
    ingestion_status: Mapped[str] = mapped_column(String(32), default="indexed")
    extracted_images_json: Mapped[list] = mapped_column(JSON, default=list)
    pdf_layout_blueprint_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    chunks: Mapped[list["VaultChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    @property
    def report_blueprint_json(self) -> dict:
        return self.pdf_layout_blueprint_json or {}

    @property
    def entities_json(self) -> dict:
        return (self.pdf_layout_blueprint_json or {}).get("entities_json", {})


class VaultChunk(Base):
    __tablename__ = "vault_chunks"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"vchk-{uuid.uuid4().hex[:10]}"
    )
    vault_document_id: Mapped[str] = mapped_column(
        ForeignKey("vault_documents.id", ondelete="CASCADE")
    )
    section_type: Mapped[str] = mapped_column(String(64), default="Procedures")
    heading_title: Mapped[str] = mapped_column(String(255))
    content_text: Mapped[str] = mapped_column(Text)
    tables_json: Mapped[list] = mapped_column(JSON, default=list)
    # Stored as JSON float list locally (portable across SQLite & Postgres)
    embedding_json: Mapped[list] = mapped_column(JSON, default=list)

    document: Mapped["VaultDocument"] = relationship(back_populates="chunks")


class GalleryAsset(Base):
    __tablename__ = "gallery_assets"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"gal-{uuid.uuid4().hex[:10]}"
    )
    title: Mapped[str] = mapped_column(String(255))
    default_caption: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), default="equipment")
    file_url: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
