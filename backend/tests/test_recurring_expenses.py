from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from tests.helpers import (
    admin_headers,
    create_expense_type,
    create_project,
    create_recurring_rule,
)


def _direct(project_id: int, amount: str | None = None):
    item = {"project_id": project_id, "allocation_method": "DIRECT"}
    if amount is not None:
        item["allocated_amount"] = amount
    return [item]


def test_monthly_rule_creates_expense(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    rule = create_recurring_rule(
        client,
        headers,
        frequency="MONTHLY",
        amount="140.00",
        next_run_date="2026-09-01",
        distributions=_direct(project["id"], "140.00"),
    )
    generated = client.post("/api/expenses/recurring/generate", headers=headers)
    assert generated.status_code == 200, generated.text
    body = generated.json()
    assert body["generated_count"] >= 1
    expense = client.get(f"/api/expenses/{body['generated_ids'][0]}", headers=headers)
    assert expense.status_code == 200
    data = expense.json()
    assert data["source"] == "RECURRING_RULE"
    assert data["billing_mode"] == "RECURRING"
    assert Decimal(data["amount"]) == Decimal("140.00")
    assert data["recurring_rule_id"] == rule["id"]
    assert len(data["distributions"]) == 1
    refreshed = client.get(f"/api/recurring-expense-rules/{rule['id']}", headers=headers).json()
    assert refreshed["next_run_date"] > "2026-09-01"


def test_quarterly_and_yearly_rules_create(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    quarterly = create_recurring_rule(
        client,
        headers,
        frequency="QUARTERLY",
        amount="300.00",
        next_run_date="2026-01-01",
        distributions=_direct(project["id"], "300.00"),
    )
    yearly = create_recurring_rule(
        client,
        headers,
        frequency="YEARLY",
        amount="1200.00",
        next_run_date="2026-01-01",
        distributions=_direct(project["id"], "1200.00"),
    )
    generated = client.post("/api/expenses/recurring/generate", headers=headers)
    assert generated.status_code == 200
    ids = generated.json()["generated_ids"]
    assert ids
    sourced = [client.get(f"/api/expenses/{item_id}", headers=headers).json() for item_id in ids]
    assert any(item["recurring_rule_id"] == quarterly["id"] for item in sourced)
    assert any(item["recurring_rule_id"] == yearly["id"] for item in sourced)


def test_generate_is_idempotent(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    create_recurring_rule(
        client,
        headers,
        frequency="MONTHLY",
        next_run_date=date.today().isoformat(),
        distributions=_direct(project["id"], "140.00"),
    )
    first = client.post("/api/expenses/recurring/generate", headers=headers)
    second = client.post("/api/expenses/recurring/generate", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    first_ids = first.json()["generated_ids"]
    assert first.json()["generated_count"] >= 1
    listed = client.get("/api/expenses", params={"source": "RECURRING_RULE"}, headers=headers)
    recurring_ids = [item["id"] for item in listed.json()["items"] if item["id"] in first_ids]
    second_listed = client.get("/api/expenses", params={"source": "RECURRING_RULE"}, headers=headers)
    after = [item["id"] for item in second_listed.json()["items"]]
    for expense_id in recurring_ids:
        assert after.count(expense_id) == 1
    assert second.json()["generated_count"] == 0 or set(second.json()["generated_ids"]).isdisjoint(set(first_ids))


def test_disabled_rule_does_not_generate(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    rule = create_recurring_rule(
        client,
        headers,
        next_run_date="2026-09-01",
        distributions=_direct(project["id"], "140.00"),
    )
    client.post(f"/api/recurring-expense-rules/{rule['id']}/disable", headers=headers)
    generated = client.post("/api/expenses/recurring/generate", headers=headers)
    assert rule["id"] not in {
        client.get(f"/api/expenses/{item_id}", headers=headers).json().get("recurring_rule_id")
        for item_id in generated.json()["generated_ids"]
    }


def test_past_end_date_does_not_generate(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    rule = create_recurring_rule(
        client,
        headers,
        start_date="2026-01-01",
        end_date="2026-02-01",
        next_run_date="2026-03-01",
        distributions=_direct(project["id"], "140.00"),
    )
    generated = client.post("/api/expenses/recurring/generate", headers=headers)
    generated_rule_ids = []
    for item_id in generated.json()["generated_ids"]:
        generated_rule_ids.append(
            client.get(f"/api/expenses/{item_id}", headers=headers).json()["recurring_rule_id"]
        )
    assert rule["id"] not in generated_rule_ids


def test_non_admin_cannot_generate(client: TestClient) -> None:
    from tests.helpers import auth_headers_for, create_employee, create_user_account

    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="BOSS", employee_id=employee["id"]
    )
    boss = auth_headers_for(client, username, password)
    assert client.post("/api/expenses/recurring/generate", headers=boss).status_code == 403
