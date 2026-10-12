from sqlalchemy import event

from fastapi.testclient import TestClient

from app.core.database import engine
from tests.helpers import admin_headers, create_expense, create_project


def _count_selects(callback) -> int:
    statements: list[str] = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        if statement.lstrip().lower().startswith("select"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        callback()
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)
    return len(statements)


def test_project_ranking_query_count_does_not_scale_with_projects(client: TestClient) -> None:
    headers = admin_headers(client)
    first_projects = [create_project(client, headers, name=f"N1-{index}") for index in range(3)]
    for project in first_projects:
        create_expense(
            client,
            headers,
            amount="10.00",
            distributions=[
                {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "10.00"}
            ],
        )

    def fetch() -> None:
        response = client.get(
            "/api/statistics/project-costs",
            params={"date_from": "2026-01-01", "date_to": "2026-12-31", "limit": 20},
            headers=headers,
        )
        assert response.status_code == 200, response.text

    first = _count_selects(fetch)
    extra = [create_project(client, headers, name=f"N2-{index}") for index in range(5)]
    for project in extra:
        create_expense(
            client,
            headers,
            amount="12.00",
            distributions=[
                {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "12.00"}
            ],
        )
    second = _count_selects(fetch)
    assert second <= first + 2
