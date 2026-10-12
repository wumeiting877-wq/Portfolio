from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

from app.core.config import settings
from tests.helpers import admin_headers, create_employee, unique


def test_pytest_does_not_write_to_development_database(client: TestClient) -> None:
    headers = admin_headers(client)
    employee_no = unique("ISO")
    created = create_employee(client, headers, employee_no=employee_no)
    assert created["employee_no"] == employee_no

    password = quote_plus(settings.POSTGRES_PASSWORD)
    dev_url = (
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{password}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/project_cost_hub"
    )
    engine = create_engine(dev_url, future=True)
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM employees WHERE employee_no = :employee_no"),
                {"employee_no": employee_no},
            ).scalar()
    finally:
        engine.dispose()
    assert exists is None
