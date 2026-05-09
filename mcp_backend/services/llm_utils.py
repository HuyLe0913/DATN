from __future__ import annotations
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_embedding_instance = None
_llm_instance = None

def get_llm():
    """
    Trả về LLM thông qua OpenRouter (Singleton).
    """
    global _llm_instance
    if _llm_instance is None:
        model_name = os.getenv("GRAPH_EXTRACTOR_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free")
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set in .env file.")
        
        _llm_instance = ChatOpenAI(
            model=model_name,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Financial RAG DATN"
            },
            temperature=0
        )
    return _llm_instance

def get_embeddings():
    """
    Trả về model Embedding thông qua OpenRouter (Singleton).
    """
    global _embedding_instance
    if _embedding_instance is None:
        embedding_model = os.getenv("EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set in .env file.")

        _embedding_instance = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=OPENROUTER_BASE_URL,
            tiktoken_model_name="cl100k_base"
        )
    return _embedding_instance
