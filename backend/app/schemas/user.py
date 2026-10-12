from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RolePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    employee_id: int | None = None
    role_id: int


class UserUpdate(BaseModel):
    """Ordinary edit. username is not a field and is rejected if sent."""

    model_config = ConfigDict(extra="forbid")

    role_id: int | None = None
    employee_id: int | None = None
    status: str | None = None


class UsernameChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_username: str


class PasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class EmployeeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_no: str
    name: str
    department: str | None = None
    employment_status: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    employee_id: int | None
    role_id: int
    role_code: str
    role_name: str
    status: str
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    employee: EmployeeBrief | None = None
