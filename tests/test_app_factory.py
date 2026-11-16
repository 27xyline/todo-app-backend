from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_task_service
from app.core.exceptions import TaskNotFoundError


@pytest.mark.anyio
async def test_factory_registers_routes_handlers_and_middleware() -> None:
    from app.main import create_app

    class MissingTaskService:
        async def get(self, task_id):
            raise TaskNotFoundError

    app = create_app()
    app.dependency_overrides[get_task_service] = lambda: MissingTaskService()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/tasks/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Задача не найдена"}
    assert "X-Request-Number" in response.headers
