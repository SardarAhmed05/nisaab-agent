from datetime import date as date_type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func

from app.db.models import Transaction

async def create_transaction(
    session: AsyncSession,
    amount: float,
    type: str,
    category: str,
    description: str,
    date: date_type,
    source: str | None = None,
    confidence: str = "confirmed",
) -> Transaction:
    txn = Transaction(
        amount=amount,
        type=type,
        category=category,
        description=description,
        date=date,
        source=source,
        confidence=confidence,
    )
    session.add(txn)
    await session.commit()
    await session.refresh(txn)
    return txn

async def get_transactions(
        session: AsyncSession,
        category: str | None = None,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        limit: int = 10,
) -> list[Transaction]:
    stmt = select(Transaction)

    if category:
        stmt = stmt.where(Transaction.category == category)
    if date_from:
        stmt = stmt.where(Transaction.date >= date_from)
    if date_to:
        stmt = stmt.where(Transaction.date <= date_to)

    stmt = stmt.order_by(Transaction.date.desc()).limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_balance(
        session: AsyncSession,
) -> float:
    income_sum = select(func.sum(Transaction.amount)).where(Transaction.type == "income")
    expense_sum = select(func.sum(Transaction.amount)).where(Transaction.type == "expense")
    
    income = (await session.execute(income_sum)).scalar() or 0.0
    expense = (await session.execute(expense_sum)).scalar() or 0.0
    return income - expense

async def get_total_expenses(
    session: AsyncSession,
    category: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
) -> float:
    expense_sum = select(func.sum(Transaction.amount)).where(Transaction.type == "expense")

    if category:
        expense_sum = expense_sum.where(Transaction.category == category)
    if date_from:
        expense_sum = expense_sum.where(Transaction.date >= date_from)
    if date_to:
        expense_sum = expense_sum.where(Transaction.date <= date_to)

    expense = (await session.execute(expense_sum)).scalar() or 0.0
    return expense

async def get_transaction_by_id(
    session: AsyncSession,
    txn_id: int
) -> Transaction | None:
    txn = select(Transaction).where(Transaction.id == txn_id)
    txn = await session.execute(txn)
    return txn.scalar_one_or_none()

async def update_transaction(
    session: AsyncSession,
    txn_id: int,
    fields: dict
) -> Transaction | None:
    txn = await get_transaction_by_id(session, txn_id)
    if txn is None:
            return None
    
    for key, value in fields.items():
        setattr(txn, key, value)

    await session.commit()
    await session.refresh(txn)
    return txn

async def delete_transaction(
    session: AsyncSession,
    txn_id: int
) -> bool:
    txn = await get_transaction_by_id(session, txn_id)
    if txn:
        await session.delete(txn)
        await session.commit()
        return True
    else:   
        return False
        


