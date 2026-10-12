from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.core.database import engine
from app.models.resource_account import ResourceAccount
from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_employee,
    create_resource,
    create_resource_type,
    create_user_account,
    unique,
)

FORBIDDEN_FIELDS = {
    "password",
    "api_key",
    "secret",
    "token",
    "credential",
    "access_key",
    "private_key",
}


def test_admin_create_update_resource(client: TestClient) -> None:
    headers = admin_headers(client)
    resource_type = create_resource_type(client, headers, code="CURSOR")
    resource_name = unique("Cursor-开发01")
    created = create_resource(
        client,
        headers,
        resource_type_id=resource_type["id"],
        resource_name=resource_name,
        provider="Cursor",
        account_identifier="dev01@example.com",
        plan_name="Pro",
    )
    assert created["resource_name"] == resource_name
    assert created["resource_type"]["code"] == "CURSOR"
    assert created["is_shared"] is False
    assert created["active_user_count"] == 0
    assert "password" not in created
    assert "api_key" not in created

    updated = client.put(
        f"/api/resources/{created['id']}",
        json={"plan_name": "Team", "remark": "修订"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["plan_name"] == "Team"
    assert updated.json()["remark"] == "修订"


def test_invalid_resource_type_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.post(
        "/api/resources",
        json={"resource_type_id": 999999, "resource_name": "无效类型"},
        headers=headers,
    )
    assert response.status_code == 400


def test_disabled_resource_type_cannot_create_account(client: TestClient) -> None:
    headers = admin_headers(client)
    resource_type = create_resource_type(client, headers)
    client.post(f"/api/resource-types/{resource_type['id']}/disable", headers=headers)
    response = client.post(
        "/api/resources",
        json={"resource_type_id": resource_type["id"], "resource_name": "停用类型"},
        headers=headers,
    )
    assert response.status_code == 400


def test_admin_disable_enable_resource(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource(client, headers)
    disabled = client.post(f"/api/resources/{created['id']}/disable", headers=headers)
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"
    enabled = client.post(f"/api/resources/{created['id']}/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.json()["status"] == "ACTIVE"


def test_resource_api_does_not_return_secret_fields(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource(client, headers)
    listed = client.get("/api/resources", headers=headers)
    assert listed.status_code == 200
    item = listed.json()["items"][0]
    for field in FORBIDDEN_FIELDS:
        assert field not in created
        assert field not in item


def test_resource_create_rejects_secret_payload_fields(client: TestClient) -> None:
    headers = admin_headers(client)
    resource_type = create_resource_type(client, headers)
    response = client.post(
        "/api/resources",
        json={
            "resource_type_id": resource_type["id"],
            "resource_name": unique("secret"),
            "password": "plain-password",
            "api_key": "sk-test",
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_resource_model_has_no_plaintext_secret_columns() -> None:
    columns = {column.name.lower() for column in inspect(ResourceAccount).columns}
    assert not (columns & FORBIDDEN_FIELDS)
    assert "price" not in columns
    assert "amount" not in columns
    assert "cost" not in columns
    assert "employee_id" not in columns
    assert "project_id" not in columns


def test_expiring_soon_is_computed(client: TestClient) -> None:
    headers = admin_headers(client)
    soon = create_resource(
        client,
        headers,
        expires_at=(date.today() + timedelta(days=10)).isoformat(),
    )
    later = create_resource(
        client,
        headers,
        expires_at=(date.today() + timedelta(days=90)).isoformat(),
    )
    assert soon["is_expiring_soon"] is True
    assert later["is_expiring_soon"] is False
    filtered = client.get("/api/resources", params={"expiring_soon": True}, headers=headers)
    ids = {item["id"] for item in filtered.json()["items"]}
    assert soon["id"] in ids
    assert later["id"] not in ids


def test_resource_write_is_audited(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource(client, headers)
    client.put(f"/api/resources/{created['id']}", json={"remark": "审计"}, headers=headers)
    client.post(f"/api/resources/{created['id']}/disable", headers=headers)
    with engine.connect() as connection:
        actions = {
            row[0]
            for row in connection.execute(
                text("SELECT action FROM audit_logs WHERE target_id = :target_id"),
                {"target_id": str(created["id"])},
            )
        }
    assert "RESOURCE_CREATE" in actions
    assert "RESOURCE_UPDATE" in actions
    assert "RESOURCE_DISABLE" in actions
