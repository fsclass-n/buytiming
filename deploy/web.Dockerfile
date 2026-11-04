# EC2 web 이미지: React 빌드(node) → nginx 정적 서빙 + /api 프록시. 빌드 컨텍스트 = 저장소 루트
FROM node:22-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /src/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/config.same-origin.js /etc/nginx/app-config.js
