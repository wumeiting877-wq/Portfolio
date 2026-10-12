from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    project_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    manager_employee_id: int
    status: str = "PLANNING"
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectUpdate(BaseModel):
    """Ordinary edit. project_code is not a field and is rejected if sent."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    manager_employee_id: int | None = None
    status: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectCodeChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_project_code: str


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_code: str
    name: str
    description: str | None
    manager_employee_id: int
    manager_name: str | None = None
    manager_employee_no: str | None = None
    status: str
    start_date: date | None
    end_date: date | None
    member_count: int = 0
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectPublic]
    total: int
    page: int
    page_size: int


class ProjectMemberCreate(BaseModel):
    employee_id: int
    member_role: str | None = "MEMBER"


class ProjectMemberUpdate(BaseModel):
    member_role: str | None = None


class ProjectMemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    employee_id: int
    employee_no: str | None = None
    name: str | None = None
    department: str | None = None
    position: str | None = None
    member_role: str
    joined_at: datetime
    left_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
