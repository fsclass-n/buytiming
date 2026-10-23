# 02. 백엔드 (FastAPI)

소스: [`backend/app/`](../backend/app). Render와 EC2는 **같은 Docker 이미지**([`backend/Dockerfile`](../backend/Dockerfile))를 사용합니다.

## 1. 시작 과정

[`main.py`](../backend/app/main.py) 기준:

1. 환경 변수 읽기 → `APP_ENV=production`인데 `JWT_SECRET`·`RPA_API_KEY`가 비어 있거나 기본값이면 **기동 거부**
2. `init_db()` → 테이블이 없으면 생성 (`create_all`, 별도 마이그레이션 도구 없음)
3. CORS 설정(`ALLOWED_ORIGINS`), 라우터 6개를 `/api/v1` 아래에 등록
4. `GET /health` → DB에 `SELECT 1`을 실행해 성공하면 `{"status":"ok"}` — Render·EC2·CI가 모두 이 경로로 상태를 확인

Docker 실행 명령은 `uvicorn app.main:app --port ${PORT:-8000}` 입니다. Render는 `PORT`를 주입하고(기본 10000), EC2는 8000을 씁니다.

## 2. 환경 변수

[`config.py`](../backend/app/config.py), [`.env.example`](../.env.example) 기준입니다.

| 변수 | 기본값 | 설명 | Render | EC2 |
|---|---|---|---|---|
| `APP_ENV` | development | `production`이면 비밀값 검사 | production | production |
| `DATABASE_URL` | sqlite:///./buytiming.db | DB 접속 문자열 | TiDB | TiDB (같은 값) |
| `DB_SSL_CA` | (없음) | TLS CA 파일 경로 (TiDB 필수) | `/etc/ssl/certs/ca-certificates.crt` | 같음 |
| `JWT_SECRET` | change-me | 로그인 토큰 서명 키 | 자동 생성 | 직접 생성 |
| `JWT_EXPIRE_MINUTES` | 60 | 토큰 유효 시간(분) | — | — |
| `RPA_API_KEY` | change-me-rpa | RPA 전용 API 인증 키 | 같은 값 권장 | rpa와 api가 **반드시 같은 값** |
| `ADMIN_EMAILS` | (없음) | 이 이메일로 가입하면 관리자 | 선택 | 선택 |
| `GEMINI_API_KEY` | (없음) | 비우면 규칙 기반 템플릿 문장으로 동작 | 선택 | 선택 |
| `GEMINI_MODEL` | gemini-2.5-flash | | | |
| `AI_DAILY_LIMIT` | 20 | 사용자별 일일 Gemini 호출 한도 | | |
| `ALLOWED_ORIGINS` | * | CORS 허용 출처(쉼표 구분) | `https://buytiming.netlify.app` | `https://buytiming.netlify.app` |
| `TZ` | Asia/Seoul | 서비스 기준 시간대 | Dockerfile에 설정됨 | |

## 3. DB 테이블 12개

[`models.py`](../backend/app/models.py). 시간은 모두 **KST 기준 naive datetime**으로 저장합니다.

| 테이블 | 내용 | 주요 관계 |
|---|---|---|
| `users` | 회원(이메일, bcrypt 해시, 역할 USER/ADMIN) | |
| `products` | 상품(이름, 브랜드, 모델 번호, 카테고리) | |
| `malls` | 쇼핑몰(이름, 주소, robots 확인일, 활성 여부) | |
| `product_listings` | 상품 × 쇼핑몰 판매 페이지 URL | products, malls (상품·쇼핑몰 쌍 유일) |
| `price_history` | 수집 가격(가격, 배송비, 실구매가, 재고, 수집 시각) | product_listings |
| `public_prices` | 참가격 공공 가격 | products |
| `watchlist` | 관심 상품 + 목표가 | users, products |
| `alerts` | 알림(목표가 도달 / 판정 변경) | users, products |
| `timing_predictions` | 적기 판정 결과(점수, 라벨, 90일 최저가 등) 캐시 | products, model_versions |
| `ai_advice_logs` | Gemini 호출 로그·캐시(토큰, 지연, 검증 결과) | products, users |
| `model_versions` | 학습된 모델(joblib 압축 바이너리, F1, 활성 여부) | |
| `rpa_job_logs` | RPA 작업 로그 | |

- 모델 파일은 DB(`model_versions.artifact`, MySQL에서는 LONGBLOB)에 저장됩니다. 시드 데이터 기준 약 **0.24 MiB**(직접 측정)이고,
  트리 깊이가 8로 제한되어 있어 TiDB의 한 행 최대 크기(기본 6 MiB)보다 충분히 작습니다.

