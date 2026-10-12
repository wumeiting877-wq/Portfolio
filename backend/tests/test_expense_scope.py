from decimal import Decimal

from fastapi.testclient import TestClient

from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_employee,
    create_expense,
    create_expense_type,
    create_project,
    create_user_account,
)


def _setup_expenses(client: TestClient):
    headers = admin_headers(client)
    pm_a = create_employee(client, headers, name="负责人A")
    pm_b = create_employee(client, headers, name="负责人B")
    member_a = create_employee(client, headers, name="成员A")
    member_d = create_employee(client, headers, name="同项目另一成员")
    extra = create_employee(client, headers)

    _, pm_a_user, pm_a_pass = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_a["id"]
    )
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_a["id"]
    )
    _, boss_user, boss_pass = create_user_account(
        client, headers, role_code="BOSS", employee_id=extra["id"]
    )

    project_a = create_project(client, headers, name="Project A", manager_employee_id=pm_a["id"])
    project_b = create_project(client, headers, name="Project B", manager_employee_id=pm_b["id"])
    client.post(
        f"/api/projects/{project_a['id']}/members",
        json={"employee_id": member_a["id"]},
        headers=headers,
    )
    client.post(
        f"/api/projects/{project_a['id']}/members",
        json={"employee_id": member_d["id"]},
        headers=headers,
    )

    expense_type = create_expense_type(client, headers)
    expense_a = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="100.00",
        distributions=[
            {
                "project_id": project_a["id"],
                "employee_id": member_a["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "100.00",
            }
        ],
    )
    expense_b = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="200.00",
        distributions=[
            {
                "project_id": project_b["id"],
                "employee_id": pm_b["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "200.00",
            }
        ],
    )
    expense_d = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="300.00",
        distributions=[
            {
                "project_id": project_a["id"],
                "employee_id": member_d["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "300.00",
            }
        ],
    )
    expense_e = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="1000.00",
        distributions=[
            {
                "project_id": project_a["id"],
                "allocation_method": "RATIO",
                "allocation_ratio": "0.6",
            },
            {
                "project_id": project_b["id"],
                "allocation_method": "RATIO",
                "allocation_ratio": "0.4",
            },
        ],
    )
    return {
        "admin": headers,
        "boss": auth_headers_for(client, boss_user, boss_pass),
        "pm": auth_headers_for(client, pm_a_user, pm_a_pass),
        "member": auth_headers_for(client, member_user, member_pass),
        "project_a": project_a,
        "project_b": project_b,
        "expense_a": expense_a,
        "expense_b": expense_b,
        "expense_d": expense_d,
        "expense_e": expense_e,
        "member_a": member_a,
        "member_d": member_d,
    }


def _ids(response) -> set[int]:
    assert response.status_code == 200, response.text
    return {item["id"] for item in response.json()["items"]}


def test_admin_sees_all_expenses_and_can_write(client: TestClient) -> None:
    ctx = _setup_expenses(client)
    ids = _ids(client.get("/api/expenses", headers=ctx["admin"]))
    assert {
        ctx["expense_a"]["id"],
        ctx["expense_b"]["id"],
        ctx["expense_d"]["id"],
        ctx["expense_e"]["id"],
    } <= ids
    updated = client.put(
        f"/api/expenses/{ctx['expense_a']['id']}",
        json={"description": "admin write"},
        headers=ctx["admin"],
    )
    assert updated.status_code == 200


def test_boss_sees_all_expenses_but_cannot_write(client: TestClient) -> None:
    ctx = _setup_expenses(client)
    ids = _ids(client.get("/api/expenses", headers=ctx["boss"]))
    assert {
        ctx["expense_a"]["id"],
        ctx["expense_b"]["id"],
        ctx["expense_d"]["id"],
        ctx["expense_e"]["id"],
    } <= ids
    write = client.put(
        f"/api/expenses/{ctx['expense_a']['id']}",
        json={"description": "boss write"},
        headers=ctx["boss"],
    )
    assert write.status_code == 403
    generate = client.post("/api/expenses/recurring/generate", headers=ctx["boss"])
    assert generate.status_code == 403


def test_pm_only_sees_managed_project_share(client: TestClient) -> None:
    ctx = _setup_expenses(client)
    ids = _ids(client.get("/api/expenses", headers=ctx["pm"]))
    assert ctx["expense_a"]["id"] in ids
    assert ctx["expense_d"]["id"] in ids
    assert ctx["expense_e"]["id"] in ids
    assert ctx["expense_b"]["id"] not in ids
    hidden = client.get(f"/api/expenses/{ctx['expense_b']['id']}", headers=ctx["pm"])
    assert hidden.status_code == 404
    shared = client.get(f"/api/expenses/{ctx['expense_e']['id']}", headers=ctx["pm"])
    assert shared.status_code == 200
    body = shared.json()
    assert Decimal(body["amount"]) == Decimal("600.00")
    assert Decimal(body["visible_allocated_amount"]) == Decimal("600.00")
    assert body["original_amount_visible"] is False
    assert {item["project_id"] for item in body["distributions"]} == {ctx["project_a"]["id"]}
    write = client.post(f"/api/expenses/{ctx['expense_a']['id']}/void", headers=ctx["pm"])
    assert write.status_code == 403


def test_member_only_sees_direct_own_share(client: TestClient) -> None:
    ctx = _setup_expenses(client)
    ids = _ids(client.get("/api/expenses", headers=ctx["member"]))
    assert ids == {ctx["expense_a"]["id"]}
    assert client.get(f"/api/expenses/{ctx['expense_d']['id']}", headers=ctx["member"]).status_code == 404
    assert client.get(f"/api/expenses/{ctx['expense_b']['id']}", headers=ctx["member"]).status_code == 404
    assert client.get(f"/api/expenses/{ctx['expense_e']['id']}", headers=ctx["member"]).status_code == 404
    own = client.get(f"/api/expenses/{ctx['expense_a']['id']}", headers=ctx["member"])
    assert own.status_code == 200
    assert Decimal(own.json()["amount"]) == Decimal("100.00")
    assert own.json()["distributions"][0]["employee_id"] == ctx["member_a"]["id"]
    write = client.put(
        f"/api/expenses/{ctx['expense_a']['id']}",
        json={"description": "member write"},
        headers=ctx["member"],
    )
    assert write.status_code == 403
