from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from tests.helpers import admin_headers, create_employee, create_project, unique


def test_admin_create_update_archive_project(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers, name="负责人甲")
    created = create_project(
        client,
        headers,
        name="项目甲",
        manager_employee_id=manager["id"],
        status="PLANNING",
    )
    assert created["name"] == "项目甲"
    assert created["manager_employee_id"] == manager["id"]
    assert created["manager_name"] == "负责人甲"
    assert created["member_count"] == 1
    assert created["status"] == "PLANNING"

    project_id = created["id"]
    updated = client.put(
        f"/api/projects/{project_id}",
        json={"name": "项目甲-修订", "status": "ACTIVE"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "项目甲-修订"
    assert updated.json()["status"] == "ACTIVE"

    archived = client.post(f"/api/projects/{project_id}/archive", headers=headers)
    assert archived.status_code == 200, archived.text
    assert archived.json()["status"] == "ARCHIVED"


def test_duplicate_project_code_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    code = unique("CODE")
    create_project(client, headers, project_code=code, manager_employee_id=manager["id"])
    response = client.post(
        "/api/projects",
        json={
            "project_code": code,
            "name": "重复编码",
            "manager_employee_id": manager["id"],
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_invalid_manager_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.post(
        "/api/projects",
        json={
            "project_code": unique("CODE"),
            "name": "无效负责人",
            "manager_employee_id": 999999,
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert response.status_code == 404


def test_inactive_manager_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    client.delete(f"/api/employees/{manager['id']}", headers=headers)
    response = client.post(
        "/api/projects",
        json={
            "project_code": unique("CODE"),
            "name": "停用负责人",
            "manager_employee_id": manager["id"],
            "status": "ACTIVE",
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_manager_is_auto_added_to_project_members(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers, name="自动成员负责人")
    project = create_project(client, headers, manager_employee_id=manager["id"])
    members = client.get(f"/api/projects/{project['id']}/members", headers=headers)
    assert members.status_code == 200, members.text
    body = members.json()
    assert len(body) == 1
    assert body[0]["employee_id"] == manager["id"]
    assert body[0]["member_role"] == "PROJECT_MANAGER"
    assert body[0]["is_active"] is True


def test_project_write_actions_are_audited(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=manager["id"])
    client.put(
        f"/api/projects/{project['id']}",
        json={"name": "审计更新"},
        headers=headers,
    )
    client.post(f"/api/projects/{project['id']}/archive", headers=headers)
    with engine.connect() as connection:
        actions = {
            row[0]
            for row in connection.execute(
                text("SELECT action FROM audit_logs WHERE target_id = :target_id"),
                {"target_id": str(project["id"])},
            )
        }
    assert "PROJECT_CREATE" in actions
    assert "PROJECT_UPDATE" in actions
    assert "PROJECT_ARCHIVE" in actions
