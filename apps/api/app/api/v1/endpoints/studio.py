import asyncio
import json
import re
import time
from typing import Any
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.drafting_agent import StyleDraftingAgent
from app.agents.intake_agent import IntakeClarifierAgent
from app.agents.qa_humanizer_agent import QaHumanizerAgent
from app.agents.research_agent import ResearchAgent
from app.api.v1.serializers import (
    serialize_attachment,
    serialize_project,
    serialize_qa_alert,
)
from app.core.database import AsyncSessionLocal, get_db_session
from app.core.exceptions import AppError
from app.models.project import Project, ProjectAttachment
from app.repositories.project_repo import ProjectRepository
from app.repositories.settings_repo import SettingsRepository
from app.repositories.vault_repo import VaultRepository
from app.schemas.agent import ChatStreamRequest, QaResolveRequest
from app.schemas.common import ok_response
from app.schemas.project import (
    AttachmentReorderRequest,
    InlineEditRequest,
    SectionChartRequest,
    SectionExpandRequest,
)
from app.services.chart_generator import (
    ScientificChartGenerator,
    extract_project_chart_params,
)
from app.services.docx_compiler import DocxCompilerService
from app.services.pdf_compiler import PdfCompilerService
from app.services.storage_service import StorageService

router = APIRouter()
storage = StorageService()
intake_agent = IntakeClarifierAgent()
drafter = StyleDraftingAgent(storage)
qa_agent = QaHumanizerAgent()
research_agent = ResearchAgent()
pdf_compiler = PdfCompilerService(storage)
docx_compiler = DocxCompilerService(storage)
chart_generator = ScientificChartGenerator(storage)


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _summarize_intake_files(proj: Project) -> str:
    """Honest, exact summary of uploaded intake files — zero fabricated row/column counts."""
    if not proj.input_files:
        return (
            f"0 raw files uploaded — authoring from project specification (`{proj.title}`)"
            + (f" & scope (`{proj.subtitle[:90]}`)" if proj.subtitle else "")
            + "."
        )
    file_bits = []
    total_rows = 0
    total_cols = 0
    for f in proj.input_files:
        s = f.parsed_summary_json or {}
        tbls = s.get("tables") or []
        r_cnt = sum(int(t.get("row_count") or len(t.get("rows") or [])) for t in tbls)
        c_cnt = max((len(t.get("columns") or []) for t in tbls), default=0)
        total_rows += r_cnt
        total_cols = max(total_cols, c_cnt)
        if tbls:
            file_bits.append(f"`{f.filename}` ({len(tbls)} table(s), {r_cnt} rows)")
        else:
            chars = len((s.get("raw_text") or "").strip())
            file_bits.append(f"`{f.filename}` ({chars:,} chars text)")
    if total_rows > 0:
        return (
            f"Parsed {', '.join(file_bits)} · `{total_rows} total rows` across "
            f"up to `{total_cols} columns` with exact decimal preservation."
        )
    return f"Parsed {', '.join(file_bits)}."


