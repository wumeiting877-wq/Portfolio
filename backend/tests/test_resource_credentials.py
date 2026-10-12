from __future__ import annotations

import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.resource_credential import ResourceCredential
from app.security.credential_encryption import CredentialEncryptionService, build_credential_aad
from app.services.resource_credential_service import get_credential_encryption_service
from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_allocation,
    create_employee,
    create_project,
    create_resource,
    create_user_account,
    unique,
)

KNOWN_SECRET = "V12_C2_KNOWN_SECRET_7Q4M"
ROTATED_SECRET = "V12_C2_ROTATED_SECRET_2K8P"
TEST_ENCRYPTION = CredentialEncryptionService(secrets.token_bytes(32), "c2-test-key")


@pytest.fixture(autouse=True)
def enabled_credentials(client: TestClient):
    app.dependency_overrides[get_credential_encryption_service] = lambda: TEST_ENCRYPTION
    yield
    app.dependency_overrides.pop(get_credential_encryption_service, None)


def _payload(resource_id: int, name: str | None = None, secret: str = KNOWN_SECRET) -> dict:
    return {
        "resource_account_id": resource_id,
        "credential_name": name or unique("credential"),
        "secret": {"credential_type": "API_KEY", "api_key": secret},
        "rotation_interval_days": 90,
    }


