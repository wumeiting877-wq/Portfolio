from __future__ import annotations

from typing import Any, Iterable

from pydantic import ValidationError

SENSITIVE_VALIDATION_FIELDS = frozenset(
    {
        "password",
        "api_key",
        "access_token",
        "refresh_token",
        "private_key",
        "passphrase",
        "client_secret",
        "secret",
        "encrypted_payload",
        "ciphertext",
        "encryption_nonce",
        "nonce",
        "authorization",
        "reauth_proof",
        "master_key",
        "credential_master_key",
    }
)


def _loc_is_sensitive(location: Iterable[object]) -> bool:
    return any(str(part).lower() in SENSITIVE_VALIDATION_FIELDS for part in location)


def sanitize_sensitive_validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
    """Return endpoint-safe 422 details without rejected input or secret-bearing context."""
    sanitized: list[dict[str, Any]] = []
    for error in exc.errors(include_input=False, include_context=False, include_url=False):
        clean = {"type": error["type"], "loc": error["loc"]}
        clean["msg"] = "Invalid sensitive value" if _loc_is_sensitive(error["loc"]) else error["msg"]
        sanitized.append(clean)
    return sanitized


def sanitize_request_validation_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sanitize FastAPI request errors without retaining rejected request values."""
    sanitized: list[dict[str, Any]] = []
    for error in errors:
        location = tuple(error.get("loc", ()))
        sanitized.append(
            {
                "type": str(error.get("type", "value_error")),
                "loc": location,
                "msg": (
                    "Invalid sensitive value"
                    if _loc_is_sensitive(location)
                    else str(error.get("msg", "Invalid value"))
                ),
            }
        )
    return sanitized
