from fastapi.testclient import TestClient

from tests.helpers import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    admin_headers,
    create_employee,
    create_user_account,
    login,
)


def test_login_success(client: TestClient) -> None:
    response = login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == ADMIN_USERNAME
    assert "password_hash" not in body["user"]
    assert "password" not in body["user"]


def test_login_wrong_password(client: TestClient) -> None:
    response = login(client, ADMIN_USERNAME, "wrong-password")
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_login_unknown_user_same_message(client: TestClient) -> None:
    response = login(client, "missing_user_xyz", "whatever")
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_disabled_user_cannot_login(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    disable = client.post(f"/api/users/{user['id']}/disable", headers=headers)
    assert disable.status_code == 200
    response = login(client, username, password)
    assert response.status_code == 403
    assert response.json()["detail"] == "账号已停用"


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_token(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == ADMIN_USERNAME
    assert body["role"] == "ADMIN"
    assert body["scope"] == "GLOBAL"
    assert body["status"] == "ACTIVE"


def test_change_password_requires_old_password(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    user, username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"]
    )
    token = login(client, username, password).json()["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}
    bad = client.post(
        "/api/auth/change-password",
        json={"old_password": "incorrect", "new_password": "NewPassw0rd!"},
        headers=user_headers,
    )
    assert bad.status_code == 400
    ok = client.post(
        "/api/auth/change-password",
        json={"old_password": password, "new_password": "NewPassw0rd!"},
        headers=user_headers,
    )
    assert ok.status_code == 200
    assert login(client, username, password).status_code == 401
    assert login(client, username, "NewPassw0rd!").status_code == 200
