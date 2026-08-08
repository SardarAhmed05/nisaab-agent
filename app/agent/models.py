import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_1_MODEL = "llama-3.3-70b-versatile"
FALLBACK_2_MODEL = "openrouter/free"


def get_primary_llm(**kwargs):
    return ChatGroq(model=PRIMARY_MODEL, **kwargs)


def get_fallback_1_llm(**kwargs):
    return ChatGroq(model=FALLBACK_1_MODEL, **kwargs)


def get_fallback_2_llm(**kwargs):
    return ChatOpenAI(
        model=FALLBACK_2_MODEL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        **kwargs
    )