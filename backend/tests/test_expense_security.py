from fastapi.testclient import TestClient

from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_employee,
    create_expense,
    create_project,
    create_user_account,
)


def test_pm_cannot_expand_scope_with_other_project_filter(client: TestClient) -> None:
    headers = admin_headers(client)
    pm = create_employee(client, headers, name="PM")
    other_pm = create_employee(client, headers, name="Other PM")
    _, pm_user, pm_pass = create_user_account(client, headers, role_code="PROJECT_MANAGER", employee_id=pm["id"])
    project_a = create_project(client, headers, manager_employee_id=pm["id"])
    project_b = create_project(client, headers, manager_employee_id=other_pm["id"])
    expense_b = create_expense(
        client,
        headers,
        amount="50.00",
        distributions=[
            {"project_id": project_b["id"], "allocation_method": "DIRECT", "allocated_amount": "50.00"}
        ],
    )
    create_expense(
        client,
        headers,
        amount="40.00",
        distributions=[
            {"project_id": project_a["id"], "allocation_method": "DIRECT", "allocated_amount": "40.00"}
        ],
    )
    pm_headers = auth_headers_for(client, pm_user, pm_pass)
    listed = client.get("/api/expenses", params={"project_id": project_b["id"]}, headers=pm_headers)
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert expense_b["id"] not in ids


def test_member_cannot_expand_scope_with_other_employee_filter(client: TestClient) -> None:
    headers = admin_headers(client)
    member = create_employee(client, headers, name="成员")
    other = create_employee(client, headers, name="其他人")
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member["id"]
    )
    other_expense = create_expense(
        client,
        headers,
        amount="70.00",
        distributions=[
            {"employee_id": other["id"], "allocation_method": "DIRECT", "allocated_amount": "70.00"}
        ],
    )
    create_expense(
        client,
        headers,
        amount="30.00",
        distributions=[
            {"employee_id": member["id"], "allocation_method": "DIRECT", "allocated_amount": "30.00"}
        ],
    )
    member_headers = auth_headers_for(client, member_user, member_pass)
    listed = client.get("/api/expenses", params={"employee_id": other["id"]}, headers=member_headers)
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert other_expense["id"] not in ids


def test_guessing_expense_id_is_not_found(client: TestClient) -> None:
    headers = admin_headers(client)
    member = create_employee(client, headers)
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member["id"]
    )
    other = create_employee(client, headers)
    hidden = create_expense(
        client,
        headers,
        amount="15.00",
        distributions=[
            {"employee_id": other["id"], "allocation_method": "DIRECT", "allocated_amount": "15.00"}
        ],
    )
    member_headers = auth_headers_for(client, member_user, member_pass)
    assert client.get(f"/api/expenses/{hidden['id']}", headers=member_headers).status_code == 404
    assert client.get(f"/api/expenses/{hidden['id'] * 1000}", headers=member_headers).status_code == 404


def test_non_admin_cannot_modify_amount_or_distribution(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    expense = create_expense(
        client,
        headers,
        amount="80.00",
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "80.00"}
        ],
    )
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="BOSS", employee_id=employee["id"]
    )
    boss = auth_headers_for(client, username, password)
    amount = client.put(
        f"/api/expenses/{expense['id']}",
        json={"amount": "10.00", "distributions": [
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "10.00"}
        ]},
        headers=boss,
    )
    assert amount.status_code == 403
    voided = client.post(f"/api/expenses/{expense['id']}/void", headers=boss)
    assert voided.status_code == 403
