from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def _money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class ExpenseTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    category: str = "OTHER"
    description: str | None = None


class ExpenseTypeUpdate(BaseModel):
    """Ordinary edit. code is not a field and is rejected if sent."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = None
    description: str | None = None


class ExpenseTypeCodeChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_code: str


class ExpenseTypePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ExpenseTypeBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str


class ExpenseDistributionInput(BaseModel):
    project_id: int | None = None
    employee_id: int | None = None
    allocation_method: str = "DIRECT"
    allocation_ratio: Decimal | None = None
    allocated_amount: Decimal | None = None

    @field_validator("allocation_ratio", "allocated_amount", mode="before")
    @classmethod
    def _decimal_fields(cls, value: Any) -> Decimal | None:
        return _parse_decimal(value)


class ExpenseDistributionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_record_id: int
    project_id: int | None
    project_name: str | None = None
    project_code: str | None = None
    employee_id: int | None
    employee_name: str | None = None
    employee_no: str | None = None
    allocation_method: str
    allocation_ratio: Decimal | None = None
    allocated_amount: Decimal
    created_at: datetime
    updated_at: datetime

    @field_serializer("allocation_ratio", "allocated_amount")
    def _ser_decimal(self, value: Decimal | None) -> str | None:
        return _money(value)


class ExpenseCreate(BaseModel):
    expense_type_id: int
    resource_account_id: int | None = None
    billing_mode: str
    source: str = "MANUAL"
    expense_date: date
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    amount: Decimal
    currency: str
    usage_quantity: Decimal | None = None
    usage_unit: str | None = Field(default=None, max_length=50)
    unit_price: Decimal | None = None
    description: str | None = None
    external_reference: str | None = Field(default=None, max_length=200)
    distributions: list[ExpenseDistributionInput]

    @field_validator("amount", "usage_quantity", "unit_price", mode="before")
    @classmethod
    def _decimal_fields(cls, value: Any) -> Decimal | None:
        return _parse_decimal(value)


class ExpenseUpdate(BaseModel):
    expense_type_id: int | None = None
    resource_account_id: int | None = None
    billing_mode: str | None = None
    expense_date: date | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    amount: Decimal | None = None
    currency: str | None = None
    usage_quantity: Decimal | None = None
    usage_unit: str | None = Field(default=None, max_length=50)
    unit_price: Decimal | None = None
    description: str | None = None
    external_reference: str | None = Field(default=None, max_length=200)
    distributions: list[ExpenseDistributionInput] | None = None

    @field_validator("amount", "usage_quantity", "unit_price", mode="before")
    @classmethod
    def _decimal_fields(cls, value: Any) -> Decimal | None:
        return _parse_decimal(value)


class ExpensePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_type: ExpenseTypeBrief
    resource_account_id: int | None = None
    resource_name: str | None = None
    billing_mode: str
    source: str
    expense_date: date
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    amount: Decimal
    visible_allocated_amount: Decimal
    original_amount_visible: bool
    currency: str
    usage_quantity: Decimal | None = None
    usage_unit: str | None = None
    unit_price: Decimal | None = None
    description: str | None = None
    external_reference: str | None = None
    status: str
    recurring_rule_id: int | None = None
    visible_attribution: str | None = None
    distributions: list[ExpenseDistributionPublic] = []
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer(
        "amount",
        "visible_allocated_amount",
        "usage_quantity",
        "unit_price",
    )
    def _ser_decimal(self, value: Decimal | None) -> str | None:
        return _money(value)


class ExpenseListResponse(BaseModel):
    items: list[ExpensePublic]
    total: int
    page: int
    page_size: int


class RecurringRuleDistributionInput(BaseModel):
    project_id: int | None = None
    employee_id: int | None = None
    allocation_method: str = "DIRECT"
    allocation_ratio: Decimal | None = None
    allocated_amount: Decimal | None = None

    @field_validator("allocation_ratio", "allocated_amount", mode="before")
    @classmethod
    def _decimal_fields(cls, value: Any) -> Decimal | None:
        return _parse_decimal(value)


class RecurringRuleDistributionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_id: int
    project_id: int | None
    project_name: str | None = None
    project_code: str | None = None
    employee_id: int | None
    employee_name: str | None = None
    employee_no: str | None = None
    allocation_method: str
    allocation_ratio: Decimal | None = None
    allocated_amount: Decimal | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("allocation_ratio", "allocated_amount")
    def _ser_decimal(self, value: Decimal | None) -> str | None:
        return _money(value)


class RecurringRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    expense_type_id: int
    resource_account_id: int | None = None
    frequency: str
    amount: Decimal
    currency: str
    start_date: date
    end_date: date | None = None
    next_run_date: date | None = None
    default_distribution_mode: str = "DIRECT"
    description: str | None = None
    distributions: list[RecurringRuleDistributionInput]

    @field_validator("amount", mode="before")
    @classmethod
    def _decimal_fields(cls, value: Any) -> Decimal | None:
        return _parse_decimal(value)


class RecurringRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    expense_type_id: int | None = None
    resource_account_id: int | None = None
    frequency: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    next_run_date: date | None = None
    default_distribution_mode: str | None = None
    description: str | None = None
    distributions: list[RecurringRuleDistributionInput] | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def _decimal_fields(cls, value: Any) -> Decimal | None:
        return _parse_decimal(value)


class RecurringRulePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    expense_type: ExpenseTypeBrief
    resource_account_id: int | None = None
    resource_name: str | None = None
    frequency: str
    amount: Decimal
    currency: str
    start_date: date
    end_date: date | None = None
    next_run_date: date
    is_active: bool
    default_distribution_mode: str
    description: str | None = None
    distributions: list[RecurringRuleDistributionPublic] = []
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount")
    def _ser_amount(self, value: Decimal) -> str:
        return format(value, "f")


class RecurringGenerateResult(BaseModel):
    generated_count: int
    skipped_count: int
    generated_ids: list[int]


class SuggestedDistribution(BaseModel):
    project_id: int | None = None
    project_name: str | None = None
    employee_id: int | None = None
    employee_name: str | None = None
    allocation_method: str
    allocation_ratio: Decimal | None = None
    allocated_amount: Decimal

    @field_serializer("allocation_ratio", "allocated_amount")
    def _ser_decimal(self, value: Decimal | None) -> str | None:
        return _money(value)
