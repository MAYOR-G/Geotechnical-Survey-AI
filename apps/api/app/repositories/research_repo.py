from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.research import ResearchThread


class ResearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_threads(self) -> list[ResearchThread]:
        res = await self.session.execute(
            select(ResearchThread).order_by(ResearchThread.created_at.desc())
        )
        return list(res.scalars().all())

    async def get_thread(self, thread_id: str) -> Optional[ResearchThread]:
        res = await self.session.execute(
            select(ResearchThread).where(ResearchThread.id == thread_id)
        )
        return res.scalar_one_or_none()

    async def create_thread(self, thread: ResearchThread) -> ResearchThread:
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def save_thread(self, thread: ResearchThread) -> ResearchThread:
        await self.session.flush()
        return thread

    async def delete_thread(self, thread_id: str) -> bool:
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        await self.session.delete(thread)
        await self.session.flush()
        return True
