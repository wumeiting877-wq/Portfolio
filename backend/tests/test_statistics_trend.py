from fastapi.testclient import TestClient

from tests.statistics_setup import setup_statistics_world


def test_trend_groups_by_month_and_currency(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/expense-trend",
        params={"date_from": ctx["span_from"], "date_to": ctx["span_to"]},
        headers=ctx["admin"],
    )
    assert response.status_code == 200, response.text
    series = response.json()["series"]
    keyed = {(item["period"], item["currency"]): item["amount"] for item in series}
    assert keyed[(ctx["sep_period"], "CNY")] == "1450.00"
    assert keyed[(ctx["sep_period"], "USD")] == "140.00"
    assert keyed[(ctx["aug_period"], "CNY")] == "200.00"
    assert keyed[(ctx["jul_period"], "CNY")] == "30.00"
    assert "total" not in response.json()


def test_pm_trend_uses_managed_share_only(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    series = client.get(
        "/api/statistics/expense-trend",
        params={"date_from": ctx["span_from"], "date_to": ctx["span_to"]},
        headers=ctx["pm"],
    ).json()["series"]
    keyed = {(item["period"], item["currency"]): item["amount"] for item in series}
    assert keyed[(ctx["sep_period"], "CNY")] == "1050.00"
    assert (ctx["aug_period"], "CNY") not in keyed


def test_member_trend_uses_self_share_only(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    series = client.get(
        "/api/statistics/expense-trend",
        params={"date_from": ctx["span_from"], "date_to": ctx["span_to"]},
        headers=ctx["member"],
    ).json()["series"]
    keyed = {(item["period"], item["currency"]): item["amount"] for item in series}
    assert keyed[(ctx["sep_period"], "CNY")] == "100.00"
    assert keyed[(ctx["jul_period"], "CNY")] == "30.00"
    assert (ctx["sep_period"], "USD") not in keyed
