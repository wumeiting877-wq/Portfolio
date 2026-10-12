from pydantic import BaseModel


class ImpactItem(BaseModel):
    label: str
    count: int


class IdentifierImpact(BaseModel):
    items: list[ImpactItem]
