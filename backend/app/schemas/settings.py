from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SystemSettingsPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_name: str
    default_currency: str
    business_timezone: str
    expiring_days: int
    page_size_default: int
    updated_by: int | None = None
    updated_at: datetime | None = None


class SystemSettingsUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    default_currency: str | None = None
    business_timezone: str | None = Field(default=None, min_length=1, max_length=64)
    expiring_days: int | None = Field(default=None, ge=1, le=365)
    page_size_default: int | None = Field(default=None, ge=5, le=100)
