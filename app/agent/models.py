import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

# Groq Free Tier Models (Separate rate-limit quota buckets)
PRIMARY_MODEL = "llama-3.3-70b-versatile"        # Groq Free: 70B primary
FALLBACK_1_MODEL = "llama-3.1-8b-instant"         # Groq Free: 8B fast fallback
FALLBACK_2_MODEL = "mixtral-8x7b-32768"           # Groq Free: 8x7B MoE fallback

# OpenRouter Dynamic Auto-Router (Automatically selects live free models)
OPENROUTER_FREE_MODEL = "openrouter/free"


def get_primary_llm(**kwargs):
    return ChatGroq(model=PRIMARY_MODEL, **kwargs)


def get_fallback_1_llm(**kwargs):
    return ChatGroq(model=FALLBACK_1_MODEL, **kwargs)


def get_fallback_2_llm(**kwargs):
    return ChatGroq(model=FALLBACK_2_MODEL, **kwargs)


def get_openrouter_free_llm(**kwargs):
    api_key = os.getenv("OPENROUTER_API_KEY") or "free"
    return ChatOpenAI(
        model=OPENROUTER_FREE_MODEL,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        **kwargs
    )