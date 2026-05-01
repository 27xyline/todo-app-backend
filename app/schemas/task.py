from uuid import UUID

from pydantic import BaseModel, field_validator, ConfigDict

from app.schemas.validators import _strip_and_validate


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    completed: bool = False


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _strip_and_validate(value, "задачи")



class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return _strip_and_validate(value, "задачи")
