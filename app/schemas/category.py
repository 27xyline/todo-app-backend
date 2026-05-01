from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.validators import _strip_and_validate


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class CategoryCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_and_validate(value, "категории")


class CategoryUpdate(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _strip_and_validate(value, "категории")
