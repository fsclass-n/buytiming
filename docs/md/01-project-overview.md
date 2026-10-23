# 01. 프로젝트 개요와 구조

## 1. 서비스 한 줄 설명

**RPA가 쇼핑몰 가격과 공공 가격(한국소비자원 참가격)을 1시간마다 수집**하고,
**scikit-learn 모델이 "과거 패턴상 지금이 싼 시점인가"를 점수로 판정**하며,
**Google Gemini가 그 근거를 자연어로 설명**하는 가격 비교·구매 적기 추천 서비스입니다.
(Final-Project 3조: 김길동(조장), 박미금, 이오리, 홍기흥)

## 2. 기술 스택

| 구분 | 기술 | 위치 |
|---|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript(ES Modules), Bootstrap 5, Plotly.js — 번들러·npm 없음 | `frontend/` |
| Backend | Python 3.11.9, FastAPI, SQLAlchemy 2, PyMySQL, PyJWT, bcrypt | `backend/` |
| AI / ML | Google Gemini(`gemini-2.5-flash`), scikit-learn RandomForest, pandas, NumPy | `backend/app/ai`, `backend/app/ml` |
| RPA | Requests, BeautifulSoup4, pandas, 내장 스케줄러 | `rpa/` |
| DB | TiDB Cloud(로컬·Render·EC2 공용), SQLite(자동 테스트), MySQL 8(CI 호환성 테스트) | — |
| 배포 | Netlify, Render(Docker), AWS EC2(docker compose + nginx) | `netlify.toml`, `render.yaml`, `docker-compose.yml`, `deploy/` |
| CI/CD | GitHub Actions | `.github/` |

## 3. 폴더 구조

```
buytiming/
├── frontend/                 # Netlify 정적 사이트 (EC2에서는 nginx가 같은 파일을 서빙)
│   ├── *.html                # 화면 10개 + 404
│   ├── css/style.css
│   ├── js/api.js             # REST 클라이언트 (API_BASE_URL 없으면 데모 모드)
│   ├── js/mock.js            # 백엔드와 같은 응답 형식의 브라우저 목업 API
│   ├── js/common.js          # 공통 레이아웃·인증 처리
│   ├── js/config.js          # API 주소 (Netlify 빌드 때 build.sh가 다시 생성)
│   ├── js/pages/*.js         # 화면별 스크립트
│   └── build.sh              # Netlify 빌드: API_BASE_URL → js/config.js
├── backend/                  # FastAPI (Render · EC2 공용 Docker 이미지)
│   ├── app/main.py           # 앱 생성, CORS, 라우터 등록, /health
│   ├── app/config.py         # 환경 변수 설정
│   ├── app/database.py       # DB 엔진 (SQLite / MySQL·TiDB + TLS)
│   ├── app/models.py         # 테이블 12개
│   ├── app/routers/          # auth, products, ai, user_data, rpa, admin
│   ├── app/services/         # 가격 비교, 적기 판정, 알림
│   ├── app/ml/               # 피처, 학습, 모델 저장(DB)
│   ├── app/ai/gemini.py      # Gemini 프롬프트·검증·템플릿 대체
│   ├── app/jobs/             # 주간 리포트(엑셀)
│   ├── app/seed.py           # 시연 데이터
│   ├── tests/                # pytest 29건
│   ├── Dockerfile            # EC2·CI용 API 이미지 (컨텍스트 ./backend)
│   └── Dockerfile.render     # Render용 풀스택 이미지: API + frontend/ (컨텍스트 = 저장소 루트)
├── rpa/                      # 가격 수집기 (EC2 컨테이너)
│   ├── collector/            # http, parsers, jobs, scheduler, api_client
│   ├── malls.json            # 쇼핑몰별 CSS 셀렉터
│   ├── public_price_map.json # 참가격 상품 ID ↔ 모델 번호
│   ├── tests/                # pytest 7건
│   └── Dockerfile
├── deploy/                   # nginx.conf, config.same-origin.js, ec2-setup.sh
├── docker-compose.yml        # EC2: web(nginx) + api + rpa (DB는 TiDB)
├── render.yaml               # Render Blueprint (서비스 이름 buytiming, Dockerfile.render)
├── .dockerignore             # 저장소 루트 컨텍스트 빌드(Render)에 backend/app·frontend만 포함
├── netlify.toml              # Netlify (base=frontend, 데모 모드)
├── .github/                  # ci.yml, deploy.yml, collect-render.yml, scripts/detect-changes.sh
├── .env.example              # 환경 변수 예시 (.env는 Git 제외)
├── .claude/, CLAUDE.md       # Claude Code 설정 (배포와 무관)
└── docs/                     # 이 문서들
```

