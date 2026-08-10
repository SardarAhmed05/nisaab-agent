from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import ChatConversationResponse, ChatHistoryMessage, ChatRequest, ChatResponse
from app.agent.graph import app
from app.auth.dependencies import get_current_user
from app.db.crud import (
    create_chat_conversation,
    create_chat_messages,
    delete_chat_conversation,
    get_chat_conversation,
    get_chat_conversations,
    get_chat_messages,
)
from app.db.session import AsyncSessionLocal
from groq import RateLimitError

from langchain_core.messages import AIMessage, HumanMessage
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/chat/conversations", response_model=list[ChatConversationResponse])
async def chat_conversations(user_id: int = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        return await get_chat_conversations(session, user_id)


@router.post("/chat/conversations", response_model=ChatConversationResponse)
async def create_conversation(user_id: int = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        return await create_chat_conversation(session, user_id)


@router.get(
    "/chat/conversations/{conversation_id}/messages",
    response_model=list[ChatHistoryMessage],
)
async def chat_history(
    conversation_id: int,
    user_id: int = Depends(get_current_user),
):
    async with AsyncSessionLocal() as session:
        conversation = await get_chat_conversation(session, user_id, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return await get_chat_messages(session, user_id, conversation_id)


@router.delete("/chat/conversations/{conversation_id}", status_code=204)
async def remove_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user),
):
    async with AsyncSessionLocal() as session:
        deleted = await delete_chat_conversation(session, user_id, conversation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")


@router.post(
    "/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_user)
):

    try:
        async with AsyncSessionLocal() as session:
            conversation = await get_chat_conversation(
                session, user_id, request.conversation_id
            )
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found")

        config = {
            "configurable": {
                "thread_id": f"web:{user_id}:{conversation.id}"
            }
        }
        messages = [HumanMessage(content=request.message)]
        snapshot = await app.aget_state(config)

        # MemorySaver is process-local. Rebuild a new thread from durable
        # history only after a restart, avoiding duplicate messages in an
        # already-active graph thread.
        if not snapshot.values.get("messages"):
            async with AsyncSessionLocal() as session:
                history = await get_chat_messages(session, user_id, conversation.id)
            messages = [
                HumanMessage(content=message.content)
                if message.role == "user"
                else AIMessage(content=message.content)
                for message in history
            ] + messages

        state = {
            "messages": messages,
            "user_id": user_id,
            "platform": "web",
            "platform_id": str(user_id),
            "confirmed": False,
        }

        result = await app.ainvoke(
            state,
            config=config,
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

        async with AsyncSessionLocal() as session:
            await create_chat_messages(
                session,
                user_id,
                conversation.id,
                [("user", request.message), ("assistant", response)],
            )

        return {
            "response": response,
            "conversation_id": conversation.id,
        }
    
    except HTTPException:
        raise

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
