from fastapi.testclient import TestClient

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


def _setup_resources(client: TestClient):
    headers = admin_headers(client)
    pm_a = create_employee(client, headers, name="负责人A")
    pm_b = create_employee(client, headers, name="负责人B")
    member_a = create_employee(client, headers, name="成员A")
    member_d = create_employee(client, headers, name="同项目另一成员")
    extra = create_employee(client, headers)

    _, pm_a_user, pm_a_pass = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_a["id"]
    )
    _, pm_b_user, pm_b_pass = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_b["id"]
    )
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_a["id"]
    )
    _, other_member_user, other_member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_d["id"]
    )
    _, boss_user, boss_pass = create_user_account(
        client, headers, role_code="BOSS", employee_id=extra["id"]
    )

    project_a = create_project(client, headers, name="Project A", manager_employee_id=pm_a["id"])
    project_b = create_project(client, headers, name="Project B", manager_employee_id=pm_b["id"])
    client.post(f"/api/projects/{project_a['id']}/members", json={"employee_id": member_a["id"]}, headers=headers)
    client.post(f"/api/projects/{project_a['id']}/members", json={"employee_id": member_d["id"]}, headers=headers)

    resource_a = create_resource(client, headers, resource_name=unique("Resource A"))
    resource_b = create_resource(client, headers, resource_name=unique("Resource B"))
    resource_c = create_resource(client, headers, resource_name=unique("Resource C"))
    resource_d = create_resource(client, headers, resource_name=unique("Resource D"))

    create_allocation(
        client, headers, resource_a["id"], project_id=project_a["id"], employee_id=member_a["id"]
    )
    create_allocation(
        client, headers, resource_b["id"], project_id=project_b["id"], employee_id=pm_b["id"]
    )
    create_allocation(
        client, headers, resource_d["id"], project_id=project_a["id"], employee_id=member_d["id"]
    )

    return {
        "admin": headers,
        "boss": auth_headers_for(client, boss_user, boss_pass),
        "pm": auth_headers_for(client, pm_a_user, pm_a_pass),
        "other_pm": auth_headers_for(client, pm_b_user, pm_b_pass),
        "member": auth_headers_for(client, member_user, member_pass),
        "other_member": auth_headers_for(client, other_member_user, other_member_pass),
        "project_a": project_a,
        "project_b": project_b,
        "resource_a": resource_a,
        "resource_b": resource_b,
        "resource_c": resource_c,
        "resource_d": resource_d,
        "member_a": member_a,
        "member_d": member_d,
    }


def _ids(response) -> set[int]:
    assert response.status_code == 200, response.text
    return {item["id"] for item in response.json()["items"]}


def test_admin_sees_all_resources_and_can_write(client: TestClient) -> None:
    ctx = _setup_resources(client)
    ids = _ids(client.get("/api/resources", headers=ctx["admin"]))
    assert {ctx["resource_a"]["id"], ctx["resource_b"]["id"], ctx["resource_c"]["id"], ctx["resource_d"]["id"]} <= ids
    write = client.put(
        f"/api/resources/{ctx['resource_a']['id']}",
        json={"remark": "admin write"},
        headers=ctx["admin"],
    )
    assert write.status_code == 200


def test_boss_sees_all_resources_but_cannot_write(client: TestClient) -> None:
    ctx = _setup_resources(client)
    ids = _ids(client.get("/api/resources", headers=ctx["boss"]))
    assert {ctx["resource_a"]["id"], ctx["resource_b"]["id"], ctx["resource_c"]["id"], ctx["resource_d"]["id"]} <= ids
    write = client.put(
        f"/api/resources/{ctx['resource_a']['id']}",
        json={"remark": "boss write"},
        headers=ctx["boss"],
    )
    assert write.status_code == 403
    allocate = client.post(
        f"/api/resources/{ctx['resource_c']['id']}/allocations",
        json={"employee_id": ctx["member_a"]["id"]},
        headers=ctx["boss"],
    )
    assert allocate.status_code == 403


