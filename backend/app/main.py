import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

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
app = FastAPI(title="PickTiming API", version="1.1.0", description="실시간 가격 비교 & 구매 적기 추천 API", lifespan=lifespan)
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

# Render(FRONTEND_DIR=/app/frontend)·로컬(저장소의 frontend/dist = npm run build 결과)은 프런트엔드와 API를 같은 도메인으로 제공.
# EC2 api 컨테이너는 폴더가 없어 API만 제공(화면은 nginx 담당)
FRONTEND_DIR = Path(settings.frontend_dir or Path(__file__).resolve().parents[2] / "frontend" / "dist")


class SPAStaticFiles(StaticFiles):
    """React(SPA) 라우팅: /search 같은 화면 경로는 index.html로, 확장자가 있는 파일만 실제 404"""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404 or "." in path.rsplit("/", 1)[-1]:
                raise
            return await super().get_response("index.html", scope)


if FRONTEND_DIR.is_dir() and (FRONTEND_DIR / "index.html").is_file():
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

    app.mount("/", SPAStaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"service": "PickTiming API", "docs": "/docs", "health": "/health"}
