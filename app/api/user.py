from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.db.models import User
from app.auth.dependencies import get_current_user


router = APIRouter()


@router.get("/me")
async def get_me(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    result = await session.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one()


    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at
    }