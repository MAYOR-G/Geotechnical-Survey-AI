import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.repositories.project_repo import ProjectRepository
from app.schemas.common import ok_response
from app.schemas.project import ExportRequest
from app.services.docx_compiler import DocxCompilerService
from app.services.pdf_compiler import PdfCompilerService
from app.services.storage_service import StorageService

router = APIRouter()
storage = StorageService()
pdf_compiler = PdfCompilerService(storage)
docx_compiler = DocxCompilerService(storage)


@router.post("/{project_id}/compile-preview")
async def compile_preview(
    project_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    pdf_url, page_count = pdf_compiler.compile_project_pdf(proj)
    proj.compiled_pdf_url = pdf_url
    await repo.save_project(proj)
    await session.commit()
    return ok_response({"compiled_pdf_url": pdf_url, "page_count": page_count})


@router.post("/{project_id}/export")
async def export_project_package(
    project_id: str,
    body: ExportRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    safe_ref = re.sub(
        r"[^a-zA-Z0-9_-]+", "_", proj.contractor_ref_code or proj.id
    )
    fmt = body.format.lower()

    if fmt == "docx":
        docx_url = docx_compiler.compile_project_docx(proj)
        proj.compiled_docx_url = docx_url
        proj.status = "completed"
        await repo.save_project(proj)
        await session.commit()
        return ok_response(
            {
                "download_url": f"{docx_url}?download=true",
                "filename": f"{safe_ref}.docx",
                "format": "docx",
            }
        )

    pdf_url, _ = pdf_compiler.compile_project_pdf(proj)
    proj.compiled_pdf_url = pdf_url
    proj.status = "completed"
    await repo.save_project(proj)
    await session.commit()
    return ok_response(
        {
            "download_url": f"{pdf_url}?download=true",
            "filename": f"{safe_ref}.pdf",
            "format": "pdf",
        }
    )
