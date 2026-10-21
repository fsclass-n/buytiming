FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY collector ./collector
COPY malls.json public_price_map.json ./
RUN useradd --create-home rpa && mkdir -p /app/reports && chown -R rpa /app
USER rpa

# 기본: 내장 스케줄러(매시 수집, 03:00 재학습, 06:00 참가격, 월 07:00 리포트)
# 단발 실행: docker compose run --rm rpa python -m collector.jobs collect
CMD ["python", "-m", "collector.scheduler"]
