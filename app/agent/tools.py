from langchain_core.tools import tool
from app.db import crud
from app.db.session import AsyncSessionLocal
from datetime import date as date_type

@tool
async def add_transaction(
    amount: float, 
    type: str, 
    category: str, 
    description: str,
    date: str, 
    source: str | None = None,
    confidence: str = "confirmed"
) -> str:  
    """Add a new income or expense transaction to the ledger"""
    parsed_date = date_type.fromisoformat(date)

    async with AsyncSessionLocal() as session:
        txn = await crud.create_transaction(
            session,
            amount=amount,
            type=type,
            category=category,
            description=description,
            date=parsed_date,
            source=source,
            confidence=confidence)
        
        return f"Added {txn.type} of {txn.amount} in category '{txn.category}' on {txn.date} (id={txn.id})"

@tool 
async def search_transaction(
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10
) -> str:
    """Search past transactions. Optionally filter by category, and/or a 
    date range (date_from, date_to, in YYYY-MM-DD format). If no filters are given, 
    returns the most recent transactions."""

    parsed_date_from = date_type.fromisoformat(date_from) if date_from else None
    parsed_date_to = date_type.fromisoformat(date_to) if date_to else None
    async with AsyncSessionLocal() as session:
        txns = await crud.get_transactions(
            session=session,
            category=category,
            date_to=parsed_date_to,
            date_from=parsed_date_from,
            limit=limit
        )
        return f"Statement: {txns}"

@tool 
async def get_total_expenses(
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """Get total expenses (money spent), optionally filtered by category and/or a date range 
(date_from, date_to, in YYYY-MM-DD format). Use this when the user asks how much they've 
spent, not their balance. This is different from get_balance, which returns net balance 
(income minus expenses), not total spending."""

    parsed_date_from = date_type.fromisoformat(date_from) if date_from else None
    parsed_date_to = date_type.fromisoformat(date_to) if date_to else None
    async with AsyncSessionLocal() as session:
        total = await crud.get_total_expenses(
            session=session,
            category=category,
            date_to=parsed_date_to,
            date_from=parsed_date_from
        )
        return f"Expenses: {total}"

@tool
async def get_balance() -> str:
    """Get the current balance from the ledger"""
    async with AsyncSessionLocal() as session:
        balance = await crud.get_balance(session)
        return f"Balance: {balance}"
    
# MULTI-STEP AGENTIC REASONING
@tool
async def delete_transaction(txn_id: int) -> str:
    """Delete a single transaction by its id. If you don't already know 
    the transaction's id, use search_transaction first to find it."""
    
    async with AsyncSessionLocal() as session:
        result = await crud.delete_transaction(session, txn_id)
        if result:
            return "Transaction Deleted Successfully from ledger"
        else:
            return "Transaction failed to delete"
        
@tool
async def update_transaction(
    txn_id: int,
    amount: float | None = None,
    txn_type: str | None = None,
    category: str | None = None,
    description: str | None = None,
    date: str | None = None,
    source: str | None = None,
    confidence: str | None = None,
) -> str :
    """Update a single transaction by its id. If you dont already know the transaction's id,
    use search_transaction first to find it. Only inclde the parameters you want to change; 
    anything left unspecified stays the same"""
    
    parsed_date = date_type.fromisoformat(date) if date else None
    fields = {
        "amount": amount,
        "type": txn_type,
        "category": category,
        "description": description,
        "date": parsed_date,
        "source": source,
        "confidence": confidence
    }

    fields = {k: v for k, v in fields.items() if v is not None}
    async with AsyncSessionLocal() as session:
        updated_txn = await crud.update_transaction(
            session=session,
            txn_id=txn_id,
            fields=fields
        )
        if updated_txn:
            return f"Transaction succesfully updated. Updated Transaction: {updated_txn}"
        else:
            return "Failed to update transaction"
        
