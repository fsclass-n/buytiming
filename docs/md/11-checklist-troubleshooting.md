# 11. 최종 점검과 문제 해결

## 1. 단계별 완료 점검표

### DB · `.env` (06)
- [ ] TiDB Starter 인스턴스 생성, `buytiming` DB 생성, 허용 IP(개발 PC, EC2, Render) 설정
- [ ] 로컬 `.env` 작성: `copy .env.example .env` → `DATABASE_URL`(TiDB), `JWT_SECRET`, `RPA_API_KEY` 채움 (나머지 필수 값은 예시 그대로)
- [ ] 로컬에서 `python -m app.seed` 1회, 데모·관리자 비밀번호 보관
- [ ] 로컬 `uvicorn app.main:app --reload` → http://localhost:8000 화면·로그인 동작

### Render — 단독 풀스택 (07)
- [ ] 서비스 이름 `buytiming`, Docker, Singapore, Free, Health Check `/health`
- [ ] Dockerfile Path `./backend/Dockerfile.render`, Build Context `.`
- [ ] Environment → **Add from .env**로 로컬 `.env` 붙여 넣기 (`FRONTEND_DIR`은 넣지 않음)
- [ ] Auto-Deploy **After CI Checks Pass**, Build Filters Included Paths `backend/**`, `frontend/**`, `render.yaml`, `.dockerignore`
- [ ] `/health` → `"status":"ok"`, `/` → 홈 화면, `/js/config.js` → `API_BASE_URL: "/"`

### EC2 — 단독 풀스택 (08)
- [ ] Elastic IP 연결, DuckDNS가 Elastic IP를 가리킴
- [ ] 보안 그룹 80 개방, 22번은 GitHub Actions 접속 가능하게(10)
- [ ] 로컬 `.env`를 `scp`로 `~/buytiming/.env`에 복사, `chmod 600`
- [ ] `docker compose ps` → api healthy, rpa·web running
- [ ] http://buytiming.duckdns.org/health → ok, 수동 `collect` 성공

### Netlify — 데모 모드 (09)
- [ ] 환경 변수 `API_BASE_URL` 없음, `/js/config.js` → `API_BASE_URL: ""`, 데모 배너 표시

### GitHub Actions (10)
- [ ] Secrets: `RENDER_RPA_API_KEY`(= `.env`의 `RPA_API_KEY`), `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` — `RENDER_DEPLOY_HOOK_URL`은 등록하지 않음
- [ ] Variables: `RENDER_URL` (필요 시 `EC2_APP_DIR`, `EC2_MODE=full`)
- [ ] Git 연동이면 `NETLIFY_*` Secret 미등록
- [ ] Deploy 워크플로 수동 실행 성공, Collect (Render) 수동 실행 성공

### 독립 동작·데이터 흐름 최종 확인
- [ ] 매시 이후 관리자 화면에 `collect_prices` 로그가 두 곳(EC2 정각, Actions 07분)에서 추가 — 나중 쪽은 저장 0건일 수 있음(중복 방지, 정상)
- [ ] Render와 duckdns 화면에서 같은 계정으로 로그인되고 같은 상품·같은 최신 가격이 보임 (같은 TiDB 공유)
- [ ] EC2를 잠시 멈춰도 Render 화면·API·Actions 수집이 계속 동작 (반대도 동일)

## 2. 자주 나는 문제

