from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CategoryNameConflictError, CategoryNotFoundError
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    """Ключевые операции с категориями, включая бизнес-логику, валидацию и прочее"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = CategoryRepository(db)

    async def list_categories(self) -> list[CategoryRead]:
        categories = await self.repository.get_all()
        return [CategoryRead.model_validate(category) for category in categories]

    async def create_category(self, payload: CategoryCreate) -> CategoryRead:
        category = await self.repository.create(name=payload.name)
        await self._commit_category()
        return CategoryRead.model_validate(category)

    async def update_category(
        self, category_id: UUID, payload: CategoryUpdate
    ) -> CategoryRead:
        category = await self.repository.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError

        if payload.name is not None:
            category.name = payload.name

        await self._commit_category()
        return CategoryRead.model_validate(category)

    async def delete_category(self, category_id: UUID) -> None:
        category = await self.repository.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError

        await self.repository.delete(category)
        await self.db.commit()

    async def _commit_category(self) -> None:
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            original = exc.orig
            diag = getattr(original, "diag", None)
            if (
                getattr(original, "sqlstate", None) == "23505"
                and getattr(diag, "constraint_name", None) == "uq_categories_name"
            ):
                raise CategoryNameConflictError from exc
            raise
