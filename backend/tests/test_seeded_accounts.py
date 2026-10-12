import pytest
from fastapi.testclient import TestClient

from tests.helpers import login


@pytest.mark.parametrize(
    ("username", "role", "scope"),
    [
        ("admin", "ADMIN", "GLOBAL"),
        ("boss", "BOSS", "GLOBAL"),
        ("pm", "PROJECT_MANAGER", "MANAGED_PROJECTS"),
        ("member", "MEMBER", "MEMBER_PROJECTS"),
    ],
)
def test_seeded_accounts_can_login(
    client: TestClient, username: str, role: str, scope: str
) -> None:
    response = login(client, username, "change_me")
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["role"] == role
    assert body["scope"] == scope
    assert body["status"] == "ACTIVE"
