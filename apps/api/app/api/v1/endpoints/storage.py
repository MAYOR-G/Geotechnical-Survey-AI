from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings
from app.services.storage_service import StorageService

router = APIRouter()

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


@router.get("/{bucket}/{filename}")
async def serve_storage_file(bucket: str, filename: str, download: bool = False):
    if bucket not in StorageService.VALID_BUCKETS:
        raise HTTPException(status_code=404, detail="Bucket not found.")

    target = (settings.STORAGE_ROOT / bucket / Path(filename).name).resolve()
    if not target.exists() or settings.STORAGE_ROOT.resolve() not in target.parents:
        raise HTTPException(status_code=404, detail="File not found.")

    ext = target.suffix.lower()
    media_type = MEDIA_TYPES.get(ext, "application/octet-stream")
    headers = {
        "Cache-Control": "no-cache, must-revalidate"
        if bucket == "compiled-exports"
        else "public, max-age=3600",
    }
    if download:
        clean_dl_name = target.name
        headers["Content-Disposition"] = f'attachment; filename="{clean_dl_name}"'
    return FileResponse(path=str(target), media_type=media_type, headers=headers)
