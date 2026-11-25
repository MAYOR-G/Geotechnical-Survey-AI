from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.settings import WorkspaceSettings


BLANK_STYLE_GUIDE = {
    "tone": "",
    "voice_rules": [],
    "preferred_nomenclature": [],
    "date_format": "",
    "time_format": "",
    "unit_conventions": {},
    "banned_ai_phrases": [],
}


class SettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self) -> WorkspaceSettings:
        res = await self.session.execute(
            select(WorkspaceSettings).where(WorkspaceSettings.id == "default")
        )
        ws = res.scalar_one_or_none()
        if ws is None:
            ws = WorkspaceSettings(
                id="default",
                style_guide_json=dict(BLANK_STYLE_GUIDE),
            )
            self.session.add(ws)
            await self.session.flush()
        elif not ws.style_guide_json:
            ws.style_guide_json = dict(BLANK_STYLE_GUIDE)
            await self.session.flush()
        return ws

    async def update(self, updates: dict) -> WorkspaceSettings:
        ws = await self.get_or_create()
        for key, value in updates.items():
            if value is not None and hasattr(ws, key):
                setattr(ws, key, value)
        ws.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return ws
