import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

# 100% Free Tier Multi-Provider Model Hierarchy
PRIMARY_MODEL = "llama-3.3-70b-versatile"                          # Groq Free: 70B primary
FALLBACK_1_MODEL = "llama-3.1-8b-instant"                           # Groq Free: 8B fast fallback
FALLBACK_2_MODEL = "mixtral-8x7b-32768"                             # Groq Free: 8x7B MoE fallback
OPENROUTER_LLAMA_FREE = "meta-llama/llama-3.3-70b-instruct:free"   # OpenRouter Free: Llama 3.3 70B
OPENROUTER_GEMINI_FREE = "google/gemini-2.0-flash-lite-preview-02-05:free"  # OpenRouter Free: Gemini 2.0
OPENROUTER_DEEPSEEK_FREE = "deepseek/deepseek-r1:free"              # OpenRouter Free: DeepSeek R1


def get_primary_llm(**kwargs):
    return ChatGroq(model=PRIMARY_MODEL, **kwargs)


def get_fallback_1_llm(**kwargs):
    return ChatGroq(model=FALLBACK_1_MODEL, **kwargs)


def get_fallback_2_llm(**kwargs):
    return ChatGroq(model=FALLBACK_2_MODEL, **kwargs)


def get_openrouter_llama_free_llm(**kwargs):
    api_key = os.getenv("OPENROUTER_API_KEY") or "free"
    return ChatOpenAI(
        model=OPENROUTER_LLAMA_FREE,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        **kwargs
    )


def get_openrouter_gemini_free_llm(**kwargs):
    api_key = os.getenv("OPENROUTER_API_KEY") or "free"
    return ChatOpenAI(
        model=OPENROUTER_GEMINI_FREE,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        **kwargs
    )


def get_openrouter_deepseek_free_llm(**kwargs):
    api_key = os.getenv("OPENROUTER_API_KEY") or "free"
    return ChatOpenAI(
        model=OPENROUTER_DEEPSEEK_FREE,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        **kwargs
    )