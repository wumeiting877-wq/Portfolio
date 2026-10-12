from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import Float, Numeric, inspect, text

from app.core.database import engine
from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.recurring_expense_rule import RecurringExpenseRule
from app.models.resource_account import ResourceAccount
from tests.helpers import admin_headers, create_expense, create_expense_type, create_project, create_resource


def _direct(project_id: int, amount: str = "100.00"):
    return [
        {
            "project_id": project_id,
            "allocation_method": "DIRECT",
            "allocated_amount": amount,
        }
    ]


def test_manual_subscription_expense_created(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    resource = create_resource(client, headers)
    expense_type = create_expense_type(client, headers, category="SUBSCRIPTION")
    created = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        resource_account_id=resource["id"],
        billing_mode="RECURRING",
        amount="140.0000",
        distributions=_direct(project["id"], "140.0000"),
    )
    assert created["billing_mode"] == "RECURRING"
    assert created["source"] == "MANUAL"
    assert Decimal(created["amount"]) == Decimal("140.0000")
    assert created["currency"] == "CNY"
    assert created["resource_account_id"] == resource["id"]
    assert created["status"] == "ACTIVE"


def test_one_time_expense_created(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    created = create_expense(
        client,
        headers,
        billing_mode="ONE_TIME",
        amount="2999.00",
        distributions=_direct(project["id"], "2999.00"),
    )
    assert created["billing_mode"] == "ONE_TIME"
    assert created["resource_account_id"] is None


def test_api_usage_expense_created(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    expense_type = create_expense_type(client, headers, category="API_USAGE")
    created = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        billing_mode="USAGE",
        amount="126.2800",
        usage_quantity="15.4",
        usage_unit="M tokens",
        unit_price="8.2",
        distributions=_direct(project["id"], "126.2800"),
    )
    assert created["billing_mode"] == "USAGE"
    assert Decimal(created["usage_quantity"]) == Decimal("15.400000")
    assert created["usage_unit"] == "M tokens"


def test_server_category_expense_created(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    expense_type = create_expense_type(client, headers, category="SERVER")
    created = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        billing_mode="RECURRING",
        amount="680.00",
        distributions=_direct(project["id"], "680.00"),
    )
    assert created["expense_type"]["category"] == "SERVER"


def test_currency_required_and_amount_is_decimal(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    expense_type = create_expense_type(client, headers)
    missing = client.post(
        "/api/expenses",
        json={
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-01",
            "amount": "10.00",
            "distributions": _direct(project["id"], "10.00"),
        },
        headers=headers,
    )
    assert missing.status_code == 422
    invalid = client.post(
        "/api/expenses",
        json={
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-01",
            "amount": "10.00",
            "currency": "EUR",
            "distributions": _direct(project["id"], "10.00"),
        },
        headers=headers,
    )
    assert invalid.status_code == 400


def test_voided_expense_excluded_from_active_list(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    created = create_expense(client, headers, distributions=_direct(project["id"]))
    voided = client.post(f"/api/expenses/{created['id']}/void", headers=headers)
    assert voided.status_code == 200
    assert voided.json()["status"] == "VOIDED"
    listed = client.get("/api/expenses", headers=headers)
    ids = {item["id"] for item in listed.json()["items"]}
    assert created["id"] not in ids
    history = client.get("/api/expenses", params={"status": "VOIDED"}, headers=headers)
    history_ids = {item["id"] for item in history.json()["items"]}
    assert created["id"] in history_ids
    detail = client.get(f"/api/expenses/{created['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == "VOIDED"


def test_expense_create_is_audited(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    created = create_expense(client, headers, distributions=_direct(project["id"]))
    with engine.connect() as connection:
        actions = {
            row[0]
            for row in connection.execute(
                text("SELECT action FROM audit_logs WHERE target_id = :target_id"),
                {"target_id": str(created["id"])},
            )
        }
    assert "EXPENSE_CREATE" in actions


def test_amount_columns_are_numeric_not_float() -> None:
    for model in (ExpenseRecord, ExpenseDistribution, RecurringExpenseRule):
        mapper = inspect(model)
        for column in mapper.columns:
            if column.name in {"amount", "allocated_amount", "unit_price", "usage_quantity", "allocation_ratio"}:
                assert isinstance(column.type, Numeric)
                assert not isinstance(column.type, Float)
    account_columns = {column.name for column in inspect(ResourceAccount).columns}
    assert "price" not in account_columns
    assert "monthly_cost" not in account_columns
    assert "amount" not in account_columns
    assert "cost" not in account_columns
