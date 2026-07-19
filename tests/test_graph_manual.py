# tests/test_graph_manual.py
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from app.agent.graph import app

async def main():
    config = {"configurable": {"thread_id": "test-conversation-1"}}
    while True:
        user_input = input("User: ")
        if user_input == "exit":
            break
        result = await app.ainvoke({"messages": [HumanMessage(content=user_input)]}, config=config)

        if "__interrupt__" in result:
            question = result["__interrupt__"][0].value
            print(f"CONFIRMATION NEEDED {question}")
            confirm_input = input("Your answer: ")
            result = await app.ainvoke(Command(resume=confirm_input), config=config)
        
            #for msg in result["messages"]:
            #    print(msg)

        # JUST FOR FORMATTING
            # Print the whole AI message object
        #print("===== FULL AI MESSAGE =====")
        #for msg in result["messages"]:
            #if isinstance(msg, AIMessage):
            #    print(msg)

        #print("\n\n")

        # Print only the AI's actual response to the user
        print("===== AI REPLY =====")
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                print(msg.content)
                break


asyncio.run(main())