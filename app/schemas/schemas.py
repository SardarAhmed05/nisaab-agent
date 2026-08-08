from pydantic import BaseModel, Field
from datetime import date, datetime

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    response: str


class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    description: str
    date: date
    created_at: datetime | None = None
    user_id: int
    source: str | None = None
    confidence: str

    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    user_id: int
    balance: float
    currency: str

class AnalyticsSummaryResponse(BaseModel):
    balance: float
    income: float
    expenses: float
    category_breakdown: dict[str, float]


class UserResponse(BaseModel):
    id: int
    username: str | None
    email: str | None

    class Config:
        from_attributes = True