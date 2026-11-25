from app.models.clarification import ClarificationItem, QaAlert
from app.models.project import Project, ProjectAttachment, ProjectInputFile
from app.models.research import ResearchThread
from app.models.settings import WorkspaceSettings
from app.models.vault import GalleryAsset, VaultChunk, VaultDocument


def serialize_settings(ws: WorkspaceSettings) -> dict:
    from app.core.config import settings as cfg

    return {
        "id": ws.id,
        "default_contractor_name": ws.default_contractor_name,
        "default_contractor_logo_url": ws.default_contractor_logo_url,
        "author_name": ws.author_name,
        "author_email": ws.author_email,
        "author_designation": ws.author_designation,
        "author_signature_url": ws.author_signature_url,
        "style_guide_json": ws.style_guide_json,
        "openrouter_configured": bool(ws.openrouter_api_key_override or cfg.OPENROUTER_API_KEY),
        "tavily_configured": bool(ws.tavily_api_key_override or cfg.TAVILY_API_KEY),
        "drafting_model": ws.drafting_model,
        "fast_model": ws.fast_model,
        "enable_passcode_gate": ws.enable_passcode_gate,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else "",
    }


def serialize_vault_chunk(chunk: VaultChunk) -> dict:
    return {
        "id": chunk.id,
        "vault_document_id": chunk.vault_document_id,
        "section_type": chunk.section_type,
        "heading_title": chunk.heading_title,
        "content_text": chunk.content_text,
        "tables_json": chunk.tables_json or [],
    }


def serialize_vault_document(doc: VaultDocument) -> dict:
    chunks = getattr(doc, "chunks", []) or []
    imgs = getattr(doc, "extracted_images_json", None) or []
    blueprint = getattr(doc, "pdf_layout_blueprint_json", None) or {}
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_url": doc.file_url,
        "file_type": doc.file_type,
        "document_category": doc.document_category,
        "ingestion_status": doc.ingestion_status,
        "chunk_count": len(chunks),
        "image_count": len(imgs),
        "extracted_images": imgs,
        "pdf_layout_blueprint": blueprint,
        "report_blueprint_json": blueprint,
        "entities_json": blueprint.get("entities_json", {}),
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
        "chunks": [serialize_vault_chunk(c) for c in chunks],
    }


def serialize_gallery_asset(asset: GalleryAsset) -> dict:
    return {
        "id": asset.id,
        "title": asset.title,
        "default_caption": asset.default_caption,
        "category": asset.category,
        "file_url": asset.file_url,
        "tags": asset.tags or [],
        "created_at": asset.created_at.isoformat() if asset.created_at else "",
    }


def serialize_input_file(item: ProjectInputFile) -> dict:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "filename": item.filename,
        "file_url": item.file_url,
        "file_type": item.file_type,
        "parsed_summary_json": item.parsed_summary_json or {},
        "created_at": item.created_at.isoformat() if item.created_at else "",
    }


def serialize_attachment(att: ProjectAttachment) -> dict:
    return {
        "id": att.id,
        "project_id": att.project_id,
        "attachment_number": att.attachment_number,
        "title": att.title,
        "file_url": att.file_url,
        "display_order": att.display_order,
        "page_count": att.page_count,
        "created_at": att.created_at.isoformat() if att.created_at else "",
    }


def serialize_clarification(c: ClarificationItem) -> dict:
    return {
        "id": c.id,
        "project_id": c.project_id,
        "category": c.category,
        "question_text": c.question_text,
        "context_reference": c.context_reference,
        "suggested_answer": c.suggested_answer,
        "user_response": c.user_response,
        "is_resolved": c.is_resolved,
        "omit_section": c.omit_section,
    }


def serialize_qa_alert(a: QaAlert) -> dict:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "severity": a.severity,
        "section_id": a.section_id,
        "field_label": a.field_label,
        "source_value": a.source_value,
        "draft_value": a.draft_value,
        "message": a.message,
        "is_resolved": a.is_resolved,
    }


def serialize_project(proj: Project) -> dict:
    return {
        "id": proj.id,
        "title": proj.title,
        "subtitle": proj.subtitle,
        "document_type": proj.document_type,
        "status": proj.status,
        "client_name": proj.client_name,
        "contractor_name": proj.contractor_name,
        "client_ref_code": proj.client_ref_code,
        "contractor_ref_code": proj.contractor_ref_code,
        "revision_number": proj.revision_number,
        "fao_text": proj.fao_text,
        "water_depth_range": proj.water_depth_range,
        "vessel_name": proj.vessel_name,
        "header_logos_json": proj.header_logos_json or [],
        "revision_history_json": proj.revision_history_json or [],
        "authorization_matrix_json": proj.authorization_matrix_json or [],
        "document_ast_json": proj.document_ast_json or {},
        "compiled_pdf_url": proj.compiled_pdf_url,
        "compiled_docx_url": proj.compiled_docx_url,
        "created_at": proj.created_at.isoformat() if proj.created_at else "",
        "updated_at": proj.updated_at.isoformat() if proj.updated_at else "",
        "input_files": [serialize_input_file(f) for f in (proj.input_files or [])],
        "attachments": [
            serialize_attachment(a)
            for a in sorted((proj.attachments or []), key=lambda x: x.display_order)
        ],
        "clarifications": [serialize_clarification(c) for c in (proj.clarifications or [])],
        "qa_alerts": [serialize_qa_alert(q) for q in (proj.qa_alerts or [])],
    }


def serialize_research_thread(t: ResearchThread) -> dict:
    return {
        "id": t.id,
        "project_id": t.project_id,
        "title": t.title,
        "scope": t.scope,
        "messages_json": t.messages_json or [],
        "created_at": t.created_at.isoformat() if t.created_at else "",
    }
