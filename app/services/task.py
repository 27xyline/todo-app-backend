from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CategoryNotFoundError, TaskNotFoundError
from app.repositories.category import CategoryRepository
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate


class TaskService:
    """Ключевые операции с задачами, включая бизнес-логику, валидацию и прочее"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = TaskRepository(db)
        self.category_repository = CategoryRepository(db)

    async def get(self, task_id: UUID) -> TaskRead:
        task = await self.repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError

        return TaskRead.model_validate(task)

    async def list_tasks(self) -> list[TaskRead]:
        tasks = await self.repository.get_all()
        return [TaskRead.model_validate(task) for task in tasks]

    async def create_task(self, payload: TaskCreate) -> TaskRead:
        if payload.category_id is not None:
            existing = await self.category_repository.get_by_id(payload.category_id)
            if not existing:
                raise CategoryNotFoundError

        task = await self.repository.create(
            title=payload.title,
            category_id=payload.category_id,
        )
        await self.db.commit()
        return TaskRead.model_validate(task)

    async def update_task(self, task_id: UUID, payload: TaskUpdate) -> TaskRead:
        task = await self.repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError

        if payload.category_id is not None:
            existing = await self.category_repository.get_by_id(payload.category_id)
            if not existing:
                raise CategoryNotFoundError

        if payload.title is not None:
            task.title = payload.title
        if payload.completed is not None:
            task.completed = payload.completed
        if "category_id" in payload.model_fields_set:
            task.category_id = payload.category_id

        await self.db.commit()
        return TaskRead.model_validate(task)

    async def delete_task(self, task_id: UUID) -> None:
        task = await self.repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError

        await self.repository.delete(task)
        await self.db.commit()