## 4. API 목록 (`/api/v1`, 문서: `/docs`)

| 분류 | 메서드·경로 | 인증 | 설명 |
|---|---|---|---|
| 인증 | `POST /auth/signup`, `POST /auth/login`, `GET /users/me` | 로그인 후 `/users/me` | JWT 발급 |
| 상품 | `GET /products/search?q=` | 사용자 | 이름·브랜드·카테고리·모델 번호 검색 (최대 50개) |
| | `POST /products` | 사용자 | 등록된 쇼핑몰 URL만 상품 등록 → 다음 수집부터 반영 |
| | `GET /products/{id}`, `/compare`, `/prices?days=` | 사용자 | 상세, 쇼핑몰별 비교, 가격 차트 |
| AI | `GET /products/{id}/timing` | 사용자 | 적기 점수·라벨(BUY_NOW / WAIT_A_BIT / WAIT / HOLD) |
| | `POST /products/{id}/advice` | 사용자 | Gemini 조언 (24시간 캐시) |
| | `POST /ai/chat` | 사용자 | 상품 질문 상담 (일일 한도) |
| 사용자 | `GET·POST /watchlist`, `PATCH·DELETE /watchlist/{id}` | 사용자 | 관심 상품·목표가 |
| | `GET /alerts`, `POST /alerts/read-all` | 사용자 | 알림 |
| | `GET /deals/today` | 사용자 | 오늘의 적기 상품·7일 하락 상품 |
| RPA | `GET /rpa/listings`, `POST /rpa/prices/bulk`, `PUT /rpa/public-prices`, `POST /rpa/models`, `POST /rpa/logs`, `POST /rpa/train`, `GET /rpa/reports/weekly` | `X-RPA-KEY` 헤더 | 수집기 전용 |
| 관리자 | `GET /admin/rpa-logs`, `GET /admin/ai-metrics` | ADMIN | 수집 현황, AI 사용 지표 |

오류 응답은 모두 `{"code": "...", "message": "..."}` 형식입니다([`errors.py`](../backend/app/errors.py)).

## 5. 적기 판정과 AI

- **판정**([`services/timing.py`](../backend/app/services/timing.py)): 쇼핑몰별 일별 최저 실구매가 → 90일 가격 위치, 30일 추세, 할인 주기 등 피처 8종 → RandomForest의 "7일 안에 5% 이상 하락할 확률" → 0~100점과 라벨. 결과는 2시간 동안 `timing_predictions`에 캐시됩니다.
- **학습**([`ml/train.py`](../backend/app/ml/train.py)): TimeSeriesSplit 5분할로 F1을 계산해 기존 모델보다 같거나 좋을 때만 교체. 데이터가 100행 미만이면 건너뜁니다.
- **Gemini**([`ai/gemini.py`](../backend/app/ai/gemini.py)): 분석 수치를 문자열로 넘기고, 응답 속 숫자가 입력에 없으면 1회 재요청, 그래도 실패하거나 키가 없으면 템플릿 문장으로 대체합니다. 키는 서버에만 있고 브라우저는 Gemini를 직접 호출하지 않습니다.

## 6. 시드 데이터 (`python -m app.seed`)

[`seed.py`](../backend/app/seed.py): 시연 쇼핑몰 3곳(`*.example.com`), 상품 12종, 가격 이력 120일, 데모 계정 2개, 초기 모델 학습.

- 데이터가 이미 있으면 아무것도 하지 않습니다(운영 DB에 다시 실행해도 안전).
- 계정: `demo@buytiming.demo`, `admin@buytiming.demo` — 비밀번호는 `SEED_DEMO_PASSWORD` / `SEED_ADMIN_PASSWORD`, 없으면 무작위 생성 후 화면에 출력.
- `--reset`은 **모든 테이블을 삭제**합니다. 운영 TiDB에서 절대 사용하지 않습니다.

## 7. 테스트

- `cd backend && pytest -q` → 24건. 기본은 임시 SQLite, `TEST_DATABASE_URL`을 주면 그 DB로 실행(CI는 MySQL 8).
- 테스트는 시작할 때 `seed(reset=True)`로 **DB를 비웁니다**. `TEST_DATABASE_URL`에 TiDB 운영 주소를 넣지 않습니다.

다음 문서: [03. 프런트엔드](03-frontend.md)
