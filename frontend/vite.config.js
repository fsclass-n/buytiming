import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// 개발 서버(npm run dev): /api·/health는 로컬 FastAPI(8000)로 프록시하고, /js/config.js는 같은 도메인 설정을 돌려준다.
// 운영 빌드(npm run build)의 public/js/config.js는 데모 모드("")이며, Render(FastAPI)·EC2(nginx)가 같은 도메인 설정으로 바꿔 응답한다.
const sameOriginConfig = {
  name: 'same-origin-config',
  configureServer(server) {
    server.middlewares.use('/js/config.js', (req, res) => {
      res.setHeader('Content-Type', 'application/javascript');
      res.end(`window.APP_CONFIG = { API_BASE_URL: "${process.env.VITE_DEMO ? '' : '/'}" };`);
    });
  },
};

export default defineConfig({
  plugins: [react(), tailwindcss(), sameOriginConfig],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8000', '/health': 'http://localhost:8000', '/docs': 'http://localhost:8000', '/openapi.json': 'http://localhost:8000' },
  },
  build: { outDir: 'dist', chunkSizeWarningLimit: 900 },
});
