from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskORM


class TaskRepository:
    """Ключевые операции с таблицей tasks в БД"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[TaskORM]:
        result = await self.db.scalars(select(TaskORM))
        return list(result)

    async def get_by_id(self, task_id: UUID) -> TaskORM | None:
        return await self.db.get(TaskORM, task_id)

    async def create(self, title: str, category_id: UUID | None) -> TaskORM:
        task = TaskORM(
            title=title,
            completed=False,
            category_id=category_id,
        )
        self.db.add(task)
        return task

    async def delete(self, task: TaskORM) -> None:
        await self.db.delete(task)
