# 10. [배포 5단계] GitHub Actions 등록 — 자동 배포 + Render 가격 수집

07~09를 마치면 수동 배포는 끝난 상태입니다. 이 단계에서 값을 등록하면
- `main` push 때 **CI 통과 → 바뀐 폴더에 해당하는 Render·EC2만 자동 배포**(05 문서)
- **매시 07분 Render용 가격 수집**(`collect-render.yml`, 04 문서)

이 동작합니다. 값을 등록하지 않은 대상·작업은 자동으로 건너뜁니다.

등록 위치: GitHub `fsclass-n/buytiming` → **Settings → Secrets and variables → Actions** (저장소 관리자 권한 필요)

## 1. Secrets (암호화 저장)

| Name | 값 | 얻는 곳 | 사용처 |
|---|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | `https://api.render.com/deploy/srv-...?key=...` | Render → Settings → Deploy Hook (07 문서 5단계) | 자동 배포 |
| `RENDER_RPA_API_KEY` | Render 환경 변수 `RPA_API_KEY`와 **같은 값** | 07 문서 2단계 | Render 가격 수집 |
| `EC2_HOST` | `buytiming.duckdns.org` (또는 Elastic IP) | 08 문서 2단계 | 자동 배포 |
| `EC2_USER` | `ubuntu` | Ubuntu AMI 기본 사용자 | 자동 배포 |
| `EC2_SSH_KEY` | `.pem` 파일 **전체 내용** (`-----BEGIN ... KEY-----`부터 `-----END ... KEY-----`까지 줄바꿈 포함) | 08 문서 1단계의 키 페어 | 자동 배포 |
| `DATA_GO_KR_KEY` | 공공데이터포털 서비스 키 (선택) | data.go.kr | Render 참가격 수집 |

> Netlify가 **Git 연동**이면 `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID`는 등록하지 않습니다. 등록하면 같은 커밋이 두 번 배포됩니다.
> Netlify를 Actions로 배포하려면(수동 업로드 사이트였던 경우) Netlify → User settings → Applications → Personal access token을
> `NETLIFY_AUTH_TOKEN`으로, Site configuration → Site ID를 `NETLIFY_SITE_ID`로 등록하고 Netlify 쪽 Git 연동은 끕니다.

## 2. Variables (평문)

| Name | 값 | 비고 |
|---|---|---|
| `RENDER_HEALTH_URL` | `https://buytiming.onrender.com/health` | 배포 후 헬스 체크 |
| `RENDER_URL` | `https://buytiming.onrender.com` | Render 가격 수집 대상 (끝에 `/` 없이) |
| `EC2_APP_DIR` | `~/buytiming` | 기본값과 같으면 생략 가능 |
| `EC2_MODE` | `full` | 기본값과 같으면 생략 가능 (`rpa-only`로 두지 않음) |
| `KCA_API_URL` | 참가격 API 주소 (선택) | Render 참가격 수집 |

`API_BASE_URL`은 **등록하지 않습니다**(Netlify 데모 모드 유지).

## 3. EC2 보안 그룹 22번 포트 (주의)

배포 작업은 GitHub가 제공하는 러너(매번 다른 공인 IP)에서 EC2로 SSH 접속합니다.
22번을 "내 IP"로만 열어 두면 **EC2 배포가 `Connection timed out`으로 실패**합니다.

| 선택지 | 방법 | 장단점 |
|---|---|---|
| A. 22번을 0.0.0.0/0으로 열기 | 보안 그룹 인바운드 22 → Anywhere | 가장 간단. 비밀번호 로그인은 기본적으로 꺼져 있고 키로만 접속되지만, 무차별 대입 시도가 로그에 쌓임 → 키 파일 관리 철저 |
| B. GitHub Actions IP 대역 허용 | https://api.github.com/meta 의 `actions` 대역 등록 | 대역이 매우 많고 자주 바뀌어 관리가 어려움 |
| C. 자체 호스팅 러너 / AWS SSM | EC2에 러너 설치 또는 SSM 명령으로 배포 | 가장 안전하지만 `deploy.yml` 수정 필요(팀 승인) |

학기 프로젝트 규모에서는 **A + 키 파일 비공개 + 필요 없을 때 인스턴스 중지**가 현실적입니다.

## 4. 동작 확인

1. 아무 영향 없는 변경으로 확인하려면 Actions → **Deploy → Run workflow**(수동 실행)에서 대상을 골라 실행합니다.
   수동 실행은 선택한 대상에 **전체 배포**합니다(EC2는 전체 재빌드).
2. 성공 기준

   | 작업 | 기대 결과 |
   |---|---|
   | ci / Backend·RPA·Frontend·Docker | success |
   | 변경 경로 판별 | success |
   | Render (FastAPI) | `Render 배포를 요청했습니다.` → 헬스 체크 통과 |
   | AWS EC2 (docker compose) | `git pull` → `docker compose up` → `{"status":"ok"...}` |
   | Netlify (frontend) | `frontend/` 변경이 없으면 작업 자체가 skipped. 수동 실행 + Git 연동이면 "Netlify Git 연동(netlify.toml)으로 배포하거나 ..." 안내만 출력 — 둘 다 정상 |

3. 이후에는 평소처럼 `main`에 push하면 됩니다. 예: `backend/`만 바꾸면 Render + EC2(api)만 배포, `frontend/`를 바꾸면 Netlify·Render·EC2 모두, `docs/`만 바꾸면 배포 없음.
4. **Render 가격 수집 확인**: Actions → **Collect (Render)** → Run workflow → `collect` 실행
   - 성공 기준: "Render 깨우기"에서 `{"status":"ok"...}`, "작업 실행"에서 `{'status': 'SUCCESS', 'inserted': ..., 'duplicate': ...}`
   - 이후 매시 07분에 자동 실행됩니다(몇 분 늦을 수 있음). 실행 기록은 Actions → Collect (Render)에서 확인합니다.
   - 공개 저장소에 60일간 활동이 없으면 GitHub가 예약 실행을 멈춥니다. 그때는 이 화면에서 **Enable workflow**를 누릅니다.

## 5. 실패했을 때

| 단계 | 메시지 | 원인·해결 |
|---|---|---|
| EC2 | `Permission denied (publickey)` | `EC2_SSH_KEY` 내용 잘림/다른 키, `EC2_USER` 오타 |
| EC2 | `Connection timed out` | 보안 그룹 22번(3단계), `EC2_HOST` 오타, 인스턴스 중지 상태 |
| EC2 | `fatal: Not possible to fast-forward` | 서버에서 추적 파일을 직접 수정함 → 서버에서 `git status` 확인 후 되돌림 |
| EC2 | `required variable MYSQL_PASSWORD is missing a value` | EC2 `.env`에 placeholder 값 입력(08 문서 6단계) |
| Render | 헬스 체크 실패 | Render Logs 확인 — DB 접속 값, `JWT_SECRET`·`RPA_API_KEY` 누락 |
| Collect (Render) | "실행할 작업 결정"에서 건너뜀 안내 | Variable `RENDER_URL` 또는 Secret `RENDER_RPA_API_KEY` 미등록 |
| Collect (Render) | `401 ... INVALID_RPA_KEY` | `RENDER_RPA_API_KEY`가 Render의 `RPA_API_KEY`와 다름 |
| Collect (Render) | `Render 헬스 체크 실패` | Render 서비스 중지·배포 실패, `RENDER_URL` 오타 |

다음 문서: [11. 최종 점검과 문제 해결](11-checklist-troubleshooting.md)
