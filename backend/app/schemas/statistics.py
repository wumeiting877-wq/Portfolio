from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def _money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


class AmountByCurrency(BaseModel):
    currency: str
    amount: Decimal

    @field_serializer("amount")
    def _amount(self, value: Decimal) -> str:
        return format(value, "f")


class OverviewResponse(BaseModel):
    amounts_by_currency: dict[str, str]
    project_count: int | None = None
    employee_count: int | None = None
    resource_count: int | None = None
    active_resource_count: int | None = None
    idle_resource_count: int | None = None
    unassigned_active_resource_count: int | None = None
    expired_resource_count: int | None = None
    expiring_soon_count: int | None = None
    my_project_count: int | None = None
    my_resource_count: int | None = None
    my_expiring_resource_count: int | None = None


class TrendPoint(BaseModel):
    period: str
    currency: str
    amount: Decimal

    @field_serializer("amount")
    def _amount(self, value: Decimal) -> str:
        return format(value, "f")


class ExpenseTrendResponse(BaseModel):
    series: list[TrendPoint]


class ProjectCostItem(BaseModel):
    project_id: int
    project_name: str
    currency: str
    allocated_amount: Decimal

    @field_serializer("allocated_amount")
    def _amount(self, value: Decimal) -> str:
        return format(value, "f")


class ProjectCostResponse(BaseModel):
    items: list[ProjectCostItem]


class EmployeeCostItem(BaseModel):
    employee_id: int
    employee_name: str
    employee_no: str | None = None
    currency: str
    allocated_amount: Decimal

    @field_serializer("allocated_amount")
    def _amount(self, value: Decimal) -> str:
        return format(value, "f")


class ProjectPublicCostItem(BaseModel):
    project_id: int
    project_name: str
    currency: str
    allocated_amount: Decimal

    @field_serializer("allocated_amount")
    def _amount(self, value: Decimal) -> str:
        return format(value, "f")


class EmployeeCostResponse(BaseModel):
    items: list[EmployeeCostItem]
    project_public_costs: list[ProjectPublicCostItem] = Field(default_factory=list)


class ResourceTypeCostItem(BaseModel):
    resource_type_id: int | None = None
    resource_type_code: str
    resource_type_name: str
    currency: str
    allocated_amount: Decimal

    @field_serializer("allocated_amount")
    def _amount(self, value: Decimal) -> str:
        return format(value, "f")


class ResourceTypeCostResponse(BaseModel):
    items: list[ResourceTypeCostItem]


class BillingCostItem(BaseModel):
    billing_mode: str
    category: str
    currency: str
    allocated_amount: Decimal

    @field_serializer("allocated_amount")
    def _amount(self, value: Decimal) -> str:
        return format(value, "f")


class BillingCostResponse(BaseModel):
    items: list[BillingCostItem]


class ResourceStatusBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_name: str
    status: str
    expires_at: date | None = None
    resource_type_name: str | None = None
    days_remaining: int | None = None


class ResourceStatusResponse(BaseModel):
    counts: dict[str, int]
    explicit_idle_count: int
    unassigned_active_count: int
    idle_resources: list[ResourceStatusBrief] = Field(default_factory=list)
    unassigned_active_resources: list[ResourceStatusBrief] = Field(default_factory=list)


class ExpiringResourceResponse(BaseModel):
    days: int
    items: list[ResourceStatusBrief]
