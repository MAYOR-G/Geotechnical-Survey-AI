import asyncio
from datetime import datetime, timezone
import json
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.research_agent import ResearchAgent
from app.api.v1.serializers import serialize_research_thread
from app.core.database import AsyncSessionLocal, get_db_session
from app.core.exceptions import AppError
from app.models.research import ResearchThread
from app.repositories.research_repo import ResearchRepository
from app.repositories.settings_repo import SettingsRepository
from app.repositories.vault_repo import VaultRepository
from app.schemas.agent import ResearchQueryRequest
from app.schemas.common import ok_response

router = APIRouter()
agent = ResearchAgent()


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.get("/threads")
async def list_threads(session: AsyncSession = Depends(get_db_session)):
    repo = ResearchRepository(session)
    threads = await repo.list_threads()
    return ok_response([serialize_research_thread(t) for t in threads])


@router.post("/query")
async def run_research_query(
    body: ResearchQueryRequest, session: AsyncSession = Depends(get_db_session)
):
    settings_repo = SettingsRepository(session)
    ws = await settings_repo.get_or_create()
    vault_repo = VaultRepository(session)
    research_repo = ResearchRepository(session)

    result = await agent.query(
        query=body.query,
        scope="both",
        vault_repo=vault_repo,
        openrouter_key=ws.openrouter_api_key_override,
        tavily_key=ws.tavily_api_key_override,
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    user_msg = {
        "id": f"rmsg-{uuid.uuid4().hex[:8]}",
        "role": "user",
        "content": body.query,
        "created_at": now_iso,
    }
    assistant_msg = {
        "id": f"rmsg-{uuid.uuid4().hex[:8]}",
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "steps": result["steps"],
        "created_at": now_iso,
    }

    thread = None
    if body.thread_id:
        thread = await research_repo.get_thread(body.thread_id)
    if thread is None:
        title = body.query[:56] + ("..." if len(body.query) > 56 else "")
        thread = ResearchThread(
            project_id=body.project_id,
            title=title,
            scope="both",
            messages_json=[user_msg, assistant_msg],
        )
        thread = await research_repo.create_thread(thread)
    else:
        thread.scope = "both"
        thread.messages_json = list(thread.messages_json or []) + [user_msg, assistant_msg]
        thread = await research_repo.save_thread(thread)

    await session.commit()
    return ok_response(
        {
            "thread": serialize_research_thread(thread),
            "sources": result["sources"],
            "answer": result["answer"],
            "steps": result["steps"],
        }
    )


@router.post("/query-stream")
async def stream_research_query(body: ResearchQueryRequest):
    """Real-time SSE endpoint streaming live Vault + Tavily reasoning steps and grounded citations."""

    async def event_stream():
        async with AsyncSessionLocal() as session:
            try:
                settings_repo = SettingsRepository(session)
                ws = await settings_repo.get_or_create()
                vault_repo = VaultRepository(session)
                research_repo = ResearchRepository(session)

                queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()

                async def on_step(step_payload: dict[str, Any]) -> None:
                    await queue.put(("reasoning_step", step_payload))

                async def run_agent() -> None:
                    try:
                        res = await agent.query(
                            query=body.query,
                            scope="both",
                            vault_repo=vault_repo,
                            openrouter_key=ws.openrouter_api_key_override,
                            tavily_key=ws.tavily_api_key_override,
                            step_callback=on_step,
                        )
                        await queue.put(("__done__", res))
                    except AppError as app_exc:
                        await queue.put(
                            ("error", {"code": app_exc.code, "message": app_exc.message})
                        )
                    except Exception as exc:
                        await queue.put(
                            ("error", {"code": "RESEARCH_ERROR", "message": str(exc)})
                        )

                task = asyncio.create_task(run_agent())
                result: dict[str, Any] | None = None

                while True:
                    ev_name, payload = await queue.get()
                    if ev_name == "__done__":
                        result = payload
                        break
                    if ev_name == "error":
                        yield _sse("error", payload)
                        await task
                        return
                    yield _sse(ev_name, payload)

                await task
                if not result:
                    return

                yield _sse("sources", {"sources": result["sources"]})

                now_iso = datetime.now(timezone.utc).isoformat()
                user_msg = {
                    "id": f"rmsg-{uuid.uuid4().hex[:8]}",
                    "role": "user",
                    "content": body.query,
                    "created_at": now_iso,
                }
                assistant_msg = {
                    "id": f"rmsg-{uuid.uuid4().hex[:8]}",
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result["sources"],
                    "steps": result["steps"],
                    "created_at": now_iso,
                }

                thread = None
                if body.thread_id:
                    thread = await research_repo.get_thread(body.thread_id)
                if thread is None:
                    title = body.query[:56] + ("..." if len(body.query) > 56 else "")
                    thread = ResearchThread(
                        project_id=body.project_id,
                        title=title,
                        scope="both",
                        messages_json=[user_msg, assistant_msg],
                    )
                    thread = await research_repo.create_thread(thread)
                else:
                    thread.scope = "both"
                    thread.messages_json = list(thread.messages_json or []) + [
                        user_msg,
                        assistant_msg,
                    ]
                    thread = await research_repo.save_thread(thread)

                await session.commit()
                yield _sse(
                    "complete",
                    {
                        "thread": serialize_research_thread(thread),
                        "sources": result["sources"],
                        "answer": result["answer"],
                        "steps": result["steps"],
                    },
                )
            except AppError as exc:
                await session.rollback()
                yield _sse("error", {"code": exc.code, "message": exc.message})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str, session: AsyncSession = Depends(get_db_session)
):
    repo = ResearchRepository(session)
    deleted = await repo.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Research thread not found.")
    await session.commit()
    return ok_response({"deleted": True})
