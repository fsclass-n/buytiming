# 09. [배포 4단계] Netlify ↔ Render 연결

현재 https://buytiming.netlify.app 은 `API_BASE_URL`이 비어 있는 **데모 모드**(브라우저 목업 데이터)로 동작합니다.
Render API(07 문서)가 `/health`에 정상 응답한 뒤 이 단계를 진행합니다.

## 1. Netlify 배포 방식 확인

Netlify → 사이트 → **Site configuration → Build & deploy → Continuous deployment**

| 화면 상태 | 배포 방식 | 이 문서에서 할 일 |
|---|---|---|
| Repository에 `fsclass-n/buytiming`이 연결됨 | **Git 연동** (Netlify가 `netlify.toml`대로 빌드) | 2단계 진행 |
| 저장소 연결 없음(수동 업로드·드래그 앤 드롭) | 수동 배포 — `build.sh`가 실행되지 않아 API 주소를 넣을 수 없음 | 저장소를 연결해 Git 연동으로 바꾸거나, 10 문서의 "Netlify를 Actions로 배포" 방식 사용 |

Git 연동일 때 빌드 설정은 저장소의 [`netlify.toml`](../netlify.toml)이 우선합니다: base `frontend`, command `sh build.sh`, publish `.`

## 2. 환경 변수 등록

Site configuration → **Environment variables** → Add a variable

| Key | Value |
|---|---|
| `API_BASE_URL` | `https://buytiming.onrender.com` |

- 끝에 `/`나 `/api/v1`을 붙이지 않습니다(프런트엔드가 `/api/v1`을 자동으로 붙임).
- Render 주소가 다르게 만들어졌다면 실제 주소를 넣습니다.

## 3. 다시 배포

환경 변수는 **다음 빌드부터** 반영됩니다. `frontend/`가 바뀌지 않으면 자동 빌드가 일어나지 않으므로 직접 실행합니다.

Deploys → **Trigger deploy → Deploy site** (또는 Clear cache and deploy site)

빌드 로그에 `config.js: API_BASE_URL=https://buytiming.onrender.com`이 보이면 성공입니다.

## 4. Render 쪽 CORS 확인

Render 환경 변수 `ALLOWED_ORIGINS`가 정확히 `https://buytiming.netlify.app`인지 확인합니다(07 문서).
값이 틀리면 브라우저 콘솔에 `blocked by CORS policy`가 나오고 화면에는 "API 서버에 연결할 수 없습니다"가 표시됩니다.

## 5. 동작 확인

1. https://buytiming.netlify.app/js/config.js → `API_BASE_URL: "https://buytiming.onrender.com"`
2. https://buytiming.netlify.app → 상단 "데모 모드" 배너가 사라지고 로그인 화면으로 이동
   (Render가 잠들어 있으면 첫 요청이 약 1분 걸립니다)
3. 시드 계정(08 문서 8단계에서 정한 비밀번호) 또는 회원가입으로 로그인 → 홈·검색·상세·AI 조언이 실제 데이터로 표시
4. 이전에 데모 모드로 접속했던 브라우저는 가짜 토큰 때문에 한 번 로그인 화면으로 이동합니다. 정상 동작입니다.

## 6. 데모 모드로 되돌리기 (문제 발생 시)

Environment variables에서 `API_BASE_URL`을 삭제(또는 빈 값) → Trigger deploy. 프런트엔드가 즉시 목업 데이터로 동작합니다.

다음 문서: [10. GitHub Actions 자동 배포 등록](10-github-actions-setup.md)
