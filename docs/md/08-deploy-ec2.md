# 08. [배포 3단계] AWS EC2 — 단독 풀스택 (http://buytiming.duckdns.org)

EC2 한 대에서 [`docker-compose.yml`](../../docker-compose.yml)의 세 컨테이너로 화면·API·가격 수집을 모두 운영합니다.
Render를 호출하지 않으며, DB만 **TiDB**(Render와 공유)를 씁니다.

| 컨테이너 | 역할 |
|---|---|
| `web` (nginx:1.27-alpine) | 80번 포트. `frontend/` 정적 파일 + `/api`, `/docs`, `/health`를 `api`로 프록시 |
| `api` (backend 이미지) | FastAPI, TiDB 접속 |
| `rpa` (rpa 이미지) | 스케줄러 — 매시 수집 등, `http://api:8000` 호출 |
| `mysql` | `localdb` 프로필 전용 — **이번 구성에서는 사용하지 않음** |

## 1. EC2 인스턴스 만들기

| 항목 | 권장값 |
|---|---|
| AMI | Ubuntu Server 24.04 LTS (22.04도 가능) |
| 인스턴스 유형 | t3.small(2 GB) 권장. 프리 티어 t2/t3.micro(1 GB)도 가능하나 **스왑 2 GB 필수**(아래 4단계) |
| 키 페어 | 새로 생성(.pem) → 안전하게 보관. GitHub Actions에도 등록함(10 문서) |
| 스토리지 | 20 GB 이상 (Docker 이미지 2개 + 빌드 캐시) |
| 보안 그룹 인바운드 | 22(SSH), 80(HTTP, 0.0.0.0/0), 443(HTTPS 구성 시) — 22번은 10 문서의 주의사항 참고 |

## 2. 고정 IP와 DuckDNS

1. EC2 → **Elastic IP** 할당 → 인스턴스에 연결 (재시작해도 IP가 바뀌지 않게)
2. https://www.duckdns.org 로그인 → 서브도메인 `buytiming`의 **current ip**를 Elastic IP로 입력 → update ip
3. PC에서 확인: `nslookup buytiming.duckdns.org` → Elastic IP가 나오면 성공
4. TiDB의 허용 IP 목록이 있다면 이 Elastic IP를 추가(06 문서)

## 3. 접속

```bash
ssh -i buytiming.pem ubuntu@buytiming.duckdns.org
```

## 4. (micro 인스턴스만) 스왑 2 GB 만들기

pandas·scikit-learn 이미지 빌드와 실행에 메모리가 부족할 수 있습니다.

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 5. 저장소 받기 + Docker 설치 ([`deploy/ec2-setup.sh`](../../deploy/ec2-setup.sh))

스크립트는 상태에 따라 한 단계씩 진행합니다. 여기서 **두 번** 실행하고, 기동은 6단계(.env 작성) 후 7단계에서 직접 합니다.

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/fsclass-n/buytiming.git ~/buytiming

# 1회차: Docker 설치 후 종료 → 로그아웃했다가 다시 SSH 접속(docker 그룹 적용)
bash ~/buytiming/deploy/ec2-setup.sh https://github.com/fsclass-n/buytiming.git
exit

# 2회차: .env.example을 복사해 ~/buytiming/.env를 만들고 종료
bash ~/buytiming/deploy/ec2-setup.sh https://github.com/fsclass-n/buytiming.git
```

## 6. `~/buytiming/.env` 작성 (가장 중요)

`ec2-setup.sh`가 복사한 `.env`(예시 파일)는 로컬 개발용 항목까지 있어 복잡합니다. **아래 최소 버전으로 통째로 바꿉니다.**

```bash
nano ~/buytiming/.env      # 기존 내용을 모두 지우고 아래를 붙여 넣은 뒤 < > 부분만 바꿈
chmod 600 ~/buytiming/.env
```

```dotenv
APP_ENV=production
DATABASE_URL=mysql+pymysql://<TiDB USER>:<URL 인코딩한 비밀번호>@<TiDB HOST>:4000/buytiming?charset=utf8mb4
DB_SSL_CA=/etc/ssl/certs/ca-certificates.crt
JWT_SECRET=<무작위 긴 문자열>
RPA_API_KEY=<무작위 긴 문자열>
ALLOWED_ORIGINS=http://buytiming.duckdns.org
RPA_TARGET_API=http://api:8000
MYSQL_PASSWORD=unused
MYSQL_ROOT_PASSWORD=unused
```

선택 항목(필요할 때만 추가): `GEMINI_API_KEY=<키>`, `ADMIN_EMAILS=<이메일>`, `KCA_API_URL`·`DATA_GO_KR_KEY`(참가격), `SEED_DEMO_PASSWORD`·`SEED_ADMIN_PASSWORD`.
나머지(`GEMINI_MODEL`, `AI_DAILY_LIMIT`, `JWT_EXPIRE_MINUTES`, `TZ`, `REQUEST_INTERVAL_SEC`, `SIMULATE_MALLS`)는 기본값이 있어 넣지 않아도 됩니다.

| 항목 | 이유 |
|---|---|
| `DATABASE_URL`, `DB_SSL_CA` | Render와 **같은 값**(같은 TiDB 공유) |
| `JWT_SECRET`, `RPA_API_KEY` | EC2 전용 값. Render와 **달라도 됨**(독립 운영). `RPA_API_KEY`는 같은 `.env`를 api·rpa가 함께 읽으므로 자동으로 일치 |
| `ALLOWED_ORIGINS` | 화면과 API가 같은 도메인이라 CORS가 필요 없으므로 자기 주소만 허용 |
| `RPA_TARGET_API=http://api:8000` | 예시 파일의 `http://localhost:8000`이 남아 있으면 compose가 그 값을 우선 사용 → 수집기가 API에 연결 못 함 |
| `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` | 로컬 MySQL은 쓰지 않지만, compose는 프로필과 관계없이 파일 전체의 `${VAR:?}`를 검사 → 비어 있으면 `docker compose up` 자체가 오류 |

