from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    description: str = Field(..., example="Магнит продукты")
    amount: Decimal = Field(..., example=1500.50)
    date: datetime = Field(..., example="2025-06-01T12:00:00")


class TransactionRead(BaseModel):
    id: int
    description: str
    amount: Decimal
    date: datetime
    category: str
    model_confidence: Optional[float]

    class Config:
        orm_mode = True


class AnalyticsByCategory(BaseModel):
    category: str
    total_amount: Decimal
    count: int
    avg_amount: Decimal


class AnalyticsByMonth(BaseModel):
    month: str
    total_amount: Decimal
    count: int


class AnalyticsResponse(BaseModel):
    total_spent: Decimal
    transaction_count: int
    by_category: List[AnalyticsByCategory]
    by_month: List[AnalyticsByMonth]

