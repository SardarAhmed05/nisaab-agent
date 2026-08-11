from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.db.models import User
from app.auth.dependencies import get_current_user


router = APIRouter()


CURRENCY_SYMBOL_MAP = {
    "PKR": "₨",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "SAR": "SAR ",
    "AED": "AED ",
    "CAD": "CA$",
    "AUD": "A$",
    "INR": "₹",
}

def get_currency_symbol(currency_code: str) -> str:
    return CURRENCY_SYMBOL_MAP.get((currency_code or "PKR").upper(), "₨")


@router.get("/me")
async def get_me(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    result = await session.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one()
    curr = user.currency or "PKR"

    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "currency": curr,
        "currency_symbol": get_currency_symbol(curr),
        "created_at": user.created_at
    }


@router.put("/user/currency")
async def update_currency(
    currency: str,
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.currency = currency.upper().strip()
        await session.commit()
        return {
            "message": "Currency updated",
            "currency": user.currency,
            "currency_symbol": get_currency_symbol(user.currency)
        }