from uuid import UUID

from pydantic import BaseModel, field_validator, ConfigDict


def _strip_and_validate(value: str | None, field_label: str) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError(f"Название {field_label} не может быть пустым")
    if len(value) > 200:
        raise ValueError(f"Название {field_label} не может быть длиннее 200 символов")
    return value


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
