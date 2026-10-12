from fastapi.testclient import TestClient

from tests.helpers import admin_headers, create_resource


def test_resource_openapi_has_no_secret_fields(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    resource_schema = spec["components"]["schemas"].get("ResourcePublic", {})
    properties = {key.lower() for key in resource_schema.get("properties", {})}
    forbidden = {"password", "api_key", "secret", "token", "credential", "access_key"}
    assert not (properties & forbidden)
    assert "price" not in properties
    assert "amount" not in properties
    assert "billing" not in properties


def test_created_resource_json_has_no_cost_fields(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource(client, headers)
    keys = {key.lower() for key in created}
    assert "price" not in keys
    assert "cost" not in keys
    assert "amount" not in keys
    assert "password" not in keys
    assert "api_key" not in keys
