# 07. [배포 2단계] Render — 단독 풀스택 (https://buytiming.onrender.com)

Render 서비스 하나가 **API와 프런트엔드 화면을 같은 도메인으로** 제공합니다.
이미지: [`backend/Dockerfile.render`](../../backend/Dockerfile.render) (빌드 컨텍스트 = 저장소 루트, 루트 [`.dockerignore`](../../.dockerignore)로 `backend/app`·`frontend/`만 포함).
가격 수집은 GitHub Actions가 매시 대신 실행합니다(10 문서).

준비물: 06 문서의 TiDB `DATABASE_URL`, GitHub 저장소 `fsclass-n/buytiming` 접근 권한, (선택) Gemini API 키

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

> 예전 설정(`./backend/Dockerfile`, 컨텍스트 `./backend`)으로 두면 API만 뜨고 화면(`/`)은 JSON 안내만 나옵니다.

## 2. 환경 변수 (Environment)

필수 6개:

| Key | Value |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | 06 문서의 TiDB 접속 문자열 (`mysql+pymysql://<USER>:<PASSWORD>@<HOST>:4000/buytiming?charset=utf8mb4`) |
| `DB_SSL_CA` | `/etc/ssl/certs/ca-certificates.crt` |
| `JWT_SECRET` | 무작위 긴 문자열 — `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `RPA_API_KEY` | 무작위 긴 문자열 — **GitHub Secret `RENDER_RPA_API_KEY`에도 같은 값**(10 문서) |
| `ALLOWED_ORIGINS` | `https://buytiming.onrender.com` (같은 도메인 호출이라 자기 주소만 허용) |

선택:

| Key | Value |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio 키 (비우면 규칙 기반 템플릿 문장으로 동작) |
| `ADMIN_EMAILS` | 관리자로 가입시킬 이메일(쉼표 구분) |
| `GEMINI_MODEL`, `AI_DAILY_LIMIT` | 기본값(`gemini-2.5-flash`, `20`)이면 생략 |

`PORT`(Render가 주입), `TZ`·`FRONTEND_DIR`(Dockerfile에 설정됨)은 넣지 않습니다.
`.env.example`의 `RPA_TARGET_API`, `SIMULATE_MALLS`, `KCA_*`, `MYSQL_*`, `SEED_*`는 Render에는 필요 없습니다.

## 3. 자동 배포 끄기 (중요)

Settings → Build & Deploy → **Auto-Deploy: Off**

- 배포는 GitHub Actions(`deploy.yml`)가 **CI 통과 후에만** Deploy Hook으로 요청합니다.
- Auto-Deploy를 켜 두면 CI 결과와 상관없이 push마다 배포되고, Actions 배포와 겹쳐 두 번 배포됩니다.

## 4. 첫 배포와 확인

1. **Manual Deploy → Deploy latest commit** (Docker 빌드에 몇 분 걸립니다)
2. Logs에서 `Uvicorn running on http://0.0.0.0:10000` 확인
3. 브라우저로 확인

   | 주소 | 기대 결과 |
   |---|---|
   | https://buytiming.onrender.com/health | `{"status":"ok","env":"production","gemini":...}` — 이때 TiDB 테이블도 자동 생성됨 |
   | https://buytiming.onrender.com/ | 바이타이밍 홈 화면 → 로그인 화면으로 이동 (데모 배너 없음) |
   | https://buytiming.onrender.com/js/config.js | `API_BASE_URL: "/"` |
   | https://buytiming.onrender.com/docs | API 문서 |

4. 시드 데이터가 아직 없으면 06 문서 4단계(PC에서) 또는 08 문서 8단계(EC2에서)로 한 번 넣습니다. Render 무료 플랜은 셸이 없습니다.
5. 기동 실패 시 로그 메시지별 원인은 [11 문서](11-checklist-troubleshooting.md) 참고

## 5. Deploy Hook 복사 (10 문서에서 사용)

Settings → **Deploy Hook** → URL 복사 → GitHub Secret `RENDER_DEPLOY_HOOK_URL`로 등록합니다.
이 URL을 아는 사람은 누구나 배포를 일으킬 수 있으므로 공유하지 않습니다(유출되면 Regenerate).

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
