from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.serializers import serialize_gallery_asset, serialize_vault_document
from app.core.database import get_db_session
from app.models.vault import GalleryAsset, VaultDocument
from app.repositories.settings_repo import SettingsRepository
from app.repositories.vault_repo import VaultRepository
from app.schemas.common import ok_response
from app.services.image_search_service import ImageSearchService
from app.services.storage_service import StorageService
from app.services.vault_ingestor import VaultIngestorService

router = APIRouter()
storage = StorageService()
ingestor = VaultIngestorService(storage)
image_search_service = ImageSearchService(storage)


class ExternalImageSearchBody(BaseModel):
    query: str
    max_results: int = 8


class ExternalImageCacheBody(BaseModel):
    image_url: str
    title: str
    caption: str = ""
    category: str = "map"
    source_url: str = ""


@router.get("/documents")
async def list_vault_documents(session: AsyncSession = Depends(get_db_session)):
    repo = VaultRepository(session)
    docs = await repo.list_documents()
    return ok_response([serialize_vault_document(d) for d in docs])


@router.post("/documents")
async def upload_vault_document(
    file: UploadFile = File(...),
    document_category: str = Form("field_report"),
    session: AsyncSession = Depends(get_db_session),
):
    content = await file.read()
    filename = file.filename or "vault_report.docx"
    url, _ = storage.save_bytes("project-inputs", filename, content)
    ext = Path(filename).suffix.lower().lstrip(".") or "docx"

    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()
    openrouter_key = ws.openrouter_api_key_override

    doc_id = f"vdoc-{uuid.uuid4().hex[:10]}"
    chunks, extracted_assets, extracted_meta, blueprint = ingestor.ingest_with_blueprint(
        doc_id, filename, content
    )

    extracted_style = await ingestor.extract_style_fingerprint(
        filename=filename,
        chunks=chunks,
        openrouter_key=openrouter_key,
    )
    doc = VaultDocument(
        id=doc_id,
        filename=filename,
        file_url=url,
        file_type=ext,
        document_category=document_category,
        ingestion_status="indexed",
        extracted_images_json=extracted_meta,
        pdf_layout_blueprint_json=blueprint,
    )
    repo = VaultRepository(session)
    saved = await repo.create_document(doc, chunks, openrouter_key=openrouter_key)

    for asset in extracted_assets:
        await repo.create_gallery_asset(asset)

    current_style = dict(ws.style_guide_json or {})
    merged_nomenclature = list(
        dict.fromkeys(
            (current_style.get("preferred_nomenclature") or [])
            + (extracted_style.get("preferred_nomenclature") or [])
        )
    )
    merged_rules = list(
        dict.fromkeys(
            (current_style.get("voice_rules") or [])
            + (extracted_style.get("voice_rules") or [])
        )
    )
    merged_banned = list(
        dict.fromkeys(
            (current_style.get("banned_ai_phrases") or [])
            + (extracted_style.get("banned_ai_phrases") or [])
        )
    )
    ws.style_guide_json = {
        "tone": extracted_style.get("tone") or current_style.get("tone") or "",
        "voice_rules": merged_rules,
        "preferred_nomenclature": merged_nomenclature,
        "date_format": extracted_style.get("date_format") or current_style.get("date_format") or "",
        "time_format": extracted_style.get("time_format") or current_style.get("time_format") or "",
        "unit_conventions": {
            **(current_style.get("unit_conventions") or {}),
            **(extracted_style.get("unit_conventions") or {}),
        },
        "standard_equations": extracted_style.get("standard_equations")
        or current_style.get("standard_equations")
        or [],
        "banned_ai_phrases": merged_banned,
    }

    await session.commit()
    return ok_response(serialize_vault_document(saved))


@router.delete("/documents/{doc_id}")
async def delete_vault_document(
    doc_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = VaultRepository(session)
    doc = await repo.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Vault document not found.")
    storage.delete_by_url(doc.file_url)
    await repo.delete_document(doc_id)
    await session.commit()
    return ok_response({"deleted": True})


@router.get("/gallery")
async def list_gallery(session: AsyncSession = Depends(get_db_session)):
    repo = VaultRepository(session)
    assets = await repo.list_gallery()
    return ok_response([serialize_gallery_asset(a) for a in assets])


@router.post("/gallery")
async def upload_gallery_asset(
    file: UploadFile = File(...),
    title: str = Form(...),
    default_caption: str = Form(""),
    category: str = Form("field_photo"),
    tags: str = Form(""),
    session: AsyncSession = Depends(get_db_session),
):
    content = await file.read()
    filename = file.filename or "equipment.png"
    url, _ = storage.save_bytes("equipment-gallery", filename, content)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    asset = GalleryAsset(
        title=title,
        default_caption=default_caption or title,
        category=category,
        file_url=url,
        tags=tag_list,
    )
    repo = VaultRepository(session)
    saved = await repo.create_gallery_asset(asset)
    await session.commit()
    return ok_response(serialize_gallery_asset(saved))


@router.delete("/gallery/{asset_id}")
async def delete_gallery_asset(
    asset_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = VaultRepository(session)
    asset = await repo.get_gallery_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Gallery asset not found.")
    storage.delete_by_url(asset.file_url)
    await repo.delete_gallery_asset(asset_id)
    await session.commit()
    return ok_response({"deleted": True})


@router.post("/images/search")
async def search_external_technical_images(
    body: ExternalImageSearchBody,
    session: AsyncSession = Depends(get_db_session),
):
    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()
    results = await image_search_service.search_external_images(
        query=body.query,
        max_results=body.max_results,
        tavily_key_override=ws.tavily_api_key_override,
    )
    return ok_response(results)


@router.post("/images/cache")
async def cache_external_technical_image(
    body: ExternalImageCacheBody,
    session: AsyncSession = Depends(get_db_session),
):
    asset, _ = await image_search_service.cache_external_image(
        image_url=body.image_url,
        title=body.title,
        caption=body.caption,
        category=body.category,
        source_url=body.source_url,
    )
    repo = VaultRepository(session)
    saved = await repo.create_gallery_asset(asset)
    await session.commit()
    return ok_response(serialize_gallery_asset(saved))
