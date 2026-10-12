"""Live Gate 2 scope verification against the running backend."""

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


def summarize_list(body: dict) -> list[dict]:
    return [
        {
            "id": item["id"],
            "project_code": item["project_code"],
            "name": item["name"],
            "manager_employee_id": item["manager_employee_id"],
            "manager_name": item["manager_name"],
            "member_count": item["member_count"],
            "status": item["status"],
        }
        for item in body.get("items", [])
    ]


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

    other_manager_status, other_manager = request(
        "POST",
        "/api/employees",
        token=admin,
        payload={"employee_no": "PM002", "name": "另一负责人", "department": "项目部", "position": "项目负责人"},
    )
    if other_manager_status == 400:
        status, employees = request("GET", "/api/employees", token=admin, payload=None)
        other_manager = next(item for item in employees if item["employee_no"] == "PM002")
    elif other_manager_status != 200:
        raise RuntimeError(f"create other manager failed: {other_manager_status} {other_manager}")

    project_a_status, project_a = request(
        "POST",
        "/api/projects",
        token=admin,
        payload={
            "project_code": "GATE2-A",
            "name": "Project A",
            "manager_employee_id": profiles["pm"]["employee_id"],
            "status": "ACTIVE",
            "description": "pm 负责，member 参与",
        },
    )
    if project_a_status == 400:
        listed = request("GET", "/api/projects", token=admin, payload=None)[1]
        project_a = next(item for item in listed["items"] if item["project_code"] == "GATE2-A")
    elif project_a_status != 200:
        raise RuntimeError(f"create project A failed: {project_a_status} {project_a}")

    project_b_status, project_b = request(
        "POST",
        "/api/projects",
        token=admin,
        payload={
            "project_code": "GATE2-B",
            "name": "Project B",
            "manager_employee_id": other_manager["id"],
            "status": "ACTIVE",
            "description": "另一负责人负责，member 未加入",
        },
    )
    if project_b_status == 400:
        listed = request("GET", "/api/projects", token=admin, payload=None)[1]
        project_b = next(item for item in listed["items"] if item["project_code"] == "GATE2-B")
    elif project_b_status != 200:
        raise RuntimeError(f"create project B failed: {project_b_status} {project_b}")

    add_status, add_body = request(
        "POST",
        f"/api/projects/{project_a['id']}/members",
        token=admin,
        payload={"employee_id": profiles["member"]["employee_id"], "member_role": "MEMBER"},
    )
    if add_status not in (200, 400):
        raise RuntimeError(f"add member failed: {add_status} {add_body}")

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
        "project_a": {"id": project_a["id"], "code": project_a["project_code"], "manager_employee_id": project_a["manager_employee_id"]},
        "project_b": {"id": project_b["id"], "code": project_b["project_code"], "manager_employee_id": project_b["manager_employee_id"]},
        "calls": {},
    }

    for role_name, token in (("admin", admin), ("boss", boss), ("pm", pm), ("member", member)):
        list_status, list_body = request("GET", "/api/projects", token=token)
        detail_a = request("GET", f"/api/projects/{project_a['id']}", token=token)
        detail_b = request("GET", f"/api/projects/{project_b['id']}", token=token)
        write = request(
            "PUT",
            f"/api/projects/{project_a['id']}",
            token=token,
            payload={"description": f"{role_name} write probe"},
        )
        result["calls"][role_name] = {
            "GET /api/projects": {
                "status": list_status,
                "ids": [item["id"] for item in (list_body or {}).get("items", [])],
                "codes": [item["project_code"] for item in (list_body or {}).get("items", [])],
                "items": summarize_list(list_body or {}),
            },
            "GET /api/projects/A": {"status": detail_a[0], "code": (detail_a[1] or {}).get("project_code") if isinstance(detail_a[1], dict) else detail_a[1]},
            "GET /api/projects/B": {"status": detail_b[0], "code": (detail_b[1] or {}).get("project_code") if isinstance(detail_b[1], dict) else detail_b[1]},
            "PUT /api/projects/A": {"status": write[0], "detail": write[1].get("detail") if isinstance(write[1], dict) else write[1]},
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
