# 04. RPA 수집기

소스: [`rpa/collector/`](../../rpa/collector). 같은 수집기 코드를 **두 곳에서 각각** 실행해, 각 서버가 독립적으로 가격을 갱신합니다.

| 실행 위치 | 방식 | 보내는 곳 | 인증 키 |
|---|---|---|---|
| EC2 | `rpa` 컨테이너 상주 — 내장 스케줄러([`scheduler.py`](../../rpa/collector/scheduler.py)), 매시 정각 | `http://api:8000` (같은 EC2의 API) | EC2 `.env`의 `RPA_API_KEY` |
| Render | GitHub Actions 예약 실행([`collect-render.yml`](../../.github/workflows/collect-render.yml)), 매시 07분 | `https://picktiming.onrender.com` | GitHub Secret `RENDER_RPA_API_KEY` = Render의 `RPA_API_KEY` |

- Render 무료 플랜은 상주 작업을 돌릴 수 없고 15분 무요청 시 잠들기 때문에, Actions가 먼저 `/health`로 깨운 뒤(최대 3분 대기) 수집합니다.
- 두 수집기는 같은 TiDB에 저장합니다. API가 **같은 판매처·같은 시간대의 두 번째 가격은 건너뛰므로**(`duplicate`) 중복 행·중복 알림이 생기지 않습니다.
  관리자 화면의 수집 로그는 두 곳 모두 남으며, 나중에 실행된 쪽은 저장 0건으로 표시될 수 있습니다(정상).
- 두 환경이 모두 구성·운영 중이면 한쪽 서버 장애 시 다른 쪽 수집을 사용할 수 있습니다.
  현재 EC2의 실제 운영은 확인 전이므로 이 구성을 이미 검증된 이중 운영으로 소개하지 않습니다.

## 1. 작업 4종

[`jobs.py`](../../rpa/collector/jobs.py), [`scheduler.py`](../../rpa/collector/scheduler.py)

| 작업 | 실행 시각(KST) | 하는 일 | 호출 API |
|---|---|---|---|
| `collect` | 매시 정각 | 수집 대상 목록 → 쇼핑몰 페이지 수집 → pandas 정제 → 일괄 저장 → 작업 로그 | `GET /rpa/listings`, `POST /rpa/prices/bulk`, `POST /rpa/logs` |
| `train` | 매일 03:00 | 모델 재학습 요청(API가 백그라운드로 학습) | `POST /rpa/train` |
| `public` | 매일 06:00 | 한국소비자원 참가격 수집 (`KCA_API_URL`, `DATA_GO_KR_KEY` 없으면 건너뜀) | `PUT /rpa/public-prices` |
| `report` | 매주 월 07:00 | 주간 가격 리포트(엑셀) 저장 → EC2 `~/picktiming/reports/`, Render용은 Actions 아티팩트(30일 보관) | `GET /rpa/reports/weekly` |

수동 실행
- EC2: `docker compose exec rpa python -m collector.jobs collect` (또는 `train`, `public`, `report`)
- Render: GitHub → Actions → **Collect (Render)** → Run workflow → 작업 선택

`train`은 두 곳에서 하루 한 번씩 실행되지만, 성능이 같거나 좋을 때만 모델을 교체하므로 문제가 없습니다.

## 2. 설정 (환경 변수)

[`config.py`](../../rpa/collector/config.py). EC2에서는 `~/picktiming/.env`를 함께 읽습니다.

| 변수 | 기본값 | EC2 설정 | GitHub Actions(Render) 설정 |
|---|---|---|---|
| `RPA_TARGET_API` | http://localhost:8000 | **`http://api:8000`** (아래 주의 참고) | Variable `RENDER_URL` |
| `RPA_API_KEY` | (없음 → 실행 거부) | api와 **같은 값** | Secret `RENDER_RPA_API_KEY` |
| `REQUEST_INTERVAL_SEC` | 3 | 요청 간격(초) | 기본값 |
| `SIMULATE_MALLS` | true | `*.example.com` 시연 쇼핑몰에 모의 가격 생성 | 기본값 |
| `KCA_API_URL`, `DATA_GO_KR_KEY` | (없음) | 참가격 API (선택) | Variable `KCA_API_URL`, Secret `DATA_GO_KR_KEY` (선택) |
| `TZ` | Asia/Seoul | | 워크플로에 설정됨 |

> **주의**: `docker-compose.yml`은 `RPA_TARGET_API: ${RPA_TARGET_API:-http://api:8000}`로 되어 있어,
> `.env`에 `RPA_TARGET_API`가 있으면 그 값이 우선합니다. 현행 `.env.example`의 해당 항목은 주석입니다.
> EC2에서는 이 줄을 넣지 않아 compose 기본값을 사용하거나 `http://api:8000`으로 지정합니다.
> `localhost:8000`을 넣으면 수집기 자신의 컨테이너를 찾아 연결에 실패합니다.

### 선택적 연동

- 네이버 검색: `NAVER_SEARCH_CLIENT_ID`, `NAVER_SEARCH_CLIENT_SECRET`. 수집용 값이 없으면 로그인용 `NAVER_CLIENT_*`를 대신 확인합니다.
- Playwright: 동적 페이지 수집 시 브라우저 설치와 대상 설정이 필요합니다.
- S3: `S3_BUCKET`, `S3_PREFIX`, `AWS_REGION`과 IAM 역할 또는 AWS 자격 증명이 필요합니다.
- 연결 코드 존재와 실제 API 수집 성공은 구분합니다. 예시 쇼핑몰 A/B/C는 실거래 판매처가 아닙니다.

## 3. 수집 원칙 (변경 금지)

[`http.py`](../../rpa/collector/http.py)

- 사이트마다 `robots.txt`를 확인하고, 확인할 수 없으면 수집하지 않습니다.
- 요청 간격 기본 3초, 실패 시 3회 재시도(지수 백오프).
- [`malls.json`](../../rpa/malls.json)에 CSS 셀렉터가 등록된(약관상 허용된) 쇼핑몰만 수집합니다. 현재는 예시 항목만 있고,
  시드 데이터의 시연 쇼핑몰 3곳(`mall-a/b/c.example.com`)은 실제 접속 없이 모의 가격(직전 가격 ±1.5%)을 만듭니다.
- 직전 가격 대비 ±50%를 넘는 값은 이상치로 제외합니다.

## 4. 인증

수집기는 모든 요청에 `X-RPA-KEY: <RPA_API_KEY>` 헤더를 붙이고([`api_client.py`](../../rpa/collector/api_client.py)),
API는 `hmac.compare_digest`로 비교합니다. 값이 다르면 401(`INVALID_RPA_KEY`)이 나며 수집 로그도 남지 않습니다.

## 5. 테스트

`cd rpa && pytest -q` → 기준 커밋 `279a4ce`에서 11건 통과(파서, 정제, 설정, 스케줄 판정 등).

다음 문서: [05. CI/CD 파이프라인](05-cicd.md)
