from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from core.config import get_settings


@lru_cache(maxsize=8)
def get_llm(model: str, temperature: float = 0.3) -> BaseChatModel:
    settings = get_settings()

    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, temperature=temperature)

    raise ValueError(f"지원하지 않는 LLM provider: {settings.llm_provider}")


@lru_cache(maxsize=1)
def get_embeddings():
    settings = get_settings()

    if settings.embedding_provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=settings.embedding_model)

    if settings.embedding_provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )

    raise ValueError(f"지원하지 않는 embedding provider: {settings.embedding_provider}")