async def _execute_full_5_stage_pipeline(
    session: AsyncSession,
    proj: Project,
    prompt_notes: str = "",
):
    """
    Async generator yielding live SSE events across all 5 rigorous pipeline stages:
      Stage 1: Intake & Verification Analyst
      Stage 2: Autonomous Vault + Web Research Agent
      Stage 3: Iterative 7-Call Section-by-Section Technical Drafter + Tri-Source Visuals
      Stage 4: Independent Cross-Checker & Numeric QA Agent (kind='verify')
      Stage 5: Senior Engineering Anti-AI Humanizer Agent (kind='thought')
      Final:   Typst A4 PDF + Editable Word (.docx) Compilation (kind='tool')
    """
    repo = ProjectRepository(session)
    settings_repo = SettingsRepository(session)
    vault_repo = VaultRepository(session)
    ws = await settings_repo.get_or_create()

    # STAGE 1: Deterministic Intake & File Verification
    t0 = time.perf_counter()
    step1_start = {
        "id": "stage1-intake",
        "kind": "read",
        "status": "running",
        "title": "Stage 1 — Inspecting project specification & uploaded raw files...",
        "detail": f"{len(proj.input_files or [])} raw file(s) attached",
    }
    yield sse_event("reasoning_step", step1_start)
    intake_summary = _summarize_intake_files(proj)
    step1_done = {
        "id": "stage1-intake",
        "kind": "read",
        "status": "done",
        "title": "Stage 1 — Verified project inputs & deterministic table structures",
        "duration": max(1, int((time.perf_counter() - t0) * 1000)),
        "output": intake_summary,
    }
    yield sse_event("reasoning_step", step1_done)

    # STAGE 2A: Knowledge Vault Memory Retrieval
    t1 = time.perf_counter()
    step2a_start = {
        "id": "stage2-vault",
        "kind": "query",
        "status": "running",
        "title": "Stage 2A — Querying Knowledge Vault for institutional style rules & blueprints...",
        "detail": "Semantic chunk index & extracted visual gallery",
    }
    yield sse_event("reasoning_step", step2a_start)
    vault_docs = await vault_repo.list_documents()
    gallery_assets = await vault_repo.list_gallery()
    vault_output = (
        f"Loaded **{len(vault_docs)}** indexed Vault report(s) ("
        + ", ".join(f"`{d.filename}`" for d in vault_docs[:3])
        + f") and `{len(gallery_assets)}` gallery visuals/logos."
        if vault_docs
        else f"0 Vault reports indexed (`{len(gallery_assets)}` gallery visuals) — applying geotechnical engineering baseline voice."
    )
    step2a_done = {
        "id": "stage2-vault",
        "kind": "query",
        "status": "done",
        "title": "Stage 2A — Retrieved Knowledge Vault institutional memory",
        "duration": max(1, int((time.perf_counter() - t1) * 1000)),
        "output": vault_output,
    }
    yield sse_event("reasoning_step", step2a_done)

    # STAGE 2B: Autonomous External Web & Standards Research (Tavily)
    t2 = time.perf_counter()
    step2b_start = {
        "id": "stage2-web-research",
        "kind": "search",
        "status": "running",
        "title": "Stage 2B — Researching regional geology & applicable engineering standards via live web search...",
        "detail": "BS 1377, EN 1997, ISO 19901-8, ASTM F1962 & regional stratigraphy",
    }
    yield sse_event("reasoning_step", step2b_start)
    search_query = f"{proj.title} {proj.subtitle or ''} regional geology BS 1377 EN 1997 ISO 19901-8 ASTM F1962".strip()
    std_sources = await research_agent._search_tavily(
        search_query,
        ws.tavily_api_key_override,
        max_results=5,
    )
    step2b_done = {
        "id": "stage2-web-research",
        "kind": "search",
        "status": "done",
        "title": f"Stage 2B — Retrieved {len(std_sources)} live external geological & standards references",
        "duration": max(1, int((time.perf_counter() - t2) * 1000)),
        "results": [
            {"title": s["title"], "site": s["site"], "url": s.get("url")}
            for s in std_sources
        ],
    }
    yield sse_event("reasoning_step", step2b_done)

    # STAGE 3: Iterative 7-Call Section-by-Section Technical Drafter + Tri-Source Visuals
    proj.status = "drafting"
    await repo.save_project(proj)

    q: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()

    async def on_drafter_step(ev_type: str, payload: dict[str, Any]) -> None:
        await q.put((ev_type, payload))

    async def run_drafter() -> None:
        try:
            res_ast = await drafter.draft_document(
                project=proj,
                style_guide=ws.style_guide_json or {},
                vault_repo=vault_repo,
                openrouter_key=ws.openrouter_api_key_override,
                tavily_key=ws.tavily_api_key_override,
                research_sources=std_sources,
                prompt_notes=prompt_notes,
                force_regenerate=True,
                step_callback=on_drafter_step,
            )
            await q.put(("__ast_done__", res_ast))
        except AppError as app_exc:
            await q.put(("__ast_err__", {"code": app_exc.code, "error": app_exc.message}))
        except Exception as exc:
            await q.put(("__ast_err__", {"code": "DRAFTING_ERROR", "error": str(exc)}))

    drafter_task = asyncio.create_task(run_drafter())
    ast: dict[str, Any] = {}
    while True:
        item = await q.get()
        if item is None:
            break
        ev_type, payload = item
        if ev_type == "__ast_done__":
            ast = payload
            break
        if ev_type == "__ast_err__":
            await drafter_task
            raise AppError(
                code=payload.get("code", "DRAFTING_ERROR"),
                message=payload.get("error", "Drafting failed"),
                status_code=502,
            )
        step_payload = dict(payload)
        if ev_type == "step_done":
            step_payload["status"] = "done"
        elif ev_type == "step_start":
            step_payload["status"] = "running"
        yield sse_event("reasoning_step", step_payload)
    await drafter_task

    # STAGE 4: Independent Cross-Checker & Numeric QA Agent
    t_qa = time.perf_counter()
    qa_start = {
        "id": "stage4-crosscheck",
        "kind": "verify",
        "status": "running",
        "title": "Stage 4 — Running Independent Numeric & Coordinate QA Cross-Check...",
        "detail": "Auditing drafted chapters & tables against raw uploaded files and research facts",
    }
    yield sse_event("reasoning_step", qa_start)
    alerts = await qa_agent.run_independent_qa_crosscheck(
        project=proj,
        document_ast=ast,
        research_sources=std_sources,
        openrouter_key=ws.openrouter_api_key_override,
    )
    await repo.clear_qa_alerts(proj.id)
    for al in alerts:
        await repo.add_qa_alert(al)
    qa_done = {
        "id": "stage4-crosscheck",
        "kind": "verify",
        "status": "done",
        "title": "Stage 4 — Completed Independent Numeric & Factual QA Cross-Check",
        "duration": max(1, int((time.perf_counter() - t_qa) * 1000)),
        "output": (
            f"Cross-checked **{len(ast.get('sections', []))}** chapters · "
            f"`{len(alerts)}` numeric QA alert(s) logged."
        ),
    }
    yield sse_event("reasoning_step", qa_done)

    # STAGE 5: Senior Engineering Anti-AI Humanizer Agent (Tier-2 Editorial Pass)
    t_hum = time.perf_counter()
    hum_start = {
        "id": "stage5-humanizer",
        "kind": "thought",
        "status": "running",
        "title": "Stage 5 — Running Senior Engineering Anti-AI Humanizer editorial pass...",
        "detail": "Stripping AI clichés & enforcing authentic geotechnical consultancy cadence",
    }
    yield sse_event("reasoning_step", hum_start)
    ast, stripped = await qa_agent.run_senior_humanizer_pass(
        document_ast=ast,
        style_guide=ws.style_guide_json or {},
        openrouter_key=ws.openrouter_api_key_override,
    )
    proj.document_ast_json = ast
    proj.status = "review"
    await repo.save_project(proj)

    hum_done = {
        "id": "stage5-humanizer",
        "kind": "thought",
        "status": "done",
        "title": "Stage 5 — Completed Senior Engineering Anti-AI Humanizer editorial pass",
        "duration": max(1, int((time.perf_counter() - t_hum) * 1000)),
        "output": (
            f"Polished **{len(ast.get('sections', []))}** chapters in consultancy voice · "
            f"`{stripped}` generic AI phrase(s) eliminated."
        ),
    }
    yield sse_event("reasoning_step", hum_done)

    # FINAL STAGE: Typst A4 PDF + Editable Word (.docx) Compilation
    t_typ = time.perf_counter()
    typ_start = {
        "id": "stage6-typst-compile",
        "kind": "tool",
        "status": "running",
        "title": "Typesetting paginated A4 PDF (via Typst) & editable Word (.docx) deliverable...",
        "detail": "Clickable TOC, List of Figures, List of Tables & corporate running headers",
    }
    yield sse_event("reasoning_step", typ_start)

    pdf_url, page_count = pdf_compiler.compile_project_pdf(proj)
    docx_url = docx_compiler.compile_project_docx(proj)
    proj.compiled_pdf_url = pdf_url
    proj.compiled_docx_url = docx_url
    proj = await repo.save_project(proj)
    await session.commit()

    typ_done = {
        "id": "stage6-typst-compile",
        "kind": "tool",
        "status": "done",
        "title": f"Typeset {page_count}-page A4 PDF (Typst) & editable Word (.docx) deliverable",
        "duration": max(1, int((time.perf_counter() - t_typ) * 1000)),
        "output": f"Compiled **{page_count} A4 pages** with clickable TOC/LOF/LOT and **.docx** export.",
    }
    yield sse_event("reasoning_step", typ_done)

    total_tables = sum(len(s.get("tables") or []) for s in ast.get("sections", []))
    total_figs = sum(len(s.get("placeholders") or []) for s in ast.get("sections", []))
    answer = (
        f"Completed the 5-stage multi-agent authoring, cross-checking, humanization, and A4 typesetting pipeline for **{proj.title}** (`{proj.revision_number}`).\n\n"
        f"- **Paginated A4 Deliverable:** **{page_count} pages** typeset across **{len(ast.get('sections', []))}** chapters with clickable Table of Contents, List of Tables, and List of Figures.\n"
        f"- **Tables & Visuals:** **{total_tables}** structured engineering tables and **{total_figs}** figures/scientific charts embedded.\n"
        f"- **QA & Editorial Verification:** `{len(alerts)}` numeric discrepancy alert(s) logged; `{stripped}` generic AI phrase(s) removed.\n\n"
        "Review and refine any section in the **Block Editor** alongside the **Live A4 PDF** preview."
    )

    yield sse_event(
        "complete",
        {
            "answer": answer,
            "sources": std_sources,
            "project": serialize_project(proj),
            "page_count": page_count,
            "artifact": {
                "id": proj.id,
                "title": proj.title,
                "subtitle": f"{page_count} A4 pages · {total_tables} tables · {total_figs} figures",
                "sectionCount": len(ast.get("sections", [])),
                "revision": proj.revision_number,
            },
        },
    )


