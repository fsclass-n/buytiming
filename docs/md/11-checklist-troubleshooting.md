# 11. 최종 점검과 문제 해결

## 1. 단계별 완료 점검표

### DB (06)
- [ ] TiDB Starter 인스턴스 생성, `buytiming` DB 생성
- [ ] 접속 문자열 확보(비밀번호 URL 인코딩), 허용 IP(EC2, Render, 개발 PC) 설정
- [ ] 시드 데이터 1회 입력(EC2 또는 PC), 데모·관리자 비밀번호 보관

### Render (07)
- [ ] 서비스 이름 `buytiming`, Docker, Singapore, Free, Health Check `/health`
- [ ] 환경 변수 10개 입력 (`APP_ENV`, `DATABASE_URL`, `DB_SSL_CA`, `JWT_SECRET`, `RPA_API_KEY`, `GEMINI_*`, `AI_DAILY_LIMIT`, `ALLOWED_ORIGINS`, `ADMIN_EMAILS`)
- [ ] Auto-Deploy **Off**
- [ ] https://buytiming.onrender.com/health → `"status":"ok"`, `"env":"production"`

### EC2 (08)
- [ ] Elastic IP 연결, DuckDNS가 Elastic IP를 가리킴
- [ ] 보안 그룹 80 개방, 22번은 GitHub Actions 접속 가능하게(10)
- [ ] `.env`: `APP_ENV=production`, TiDB 접속 값, `RPA_TARGET_API=http://api:8000`, `MYSQL_*` placeholder, `chmod 600`
- [ ] `docker compose ps` → api healthy, rpa·web running
- [ ] http://buytiming.duckdns.org/health → ok, 수동 `collect` 성공

### Netlify (09)
- [ ] `API_BASE_URL=https://buytiming.onrender.com` 등록 후 재배포
- [ ] 데모 배너 사라짐, 실제 로그인·검색·상세 동작

### GitHub Actions (10)
- [ ] Secrets: `RENDER_DEPLOY_HOOK_URL`, `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`
- [ ] Variables: `RENDER_HEALTH_URL` (필요 시 `EC2_APP_DIR`, `EC2_MODE=full`)
- [ ] Git 연동이면 `NETLIFY_*` Secret 미등록
- [ ] Deploy 워크플로 수동 실행 성공

### 데이터 흐름 최종 확인
- [ ] 매시 정각 이후 관리자 화면에 `collect_prices` SUCCESS 로그 추가
- [ ] Netlify(=Render API)와 duckdns(=EC2 API) 화면에서 같은 상품·같은 최신 가격이 보임 (같은 TiDB 공유 확인)

## 2. 자주 나는 문제

| 증상 | 확인할 곳 | 원인 → 해결 |
|---|---|---|
| Render 기동 실패: `운영 환경에서는 jwt_secret, rpa_api_key 값을 반드시 설정해야 합니다` | Render Logs | 해당 환경 변수가 비었거나 기본값 → 입력 |
| `(1045, "Access denied for user ...")` | api 로그 | TiDB 사용자 이름(`xxxx.root` 접두어 포함)·비밀번호 확인, 특수문자 URL 인코딩 |
| `Connections using insecure transport are prohibited` 또는 SSL 오류 | api 로그 | `DB_SSL_CA=/etc/ssl/certs/ca-certificates.crt` 누락 |
| `(1049, "Unknown database 'buytiming'")` | api 로그 | TiDB에서 `CREATE DATABASE buytiming;` |
| `Can't connect to MySQL server ... timed out` | api 로그 | TiDB 허용 IP 목록에 Render/EC2 IP 없음 |
| `Lost connection to MySQL server during query` (가끔) | api 로그 | TiDB Starter 유휴 연결 정리 — `pool_pre_ping`·`pool_recycle`로 자동 재연결됨. 반복되면 보고 |
| 화면: "API 서버에 연결할 수 없습니다" + 콘솔 `CORS` | 브라우저 F12 콘솔 | Render `ALLOWED_ORIGINS`에 `https://buytiming.netlify.app` 정확히 입력(끝 `/` 없이) |
| Netlify가 계속 데모 모드 | `/js/config.js` 내용 | 환경 변수 등록 후 재배포 안 함, 또는 수동 업로드 사이트(09 문서 1단계) |
| Netlify 첫 화면이 1분 가까이 멈춤 | — | Render 무료 플랜이 잠들었다 깨는 중. 정상 |
| `docker compose up`: `required variable MYSQL_PASSWORD is missing a value` | EC2 터미널 | `.env`에 `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` placeholder 입력 |
| rpa 로그: `Connection refused ... localhost:8000` | `docker compose logs rpa` | `.env`의 `RPA_TARGET_API`를 `http://api:8000`으로 |
| rpa 로그: `401 ... INVALID_RPA_KEY` | `docker compose logs rpa` | api와 rpa가 읽는 `RPA_API_KEY`가 다름 → `.env` 하나만 쓰므로 값 확인 후 `docker compose up -d` |
| EC2 빌드 중 멈춤·`Killed` | `free -h`, `dmesg` | 메모리 부족 → 스왑 2 GB(08 문서 4단계) 또는 t3.small |
| 관리자 메뉴가 안 보임 | — | 시드의 `admin@buytiming.demo`로 로그인하거나, `ADMIN_EMAILS`에 넣은 이메일로 **새로 가입**(기존 계정은 자동 변경 안 됨) |
| AI 조언이 항상 비슷한 문장 | `/health`의 `"gemini"` | `false`면 키 없음 → 템플릿 문장으로 동작(정상 대체 동작) |
| `429 AI_LIMIT_EXCEEDED` | — | 사용자별 일일 한도(`AI_DAILY_LIMIT`) 초과 |

## 3. 되돌리기

| 대상 | 방법 |
|---|---|
| Netlify | Deploys에서 이전 배포 선택 → **Publish deploy**, 또는 `API_BASE_URL` 삭제 후 재배포(데모 모드) |
| Render | Events/Deploys에서 이전 배포 **Rollback**(무료 플랜은 최근 2개까지) |
| EC2 | `git log`로 이전 커밋 확인 → 문제 커밋을 GitHub에서 revert해 `main`에 push(자동 재배포). 서버에서 직접 checkout하지 않음 |
| DB | TiDB Starter의 백업·복원 기능 확인. 시드/테스트를 운영 DB에 실행하지 않는 것이 최선 |

## 4. 보안 마무리

- `.env`, `.pem`, Deploy Hook URL, TiDB 비밀번호는 Git·메신저 공개 채널에 올리지 않습니다.
- 값이 노출되면: TiDB 비밀번호 Reset, Render Deploy Hook Regenerate, `JWT_SECRET`·`RPA_API_KEY` 교체(Render와 EC2 동시), EC2 키 페어 교체.
- 운영 데이터가 들어간 뒤에는 `python -m app.seed --reset`, `pytest`를 TiDB 주소로 실행하지 않습니다.

처음으로: [문서 목록](README.md)
