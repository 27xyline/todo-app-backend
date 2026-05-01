from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.category import CategoryORM


class CategoryRepository:
    """Ключевые операции с таблицей categories в БД"""

    def __init__(self, db: Session):
        self.db = db


    def get_all(self) -> list[CategoryORM]:
        return self.db.scalars(select(CategoryORM)).all()

    
    def get_by_id(self, category_id: UUID) -> CategoryORM | None:
        return self.db.get(CategoryORM, category_id)


    def create(self, name: str) -> CategoryORM:
        category = CategoryORM(name=name)
        self.db.add(category)
        return category
    

    def delete(self, category: CategoryORM) -> None:
        self.db.delete(category)
