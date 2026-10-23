# 바이타이밍(BuyTiming) — 생성형 AI & RPA 기반 실시간 가격 비교·구매 적기 추천

Final-Project 3조 (김길동(조장), 박미금, 이오리, 홍기흥)

RPA가 쇼핑몰 가격과 공공 가격 데이터를 1시간마다 모아 실시간으로 비교하고, scikit-learn 모델이
"과거 패턴상 지금이 싼 시점인가?"를 판단하면 Google Gemini가 그 근거를 자연어로 설명합니다.

| 구분 | 기술 |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript(ES Modules), Bootstrap 5, Flexbox, Plotly.js — **Netlify(데모 모드)**, Render·EC2(실서비스) |
| Backend | Python 3.11 · FastAPI · SQLAlchemy — **Render / AWS EC2 (Docker)** |
| Database | TiDB Cloud(로컬·Render·EC2 공용) / SQLite(자동 테스트) / MySQL 8.x(CI 호환성 테스트) |
| AI | Google Gemini(gemini-2.5-flash, JSON 구조화 출력 + 숫자 대조 검증), scikit-learn RandomForest |
| RPA / Data | Python 3.11.9 · Requests · BeautifulSoup4 · pandas · NumPy · Seaborn · Matplotlib |
| External | 공공데이터 API(한국소비자원 참가격) |
| CI/CD | GitHub Actions(`ci.yml`, `deploy.yml`, `collect-render.yml`), Render Auto-Deploy(After CI Checks Pass), EC2 SSH 배포, Netlify |

## 실행계획 단계와 구현 대응

| 단계 | 구현 결과물 |
|---|---|
| 설계 | `backend/app/models.py`(테이블 12개), `frontend/*.html`(화면 10개), `backend/app/routers`(API 22개 + RPA 보조 3개) |
| 구현 | 프런트엔드·백엔드·Gemini 연동·RPA 수집기, 판정 모델(`app/ml`), 주간 리포트(`app/jobs`) |
| 배포 | Dockerfile·docker-compose·nginx·render.yaml·netlify.toml, GitHub Actions CI/CD, 테스트 36건 |

## 폴더 구조

```
buytiming/
├── frontend/              # 정적 사이트 (Netlify=데모 모드, Render·EC2=같은 도메인 API 연동)
│   ├── *.html             # 홈·로그인·회원가입·검색·상세·AI 상담·관심 상품·알림·관리자 2종
│   ├── js/api.js          # REST 클라이언트 (API_BASE_URL 없으면 mock.js로 데모 모드)
│   ├── js/mock.js         # 백엔드와 같은 응답 형식의 브라우저 목업 API
│   └── build.sh           # Netlify 빌드: API_BASE_URL → js/config.js
├── backend/               # FastAPI (Render · EC2)
│   ├── app/routers/       # auth, products, ai, user_data, rpa, admin
│   ├── app/ai/gemini.py   # 프롬프트·구조화 출력·숫자 검증·재요청·템플릿 대체
│   ├── app/ml/            # 피처 8종, 학습(TimeSeriesSplit), 모델 저장(DB)
│   ├── app/seed.py        # 시연 데이터(쇼핑몰 3곳·상품 12종·120일)
│   ├── tests/             # pytest 29건
│   ├── Dockerfile         # EC2·CI용 API 이미지
│   ├── Dockerfile.render  # Render용 풀스택 이미지(API + frontend, 컨텍스트 = 저장소 루트)
│   ├── requirements.txt · requirements-dev.txt
├── rpa/                   # 수집기 (EC2 컨테이너 스케줄러 / Render용은 GitHub Actions 예약 실행)
│   ├── collector/         # http(robots.txt·간격·재시도), parsers, jobs, scheduler
│   ├── malls.json         # 쇼핑몰별 CSS 셀렉터 (약관상 허용된 곳만)
│   ├── tests/             # pytest 7건
│   └── Dockerfile · requirements.txt
├── deploy/                # nginx.conf, EC2 설정 스크립트
├── docker-compose.yml     # EC2: web(nginx) + api + rpa [+ mysql]
├── render.yaml            # Render Blueprint (단독 풀스택)
├── .dockerignore          # Render 빌드(저장소 루트 컨텍스트)용
├── netlify.toml           # Netlify (base=frontend, 데모 모드)
├── .github/workflows/     # ci.yml, deploy.yml, collect-render.yml
├── docs/md/               # 단계별 배포 문서 (docs/md/README.md부터)
├── .env.example           # 환경 변수 예시 (.env는 Git 제외)
└── ruff.toml
```

> 운영 구성: **Netlify = 프런트엔드 데모**, **Render·EC2 = 각각 독립된 풀스택**, **DB = TiDB 하나를 로컬·Render·EC2가 공유**,
> **설정 = `.env` 하나**(로컬 작성 → EC2로 복사 → Render에 붙여 넣기). 단계별 상세 절차는 [`docs/md/README.md`](docs/md/README.md)를 따릅니다.

## 1. 로컬 실행 (.venv)

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements-dev.txt -r rpa/requirements-dev.txt
cp .env.example .env              # DATABASE_URL(TiDB), JWT_SECRET, RPA_API_KEY를 채운다 — 이 .env를 EC2·Render에도 그대로 사용

