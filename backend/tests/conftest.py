"""Isolate pytest onto project_cost_hub_test. Must run before app imports."""

from __future__ import annotations

import os
import re
from pathlib import Path

from urllib.parse import quote_plus

TEST_DB_NAME = os.environ.get("POSTGRES_TEST_DB", "project_cost_hub_test")

if not re.fullmatch(r"[A-Za-z0-9_]+", TEST_DB_NAME) or "test" not in TEST_DB_NAME.lower():
    raise RuntimeError(
        f"Refusing to run pytest against non-test database: {TEST_DB_NAME!r}"
    )

# Force the application settings to use the test database before any app import.
os.environ["POSTGRES_DB"] = TEST_DB_NAME

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


def _maintenance_url() -> str:
    user = os.environ.get("POSTGRES_USER", "project_cost")
    password = quote_plus(os.environ.get("POSTGRES_PASSWORD", "change_me"))
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/postgres"


def _ensure_test_database() -> None:
    engine = create_engine(_maintenance_url(), isolation_level="AUTOCOMMIT", future=True)
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": TEST_DB_NAME},
            ).scalar()
            if not exists:
                connection.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    finally:
        engine.dispose()


def _assert_test_database() -> None:
    from app.core.config import settings
    from app.core.database import engine

    if settings.POSTGRES_DB != TEST_DB_NAME:
        raise RuntimeError(
            f"Refusing to run pytest: settings.POSTGRES_DB={settings.POSTGRES_DB!r} "
            f"is not the isolated test database {TEST_DB_NAME!r}."
        )
    if "test" not in (settings.POSTGRES_DB or "").lower():
        raise RuntimeError("Refusing to run pytest against a non-test database.")
    if engine.url.database != TEST_DB_NAME:
        raise RuntimeError(
            f"Refusing to run pytest: engine database={engine.url.database!r} "
            f"is not {TEST_DB_NAME!r}."
        )


def _reset_schema_and_migrate() -> None:
    from app.core.database import engine

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")

    from app.scripts.bootstrap import main as bootstrap_main

    bootstrap_main()


@pytest.fixture(scope="session", autouse=True)
def isolated_test_database() -> None:
    _ensure_test_database()
    _assert_test_database()
    _reset_schema_and_migrate()
    _assert_test_database()


@pytest.fixture
def client(isolated_test_database: None) -> TestClient:
    from app.main import app

    return TestClient(app)
