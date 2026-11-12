from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import CategoryORM


class CategoryRepository:
    """Ключевые операции с таблицей categories в БД"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[CategoryORM]:
        result = await self.db.scalars(select(CategoryORM))
        return list(result)

    async def get_by_id(self, category_id: UUID) -> CategoryORM | None:
        return await self.db.get(CategoryORM, category_id)

    async def create(self, name: str) -> CategoryORM:
        category = CategoryORM(name=name)
        self.db.add(category)
        return category

    async def delete(self, category: CategoryORM) -> None:
        await self.db.delete(category)
