# 09. [배포 4단계] Netlify — 프런트엔드 전용 (데모 모드 유지)

https://buytiming.netlify.app 은 **프런트엔드 시연용**으로 유지합니다. 서버·DB와 연결하지 않고,
[`frontend/js/mock.js`](../../frontend/js/mock.js)가 백엔드와 같은 형식의 응답을 브라우저에서 만들어 모든 화면이 동작합니다.
실제 데이터가 필요한 사용자는 Render(https://buytiming.onrender.com) 또는 EC2(http://buytiming.duckdns.org)를 사용합니다.

## 1. 할 일: 없음 (확인만)

| 확인 항목 | 방법 | 기대 결과 |
|---|---|---|
| 데모 모드 | https://buytiming.netlify.app/js/config.js | `API_BASE_URL: ""` |
| 화면 | https://buytiming.netlify.app | 상단 "데모 모드" 배너, 아무 이메일·비밀번호로 로그인 가능 |
| 관리자 화면 | `admin@`으로 시작하는 이메일로 로그인 | 관리자 메뉴 표시 |
| 환경 변수 | Site configuration → Environment variables | **`API_BASE_URL`이 없어야 함** |

## 2. 배포 방식

- Netlify → Site configuration → Build & deploy → Continuous deployment에 저장소 `fsclass-n/buytiming`이 연결되어 있으면
  **Git 연동**입니다. `frontend/`가 바뀐 커밋이 `main`에 올라오면 Netlify가 [`netlify.toml`](../../netlify.toml)대로
  (`base = "frontend"`, `sh build.sh`) 다시 빌드합니다. `API_BASE_URL`이 없으므로 항상 데모 모드로 빌드됩니다.
- Git 연동이면 GitHub Secret `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID`를 등록하지 않습니다(중복 배포 방지, 10 문서).

## 3. 주의

- Netlify 환경 변수에 `API_BASE_URL`을 넣으면 그 주소의 API를 호출하게 됩니다. 이번 구성에서는 넣지 않습니다.
  (나중에 넣는다면 대상 서버의 `ALLOWED_ORIGINS`에 `https://buytiming.netlify.app`을 추가해야 CORS 오류가 나지 않습니다.)
- 데모 모드에서 바꾼 데이터(관심 상품 등)는 그 브라우저의 `localStorage`에만 저장됩니다. 다른 브라우저·기기와 공유되지 않습니다.

다음 문서: [10. GitHub Actions 등록](10-github-actions-setup.md)
