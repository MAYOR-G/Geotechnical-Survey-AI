from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.serializers import serialize_project
from app.core.database import get_db_session
from app.models.project import Project
from app.repositories.project_repo import ProjectRepository
from app.repositories.settings_repo import SettingsRepository
from app.schemas.common import ok_response
from app.schemas.project import DocumentAstUpdate, ProjectCreate, ProjectUpdate
from app.services.docx_compiler import DocxCompilerService
from app.services.pdf_compiler import PdfCompilerService
from app.services.storage_service import StorageService

router = APIRouter()
storage = StorageService()
pdf_compiler = PdfCompilerService(storage)
docx_compiler = DocxCompilerService(storage)


@router.get("")
async def list_projects(session: AsyncSession = Depends(get_db_session)):
    repo = ProjectRepository(session)
    projects = await repo.list_projects()
    return ok_response([serialize_project(p) for p in projects])


@router.post("")
async def create_project(
    body: ProjectCreate, session: AsyncSession = Depends(get_db_session)
):
    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()

    logos = list(body.header_logos_json or [])
    if not logos and ws.default_contractor_logo_url:
        logos.append(
            {
                "role": "contractor",
                "label": body.contractor_name or ws.default_contractor_name or "Contractor",
                "url": ws.default_contractor_logo_url,
            }
        )

    auth_matrix = list(body.authorization_matrix_json or [])
    if not auth_matrix:
        auth_matrix = [
            {
                "role": "Prepared By",
                "name": ws.author_name or "",
                "designation": ws.author_designation or "",
                "email": ws.author_email or "",
                "date": "",
                "signature_url": ws.author_signature_url or "",
            },
            {
                "role": "Reviewed By",
                "name": "",
                "designation": "",
                "email": "",
                "date": "",
            },
            {
                "role": "Approved By",
                "name": "",
                "designation": "",
                "email": "",
                "date": "",
            },
        ]

    initials = (
        "".join(p[0] + "." for p in ws.author_name.split()[:2])
        if ws.author_name
        else ""
    )
    rev_history = list(body.revision_history_json or [])
    if not rev_history:
        rev_history = [
            {
                "rev": body.revision_number,
                "date": "Draft",
                "description": "IFR",
                "prepared_by": initials,
                "checked_by": "",
                "approved_by": "",
            }
        ]

    initial_ast = {
        "report_title": body.title,
        "report_subtitle": body.subtitle or "",
        "program_title": "",
        "location_line": "",
        "campaign_dates": "",
        "layout_blueprint": {},
        "abbreviations": [],
        "sections": [],
    }

    proj = Project(
        title=body.title,
        subtitle=body.subtitle,
        document_type=body.document_type,
        status="intake",
        client_name=body.client_name,
        contractor_name=body.contractor_name or ws.default_contractor_name or "",
        client_ref_code=body.client_ref_code,
        contractor_ref_code=body.contractor_ref_code,
        revision_number=body.revision_number,
        fao_text=body.fao_text or "",
        water_depth_range=body.water_depth_range or "",
        vessel_name=body.vessel_name or "",
        header_logos_json=logos,
        revision_history_json=rev_history,
        authorization_matrix_json=auth_matrix,
        document_ast_json=initial_ast,
    )
    repo = ProjectRepository(session)
    created = await repo.create_project(proj)

    await session.flush()
    created = await repo.get_project(created.id)
    pdf_url, _ = pdf_compiler.compile_project_pdf(created)
    docx_url = docx_compiler.compile_project_docx(created)
    created.compiled_pdf_url = pdf_url
    created.compiled_docx_url = docx_url
    created = await repo.save_project(created)
    await session.commit()
    refreshed = await repo.get_project(created.id)
    return ok_response(serialize_project(refreshed))


@router.get("/{project_id}")
async def get_project(
    project_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ok_response(serialize_project(proj))


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(proj, key, val)
    saved = await repo.save_project(proj)
    await session.commit()
    return ok_response(serialize_project(saved))


@router.patch("/{project_id}/document")
async def update_project_document(
    project_id: str,
    body: DocumentAstUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    proj.document_ast_json = body.document_ast_json
    saved = await repo.save_project(proj)
    await session.commit()
    return ok_response(serialize_project(saved))


@router.delete("/{project_id}")
async def delete_project(
    project_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    storage.delete_by_url(proj.compiled_pdf_url)
    storage.delete_by_url(proj.compiled_docx_url)
    for f in proj.input_files or []:
        storage.delete_by_url(f.file_url)
    for att in proj.attachments or []:
        storage.delete_by_url(att.file_url)
    await repo.delete_project(project_id)
    await session.commit()
    return ok_response({"deleted": True})
