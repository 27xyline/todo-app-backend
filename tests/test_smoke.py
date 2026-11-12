import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_create_and_get_task(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"title": "Тестовая задача"})

    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Тестовая задача"

    response = await client.get(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json() == task
