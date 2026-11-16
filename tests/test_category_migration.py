import os
import subprocess
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def test_unique_category_migration(test_engine: Engine) -> None:
    schema = f"migration_{uuid4().hex}"
    admin = create_engine(test_engine.url.difference_update_query(["options"]))
    with admin.begin() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    url = test_engine.url.update_query_dict({"options": f"-csearch_path={schema}"})
    engine = create_engine(url)
    env = {
        **os.environ,
        "DATABASE_URL": test_engine.url.difference_update_query(
            ["options"]
        ).render_as_string(hide_password=False),
        "PGOPTIONS": f"-csearch_path={schema}",
    }

    def migrate(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [".venv/bin/alembic", *args], env=env, capture_output=True, text=True
        )

    try:
        result = migrate("upgrade", "b52894278bbe")
        assert result.returncode == 0, result.stderr
        ids = [uuid4(), uuid4()]
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO categories (id, name) VALUES (:id, :name)"),
                [
                    {"id": ids[0], "name": "Одинаковое"},
                    {"id": ids[1], "name": "Одинаковое"},
                ],
            )
        result = migrate("upgrade", "head")
        assert result.returncode != 0
        with engine.begin() as connection:
            assert connection.scalar(text("SELECT count(*) FROM categories")) == 2
            connection.execute(
                text("DELETE FROM categories WHERE id = :id"), {"id": ids[1]}
            )
        result = migrate("upgrade", "head")
        assert result.returncode == 0, result.stderr
        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM pg_constraint "
                        "WHERE conname = 'uq_categories_name' "
                        "AND conrelid = 'categories'::regclass"
                    )
                )
                == 1
            )
            assert connection.scalar(text("SELECT count(*) FROM categories")) == 1
        result = migrate("downgrade", "b52894278bbe")
        assert result.returncode == 0, result.stderr
        with engine.begin() as connection:
            connection.execute(
                text("INSERT INTO categories (id, name) VALUES (:id, :name)"),
                {"id": ids[1], "name": "Одинаковое"},
            )
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
        admin.dispose()
