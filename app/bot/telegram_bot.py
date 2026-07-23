# app/bot/telegram_bot.py
import os
import logging

import aiosqlite
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agent.graph import graph

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Path to the durable checkpoint store (conversation memory + pending interrupts).
CHECKPOINT_DB = os.environ.get("CHECKPOINT_DB", "app/db/checkpoints.db")

# Compiled graph with a persistent checkpointer. Built in post_init (needs the
# running event loop) so it survives restarts and doesn't lose in-flight
# confirmations the way an in-memory saver would.
agent_app = None


def _awaiting_confirmation(snapshot) -> bool:
    """True if this thread is paused on a confirmation interrupt.

    Derived from durable graph state (not an in-memory flag), so a restart
    mid-confirmation still routes the user's reply to Command(resume=...).
    """
    if getattr(snapshot, "interrupts", None):
        return True
    for task in getattr(snapshot, "tasks", ()):
        if getattr(task, "interrupts", None):
            return True
    return False


def _latest_reply(result) -> str | None:
    """Extract the last non-empty AI message to send back to the user."""
    for msg in reversed(result.get("messages", [])):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Guard against edited messages / captions / non-text updates slipping through.
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user_text = update.message.text
    config = {"configurable": {"thread_id": str(chat_id)}}
    logger.info("Received from %s: %s", chat_id, user_text)

    try:
        snapshot = await agent_app.aget_state(config)

        if _awaiting_confirmation(snapshot):
            result = await agent_app.ainvoke(Command(resume=user_text), config=config)
        else:
            result = await agent_app.ainvoke(
                {
                    "messages": [HumanMessage(content=user_text)],
                    "platform": "telegram",
                    "platform_id": str(chat_id),
                },
                config=config,
            )
    except Exception:
        logger.exception("Error while handling message from %s", chat_id)
        await update.message.reply_text(
            "Sorry, something went wrong on my end. Please try that again."
        )
        return

    if "__interrupt__" in result:
        question = result["__interrupt__"][0].value
        await update.message.reply_text(question)
        return

    reply = _latest_reply(result)
    if reply:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("Sorry, I didn't catch that. Could you rephrase?")


async def post_init(application: Application) -> None:
    """Open the durable checkpointer and compile the graph on the bot's loop."""
    global agent_app
    conn = await aiosqlite.connect(CHECKPOINT_DB)
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    agent_app = graph.compile(checkpointer=checkpointer)
    # Keep the connection alive for the process lifetime; closed in post_shutdown.
    application.bot_data["_checkpoint_conn"] = conn
    logger.info("Agent compiled with persistent checkpointer at %s", CHECKPOINT_DB)


async def post_shutdown(application: Application) -> None:
    conn = application.bot_data.get("_checkpoint_conn")
    if conn is not None:
        await conn.close()
        logger.info("Checkpoint connection closed")


def main():
    logger.info("Starting...")
    proxy_url = os.environ.get("PROXY_URL")
    request = HTTPXRequest(proxy=proxy_url) if proxy_url else HTTPXRequest()
    application = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .get_updates_request(request)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
