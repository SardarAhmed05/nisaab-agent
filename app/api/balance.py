from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.crud import get_balance
from app.auth.dependencies import get_current_user
from app.schemas.schemas import BalanceResponse

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
async def balance(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    balance = await get_balance(
        session,
        user_id
    )

    return {
        "user_id": user_id,
        "balance": balance,
        "currency": "PKR"
    }