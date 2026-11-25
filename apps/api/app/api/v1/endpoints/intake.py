from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.intake_agent import IntakeClarifierAgent
from app.api.v1.serializers import serialize_clarification, serialize_input_file
from app.core.database import get_db_session
from app.models.project import ProjectInputFile
from app.repositories.project_repo import ProjectRepository
from app.repositories.settings_repo import SettingsRepository
from app.schemas.agent import IntakeAnalyzeRequest
from app.schemas.common import ok_response
from app.schemas.project import ClarificationBatchPatch
from app.services.intake_parser import IntakeParserService
from app.services.storage_service import StorageService

router = APIRouter()
storage = StorageService()
parser = IntakeParserService()
intake_agent = IntakeClarifierAgent()


@router.post("/{project_id}/intake-files")
async def upload_intake_files(
    project_id: str,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    uploaded: list[ProjectInputFile] = []
    for f in files:
        content = await f.read()
        fname = f.filename or "upload.csv"
        url, _ = storage.save_bytes("project-inputs", fname, content)
        parsed = parser.parse_file(fname, content)
        ext = Path(fname).suffix.lower().lstrip(".") or "txt"
        rec = ProjectInputFile(
            project_id=proj.id,
            filename=fname,
            file_url=url,
            file_type=ext,
            parsed_summary_json=parsed,
        )
        await repo.add_input_file(rec)
        uploaded.append(rec)

    proj = await repo.get_project(project_id)
    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()

    new_clarifications = await intake_agent.analyze(
        proj,
        proj.input_files,
        prompt="",
        api_key_override=ws.openrouter_api_key_override,
    )
    existing_questions = {c.question_text for c in proj.clarifications}
    created_items = []
    for item in new_clarifications:
        if item.question_text not in existing_questions:
            await repo.add_clarification(item)
            created_items.append(item)

    proj.status = "clarifying"
    await repo.save_project(proj)
    await session.commit()

    return ok_response(
        {
            "uploaded": [serialize_input_file(u) for u in uploaded],
            "clarifications": [
                serialize_clarification(c)
                for c in (proj.clarifications or created_items)
            ],
        }
    )


@router.post("/{project_id}/intake-analyze")
async def analyze_intake(
    project_id: str,
    body: IntakeAnalyzeRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()

    items = await intake_agent.analyze(
        proj,
        proj.input_files,
        prompt=body.prompt,
        api_key_override=ws.openrouter_api_key_override,
    )
    existing_q = {c.question_text for c in proj.clarifications}
    for item in items:
        if item.question_text not in existing_q:
            await repo.add_clarification(item)

    proj.status = "clarifying"
    await repo.save_project(proj)
    await session.commit()

    refreshed = await repo.get_project(project_id)
    return ok_response(
        {
            "clarifications": [
                serialize_clarification(c) for c in (refreshed.clarifications or [])
            ]
        }
    )


@router.patch("/{project_id}/clarifications")
async def resolve_clarifications(
    project_id: str,
    body: ClarificationBatchPatch,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    for patch in body.items:
        item = await repo.get_clarification(patch.id)
        if item and item.project_id == project_id:
            item.user_response = patch.user_response
            item.is_resolved = patch.is_resolved
            item.omit_section = patch.omit_section

            if patch.is_resolved and not patch.omit_section and patch.user_response:
                resp = patch.user_response.strip()
                ctx_lower = (item.context_reference or "").lower()
                if "cover" in ctx_lower or "vessel" in ctx_lower or "reference" in ctx_lower:
                    if not proj.client_ref_code:
                        proj.client_ref_code = resp.split("|")[0].strip()[:48]
                    if "m" in resp and (
                        not proj.water_depth_range
                        or proj.water_depth_range.lower().startswith("pending")
                    ):
                        proj.water_depth_range = resp[:48]
                ast = dict(proj.document_ast_json or {})
                sections = list(ast.get("sections") or [])
                if sections:
                    note = f"<p><strong>Engineer Clarification ({item.context_reference}):</strong> {resp}</p>"
                    if resp not in (sections[0].get("html_content") or ""):
                        sections[0]["html_content"] = f"{sections[0].get('html_content', '')}{note}"
                        ast["sections"] = sections
                        proj.document_ast_json = ast

    await session.commit()
    refreshed = await repo.get_project(project_id)
    return ok_response(
        [serialize_clarification(c) for c in (refreshed.clarifications or [])]
    )
