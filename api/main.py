import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from api.routes import router  # noqa: E402
from core.config import get_settings  # noqa: E402
from rag.retriever import DB_PATH  # noqa: E402

app = FastAPI(title="진로 AI API", version="0.1.0")
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}


def _probe_ollama(base_url: str, models: list[str]) -> str:
    for model in dict.fromkeys(models):
        request = Request(
            f"{base_url.rstrip('/')}/api/show",
            data=json.dumps({"model": model}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=2):
                pass
        except HTTPError as exc:
            return "missing" if exc.code == 404 else "unavailable"
        except (URLError, TimeoutError):
            return "unavailable"
    return "ok"


@app.get("/ready")
def ready():
    settings = get_settings()
    checks: dict[str, str] = {}
    ollama_models: list[str] = []

    if settings.llm_provider == "ollama":
        ollama_models.extend([settings.chat_model, settings.roadmap_model])
    elif settings.llm_provider == "anthropic":
        checks["anthropic_key"] = "ok" if settings.anthropic_api_key else "missing"
    else:
        checks["llm_provider"] = "unsupported"

    if settings.embedding_provider == "ollama":
        ollama_models.append(settings.embedding_model)
    elif settings.embedding_provider == "huggingface":
        checks["embedding_model"] = "ok" if settings.embedding_model else "missing"
        db_path = Path(DB_PATH)
        try:
            checks["vector_db"] = (
                "ok" if db_path.is_dir() and any(db_path.iterdir()) else "missing"
            )
        except OSError:
            checks["vector_db"] = "unavailable"
    else:
        checks["embedding_provider"] = "unsupported"

    if ollama_models:
        checks["ollama"] = _probe_ollama(settings.ollama_base_url, ollama_models)

    status = "ready" if all(result == "ok" for result in checks.values()) else "not_ready"
    return JSONResponse(
        status_code=200 if status == "ready" else 503,
        content={"status": status, "checks": checks},
    )
