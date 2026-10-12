"""Live Gate 4 recurring generator idempotency verification."""

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


def main() -> None:
    status, body = request("POST", "/api/auth/login", payload={"username": "admin", "password": PASSWORD})
    if status != 200:
        raise RuntimeError(f"login failed: {status} {body}")
    admin = body["access_token"]
    type_status, expense_type = request(
        "POST",
        "/api/expense-types",
        token=admin,
        payload={"code": "GATE4-RECURRING", "name": "周期验证", "category": "SUBSCRIPTION"},
    )
    if type_status == 400:
        types = request("GET", "/api/expense-types?include_inactive=true", token=admin)[1]
        expense_type = next(item for item in types if item["code"] == "GATE4-RECURRING")
    elif type_status != 200:
        raise RuntimeError(f"create type failed: {type_status} {expense_type}")
    listed = request("GET", "/api/projects", token=admin)[1]
    project_a = next(item for item in listed["items"] if item["project_code"] == "GATE2-A")
    rules = request("GET", "/api/recurring-expense-rules?include_inactive=true", token=admin)[1]
    rule = next((item for item in rules if item["name"] == "GATE4-CURSOR-MONTHLY"), None)
    if rule is None:
        rule_status, rule = request(
            "POST",
            "/api/recurring-expense-rules",
            token=admin,
            payload={
                "name": "GATE4-CURSOR-MONTHLY",
                "expense_type_id": expense_type["id"],
                "frequency": "MONTHLY",
                "amount": "140.00",
                "currency": "CNY",
                "start_date": "2026-09-01",
                "next_run_date": "2026-09-01",
                "default_distribution_mode": "DIRECT",
                "distributions": [
                    {
                        "project_id": project_a["id"],
                        "allocation_method": "DIRECT",
                        "allocated_amount": "140.00",
                    }
                ],
            },
        )
        if rule_status != 200:
            raise RuntimeError(f"create rule failed: {rule_status} {rule}")
    first = request("POST", "/api/expenses/recurring/generate", token=admin)
    second = request("POST", "/api/expenses/recurring/generate", token=admin)
    listed_expenses = request(
        "GET",
        "/api/expenses?source=RECURRING_RULE",
        token=admin,
    )[1]
    recurring_items = [
        item
        for item in (listed_expenses or {}).get("items", [])
        if item.get("recurring_rule_id") == rule["id"]
    ]
    periods = [item.get("billing_period_start") for item in recurring_items]
    result = {
        "rule_id": rule["id"],
        "first": first,
        "second": second,
        "generated_expense_ids": [item["id"] for item in recurring_items],
        "billing_periods": periods,
        "duplicate_periods": [period for period in set(periods) if periods.count(period) > 1],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
