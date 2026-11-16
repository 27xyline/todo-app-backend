from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.models.task import TaskORM

pytestmark = pytest.mark.anyio


async def test_filter_tasks_by_title_status_and_category(client: AsyncClient) -> None:
    first = (await client.post("/categories", json={"name": "Первая"})).json()
    second = (await client.post("/categories", json={"name": "Вторая"})).json()
    tasks = []
    for title, category_id in [
        ("Купить молоко", first["id"]),
        ("Забрать молоко", first["id"]),
        ("Вторая выполнена", second["id"]),
        ("Заказать молоко", None),
        ("Проверить почту", first["id"]),
    ]:
        response = await client.post(
            "/tasks", json={"title": title, "category_id": category_id}
        )
        assert response.status_code == 201
        tasks.append(response.json())
    for index in (0, 2):
        response = await client.patch(
            f"/tasks/{tasks[index]['id']}", json={"completed": True}
        )
        assert response.status_code == 200

    for params, expected in [
        ({"completed": "true"}, {tasks[0]["id"], tasks[2]["id"]}),
        ({"completed": "false"}, {tasks[1]["id"], tasks[3]["id"], tasks[4]["id"]}),
        (
            {"category_id": first["id"]},
            {tasks[0]["id"], tasks[1]["id"], tasks[4]["id"]},
        ),
        (
            {"category_id": first["id"], "completed": "false"},
            {tasks[1]["id"], tasks[4]["id"]},
        ),
        ({"title_contains": "мОЛо"}, {tasks[0]["id"], tasks[1]["id"], tasks[3]["id"]}),
        (
            {
                "title_contains": "мОЛо",
                "completed": "false",
                "category_id": first["id"],
            },
            {tasks[1]["id"]},
        ),
        ({"category_id": str(uuid4())}, set()),
    ]:
        response = await client.get("/tasks", params=params)
        assert response.status_code == 200
        assert {task["id"] for task in response.json()} == expected


@pytest.mark.parametrize(
    ("search", "expected_title"),
    [("100%", "Скидка 100%"), ("a_b", "Файл a_b")],
)
async def test_title_search_treats_wildcards_as_text(
    client: AsyncClient, search: str, expected_title: str
) -> None:
    for title in ("Скидка 100%", "Скидка 1000", "Файл a_b", "Файл acb"):
        response = await client.post("/tasks", json={"title": title})
        assert response.status_code == 201

    response = await client.get("/tasks", params={"title_contains": search})
    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == [expected_title]


async def test_filters_are_applied_before_pagination(client: AsyncClient) -> None:
    category = (await client.post("/categories", json={"name": "Покупки"})).json()
    other = (await client.post("/categories", json={"name": "Работа"})).json()
    matching_ids = []
    for title, category_id, completed in [
        ("Купить молоко 1", category["id"], False),
        ("Купить молоко 2", category["id"], False),
        ("Купить молоко 3", category["id"], False),
        ("Купить молоко 4", category["id"], False),
        ("Купить молоко готово", category["id"], True),
        ("Купить молоко работа", other["id"], False),
        ("Купить хлеб", category["id"], False),
    ]:
        response = await client.post(
            "/tasks", json={"title": title, "category_id": category_id}
        )
        assert response.status_code == 201
        task_id = response.json()["id"]
        if completed:
            assert (
                await client.patch(f"/tasks/{task_id}", json={"completed": True})
            ).status_code == 200
        elif title.startswith("Купить молоко") and category_id == category["id"]:
            matching_ids.append(task_id)

    # All inserts share the test transaction's now(); UUID breaks the tie.
    expected = sorted(matching_ids, reverse=True)
    for offset in (0, 2, 4):
        response = await client.get(
            "/tasks",
            params={
                "title_contains": "МОЛОКО",
                "category_id": category["id"],
                "completed": "false",
                "limit": 2,
                "offset": offset,
            },
        )
        assert response.status_code == 200
        assert [task["id"] for task in response.json()] == expected[offset : offset + 2]


async def test_task_pagination_and_order(client: AsyncClient) -> None:
    from app.db.session import get_db
    from app.main import app

    tasks = []
    for number in range(27):
        response = await client.post("/tasks", json={"title": f"Задача {number}"})
        assert response.status_code == 201
        tasks.append(response.json())

    # PostgreSQL now() is fixed for the test transaction; set known timestamps.
    dependency = app.dependency_overrides[get_db]()
    session = await anext(dependency)
    try:
        base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for index, task in enumerate(tasks):
            # Two tasks share a timestamp, so the ID tie-breaker is exercised.
            created_at = base_time + timedelta(seconds=index // 2)
            await session.execute(
                update(TaskORM)
                .where(TaskORM.id == UUID(task["id"]))
                .values(created_at=created_at)
            )
        await session.flush()
    finally:
        await dependency.aclose()

    expected = sorted(
        enumerate(tasks), key=lambda pair: (pair[0] // 2, pair[1]["id"]), reverse=True
    )
    expected_ids = [task["id"] for _, task in expected]
    response = await client.get("/tasks")
    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == expected_ids[:10]

    for offset in (0, 5, 10, 15, 20, 25, 30, 2**63 - 1):
        response = await client.get("/tasks", params={"limit": 5, "offset": offset})
        assert response.status_code == 200
        assert [task["id"] for task in response.json()] == expected_ids[
            offset : offset + 5
        ]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"limit": "abc"},
        {"offset": -1},
        {"offset": "abc"},
        {"offset": 2**63},
        {"title_contains": "\x00"},
        {"category_id": "invalid-id"},
        {"completed": "invalid-bool"},
    ],
)
async def test_invalid_task_list_parameters(client: AsyncClient, params: dict) -> None:
    assert (await client.get("/tasks", params=params)).status_code == 422


@pytest.mark.parametrize("limit", [1, 100])
async def test_valid_limit_boundaries(client: AsyncClient, limit: int) -> None:
    assert (await client.get("/tasks", params={"limit": limit})).status_code == 200
