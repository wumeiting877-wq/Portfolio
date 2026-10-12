from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import engine
from tests.helpers import (
    admin_headers,
    create_allocation,
    create_employee,
    create_project,
    create_resource,
    unique,
)


def test_project_level_allocation_succeeds(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=manager["id"])
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], project_id=project["id"])
    assert allocation["project_id"] == project["id"]
    assert allocation["employee_id"] is None
    assert allocation["is_active"] is True


def test_member_level_allocation_succeeds(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers, name="个人使用人")
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], employee_id=employee["id"])
    assert allocation["employee_id"] == employee["id"]
    assert allocation["project_id"] is None
    assert allocation["employee_name"] == "个人使用人"


def test_project_and_member_allocation_succeeds(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    member = create_employee(client, headers, name="李四")
    project = create_project(client, headers, manager_employee_id=manager["id"])
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member["id"]},
        headers=headers,
    )
    resource = create_resource(client, headers, resource_name=unique("Cursor-开发01"))
    allocation = create_allocation(
        client, headers, resource["id"], project_id=project["id"], employee_id=member["id"]
    )
    assert allocation["project_id"] == project["id"]
    assert allocation["employee_id"] == member["id"]


def test_same_resource_can_be_shared_by_multiple_people(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    zhang = create_employee(client, headers, name="张三")
    li = create_employee(client, headers, name="李四")
    project = create_project(client, headers, manager_employee_id=manager["id"])
    client.post(f"/api/projects/{project['id']}/members", json={"employee_id": zhang["id"]}, headers=headers)
    client.post(f"/api/projects/{project['id']}/members", json={"employee_id": li["id"]}, headers=headers)
    resource = create_resource(client, headers, resource_name=unique("ChatGPT-Team-01"))
    create_allocation(client, headers, resource["id"], project_id=project["id"], employee_id=zhang["id"])
    create_allocation(client, headers, resource["id"], project_id=project["id"], employee_id=li["id"])
    detail = client.get(f"/api/resources/{resource['id']}", headers=headers)
    body = detail.json()
    assert body["is_shared"] is True
    assert body["active_user_count"] == 2
    assert body["active_project_count"] == 1


def test_cross_project_sharing_succeeds(client: TestClient) -> None:
    headers = admin_headers(client)
    pm_a = create_employee(client, headers, name="新华负责人")
    pm_b = create_employee(client, headers, name="佳悦负责人")
    wang = create_employee(client, headers, name="王五")
    project_a = create_project(client, headers, name="新华制药", manager_employee_id=pm_a["id"])
    project_b = create_project(client, headers, name="佳悦", manager_employee_id=pm_b["id"])
    client.post(f"/api/projects/{project_b['id']}/members", json={"employee_id": wang["id"]}, headers=headers)
    resource = create_resource(client, headers, resource_name=unique("ChatGPT-Team-01"))
    create_allocation(client, headers, resource["id"], project_id=project_a["id"], employee_id=pm_a["id"])
    create_allocation(client, headers, resource["id"], project_id=project_b["id"], employee_id=wang["id"])
    detail = client.get(f"/api/resources/{resource['id']}", headers=headers).json()
    assert detail["is_shared"] is True
    assert detail["active_project_count"] == 2
    allocations = client.get(f"/api/resources/{resource['id']}/allocations", headers=headers).json()
    assert len([item for item in allocations if item["is_active"]]) == 2


def test_mismatched_project_member_allocation_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    outsider = create_employee(client, headers, name="局外人")
    project = create_project(client, headers, name="新华制药", manager_employee_id=manager["id"])
    resource = create_resource(client, headers)
    response = client.post(
        f"/api/resources/{resource['id']}/allocations",
        json={"project_id": project["id"], "employee_id": outsider["id"]},
        headers=headers,
    )
    assert response.status_code == 400


def test_allocation_requires_project_or_employee(client: TestClient) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    response = client.post(f"/api/resources/{resource['id']}/allocations", json={}, headers=headers)
    assert response.status_code == 400


def test_release_and_restore_allocation(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], employee_id=employee["id"])
    released = client.delete(
        f"/api/resources/{resource['id']}/allocations/{allocation['id']}",
        headers=headers,
    )
    assert released.status_code == 200, released.text
    assert released.json()["is_active"] is False
    assert released.json()["released_at"] is not None
    detail = client.get(f"/api/resources/{resource['id']}", headers=headers).json()
    assert detail["active_user_count"] == 0
    restored = client.post(
        f"/api/resources/{resource['id']}/allocations/{allocation['id']}/restore",
        headers=headers,
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["is_active"] is True
    assert restored.json()["released_at"] is None


def test_recreate_same_allocation_restores_history(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], employee_id=employee["id"])
    client.delete(f"/api/resources/{resource['id']}/allocations/{allocation['id']}", headers=headers)
    restored = create_allocation(client, headers, resource["id"], employee_id=employee["id"])
    assert restored["id"] == allocation["id"]
    assert restored["is_active"] is True


def test_allocation_actions_are_audited(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], employee_id=employee["id"])
    client.delete(f"/api/resources/{resource['id']}/allocations/{allocation['id']}", headers=headers)
    client.post(
        f"/api/resources/{resource['id']}/allocations/{allocation['id']}/restore",
        headers=headers,
    )
    with engine.connect() as connection:
        actions = {
            row[0]
            for row in connection.execute(
                text("SELECT action FROM audit_logs WHERE target_id = :target_id"),
                {"target_id": str(allocation["id"])},
            )
        }
    assert "RESOURCE_ALLOCATION_ADD" in actions
    assert "RESOURCE_ALLOCATION_RELEASE" in actions
    assert "RESOURCE_ALLOCATION_RESTORE" in actions
