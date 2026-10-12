"""Live Gate 3 shared-resource verification against the running backend."""

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


def ensure_type(admin: str, code: str, name: str, category: str) -> dict:
    status, body = request(
        "POST",
        "/api/resource-types",
        token=admin,
        payload={"code": code, "name": name, "category": category},
    )
    if status == 400:
        types = request("GET", "/api/resource-types", token=admin)[1]
        return next(item for item in types if item["code"] == code)
    if status != 200:
        raise RuntimeError(f"create type {code} failed: {status} {body}")
    return body


def ensure_resource(admin: str, name: str, type_id: int, provider: str) -> dict:
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
            "provider": provider,
            "account_identifier": f"{name.lower()}@example.com",
            "plan_name": "Team",
            "status": "ACTIVE",
        },
    )
    if status != 200:
        raise RuntimeError(f"create resource {name} failed: {status} {body}")
    return body


def main() -> None:
    admin = login("admin")
    boss = login("boss")
    pm = login("pm")
    member = login("member")
    profiles = {name: me(token) for name, token in (("admin", admin), ("boss", boss), ("pm", pm), ("member", member))}

    _, employees = request("GET", "/api/employees", token=admin)
    other_manager = next(item for item in employees if item["employee_no"] == "PM002")
    other_member = next(item for item in employees if item["employee_no"] == "MB002")
    listed_projects = request("GET", "/api/projects", token=admin)[1]["items"]
    project_a = next(item for item in listed_projects if item["project_code"] == "GATE2-A")
    project_b = next(item for item in listed_projects if item["project_code"] == "GATE2-B")

    chatgpt_type = ensure_type(admin, "CHATGPT", "ChatGPT", "AI")
    github_type = ensure_type(admin, "GITHUB", "GitHub", "GIT")
    ecs_type = ensure_type(admin, "ALIYUN_ECS", "阿里云 ECS", "CLOUD_SERVER")

    project_level = ensure_resource(admin, "GATE3-ECS-新华", ecs_type["id"], "Aliyun")
    personal = ensure_resource(admin, "GATE3-GitHub-Seat", github_type["id"], "GitHub")
    shared = ensure_resource(admin, "GATE3-ChatGPT-Team-01", chatgpt_type["id"], "OpenAI")

    request(
        "POST",
        f"/api/resources/{project_level['id']}/allocations",
        token=admin,
        payload={"project_id": project_a["id"]},
    )
    request(
        "POST",
        f"/api/resources/{personal['id']}/allocations",
        token=admin,
        payload={"employee_id": profiles["member"]["employee_id"]},
    )
    for project_id, employee_id in (
        (project_a["id"], profiles["pm"]["employee_id"]),
        (project_a["id"], profiles["member"]["employee_id"]),
        (project_b["id"], other_manager["id"]),
    ):
        request(
            "POST",
            f"/api/resources/{shared['id']}/allocations",
            token=admin,
            payload={"project_id": project_id, "employee_id": employee_id},
        )

    detail = request("GET", f"/api/resources/{shared['id']}", token=admin)
    allocations = request("GET", f"/api/resources/{shared['id']}/allocations", token=admin)
    member_list = request("GET", "/api/resources", token=member)
    pm_list = request("GET", "/api/resources", token=pm)
    member_shared = request("GET", f"/api/resources/{shared['id']}/allocations", token=member)
    pm_shared = request("GET", f"/api/resources/{shared['id']}/allocations", token=pm)

    result = {
        "shared_resource": {
            "status": detail[0],
            "id": (detail[1] or {}).get("id"),
            "name": (detail[1] or {}).get("resource_name"),
            "is_shared": (detail[1] or {}).get("is_shared"),
            "active_user_count": (detail[1] or {}).get("active_user_count"),
            "active_project_count": (detail[1] or {}).get("active_project_count"),
        },
        "admin_allocations": allocations[1] if allocations[0] == 200 else allocations,
        "pm_visible_names": [item["resource_name"] for item in (pm_list[1] or {}).get("items", [])],
        "member_visible_names": [item["resource_name"] for item in (member_list[1] or {}).get("items", [])],
        "pm_shared_employee_ids": [item.get("employee_id") for item in pm_shared[1]]
        if pm_shared[0] == 200 and isinstance(pm_shared[1], list)
        else pm_shared,
        "member_shared_employee_ids": [item.get("employee_id") for item in member_shared[1]]
        if member_shared[0] == 200 and isinstance(member_shared[1], list)
        else member_shared,
        "project_level_id": project_level["id"],
        "personal_id": personal["id"],
        "shared_id": shared["id"],
        "other_member_id": other_member["id"],
        "other_manager_id": other_manager["id"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
