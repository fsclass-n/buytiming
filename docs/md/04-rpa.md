# 04. RPA 수집기

소스: [`rpa/collector/`](../rpa/collector). EC2의 `rpa` 컨테이너에서 상주하며 **같은 EC2의 `api` 컨테이너**(`http://api:8000`)를 호출합니다.
API가 TiDB에 저장하므로 Render API에서도 같은 데이터가 보입니다.

## 1. 작업 4종

[`jobs.py`](../rpa/collector/jobs.py), [`scheduler.py`](../rpa/collector/scheduler.py)

| 작업 | 실행 시각(KST) | 하는 일 | 호출 API |
|---|---|---|---|
| `collect` | 매시 정각 | 수집 대상 목록 → 쇼핑몰 페이지 수집 → pandas 정제 → 일괄 저장 → 작업 로그 | `GET /rpa/listings`, `POST /rpa/prices/bulk`, `POST /rpa/logs` |
| `train` | 매일 03:00 | 모델 재학습 요청(API가 백그라운드로 학습) | `POST /rpa/train` |
| `public` | 매일 06:00 | 한국소비자원 참가격 수집 (`KCA_API_URL`, `DATA_GO_KR_KEY` 없으면 건너뜀) | `PUT /rpa/public-prices` |
| `report` | 매주 월 07:00 | 주간 가격 리포트(엑셀) 저장 → EC2 `~/buytiming/reports/` | `GET /rpa/reports/weekly` |

수동 실행: `docker compose exec rpa python -m collector.jobs collect` (또는 `train`, `public`, `report`)

## 2. 설정 (환경 변수)

[`config.py`](../rpa/collector/config.py). EC2에서는 `~/buytiming/.env`를 함께 읽습니다.

| 변수 | 기본값 | EC2 설정 |
|---|---|---|
| `RPA_TARGET_API` | http://localhost:8000 | **`http://api:8000`** (아래 주의 참고) |
| `RPA_API_KEY` | (없음 → 실행 거부) | api와 **같은 값** |
| `REQUEST_INTERVAL_SEC` | 3 | 요청 간격(초) |
| `SIMULATE_MALLS` | true | `*.example.com` 시연 쇼핑몰에 모의 가격 생성 |
| `KCA_API_URL`, `DATA_GO_KR_KEY` | (없음) | 참가격 API (선택) |
| `TZ` | Asia/Seoul | |

> **주의**: `docker-compose.yml`은 `RPA_TARGET_API: ${RPA_TARGET_API:-http://api:8000}`로 되어 있어,
> `.env`에 `RPA_TARGET_API`가 있으면 그 값이 우선합니다. `.env.example`을 그대로 복사하면 `http://localhost:8000`이 들어가
> 수집기가 자기 컨테이너 안의 localhost를 찾다가 **연결 실패**합니다. EC2 `.env`에서는 `http://api:8000`으로 바꿉니다.

## 3. 수집 원칙 (변경 금지)

[`http.py`](../rpa/collector/http.py)

- 사이트마다 `robots.txt`를 확인하고, 확인할 수 없으면 수집하지 않습니다.
- 요청 간격 기본 3초, 실패 시 3회 재시도(지수 백오프).
- [`malls.json`](../rpa/malls.json)에 CSS 셀렉터가 등록된(약관상 허용된) 쇼핑몰만 수집합니다. 현재는 예시 항목만 있고,
  시드 데이터의 시연 쇼핑몰 3곳(`mall-a/b/c.example.com`)은 실제 접속 없이 모의 가격(직전 가격 ±1.5%)을 만듭니다.
- 직전 가격 대비 ±50%를 넘는 값은 이상치로 제외합니다.

## 4. 인증

수집기는 모든 요청에 `X-RPA-KEY: <RPA_API_KEY>` 헤더를 붙이고([`api_client.py`](../rpa/collector/api_client.py)),
API는 `hmac.compare_digest`로 비교합니다. 값이 다르면 401(`INVALID_RPA_KEY`)이 나며 수집 로그도 남지 않습니다.

## 5. 테스트

`cd rpa && pytest -q` → 7건 (파서, 정제, 스케줄 판정 등).

다음 문서: [05. CI/CD 파이프라인](05-cicd.md)
