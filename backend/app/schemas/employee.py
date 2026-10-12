import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Same rule as the employee form and the import checker: blank is allowed.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_optional_email(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("请输入正确的邮箱地址")
    text = value.strip()
    if not text:
        return None
    if _EMAIL_RE.fullmatch(text) is None:
        raise ValueError("请输入正确的邮箱地址")
    return text


class EmployeeCreate(BaseModel):
    employee_no: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    department: str | None = None
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    remark: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, value: object) -> str | None:
        return normalize_optional_email(value)


class EmployeeUpdate(BaseModel):
    """Ordinary edit. employee_no is not a field and is rejected if sent."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    department: str | None = None
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    employment_status: str | None = None
    remark: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def _email(cls, value: object) -> str | None:
        return normalize_optional_email(value)


class EmployeeNoChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_employee_no: str


class EmployeePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_no: str
    name: str
    department: str | None
    position: str | None
    email: str | None
    phone: str | None
    employment_status: str
    remark: str | None
    has_account: bool = False
    created_at: datetime
    updated_at: datetime
