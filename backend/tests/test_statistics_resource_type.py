from fastapi.testclient import TestClient

from tests.statistics_setup import setup_statistics_world


def test_bound_and_unbound_resource_type_costs(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/resource-type-costs",
        params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"], "limit": 20},
        headers=ctx["admin"],
    )
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    keyed = {(item["resource_type_code"], item["currency"]): item["allocated_amount"] for item in items}
    assert keyed[(ctx["rt_ai"]["code"], "CNY")] == "100.00"
    assert keyed[("UNBOUND", "USD")] == "140.00"
    assert keyed[("UNBOUND", "CNY")] == "1350.00"


def test_member_resource_type_costs_stay_in_scope(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/resource-type-costs",
        params={"date_from": ctx["year_from"], "date_to": ctx["year_to"], "limit": 20},
        headers=ctx["member"],
    )
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    keyed = {(item["resource_type_code"], item["currency"]): item["allocated_amount"] for item in items}
    assert keyed[(ctx["rt_ai"]["code"], "CNY")] == "100.00"
    assert keyed[("UNBOUND", "CNY")] == "30.00"
    assert all(item["currency"] != "USD" or item["allocated_amount"] == "0.00" for item in items)


def test_billing_costs_group_mode_category_currency(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/billing-costs",
        params={"date_from": ctx["year_from"], "date_to": ctx["year_to"]},
        headers=ctx["admin"],
    )
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    keyed = {
        (item["billing_mode"], item["category"], item["currency"]): item["allocated_amount"]
        for item in items
    }
    assert keyed[("ONE_TIME", "SERVER", "CNY")] == "200.00"
    assert keyed[("USAGE", "API_USAGE", "CNY")] == "30.00"
    assert keyed[("MANUAL", "SOFTWARE", "USD")] == "140.00"
