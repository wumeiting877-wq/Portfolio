from fastapi.testclient import TestClient


def test_openapi_includes_health(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/health/db" in paths
    assert "/version" in paths
