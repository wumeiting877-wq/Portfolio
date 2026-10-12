from __future__ import annotations

import base64
import secrets
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings, validate_runtime_config
from app.core.database import SessionLocal, engine
from app.models.enums import CredentialStatus, CredentialType
from app.models.resource_account import ResourceAccount
from app.models.resource_credential import ResourceCredential
from app.models.resource_credential_grant import ResourceCredentialGrant
from app.models.resource_type import ResourceType
from app.models.user import User
from app.schemas.credential_secret import ApiKeySecret, serialize_credential_secret
from app.schemas.resource import ResourcePublic
from app.schemas.resource_credential import ResourceCredentialGrantInternal, ResourceCredentialMetadata
from app.security.credential_encryption import (
    CredentialDecryptionError,
    CredentialEncryptionService,
    build_credential_aad,
)
from app.security.sensitive_validation import sanitize_sensitive_validation_errors
from app.services.audit_service import _sanitize

KNOWN_SECRET = "V12_C1_KNOWN_SECRET_9X7K"
KEY_ID = "resource-credentials-v1"


def _encoded_key(raw: bytes | None = None) -> str:
    return base64.b64encode(raw or secrets.token_bytes(32)).decode("ascii")


def test_master_key_feature_flag_and_fail_fast() -> None:
    validate_runtime_config(
        Settings(RESOURCE_CREDENTIALS_ENABLED=False, CREDENTIAL_MASTER_KEY="", CREDENTIAL_ACTIVE_KEY_ID="")
    )
    with pytest.raises(RuntimeError):
        validate_runtime_config(Settings(RESOURCE_CREDENTIALS_ENABLED=True, CREDENTIAL_MASTER_KEY=""))
    with pytest.raises(RuntimeError):
        validate_runtime_config(
            Settings(
                RESOURCE_CREDENTIALS_ENABLED=True,
                CREDENTIAL_MASTER_KEY="not valid base64!",
                CREDENTIAL_ACTIVE_KEY_ID=KEY_ID,
            )
        )
    with pytest.raises(RuntimeError):
        validate_runtime_config(
            Settings(
                RESOURCE_CREDENTIALS_ENABLED=True,
                CREDENTIAL_MASTER_KEY=_encoded_key(b"too-short"),
                CREDENTIAL_ACTIVE_KEY_ID=KEY_ID,
            )
        )
    validate_runtime_config(
        Settings(
            RESOURCE_CREDENTIALS_ENABLED=True,
            CREDENTIAL_MASTER_KEY=_encoded_key(),
            CREDENTIAL_ACTIVE_KEY_ID=KEY_ID,
        )
    )


def test_aes_gcm_roundtrip_nonce_randomness_and_tamper_fail_secure() -> None:
    key = secrets.token_bytes(32)
    service = CredentialEncryptionService(key, KEY_ID)
    plaintext = KNOWN_SECRET.encode()
    aad = build_credential_aad(1, 2)

    first = service.encrypt(plaintext, aad)
    second = service.encrypt(plaintext, aad)
    assert plaintext not in first.ciphertext
    assert first.nonce != second.nonce
    assert first.ciphertext != second.ciphertext
    assert service.decrypt(first.ciphertext, first.nonce, aad) == plaintext
    assert service.decrypt(second.ciphertext, second.nonce, aad) == plaintext

    wrong_key = CredentialEncryptionService(secrets.token_bytes(32), "wrong-key")
    tampered_ciphertext = bytes([first.ciphertext[0] ^ 1]) + first.ciphertext[1:]
    tampered_nonce = bytes([first.nonce[0] ^ 1]) + first.nonce[1:]
    failures = (
        lambda: wrong_key.decrypt(first.ciphertext, first.nonce, aad),
        lambda: service.decrypt(tampered_ciphertext, first.nonce, aad),
        lambda: service.decrypt(first.ciphertext, tampered_nonce, aad),
        lambda: service.decrypt(first.ciphertext, first.nonce, build_credential_aad(1, 3)),
    )
    for operation in failures:
        with pytest.raises(CredentialDecryptionError) as exc_info:
            operation()
        assert str(exc_info.value) == "Credential decryption failed"
        leaked = str(exc_info.value)
        assert KNOWN_SECRET not in leaked
        assert KEY_ID not in leaked


def test_canonical_secret_schema_and_validation_error_sanitizer() -> None:
    model = ApiKeySecret(credential_type="API_KEY", api_key=KNOWN_SECRET)
    assert serialize_credential_secret(model) == (
        b'{"api_key":"V12_C1_KNOWN_SECRET_9X7K","credential_type":"API_KEY"}'
    )
    try:
        ApiKeySecret.model_validate({"credential_type": "API_KEY", "api_key": 123})
    except ValidationError as exc:
        raw = str(exc)
        assert "123" in raw
        safe = sanitize_sensitive_validation_errors(exc)
    else:
        raise AssertionError("Expected sensitive schema validation to fail")
    assert "123" not in str(safe)
    assert "input" not in str(safe).lower()


