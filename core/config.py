from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    # eu-central-1 에서는 Claude 계열이 크로스리전 추론 프로필(eu. 접두사)만 지원합니다.
    llm_provider: str = "bedrock"          # "bedrock" | "ollama" | "anthropic"
    ollama_base_url: str = "http://localhost:11434"
    chat_model: str = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    roadmap_model: str = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # 응답 최대 출력 토큰. 답변이 중간에 잘리면 이 값을 늘리세요.
    max_tokens: int = 8192

    # 임베딩
    embedding_provider: str = "bedrock"       # "bedrock" | "huggingface" | "ollama"
    embedding_model: str = "amazon.titan-embed-text-v2:0"

    # Amazon Bedrock (llm_provider=bedrock 사용 시)
    # 값을 비워두면 boto3 기본 자격 증명 체인(EC2 IAM 역할, ~/.aws, 환경 변수)을 사용합니다.
    aws_region: str = "eu-central-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""

    # Anthropic (llm_provider=anthropic 사용 시)
    anthropic_api_key: str = ""

    # API 인증 키. 값이 설정되면 /api/* 요청에 X-API-Key 헤더가 일치해야 함.
    # 비워두면 인증 없이 허용(로컬 개발용).
    api_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
