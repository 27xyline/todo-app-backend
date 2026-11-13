from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.validators import _strip_and_validate


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    completed: bool = False
    category_id: UUID | None


class TaskCreate(BaseModel):
    title: str
    category_id: UUID | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _strip_and_validate(value, "задачи")


class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None
    category_id: UUID | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return _strip_and_validate(value, "задачи")
