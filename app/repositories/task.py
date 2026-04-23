from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import TaskORM


class TaskRepository:
    """Ключевые операции с таблицей tasks в БД"""

    def __init__(self, db: Session):
        self.db = db
    

    def get_all(self) -> list[TaskORM]:
        return self.db.scalars(select(TaskORM)).all()
    

    def get_by_id(self, task_id: UUID) -> TaskORM | None:
        return self.db.get(TaskORM, task_id)
    

    def create(self, title: str) -> TaskORM:
        task = TaskORM(title=title, completed=False)
        self.db.add(task)
        return task
    

    def delete(self, task: TaskORM) -> None:
        self.db.delete(task)
