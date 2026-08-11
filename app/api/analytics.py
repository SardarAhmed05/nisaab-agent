from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.crud import get_analytics_summary
from app.auth.dependencies import get_current_user
from app.schemas.schemas import AnalyticsSummaryResponse

from sqlalchemy import select
from app.db.models import User
from app.agent.tools import get_exchange_rate_to_pkr
from app.api.user import get_currency_symbol

router = APIRouter()


@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):

    user_res = await session.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    curr_code = (user.currency if user and user.currency else "PKR").upper()
    symbol = get_currency_symbol(curr_code)

    summary = await get_analytics_summary(
        session,
        user_id
    )

    if curr_code != "PKR":
        rate = get_exchange_rate_to_pkr(curr_code)
        if rate > 0:
            summary["balance"] = round(summary["balance"] / rate, 2)
            summary["income"] = round(summary["income"] / rate, 2)
            summary["expenses"] = round(summary["expenses"] / rate, 2)
            summary["category_breakdown"] = {
                cat: round(amt / rate, 2)
                for cat, amt in summary.get("category_breakdown", {}).items()
            }

    summary["currency"] = curr_code
    summary["currency_symbol"] = symbol

    return summary