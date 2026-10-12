from fastapi.testclient import TestClient

from tests.helpers import admin_headers, create_employee, create_user_account, login, unique


def test_admin_can_create_system_user(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, username, _password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    assert user["username"] == username
    assert "password_hash" not in user
    listed = client.get("/api/users", headers=headers)
    assert listed.status_code == 200
    assert all("password_hash" not in item for item in listed.json())


def test_non_admin_cannot_create_user(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    token = login(client, username, password).json()["access_token"]
    response = client.post(
        "/api/users",
        json={"username": unique("blocked"), "password": "Passw0rd!", "role_id": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_duplicate_username_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, username, _password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    roles = client.get("/api/roles", headers=headers).json()
    member_role = next(item["id"] for item in roles if item["code"] == "MEMBER")
    another_employee = create_employee(client, headers)
    response = client.post(
        "/api/users",
        json={
            "username": username,
            "password": "Passw0rd!",
            "role_id": member_role,
            "employee_id": another_employee["id"],
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "用户名已存在"
    assert user["username"] == username


def test_reset_password_success(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, username, old_password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    reset = client.post(
        f"/api/users/{user['id']}/reset-password",
        json={"password": "ResetPass1"},
        headers=headers,
    )
    assert reset.status_code == 200
    assert login(client, username, old_password).status_code == 401
    assert login(client, username, "ResetPass1").status_code == 200


def test_disable_then_cannot_login(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    assert login(client, username, password).status_code == 200
    disable = client.post(f"/api/users/{user['id']}/disable", headers=headers)
    assert disable.status_code == 200
    assert login(client, username, password).status_code == 403
    enable = client.post(f"/api/users/{user['id']}/enable", headers=headers)
    assert enable.status_code == 200
    assert login(client, username, password).status_code == 200


def test_physical_delete_user_not_allowed(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, _username, _password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    response = client.delete(f"/api/users/{user['id']}", headers=headers)
    assert response.status_code == 405
