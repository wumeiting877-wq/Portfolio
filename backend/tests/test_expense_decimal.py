from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.money import split_equal
from tests.helpers import admin_headers, create_employee, create_expense, create_project


def test_decimal_point_one_plus_point_two(client: TestClient) -> None:
    headers = admin_headers(client)
    project_a = create_project(client, headers)
    project_b = create_project(client, headers)
    created = create_expense(
        client,
        headers,
        amount="0.30",
        distributions=[
            {"project_id": project_a["id"], "allocation_method": "MANUAL", "allocated_amount": "0.10"},
            {"project_id": project_b["id"], "allocation_method": "MANUAL", "allocated_amount": "0.20"},
        ],
    )
    total = Decimal(created["distributions"][0]["allocated_amount"]) + Decimal(
        created["distributions"][1]["allocated_amount"]
    )
    assert total == Decimal("0.30")
    assert Decimal(created["amount"]) == Decimal("0.30")


def test_equal_split_one_thousand_by_three() -> None:
    parts = split_equal(Decimal("1000.00"), 3)
    assert sum(parts) == Decimal("1000.00")
    assert sorted(parts) == [Decimal("333.33"), Decimal("333.33"), Decimal("333.34")]


def test_equal_split_persisted(client: TestClient) -> None:
    headers = admin_headers(client)
    a = create_employee(client, headers)
    b = create_employee(client, headers)
    c = create_employee(client, headers)
    created = create_expense(
        client,
        headers,
        amount="1000.00",
        distributions=[
            {"employee_id": a["id"], "allocation_method": "EQUAL"},
            {"employee_id": b["id"], "allocation_method": "EQUAL"},
            {"employee_id": c["id"], "allocation_method": "EQUAL"},
        ],
    )
    amounts = [Decimal(item["allocated_amount"]) for item in created["distributions"]]
    assert sum(amounts) == Decimal("1000.00")
    assert Decimal(created["amount"]) == Decimal("1000.00")
    assert not any(isinstance(item["allocated_amount"], float) for item in created["distributions"])
