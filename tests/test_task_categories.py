from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_create_tasks_with_and_without_category(client: AsyncClient) -> None:
    category = (await client.post("/categories", json={"name": "Покупки"})).json()

    response = await client.post(
        "/tasks", json={"title": "Молоко", "category_id": category["id"]}
    )
    assert response.status_code == 201
    task = response.json()
    assert task["category_id"] == category["id"]
    assert (await client.get(f"/tasks/{task['id']}")).json()["category_id"] == category[
        "id"
    ]

    response = await client.post("/tasks", json={"title": "Общая задача"})
    assert response.status_code == 201
    assert response.json()["category_id"] is None


async def test_update_task_category_and_clear_it(client: AsyncClient) -> None:
    first = (await client.post("/categories", json={"name": "Первая"})).json()
    second = (await client.post("/categories", json={"name": "Вторая"})).json()
    task = (
        await client.post(
            "/tasks", json={"title": "Задача", "category_id": first["id"]}
        )
    ).json()
    url = f"/tasks/{task['id']}"

    response = await client.patch(url, json={"title": "Новое название"})
    assert response.status_code == 200
    assert response.json()["category_id"] == first["id"]

    for category_id in (first["id"], second["id"]):
        response = await client.patch(url, json={"category_id": category_id})
        assert response.status_code == 200
        assert response.json()["category_id"] == category_id

    response = await client.patch(url, json={"category_id": None})
    assert response.status_code == 200
    assert response.json()["category_id"] is None
    assert (await client.get(url)).json()["category_id"] is None


async def test_missing_category_is_rejected(client: AsyncClient) -> None:
    missing_id = str(uuid4())
    response = await client.post(
        "/tasks", json={"title": "Задача", "category_id": missing_id}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Категория не найдена"
    assert (await client.get("/tasks")).json() == []

    task = (await client.post("/tasks", json={"title": "Задача"})).json()
    response = await client.patch(
        f"/tasks/{task['id']}", json={"category_id": missing_id}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Категория не найдена"
    assert (await client.get(f"/tasks/{task['id']}")).json() == task


async def test_deleting_category_deletes_only_its_tasks(client: AsyncClient) -> None:
    category = (await client.post("/categories", json={"name": "Покупки"})).json()
    other = (await client.post("/categories", json={"name": "Работа"})).json()
    deleted = (
        await client.post(
            "/tasks", json={"title": "Молоко", "category_id": category["id"]}
        )
    ).json()
    general = (await client.post("/tasks", json={"title": "Общая"})).json()
    kept = (
        await client.post(
            "/tasks", json={"title": "Рабочая", "category_id": other["id"]}
        )
    ).json()

    response = await client.delete(f"/categories/{category['id']}")
    assert response.status_code == 204
    assert (await client.get(f"/tasks/{deleted['id']}")).status_code == 404
    assert (await client.get(f"/tasks/{general['id']}")).json() == general
    assert (await client.get(f"/tasks/{kept['id']}")).json() == kept
