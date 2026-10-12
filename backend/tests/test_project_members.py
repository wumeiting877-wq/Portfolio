from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_employee,
    create_project,
    create_user_account,
)


def test_admin_add_remove_and_restore_member(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers, name="项目负责人")
    member_employee = create_employee(client, headers, name="普通成员甲")
    project = create_project(client, headers, manager_employee_id=manager["id"])

    added = client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member_employee["id"], "member_role": "MEMBER"},
        headers=headers,
    )
    assert added.status_code == 200, added.text
    assert added.json()["is_active"] is True

    duplicate = client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member_employee["id"], "member_role": "MEMBER"},
        headers=headers,
    )
    assert duplicate.status_code == 400

    removed = client.delete(
        f"/api/projects/{project['id']}/members/{member_employee['id']}",
        headers=headers,
    )
    assert removed.status_code == 200, removed.text
    assert removed.json()["is_active"] is False
    assert removed.json()["left_at"] is not None

    restored = client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member_employee["id"], "member_role": "MEMBER"},
        headers=headers,
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["is_active"] is True
    assert restored.json()["left_at"] is None


def test_cannot_remove_current_manager(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=manager["id"])
    response = client.delete(
        f"/api/projects/{project['id']}/members/{manager['id']}",
        headers=headers,
    )
    assert response.status_code == 400


def test_manager_change_keeps_previous_manager_as_member(client: TestClient) -> None:
    headers = admin_headers(client)
    manager_a = create_employee(client, headers, name="原负责人")
    manager_b = create_employee(client, headers, name="新负责人")
    project = create_project(client, headers, manager_employee_id=manager_a["id"])
    updated = client.put(
        f"/api/projects/{project['id']}",
        json={"manager_employee_id": manager_b["id"]},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["manager_employee_id"] == manager_b["id"]

    members = client.get(f"/api/projects/{project['id']}/members", headers=headers).json()
    by_employee = {item["employee_id"]: item for item in members}
    assert by_employee[manager_a["id"]]["is_active"] is True
    assert by_employee[manager_a["id"]]["member_role"] == "MEMBER"
    assert by_employee[manager_b["id"]]["is_active"] is True
    assert by_employee[manager_b["id"]]["member_role"] == "PROJECT_MANAGER"


def test_removed_member_loses_access_and_restore_returns_it(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    member_employee = create_employee(client, headers, name="可移除成员")
    _, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_employee["id"]
    )
    project = create_project(client, headers, manager_employee_id=manager["id"])
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member_employee["id"]},
        headers=headers,
    )
    member_headers = auth_headers_for(client, username, password)
    visible = client.get("/api/projects", headers=member_headers)
    assert visible.status_code == 200
    assert any(item["id"] == project["id"] for item in visible.json()["items"])

    client.delete(
        f"/api/projects/{project['id']}/members/{member_employee['id']}",
        headers=headers,
    )
    after_remove = client.get("/api/projects", headers=member_headers)
    assert after_remove.status_code == 200
    assert all(item["id"] != project["id"] for item in after_remove.json()["items"])
    hidden_detail = client.get(f"/api/projects/{project['id']}", headers=member_headers)
    assert hidden_detail.status_code == 404

    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member_employee["id"]},
        headers=headers,
    )
    restored = client.get(f"/api/projects/{project['id']}", headers=member_headers)
    assert restored.status_code == 200
    assert restored.json()["id"] == project["id"]


def test_member_actions_are_audited(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    member_employee = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=manager["id"])
    added = client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member_employee["id"]},
        headers=headers,
    ).json()
    client.delete(
        f"/api/projects/{project['id']}/members/{member_employee['id']}",
        headers=headers,
    )
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member_employee["id"]},
        headers=headers,
    )
    with engine.connect() as connection:
        actions = {
            row[0]
            for row in connection.execute(
                text("SELECT action FROM audit_logs WHERE target_id = :target_id"),
                {"target_id": str(added["id"])},
            )
        }
    assert "PROJECT_MEMBER_ADD" in actions
    assert "PROJECT_MEMBER_REMOVE" in actions
    assert "PROJECT_MEMBER_RESTORE" in actions