def test_audit_sanitizer_is_case_insensitive_and_recursive() -> None:
    value = {
        "safe": "kept",
        "nested": [
            {"Password": KNOWN_SECRET, "name": "ok"},
            ({"client_secret": KNOWN_SECRET}, {"nonce": KNOWN_SECRET}),
        ],
        "authorization": KNOWN_SECRET,
        "encrypted_payload": KNOWN_SECRET,
    }
    sanitized = _sanitize(value)
    assert sanitized["safe"] == "kept"
    assert KNOWN_SECRET not in str(sanitized)
    assert sanitized["nested"][0] == {"name": "ok"}
    assert isinstance(sanitized["nested"][1], tuple)


def _create_resource(db, suffix: str) -> ResourceAccount:
    resource_type = ResourceType(
        code=f"C1_{suffix}"[:50],
        name=f"C1 Type {suffix}"[:100],
        category="OTHER",
        is_active=True,
    )
    db.add(resource_type)
    db.flush()
    resource = ResourceAccount(
        resource_type_id=resource_type.id,
        resource_name=f"C1 Resource {suffix}"[:200],
        status="ACTIVE",
    )
    db.add(resource)
    db.flush()
    return resource


def _encrypted_credential(db, resource: ResourceAccount, user: User, name: str) -> ResourceCredential:
    credential_id = db.execute(
        text("SELECT nextval(pg_get_serial_sequence('resource_credentials', 'id'))")
    ).scalar_one()
    payload = serialize_credential_secret(
        ApiKeySecret(credential_type="API_KEY", api_key=KNOWN_SECRET)
    )
    encrypted = CredentialEncryptionService(secrets.token_bytes(32), KEY_ID).encrypt(
        payload,
        build_credential_aad(credential_id, resource.id),
    )
    credential = ResourceCredential(
        id=credential_id,
        resource_account_id=resource.id,
        credential_name=name,
        credential_type=CredentialType.API_KEY.value,
        encrypted_payload=encrypted.ciphertext,
        encryption_nonce=encrypted.nonce,
        encryption_version=encrypted.encryption_version,
        key_id=encrypted.key_id,
        status=CredentialStatus.ACTIVE.value,
        created_by_user_id=user.id,
        updated_by_user_id=user.id,
    )
    db.add(credential)
    db.flush()
    return credential


def test_credential_model_constraints_grant_user_fk_and_plaintext_absence() -> None:
    suffix = uuid.uuid4().hex[:10]
    with SessionLocal() as db:
        user = db.query(User).order_by(User.id).first()
        assert user is not None
        resource_one = _create_resource(db, suffix + "a")
        resource_two = _create_resource(db, suffix + "b")
        first = _encrypted_credential(db, resource_one, user, "shared-name")
        second = _encrypted_credential(db, resource_two, user, "shared-name")
        grant = ResourceCredentialGrant(
            credential_id=first.id,
            user_id=user.id,
            can_reveal=True,
            granted_by_user_id=user.id,
        )
        db.add(grant)
        db.commit()

        assert first.resource_account_id == resource_one.id
        assert second.resource_account_id == resource_two.id
        stored = db.execute(
            text(
                "SELECT encrypted_payload, encryption_nonce "
                "FROM resource_credentials WHERE id IN (:first_id, :second_id)"
            ),
            {"first_id": first.id, "second_id": second.id},
        ).all()
        assert stored
        assert all(KNOWN_SECRET.encode() not in ciphertext for ciphertext, _ in stored)
        assert all(KNOWN_SECRET.encode() not in nonce for _, nonce in stored)
        assert db.get(ResourceCredentialGrant, grant.id).user_id == user.id

    with SessionLocal() as db:
        user = db.query(User).order_by(User.id).first()
        resource = db.query(ResourceAccount).filter(ResourceAccount.resource_name == f"C1 Resource {suffix}a").one()
        with pytest.raises(IntegrityError):
            _encrypted_credential(db, resource, user, "shared-name")
            db.commit()
        db.rollback()

    with SessionLocal() as db:
        user = db.query(User).order_by(User.id).first()
        credential = db.query(ResourceCredential).filter(ResourceCredential.credential_name == "shared-name").first()
        with pytest.raises(IntegrityError):
            db.add(
                ResourceCredentialGrant(
                    credential_id=credential.id,
                    user_id=user.id,
                    can_reveal=False,
                    granted_by_user_id=user.id,
                )
            )
            db.commit()
        db.rollback()

    with SessionLocal() as db:
        user = db.query(User).order_by(User.id).first()
        resource = _create_resource(db, suffix + "c")
        bad = _encrypted_credential(db, resource, user, "bad-rotation")
        bad.rotation_interval_days = 0
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_resource_serialization_boundary_and_logging_defaults() -> None:
    assert "credentials" not in ResourcePublic.model_fields
    assert "encrypted_payload" not in ResourcePublic.model_fields
    assert "encrypted_payload" not in ResourceCredentialMetadata.model_fields
    assert "encryption_nonce" not in ResourceCredentialMetadata.model_fields
    assert "user" not in ResourceCredentialGrantInternal.model_fields
    assert "password_hash" not in ResourceCredentialGrantInternal.model_fields
    assert not engine.echo
    columns = {column.name for column in inspect(ResourceAccount).columns}
    assert "encrypted_payload" not in columns
    assert "secret" not in columns
