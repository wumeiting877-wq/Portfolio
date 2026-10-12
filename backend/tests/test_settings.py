from fastapi.testclient import TestClient

from app.core.config import Settings, validate_runtime_config
from tests.helpers import admin_headers, auth_headers_for, create_employee, create_user_account


def test_admin_read_write_settings(client: TestClient) -> None:
    headers = admin_headers(client)
    current = client.get("/api/settings", headers=headers)
    assert current.status_code == 200
    body = current.json()
    assert body["default_currency"] in {"CNY", "USD"}
    updated = client.put(
        "/api/settings",
        headers=headers,
        json={"expiring_days": 14, "business_timezone": "Asia/Shanghai", "default_currency": "USD"},
    )
    assert updated.status_code == 200
    assert updated.json()["expiring_days"] == 14
    assert updated.json()["default_currency"] == "USD"
    restored = client.put(
        "/api/settings",
        headers=headers,
        json={"expiring_days": 30, "default_currency": "CNY"},
    )
    assert restored.status_code == 200


def test_boss_read_only_settings(client: TestClient) -> None:
    admin = admin_headers(client)
    employee = create_employee(client, admin)
    _, username, password = create_user_account(client, admin, role_code="BOSS", employee_id=employee["id"])
    headers = auth_headers_for(client, username, password)
    assert client.get("/api/settings", headers=headers).status_code == 200
    assert client.put("/api/settings", headers=headers, json={"expiring_days": 10}).status_code == 403


def test_pm_member_settings_forbidden(client: TestClient) -> None:
    admin = admin_headers(client)
    pm = create_employee(client, admin)
    member = create_employee(client, admin)
    _, pm_user, pm_pass = create_user_account(client, admin, role_code="PROJECT_MANAGER", employee_id=pm["id"])
    _, member_user, member_pass = create_user_account(client, admin, role_code="MEMBER", employee_id=member["id"])
    assert client.get("/api/settings", headers=auth_headers_for(client, pm_user, pm_pass)).status_code == 403
    assert client.get("/api/settings", headers=auth_headers_for(client, member_user, member_pass)).status_code == 403


def test_invalid_timezone_rejected(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.put("/api/settings", headers=headers, json={"business_timezone": "Not/A_Zone"})
    assert response.status_code == 400


def test_default_currency_does_not_create_fx_total(client: TestClient) -> None:
    headers = admin_headers(client)
    overview = client.get("/api/statistics/overview", headers=headers)
    assert overview.status_code == 200
    assert "total" not in overview.json()
    assert "amounts_by_currency" in overview.json()


def test_production_config_rejects_placeholders() -> None:
    values = Settings(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET_KEY="change_me",
        POSTGRES_PASSWORD="change_me",
        INITIAL_ADMIN_PASSWORD="change_me",
        CORS_ORIGINS="https://app.example.com",
    )
    try:
        validate_runtime_config(values)
        assert False, "expected production placeholder rejection"
    except RuntimeError:
        pass


def test_production_rejects_debug_and_star_cors() -> None:
    debug_values = Settings(
        APP_ENV="production",
        DEBUG=True,
        JWT_SECRET_KEY="a-very-long-production-secret",
        POSTGRES_PASSWORD="prod-db-pass",
        INITIAL_ADMIN_PASSWORD="prod-admin-pass",
        CORS_ORIGINS="https://app.example.com",
    )
    try:
        validate_runtime_config(debug_values)
        assert False
    except RuntimeError:
        pass
    star = Settings(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET_KEY="a-very-long-production-secret",
        POSTGRES_PASSWORD="prod-db-pass",
        INITIAL_ADMIN_PASSWORD="prod-admin-pass",
        CORS_ORIGINS="*",
    )
    try:
        validate_runtime_config(star)
        assert False
    except RuntimeError:
        pass


def test_development_star_cors_still_rejected() -> None:
    values = Settings(APP_ENV="development", CORS_ORIGINS="*")
    try:
        validate_runtime_config(values)
        assert False
    except RuntimeError:
        pass


def test_version_endpoint(client: TestClient) -> None:
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "project-cost-hub"
    assert body["version"] == "1.0.0"
    dumped = str(body).lower()
    assert "password" not in dumped
    assert "secret" not in dumped
    assert "postgres" not in dumped
