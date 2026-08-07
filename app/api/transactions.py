from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.crud import get_transactions
from app.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/transactions")
async def transactions(
    limit: int = Query(default=10, ge=1, le=1000),
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    txns = await get_transactions(
        session,
        user_id,
        limit=limit
    )

    return txns