import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import check_database_connection


def test_health_db_returns_ok_when_postgres_available(client: TestClient) -> None:
    try:
        check_database_connection()
    except SQLAlchemyError:
        pytest.skip("PostgreSQL is not available in this test environment")

    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
