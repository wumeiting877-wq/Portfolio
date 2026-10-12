from fastapi.testclient import TestClient

from tests.helpers import admin_headers, auth_headers_for, create_employee, create_user_account, unique


def test_admin_and_boss_can_query_audit(client: TestClient) -> None:
    admin = admin_headers(client)
    create_employee(client, admin, employee_no=unique("AUD"))
    listed = client.get("/api/audit-logs", headers=admin)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    item = listed.json()["items"][0]
    detail = client.get(f"/api/audit-logs/{item['id']}", headers=admin)
    assert detail.status_code == 200
    boss_emp = create_employee(client, admin)
    _, username, password = create_user_account(client, admin, role_code="BOSS", employee_id=boss_emp["id"])
    boss = auth_headers_for(client, username, password)
    assert client.get("/api/audit-logs", headers=boss).status_code == 200


def test_pm_and_member_denied_audit(client: TestClient) -> None:
    admin = admin_headers(client)
    pm_emp = create_employee(client, admin)
    member_emp = create_employee(client, admin)
    _, pm_user, pm_pass = create_user_account(client, admin, role_code="PROJECT_MANAGER", employee_id=pm_emp["id"])
    _, member_user, member_pass = create_user_account(client, admin, role_code="MEMBER", employee_id=member_emp["id"])
    assert client.get("/api/audit-logs", headers=auth_headers_for(client, pm_user, pm_pass)).status_code == 403
    assert client.get("/api/audit-logs", headers=auth_headers_for(client, member_user, member_pass)).status_code == 403


def test_audit_hides_password_fields(client: TestClient) -> None:
    admin = admin_headers(client)
    employee = create_employee(client, admin)
    create_user_account(client, admin, role_code="MEMBER", employee_id=employee["id"], password="Passw0rd!")
    listed = client.get("/api/audit-logs", headers=admin, params={"module": "users", "page_size": 50})
    assert listed.status_code == 200
    blob = str(listed.json()).lower()
    assert "password_hash" not in blob
    assert "passw0rd" not in blob
    assert '"password"' not in blob


def test_audit_filter_and_pagination(client: TestClient) -> None:
    admin = admin_headers(client)
    create_employee(client, admin, employee_no=unique("PG1"))
    create_employee(client, admin, employee_no=unique("PG2"))
    page1 = client.get("/api/audit-logs", headers=admin, params={"page": 1, "page_size": 1, "module": "employees"})
    page2 = client.get("/api/audit-logs", headers=admin, params={"page": 2, "page_size": 1, "module": "employees"})
    assert page1.status_code == 200
    assert page1.json()["page_size"] == 1
    assert page1.json()["items"][0]["id"] != page2.json()["items"][0]["id"]
    filtered = client.get("/api/audit-logs", headers=admin, params={"module": "employees", "action": "create_employee"})
    assert filtered.status_code == 200
    assert all(item["module"] == "employees" for item in filtered.json()["items"])
