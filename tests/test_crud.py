from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("resource", "field"), [("tasks", "title"), ("categories", "name")]
)
def test_crud(client: TestClient, resource: str, field: str) -> None:
    url = f"/{resource}"
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == []

    response = client.post(url, json={field: "  Первое название  "})
    assert response.status_code == 201
    item = response.json()
    assert item[field] == "Первое название"
    if resource == "tasks":
        assert item["completed"] is False

    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == [item]

    response = client.patch(f"{url}/{item['id']}", json={field: "  Новое название  "})
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == item["id"]
    assert updated[field] == "Новое название"
    assert client.get(url).json() == [updated]

    response = client.delete(f"{url}/{item['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(url).json() == []


@pytest.mark.parametrize("resource", ["tasks", "categories"])
@pytest.mark.parametrize("method", ["patch", "delete"])
def test_missing_item(client: TestClient, resource: str, method: str) -> None:
    response = client.request(method, f"/{resource}/{uuid4()}", json={})
    assert response.status_code == 404


def test_missing_task(client: TestClient) -> None:
    assert client.get(f"/tasks/{uuid4()}").status_code == 404


@pytest.mark.parametrize("resource", ["tasks", "categories"])
@pytest.mark.parametrize("method", ["patch", "delete"])
def test_invalid_id(client: TestClient, resource: str, method: str) -> None:
    response = client.request(method, f"/{resource}/invalid-id", json={})
    assert response.status_code == 422


def test_invalid_task_id(client: TestClient) -> None:
    assert client.get("/tasks/invalid-id").status_code == 422


def test_update_task_completed(client: TestClient) -> None:
    task = client.post("/tasks", json={"title": "Задача"}).json()
    response = client.patch(f"/tasks/{task['id']}", json={"completed": True})
    assert response.status_code == 200
    assert response.json() == {**task, "completed": True}
    assert client.get(f"/tasks/{task['id']}").json() == response.json()


@pytest.mark.parametrize(
    ("resource", "field"), [("tasks", "title"), ("categories", "name")]
)
@pytest.mark.parametrize("invalid_name", ["", "   ", "a" * 201])
@pytest.mark.parametrize("method", ["post", "patch"])
def test_invalid_names(
    client: TestClient, resource: str, field: str, invalid_name: str, method: str
) -> None:
    url = f"/{resource}"
    if method == "patch":
        item = client.post(url, json={field: "Исходное название"}).json()
        url = f"{url}/{item['id']}"
    response = client.request(method, url, json={field: invalid_name})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("resource", "field"), [("tasks", "title"), ("categories", "name")]
)
def test_create_requires_name_and_accepts_200_characters(
    client: TestClient, resource: str, field: str
) -> None:
    assert client.post(f"/{resource}", json={}).status_code == 422
    response = client.post(f"/{resource}", json={field: "a" * 200})
    assert response.status_code == 201
    assert response.json()[field] == "a" * 200
