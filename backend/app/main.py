import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import get_settings
from .database import engine, init_db
from .errors import register_error_handlers
from .routers import admin, ai, auth, products, rpa, user_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_settings().validate_for_production()
    init_db()
    yield


settings = get_settings()
app = FastAPI(title="BuyTiming API", version="1.1.0", description="실시간 가격 비교 & 구매 적기 추천 API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_methods=["*"], allow_headers=["*"],
                   allow_credentials=False)
register_error_handlers(app)

for r in (auth.router, products.router, ai.router, user_data.router, rpa.router, admin.router):
    app.include_router(r, prefix="/api/v1")


@app.get("/health", tags=["운영"])
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "env": settings.app_env, "gemini": bool(settings.gemini_api_key)}


SECURITY_HEADERS = {"X-Frame-Options": "DENY", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "strict-origin-when-cross-origin"}

if settings.frontend_dir and Path(settings.frontend_dir).is_dir():
    # Render 단독 풀스택: 프런트엔드와 API를 같은 도메인으로 제공 (EC2에서는 nginx가 같은 역할)
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        return response

    @app.get("/js/config.js", include_in_schema=False)
    def frontend_config():
        return Response('window.APP_CONFIG = { API_BASE_URL: "/" };\n', media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})

    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"service": "BuyTiming API", "docs": "/docs", "health": "/health"}
