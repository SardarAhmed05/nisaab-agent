from fastapi import APIRouter, Depends
from app.schemas.schemas import ChatRequest, ChatResponse
from app.agent.graph import app
from app.auth.dependencies import get_current_user

from langchain_core.messages import HumanMessage


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


    result = await app.ainvoke(
        state,
        config={
            "configurable": {
                "thread_id": str(user_id)
            }
        }
    )


    final_message = result["messages"][-1]


    return {
        "response": final_message.content
    }