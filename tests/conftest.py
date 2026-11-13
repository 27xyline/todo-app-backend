import os
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.models.base import Base
from app.models.category import CategoryORM  # noqa: F401
from app.models.task import TaskORM  # noqa: F401


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "postgresql" or not url.database:
        pytest.fail("DATABASE_URL must point to a PostgreSQL database")

    test_name = f"{url.database}_test"
    if len(test_name.encode("utf-8")) > 63:
        pytest.fail("PostgreSQL test database name exceeds 63 bytes")

    admin_engine = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with admin_engine.connect() as connection:
            exists = connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": test_name},
            )
            if not exists:
                quoted_name = connection.dialect.identifier_preparer.quote_identifier(
                    test_name
                )
                connection.exec_driver_sql(f"CREATE DATABASE {quoted_name}")
    finally:
        admin_engine.dispose()

    # The application creates its engine on import, so configure it first.
    test_url = url.set(database=test_name)
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_url.render_as_string(hide_password=False)
    os.environ.setdefault("CORS_ORIGINS", "[]")
    get_settings.cache_clear()
    schema = f"test_{uuid4().hex}"
    schema_engine = create_engine(test_url)
    with schema_engine.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    schema_url = test_url.update_query_dict({"options": f"-csearch_path={schema}"})
    engine = create_engine(schema_url)
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()
        with schema_engine.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        schema_engine.dispose()
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        get_settings.cache_clear()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(test_engine: Engine) -> AsyncGenerator[AsyncClient, None]:
    from app.db.session import get_db
    from app.main import app

    engine = create_async_engine(test_engine.url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                async with AsyncSession(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                    expire_on_commit=False,
                ) as session:

                    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
                        yield session

                    app.dependency_overrides[get_db] = override_get_db
                    try:
                        async with AsyncClient(
                            transport=ASGITransport(app=app), base_url="http://test"
                        ) as test_client:
                            yield test_client
                    finally:
                        app.dependency_overrides.pop(get_db, None)
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
