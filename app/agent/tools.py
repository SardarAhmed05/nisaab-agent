from langchain_core.tools import tool
from app.db import crud
from app.db.session import AsyncSessionLocal
from datetime import date as date_type

# PHASE 1

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
    """Add a new income or expense transaction to the ledger. The category must describe 
the actual source (for income) or purpose (for expense) — e.g. 'freelance', 'allowance', 
'food', 'groceries', 'transport'. Never use the transaction's own type ('income' or 'expense') 
as the category. Even if a category seems obvious, always call search_transaction first to check 
whether a similar category already exists (e.g. don't create 'chai' as its own category if 'food' 
already covers casual food/drink purchases) — reuse the existing category instead of creating a 
near-duplicate. Only ask the user if search_transaction shows no reasonable existing match."""
    category = category.lower()
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

    category = category.lower() if category else None
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
    """
Get the user's current balance.

Use this tool whenever the user asks about:
- remaining money
- money left for the month
- available funds
- spending capacity
- budget planning
- affordability
"""
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
        

# PHASE 2

@tool
async def get_category_summary(
    cat_type: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """Get a breakdown of totals grouped by category, for a given transaction type 
("expense" or "income"). Use this to answer questions like "where's my money going" 
(type="expense") or "where's my income coming from" (type="income"). Optionally filter 
by a date range (date_from, date_to, in YYYY-MM-DD format). Unlike get_total_expenses, 
which returns one single total, this returns a separate total for each category."""

    parsed_date_from = date_type.fromisoformat(date_from) if date_from else None
    parsed_date_to = date_type.fromisoformat(date_to) if date_to else None
    async with AsyncSessionLocal() as session:
        result = await crud.get_category_summary(
            session=session,
            type=cat_type,
            date_from=parsed_date_from,
            date_to=parsed_date_to
        )
        return f"Breakdown by category: ({cat_type}): {result}"
    

# PHASE 3

@tool
async def create_budget(
    end_date: str,
    limit_amount: float,
    start_date: str | None = None,
    category: str | None = None
) -> str:  
    """Create a budget with a given category, if there is no category provided, leave it as None
    and assume its an overall budget. If start_date is not given, add it as today's date.
    If end_date is not provided, infer the duration from the user's instruction. For weekly, monthly, or multi-day budgets, calculate the end_date from the start_date, not from calendar boundaries.
    Example: a 1-week budget starting on 2026-07-19 ends on 2026-07-26.
    If you are unable, ask them. Budget should be
    created with four parameters, start date, end date, limit amount and category
    If setting a category-specific budget, reuse the exact existing transaction category name. 
    Do not invent capitalization, singular/plural, or spelling variations.
    If its entirely a new category, create it"""
    if start_date is None:
        parsed_start_date = date_type.today()
    else:
        parsed_start_date = date_type.fromisoformat(start_date)

    parsed_end_date = date_type.fromisoformat(end_date)

    category = category.lower() if category else None
    async with AsyncSessionLocal() as session:
        budget = await crud.create_budget(
            session,
            limit_amount=limit_amount,
            category=category,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return f"Added budget: {budget.limit_amount} PKR for category '{budget.category}' from {budget.start_date} to {budget.end_date} (id={budget.id})"
    

@tool
async def get_active_budgets(
    category: str | None = None
) -> str:
    """Find the currently active budget for a given category, 
    or the overall budget if no category is given. Returns the 
    budget's id, which is needed before calling update_budget or delete_budget."""
    category = category.lower() if category else None
    async with AsyncSessionLocal() as session:
        budgets = await crud.get_active_budgets(
            session,
            category
        )

    if not budgets:
        return "No Budgets found"
    else:
        budget = budgets[0]
        
    return f"Budget (id: {budget.id}) found with category: {budget.category}, Started on {budget.start_date} and ends on {budget.end_date} with limit: {budget.limit_amount}"

@tool
async def get_all_active_budgets() -> str:
    """Return a budget or a list of active budgets"""
    async with AsyncSessionLocal() as session:
        budgets = await crud.get_all_active_budgets(session)
    
    if not budgets:
        return "No Active Budgets Found"
    else:
        lines = lines = [
    f"Category: {b.category or 'Overall'}, Limit: {b.limit_amount}, Start: {b.start_date}, End: {b.end_date} (id={b.id})"
    for b in budgets
    ]
        return "\n".join(lines)

@tool
async def update_budget(
    budget_id: int,
    limit_amount: float | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
) -> str :
    """Update a budget by its id. If you dont already know the budget's id,
    use get_active_budgets tool first to find it. Only include the parameters you want to change; 
    anything left unspecified stays the same"""
    
    category = category.lower() if category else None
    parsed_start_date = date_type.fromisoformat(start_date) if start_date else None
    parsed_end_date = date_type.fromisoformat(end_date) if end_date else None
    fields = {
        "limit_amount": limit_amount,
        "start_date": parsed_start_date,
        "end_date": parsed_end_date,
        "category": category
    }

    fields = {k: v for k, v in fields.items() if v is not None}
    async with AsyncSessionLocal() as session:
        updated_budget = await crud.update_budget(
            session=session,
            budget_id=budget_id,
            fields=fields
        )
        if updated_budget:
            return f"Budget successfully updated. Updated Budget: {updated_budget}"
        else:
            return "Budget not found"
        
@tool
async def delete_budget(budget_id: int) -> str:
    """Delete a budget by its id. If you don't already know 
    the budget's id, use get_active_budgets first to find it."""
    
    async with AsyncSessionLocal() as session:
        result = await crud.delete_budget(session, budget_id)
        if result:
            return "Budget Deleted Successfully from ledger"
        else:
            return "Budget not found"
        
@tool
async def get_budget_status(category: str | None = None) -> str:
    """Return a budget's current status — limit, amount spent, remaining amount, and percentage used —
for a given category, or the overall budget if no category is given. This tool automatically uses
the budget's own actual start_date and end_date (which may not match the calendar month — a budget
can start on any day and run for any length of time, e.g. 3 days, a week, or 6 months). This is the
single correct tool for answering "how much have I spent against my budget" or "how am I doing on
my budget" — do not call get_total_expenses separately to check budget progress, since that requires
guessing the correct date range yourself and will likely use the wrong period (e.g. calendar month)
instead of the budget's actual dates. If no active budget exists for the category, this tool will
say so clearly."""

    category = category.lower() if category else None
    async with AsyncSessionLocal() as session:
        status = await crud.get_budget_status(session, category)

    if status:
        return (
            f"Budget Status\n"
            f"Limit: PKR {status['limit']}\n"
            f"Spent: PKR {status['spent']}\n"
            f"Remaining: PKR {status['limit'] - status['spent']}\n"
            f"Used: {status['percentage_used']}%"
        )
    else:
        return "No active budget found for this category"