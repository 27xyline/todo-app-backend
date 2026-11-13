from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskORM(Base):
    __tablename__ = "tasks"

    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        default=None,
    )
