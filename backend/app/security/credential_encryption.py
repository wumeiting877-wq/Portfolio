from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import re
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_BYTES = 12
MASTER_KEY_BYTES = 32
CURRENT_ENCRYPTION_VERSION = 1
_KEY_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


class CredentialConfigurationError(RuntimeError):
    pass


class CredentialDecryptionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class EncryptedCredential:
    ciphertext: bytes
    nonce: bytes
    encryption_version: int
    key_id: str


def decode_master_key(encoded_key: str) -> bytes:
    if not encoded_key:
        raise CredentialConfigurationError("Credential encryption configuration is invalid")
    try:
        key = base64.b64decode(encoded_key, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise CredentialConfigurationError("Credential encryption configuration is invalid") from exc
    if len(key) != MASTER_KEY_BYTES:
        raise CredentialConfigurationError("Credential encryption configuration is invalid")
    return key


def validate_key_id(key_id: str) -> str:
    if not _KEY_ID_PATTERN.fullmatch(key_id or ""):
        raise CredentialConfigurationError("Credential encryption configuration is invalid")
    return key_id


def build_credential_aad(
    credential_id: int,
    resource_account_id: int,
    encryption_version: int = CURRENT_ENCRYPTION_VERSION,
) -> bytes:
    if credential_id <= 0 or resource_account_id <= 0 or encryption_version <= 0:
        raise ValueError("Credential AAD identifiers must be positive")
    return (
        f"credential:{credential_id}\n"
        f"resource:{resource_account_id}\n"
        f"version:{encryption_version}"
    ).encode("ascii")


class CredentialEncryptionService:
    def __init__(self, master_key: bytes, key_id: str) -> None:
        if len(master_key) != MASTER_KEY_BYTES:
            raise CredentialConfigurationError("Credential encryption configuration is invalid")
        self._cipher = AESGCM(master_key)
        self.key_id = validate_key_id(key_id)

    @classmethod
    def from_base64_key(cls, encoded_key: str, key_id: str) -> "CredentialEncryptionService":
        return cls(decode_master_key(encoded_key), key_id)

    def encrypt(self, plaintext: bytes, aad: bytes) -> EncryptedCredential:
        if not isinstance(plaintext, bytes) or not isinstance(aad, bytes):
            raise TypeError("Credential encryption inputs must be bytes")
        nonce = secrets.token_bytes(NONCE_BYTES)
        ciphertext = self._cipher.encrypt(nonce, plaintext, aad)
        return EncryptedCredential(
            ciphertext=ciphertext,
            nonce=nonce,
            encryption_version=CURRENT_ENCRYPTION_VERSION,
            key_id=self.key_id,
        )

    def decrypt(self, ciphertext: bytes, nonce: bytes, aad: bytes) -> bytes:
        if len(nonce) != NONCE_BYTES:
            raise CredentialDecryptionError("Credential decryption failed")
        try:
            return self._cipher.decrypt(nonce, ciphertext, aad)
        except (InvalidTag, ValueError, TypeError) as exc:
            raise CredentialDecryptionError("Credential decryption failed") from exc
