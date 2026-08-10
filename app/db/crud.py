from datetime import date as date_type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update
from sqlalchemy import func

from app.db.models import ChatConversation, ChatMessage, Transaction, Budget, User, UserIdentity, Notifications

# PHASE 1 CRUD

async def create_transaction(
    session: AsyncSession,
    user_id: int,
    amount: float,
    type: str,
    category: str,
    description: str,
    date: date_type,
    source: str | None = None,
    confidence: str = "confirmed",
) -> Transaction:
    txn = Transaction(
        user_id=user_id,
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
        user_id: int,
        category: str | None = None,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        limit: int = 10,
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.user_id==user_id)

    if category:
        stmt = stmt.where(Transaction.category.ilike(f"%{category}%"))
    if date_from:
        stmt = stmt.where(Transaction.date >= date_from)
    if date_to:
        stmt = stmt.where(Transaction.date <= date_to)

    stmt = stmt.order_by(Transaction.date.desc()).limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_balance(
        session: AsyncSession,
        user_id: int,
) -> float:
    income_sum = select(func.sum(Transaction.amount)).where(Transaction.user_id==user_id) 
    income_sum = income_sum.where(Transaction.type == "income")
    expense_sum = select(func.sum(Transaction.amount)).where(Transaction.user_id==user_id)
    expense_sum = expense_sum.where(Transaction.type == "expense")
    
    income = (await session.execute(income_sum)).scalar() or 0.0
    expense = (await session.execute(expense_sum)).scalar() or 0.0
    return income - expense

async def get_total_expenses(
    session: AsyncSession,
    user_id: int,
    category: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
) -> float:
    expense_sum = select(func.sum(Transaction.amount)).where(Transaction.user_id==user_id)
    expense_sum = expense_sum.where(Transaction.type == "expense")
    
    if category:
        expense_sum = expense_sum.where(Transaction.category == category)
    if date_from:
        expense_sum = expense_sum.where(Transaction.date >= date_from)
    if date_to:
        expense_sum = expense_sum.where(Transaction.date <= date_to)

    expense = (await session.execute(expense_sum)).scalar() or 0.0
    return expense

async def get_total_income(
    session: AsyncSession,
    user_id: int,
    category: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
) -> float:
    income_sum = select(func.sum(Transaction.amount)).where(Transaction.user_id==user_id)
    income_sum = income_sum.where(Transaction.type == "income")
    
    if category:
        income_sum = income_sum.where(Transaction.category == category)
    if date_from:
        income_sum = income_sum.where(Transaction.date >= date_from)
    if date_to:
        income_sum = income_sum.where(Transaction.date <= date_to)

    income = (await session.execute(income_sum)).scalar() or 0.0
    return income


async def get_transaction_by_id(
    session: AsyncSession,
    user_id: int,
    txn_id: int
) -> Transaction | None:
    txn = select(Transaction).where(Transaction.id == txn_id, Transaction.user_id == user_id)
    txn = await session.execute(txn)
    return txn.scalar_one_or_none()

async def update_transaction(
    session: AsyncSession,
    user_id: int,
    txn_id: int,
    fields: dict
) -> Transaction | None:
    txn = await get_transaction_by_id(session, user_id, txn_id)
    if txn is None:
            return None
    
    for key, value in fields.items():
        setattr(txn, key, value)

    await session.commit()
    await session.refresh(txn)
    return txn

async def delete_transaction(
    session: AsyncSession,
    user_id: int,
    txn_id: int
) -> bool:
    txn = await get_transaction_by_id(session, user_id, txn_id)
    if txn:
        await session.delete(txn)
        await session.commit()
        return True
    else:   
        return False
        
# PHASE 2 CRUD

async def get_category_summary (
        session: AsyncSession,
        user_id: int,
        type: str,
        date_from: date_type | None = None,
        date_to: date_type | None = None
) -> dict:
    stmt = select(Transaction.category, func.sum(Transaction.amount)).where(Transaction.type == type, Transaction.user_id==user_id).group_by(Transaction.category)

    if date_from:
        stmt = stmt.where(Transaction.date >= date_from)
    if date_to:
        stmt = stmt.where(Transaction.date <= date_to)

    result = await session.execute(stmt)
    rows = result.all()
    return dict(rows)

async def get_analytics_summary(
    session: AsyncSession,
    user_id: int,
) -> dict:
    balance = await get_balance(session, user_id)
    income = await get_total_income(session, user_id)
    expenses = await get_total_expenses(session, user_id)
    category_breakdown = await get_category_summary(session, user_id, type="expense")

    return {
        "balance": balance,
        "income": income,
        "expenses": expenses,
        "category_breakdown": category_breakdown,
    }

# PHASE 3

async def create_budget(
    session: AsyncSession,
    user_id: int,
    limit_amount: float,
    start_date: date_type,
    end_date: date_type,
    category: str | None = None
) -> Budget:
    budget = Budget(
        user_id=user_id,
        limit_amount=limit_amount,
        start_date=start_date,
        end_date=end_date,
        category=category,
    )
    session.add(budget)
    await session.commit()
    await session.refresh(budget)
    return budget

async def get_active_budgets(
        session: AsyncSession,
        user_id: int,
        category: str | None = None,
) -> list[Budget]:
    today = date_type.today()
    if category is not None:
        query = select(Budget).where(Budget.category == category, Budget.start_date <= today, Budget.end_date >= today, Budget.user_id==user_id)
    else:
        query = select(Budget).where(Budget.category.is_(None), Budget.start_date <= today, Budget.end_date >= today, Budget.user_id==user_id)

    result = await session.execute(query)

    return list(result.scalars().all())

