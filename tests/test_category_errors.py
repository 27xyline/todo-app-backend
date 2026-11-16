from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_duplicate_category_create_returns_conflict(client: AsyncClient) -> None:
    assert (
        await client.post("/categories", json={"name": "Работа"})
    ).status_code == 201
    response = await client.post("/categories", json={"name": " Работа "})
    assert response.status_code == 409
    assert response.json() == {"detail": "Категория с таким названием уже существует"}
    assert (
        await client.post("/categories", json={"name": "Другая"})
    ).status_code == 201


async def test_duplicate_category_update_returns_conflict(client: AsyncClient) -> None:
    first = (await client.post("/categories", json={"name": "Одна"})).json()
    second = (await client.post("/categories", json={"name": "Другая"})).json()
    assert (
        await client.patch(f"/categories/{first['id']}", json={"name": "Одна"})
    ).status_code == 200
    response = await client.patch(f"/categories/{second['id']}", json={"name": "Одна"})
    assert response.status_code == 409
    assert {item["name"] for item in (await client.get("/categories")).json()} == {
        "Одна",
        "Другая",
    }


@pytest.mark.parametrize(
    ("method", "path", "body", "detail"),
    [
        ("GET", "/tasks/{id}", None, "Задача не найдена"),
        ("PATCH", "/tasks/{id}", {}, "Задача не найдена"),
        ("DELETE", "/tasks/{id}", None, "Задача не найдена"),
        ("PATCH", "/categories/{id}", {}, "Категория не найдена"),
        ("DELETE", "/categories/{id}", None, "Категория не найдена"),
        (
            "POST",
            "/tasks",
            {"title": "Задача", "category_id": "{id}"},
            "Категория не найдена",
        ),
    ],
)
async def test_missing_objects_have_consistent_response(
    client: AsyncClient, method: str, path: str, body: dict | None, detail: str
) -> None:
    missing_id = str(uuid4())
    if body and body.get("category_id") == "{id}":
        body = {**body, "category_id": missing_id}
    response = await client.request(method, path.replace("{id}", missing_id), json=body)
    assert response.status_code == 404
    assert response.json() == {"detail": detail}


async def test_other_integrity_error_is_not_reported_as_duplicate(client, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    from app.models.category import CategoryORM
    from app.repositories.category import CategoryRepository

    async def create_invalid_category(self, name):
        category = CategoryORM(name=None)
        self.db.add(category)
        return category

    monkeypatch.setattr(CategoryRepository, "create", create_invalid_category)
    with pytest.raises(IntegrityError):
        await client.post("/categories", json={"name": "Категория"})
