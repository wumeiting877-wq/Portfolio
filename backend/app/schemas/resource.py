from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResourceTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    category: str = "OTHER"
    description: str | None = None


class ResourceTypeUpdate(BaseModel):
    """Ordinary edit. Code is not a field and extra keys, including code, are rejected."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = None
    description: str | None = None


class ResourceTypeCodeChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_code: str


class ResourceTypePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ResourceTypeCodeChangeResult(ResourceTypePublic):
    related_account_count: int


class ResourceTypeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str


class ResourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_type_id: int
    resource_name: str = Field(min_length=1, max_length=200)
    provider: str | None = Field(default=None, max_length=100)
    account_identifier: str | None = Field(default=None, max_length=200)
    plan_name: str | None = Field(default=None, max_length=100)
    status: str = "ACTIVE"
    purchased_at: date | None = None
    activated_at: date | None = None
    expires_at: date | None = None
    remark: str | None = None

    @field_validator("resource_name")
    @classmethod
    def _resource_name(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("请输入资源名称")
        return text


class ResourceNameChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_resource_name: str


class ResourceUpdate(BaseModel):
    """Ordinary edit. resource_name is not a field and is rejected if sent."""

    model_config = ConfigDict(extra="forbid")

    resource_type_id: int | None = None
    provider: str | None = Field(default=None, max_length=100)
    account_identifier: str | None = Field(default=None, max_length=200)
    plan_name: str | None = Field(default=None, max_length=100)
    status: str | None = None
    purchased_at: date | None = None
    activated_at: date | None = None
    expires_at: date | None = None
    remark: str | None = None


class ResourceUsageProject(BaseModel):
    id: int
    name: str
    project_code: str


class ResourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_name: str
    resource_type: ResourceTypeBrief
    provider: str | None
    account_identifier: str | None
    plan_name: str | None
    status: str
    purchased_at: date | None
    activated_at: date | None
    expires_at: date | None
    remark: str | None = None
    is_expiring_soon: bool = False
    is_shared: bool = False
    active_user_count: int = 0
    active_project_count: int = 0
    usage_projects: list[ResourceUsageProject] = []
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime


class ResourceListResponse(BaseModel):
    items: list[ResourcePublic]
    total: int
    page: int
    page_size: int


class ResourceAllocationCreate(BaseModel):
    project_id: int | None = None
    employee_id: int | None = None
    allocated_at: datetime | None = None
    remark: str | None = None


class ResourceAllocationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_account_id: int
    project_id: int | None
    project_name: str | None = None
    project_code: str | None = None
    employee_id: int | None
    employee_name: str | None = None
    employee_no: str | None = None
    allocated_at: datetime
    released_at: datetime | None
    is_active: bool
    remark: str | None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime


class ResourceAllocationListResponse(BaseModel):
    items: list[ResourceAllocationPublic]
    total: int
    page: int
    page_size: int
