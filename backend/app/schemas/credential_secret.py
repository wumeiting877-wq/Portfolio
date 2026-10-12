from __future__ import annotations

import json
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

SecretValue = Annotated[str, StringConstraints(min_length=1, max_length=65536)]
IdentifierValue = Annotated[str, StringConstraints(min_length=1, max_length=1000)]


class _SecretBase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class UsernamePasswordSecret(_SecretBase):
    credential_type: Literal["USERNAME_PASSWORD"]
    username: IdentifierValue
    password: SecretValue


class ApiKeySecret(_SecretBase):
    credential_type: Literal["API_KEY"]
    api_key: SecretValue


class AccessTokenSecret(_SecretBase):
    credential_type: Literal["ACCESS_TOKEN"]
    access_token: SecretValue


class ClientCredentialSecret(_SecretBase):
    credential_type: Literal["CLIENT_CREDENTIAL"]
    client_id: IdentifierValue
    client_secret: SecretValue


class SshKeySecret(_SecretBase):
    credential_type: Literal["SSH_KEY"]
    username: IdentifierValue
    private_key: SecretValue
    passphrase: SecretValue | None = None


class OtherSecret(_SecretBase):
    credential_type: Literal["OTHER"]
    secret: SecretValue


CredentialSecret = Annotated[
    Union[
        UsernamePasswordSecret,
        ApiKeySecret,
        AccessTokenSecret,
        ClientCredentialSecret,
        SshKeySecret,
        OtherSecret,
    ],
    Field(discriminator="credential_type"),
]

_SECRET_ADAPTER = TypeAdapter(CredentialSecret)


def serialize_credential_secret(secret: CredentialSecret) -> bytes:
    return json.dumps(
        secret.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def deserialize_credential_secret(payload: bytes) -> CredentialSecret:
    return _SECRET_ADAPTER.validate_json(payload)
