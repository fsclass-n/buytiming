# 03. 프런트엔드 (Netlify 정적 사이트)

소스: [`frontend/`](../../frontend). 빌드 도구·npm 없이 HTML + ES Modules로 동작합니다.

## 1. 화면 10개

| 파일 | 화면 | 스크립트 | 로그인 |
|---|---|---|---|
| `index.html` | 홈(오늘의 적기·하락 상품) | `js/pages/home.js` | 필요 |
| `login.html` / `signup.html` | 로그인 / 회원가입 | `login.js` / `signup.js` | 불필요 |
| `search.html` | 상품 검색·URL 등록 | `search.js` | 필요 |
| `product.html` | 상품 상세(가격 비교·차트·적기 판정·AI 조언) | `product.js` | 필요 |
| `chat.html` | AI 상담 | `chat.js` | 필요 |
| `watchlist.html` | 관심 상품·목표가 | `watchlist.js` | 필요 |
| `alerts.html` | 알림 | `alerts.js` | 필요 |
| `admin.html` | 관리자: 수집·모델 현황 | `admin.js` | ADMIN |
| `admin-ai.html` | 관리자: AI 사용량 | `admin-ai.js` | ADMIN |

공통 레이아웃·로그인 확인은 [`js/common.js`](../../frontend/js/common.js)의 `initPage()`가 담당합니다.

## 2. API 주소 결정 방식 (가장 중요)

모든 HTML은 `js/config.js`를 먼저 불러온 뒤 화면 스크립트를 실행합니다.

```js
// js/config.js
window.APP_CONFIG = { API_BASE_URL: "" };
```

[`js/api.js`](../../frontend/js/api.js)의 동작:

| `API_BASE_URL` 값 | 동작 | 사용처 |
|---|---|---|
| `""` (빈 값) | **데모 모드** — 서버 없이 [`js/mock.js`](../../frontend/js/mock.js)가 응답. 화면 상단에 "데모 모드" 배너 | **Netlify(운영 — 데모 모드 유지)**, 로컬 |
| `/` | 같은 도메인의 `/api/v1/...` 호출 | **Render(FastAPI)**, **EC2(nginx)** |
| `https://<다른 주소>` | 다른 도메인의 API 호출 (CORS 설정 필요) | 현재 사용하지 않음 |

### 환경별로 config.js가 바뀌는 방법

- **Netlify**: [`netlify.toml`](../../netlify.toml) → `base = "frontend"`, `command = "sh build.sh"`.
  [`build.sh`](../../frontend/build.sh)가 Netlify 환경 변수 `API_BASE_URL` 값으로 `js/config.js`를 빌드할 때마다 새로 만듭니다.
  이 변수를 **등록하지 않으므로** 빈 값 → 데모 모드입니다.
- **Render·로컬**: FastAPI가 `/js/config.js` 요청에 `API_BASE_URL: "/"`를 직접 응답합니다([`main.py`](../../backend/app/main.py)).
  Render는 Dockerfile의 `FRONTEND_DIR=/app/frontend`, 로컬은 저장소의 `frontend/`를 자동으로 찾아 서빙합니다(http://localhost:8000).
- **EC2**: nginx가 `/js/config.js` 요청을 [`deploy/config.same-origin.js`](../../deploy/config.same-origin.js)(`API_BASE_URL: "/"`)로 바꿔서 응답합니다([`deploy/nginx.conf`](../../deploy/nginx.conf)).
- **저장소에 커밋되는 config.js**는 항상 `API_BASE_URL: ""`(데모 모드)로 유지합니다. 로컬에서 `build.sh`를 실행해 바뀐 파일은 커밋하지 않습니다.

## 3. 로그인·토큰

- 로그인 성공 시 JWT를 `localStorage`(`bt_token`, `bt_user`)에 저장하고 `Authorization: Bearer ...` 헤더로 보냅니다.
- API가 401을 돌려주면 토큰을 지우고 `login.html?next=...`로 이동합니다.
- 토큰은 도메인별로 따로 저장됩니다. Netlify(데모)·Render·EC2에서 각각 로그인합니다. Render와 EC2는 같은 DB를 쓰므로 **같은 계정**으로 로그인할 수 있습니다.
- 데모 모드에서는 아무 이메일·비밀번호로 로그인되지만, **실제 API에서는 회원가입하거나 시드 계정(02 문서)으로 로그인**해야 합니다.

## 4. 보안 헤더·캐시

`netlify.toml`에서 `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`를 설정하고,
`/js/config.js`는 `Cache-Control: no-cache`로 API 주소 변경이 바로 반영되게 합니다. EC2 nginx와 Render(FastAPI)도 `X-Frame-Options`, `nosniff`, `Referrer-Policy`를 붙입니다.

## 5. CI 검사·배포

`.github/workflows/ci.yml`의 Frontend 작업이 `frontend/js/*.js`, `frontend/js/pages/*.js`를 `node --check`로 문법 검사하고,
`build.sh`가 `API_BASE_URL`을 config.js에 제대로 넣는지 확인합니다. Docker 작업은 Render 풀스택 이미지를 빌드해 `/`와 `/js/config.js`가 제대로 나오는지 확인합니다.

`frontend/`를 바꿔 `main`에 push하면 **Netlify, Render, EC2 세 곳 모두** 새 화면이 배포됩니다(05 문서).

다음 문서: [04. RPA 수집기](04-rpa.md)