def _create_credential(
    client: TestClient,
    headers: dict[str, str],
    resource_id: int,
    *,
    name: str | None = None,
    secret: str = KNOWN_SECRET,
) -> tuple[dict, dict]:
    payload = _payload(resource_id, name=name, secret=secret)
    response = client.post("/api/resource-credentials", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json(), payload


def _assert_public_boundary(body: dict) -> None:
    assert body["has_secret"] is True
    forbidden = {
        "secret",
        "encrypted_payload",
        "encryption_nonce",
        "ciphertext",
        "nonce",
        "key_id",
        "encryption_version",
    }
    assert not (forbidden & set(body))


def test_create_list_detail_update_status_and_rotate(client: TestClient) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    created, _ = _create_credential(client, headers, resource["id"])
    _assert_public_boundary(created)
    assert created["credential_type"] == "API_KEY"
    assert created["status"] == "ACTIVE"

    listed = client.get(
        "/api/resource-credentials",
        params={"resource_account_id": resource["id"]},
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    assert created["id"] in {item["id"] for item in listed.json()["items"]}
    _assert_public_boundary(listed.json()["items"][0])

    detail = client.get(f"/api/resource-credentials/{created['id']}", headers=headers)
    assert detail.status_code == 200
    _assert_public_boundary(detail.json())

    renamed = unique("renamed")
    updated = client.put(
        f"/api/resource-credentials/{created['id']}",
        json={"credential_name": renamed, "rotation_interval_days": 30},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["credential_name"] == renamed

    disabled = client.patch(
        f"/api/resource-credentials/{created['id']}/status",
        json={"status": "DISABLED"},
        headers=headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"

    before_rotation = disabled.json()["last_rotated_at"]
    rotated = client.post(
        f"/api/resource-credentials/{created['id']}/rotate",
        json={"secret": {"credential_type": "API_KEY", "api_key": ROTATED_SECRET}},
        headers=headers,
    )
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["last_rotated_at"] >= before_rotation
    assert ROTATED_SECRET not in rotated.text

    with SessionLocal() as db:
        row = db.get(ResourceCredential, created["id"])
        assert row is not None
        plaintext = TEST_ENCRYPTION.decrypt(
            row.encrypted_payload,
            row.encryption_nonce,
            build_credential_aad(row.id, row.resource_account_id, row.encryption_version),
        )
        assert ROTATED_SECRET.encode() in plaintext
        assert KNOWN_SECRET.encode() not in row.encrypted_payload
        assert ROTATED_SECRET.encode() not in row.encrypted_payload


def test_auth_role_and_resource_relation_are_enforced(client: TestClient) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    payload = _payload(resource["id"])
    assert client.post("/api/resource-credentials", json=payload).status_code == 401

    boss_employee = create_employee(client, headers)
    _, boss_name, boss_password = create_user_account(
        client,
        headers,
        role_code="BOSS",
        employee_id=boss_employee["id"],
    )
    boss_headers = auth_headers_for(client, boss_name, boss_password)
    assert (
        client.post("/api/resource-credentials", json=payload, headers=boss_headers).status_code
        == 403
    )
    missing = _payload(2_000_000_000)
    response = client.post("/api/resource-credentials", json=missing, headers=headers)
    assert response.status_code == 404
    assert KNOWN_SECRET not in response.text


def test_resource_scope_blocks_cross_project_metadata(client: TestClient) -> None:
    headers = admin_headers(client)
    pm_a = create_employee(client, headers)
    pm_b = create_employee(client, headers)
    member = create_employee(client, headers)
    _, pm_a_name, pm_a_password = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_a["id"]
    )
    _, pm_b_name, pm_b_password = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_b["id"]
    )
    project_a = create_project(client, headers, manager_employee_id=pm_a["id"])
    project_b = create_project(client, headers, manager_employee_id=pm_b["id"])
    member_response = client.post(
        f"/api/projects/{project_a['id']}/members",
        json={"employee_id": member["id"]},
        headers=headers,
    )
    assert member_response.status_code == 200, member_response.text
    resource = create_resource(client, headers)
    create_allocation(
        client,
        headers,
        resource["id"],
        project_id=project_a["id"],
        employee_id=member["id"],
    )
    created, _ = _create_credential(client, headers, resource["id"])
    visible_headers = auth_headers_for(client, pm_a_name, pm_a_password)
    hidden_headers = auth_headers_for(client, pm_b_name, pm_b_password)

    assert (
        client.get(f"/api/resource-credentials/{created['id']}", headers=visible_headers).status_code
        == 200
    )
    assert (
        client.get(f"/api/resource-credentials/{created['id']}", headers=hidden_headers).status_code
        == 404
    )
    hidden_list = client.get(
        "/api/resource-credentials",
        params={"resource_account_id": resource["id"]},
        headers=hidden_headers,
    )
    assert hidden_list.status_code == 200
    assert hidden_list.json()["items"] == []
    assert project_b["id"] != project_a["id"]


def test_invalid_secret_is_rejected_without_echo(client: TestClient) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    rejected = "V12_C2_REJECTED_SECRET_SHOULD_NOT_ECHO"
    response = client.post(
        "/api/resource-credentials",
        json={
            "resource_account_id": resource["id"],
            "credential_name": "bad",
            "secret": {
                "credential_type": "API_KEY",
                "api_key": rejected,
                "unexpected": rejected,
            },
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert rejected not in response.text
    assert "input" not in response.text.lower()


def test_duplicate_name_conflict_and_no_secret_echo(client: TestClient) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    name = unique("duplicate")
    _create_credential(client, headers, resource["id"], name=name)
    response = client.post(
        "/api/resource-credentials",
        json=_payload(resource["id"], name=name),
        headers=headers,
    )
    assert response.status_code == 409
    assert KNOWN_SECRET not in response.text


def test_transaction_rolls_back_when_audit_write_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    name = unique("rollback")

    def fail_audit(*args, **kwargs):
        raise RuntimeError("simulated audit failure")

    monkeypatch.setattr("app.services.resource_credential_service.write_audit", fail_audit)
    with pytest.raises(RuntimeError, match="simulated audit failure"):
        client.post(
            "/api/resource-credentials",
            json=_payload(resource["id"], name=name),
            headers=headers,
        )
    with SessionLocal() as db:
        assert (
            db.query(ResourceCredential)
            .filter(
                ResourceCredential.resource_account_id == resource["id"],
                ResourceCredential.credential_name == name,
            )
            .first()
            is None
        )


def test_tampered_data_and_wrong_key_fail_secure(client: TestClient) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    tampered, _ = _create_credential(client, headers, resource["id"])
    with SessionLocal() as db:
        row = db.get(ResourceCredential, tampered["id"])
        assert row is not None
        row.encrypted_payload = bytes([row.encrypted_payload[0] ^ 1]) + row.encrypted_payload[1:]
        db.commit()

    response = client.post(
        f"/api/resource-credentials/{tampered['id']}/rotate",
        json={"secret": {"credential_type": "API_KEY", "api_key": ROTATED_SECRET}},
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "凭据完整性校验失败"}
    assert ROTATED_SECRET not in response.text

    intact, _ = _create_credential(client, headers, resource["id"])
    wrong_encryption = CredentialEncryptionService(secrets.token_bytes(32), "c2-test-key")
    app.dependency_overrides[get_credential_encryption_service] = lambda: wrong_encryption
    wrong_key = client.post(
        f"/api/resource-credentials/{intact['id']}/rotate",
        json={"secret": {"credential_type": "API_KEY", "api_key": ROTATED_SECRET}},
        headers=headers,
    )
    assert wrong_key.status_code == 409
    assert wrong_key.json() == {"detail": "凭据完整性校验失败"}


def test_plaintext_absent_from_database_audit_response_and_logs(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    headers = admin_headers(client)
    resource = create_resource(client, headers)
    created, _ = _create_credential(client, headers, resource["id"])
    assert KNOWN_SECRET not in str(created)
    assert KNOWN_SECRET not in caplog.text

    with SessionLocal() as db:
        stored = db.execute(
            text(
                "SELECT encrypted_payload, encryption_nonce FROM resource_credentials WHERE id = :id"
            ),
            {"id": created["id"]},
        ).one()
        assert KNOWN_SECRET.encode() not in stored.encrypted_payload
        assert KNOWN_SECRET.encode() not in stored.encryption_nonce
        audits = (
            db.query(AuditLog)
            .filter(
                AuditLog.module == "resource_credentials",
                AuditLog.target_id == str(created["id"]),
            )
            .all()
        )
        assert audits
        assert KNOWN_SECRET not in str([(item.before_data, item.after_data) for item in audits])
        assert all(
            "encrypted_payload" not in str(item.after_data) and "nonce" not in str(item.after_data)
            for item in audits
        )


def test_openapi_has_no_reveal_and_no_sensitive_response_fields(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert not any(path.endswith("/reveal") for path in spec["paths"])
    properties = spec["components"]["schemas"]["ResourceCredentialPublic"]["properties"]
    assert not {
        "secret",
        "encrypted_payload",
        "encryption_nonce",
        "key_id",
        "encryption_version",
    } & set(properties)


def test_disabled_feature_fails_closed(client: TestClient) -> None:
    headers = admin_headers(client)
    app.dependency_overrides.pop(get_credential_encryption_service, None)
    response = client.get("/api/resource-credentials", headers=headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "凭据管理功能未启用"}
    app.dependency_overrides[get_credential_encryption_service] = lambda: TEST_ENCRYPTION
