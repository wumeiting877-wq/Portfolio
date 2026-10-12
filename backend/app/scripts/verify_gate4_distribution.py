"""Live Gate 4 distribution verification against the running backend."""

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


def login() -> str:
    status, body = request("POST", "/api/auth/login", payload={"username": "admin", "password": PASSWORD})
    if status != 200:
        raise RuntimeError(f"login failed: {status} {body}")
    return body["access_token"]


def ensure_type(admin: str) -> dict:
    status, body = request(
        "POST",
        "/api/expense-types",
        token=admin,
        payload={"code": "GATE4-DIST", "name": "分摊验证", "category": "SOFTWARE"},
    )
    if status == 400:
        types = request("GET", "/api/expense-types?include_inactive=true", token=admin)[1]
        return next(item for item in types if item["code"] == "GATE4-DIST")
    if status != 200:
        raise RuntimeError(f"create type failed: {status} {body}")
    return body


def main() -> None:
    admin = login()
    me = request("GET", "/api/auth/me", token=admin)[1]
    type_id = ensure_type(admin)["id"]
    listed = request("GET", "/api/projects", token=admin)[1]
    project_a = next(item for item in listed["items"] if item["project_code"] == "GATE2-A")
    project_b = next(item for item in listed["items"] if item["project_code"] == "GATE2-B")
    equal_status, equal_body = request(
        "POST",
        "/api/expenses",
        token=admin,
        payload={
            "expense_type_id": type_id,
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-10",
            "amount": "1000.00",
            "currency": "CNY",
            "description": "GATE4-EQUAL-1000",
            "distributions": [
                {"employee_id": me["employee_id"], "allocation_method": "EQUAL"},
                {"project_id": project_a["id"], "allocation_method": "EQUAL"},
                {"project_id": project_b["id"], "allocation_method": "EQUAL"},
            ],
        },
    )
    mismatch_status, mismatch_body = request(
        "POST",
        "/api/expenses",
        token=admin,
        payload={
            "expense_type_id": type_id,
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-10",
            "amount": "1000.00",
            "currency": "CNY",
            "description": "GATE4-MISMATCH",
            "distributions": [
                {"project_id": project_a["id"], "allocation_method": "MANUAL", "allocated_amount": "900.00"}
            ],
        },
    )
    ratio_status, ratio_body = request(
        "POST",
        "/api/expenses",
        token=admin,
        payload={
            "expense_type_id": type_id,
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-10",
            "amount": "1000.00",
            "currency": "CNY",
            "description": "GATE4-RATIO-60-40",
            "distributions": [
                {"project_id": project_a["id"], "allocation_method": "RATIO", "allocation_ratio": "0.6"},
                {"project_id": project_b["id"], "allocation_method": "RATIO", "allocation_ratio": "0.4"},
            ],
        },
    )
    result = {
        "equal": {
            "status": equal_status,
            "amounts": [item.get("allocated_amount") for item in (equal_body or {}).get("distributions", [])]
            if equal_status == 200
            else equal_body,
        },
        "mismatch": {"status": mismatch_status, "detail": (mismatch_body or {}).get("detail") if isinstance(mismatch_body, dict) else mismatch_body},
        "ratio": {
            "status": ratio_status,
            "amounts": [item.get("allocated_amount") for item in (ratio_body or {}).get("distributions", [])]
            if ratio_status == 200
            else ratio_body,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
