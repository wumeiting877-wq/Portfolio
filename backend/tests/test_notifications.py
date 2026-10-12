from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.models.enums import NotificationType
from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_allocation,
    create_employee,
    create_project,
    create_resource,
    create_user_account,
    unique,
)


def test_generate_expiring_expired_unassigned_and_idempotent(client: TestClient) -> None:
    headers = admin_headers(client)
    expiring = create_resource(
        client,
        headers,
        resource_name=unique("N-EXP"),
        expires_at=(date.today() + timedelta(days=5)).isoformat(),
        status="ACTIVE",
    )
    expired = create_resource(
        client,
        headers,
        resource_name=unique("N-EXPED"),
        expires_at=(date.today() - timedelta(days=1)).isoformat(),
        status="ACTIVE",
    )
    unassigned = create_resource(client, headers, resource_name=unique("N-UNAS"), status="ACTIVE")
    first = client.post("/api/notifications/refresh", headers=headers)
    assert first.status_code == 200
    second = client.post("/api/notifications/refresh", headers=headers)
    assert second.status_code == 200
    listed = client.get("/api/notifications", headers=headers, params={"page_size": 100})
    items = listed.json()["items"]
    types_by_resource = {}
    for item in items:
        types_by_resource.setdefault(item["resource_account_id"], []).append(item["type"])
    assert NotificationType.RESOURCE_EXPIRING.value in types_by_resource.get(expiring["id"], [])
    assert NotificationType.RESOURCE_EXPIRED.value in types_by_resource.get(expired["id"], [])
    assert NotificationType.RESOURCE_UNASSIGNED.value in types_by_resource.get(unassigned["id"], [])
    expiring_count = len(
        [item for item in items if item["resource_account_id"] == expiring["id"] and item["type"] == "RESOURCE_EXPIRING"]
    )
    assert expiring_count == 1


def test_notification_scope_and_status(client: TestClient) -> None:
    admin = admin_headers(client)
    manager = create_employee(client, admin)
    member_emp = create_employee(client, admin)
    outsider = create_employee(client, admin)
    project = create_project(client, admin, manager_employee_id=manager["id"])
    mine = create_resource(client, admin, resource_name=unique("N-MINE"), expires_at=(date.today() + timedelta(days=4)).isoformat())
    other = create_resource(client, admin, resource_name=unique("N-OTHER"), expires_at=(date.today() + timedelta(days=4)).isoformat())
    added = client.post(
        f"/api/projects/{project['id']}/members",
        headers=admin,
        json={"employee_id": member_emp["id"], "member_role": "MEMBER"},
    )
    assert added.status_code == 200
    create_allocation(client, admin, mine["id"], project_id=project["id"], employee_id=member_emp["id"])
    other_project = create_project(client, admin, manager_employee_id=outsider["id"])
    create_allocation(client, admin, other["id"], project_id=other_project["id"], employee_id=outsider["id"])
    client.post("/api/notifications/refresh", headers=admin)

    _, pm_user, pm_pass = create_user_account(client, admin, role_code="PROJECT_MANAGER", employee_id=manager["id"])
    _, member_user, member_pass = create_user_account(client, admin, role_code="MEMBER", employee_id=member_emp["id"])
    boss_person = create_employee(client, admin)
    _, boss_user, boss_pass = create_user_account(client, admin, role_code="BOSS", employee_id=boss_person["id"])

    admin_items = client.get("/api/notifications", headers=admin, params={"page_size": 100}).json()["items"]
    boss_items = client.get(
        "/api/notifications", headers=auth_headers_for(client, boss_user, boss_pass), params={"page_size": 100}
    ).json()["items"]
    pm_items = client.get(
        "/api/notifications", headers=auth_headers_for(client, pm_user, pm_pass), params={"page_size": 100}
    ).json()["items"]
    member_items = client.get(
        "/api/notifications", headers=auth_headers_for(client, member_user, member_pass), params={"page_size": 100}
    ).json()["items"]

    admin_ids = {item["resource_account_id"] for item in admin_items}
    assert mine["id"] in admin_ids
    assert other["id"] in admin_ids
    assert {item["resource_account_id"] for item in boss_items} >= {mine["id"], other["id"]}
    pm_ids = {item["resource_account_id"] for item in pm_items}
    assert mine["id"] in pm_ids
    assert other["id"] not in pm_ids
    member_ids = {item["resource_account_id"] for item in member_items}
    assert mine["id"] in member_ids
    assert other["id"] not in member_ids

    target = next(item for item in admin_items if item["resource_account_id"] == mine["id"])
    read = client.post(f"/api/notifications/{target['id']}/read", headers=admin)
    assert read.status_code == 200
    assert read.json()["status"] == "READ"
    resolved = client.post(f"/api/notifications/{target['id']}/resolve", headers=admin)
    assert resolved.json()["status"] == "RESOLVED"
