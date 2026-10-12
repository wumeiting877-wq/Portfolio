from fastapi.testclient import TestClient

from tests.statistics_setup import setup_statistics_world


def test_pm_other_project_filter_cannot_expand_statistics(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/overview",
        params={
            "date_from": ctx["year_from"],
            "date_to": ctx["year_to"],
            "project_id": ctx["project_b"]["id"],
        },
        headers=ctx["pm"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["amounts_by_currency"] == {}
    assert body["project_count"] == 0


def test_member_other_employee_filter_cannot_expand_statistics(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/overview",
        params={
            "date_from": ctx["year_from"],
            "date_to": ctx["year_to"],
            "employee_id": ctx["member_d"]["id"],
        },
        headers=ctx["member"],
    )
    assert response.status_code == 200, response.text
    assert response.json()["amounts_by_currency"] == {}


def test_member_cannot_request_project_or_employee_ranking(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    assert client.get("/api/statistics/project-costs", headers=ctx["member"]).status_code == 403
    assert client.get("/api/statistics/employee-costs", headers=ctx["member"]).status_code == 403


def test_unauthorized_resource_filter_does_not_leak_counts(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get(
        "/api/statistics/resource-status",
        params={"project_id": ctx["project_b"]["id"]},
        headers=ctx["pm"],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["counts"]["ACTIVE"] == 0
    assert body["explicit_idle_count"] == 0
    assert body["unassigned_active_count"] == 0
