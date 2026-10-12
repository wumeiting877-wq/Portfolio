from fastapi.testclient import TestClient

from tests.statistics_setup import setup_statistics_world


def test_admin_employee_costs_exclude_project_public(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/employee-costs",
        params={"date_from": ctx["year_from"], "date_to": ctx["year_to"], "limit": 20},
        headers=ctx["admin"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    by_emp = {(item["employee_id"], item["currency"]): item["allocated_amount"] for item in body["items"]}
    assert by_emp[(ctx["member_a"]["id"], "CNY")] == "130.00"
    assert by_emp[(ctx["member_d"]["id"], "CNY")] == "300.00"
    public = {
        (item["project_id"], item["currency"]): item["allocated_amount"]
        for item in body["project_public_costs"]
    }
    assert public[(ctx["project_a"]["id"], "CNY")] == "650.00"
    assert public[(ctx["project_a"]["id"], "USD")] == "140.00"


def test_pm_employee_costs_only_managed_distributions(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/employee-costs",
        params={"date_from": ctx["year_from"], "date_to": ctx["year_to"], "limit": 20},
        headers=ctx["pm"],
    )
    body = response.json()
    employee_ids = {item["employee_id"] for item in body["items"]}
    assert ctx["pm_b"]["id"] not in employee_ids
    assert ctx["member_d"]["id"] in employee_ids
    assert ctx["member_a"]["id"] in employee_ids


def test_member_employee_costs_forbidden(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get("/api/statistics/employee-costs", headers=ctx["member"])
    assert response.status_code == 403
