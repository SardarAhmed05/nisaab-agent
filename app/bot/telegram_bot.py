# app/bot/telegram_bot.py
#import logging
#logging.basicConfig(level=logging.DEBUG)

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from telegram.request import HTTPXRequest

from app.agent.graph import app as agent_app

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Tracks whether each chat is currently waiting for a yes/no confirmation reply
pending_confirmations = {}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("Received:", update.message.text)
    chat_id = update.effective_chat.id
    user_text = update.message.text
    config = {"configurable": {"thread_id": str(chat_id)}}

    if chat_id in pending_confirmations:
        result = await agent_app.ainvoke(Command(resume=user_text), config=config)
        pending_confirmations.pop(chat_id, None)
    else:
        result = await agent_app.ainvoke({"messages": [HumanMessage(content=user_text)]}, config=config)

    if "__interrupt__" in result:
        question = result["__interrupt__"][0].value
        pending_confirmations[chat_id] = True
        await update.message.reply_text(question)
        return

    for msg in reversed(result["messages"]):
        if msg.__class__.__name__ == "AIMessage" and msg.content:
            await update.message.reply_text(msg.content)
            break


def main():
    print("Starting...")
    request = HTTPXRequest(proxy="socks5://sardarthethird:8zTGpL6YPJ@95.164.145.233:50101")
    application = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .get_updates_request(request)
        .build()
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Polling...")
    application.run_polling()


if __name__ == "__main__":
    main()