from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_employee,
    create_expense_type,
    create_user_account,
    unique,
)


def test_admin_create_update_expense_type(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_expense_type(client, headers, name="Cursor 订阅", category="SUBSCRIPTION")
    assert created["name"] == "Cursor 订阅"
    assert created["category"] == "SUBSCRIPTION"
    assert created["is_active"] is True
    updated = client.put(
        f"/api/expense-types/{created['id']}",
        json={"name": "Cursor Pro", "description": "月订阅"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Cursor Pro"


def test_duplicate_expense_type_code_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    code = unique("CURSOR").upper()
    create_expense_type(client, headers, code=code)
    response = client.post(
        "/api/expense-types",
        json={"code": code, "name": "重复", "category": "SUBSCRIPTION"},
        headers=headers,
    )
    assert response.status_code == 400


def test_admin_disable_enable_expense_type(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_expense_type(client, headers)
    disabled = client.post(f"/api/expense-types/{created['id']}/disable", headers=headers)
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
    enabled = client.post(f"/api/expense-types/{created['id']}/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.json()["is_active"] is True


def test_non_admin_cannot_write_expense_types(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="BOSS", employee_id=employee["id"]
    )
    boss = auth_headers_for(client, username, password)
    payload = {"code": unique("X").upper(), "name": "禁止", "category": "OTHER"}
    assert client.post("/api/expense-types", json=payload, headers=boss).status_code == 403


def test_logged_in_users_can_read_active_expense_types(client: TestClient) -> None:
    headers = admin_headers(client)
    active = create_expense_type(client, headers, code=unique("ON").upper())
    inactive = create_expense_type(client, headers, code=unique("OFF").upper())
    client.post(f"/api/expense-types/{inactive['id']}/disable", headers=headers)
    member_emp = create_employee(client, headers)
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_emp["id"]
    )
    member = auth_headers_for(client, member_user, member_pass)
    listed = client.get("/api/expense-types", headers=member)
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()}
    assert active["id"] in ids
    assert inactive["id"] not in ids


def test_expense_type_write_is_audited(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_expense_type(client, headers, code=unique("AUD").upper())
    client.put(f"/api/expense-types/{created['id']}", json={"name": "审计类型"}, headers=headers)
    client.post(f"/api/expense-types/{created['id']}/disable", headers=headers)
    with engine.connect() as connection:
        actions = {
            row[0]
            for row in connection.execute(
                text("SELECT action FROM audit_logs WHERE target_id = :target_id"),
                {"target_id": str(created["id"])},
            )
        }
    assert "EXPENSE_TYPE_CREATE" in actions
    assert "EXPENSE_TYPE_UPDATE" in actions
    assert "EXPENSE_TYPE_DISABLE" in actions
