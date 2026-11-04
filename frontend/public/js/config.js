// API 주소. 비어 있으면 데모 모드(브라우저 목업 API) — Netlify는 이 파일 그대로 배포된다.
// Render(FastAPI)·EC2(nginx)는 이 경로를 API_BASE_URL: "/"(같은 도메인)로 바꿔 응답한다.
window.APP_CONFIG = { API_BASE_URL: "" };
