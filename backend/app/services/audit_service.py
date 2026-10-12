from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "old_password",
    "new_password",
    "initial_password",
    "api_key",
    "secret",
    "token",
    "credential",
    "access_key",
    "private_key",
    "ssh_private_key",
    "client_secret",
    "passphrase",
    "refresh_token",
    "encrypted_payload",
    "ciphertext",
    "encryption_nonce",
    "nonce",
    "authorization",
    "reauth_proof",
    "master_key",
    "credential_master_key",
}


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    if lowered in SENSITIVE_KEYS:
        return True
    return any(token in lowered for token in ("password", "secret", "token", "api_key"))


def _sanitize(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: _sanitize(value) for key, value in data.items() if not _is_sensitive_key(str(key))}
    if isinstance(data, (list, tuple)):
        sanitized = [_sanitize(item) for item in data]
        return tuple(sanitized) if isinstance(data, tuple) else sanitized
    return data


def write_audit(
    db: Session,
    *,
    operator_user_id: int | None,
    action: str,
    module: str,
    target_type: str | None = None,
    target_id: str | int | None = None,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            operator_user_id=operator_user_id,
            action=action,
            module=module,
            target_type=target_type,
            target_id=None if target_id is None else str(target_id),
            before_data=_sanitize(before_data),
            after_data=_sanitize(after_data),
            ip_address=ip_address,
        )
    )


def public_audit_payload(log: AuditLog) -> dict[str, Any]:
    return {
        "id": log.id,
        "operator_user_id": log.operator_user_id,
        "action": log.action,
        "module": log.module,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "before_data": _sanitize(log.before_data),
        "after_data": _sanitize(log.after_data),
        "ip_address": log.ip_address,
        "created_at": log.created_at,
    }