@router.post("/{project_id}/generate-draft")
async def generate_draft_stream(project_id: str):
    async def event_stream():
        async with AsyncSessionLocal() as session:
            try:
                repo = ProjectRepository(session)
                proj = await repo.get_project(project_id)
                if not proj:
                    yield sse_event("error", {"code": "NOT_FOUND", "message": "Project not found."})
                    return

                unresolved = [
                    c
                    for c in (proj.clarifications or [])
                    if not c.is_resolved and not c.omit_section
                ]
                if unresolved:
                    for c in unresolved:
                        yield sse_event(
                            "approval_needed",
                            {
                                "id": f"clar-{c.id}",
                                "clarification_id": c.id,
                                "title": "Project verification required before drafting",
                                "detail": c.context_reference,
                                "message": c.question_text,
                                "allowLabel": "Confirm & Apply",
                                "denyLabel": "Omit Item",
                                "inputPlaceholder": c.suggested_answer or "Enter verified value...",
                            },
                        )
                    yield sse_event(
                        "complete",
                        {
                            "answer": (
                                f"Paused before drafting: please confirm or omit the **{len(unresolved)}** "
                                "verification item(s) above, then click **Generate Full Report**."
                            ),
                            "project": serialize_project(proj),
                        },
                    )
                    return

                async for chunk in _execute_full_5_stage_pipeline(session, proj):
                    yield chunk
            except AppError as exc:
                await session.rollback()
                yield sse_event("error", {"code": exc.code, "message": exc.message})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{project_id}/chat-stream")
