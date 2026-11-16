from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped

from app.models.base import Base


class CategoryORM(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    name: Mapped[str]
