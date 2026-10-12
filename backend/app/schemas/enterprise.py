from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ImportErrorItem(BaseModel):
    row: int
    field: str
    message: str


class ImportPreviewResponse(BaseModel):
    import_type: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[ImportErrorItem] = Field(default_factory=list)


class ImportCommitResponse(ImportPreviewResponse):
    committed: bool
    created_count: int = 0


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    target_type: str
    target_id: str
    title: str
    message: str
    status: str
    resource_account_id: int | None = None
    resource_name: str | None = None
    project_id: int | None = None
    project_name: str | None = None
    due_date: str | None = None
    created_at: datetime
    read_at: datetime | None = None
    resolved_at: datetime | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationPublic]
    total: int
    page: int
    page_size: int
    generated: int = 0


class AuditLogPublic(BaseModel):
    id: int
    operator_user_id: int | None
    operator_username: str | None = None
    action: str
    module: str
    target_type: str | None
    target_id: str | None
    summary: str | None = None
    before_data: dict[str, Any] | None = None
    after_data: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogPublic]
    total: int
    page: int
    page_size: int


class VersionResponse(BaseModel):
    name: str
    version: str
    environment: str
