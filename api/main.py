from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402

from api.routes import router  # noqa: E402

app = FastAPI(title="진로 AI API", version="0.1.0")
app.include_router(router, prefix="/api")