## 4. 전체 데이터 흐름

```
[매시] 수집기 — 두 갈래가 각자 자기 서버의 API로 보냄
   EC2:    rpa 컨테이너(정각)          ──▶ http://api:8000 (EC2 API)
   Render: GitHub Actions(매시 07분)   ──▶ https://buytiming.onrender.com (Render API)
   │ 1) GET  /api/v1/rpa/listings        수집 대상(판매 페이지) 목록
   │ 2) 각 쇼핑몰 페이지 수집 (robots.txt 확인, 3초 간격)  ※ *.example.com 시연 쇼핑몰은 모의 가격
   │ 3) pandas 정제 (중복·이상치 제거)
   │ 4) POST /api/v1/rpa/prices/bulk     가격 저장(같은 시간대 중복은 건너뜀) → 적기 판정 갱신 → 알림 생성
   ▼
TiDB (운영 DB) ◀── Render API, EC2 API 둘 다 같은 DB 사용
   ▲
   │ 사용자 요청 (JWT 로그인 후) — 각 서버의 프런트엔드가 같은 도메인의 API를 호출
Render(buytiming.onrender.com) / EC2(buytiming.duckdns.org): 검색 / 상세·가격 비교 / 적기 판정 / AI 조언·상담 / 관심 상품 / 알림

Netlify(buytiming.netlify.app): 데모 모드 — 브라우저 목업 데이터만 사용, 서버·DB와 연결 없음
```

| 시각(KST) | 작업 | 결과 |
|---|---|---|
| 매시 | 가격 수집(`collect`) | `price_history` 추가, 판정·알림 갱신 |
| 매일 03시 | 모델 재학습(`train`) | 성능이 같거나 좋으면 새 모델을 활성화(`model_versions`) |
| 매일 06시 | 참가격 공공데이터(`public`) | `public_prices` 갱신 (키가 없으면 건너뜀) |
| 매주 월 07시 | 주간 리포트(`report`) | EC2: `~/buytiming/reports/`, Render: Actions 아티팩트(30일 보관) |

## 5. 환경별 차이 한눈에 보기

| 항목 | 로컬 PC | Netlify | Render | EC2 |
|---|---|---|---|---|
| 주소 | http://localhost:8000 | buytiming.netlify.app | buytiming.onrender.com | buytiming.duckdns.org |
| DB | **TiDB** | 없음 | **TiDB** | **TiDB** (세 곳 같은 DB) |
| 프런트엔드 제공 | FastAPI(StaticFiles, 저장소 `frontend/` 자동) | Netlify CDN | FastAPI(StaticFiles) | nginx |
| API 주소(프런트) | 같은 도메인(`/`) | 없음(데모 모드) | 같은 도메인(`/`) | 같은 도메인(`/`) |
| 실행 방식 | `uvicorn` | 정적 호스팅 | `backend/Dockerfile.render` (컨텍스트: 저장소 루트) | `backend/Dockerfile`, `rpa/Dockerfile` (compose) |
| RPA | 수동 실행 | 없음 | GitHub Actions 예약 실행 | 컨테이너 상주 |
| 설정 값 | 루트 `.env` | 없음 | **같은 `.env`** 를 Environment에 붙여 넣기 | **같은 `.env`** 를 `~/buytiming/.env`로 복사 |
| 배포 | — | Netlify Git 연동 | 커밋 → CI 통과 → Render Auto-Deploy | 커밋 → CI 통과 → GitHub Actions SSH |

다음 문서: [02. 백엔드](02-backend.md)