async def get_all_active_budgets(
        session: AsyncSession,
        user_id: int
) -> list[Budget]:
    today = date_type.today()
    query = select(Budget).where(Budget.start_date <= today, Budget.end_date >= today, Budget.user_id==user_id)

    result = await session.execute(query)
    return list(result.scalars().all())

async def get_budget_by_id(
    session: AsyncSession,
    user_id: int,
    budget_id: int
) -> Budget | None:
    budget = select(Budget).where(Budget.id == budget_id, Budget.user_id==user_id)
    budget = await session.execute(budget)
    return budget.scalar_one_or_none()

async def update_budget(
    session: AsyncSession,
    user_id: int,
    budget_id: int,
    fields: dict
) -> Budget | None:
    budget = await get_budget_by_id(session, user_id, budget_id)
    if budget is None:
            return None
    
    for key, value in fields.items():
        setattr(budget, key, value)

    await session.commit()
    await session.refresh(budget)
    return budget

async def delete_budget(
    session: AsyncSession,
    user_id: int,
    budget_id: int
) -> bool:
    budget = await get_budget_by_id(session, user_id, budget_id)
    if budget:
        await session.delete(budget)
        await session.commit()
        return True
    else:   
        return False
    
async def get_budget_status(
        session: AsyncSession,
        user_id: int,
        category: str | None = None,
) -> dict | None:
    budgets = await get_active_budgets(session, user_id, category)
    if not budgets:
        return None
    budget = budgets[0]

    limit = budget.limit_amount
    spent = await get_total_expenses(session, user_id, category=budget.category, date_from=budget.start_date, date_to=budget.end_date)
    percentage_used = round((spent/limit) * 100, 2) if limit > 0 else 0
    status = {"limit": limit, "spent": spent, "percentage_used": percentage_used}
    return status

# PHASE 3.5

async def get_or_create_user(
    session: AsyncSession,
    platform: str,
    platform_id: str,
    username: str | None = None,
    name: str | None = None
) -> User:
    query = select(UserIdentity).where(UserIdentity.platform == platform, UserIdentity.platform_id == platform_id)
    identity = await session.execute(query)
    identity = identity.scalar_one_or_none()

    if identity is not None:
        user_query = select(User).where(User.id == identity.user_id)
        user_result = await session.execute(user_query)
        return user_result.scalar_one_or_none()
    

    user = User(
        username=username,
        name=name
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user_identity = UserIdentity(
        user_id=user.id,
        platform=platform,
        platform_id=platform_id
    )
    session.add(user_identity)
    await session.commit()
    await session.refresh(user_identity)

    return user


async def create_chat_conversation(
    session: AsyncSession,
    user_id: int,
    title: str = "New chat",
) -> ChatConversation:
    conversation = ChatConversation(user_id=user_id, title=title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def get_chat_conversation(
    session: AsyncSession,
    user_id: int,
    conversation_id: int,
) -> ChatConversation | None:
    result = await session.execute(
        select(ChatConversation).where(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_chat_conversations(
    session: AsyncSession,
    user_id: int,
) -> list[ChatConversation]:
    result = await session.execute(
        select(ChatConversation)
        .where(ChatConversation.user_id == user_id)
        .order_by(ChatConversation.updated_at.desc(), ChatConversation.id.desc())
    )
    return list(result.scalars().all())


async def create_chat_messages(
    session: AsyncSession,
    user_id: int,
    conversation_id: int,
    messages: list[tuple[str, str]],
) -> None:
    conversation = await get_chat_conversation(session, user_id, conversation_id)
    if conversation is None:
        raise ValueError("Conversation does not belong to this user")

    session.add_all(
        ChatMessage(
            user_id=user_id,
            conversation_id=conversation.id,
            role=role,
            content=content,
        )
        for role, content in messages
    )
    values = {"updated_at": func.now()}
    if conversation.title == "New chat":
        values["title"] = messages[0][1].strip().replace("\n", " ")[:120] or "New chat"
    await session.execute(
        update(ChatConversation)
        .where(ChatConversation.id == conversation.id)
        .values(**values)
    )
    await session.commit()


async def get_chat_messages(
    session: AsyncSession,
    user_id: int,
    conversation_id: int,
) -> list[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(
            ChatMessage.user_id == user_id,
            ChatMessage.conversation_id == conversation_id,
        )
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
    )
    result = await session.execute(stmt)
    messages = list(result.scalars().all())
    messages.reverse()
    return messages


async def delete_chat_conversation(
    session: AsyncSession,
    user_id: int,
    conversation_id: int,
) -> bool:
    conversation = await get_chat_conversation(session, user_id, conversation_id)
    if conversation is None:
        return False

    await session.execute(
        delete(ChatMessage).where(
            ChatMessage.user_id == user_id,
            ChatMessage.conversation_id == conversation_id,
        )
    )
    await session.delete(conversation)
    await session.commit()
    return True

# PHASE 4

async def get_all_users(session: AsyncSession) -> list[User]:
    stmt = select(User)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def has_notification(
    session: AsyncSession,
    user_id: int,
    notification_type: str,
    reference_id:  int | None = None
) -> bool:
    notif = select(Notifications).where(Notifications.user_id == user_id,
    Notifications.notification_type == notification_type,   
    )

    if reference_id is not None:
        notif = notif.where(Notifications.reference_id == reference_id)

    result = await session.execute(notif)
    found = result.scalar_one_or_none()
    if found:
        return True
    else:
        return False

async def create_notification(
    session: AsyncSession,
    user_id: int,
    notification_type: str,
    reference_id:  int | None = None
) -> Notifications:
    notif = Notifications(
        user_id=user_id,
        notification_type=notification_type,
        reference_id=reference_id
    )

    session.add(notif)
    await session.commit()
    await session.refresh(notif)
    return notif
