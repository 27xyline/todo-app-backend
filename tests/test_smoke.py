from fastapi.testclient import TestClient


def test_create_and_get_task(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Тестовая задача"})

    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Тестовая задача"

    response = client.get(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json() == task
