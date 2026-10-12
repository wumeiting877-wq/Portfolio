from fastapi.testclient import TestClient

from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_employee,
    create_project,
    create_user_account,
)


def _setup_two_projects(client: TestClient):
    headers = admin_headers(client)
    pm_a = create_employee(client, headers, name="负责人A")
    pm_b = create_employee(client, headers, name="负责人B")
    member_a = create_employee(client, headers, name="成员A")
    member_b = create_employee(client, headers, name="成员B")
    extra_member = create_employee(client, headers, name="多项目成员")

    _, pm_a_user, pm_a_pass = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_a["id"]
    )
    _, pm_b_user, pm_b_pass = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_b["id"]
    )
    _, member_a_user, member_a_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_a["id"]
    )
    _, member_b_user, member_b_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_b["id"]
    )
    _, extra_user, extra_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=extra_member["id"]
    )
    _, boss_user, boss_pass = create_user_account(
        client, headers, role_code="BOSS", employee_id=create_employee(client, headers)["id"]
    )

    project_a = create_project(
        client, headers, name="Project A", manager_employee_id=pm_a["id"]
    )
    project_b = create_project(
        client, headers, name="Project B", manager_employee_id=pm_b["id"]
    )
    client.post(
        f"/api/projects/{project_a['id']}/members",
        json={"employee_id": member_a["id"]},
        headers=headers,
    )
    client.post(
        f"/api/projects/{project_b['id']}/members",
        json={"employee_id": member_b["id"]},
        headers=headers,
    )
    client.post(
        f"/api/projects/{project_a['id']}/members",
        json={"employee_id": extra_member["id"]},
        headers=headers,
    )
    client.post(
        f"/api/projects/{project_b['id']}/members",
        json={"employee_id": extra_member["id"]},
        headers=headers,
    )
    return {
        "admin": headers,
        "project_a": project_a,
        "project_b": project_b,
        "pm_a": auth_headers_for(client, pm_a_user, pm_a_pass),
        "pm_b": auth_headers_for(client, pm_b_user, pm_b_pass),
        "member_a": auth_headers_for(client, member_a_user, member_a_pass),
        "member_b": auth_headers_for(client, member_b_user, member_b_pass),
        "extra_member": auth_headers_for(client, extra_user, extra_pass),
        "boss": auth_headers_for(client, boss_user, boss_pass),
        "pm_a_employee": pm_a,
    }


def _ids(response) -> set[int]:
    assert response.status_code == 200, response.text
    return {item["id"] for item in response.json()["items"]}


def test_admin_sees_all_projects_and_can_write(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    ids = _ids(client.get("/api/projects", headers=ctx["admin"]))
    assert ctx["project_a"]["id"] in ids
    assert ctx["project_b"]["id"] in ids
    write = client.put(
        f"/api/projects/{ctx['project_a']['id']}",
        json={"description": "admin write"},
        headers=ctx["admin"],
    )
    assert write.status_code == 200


def test_boss_sees_all_projects_but_cannot_write(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    ids = _ids(client.get("/api/projects", headers=ctx["boss"]))
    assert ctx["project_a"]["id"] in ids
    assert ctx["project_b"]["id"] in ids
    detail = client.get(f"/api/projects/{ctx['project_a']['id']}", headers=ctx["boss"])
    assert detail.status_code == 200
    members = client.get(f"/api/projects/{ctx['project_a']['id']}/members", headers=ctx["boss"])
    assert members.status_code == 200
    assert client.post(
        "/api/projects",
        json={
            "project_code": "BOSS-WRITE",
            "name": "越权",
            "manager_employee_id": ctx["pm_a_employee"]["id"],
            "status": "ACTIVE",
        },
        headers=ctx["boss"],
    ).status_code == 403
    assert client.put(
        f"/api/projects/{ctx['project_a']['id']}",
        json={"name": "越权修改"},
        headers=ctx["boss"],
    ).status_code == 403
    assert client.post(
        f"/api/projects/{ctx['project_a']['id']}/archive",
        headers=ctx["boss"],
    ).status_code == 403
    assert client.post(
        f"/api/projects/{ctx['project_a']['id']}/members",
        json={"employee_id": ctx["pm_a_employee"]["id"]},
        headers=ctx["boss"],
    ).status_code == 403


def test_project_manager_only_sees_managed_projects(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    ids = _ids(client.get("/api/projects", headers=ctx["pm_a"]))
    assert ids == {ctx["project_a"]["id"]}
    assert client.get(f"/api/projects/{ctx['project_a']['id']}", headers=ctx["pm_a"]).status_code == 200
    assert client.get(f"/api/projects/{ctx['project_b']['id']}", headers=ctx["pm_a"]).status_code == 404
    assert client.put(
        f"/api/projects/{ctx['project_a']['id']}",
        json={"name": "越权修改"},
        headers=ctx["pm_a"],
    ).status_code == 403
    assert client.post(
        f"/api/projects/{ctx['project_a']['id']}/archive",
        headers=ctx["pm_a"],
    ).status_code == 403
    assert client.post(
        f"/api/projects/{ctx['project_a']['id']}/members",
        json={"employee_id": ctx["pm_a_employee"]["id"]},
        headers=ctx["pm_a"],
    ).status_code == 403


def test_member_only_sees_joined_projects(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    ids = _ids(client.get("/api/projects", headers=ctx["member_a"]))
    assert ids == {ctx["project_a"]["id"]}
    assert client.get(f"/api/projects/{ctx['project_a']['id']}", headers=ctx["member_a"]).status_code == 200
    assert client.get(f"/api/projects/{ctx['project_b']['id']}", headers=ctx["member_a"]).status_code == 404
    assert client.put(
        f"/api/projects/{ctx['project_a']['id']}",
        json={"name": "越权修改"},
        headers=ctx["member_a"],
    ).status_code == 403


def test_member_can_see_multiple_joined_projects(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    ids = _ids(client.get("/api/projects", headers=ctx["extra_member"]))
    assert ids == {ctx["project_a"]["id"], ctx["project_b"]["id"]}


def test_guessing_project_id_cannot_bypass_scope(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    guessed = ctx["project_b"]["id"]
    assert client.get(f"/api/projects/{guessed}", headers=ctx["pm_a"]).status_code == 404
    assert client.get(f"/api/projects/{guessed}/members", headers=ctx["member_a"]).status_code == 404
    assert client.get("/api/projects/999999", headers=ctx["pm_a"]).status_code == 404


def test_forged_employee_query_cannot_expand_scope(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    response = client.get(
        "/api/projects",
        headers=ctx["pm_a"],
        params={"employee_id": ctx["project_b"]["manager_employee_id"]},
    )
    ids = _ids(response)
    assert ids == {ctx["project_a"]["id"]}


def test_manager_scope_follows_manager_employee_id(client: TestClient) -> None:
    ctx = _setup_two_projects(client)
    client.put(
        f"/api/projects/{ctx['project_a']['id']}",
        json={"manager_employee_id": ctx["project_b"]["manager_employee_id"]},
        headers=ctx["admin"],
    )
    pm_a_ids = _ids(client.get("/api/projects", headers=ctx["pm_a"]))
    pm_b_ids = _ids(client.get("/api/projects", headers=ctx["pm_b"]))
    assert ctx["project_a"]["id"] not in pm_a_ids
    assert ctx["project_a"]["id"] in pm_b_ids
    assert ctx["project_b"]["id"] in pm_b_ids
