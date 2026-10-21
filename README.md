# 바이타이밍(BuyTiming) — 생성형 AI & RPA 기반 실시간 가격 비교·구매 적기 추천

Final-Project 3조 (김길동(조장), 박미금, 이오리, 홍기흥)

RPA가 쇼핑몰 가격과 공공 가격 데이터를 1시간마다 모아 실시간으로 비교하고, scikit-learn 모델이
"과거 패턴상 지금이 싼 시점인가?"를 판단하면 Google Gemini가 그 근거를 자연어로 설명합니다.

| 구분 | 기술 |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript(ES Modules), Bootstrap 5, Flexbox, Plotly.js — **Netlify** |
| Backend | Python 3.11 · FastAPI · SQLAlchemy — **Render / AWS EC2 (Docker)** |
| Database | MySQL 8.x(개발·EC2) / TiDB Cloud(운영) / SQLite(로컬 빠른 실행·테스트) |
| AI | Google Gemini(gemini-2.5-flash, JSON 구조화 출력 + 숫자 대조 검증), scikit-learn RandomForest |
| RPA / Data | Python 3.11.9 · Requests · BeautifulSoup4 · pandas · NumPy · Seaborn · Matplotlib |
| External | 공공데이터 API(한국소비자원 참가격) |
| CI/CD | GitHub Actions(`ci.yml`, `deploy.yml`), Render Deploy Hook, EC2 SSH 배포, Netlify |

## 실행계획 단계와 구현 대응

| 단계 | 구현 결과물 |
|---|---|
| 설계 | `backend/app/models.py`(테이블 12개), `frontend/*.html`(화면 10개), `backend/app/routers`(API 22개 + RPA 보조 3개) |
| 구현 | 프런트엔드·백엔드·Gemini 연동·RPA 수집기, 판정 모델(`app/ml`), 주간 리포트(`app/jobs`) |
| 배포 | Dockerfile·docker-compose·nginx·render.yaml·netlify.toml, GitHub Actions CI/CD, 테스트 31건 |

## 폴더 구조

```
buytiming/
├── frontend/              # Netlify 정적 사이트 (데모 모드 내장)
│   ├── *.html             # 홈·로그인·회원가입·검색·상세·AI 상담·관심 상품·알림·관리자 2종
│   ├── js/api.js          # REST 클라이언트 (API_BASE_URL 없으면 mock.js로 데모 모드)
│   ├── js/mock.js         # 백엔드와 같은 응답 형식의 브라우저 목업 API
│   └── build.sh           # Netlify 빌드: API_BASE_URL → js/config.js
├── backend/               # FastAPI (Render · EC2)
│   ├── app/routers/       # auth, products, ai, user_data, rpa, admin
│   ├── app/ai/gemini.py   # 프롬프트·구조화 출력·숫자 검증·재요청·템플릿 대체
│   ├── app/ml/            # 피처 8종, 학습(TimeSeriesSplit), 모델 저장(DB)
│   ├── app/seed.py        # 시연 데이터(쇼핑몰 3곳·상품 12종·120일)
│   ├── tests/             # pytest 24건
│   ├── Dockerfile · requirements.txt · requirements-dev.txt
├── rpa/                   # 수집기 (EC2 컨테이너 스케줄러 또는 cron)
│   ├── collector/         # http(robots.txt·간격·재시도), parsers, jobs, scheduler
│   ├── malls.json         # 쇼핑몰별 CSS 셀렉터 (약관상 허용된 곳만)
│   ├── tests/             # pytest 7건
│   └── Dockerfile · requirements.txt
├── deploy/                # nginx.conf, EC2 설정 스크립트
├── docker-compose.yml     # EC2: web(nginx) + api + rpa [+ mysql]
├── render.yaml            # Render Blueprint
├── netlify.toml           # Netlify (base=frontend)
├── .github/workflows/     # ci.yml, deploy.yml
├── .env.example           # 환경 변수 예시 (.env는 Git 제외)
└── ruff.toml
```

## 1. 로컬 실행 (.venv)

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements-dev.txt -r rpa/requirements-dev.txt
cp .env.example .env              # JWT_SECRET, RPA_API_KEY 등을 채운다

