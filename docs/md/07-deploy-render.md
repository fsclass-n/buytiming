# 07. [배포 2단계] Render — 단독 풀스택 (https://buytiming.onrender.com)

Render 서비스 하나가 **API와 프런트엔드 화면을 같은 도메인으로** 제공합니다.
이미지: [`backend/Dockerfile.render`](../../backend/Dockerfile.render) (빌드 컨텍스트 = 저장소 루트, 루트 [`.dockerignore`](../../.dockerignore)로 `backend/app`·`frontend/`만 포함).
가격 수집은 GitHub Actions가 매시 대신 실행합니다(10 문서).

준비물: 값을 채운 로컬 `.env`(06 문서, [`.env.example`](../../.env.example) 기반), GitHub 저장소 `fsclass-n/buytiming` 접근 권한

## 1. 서비스 만들기 / 기존 서비스 설정 바꾸기

Render 대시보드에서 이미 `buytiming` 서비스를 만들었다면 **Settings**에서 아래 값으로 맞춥니다.
새로 만든다면 **New → Web Service** → 저장소 `fsclass-n/buytiming` 연결 후 같은 값으로 입력합니다.
(Blueprint로 만들면 [`render.yaml`](../../render.yaml)이 같은 값을 자동으로 넣습니다.)

| 항목 | 값 |
|---|---|
| Name | `buytiming` |
| Language / Runtime | **Docker** |
| Branch | `main` |
| Region | **Singapore** |
| Root Directory | (비움) |
| Dockerfile Path | **`./backend/Dockerfile.render`** |
| Docker Build Context Directory | **`.`** (저장소 루트) |
| Instance Type | **Free** |
| Health Check Path | `/health` |
| Auto-Deploy | **After CI Checks Pass** (3단계) |
| Build Filters → Included Paths | `backend/**`, `frontend/**`, `render.yaml`, `.dockerignore` (3단계) |

> 예전 설정(`./backend/Dockerfile`, 컨텍스트 `./backend`)으로 두면 API만 뜨고 화면(`/`)은 JSON 안내만 나옵니다.

## 2. 환경 변수 — 로컬 `.env`를 그대로 붙여 넣기

로컬 PC·EC2와 **같은 `.env`** 를 씁니다.

1. Render → buytiming 서비스 → **Environment** → **Add from .env**
2. 로컬 `.env` 파일 내용을 전부 복사해 붙여 넣기 → 추가된 목록 확인 → **Save, rebuild, and deploy**
   (예전에 넣은 같은 이름의 값이 있으면 새 값으로 바뀌었는지 확인합니다)

| 붙여 넣으면 들어가는 값 | 비고 |
|---|---|
| `APP_ENV`, `DATABASE_URL`, `DB_SSL_CA`, `JWT_SECRET`, `RPA_API_KEY`, `ALLOWED_ORIGINS` | 필수 6개. 세 환경 모두 같은 값으로 동작 |
| `ADMIN_EMAILS`, `GEMINI_API_KEY`, `KCA_API_URL`, `DATA_GO_KR_KEY`, `SEED_*` | 선택. 비어 있어도 문제없음 |

- `PORT`(Render가 주입), `TZ`·`FRONTEND_DIR`(Dockerfile에 설정됨)은 `.env`에 없으므로 따로 넣지 않습니다. **`FRONTEND_DIR`을 Render에 넣지 마세요**(Dockerfile 값을 덮어써 화면이 사라질 수 있음).
- `.env` 값을 바꾸면 Render에도 같은 값을 다시 붙여 넣고, EC2에도 다시 복사합니다(08 문서).
- `RPA_API_KEY`는 GitHub Secret `RENDER_RPA_API_KEY`에도 같은 값으로 등록합니다(10 문서).

## 3. 자동 배포 — After CI Checks Pass

Settings → Build & Deploy → **Auto-Deploy: After CI Checks Pass**

| 선택지 | 동작 | 이 프로젝트 |
|---|---|---|
| On Commit | push하면 테스트 결과와 상관없이 바로 배포 | 테스트가 실패한 코드도 배포됨 |
| **After CI Checks Pass** | push하면 GitHub Actions 검사가 모두 통과한 뒤 자동 배포 | **권장** — 커밋하면 자동 배포 + 테스트 실패 시 배포 안 함 |
| Off | 자동 배포 없음 (Deploy Hook·수동 배포만) | 사용 안 함 |

- 같은 화면의 **Build Filters → Included Paths**에 `backend/**`, `frontend/**`, `render.yaml`, `.dockerignore`를 넣으면
  문서(`docs/`)·EC2 설정만 바뀐 커밋은 Render를 다시 빌드하지 않습니다.
