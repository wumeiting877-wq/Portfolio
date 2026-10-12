from fastapi.testclient import TestClient

from tests.helpers import admin_headers, create_employee, create_user_account, login


def _token_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = login(client, username, password)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_can_create_employee(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers, name="管理员创建")
    assert employee["name"] == "管理员创建"


def test_boss_cannot_create_employee(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="BOSS", employee_id=employee["id"]
    )
    boss_headers = _token_headers(client, username, password)
    response = client.post(
        "/api/employees",
        json={"employee_no": "X-BOSS", "name": "越权"},
        headers=boss_headers,
    )
    assert response.status_code == 403


def test_project_manager_cannot_create_employee(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=employee["id"]
    )
    pm_headers = _token_headers(client, username, password)
    response = client.post(
        "/api/employees",
        json={"employee_no": "X-PM", "name": "越权"},
        headers=pm_headers,
    )
    assert response.status_code == 403


def test_member_cannot_create_employee(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    member_headers = _token_headers(client, username, password)
    response = client.post(
        "/api/employees",
        json={"employee_no": "X-MB", "name": "越权"},
        headers=member_headers,
    )
    assert response.status_code == 403


def test_member_cannot_list_employees(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    member_headers = _token_headers(client, username, password)
    response = client.get("/api/employees", headers=member_headers)
    assert response.status_code == 403


def test_non_admin_cannot_access_users(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="BOSS", employee_id=employee["id"]
    )
    boss_headers = _token_headers(client, username, password)
    response = client.get("/api/users", headers=boss_headers)
    assert response.status_code == 403
