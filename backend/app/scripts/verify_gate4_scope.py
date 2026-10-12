"""Live Gate 4 expense scope verification against the running backend."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8010"
PASSWORD = "change_me"


def request(method: str, path: str, token: str | None = None, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def login(username: str) -> str:
    status, body = request("POST", "/api/auth/login", payload={"username": username, "password": PASSWORD})
    if status != 200:
        raise RuntimeError(f"login failed for {username}: {status} {body}")
    return body["access_token"]


def me(token: str) -> dict:
    status, body = request("GET", "/api/auth/me", token=token)
    if status != 200:
        raise RuntimeError(f"/me failed: {status} {body}")
    return body


def ensure_employee(admin: str, employee_no: str, name: str) -> dict:
    status, body = request(
        "POST",
        "/api/employees",
        token=admin,
        payload={"employee_no": employee_no, "name": name, "department": "项目部", "position": "成员"},
    )
    if status == 400:
        employees = request("GET", "/api/employees", token=admin)[1]
        return next(item for item in employees if item["employee_no"] == employee_no)
    if status != 200:
        raise RuntimeError(f"create employee {employee_no} failed: {status} {body}")
    return body


def ensure_project(admin: str, code: str, name: str, manager_id: int) -> dict:
    status, body = request(
        "POST",
        "/api/projects",
        token=admin,
        payload={"project_code": code, "name": name, "manager_employee_id": manager_id, "status": "ACTIVE"},
    )
    if status == 400:
        listed = request("GET", "/api/projects", token=admin)[1]
        return next(item for item in listed["items"] if item["project_code"] == code)
    if status != 200:
        raise RuntimeError(f"create project {code} failed: {status} {body}")
    return body


def ensure_expense_type(admin: str, code: str, name: str, category: str) -> dict:
    status, body = request(
        "POST",
        "/api/expense-types",
        token=admin,
        payload={"code": code, "name": name, "category": category},
    )
    if status == 400:
        types = request("GET", "/api/expense-types", token=admin, payload=None)[1]
        include = request("GET", "/api/expense-types?include_inactive=true", token=admin)[1]
        return next(item for item in include if item["code"] == code)
    if status != 200:
        raise RuntimeError(f"create expense type {code} failed: {status} {body}")
    return body


def find_expense(admin: str, description: str) -> dict | None:
    listed = request("GET", "/api/expenses", token=admin, payload=None)[1]
    return next((item for item in listed["items"] if item.get("description") == description), None)


def create_expense(admin: str, payload: dict) -> dict:
    existing = find_expense(admin, payload["description"])
    if existing:
        return existing
    status, body = request("POST", "/api/expenses", token=admin, payload=payload)
    if status != 200:
        raise RuntimeError(f"create expense {payload['description']} failed: {status} {body}")
    return body


def main() -> None:
    admin = login("admin")
    boss = login("boss")
    pm = login("pm")
    member = login("member")
    profiles = {
        "admin": me(admin),
        "boss": me(boss),
        "pm": me(pm),
        "member": me(member),
    }
    other_manager = ensure_employee(admin, "PM002", "另一负责人")
    other_member = ensure_employee(admin, "MB002", "同项目另一成员")
    project_a = ensure_project(admin, "GATE2-A", "Project A", profiles["pm"]["employee_id"])
    project_b = ensure_project(admin, "GATE2-B", "Project B", other_manager["id"])
    request(
        "POST",
        f"/api/projects/{project_a['id']}/members",
        token=admin,
        payload={"employee_id": profiles["member"]["employee_id"], "member_role": "MEMBER"},
    )
    request(
        "POST",
        f"/api/projects/{project_a['id']}/members",
        token=admin,
        payload={"employee_id": other_member["id"], "member_role": "MEMBER"},
    )
    expense_type = ensure_expense_type(admin, "GATE4-SOFTWARE", "Gate4 软件", "SOFTWARE")
    expense_a = create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-01",
            "amount": "100.00",
            "currency": "CNY",
            "description": "GATE4-A",
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
    expense_b = create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "ONE_TIME",
            "expense_date": "2026-09-02",
            "amount": "200.00",
            "currency": "CNY",
            "description": "GATE4-B",
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
    expense_d = create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-03",
            "amount": "300.00",
            "currency": "CNY",
            "description": "GATE4-D",
            "distributions": [
                {
                    "project_id": project_a["id"],
                    "employee_id": other_member["id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "300.00",
                }
            ],
        },
    )
    expense_e = create_expense(
        admin,
        {
            "expense_type_id": expense_type["id"],
            "billing_mode": "RECURRING",
            "expense_date": "2026-09-04",
            "amount": "1000.00",
            "currency": "CNY",
            "description": "GATE4-E-SHARED",
            "distributions": [
                {"project_id": project_a["id"], "allocation_method": "RATIO", "allocation_ratio": "0.6"},
                {"project_id": project_b["id"], "allocation_method": "RATIO", "allocation_ratio": "0.4"},
            ],
        },
    )
    result = {
        "profiles": {
            name: {
                "username": profile["username"],
                "role": profile["role"],
                "scope": profile["scope"],
                "employee_id": profile["employee_id"],
                "employee_name": profile.get("employee_name"),
            }
            for name, profile in profiles.items()
        },
        "expenses": {
            "A": {"id": expense_a["id"], "description": expense_a["description"], "amount": expense_a["amount"]},
            "B": {"id": expense_b["id"], "description": expense_b["description"], "amount": expense_b["amount"]},
            "D": {"id": expense_d["id"], "description": expense_d["description"], "amount": expense_d["amount"]},
            "E": {"id": expense_e["id"], "description": expense_e["description"], "amount": expense_e["amount"]},
        },
        "calls": {},
    }
    for role_name, token in (("admin", admin), ("boss", boss), ("pm", pm), ("member", member)):
        list_status, list_body = request("GET", "/api/expenses", token=token)
        items = (list_body or {}).get("items", [])
        result["calls"][role_name] = {
            "GET /api/expenses": {
                "status": list_status,
                "ids": [item["id"] for item in items],
                "descriptions": [item.get("description") for item in items],
                "amounts": [item.get("amount") for item in items],
            },
            "GET A": request("GET", f"/api/expenses/{expense_a['id']}", token=token),
            "GET B": request("GET", f"/api/expenses/{expense_b['id']}", token=token),
            "GET D": request("GET", f"/api/expenses/{expense_d['id']}", token=token),
            "GET E": request("GET", f"/api/expenses/{expense_e['id']}", token=token),
            "PUT A": request(
                "PUT",
                f"/api/expenses/{expense_a['id']}",
                token=token,
                payload={"description": f"{role_name} write probe"},
            ),
        }
        for key in ("GET A", "GET B", "GET D", "GET E"):
            status, body = result["calls"][role_name][key]
            summary = {"status": status}
            if status == 200 and isinstance(body, dict):
                summary["amount"] = body.get("amount")
                summary["visible_allocated_amount"] = body.get("visible_allocated_amount")
                summary["original_amount_visible"] = body.get("original_amount_visible")
                summary["distribution_project_ids"] = [item.get("project_id") for item in body.get("distributions", [])]
                summary["distribution_employee_ids"] = [
                    item.get("employee_id") for item in body.get("distributions", [])
                ]
            elif isinstance(body, dict):
                summary["detail"] = body.get("detail")
            result["calls"][role_name][key] = summary
        put_status, put_body = result["calls"][role_name]["PUT A"]
        result["calls"][role_name]["PUT A"] = {
            "status": put_status,
            "detail": put_body.get("detail") if isinstance(put_body, dict) else put_body,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
