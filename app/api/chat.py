from fastapi import APIRouter, Depends
from app.schemas.schemas import ChatRequest, ChatResponse
from app.agent.graph import app
from app.auth.dependencies import get_current_user
from groq import RateLimitError

from langchain_core.messages import HumanMessage
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_user)
):

    state = {
        "messages": [
            HumanMessage(content=request.message)
        ],

        "user_id": user_id,

        "platform": "web",

        "platform_id": str(user_id),

        "confirmed": False
    }


    try:
        result = await app.ainvoke(
            state,
            config={
                "configurable": {
                    "thread_id": str(user_id)
                }
            }
        )


        messages = result.get("messages", [])

        if not messages:
            return {
                "response": (
                    "I'm sorry, but I couldn't generate a response. "
                    "Please try again."
                )
            }

        final_message = messages[-1]

        response = getattr(final_message, "content", "")

        if isinstance(response, list):
            response = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in response
            )

        response = str(response).strip()

        if not response:
            response = (
                "I'm sorry, but I couldn't generate a response. "
                "Please try asking again."
            )

        return {
            "response": response
        }
    
    except RateLimitError:
        return {
            "response": (
                "Nisaab is temporarily unavailable because the AI service has "
                "reached its usage limit. Please try again in a few minutes."
            )
        }

    except Exception:
        logger.exception("Chat endpoint failed")
        return {
            "response": (
                "Sorry, something went wrong while processing your request. "
                "Please try again."
            )
        }