from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("resource", "field"), [("tasks", "title"), ("categories", "name")]
)
async def test_crud(client: AsyncClient, resource: str, field: str) -> None:
    url = f"/{resource}"
    response = await client.get(url)
    assert response.status_code == 200
    assert response.json() == []

    response = await client.post(url, json={field: "  Первое название  "})
    assert response.status_code == 201
    item = response.json()
    assert item[field] == "Первое название"
    if resource == "tasks":
        assert item["completed"] is False

    response = await client.get(url)
    assert response.status_code == 200
    assert response.json() == [item]

    response = await client.patch(
        f"{url}/{item['id']}", json={field: "  Новое название  "}
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == item["id"]
    assert updated[field] == "Новое название"
    assert (await client.get(url)).json() == [updated]

    response = await client.delete(f"{url}/{item['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert (await client.get(url)).json() == []


@pytest.mark.parametrize("resource", ["tasks", "categories"])
@pytest.mark.parametrize("method", ["patch", "delete"])
async def test_missing_item(client: AsyncClient, resource: str, method: str) -> None:
    response = await client.request(method, f"/{resource}/{uuid4()}", json={})
    assert response.status_code == 404


async def test_missing_task(client: AsyncClient) -> None:
    assert (await client.get(f"/tasks/{uuid4()}")).status_code == 404


@pytest.mark.parametrize("resource", ["tasks", "categories"])
@pytest.mark.parametrize("method", ["patch", "delete"])
async def test_invalid_id(client: AsyncClient, resource: str, method: str) -> None:
    response = await client.request(method, f"/{resource}/invalid-id", json={})
    assert response.status_code == 422


async def test_invalid_task_id(client: AsyncClient) -> None:
    assert (await client.get("/tasks/invalid-id")).status_code == 422


async def test_update_task_completed(client: AsyncClient) -> None:
    task = (await client.post("/tasks", json={"title": "Задача"})).json()
    response = await client.patch(f"/tasks/{task['id']}", json={"completed": True})
    assert response.status_code == 200
    assert response.json() == {**task, "completed": True}
    assert (await client.get(f"/tasks/{task['id']}")).json() == response.json()


@pytest.mark.parametrize(
    ("resource", "field"), [("tasks", "title"), ("categories", "name")]
)
@pytest.mark.parametrize("invalid_name", ["", "   ", "a" * 201])
@pytest.mark.parametrize("method", ["post", "patch"])
async def test_invalid_names(
    client: AsyncClient, resource: str, field: str, invalid_name: str, method: str
) -> None:
    url = f"/{resource}"
    if method == "patch":
        item = (await client.post(url, json={field: "Исходное название"})).json()
        url = f"{url}/{item['id']}"
    response = await client.request(method, url, json={field: invalid_name})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("resource", "field"), [("tasks", "title"), ("categories", "name")]
)
async def test_create_requires_name_and_accepts_200_characters(
    client: AsyncClient, resource: str, field: str
) -> None:
    assert (await client.post(f"/{resource}", json={})).status_code == 422
    response = await client.post(f"/{resource}", json={field: "a" * 200})
    assert response.status_code == 201
    assert response.json()[field] == "a" * 200
