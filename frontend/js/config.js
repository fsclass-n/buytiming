// Netlify 빌드 시 build.sh가 환경 변수 API_BASE_URL 값으로 이 파일을 다시 생성한다.
// API_BASE_URL이 비어 있으면 데모 모드(브라우저 내 목업 API)로 동작한다.
//   예) "https://buytiming-api.onrender.com"  /  "http://<EC2 주소>"  /  "/" (같은 도메인의 /api/v1)
window.APP_CONFIG = { API_BASE_URL: "" };
