from datetime import date

from pydantic import BaseModel


class TargetGenerateRequest(BaseModel):
    period: str = "monthly"
    entity_type: str = "product"


class SalesHistoryIngestRequest(BaseModel):
    sales_date: date
    product_id: int
    customer_id: int
    quantity: float
    revenue: float
    branch_id: int
