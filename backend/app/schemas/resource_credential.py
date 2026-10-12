from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import CredentialStatus
from app.schemas.credential_secret import CredentialSecret


def _require_timezone(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("时间必须包含时区")
    return value


class ResourceCredentialMetadata(BaseModel):
    """Internal metadata boundary; deliberately excludes encrypted and plaintext fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_account_id: int
    credential_name: str
    credential_type: str
    encryption_version: int
    key_id: str
    status: str
    expires_at: datetime | None
    last_rotated_at: datetime | None
    rotation_interval_days: int | None
    created_by_user_id: int
    updated_by_user_id: int
    created_at: datetime
    updated_at: datetime


class ResourceCredentialGrantInternal(BaseModel):
    """Internal grant shape; IDs only, with no nested User serialization."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    credential_id: int
    user_id: int
    can_reveal: bool
    valid_from: datetime | None
    valid_until: datetime | None
    revoked_at: datetime | None
    granted_by_user_id: int
    created_at: datetime
    updated_at: datetime


class ResourceCredentialCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_account_id: int = Field(gt=0)
    credential_name: str = Field(min_length=1, max_length=200)
    secret: CredentialSecret
    expires_at: datetime | None = None
    rotation_interval_days: int | None = Field(default=None, gt=0, le=36500)

    _expires_timezone = field_validator("expires_at")(_require_timezone)

    @model_validator(mode="after")
    def normalize_name(self) -> "ResourceCredentialCreate":
        self.credential_name = self.credential_name.strip()
        if not self.credential_name:
            raise ValueError("请输入凭据名称")
        return self


class ResourceCredentialUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    credential_name: str | None = Field(default=None, min_length=1, max_length=200)
    expires_at: datetime | None = None
    rotation_interval_days: int | None = Field(default=None, gt=0, le=36500)

    _expires_timezone = field_validator("expires_at")(_require_timezone)

    @model_validator(mode="after")
    def validate_update(self) -> "ResourceCredentialUpdate":
        if not self.model_fields_set:
            raise ValueError("至少提供一个可修改字段")
        if self.credential_name is not None:
            self.credential_name = self.credential_name.strip()
            if not self.credential_name:
                raise ValueError("请输入凭据名称")
        return self


class ResourceCredentialRotate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    secret: CredentialSecret


class ResourceCredentialStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CredentialStatus


class ResourceCredentialPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_account_id: int
    credential_name: str
    credential_type: str
    status: str
    expires_at: datetime | None
    last_rotated_at: datetime | None
    rotation_interval_days: int | None
    has_secret: bool = True
    created_at: datetime
    updated_at: datetime


class ResourceCredentialListResponse(BaseModel):
    items: list[ResourceCredentialPublic]
    total: int
    page: int
    page_size: int
