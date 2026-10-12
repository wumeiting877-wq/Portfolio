"""Live Gate 5 statistics scope verification against the running backend."""

from __future__ import annotations

import json
from datetime import date, timedelta
from urllib import error, request as urllib_request

BASE = "http://127.0.0.1:8010"
PASSWORD = "change_me"
DATE = "2026-09-22"


def http(method: str, path: str, token: str | None = None, payload: dict | None = None, query: str = ""):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib_request.Request(BASE + path + query, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def login(username: str) -> str:
    status, body = http("POST", "/api/auth/login", payload={"username": username, "password": PASSWORD})
    if status != 200:
        raise RuntimeError(f"login failed for {username}: {status} {body}")
    return body["access_token"]


def me(token: str) -> dict:
    status, body = http("GET", "/api/auth/me", token=token)
    if status != 200:
        raise RuntimeError(f"/me failed: {status} {body}")
    return body


def ensure_employee(admin: str, employee_no: str, name: str) -> dict:
    status, body = http(
        "POST",
        "/api/employees",
        token=admin,
        payload={"employee_no": employee_no, "name": name, "department": "项目部", "position": "成员"},
    )
    if status == 400:
        employees = http("GET", "/api/employees", token=admin)[1]
        return next(item for item in employees if item["employee_no"] == employee_no)
    if status != 200:
        raise RuntimeError(f"create employee {employee_no} failed: {status} {body}")
    return body


def ensure_project(admin: str, code: str, name: str, manager_id: int) -> dict:
    status, body = http(
        "POST",
        "/api/projects",
        token=admin,
        payload={"project_code": code, "name": name, "manager_employee_id": manager_id, "status": "ACTIVE"},
    )
    if status == 400:
        listed = http("GET", "/api/projects", token=admin)[1]
        return next(item for item in listed["items"] if item["project_code"] == code)
    if status != 200:
        raise RuntimeError(f"create project {code} failed: {status} {body}")
    return body


def ensure_expense_type(admin: str, code: str, name: str, category: str) -> dict:
    status, body = http(
        "POST",
        "/api/expense-types",
        token=admin,
        payload={"code": code, "name": name, "category": category},
    )
    if status == 400:
        include = http("GET", "/api/expense-types?include_inactive=true", token=admin)[1]
        return next(item for item in include if item["code"] == code)
    if status != 200:
        raise RuntimeError(f"create expense type {code} failed: {status} {body}")
    return body


def find_expense(admin: str, description: str) -> dict | None:
    listed = http("GET", "/api/expenses?page_size=100", token=admin)[1]
    return next((item for item in listed["items"] if item.get("description") == description), None)


def create_expense(admin: str, payload: dict) -> dict:
    existing = find_expense(admin, payload["description"])
    if existing:
        return existing
    status, body = http("POST", "/api/expenses", token=admin, payload=payload)
    if status != 200:
        raise RuntimeError(f"create expense {payload['description']} failed: {status} {body}")
    return body


def ensure_resource_type(admin: str, code: str, name: str) -> dict:
    status, body = http(
        "POST",
        "/api/resource-types",
        token=admin,
        payload={"code": code, "name": name, "category": "AI"},
    )
    if status == 400:
        types = http("GET", "/api/resource-types?include_inactive=true", token=admin)[1]
        return next(item for item in types if item["code"] == code)
    if status != 200:
        raise RuntimeError(f"create resource type failed: {status} {body}")
    return body


def find_resource(admin: str, name: str) -> dict | None:
    listed = http("GET", "/api/resources?page_size=100", token=admin)[1]
    return next((item for item in listed["items"] if item.get("resource_name") == name), None)


def create_resource(admin: str, payload: dict) -> dict:
    existing = find_resource(admin, payload["resource_name"])
    if existing:
        return existing
    status, body = http("POST", "/api/resources", token=admin, payload=payload)
    if status != 200:
        raise RuntimeError(f"create resource {payload['resource_name']} failed: {status} {body}")
    return body


def stats(token: str, path: str, extra: str = "") -> tuple[int, dict | None]:
    query = f"?date_from={DATE}&date_to={DATE}{extra}"
    return http("GET", f"/api/statistics/{path}", token=token, query=query)


def main() -> None:
    admin = login("admin")
    boss = login("boss")
    pm = login("pm")
    member = login("member")
    profiles = {name: me(token) for name, token in (("admin", admin), ("boss", boss), ("pm", pm), ("member", member))}
    other_manager = ensure_employee(admin, "PM002", "另一负责人")
    other_member = ensure_employee(admin, "MB002", "同项目另一成员")
    project_a = ensure_project(admin, "GATE2-A", "Project A", profiles["pm"]["employee_id"])
    project_b = ensure_project(admin, "GATE2-B", "Project B", other_manager["id"])
    http(
        "POST",
        f"/api/projects/{project_a['id']}/members",
        token=admin,
        payload={"employee_id": profiles["member"]["employee_id"], "member_role": "MEMBER"},
    )
    expense_type = ensure_expense_type(admin, "GATE5-SOFTWARE", "Gate5 软件", "SOFTWARE")
    rt = ensure_resource_type(admin, "GATE5-AI", "Gate5 AI")
    bound = create_resource(
        admin,
        {"resource_type_id": rt["id"], "resource_name": "GATE5-BOUND", "status": "ACTIVE"},
    )
    idle = create_resource(
        admin,
        {"resource_type_id": rt["id"], "resource_name": "GATE5-IDLE", "status": "IDLE"},
    )
    unassigned = create_resource(
        admin,
        {"resource_type_id": rt["id"], "resource_name": "GATE5-UNASSIGNED", "status": "ACTIVE"},
    )
    expiring = create_resource(
        admin,
        {
            "resource_type_id": rt["id"],
            "resource_name": "GATE5-EXPIRING",
            "status": "ACTIVE",
            "expires_at": (date.today() + timedelta(days=10)).isoformat(),
        },
    )
    http(
        "POST",
        f"/api/resources/{bound['id']}/allocations",
        token=admin,
        payload={"project_id": project_a["id"], "employee_id": profiles["member"]["employee_id"]},
    )
    create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "resource_account_id": bound["id"],
            "billing_mode": "MANUAL",
            "expense_date": DATE,
            "amount": "100.00",
            "currency": "CNY",
            "description": "GATE5-A-CNY",
            "distributions": [
                {
                    "project_id": project_a["id"],
                    "employee_id": profiles["member"]["employee_id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "100.00",
                }
            ],
        },
    )
    create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": DATE,
            "amount": "100.00",
            "currency": "USD",
            "description": "GATE5-A-USD",
            "distributions": [
                {"project_id": project_a["id"], "allocation_method": "DIRECT", "allocated_amount": "100.00"}
            ],
        },
    )
    create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "ONE_TIME",
            "expense_date": DATE,
            "amount": "200.00",
            "currency": "CNY",
            "description": "GATE5-B-CNY",
            "distributions": [
                {
                    "project_id": project_b["id"],
                    "employee_id": other_manager["id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "200.00",
                }
            ],
        },
    )
    create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": DATE,
            "amount": "1000.00",
            "currency": "CNY",
            "description": "GATE5-SHARED",
            "distributions": [
                {"project_id": project_a["id"], "allocation_method": "RATIO", "allocation_ratio": "0.6"},
                {"project_id": project_b["id"], "allocation_method": "RATIO", "allocation_ratio": "0.4"},
            ],
        },
    )
    create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "USAGE",
            "expense_date": DATE,
            "amount": "30.00",
            "currency": "CNY",
            "description": "GATE5-MEMBER-DIRECT",
            "distributions": [
                {
                    "employee_id": profiles["member"]["employee_id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "30.00",
                }
            ],
        },
    )
    create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": DATE,
            "amount": "50.00",
            "currency": "CNY",
            "description": "GATE5-PUBLIC",
            "distributions": [
                {"project_id": project_a["id"], "allocation_method": "DIRECT", "allocated_amount": "50.00"}
            ],
        },
    )
    voided = create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": DATE,
            "amount": "999.00",
            "currency": "CNY",
            "description": "GATE5-VOIDED",
            "distributions": [
                {"project_id": project_a["id"], "allocation_method": "DIRECT", "allocated_amount": "999.00"}
            ],
        },
    )
    if voided.get("status") != "VOIDED":
        http("POST", f"/api/expenses/{voided['id']}/void", token=admin)

    result = {
        "date": DATE,
        "projects": {"A": {"id": project_a["id"], "code": project_a["project_code"]}, "B": {"id": project_b["id"], "code": project_b["project_code"]}},
        "resources": {
            "bound": bound["id"],
            "idle": idle["id"],
            "unassigned": unassigned["id"],
            "expiring": expiring["id"],
        },
        "calls": {},
    }
    tokens = (("admin", admin), ("boss", boss), ("pm", pm), ("member", member))
    for name, token in tokens:
        overview = stats(token, "overview")
        trend = stats(token, "expense-trend")
        projects = stats(token, "project-costs", "&limit=20")
        employees = stats(token, "employee-costs", "&limit=20")
        types = stats(token, "resource-type-costs", "&limit=20")
        billing = stats(token, "billing-costs")
        status = http("GET", "/api/statistics/resource-status", token=token)
        expiring_api = http("GET", "/api/statistics/expiring-resources?days=30", token=token)
        result["calls"][name] = {
            "overview": {"status": overview[0], "body": overview[1]},
            "trend": {"status": trend[0], "body": trend[1]},
            "project_costs": {"status": projects[0], "body": projects[1]},
            "employee_costs": {"status": employees[0], "body": employees[1]},
            "resource_type_costs": {"status": types[0], "body": types[1]},
            "billing_costs": {"status": billing[0], "body": billing[1]},
            "resource_status": {"status": status[0], "body": status[1]},
            "expiring": {"status": expiring_api[0], "body": expiring_api[1]},
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
