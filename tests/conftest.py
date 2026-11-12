import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

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
    engine = create_engine(test_url)
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        get_settings.cache_clear()


@pytest.fixture
def client(test_engine: Engine) -> Generator[TestClient, None, None]:
    from app.db.session import get_db
    from app.main import app

    with test_engine.connect() as connection:
        transaction = connection.begin()
        with Session(
            bind=connection, join_transaction_mode="create_savepoint"
        ) as session:

            def override_get_db() -> Generator[Session, None, None]:
                yield session

            app.dependency_overrides[get_db] = override_get_db
            try:
                with TestClient(app) as test_client:
                    yield test_client
            finally:
                app.dependency_overrides.pop(get_db, None)
                transaction.rollback()