- 이 방식에서는 GitHub Secret `RENDER_DEPLOY_HOOK_URL`을 **등록하지 않습니다**. 등록하면 Actions도 배포를 요청해 두 번 배포됩니다.
- Render는 그 커밋의 **모든** GitHub 검사가 성공(또는 건너뜀)해야 배포합니다. 같은 커밋에서 EC2 배포 작업이 실패하면 Render도 배포하지 않으니,
  그때는 원인을 고친 뒤 다시 push하거나 Render에서 Manual Deploy를 누릅니다.
- 배포를 원하지 않는 커밋은 메시지에 `[skip render]`를 넣으면 건너뜁니다.

## 4. 첫 배포와 확인

1. 환경 변수 저장 시 **Save, rebuild, and deploy**를 골랐다면 자동으로 배포가 시작됩니다. 아니면 **Manual Deploy → Deploy latest commit** (Docker 빌드에 몇 분 걸립니다)
2. Logs에서 `Uvicorn running on http://0.0.0.0:10000` 확인
3. 브라우저로 확인

   | 주소 | 기대 결과 |
   |---|---|
   | https://buytiming.onrender.com/health | `{"status":"ok","env":"production","gemini":...}` — 이때 TiDB 테이블도 자동 생성됨 |
   | https://buytiming.onrender.com/ | 바이타이밍 홈 화면 → 로그인 화면으로 이동 (데모 배너 없음) |
   | https://buytiming.onrender.com/js/config.js | `API_BASE_URL: "/"` |
   | https://buytiming.onrender.com/docs | API 문서 |

4. 시드 데이터가 아직 없으면 06 문서 4단계(로컬 PC에서)로 한 번 넣습니다. Render 무료 플랜은 셸이 없습니다.
5. 기동 실패 시 로그 메시지별 원인은 [11 문서](11-checklist-troubleshooting.md) 참고

## 5. (사용 안 함) Deploy Hook

Settings → Deploy Hook URL은 Auto-Deploy를 **Off**로 두고 GitHub Actions가 배포를 요청하게 할 때만 GitHub Secret `RENDER_DEPLOY_HOOK_URL`로 등록합니다.
이번 구성(After CI Checks Pass)에서는 등록하지 않습니다. 이 URL을 아는 사람은 누구나 배포를 일으킬 수 있으므로 공유하지 않습니다.

## 6. 무료 플랜 특성

| 특성 | 영향 | 대응 |
|---|---|---|
| 15분간 요청이 없으면 잠듦, 깨어나는 데 약 1분 | 첫 화면이 느림 | UptimeRobot 등으로 5분마다 `/health` 호출(아래 참고). Actions 수집기는 1시간에 한 번만 깨우므로 이 역할을 대신하지 못함 |
| 셸·SSH 접속 불가 | Render에서 `python -m app.seed` 실행 불가 | 시드는 EC2나 PC에서 TiDB로 실행(06 문서) |
| 상주 작업(Background Worker·Cron) 불가 | 서버 안에서 RPA 스케줄러를 돌릴 수 없음 | GitHub Actions `collect-render.yml`이 매시 수집(10 문서) |
| 메모리 512 MB, 0.1 CPU | 모델 재학습(매일 03시)이 느릴 수 있음 | 학습은 백그라운드로 실행되어 응답에는 영향 없음 |
| 파일 시스템 휘발 | 재시작 시 로컬 파일 삭제 | 데이터는 모두 TiDB에 있으므로 문제없음 |

### 깨우기(UptimeRobot)와 가격 수집(Actions)의 역할 분리

| | UptimeRobot (5분마다 `/health`) | GitHub Actions `collect-render.yml` (매시 07분) |
|---|---|---|
| 목적 | 사용자 접속 시 바로 열리게 함 | 가격 수집 |
| Render가 잠들어 있으면 | 깨움 | `/health`를 최대 18회(10초 간격) 호출해 **깨어날 때까지 기다린 뒤** 수집 → 잠들어 있어도 문제없음 |
| 실행이 늦거나 빠지면 | — | GitHub 예약 실행은 늦거나 가끔 건너뜀. 같은 TiDB에 EC2 수집기가 매시 저장하므로 데이터 공백 없음 |

- 둘 다 유지합니다. Actions만으로 15분 안쪽 간격을 정확히 지키기는 어렵습니다(예약 실행 지연).
- Render 무료 플랜은 **워크스페이스 전체 월 750시간**입니다. 서비스 하나를 24시간 깨워 두면 약 744시간이므로, 같은 워크스페이스의 다른 무료 서비스까지 상시 깨우면 한도를 넘을 수 있습니다.
- `/health`는 TiDB에 `SELECT 1`을 보냅니다. 5분 간격(월 약 8,600회)은 TiDB 무료 한도에 비해 무시할 수준입니다.

다음 문서: [08. EC2 배포](08-deploy-ec2.md)