def test_project_manager_only_sees_managed_project_resources(client: TestClient) -> None:
    ctx = _setup_resources(client)
    ids = _ids(client.get("/api/resources", headers=ctx["pm"]))
    assert ctx["resource_a"]["id"] in ids
    assert ctx["resource_d"]["id"] in ids
    assert ctx["resource_b"]["id"] not in ids
    assert ctx["resource_c"]["id"] not in ids
    hidden = client.get(f"/api/resources/{ctx['resource_b']['id']}", headers=ctx["pm"])
    assert hidden.status_code == 404
    unassigned = client.get(f"/api/resources/{ctx['resource_c']['id']}", headers=ctx["pm"])
    assert unassigned.status_code == 404
    write = client.post(f"/api/resources/{ctx['resource_a']['id']}/disable", headers=ctx["pm"])
    assert write.status_code == 403


def test_member_only_sees_directly_assigned_resources(client: TestClient) -> None:
    ctx = _setup_resources(client)
    ids = _ids(client.get("/api/resources", headers=ctx["member"]))
    assert ids == {ctx["resource_a"]["id"]}
    assert client.get(f"/api/resources/{ctx['resource_d']['id']}", headers=ctx["member"]).status_code == 404
    assert client.get(f"/api/resources/{ctx['resource_b']['id']}", headers=ctx["member"]).status_code == 404
    assert client.get(f"/api/resources/{ctx['resource_c']['id']}", headers=ctx["member"]).status_code == 404
    write = client.put(
        f"/api/resources/{ctx['resource_a']['id']}",
        json={"remark": "member write"},
        headers=ctx["member"],
    )
    assert write.status_code == 403


def test_member_cannot_see_other_member_allocations_on_shared_resource(client: TestClient) -> None:
    ctx = _setup_resources(client)
    headers = ctx["admin"]
    create_allocation(
        client,
        headers,
        ctx["resource_a"]["id"],
        project_id=ctx["project_a"]["id"],
        employee_id=ctx["member_d"]["id"],
    )
    allocations = client.get(
        f"/api/resources/{ctx['resource_a']['id']}/allocations",
        headers=ctx["member"],
    )
    assert allocations.status_code == 200, allocations.text
    employee_ids = {item["employee_id"] for item in allocations.json()}
    assert employee_ids == {ctx["member_a"]["id"]}
    assert ctx["member_d"]["id"] not in employee_ids


def test_member_filter_cannot_expand_scope(client: TestClient) -> None:
    ctx = _setup_resources(client)
    response = client.get(
        "/api/resources",
        params={"employee_id": ctx["member_d"]["id"]},
        headers=ctx["member"],
    )
    assert _ids(response) == set()


def test_pm_filter_cannot_expand_scope(client: TestClient) -> None:
    ctx = _setup_resources(client)
    response = client.get(
        "/api/resources",
        params={"project_id": ctx["project_b"]["id"]},
        headers=ctx["pm"],
    )
    assert _ids(response) == set()


def test_guessing_resource_id_cannot_bypass_scope(client: TestClient) -> None:
    ctx = _setup_resources(client)
    assert client.get(f"/api/resources/{ctx['resource_b']['id']}", headers=ctx["member"]).status_code == 404
    assert client.get(
        f"/api/resources/{ctx['resource_b']['id']}/allocations",
        headers=ctx["member"],
    ).status_code == 404


def test_non_admin_cannot_release_allocation(client: TestClient) -> None:
    ctx = _setup_resources(client)
    listed = client.get(f"/api/resources/{ctx['resource_a']['id']}/allocations", headers=ctx["admin"])
    allocation_id = listed.json()[0]["id"]
    for role_headers in (ctx["boss"], ctx["pm"], ctx["member"]):
        response = client.delete(
            f"/api/resources/{ctx['resource_a']['id']}/allocations/{allocation_id}",
            headers=role_headers,
        )
        assert response.status_code == 403
