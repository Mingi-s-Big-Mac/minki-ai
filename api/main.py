from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from api.routes import router  # noqa: E402
from core.config import get_settings  # noqa: E402

app = FastAPI(title="진로 AI API", version="0.1.0")


@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    """API_KEY 가 설정된 경우 /api/* 경로는 X-API-Key 헤더 검증을 요구한다.

    설정되지 않으면(빈 값) 검증을 건너뛴다(로컬 개발 편의).
    """
    settings = get_settings()
    if settings.api_key and request.url.path.startswith("/api"):
        provided = request.headers.get("x-api-key", "")
        if provided != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "유효하지 않은 API 키입니다."},
            )
    return await call_next(request)


app.include_router(router, prefix="/api")
