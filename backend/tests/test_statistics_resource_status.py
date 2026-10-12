from fastapi.testclient import TestClient

from tests.statistics_setup import setup_statistics_world


def test_resource_status_distinguishes_idle_unassigned_expired_expiring(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get("/api/statistics/resource-status", headers=ctx["admin"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["explicit_idle_count"] >= 1
    assert body["unassigned_active_count"] >= 1
    assert body["counts"]["IDLE"] == body["explicit_idle_count"]
    assert body["counts"]["UNASSIGNED_ACTIVE"] == body["unassigned_active_count"]
    assert body["counts"]["EXPIRED"] >= 1
    assert body["counts"]["EXPIRING_SOON"] >= 1
    idle_ids = {item["id"] for item in body["idle_resources"]}
    unassigned_ids = {item["id"] for item in body["unassigned_active_resources"]}
    assert ctx["idle"]["id"] in idle_ids
    assert ctx["unassigned"]["id"] in unassigned_ids
    assert ctx["idle"]["id"] not in unassigned_ids
    assert ctx["unassigned"]["id"] not in idle_ids


def test_released_allocation_is_not_active_relationship(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    body = client.get("/api/statistics/resource-status", headers=ctx["admin"]).json()
    unassigned_ids = {item["id"] for item in body["unassigned_active_resources"]}
    assert ctx["released_resource"]["id"] in unassigned_ids


def test_expiring_soon_is_dynamic_and_within_days(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    response = client.get("/api/statistics/expiring-resources", params={"days": 30}, headers=ctx["admin"])
    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()["items"]}
    assert ctx["expiring"]["id"] in ids
    assert ctx["later"]["id"] not in ids
    assert response.json()["days"] == 30
    resource = client.get(f"/api/resources/{ctx['expiring']['id']}", headers=ctx["admin"]).json()
    assert resource["status"] == "ACTIVE"
    assert resource["expires_at"] is not None


def test_pm_resource_status_does_not_include_unallocated_global_resources(client: TestClient) -> None:
    ctx = setup_statistics_world(client)
    body = client.get("/api/statistics/resource-status", headers=ctx["pm"]).json()
    unassigned_ids = {item["id"] for item in body["unassigned_active_resources"]}
    assert ctx["unassigned"]["id"] not in unassigned_ids
    expiring = client.get("/api/statistics/expiring-resources", headers=ctx["pm"]).json()
    expiring_ids = {item["id"] for item in expiring["items"]}
    assert ctx["expiring"]["id"] not in expiring_ids
