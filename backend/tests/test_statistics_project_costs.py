from fastapi.testclient import TestClient

from tests.helpers import admin_headers, create_employee, create_expense, create_project
from tests.statistics_setup import setup_statistics_world


def _by_project(items: list[dict]) -> dict[tuple[int, str], str]:
    return {(item["project_id"], item["currency"]): item["allocated_amount"] for item in items}


def test_admin_project_costs_include_all_projects_by_currency(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/project-costs",
        params={"date_from": ctx["year_from"], "date_to": ctx["year_to"], "limit": 20},
        headers=ctx["admin"],
    )
    assert response.status_code == 200, response.text
    keyed = _by_project(response.json()["items"])
    assert keyed[(ctx["project_a"]["id"], "CNY")] == "1050.00"
    assert keyed[(ctx["project_a"]["id"], "USD")] == "140.00"
    assert keyed[(ctx["project_b"]["id"], "CNY")] == "600.00"


def test_boss_project_costs_match_admin(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    params = {"date_from": ctx["year_from"], "date_to": ctx["year_to"], "limit": 20}
    admin_items = client.get("/api/statistics/project-costs", params=params, headers=ctx["admin"]).json()["items"]
    boss_items = client.get("/api/statistics/project-costs", params=params, headers=ctx["boss"]).json()["items"]
    assert _by_project(admin_items) == _by_project(boss_items)


def test_pm_project_costs_only_managed_and_shared_share(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/project-costs",
        params={"date_from": ctx["year_from"], "date_to": ctx["year_to"], "limit": 20},
        headers=ctx["pm"],
    )
    keyed = _by_project(response.json()["items"])
    assert ctx["project_b"]["id"] not in {item["project_id"] for item in response.json()["items"]}
    assert keyed[(ctx["project_a"]["id"], "CNY")] == "1050.00"


def test_member_project_costs_forbidden(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get("/api/statistics/project-costs", headers=ctx["member"])
    assert response.status_code == 403


def test_employee_only_expense_does_not_infer_project(client: TestClient) -> None:
    headers = admin_headers(client)
    member = create_employee(client, headers, name="仅成员费用")
    project = create_project(client, headers, name="不应被反推", manager_employee_id=member["id"])
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member["id"]},
        headers=headers,
    )
    create_expense(
        client,
        headers,
        amount="88.00",
        currency="CNY",
        expense_date="2025-05-01",
        distributions=[
            {"employee_id": member["id"], "allocation_method": "DIRECT", "allocated_amount": "88.00"}
        ],
    )
    items = client.get(
        "/api/statistics/project-costs",
        params={"date_from": "2025-05-01", "date_to": "2025-05-31", "limit": 20},
        headers=headers,
    ).json()["items"]
    amounts = [
        item["allocated_amount"]
        for item in items
        if item["project_id"] == project["id"] and item["currency"] == "CNY"
    ]
    assert "88.00" not in amounts
