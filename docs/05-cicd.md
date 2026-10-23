# 05. CI/CD 파이프라인 (GitHub Actions)

소스: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml),
[`.github/scripts/detect-changes.sh`](../.github/scripts/detect-changes.sh)

## 1. 언제 무엇이 도는가

| 이벤트 | 워크플로 | 내용 |
|---|---|---|
| `main` 외 브랜치 push, Pull Request | `ci.yml` | 검사만 (배포 없음) |
| `main` push | `deploy.yml` | `ci.yml` 전체 통과 → **바뀐 폴더에 해당하는 대상만** 배포 |
| 수동 실행 (Actions → Deploy → Run workflow) | `deploy.yml` | 체크한 대상(Netlify/Render/EC2)에 전체 배포 |

## 2. CI 작업 (`ci.yml`)

| 작업 | 내용 |
|---|---|
| Backend (lint · pytest on SQLite) | `ruff check backend`, `pytest` |
| Backend (pytest on MySQL 8) | MySQL 8.0 서비스 컨테이너에서 같은 테스트 (TiDB 호환성 사전 확인) |
| RPA (lint · pytest) | `ruff check rpa`, `pytest` |
| Frontend | JS 문법 검사, `build.sh` 동작 확인 |
| Docker build | api·rpa 이미지 빌드, API 컨테이너 `/health` 확인, `docker compose config` 검증 |

## 3. 배포 대상 판별 (`detect-changes.sh`)

직전 push와 비교해 바뀐 파일 경로로 대상을 정합니다.

| 바뀐 경로 | Netlify | Render | EC2 (full) |
|---|:---:|:---:|:---:|
| `frontend/` | ✅ | – | ✅ (git pull만으로 반영) |
| `netlify.toml` | ✅ | – | – |
| `backend/` | – | ✅ | ✅ (api만 재빌드) |
| `render.yaml` | – | ✅ | – |
| `rpa/` | – | – | ✅ (rpa만 재빌드) |
| `docker-compose.yml` | – | – | ✅ (전체 재빌드) |
| `deploy/` | – | – | ✅ (nginx 재시작) |
| 그 외 (`docs/`, `README.md`, `.claude/`, 워크플로 등) | – | – | – |

- 이번 구성은 **EC2 full 모드**(nginx + api + rpa)입니다. `EC2_MODE` 변수는 등록하지 않거나 `full`로 둡니다.
- `backend/`와 `rpa/`가 함께 바뀌면 Render를 먼저 배포한 뒤 EC2를 배포합니다.
- 비교 기준 커밋이 없는 첫 push·강제 push는 모든 대상에 배포합니다.

로컬에서 미리 확인:

```bash
CHANGED_FILES="backend/app/main.py" EVENT=push bash .github/scripts/detect-changes.sh
```

## 4. 대상별 배포 방식

| 대상 | 방식 | 필요한 값 (없으면 그 대상만 건너뜀) |
|---|---|---|
| Render | Deploy Hook URL에 POST → 60초 대기 후 헬스 체크(최대 5분) | Secret `RENDER_DEPLOY_HOOK_URL`, Variable `RENDER_HEALTH_URL` |
| EC2 | SSH 접속 → `git pull --ff-only origin main` → 바뀐 서비스만 `docker compose up -d --build` → `http://localhost/health` 확인 | Secrets `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, Variable `EC2_APP_DIR`(기본 `~/buytiming`) |
| Netlify | (Actions 방식) `build.sh` → zip을 Netlify API로 업로드 | Secrets `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID`, Variable `API_BASE_URL` |

> Netlify는 **Git 연동(Netlify가 저장소를 직접 빌드)과 Actions 방식 중 하나만** 씁니다. 이미 Git 연동으로 배포했다면
> `NETLIFY_*` Secret을 등록하지 않습니다(중복 배포 방지). 자세한 내용은 [09](09-netlify-connect.md), [10](10-github-actions-setup.md).

다음 문서: [06. DB 준비](06-database.md)
