from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.serializers import serialize_settings
from app.core.database import get_db_session
from app.repositories.settings_repo import SettingsRepository
from app.schemas.common import ok_response
from app.schemas.vault import SettingsUpdate
from app.services.storage_service import StorageService

router = APIRouter()
storage = StorageService()


@router.get("")
async def get_settings(session: AsyncSession = Depends(get_db_session)):
    repo = SettingsRepository(session)
    ws = await repo.get_or_create()
    await session.commit()
    return ok_response(serialize_settings(ws))


@router.patch("")
async def update_settings(
    body: SettingsUpdate, session: AsyncSession = Depends(get_db_session)
):
    repo = SettingsRepository(session)
    updates = body.model_dump(exclude_none=True)
    ws = await repo.update(updates)
    await session.commit()
    return ok_response(serialize_settings(ws))


@router.post("/upload-asset")
async def upload_branding_asset(
    file: UploadFile = File(...),
    kind: str = Form("logo"),
    session: AsyncSession = Depends(get_db_session),
):
    content = await file.read()
    repo = SettingsRepository(session)
    ws = await repo.get_or_create()
    if kind == "signature" and ws.author_signature_url:
        storage.delete_by_url(ws.author_signature_url)
    elif kind != "signature" and ws.default_contractor_logo_url:
        storage.delete_by_url(ws.default_contractor_logo_url)

    url, _ = storage.save_bytes("branding-assets", file.filename or f"{kind}.png", content)
    if kind == "signature":
        await repo.update({"author_signature_url": url})
    else:
        await repo.update({"default_contractor_logo_url": url})
    await session.commit()
    return ok_response({"url": url})
