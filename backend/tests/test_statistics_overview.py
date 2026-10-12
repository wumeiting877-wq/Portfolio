from fastapi.testclient import TestClient

from tests.statistics_setup import setup_statistics_world


def test_admin_overview_splits_currency_and_excludes_voided(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/overview",
        params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"]},
        headers=ctx["admin"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "total" not in body
    assert body["amounts_by_currency"]["CNY"] == "1450.00"
    assert body["amounts_by_currency"]["USD"] == "140.00"
    assert "1450.00" != "1590.00"
    assert body["project_count"] >= 2
    assert body["resource_count"] >= 1
    assert "my_project_count" not in body


def test_boss_overview_matches_admin_range(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    params = {"date_from": ctx["sep_from"], "date_to": ctx["sep_to"]}
    admin_body = client.get("/api/statistics/overview", params=params, headers=ctx["admin"]).json()
    boss = client.get("/api/statistics/overview", params=params, headers=ctx["boss"])
    assert boss.status_code == 200
    boss_body = boss.json()
    assert boss_body["amounts_by_currency"] == admin_body["amounts_by_currency"]
    assert boss_body["project_count"] == admin_body["project_count"]


def test_pm_overview_only_managed_project_share(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/overview",
        params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"]},
        headers=ctx["pm"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["amounts_by_currency"]["CNY"] == "1050.00"
    assert body["amounts_by_currency"]["USD"] == "140.00"
    assert body["project_count"] == 1


def test_member_overview_only_self_direct_costs(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/overview",
        params={"date_from": ctx["year_from"], "date_to": ctx["year_to"]},
        headers=ctx["member"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["amounts_by_currency"]["CNY"] == "130.00"
    assert "USD" not in body["amounts_by_currency"]
    assert body["my_project_count"] == 1
    assert "project_count" not in body
    assert "employee_count" not in body
    assert "resource_count" not in body


def test_voided_amount_is_not_in_any_role_overview(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    for role in ("admin", "boss", "pm", "member"):
        body = client.get(
            "/api/statistics/overview",
            params={"date_from": ctx["sep_from"], "date_to": ctx["sep_to"]},
            headers=ctx[role],
        ).json()
        joined = "|".join(body["amounts_by_currency"].values())
        assert "999" not in joined
