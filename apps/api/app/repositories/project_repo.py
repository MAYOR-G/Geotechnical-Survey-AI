from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.clarification import ClarificationItem, QaAlert
from app.models.project import Project, ProjectAttachment, ProjectInputFile


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_projects(self) -> list[Project]:
        res = await self.session.execute(
            select(Project)
            .options(
                selectinload(Project.input_files),
                selectinload(Project.attachments),
                selectinload(Project.clarifications),
                selectinload(Project.qa_alerts),
            )
            .order_by(Project.updated_at.desc())
        )
        return list(res.scalars().all())

    async def get_project(self, project_id: str) -> Optional[Project]:
        res = await self.session.execute(
            select(Project)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Project.input_files),
                selectinload(Project.attachments),
                selectinload(Project.clarifications),
                selectinload(Project.qa_alerts),
            )
            .where(Project.id == project_id)
        )
        return res.scalar_one_or_none()

    async def create_project(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return await self.get_project(project.id) or project

    async def save_project(self, project: Project) -> Project:
        project.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return await self.get_project(project.id) or project

    async def delete_project(self, project_id: str) -> bool:
        proj = await self.get_project(project_id)
        if not proj:
            return False
        await self.session.delete(proj)
        await self.session.flush()
        return True

    async def add_input_file(self, item: ProjectInputFile) -> ProjectInputFile:
        self.session.add(item)
        await self.session.flush()
        return item

    async def add_clarification(self, item: ClarificationItem) -> ClarificationItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_clarification(self, item_id: str) -> Optional[ClarificationItem]:
        res = await self.session.execute(
            select(ClarificationItem).where(ClarificationItem.id == item_id)
        )
        return res.scalar_one_or_none()

    async def clear_qa_alerts(self, project_id: str) -> None:
        res = await self.session.execute(
            select(QaAlert).where(QaAlert.project_id == project_id)
        )
        for alert in res.scalars().all():
            await self.session.delete(alert)
        await self.session.flush()

    async def add_qa_alert(self, alert: QaAlert) -> QaAlert:
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_qa_alert(self, alert_id: str) -> Optional[QaAlert]:
        res = await self.session.execute(
            select(QaAlert).where(QaAlert.id == alert_id)
        )
        return res.scalar_one_or_none()

    async def add_attachment(self, att: ProjectAttachment) -> ProjectAttachment:
        self.session.add(att)
        await self.session.flush()
        return att

    async def get_attachment(self, att_id: str) -> Optional[ProjectAttachment]:
        res = await self.session.execute(
            select(ProjectAttachment).where(ProjectAttachment.id == att_id)
        )
        return res.scalar_one_or_none()

    async def delete_attachment(self, att_id: str) -> bool:
        att = await self.get_attachment(att_id)
        if not att:
            return False
        await self.session.delete(att)
        await self.session.flush()
        return True