cd backend
python -m app.seed                # (최초 1회) 시연 데이터 + 초기 모델 학습 → TiDB에 저장
uvicorn app.main:app --reload     # http://localhost:8000 (화면 + API, /docs)
```

로컬도 운영과 같은 TiDB를 사용하므로 `python -m app.seed --reset`은 실행하지 않습니다. 화면 수정만 볼 때는 `cd frontend && python -m http.server 5501`(데모 모드)도 가능합니다.

RPA 작업(다른 터미널):

```bash
cd rpa
python -m collector.jobs collect  # 가격 수집 1회 (시연 쇼핑몰은 모의 가격)
python -m collector.jobs train    # 모델 재학습 요청
python -m collector.jobs report   # 주간 리포트 엑셀 저장(reports/)
python -m collector.scheduler     # 스케줄 상주 실행
```

테스트·린트:

```bash
cd backend && pytest -q           # 33 passed (임시 SQLite 사용 — .env의 TiDB는 건드리지 않음)
cd rpa && pytest -q               # 7 passed
ruff check backend rpa
```

## 2. Netlify — 프런트엔드 (데모 모드)

1. Netlify에서 이 저장소를 연결하면 루트의 `netlify.toml`을 읽어 `frontend/`를 배포합니다.
2. `API_BASE_URL`을 등록하지 않으므로 **데모 모드**(브라우저 목업 API)로 모든 화면이 동작합니다. 서버·DB와 연결하지 않습니다.

## 3. Render — 단독 풀스택 (API + 프런트엔드)

1. Render 웹 서비스(Docker): Dockerfile Path `./backend/Dockerfile.render`, Build Context `.`, Health Check `/health` (`render.yaml`과 동일).
2. 환경 변수: Environment → **Add from .env** → 로컬 `.env` 내용을 그대로 붙여 넣습니다(`FRONTEND_DIR`은 넣지 않음).
3. Auto-Deploy: **After CI Checks Pass** — 커밋하면 GitHub Actions CI 통과 후 자동 배포. Build Filters Included Paths: `backend/**`, `frontend/**`, `render.yaml`, `.dockerignore`.
   (이 경우 GitHub Secret `RENDER_DEPLOY_HOOK_URL`은 등록하지 않음 — 중복 배포 방지)
4. 무료 플랜은 셸이 없으므로 시연 데이터는 로컬에서 `python -m app.seed`로 TiDB에 넣습니다.
5. 가격 수집은 GitHub Actions `collect-render.yml`이 매시 실행합니다(Variable `RENDER_URL`, Secret `RENDER_RPA_API_KEY` = `.env`의 `RPA_API_KEY`).

## 4. AWS EC2 — 단독 풀스택(nginx + API + RPA)

```bash
# EC2(Ubuntu)에서
bash deploy/ec2-setup.sh https://github.com/fsclass-n/buytiming.git      # Docker 설치 → 재접속 후 다시 실행
# PC에서: scp -i <키.pem> .env ubuntu@buytiming.duckdns.org:~/buytiming/.env   (로컬 .env를 그대로 복사)
cd ~/buytiming && docker compose up -d --build                            # http://buytiming.duckdns.org
```

- EC2 `.env`는 로컬 `.env`와 같은 파일입니다(서버에서 다시 입력하지 않음). `RPA_TARGET_API`는 넣지 않습니다(compose 기본값 `http://api:8000`).
- 두 수집기(EC2 rpa, Render용 Actions)가 같은 TiDB에 보내도 API가 같은 판매처·같은 시간대 가격은 한 번만 저장합니다.
- 보안 그룹은 80(HTTP)과 22(SSH)를 엽니다. GitHub Actions가 SSH로 배포하므로 22번 접근 범위는 `docs/md/10-github-actions-setup.md`를 참고합니다.

## 5. GitHub Actions CI/CD

| 워크플로 | 시점 | 내용 |
|---|---|---|
| `ci.yml` | `main` 외 브랜치 push, PR | ruff, pytest(SQLite), pytest(MySQL 8 서비스 컨테이너), RPA 테스트, JS 문법·build.sh 검사, Docker 빌드·헬스 체크, compose 검증 |
| `deploy.yml` | `main` push, 수동 | CI 재사용(중복 실행 없음) → **바뀐 폴더에 해당하는 대상만** Render · EC2 · Netlify 배포 |
| `collect-render.yml` | 매시 07분, 수동 | Render용 가격 수집(KST 03시 재학습, 06시 참가격, 월 07시 리포트 포함) |

바뀐 폴더별 배포 대상 (`.github/scripts/detect-changes.sh`):

| 바뀐 경로 | Netlify | Render | EC2 (full) | EC2 (rpa-only) |
|---|:---:|:---:|:---:|:---:|
| `frontend/` | ✅ | ✅ | ✅ (git pull로 반영) | – |
| `netlify.toml` | ✅ | – | – | – |
| `backend/` | – | ✅ | ✅ (api만 재빌드) | – |
| `render.yaml`, `.dockerignore` | – | ✅ | – | – |
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
| Secret | `RENDER_RPA_API_KEY` | `.env`의 `RPA_API_KEY`와 같은 값 (Render 가격 수집) |
| Secret | `RENDER_DEPLOY_HOOK_URL` | **등록하지 않음** (Render Auto-Deploy를 Off로 둘 때만 사용) |
| Secret | `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` | EC2 주소, 접속 사용자(ubuntu), 개인 키(PEM 전체) |
| Secret | `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID` | (선택) Git 연동 대신 Actions로 Netlify 배포 |
| Variable | `RENDER_URL` | `https://buytiming.onrender.com` (Render 가격 수집 대상) |
| Variable | `EC2_APP_DIR` | 기본 `~/buytiming` |
| Variable | `EC2_MODE` | `full`(기본) 또는 `rpa-only` |

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
