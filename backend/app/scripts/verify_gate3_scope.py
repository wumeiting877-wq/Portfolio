"""Live Gate 3 resource scope verification against the running backend."""

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


def ensure(status_ok, body, message: str):
    status, payload = status_ok, body
    if status not in (200, 400):
        raise RuntimeError(f"{message}: {status} {payload}")
    return status, payload


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
        _, employees = request("GET", "/api/employees", token=admin)
        other_manager = next(item for item in employees if item["employee_no"] == "PM002")
    elif other_manager_status != 200:
        raise RuntimeError(f"create other manager failed: {other_manager_status} {other_manager}")

    other_member_status, other_member = request(
        "POST",
        "/api/employees",
        token=admin,
        payload={"employee_no": "MB002", "name": "同项目另一成员", "department": "项目部", "position": "成员"},
    )
    if other_member_status == 400:
        _, employees = request("GET", "/api/employees", token=admin)
        other_member = next(item for item in employees if item["employee_no"] == "MB002")
    elif other_member_status != 200:
        raise RuntimeError(f"create other member failed: {other_member_status} {other_member}")

    project_a_status, project_a = request(
        "POST",
        "/api/projects",
        token=admin,
        payload={
            "project_code": "GATE2-A",
            "name": "Project A",
            "manager_employee_id": profiles["pm"]["employee_id"],
            "status": "ACTIVE",
        },
    )
    if project_a_status == 400:
        listed = request("GET", "/api/projects", token=admin)[1]
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
        },
    )
    if project_b_status == 400:
        listed = request("GET", "/api/projects", token=admin)[1]
        project_b = next(item for item in listed["items"] if item["project_code"] == "GATE2-B")
    elif project_b_status != 200:
        raise RuntimeError(f"create project B failed: {project_b_status} {project_b}")

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

    def ensure_type(code: str, name: str, category: str) -> dict:
        status, body = request(
            "POST",
            "/api/resource-types",
            token=admin,
            payload={"code": code, "name": name, "category": category},
        )
        if status == 400:
            types = request("GET", "/api/resource-types", token=admin, payload=None)[1]
            return next(item for item in types if item["code"] == code)
        if status != 200:
            raise RuntimeError(f"create type {code} failed: {status} {body}")
        return body

    cursor_type = ensure_type("CURSOR", "Cursor", "DEVELOPMENT")
    chatgpt_type = ensure_type("CHATGPT", "ChatGPT", "AI")
    ecs_type = ensure_type("ALIYUN_ECS", "阿里云 ECS", "CLOUD_SERVER")

    def ensure_resource(name: str, type_id: int) -> dict:
        listed = request("GET", "/api/resources", token=admin)[1]
        existing = next((item for item in listed["items"] if item["resource_name"] == name), None)
        if existing:
            return existing
        status, body = request(
            "POST",
            "/api/resources",
            token=admin,
            payload={
                "resource_type_id": type_id,
                "resource_name": name,
                "provider": name.split("-")[0],
                "account_identifier": f"{name.lower()}@example.com",
                "plan_name": "Team",
                "status": "ACTIVE",
            },
        )
        if status != 200:
            raise RuntimeError(f"create resource {name} failed: {status} {body}")
        return body

    resource_a = ensure_resource("GATE3-A", cursor_type["id"])
    resource_b = ensure_resource("GATE3-B", chatgpt_type["id"])
    resource_c = ensure_resource("GATE3-C", ecs_type["id"])
    resource_d = ensure_resource("GATE3-D", cursor_type["id"])

    def ensure_allocation(resource_id: int, project_id=None, employee_id=None):
        request(
            "POST",
            f"/api/resources/{resource_id}/allocations",
            token=admin,
            payload={"project_id": project_id, "employee_id": employee_id},
        )

    ensure_allocation(resource_a["id"], project_a["id"], profiles["member"]["employee_id"])
    ensure_allocation(resource_b["id"], project_b["id"], other_manager["id"])
    ensure_allocation(resource_d["id"], project_a["id"], other_member["id"])

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
        "resources": {
            "A": {"id": resource_a["id"], "name": resource_a["resource_name"]},
            "B": {"id": resource_b["id"], "name": resource_b["resource_name"]},
            "C": {"id": resource_c["id"], "name": resource_c["resource_name"]},
            "D": {"id": resource_d["id"], "name": resource_d["resource_name"]},
        },
        "calls": {},
    }

    for role_name, token in (("admin", admin), ("boss", boss), ("pm", pm), ("member", member)):
        list_status, list_body = request("GET", "/api/resources", token=token)
        items = (list_body or {}).get("items", [])
        result["calls"][role_name] = {
            "GET /api/resources": {
                "status": list_status,
                "ids": [item["id"] for item in items],
                "names": [item["resource_name"] for item in items],
            },
            "GET A": {
                "status": request("GET", f"/api/resources/{resource_a['id']}", token=token)[0],
            },
            "GET B": {
                "status": request("GET", f"/api/resources/{resource_b['id']}", token=token)[0],
            },
            "GET C": {
                "status": request("GET", f"/api/resources/{resource_c['id']}", token=token)[0],
            },
            "GET D": {
                "status": request("GET", f"/api/resources/{resource_d['id']}", token=token)[0],
            },
            "GET A allocations": request("GET", f"/api/resources/{resource_a['id']}/allocations", token=token),
            "PUT A": request(
                "PUT",
                f"/api/resources/{resource_a['id']}",
                token=token,
                payload={"remark": f"{role_name} write probe"},
            ),
        }
        result["calls"][role_name]["PUT A"] = {
            "status": result["calls"][role_name]["PUT A"][0],
            "detail": result["calls"][role_name]["PUT A"][1].get("detail")
            if isinstance(result["calls"][role_name]["PUT A"][1], dict)
            else result["calls"][role_name]["PUT A"][1],
        }
        alloc_status, alloc_body = result["calls"][role_name]["GET A allocations"]
        result["calls"][role_name]["GET A allocations"] = {
            "status": alloc_status,
            "employee_ids": [item.get("employee_id") for item in alloc_body]
            if isinstance(alloc_body, list)
            else alloc_body,
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
