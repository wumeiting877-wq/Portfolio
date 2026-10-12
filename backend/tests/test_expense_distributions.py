from decimal import Decimal

from fastapi.testclient import TestClient

from tests.helpers import (
    admin_headers,
    create_employee,
    create_expense,
    create_project,
)


def test_single_project_direct(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    created = create_expense(
        client,
        headers,
        amount="1000.00",
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "1000.00"}
        ],
    )
    assert len(created["distributions"]) == 1
    assert created["distributions"][0]["project_id"] == project["id"]
    assert created["distributions"][0]["employee_id"] is None


def test_single_employee_direct(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    created = create_expense(
        client,
        headers,
        amount="500.00",
        distributions=[
            {"employee_id": employee["id"], "allocation_method": "DIRECT", "allocated_amount": "500.00"}
        ],
    )
    assert created["distributions"][0]["employee_id"] == employee["id"]
    assert created["distributions"][0]["project_id"] is None


def test_project_and_employee_direct(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=employee["id"])
    created = create_expense(
        client,
        headers,
        amount="800.00",
        distributions=[
            {
                "project_id": project["id"],
                "employee_id": employee["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "800.00",
            }
        ],
    )
    assert created["distributions"][0]["project_id"] == project["id"]
    assert created["distributions"][0]["employee_id"] == employee["id"]


def test_equal_split_among_members(client: TestClient) -> None:
    headers = admin_headers(client)
    a = create_employee(client, headers, name="张三")
    b = create_employee(client, headers, name="李四")
    c = create_employee(client, headers, name="王五")
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
    assert sorted(amounts) == [Decimal("333.33"), Decimal("333.33"), Decimal("333.34")]


def test_multi_project_ratio(client: TestClient) -> None:
    headers = admin_headers(client)
    project_a = create_project(client, headers, name="新华")
    project_b = create_project(client, headers, name="佳悦")
    created = create_expense(
        client,
        headers,
        amount="1000.00",
        distributions=[
            {"project_id": project_a["id"], "allocation_method": "RATIO", "allocation_ratio": "0.6"},
            {"project_id": project_b["id"], "allocation_method": "RATIO", "allocation_ratio": "0.4"},
        ],
    )
    by_project = {item["project_id"]: Decimal(item["allocated_amount"]) for item in created["distributions"]}
    assert by_project[project_a["id"]] == Decimal("600.00")
    assert by_project[project_b["id"]] == Decimal("400.00")


def test_manual_amount_distribution(client: TestClient) -> None:
    headers = admin_headers(client)
    project_a = create_project(client, headers)
    project_b = create_project(client, headers)
    created = create_expense(
        client,
        headers,
        amount="1000.00",
        distributions=[
            {"project_id": project_a["id"], "allocation_method": "MANUAL", "allocated_amount": "650.00"},
            {"project_id": project_b["id"], "allocation_method": "MANUAL", "allocated_amount": "350.00"},
        ],
    )
    assert Decimal(created["distributions"][0]["allocated_amount"]) + Decimal(
        created["distributions"][1]["allocated_amount"]
    ) == Decimal("1000.00")


def test_distribution_sum_mismatch_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers)
    from tests.helpers import create_expense_type

    expense_type = create_expense_type(client, headers)
    response = client.post(
        "/api/expenses",
        json={
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-01",
            "amount": "1000.00",
            "currency": "CNY",
            "distributions": [
                {"project_id": project["id"], "allocation_method": "MANUAL", "allocated_amount": "900.00"}
            ],
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert "分摊金额合计必须等于费用金额" in response.json()["detail"]


def test_mismatched_project_member_distribution_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    outsider = create_employee(client, headers, name="外人")
    manager = create_employee(client, headers, name="负责人")
    project = create_project(client, headers, manager_employee_id=manager["id"])
    from tests.helpers import create_expense_type

    expense_type = create_expense_type(client, headers)
    response = client.post(
        "/api/expenses",
        json={
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-01",
            "amount": "100.00",
            "currency": "CNY",
            "distributions": [
                {
                    "project_id": project["id"],
                    "employee_id": outsider["id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "100.00",
                }
            ],
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_distribution_requires_target(client: TestClient) -> None:
    headers = admin_headers(client)
    from tests.helpers import create_expense_type

    expense_type = create_expense_type(client, headers)
    response = client.post(
        "/api/expenses",
        json={
            "expense_type_id": expense_type["id"],
            "billing_mode": "MANUAL",
            "expense_date": "2026-09-01",
            "amount": "100.00",
            "currency": "CNY",
            "distributions": [{"allocation_method": "DIRECT", "allocated_amount": "100.00"}],
        },
        headers=headers,
    )
    assert response.status_code == 400
