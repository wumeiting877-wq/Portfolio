from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from tests.helpers import admin_headers, create_employee, create_user_account


def test_api_never_returns_password_hash(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, _username, _password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    detail = client.get(f"/api/users/{user['id']}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert "password_hash" not in body
    assert "password" not in body


def test_database_stores_hashed_password(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT password_hash FROM users WHERE id = :id"),
            {"id": user["id"]},
        ).one()
    assert row.password_hash
    assert row.password_hash != password
    assert username not in row.password_hash
    assert not row.password_hash.startswith(password)


def test_audit_log_does_not_store_password(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, _username, _password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    client.post(
        f"/api/users/{user['id']}/reset-password",
        json={"password": "AnotherPass1"},
        headers=headers,
    )
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT action, before_data::text AS before_data, after_data::text AS after_data
                FROM audit_logs
                WHERE target_id = :target_id
                """
            ),
            {"target_id": str(user["id"])},
        ).mappings().all()
    assert rows
    combined = " ".join(
        f"{row['action']} {row['before_data'] or ''} {row['after_data'] or ''}" for row in rows
    )
    assert "password" not in combined.lower() or "password_hash" not in combined.lower()
    for row in rows:
        for field in ("before_data", "after_data"):
            value = (row[field] or "").lower()
            assert "password_hash" not in value
            assert "anotherpass1" not in value
