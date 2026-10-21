#!/bin/sh
# Netlify 빌드 스크립트: 환경 변수 API_BASE_URL로 js/config.js를 생성한다.
# API_BASE_URL을 설정하지 않으면 데모 모드(브라우저 목업 API)로 배포된다.
set -eu
API_BASE_URL="${API_BASE_URL:-}"
cat > js/config.js <<EOF
window.APP_CONFIG = { API_BASE_URL: "${API_BASE_URL}" };
EOF
if [ -n "$API_BASE_URL" ]; then echo "config.js: API_BASE_URL=${API_BASE_URL}"; else echo "config.js: demo mode"; fi
