# tests/test_crud_manual.py
import asyncio
from datetime import date

from app.db.session import AsyncSessionLocal
from app.db import crud


async def main():
    async with AsyncSessionLocal() as session:
        # Resolve a test user (created on first run, reused afterwards).
        user = await crud.get_or_create_user(session, platform="cli", platform_id="crud-test-user")
        user_id = user.id
        print("User:", user)

        # Create
        txn = await crud.create_transaction(
            session,
            user_id=user_id,
            amount=700,
            type="expense",
            category="food",
            description="lunch",
            date=date.today(),
        )
        print("Created:", txn)

        # Balance after creating one expense
        balance = await crud.get_balance(session, user_id=user_id)
        print("Balance after expense:", balance)

        # Add an income too
        await crud.create_transaction(
            session,
            user_id=user_id,
            amount=5000,
            type="income",
            category="allowance",
            description="from dad",
            date=date.today(),
            source="dad",
        )
        balance = await crud.get_balance(session, user_id=user_id)
        print("Balance after income:", balance)

        # Read back recent transactions
        recent = await crud.get_transactions(session, user_id=user_id, limit=5)
        print("Recent:", recent)

        # Update the first transaction
        updated = await crud.update_transaction(session, user_id, txn.id, {"amount": 850})
        print("Updated:", updated)

        # Delete it
        deleted = await crud.delete_transaction(session, user_id, txn.id)
        print("Deleted:", deleted)

        # Confirm it's gone
        gone = await crud.get_transaction_by_id(session, user_id, txn.id)
        print("Should be None:", gone)


asyncio.run(main())