async def studio_chat_stream(project_id: str, body: ChatStreamRequest):
    async def event_stream():
        async with AsyncSessionLocal() as session:
            try:
                repo = ProjectRepository(session)
                proj = await repo.get_project(project_id)
                if not proj:
                    yield sse_event("error", {"code": "NOT_FOUND", "message": "Project not found."})
                    return

                settings_repo = SettingsRepository(session)
                vault_repo = VaultRepository(session)
                ws = await settings_repo.get_or_create()
                msg_lower = body.message.lower().strip()

                # Branch A: Grounded Research / Standards Question inside Studio
                is_research_only = (
                    any(
                        w in msg_lower
                        for w in ("what is", "what are", "explain", "research", "summarize standard", "iso ", "astm ", "bs 1377", "eurocode")
                    )
                    and not any(
                        w in msg_lower
                        for w in ("draft", "generate", "full report", "pipeline", "write report", "compile")
                    )
                )
                if is_research_only:
                    q_res: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()

                    async def on_res_step(st: dict[str, Any]) -> None:
                        await q_res.put(("reasoning_step", st))

                    async def run_res() -> None:
                        try:
                            res_out = await research_agent.query(
                                query=body.message,
                                scope="both",
                                vault_repo=vault_repo,
                                openrouter_key=ws.openrouter_api_key_override,
                                tavily_key=ws.tavily_api_key_override,
                                step_callback=on_res_step,
                            )
                            await q_res.put(("__done__", res_out))
                        except AppError as exc:
                            await q_res.put(("error", {"code": exc.code, "message": exc.message}))
                        except Exception as exc:
                            await q_res.put(("error", {"code": "RESEARCH_ERROR", "message": str(exc)}))

                    t_res_task = asyncio.create_task(run_res())
                    res_final: dict[str, Any] | None = None
                    while True:
                        ev_n, pl = await q_res.get()
                        if ev_n == "__done__":
                            res_final = pl
                            break
                        if ev_n == "error":
                            yield sse_event("error", pl)
                            await t_res_task
                            return
                        yield sse_event(ev_n, pl)
                    await t_res_task

                    if res_final:
                        yield sse_event("sources", {"sources": res_final["sources"]})
                        yield sse_event(
                            "complete",
                            {
                                "answer": res_final["answer"],
                                "sources": res_final["sources"],
                                "project": serialize_project(proj),
                            },
                        )
                    return

                # Stage 1 Intake Clarification Gate when starting a fresh report with unverified details
                has_sections = bool((proj.document_ast_json or {}).get("sections"))
                bypass_gate = any(
                    kw in msg_lower
                    for kw in ("proceed", "continue", "standard assumption", "force", "approved", "confirm all")
                )

                if not has_sections and not proj.clarifications and not bypass_gate:
                    t_int = time.perf_counter()
                    int_start = {
                        "id": "intake-verify",
                        "kind": "verify",
                        "status": "running",
                        "title": "Stage 1 — Running Intake Gap & Blueprint Verification...",
                        "detail": "Checking project metadata & raw files for missing engineering controls",
                    }
                    yield sse_event("reasoning_step", int_start)

                    generated_clars = await intake_agent.analyze(
                        proj,
                        proj.input_files or [],
                        prompt=body.message,
                        api_key_override=ws.openrouter_api_key_override,
                    )
                    for item in generated_clars:
                        await repo.add_clarification(item)
                    if generated_clars:
                        proj.status = "clarifying"
                        await repo.save_project(proj)
                        await session.commit()
                        proj = await repo.get_project(project_id) or proj

                    int_done = {
                        "id": "intake-verify",
                        "kind": "verify",
                        "status": "done",
                        "title": "Stage 1 — Completed Intake Gap & Blueprint Verification",
                        "duration": max(1, int((time.perf_counter() - t_int) * 1000)),
                        "output": f"Identified `{len(generated_clars)}` project-specific verification item(s).",
                    }
                    yield sse_event("reasoning_step", int_done)

                unresolved = [
                    c
                    for c in (proj.clarifications or [])
                    if not c.is_resolved and not c.omit_section
                ]
                if unresolved and not bypass_gate and not has_sections:
                    for c in unresolved:
                        yield sse_event(
                            "approval_needed",
                            {
                                "id": f"clar-{c.id}",
                                "clarification_id": c.id,
                                "title": "Confirm project variable before drafting",
                                "detail": c.context_reference,
                                "message": c.question_text,
                                "allowLabel": "Approve & Use Value",
                                "denyLabel": "Omit Item",
                                "inputPlaceholder": c.suggested_answer or "Enter verified value...",
                            },
                        )
                    yield sse_event(
                        "complete",
                        {
                            "answer": (
                                f"I reviewed **{proj.title}** and identified **{len(unresolved)}** project-specific item(s) "
                                "to verify so zero coordinates, client details, or design parameters are guessed.\n\n"
                                "Confirm or adjust each card above (or reply **\"Proceed with standard assumptions\"**) to launch the full 5-stage report generation pipeline."
                            ),
                            "project": serialize_project(proj),
                        },
                    )
                    return

                if bypass_gate and unresolved:
                    for c in unresolved:
                        c.user_response = c.suggested_answer or "Confirmed per standard project specification"
                        c.is_resolved = True
                    await session.commit()
                    proj = await repo.get_project(project_id) or proj

                # Branch B: Full 5-Stage Multi-Agent Authoring, QA, Humanizer & Typst Compilation
                async for chunk in _execute_full_5_stage_pipeline(
                    session, proj, prompt_notes=body.message
                ):
                    yield chunk

            except AppError as exc:
                await session.rollback()
                yield sse_event("error", {"code": exc.code, "message": exc.message})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{project_id}/inline-edit")