cd backend
python -m app.seed                # 시연 데이터 + 초기 모델 학습, 데모 계정 비밀번호 출력
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

프런트엔드(다른 터미널):

```bash
cd frontend
python -m http.server 5501        # http://localhost:5501  → 데모 모드
API_BASE_URL=http://localhost:8000 sh build.sh   # 실제 API 연동 (되돌리려면 API_BASE_URL 없이 다시 실행)
```

RPA 작업(다른 터미널, `.env`의 `RPA_API_KEY`가 백엔드와 같아야 함):

```bash
cd rpa
python -m collector.jobs collect  # 가격 수집 1회 (시연 쇼핑몰은 모의 가격)
python -m collector.jobs train    # 모델 재학습 요청
python -m collector.jobs report   # 주간 리포트 엑셀 저장(reports/)
python -m collector.scheduler     # 스케줄 상주 실행
```

테스트·린트:

```bash
cd backend && pytest -q           # 24 passed
cd rpa && pytest -q               # 7 passed
ruff check backend rpa
```

## 2. Netlify — 프런트엔드

1. Netlify에서 이 저장소를 연결하면 루트의 `netlify.toml`을 읽어 `frontend/`를 배포합니다.
2. **API 없이 배포하면 데모 모드**(브라우저 목업 API)로 모든 화면이 동작합니다.
3. 백엔드 배포 후 Site settings → Environment variables에 `API_BASE_URL=https://<서비스>.onrender.com` (또는 EC2 주소)을 넣고 재배포합니다.
4. 백엔드의 `ALLOWED_ORIGINS`에 Netlify 사이트 주소를 추가합니다.

## 3. Render — 백엔드 API

1. TiDB Cloud Serverless에서 `buytiming` DB를 만들고 접속 문자열을 준비합니다.
   `DATABASE_URL=mysql+pymysql://<USER>:<PASSWORD>@<HOST>:4000/buytiming`
2. Render → New → Blueprint로 저장소를 연결하면 `render.yaml`대로 Docker 웹 서비스가 생성됩니다.
   `DATABASE_URL`, `RPA_API_KEY`, `GEMINI_API_KEY`, `ALLOWED_ORIGINS`, `ADMIN_EMAILS`를 입력합니다(`JWT_SECRET`은 자동 생성).
3. 최초 1회 Render Shell에서 `python -m app.seed` 실행(시연 데이터가 필요할 때).
4. 서비스 Settings → Deploy Hook URL을 GitHub secret `RENDER_DEPLOY_HOOK_URL`에 등록하면 CI 통과 후 자동 배포됩니다.

## 4. AWS EC2 — 전체 스택(nginx + API + RPA) 또는 RPA 전용

```bash
# EC2(Ubuntu)에서
bash deploy/ec2-setup.sh https://github.com/<조 Organization>/buytiming.git   # Docker 설치 → 재접속 후 다시 실행
vi ~/buytiming/.env                                                       # 운영 값 입력 (APP_ENV=production)
cd ~/buytiming && docker compose up -d --build                            # http://<EC2 공인 IP>
docker compose exec api python -m app.seed                                # (선택) 시연 데이터
```

- 같은 EC2의 MySQL을 쓰려면 `docker compose --profile localdb up -d --build`와
  `DATABASE_URL=mysql+pymysql://buytiming:<MYSQL_PASSWORD>@mysql:3306/buytiming`을 사용합니다.
- **Render API + EC2 RPA 조합**: `.env`에 `RPA_TARGET_API=https://<서비스>.onrender.com`를 넣고
  `docker compose up -d --build --no-deps rpa`로 수집기만 실행합니다.
- 보안 그룹은 80(HTTP)과 22(SSH, 관리자 IP만)만 엽니다. HTTPS는 도메인 연결 후 ALB 또는 certbot으로 구성합니다.

## 5. GitHub Actions CI/CD

| 워크플로 | 시점 | 내용 |
|---|---|---|
| `ci.yml` | `main` 외 브랜치 push, PR | ruff, pytest(SQLite), pytest(MySQL 8 서비스 컨테이너), RPA 테스트, JS 문법·build.sh 검사, Docker 빌드·헬스 체크, compose 검증 |
| `deploy.yml` | `main` push, 수동 | CI 재사용(중복 실행 없음) → **바뀐 폴더에 해당하는 대상만** Render · EC2 · Netlify 배포 |

