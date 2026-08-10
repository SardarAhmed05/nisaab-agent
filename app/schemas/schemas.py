from pydantic import BaseModel, Field
from datetime import date, datetime

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: int = Field(..., gt=0)

class ChatResponse(BaseModel):
    response: str
    conversation_id: int


class ChatConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryMessage(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


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
