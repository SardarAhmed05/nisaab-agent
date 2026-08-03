from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.crud import get_analytics_summary
from app.auth.dependencies import get_current_user
from app.schemas.schemas import AnalyticsSummaryResponse

router = APIRouter()


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    summary = await get_analytics_summary(
        session,
        user_id
    )

    return summary