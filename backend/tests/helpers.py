import uuid

from fastapi.testclient import TestClient

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "change_me"


def unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def login(client: TestClient, username: str, password: str):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def admin_headers(client: TestClient) -> dict[str, str]:
    response = login(client, ADMIN_USERNAME, ADMIN_PASSWORD)
    assert response.status_code == 200, response.text
    return auth_header(response.json()["access_token"])


def role_ids(client: TestClient, headers: dict[str, str]) -> dict[str, int]:
    response = client.get("/api/roles", headers=headers)
    assert response.status_code == 200, response.text
    return {item["code"]: item["id"] for item in response.json()}


def create_employee(client: TestClient, headers: dict[str, str], **overrides):
    payload = {
        "employee_no": unique("E"),
        "name": "测试人员",
        "department": "测试部",
        "position": "工程师",
        "email": "test@example.com",
        "phone": "13800000000",
        "remark": "gate1",
    }
    payload.update(overrides)
    response = client.post("/api/employees", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def create_user_account(
    client: TestClient,
    headers: dict[str, str],
    *,
    role_code: str,
    password: str = "Passw0rd!",
    username: str | None = None,
    employee_id: int | None = None,
):
    roles = role_ids(client, headers)
    payload = {
        "username": username or unique("u"),
        "password": password,
        "role_id": roles[role_code],
        "employee_id": employee_id,
    }
    response = client.post("/api/users", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    return body, payload["username"], password


def auth_headers_for(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = login(client, username, password)
    assert response.status_code == 200, response.text
    return auth_header(response.json()["access_token"])


def create_project(client: TestClient, headers: dict[str, str], **overrides):
    payload = {
        "project_code": unique("P"),
        "name": "测试项目",
        "status": "ACTIVE",
        "description": "gate2",
    }
    payload.update(overrides)
    if "manager_employee_id" not in payload:
        payload["manager_employee_id"] = create_employee(client, headers)["id"]
    response = client.post("/api/projects", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def create_resource_type(client: TestClient, headers: dict[str, str], **overrides):
    payload = {
        "code": unique("RT").upper(),
        "name": "测试资源类型",
        "category": "DEVELOPMENT",
        "description": "gate3",
    }
    payload.update(overrides)
    response = client.post("/api/resource-types", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def create_resource(client: TestClient, headers: dict[str, str], **overrides):
    if "resource_type_id" not in overrides:
        overrides["resource_type_id"] = create_resource_type(client, headers)["id"]
    payload = {
        "resource_name": unique("资源"),
        "provider": "Cursor",
        "account_identifier": f"{unique('acc')}@example.com",
        "plan_name": "Pro",
        "status": "ACTIVE",
    }
    payload.update(overrides)
    response = client.post("/api/resources", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def create_allocation(client: TestClient, headers: dict[str, str], resource_id: int, **payload):
    response = client.post(
        f"/api/resources/{resource_id}/allocations",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def create_expense_type(client: TestClient, headers: dict[str, str], **overrides):
    payload = {
        "code": unique("ET").upper(),
        "name": "测试费用类型",
        "category": "SOFTWARE",
        "description": "gate4",
    }
    payload.update(overrides)
    response = client.post("/api/expense-types", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def create_expense(client: TestClient, headers: dict[str, str], **overrides):
    if "expense_type_id" not in overrides:
        overrides["expense_type_id"] = create_expense_type(client, headers)["id"]
    distributions = overrides.pop("distributions", None)
    if distributions is None:
        raise AssertionError("create_expense requires distributions")
    payload = {
        "billing_mode": "MANUAL",
        "source": "MANUAL",
        "expense_date": "2026-09-01",
        "amount": "100.00",
        "currency": "CNY",
        "description": "gate4 expense",
        "distributions": distributions,
    }
    payload.update(overrides)
    response = client.post("/api/expenses", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def create_recurring_rule(client: TestClient, headers: dict[str, str], **overrides):
    if "expense_type_id" not in overrides:
        overrides["expense_type_id"] = create_expense_type(client, headers)["id"]
    distributions = overrides.pop("distributions", None)
    if distributions is None:
        raise AssertionError("create_recurring_rule requires distributions")
    payload = {
        "name": unique("周期规则"),
        "frequency": "MONTHLY",
        "amount": "140.00",
        "currency": "CNY",
        "start_date": "2026-09-01",
        "next_run_date": "2026-09-01",
        "default_distribution_mode": "DIRECT",
        "distributions": distributions,
    }
    payload.update(overrides)
    response = client.post("/api/recurring-expense-rules", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()
