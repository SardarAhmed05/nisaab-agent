# app/db/models.py
from sqlalchemy import String, Float, Date, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from datetime import date, datetime, timedelta

class Base(DeclarativeBase):
    pass

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)          # "expense" | "income"
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "dad", "freelance"
    date: Mapped[date] = mapped_column(Date, nullable=False)
    confidence: Mapped[str] = mapped_column(String(10), default="confirmed")  # "confirmed" | "estimated"
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Transaction {self.id} {self.type} {self.amount} {self.category} {self.description} {self.source} {self.created_at + timedelta(hours=5)} {self.date} {self.confidence}>"
    

class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    limit_amount: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Budget {self.id} {self.category} {self.limit_amount} {self.start_date} {self.end_date} {self.created_at + timedelta(hours=5)} >"
    
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(25), nullable=True, unique=True)
    name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<User {self.id} {self.name} {self.username} {self.created_at + timedelta(hours=5)} >"
    
class UserIdentity(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
    UniqueConstraint("platform", "platform_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    platform_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<UserIdentity {self.id} {self.user_id} {self.platform} {self.platform_id} {self.created_at + timedelta(hours=5)} >"
    
