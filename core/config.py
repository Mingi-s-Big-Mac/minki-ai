from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: str = "ollama"          # "ollama" | "anthropic"
    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "llama3.2"
    roadmap_model: str = "llama3.2"

    # 임베딩
    embedding_provider: str = "huggingface"   # "huggingface" | "ollama"
    embedding_model: str = "jhgan/ko-sroberta-multitask"

    # Anthropic (llm_provider=anthropic 사용 시)
    anthropic_api_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