- 값에 `$`가 들어 있으면 compose가 변수로 해석합니다. 그런 값은 작은따옴표로 감쌉니다(`JWT_SECRET='ab$cd'`).

## 7. 기동

```bash
cd ~/buytiming
docker compose config -q && echo "compose OK"      # .env 검증
docker compose up -d --build                         # 첫 빌드는 수 분 소요
docker compose ps                                    # api: healthy, rpa·web: running
curl -fsS http://localhost/health                    # {"status":"ok","env":"production",...}
```

PC 브라우저: http://buytiming.duckdns.org (프런트엔드), http://buytiming.duckdns.org/docs (API 문서)

## 8. 시드 데이터 (TiDB에 아직 데이터가 없을 때 1회)

```bash
docker compose exec -e SEED_DEMO_PASSWORD='<데모 비번>' -e SEED_ADMIN_PASSWORD='<관리자 비번>' api python -m app.seed
```

TiDB를 Render와 공유하므로 여기서 한 번 넣으면 Render API에서도 보입니다.

## 9. RPA 동작 확인

```bash
docker compose logs -f rpa                                   # "scheduler started (tz=Asia/Seoul, api=http://api:8000)"
docker compose exec rpa python -m collector.jobs collect     # 즉시 1회 수집 → {'status': 'SUCCESS', 'inserted': 36, 'duplicate': 0, ...} (시드 기준 12상품 × 3쇼핑몰)
# 같은 시간대에 Render용 Actions 수집이 먼저 돌았다면 'inserted': 0, 'duplicate': 36 — 중복 방지가 동작한 것(정상)
```

관리자 계정으로 로그인 → 관리자 화면에서 수집 로그가 쌓이는지 확인합니다.

## 10. 운영 명령 모음

| 목적 | 명령 |
|---|---|
| 로그 | `docker compose logs -f --tail 100 api` (rpa, web) |
| 재시작 | `docker compose restart api` |
| 수동 업데이트 | `git pull --ff-only origin main && docker compose up -d --build` |
| 디스크 정리 | `docker image prune -f`, 확인 `df -h` |
| 주간 리포트 | `ls ~/buytiming/reports/` |

- 서버에서 저장소 파일(추적 대상)을 직접 수정하지 않습니다. 자동 배포의 `git pull --ff-only`가 실패합니다. 설정은 `.env`(Git 제외)에서만 바꿉니다.

## 11. (선택) HTTPS 구성

EC2는 HTTP만으로도 동작하지만, http://buytiming.duckdns.org 화면은 로그인 비밀번호가 암호화되지 않은 채 전송되므로
시연·운영 전에 HTTPS를 권장합니다. HTTPS로 바꾸면 `.env`의 `ALLOWED_ORIGINS`도 `https://buytiming.duckdns.org`로 바꿉니다.

- 방법: Let's Encrypt(certbot)로 `buytiming.duckdns.org` 인증서 발급 → nginx에 443 서버 블록 추가·80→443 리다이렉트 →
  compose `web`에 `443:443` 포트와 인증서 볼륨 추가 → 보안 그룹 443 열기 → 인증서 자동 갱신 설정
- `deploy/nginx.conf`, `docker-compose.yml`을 바꾸는 작업이므로(EC2 전체 재배포 발생) 별도 작업으로 팀 승인 후 진행합니다.

다음 문서: [09. Netlify (데모 모드 유지)](09-netlify-connect.md)