async def inline_edit_selection(
    project_id: str,
    body: InlineEditRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()
    revised, notes = await qa_agent.inline_rewrite(
        selection_text=body.selection_text,
        instruction=body.instruction,
        style_guide=ws.style_guide_json or {},
        openrouter_key=ws.openrouter_api_key_override,
    )
    return ok_response({"revised_text": revised, "style_notes": notes})


@router.post("/{project_id}/sections/{section_id}/expand")
async def expand_report_section(
    project_id: str,
    section_id: str,
    body: SectionExpandRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()

    ast = dict(proj.document_ast_json or {})
    sections = list(ast.get("sections") or [])
    target_idx = next(
        (i for i, s in enumerate(sections) if s.get("id") == section_id), -1
    )
    if target_idx == -1:
        raise HTTPException(status_code=404, detail="Section not found in document AST.")

    updated_sec = await qa_agent.expand_section(
        section=dict(sections[target_idx]),
        instruction=body.instruction,
        style_guide=ws.style_guide_json or {},
        openrouter_key=ws.openrouter_api_key_override,
    )
    sections[target_idx] = updated_sec
    ast["sections"] = sections
    proj.document_ast_json = ast

    pdf_url, page_count = pdf_compiler.compile_project_pdf(proj)
    docx_url = docx_compiler.compile_project_docx(proj)
    proj.compiled_pdf_url = pdf_url
    proj.compiled_docx_url = docx_url
    proj = await repo.save_project(proj)
    await session.commit()

    return ok_response(
        {
            "project": serialize_project(proj),
            "section": updated_sec,
            "page_count": page_count,
        }
    )


@router.post("/{project_id}/sections/{section_id}/generate-chart")
async def generate_section_chart(
    project_id: str,
    section_id: str,
    body: SectionChartRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    ast = dict(proj.document_ast_json or {})
    sections = list(ast.get("sections") or [])
    target_idx = next(
        (i for i, s in enumerate(sections) if s.get("id") == section_id), -1
    )
    if target_idx == -1:
        raise HTTPException(status_code=404, detail="Section not found.")

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", proj.contractor_ref_code or proj.id)[:36]
    params = extract_project_chart_params(proj)
    ct = body.chart_type.lower()
    if "moisture" in ct or "density" in ct:
        chart = chart_generator.generate_moisture_density_depth_chart(slug, params)
    elif "shear" in ct or "triaxial" in ct:
        chart = chart_generator.generate_shear_strength_depth_chart(slug, params)
    elif "long" in ct or "bore" in ct:
        chart = chart_generator.generate_hdd_long_section_chart(slug, params)
    elif "hazard" in ct:
        chart = chart_generator.generate_geohazard_chainage_chart(slug, params)
    else:
        chart = chart_generator.generate_casagrande_plasticity_chart(slug, params)

    sec = dict(sections[target_idx])
    placeholders = list(sec.get("placeholders") or [])
    fig_num = f"Figure {sec.get('section_number', '').rstrip('.')}.{len(placeholders) + 1}"
    placeholders.append(
        {
            "id": f"ph-gen-{int(time.time() * 1000)}",
            "figure_number": fig_num,
            "prompt": chart["title"],
            "suggested_category": "lab_equipment",
            "resolved_asset_id": f"gen-{ct}",
            "resolved_url": chart["file_url"],
            "caption": chart["caption"],
        }
    )
    sec["placeholders"] = placeholders
    sections[target_idx] = sec
    ast["sections"] = sections
    proj.document_ast_json = ast

    pdf_url, page_count = pdf_compiler.compile_project_pdf(proj)
    proj.compiled_pdf_url = pdf_url
    proj = await repo.save_project(proj)
    await session.commit()

    return ok_response(
        {
            "project": serialize_project(proj),
            "chart": chart,
            "page_count": page_count,
        }
    )


@router.get("/{project_id}/qa-alerts")
async def get_qa_alerts(
    project_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")
    return ok_response([serialize_qa_alert(a) for a in (proj.qa_alerts or [])])


@router.post("/{project_id}/qa-alerts/{alert_id}/resolve")
async def resolve_qa_alert(
    project_id: str,
    alert_id: str,
    body: QaResolveRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    alert = await repo.get_qa_alert(alert_id)
    if not proj or not alert or alert.project_id != project_id:
        raise HTTPException(status_code=404, detail="QA alert not found.")

    if body.apply_fix and alert.draft_value and alert.source_value:
        ast = dict(proj.document_ast_json or {})
        for sec in ast.get("sections", []):
            if sec.get("id") == alert.section_id or alert.draft_value in sec.get("html_content", ""):
                sec["html_content"] = sec.get("html_content", "").replace(
                    alert.draft_value, alert.source_value
                )
        proj.document_ast_json = ast
        pdf_url, _ = pdf_compiler.compile_project_pdf(proj)
        proj.compiled_pdf_url = pdf_url

    alert.is_resolved = True
    proj = await repo.save_project(proj)
    await session.commit()
    return ok_response(
        {"alert": serialize_qa_alert(alert), "project": serialize_project(proj)}
    )


@router.post("/{project_id}/attachments")
async def upload_attachment(
    project_id: str,
    file: UploadFile = File(...),
    title: str = Form("External Geotechnical Attachment"),
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    content = await file.read()
    fname = file.filename or "attachment.pdf"
    url, saved_path = storage.save_bytes("project-inputs", fname, content)
    pages = 1
    try:
        pages = len(PdfReader(str(saved_path)).pages)
    except Exception:
        pages = 1

    next_order = len(proj.attachments) + 1
    att = ProjectAttachment(
        project_id=proj.id,
        attachment_number=f"Attachment {next_order}",
        title=title,
        file_url=url,
        display_order=next_order,
        page_count=pages,
    )
    await repo.add_attachment(att)
    await session.commit()
    return ok_response(serialize_attachment(att))


@router.patch("/{project_id}/attachments/reorder")
async def reorder_attachments(
    project_id: str,
    body: AttachmentReorderRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ProjectRepository(session)
    proj = await repo.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    order_map = {att_id: idx + 1 for idx, att_id in enumerate(body.ordered_ids)}
    for att in proj.attachments:
        if att.id in order_map:
            att.display_order = order_map[att.id]
            att.attachment_number = f"Attachment {att.display_order}"
    await session.commit()

    refreshed = await repo.get_project(project_id)
    return ok_response(
        [
            serialize_attachment(a)
            for a in sorted(refreshed.attachments, key=lambda x: x.display_order)
        ]
    )


@router.delete("/{project_id}/attachments/{att_id}")
async def delete_attachment(
    project_id: str, att_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = ProjectRepository(session)
    att = await repo.get_attachment(att_id)
    if not att or att.project_id != project_id:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    storage.delete_by_url(att.file_url)
    await repo.delete_attachment(att_id)
    await session.commit()
    return ok_response({"deleted": True})
