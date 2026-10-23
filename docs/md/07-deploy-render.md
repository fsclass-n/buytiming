# 07. [배포 2단계] Render — 백엔드 API (https://buytiming.onrender.com)

준비물: 06 문서의 TiDB `DATABASE_URL`, GitHub 저장소 `fsclass-n/buytiming` 접근 권한, (선택) Gemini API 키

## 1. 서비스 생성 방법 선택

Render 주소(`<이름>.onrender.com`)는 **서비스 이름**으로 정해집니다.
저장소의 [`render.yaml`](../render.yaml)은 이름이 `buytiming-api`라서 Blueprint로 만들면 `buytiming-api.onrender.com`이 됩니다.
목표 주소가 `buytiming.onrender.com`이므로 아래 **방법 A(권장)** 로 직접 만듭니다.

| 방법 | 주소 | 코드 변경 |
|---|---|---|
| **A. 직접 생성 (New → Web Service), 이름 `buytiming`** | buytiming.onrender.com | 없음 |
| B. Blueprint(render.yaml) | buytiming-api.onrender.com | 원하는 주소를 쓰려면 render.yaml의 `name` 변경 필요(변경 시 팀 승인) |

> 이미 `buytiming` 서비스를 만들어 두었다면 1~2단계는 건너뛰고 3단계 설정만 확인합니다.
> 이름 `buytiming`이 이미 다른 사람에게 쓰이고 있으면 Render가 뒤에 임의 문자를 붙입니다. 그 경우 실제 주소로 이후 문서의 값을 바꿉니다.

## 2. 서비스 생성 (방법 A)

Render 대시보드 → **New → Web Service** → GitHub 저장소 `fsclass-n/buytiming` 연결 후:

| 항목 | 값 (render.yaml과 동일하게) |
|---|---|
| Name | `buytiming` |
| Language / Runtime | **Docker** |
| Branch | `main` |
| Region | **Singapore** |
| Root Directory | (비움) |
| Dockerfile Path | `./backend/Dockerfile` |
| Docker Build Context Directory | `./backend` |
| Instance Type | **Free** |
| Health Check Path (Advanced) | `/health` |

## 3. 환경 변수 (Environment)

| Key | Value |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | 06 문서의 TiDB 접속 문자열 (`...:4000/buytiming?charset=utf8mb4`) |
| `DB_SSL_CA` | `/etc/ssl/certs/ca-certificates.crt` |
| `JWT_SECRET` | 무작위 긴 문자열 — `python -c "import secrets;print(secrets.token_urlsafe(48))"` (또는 Render의 Generate 버튼) |
| `RPA_API_KEY` | 무작위 긴 문자열 — **EC2 `.env`에도 같은 값 사용 권장** |
| `GEMINI_API_KEY` | Google AI Studio 키 (비우면 템플릿 문장으로 동작) |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `AI_DAILY_LIMIT` | `20` |
| `ALLOWED_ORIGINS` | `https://buytiming.netlify.app` (끝에 `/` 없이, 여러 개면 쉼표 구분) |
| `ADMIN_EMAILS` | 관리자로 가입시킬 이메일(쉼표 구분, 선택) |

`PORT`는 Render가 자동으로 넣으므로 설정하지 않습니다. `TZ=Asia/Seoul`은 Dockerfile에 들어 있습니다.

## 4. 자동 배포 끄기 (중요)

Settings → Build & Deploy → **Auto-Deploy: Off**

- 배포는 GitHub Actions(`deploy.yml`)가 **CI 통과 후에만** Deploy Hook으로 요청합니다(render.yaml의 `autoDeployTrigger: "off"`와 같은 의도).
- Auto-Deploy를 켜 두면 CI 결과와 상관없이 push마다 배포되고, Actions 배포와 겹쳐 두 번 배포됩니다.

## 5. 첫 배포와 확인

1. **Manual Deploy → Deploy latest commit** (Docker 빌드에 몇 분 걸립니다)
2. Logs에서 `Uvicorn running on http://0.0.0.0:10000` 확인
3. 브라우저로 확인
   - https://buytiming.onrender.com/health → `{"status":"ok","env":"production","gemini":true}` (키가 없으면 `false`)
   - https://buytiming.onrender.com/docs → API 문서
4. 기동 실패 시 로그 메시지별 원인은 [11 문서](11-checklist-troubleshooting.md) 참고
   (`운영 환경에서는 ... 값을 반드시 설정해야 합니다` → `JWT_SECRET`/`RPA_API_KEY` 누락, `Access denied`/`SSL` → DB 값 확인)

## 6. Deploy Hook 복사 (10 문서에서 사용)

Settings → **Deploy Hook** → URL 복사 → GitHub Secret `RENDER_DEPLOY_HOOK_URL`로 등록합니다.
이 URL을 아는 사람은 누구나 배포를 일으킬 수 있으므로 공유하지 않습니다(유출되면 Regenerate).

## 7. 무료 플랜 특성

| 특성 | 영향 | 대응 |
|---|---|---|
| 15분간 요청이 없으면 잠듦, 깨어나는 데 약 1분 | Netlify 첫 화면이 느림 | 정상 동작. 시연 직전에 `/health`를 한 번 열어 깨워 둠 |
| 셸·SSH 접속 불가 | Render에서 `python -m app.seed` 실행 불가 | 시드는 EC2나 PC에서 TiDB로 실행(06 문서) |
| 메모리 512 MB, 0.1 CPU | 모델 학습이 느릴 수 있음 | 학습은 EC2 RPA가 EC2 API로 요청하므로 Render 부담 없음 |
| 파일 시스템 휘발 | 재시작 시 로컬 파일 삭제 | 데이터는 모두 TiDB에 있으므로 문제없음 |

다음 문서: [08. EC2 배포](08-deploy-ec2.md)