| 증상 | 확인할 곳 | 원인 → 해결 |
|---|---|---|
| Render 기동 실패: `운영 환경에서는 jwt_secret, rpa_api_key 값을 반드시 설정해야 합니다` | Render Logs | 해당 환경 변수가 비었거나 기본값 → 입력 |
| `(1045, "Access denied for user ...")` | api 로그 | TiDB 사용자 이름(`xxxx.root` 접두어 포함)·비밀번호 확인, 특수문자 URL 인코딩 |
| `Connections using insecure transport are prohibited` 또는 SSL 오류 | api 로그 | `.env`의 `DB_SSL_CA=/etc/ssl/certs/ca-certificates.crt` 누락(값이 비면 TLS를 쓰지 않음) |
| 로컬에서 `CERTIFICATE_VERIFY_FAILED` | 터미널 | 회사·학원 프록시가 TLS를 가로채는 경우. 다른 네트워크에서 확인하거나 프록시 루트 인증서 파일 경로를 `DB_SSL_CA`에 지정 |
| `(1049, "Unknown database 'buytiming'")` | api 로그 | TiDB에서 `CREATE DATABASE buytiming;` |
| `Can't connect to MySQL server ... timed out` | api 로그 | TiDB 허용 IP 목록에 Render/EC2 IP 없음 |
| `Lost connection to MySQL server during query` (가끔) | api 로그 | TiDB Starter 유휴 연결 정리 — `pool_pre_ping`·`pool_recycle`로 자동 재연결됨. 반복되면 보고 |
| Render `/`가 화면 대신 `{"service":"BuyTiming API",...}` JSON | Render Settings | Dockerfile Path가 `./backend/Dockerfile`(API 전용)로 되어 있음 → `./backend/Dockerfile.render`, Build Context `.` |
| Render 화면이 "데모 모드" 배너로 뜸 | `/js/config.js` | 위와 같은 원인(예전 이미지). 설정 변경 후 재배포 |
| 화면: "API 서버에 연결할 수 없습니다" | 브라우저 F12 콘솔·Network | 같은 도메인 호출이라 CORS 문제는 아님 → `/health` 응답과 서버 로그 확인 |
| Render 첫 화면이 1분 가까이 멈춤 | — | 무료 플랜이 잠들었다 깨는 중. 정상 |
| Netlify가 실제 데이터를 안 보여 줌 | — | 의도된 동작(데모 모드 유지, 09 문서) |
| Collect (Render) 실패: `401 INVALID_RPA_KEY` | Actions 로그 | Secret `RENDER_RPA_API_KEY` ≠ Render `RPA_API_KEY` |
| 수집 결과 `inserted: 0, duplicate: N` | — | 같은 시간대에 다른 수집기(EC2/Actions)가 먼저 저장함. 정상 |
| Render에서 push 후 자동 배포가 안 됨 | Render Events, GitHub 커밋의 검사 결과 | Auto-Deploy = After CI Checks Pass인지, 실패한 검사가 없는지, 바뀐 경로가 Build Filter에 포함되는지 |
| Render 화면이 사라지고 JSON만 나옴(설정 붙여 넣은 뒤) | Render Environment | `FRONTEND_DIR`이 들어가 있으면 삭제(Dockerfile 값 사용) |
| rpa 로그: `Connection refused ... localhost:8000` | `docker compose logs rpa` | EC2 `.env`에서 `RPA_TARGET_API` 줄 삭제(compose 기본값 `http://api:8000` 사용) |
| rpa 로그: `401 ... INVALID_RPA_KEY` | `docker compose logs rpa` | `.env`를 바꾼 뒤 컨테이너를 다시 만들지 않음 → `docker compose up -d` |
| EC2 빌드 중 멈춤·`Killed` | `free -h`, `dmesg` | 메모리 부족 → 스왑 2 GB(08 문서 4단계) 또는 t3.small |
| 관리자 메뉴가 안 보임 | — | 시드의 `admin@buytiming.demo`로 로그인하거나, `ADMIN_EMAILS`에 넣은 이메일로 **새로 가입**(기존 계정은 자동 변경 안 됨) |
| AI 조언이 항상 비슷한 문장 | `/health`의 `"gemini"` | `false`면 키 없음 → 템플릿 문장으로 동작(정상 대체 동작) |
| `429 AI_LIMIT_EXCEEDED` | — | 사용자별 일일 한도(`AI_DAILY_LIMIT`) 초과 |

## 3. 되돌리기

| 대상 | 방법 |
|---|---|
| Netlify | Deploys에서 이전 배포 선택 → **Publish deploy** |
| Render 가격 수집 | Actions → Collect (Render) → ··· → **Disable workflow** (EC2 수집은 계속됨) |
| Render | Events/Deploys에서 이전 배포 **Rollback**(무료 플랜은 최근 2개까지) |
| EC2 | `git log`로 이전 커밋 확인 → 문제 커밋을 GitHub에서 revert해 `main`에 push(자동 재배포). 서버에서 직접 checkout하지 않음 |
| DB | TiDB Starter의 백업·복원 기능 확인. 시드/테스트를 운영 DB에 실행하지 않는 것이 최선 |

## 4. 보안 마무리

- `.env`, `.pem`, TiDB 비밀번호는 Git·메신저 공개 채널에 올리지 않습니다. `.env` 하나가 세 환경 공용이므로 유출 시 영향이 큽니다.
- 값이 노출되면: 로컬 `.env`에서 TiDB 비밀번호(Reset)·`JWT_SECRET`·`RPA_API_KEY`를 교체 → EC2로 다시 `scp`, Render에 다시 붙여 넣기,
  GitHub Secret `RENDER_RPA_API_KEY`도 같은 값으로 교체, EC2 키 페어 교체.
- `python -m app.seed --reset`과 `TEST_DATABASE_URL=<TiDB>` 테스트는 운영 데이터를 지우므로 실행하지 않습니다(일반 `pytest`는 임시 SQLite라 안전).

처음으로: [문서 목록](README.md)
