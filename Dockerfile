# Render 단독 풀스택 이미지: FastAPI + React 빌드 결과를 같은 도메인으로 제공
# 저장소 루트의 Dockerfile = Render 기본값이라 대시보드의 Dockerfile Path를 비워 두거나 ./Dockerfile로 두면 된다.
# 빌드 컨텍스트는 저장소 루트(.)이며, 루트 .dockerignore가 필요한 파일만 남긴다.
#   docker build -t picktiming-render .
# EC2·CI용 API 이미지는 backend/Dockerfile(같은 저장소 루트 컨텍스트)을 사용한다.
# 1단계: React 빌드
FROM node:22-alpine AS web
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# 2단계: FastAPI + 빌드 결과(dist)
FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul \
    FRONTEND_DIR=/app/frontend

# fonts-nanum: 주간 리포트(Seaborn·Matplotlib) 한글 차트, curl: 헬스 체크
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-nanum curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY --from=web /src/dist ./frontend
RUN useradd --create-home appuser && mkdir -p /app/data && chown -R appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD curl -fsS "http://localhost:${PORT:-8000}/health" || exit 1
# Render는 PORT 환경 변수를 주입한다(기본 10000).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
