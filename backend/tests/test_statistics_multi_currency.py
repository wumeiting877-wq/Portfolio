from fastapi.testclient import TestClient

from tests.helpers import admin_headers, create_expense, create_project
from tests.statistics_setup import setup_statistics_world


def test_cny_and_usd_are_never_summed(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    overview = client.get(
        "/api/statistics/overview",
        params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"]},
        headers=ctx["admin"],
    ).json()
    assert overview["amounts_by_currency"]["CNY"] == "1450.00"
    assert overview["amounts_by_currency"]["USD"] == "140.00"
    assert "1590.00" not in overview["amounts_by_currency"].values()
    assert "total" not in overview

    trend = client.get(
        "/api/statistics/expense-trend",
        params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"]},
        headers=ctx["admin"],
    ).json()["series"]
    september = [item for item in trend if item["period"] == ctx["sep_period"]]
    currencies = {item["currency"] for item in september}
    assert currencies == {"CNY", "USD"}
    assert all(item["amount"] != "1590.00" for item in september)

    projects = client.get(
        "/api/statistics/project-costs",
        params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"], "limit": 20},
        headers=ctx["admin"],
    ).json()["items"]
    project_a = [item for item in projects if item["project_id"] == ctx["project_a"]["id"]]
    assert {item["currency"] for item in project_a} == {"CNY", "USD"}

    types = client.get(
        "/api/statistics/resource-type-costs",
        params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"], "limit": 20},
        headers=ctx["admin"],
    ).json()["items"]
    assert any(item["currency"] == "CNY" for item in types)
    assert any(item["currency"] == "USD" for item in types)


def test_equal_cny_usd_remain_separate(client: TestClient) -> None:
    headers = admin_headers(client)
    project = create_project(client, headers, name="多币种专项")
    create_expense(
        client,
        headers,
        amount="100.00",
        currency="CNY",
        expense_date="2026-03-15",
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "100.00"}
        ],
    )
    create_expense(
        client,
        headers,
        amount="100.00",
        currency="USD",
        expense_date="2026-03-15",
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "100.00"}
        ],
    )
    overview = client.get(
        "/api/statistics/overview",
        params={
            "date_from": "2026-03-15",
            "date_to": "2026-03-15",
            "project_id": project["id"],
        },
        headers=headers,
    ).json()
    assert overview["amounts_by_currency"]["CNY"] == "100.00"
    assert overview["amounts_by_currency"]["USD"] == "100.00"
    assert overview["amounts_by_currency"].get("total") is None
    assert "200.00" not in overview["amounts_by_currency"].values()
