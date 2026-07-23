from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from core.config import get_settings


def _bedrock_credentials() -> dict:
    """설정에 명시된 AWS 자격 증명만 kwargs로 반환.

    비어 있으면 boto3 기본 자격 증명 체인(환경 변수, ~/.aws, IAM 역할 등)을 사용한다.
    """
    settings = get_settings()
    creds: dict = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        creds["aws_access_key_id"] = settings.aws_access_key_id
        creds["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            creds["aws_session_token"] = settings.aws_session_token
    return creds


@lru_cache(maxsize=8)
def get_llm(model: str, temperature: float = 0.3) -> BaseChatModel:
    settings = get_settings()

    if settings.llm_provider == "bedrock":
        from langchain_aws import ChatBedrockConverse
        return ChatBedrockConverse(
            model=model,
            temperature=temperature,
            **_bedrock_credentials(),
        )

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

    if settings.embedding_provider == "bedrock":
        from langchain_aws import BedrockEmbeddings
        return BedrockEmbeddings(
            model_id=settings.embedding_model,
            **_bedrock_credentials(),
        )

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