바뀐 폴더별 배포 대상 (`.github/scripts/detect-changes.sh`):

| 바뀐 경로 | Netlify | Render | EC2 (full) | EC2 (rpa-only) |
|---|:---:|:---:|:---:|:---:|
| `frontend/` | ✅ | – | ✅ (git pull로 반영) | – |
| `netlify.toml` | ✅ | – | – | – |
| `backend/` | – | ✅ | ✅ (api만 재빌드) | – |
| `render.yaml` | – | ✅ | – | – |
| `rpa/` | – | – | ✅ (rpa만 재빌드) | ✅ |
| `docker-compose.yml` | – | – | ✅ (전체) | ✅ |
| `deploy/` | – | – | ✅ (nginx 재시작) | – |
| 그 외(README, 워크플로 등) | – | – | – | – |

- **EC2 (full)**: EC2에서 nginx + api + rpa 전체 운영(기본). **EC2 (rpa-only)**: API는 Render, EC2는 수집기만 운영 → Variable `EC2_MODE=rpa-only`.
- `backend/`와 `rpa/`가 함께 바뀌면 Render(API)를 먼저 배포한 뒤 EC2(RPA)를 배포합니다.
- 비교 기준 커밋이 없는 첫 push·강제 push는 모든 대상에 배포하고, 수동 실행(Actions → Deploy → Run workflow)은 선택한 대상에 전체 배포합니다.
- Netlify Git 연동을 쓰는 경우 Netlify 자체도 `frontend/`(base) 변경이 없으면 빌드를 건너뜁니다. Git 연동과 Actions 배포 중 하나만 사용하세요.

등록할 값 (Settings → Secrets and variables → Actions):

| 종류 | 이름 | 설명 |
|---|---|---|
| Secret | `RENDER_DEPLOY_HOOK_URL` | Render 서비스의 Deploy Hook |
| Secret | `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` | EC2 주소, 접속 사용자(ubuntu), 개인 키(PEM 전체) |
| Secret | `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID` | (선택) Git 연동 대신 Actions로 Netlify 배포 |
| Variable | `RENDER_HEALTH_URL` | 예: `https://buytiming-api.onrender.com/health` |
| Variable | `EC2_APP_DIR` | 기본 `~/buytiming` |
| Variable | `EC2_MODE` | `full`(기본) 또는 `rpa-only` |
| Variable | `API_BASE_URL` | Netlify 프런트엔드가 호출할 API 주소 |

등록하지 않은 대상은 자동으로 건너뜁니다.

## 6. 보안·운영 원칙

- `.env`·API 키는 Git에 올리지 않습니다. `APP_ENV=production`에서 기본 비밀값을 쓰면 서버가 기동을 거부합니다.
- Gemini 키는 서버에만 두며, 브라우저는 Gemini를 직접 호출하지 않습니다. 응답 속 숫자는 분석 수치와 대조하고 불일치 시 재요청·템플릿으로 대체합니다.
- 수집기는 robots.txt를 확인하고 요청 간격(기본 3초)을 지키며, `malls.json`에 등록된(약관상 허용된) 쇼핑몰만 수집합니다.
- `python -m app.seed --reset`은 DB 전체를 지우므로 개발 DB에서만 사용합니다.

## API 요약 (`/api/v1`, 문서: `/docs`)

인증 `POST /auth/signup` · `POST /auth/login` · `GET /users/me`
상품 `GET /products/search` · `POST /products` · `GET /products/{id}` · `GET /products/{id}/compare` · `GET /products/{id}/prices`
AI `GET /products/{id}/timing` · `POST /products/{id}/advice` · `POST /ai/chat`
사용자 `GET·POST /watchlist` · `PATCH·DELETE /watchlist/{id}` · `GET /alerts` · `POST /alerts/read-all` · `GET /deals/today`
RPA(X-RPA-KEY) `GET /rpa/listings` · `POST /rpa/prices/bulk` · `PUT /rpa/public-prices` · `POST /rpa/models` · `POST /rpa/logs` · `POST /rpa/train` · `GET /rpa/reports/weekly`
관리자 `GET /admin/rpa-logs` · `GET /admin/ai-metrics`
