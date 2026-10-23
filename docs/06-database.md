# 06. [배포 1단계] DB 준비 — TiDB(운영) · MySQL 8(개발)

## 1. 역할 정리

| DB | 용도 | 사용하는 곳 |
|---|---|---|
| **TiDB Cloud Starter** | 운영 DB **하나** | Render API, EC2 API(+RPA) — 같은 접속 문자열 |
| **MySQL 8** | 개발·통합 테스트 | 개발자 PC, GitHub Actions CI(이미 구성됨) |
| SQLite | 빠른 로컬 실행·단위 테스트 | 개발자 PC, CI |

코드 변경은 필요 없습니다. 백엔드는 `DATABASE_URL`만 보고 SQLite / MySQL·TiDB를 구분하며([`database.py`](../backend/app/database.py)),
`DB_SSL_CA`가 있으면 TLS로 접속합니다. 연결은 280초마다 재생성(`pool_recycle=280`)되어, 유휴 연결을 끊는 TiDB Starter의 특성(공식 문서 권장값 300초)에 맞춰져 있습니다.

## 2. TiDB Cloud 준비

1. https://tidbcloud.com 가입 → **Starter**(무료) 인스턴스 생성
   - 리전: Render 서비스가 `singapore`이므로 **AWS Singapore**를 권장합니다(Render ↔ DB 지연 최소). EC2도 가까운 리전이면 좋습니다.
   - 무료 한도(인스턴스당): 행 저장소 5 GiB, 월 5,000만 RU. 이 프로젝트 규모에는 충분합니다.
2. 인스턴스 → 우측 상단 **Connect**
   - Connection Type: `Public`, Connect With: `General`
   - **Generate Password**로 비밀번호 생성 → 안전한 곳에 보관(다시 볼 수 없음)
   - 표시되는 값: `HOST`(예: `gateway01.<리전>.prod.aws.tidbcloud.com`), `PORT`(4000), `USER`(예: `xxxxxxxx.root`)
3. 접근 허용 IP(IP Access List / Firewall 규칙)가 보이면 다음을 허용합니다.
   - EC2 고정 IP(08 문서에서 만드는 Elastic IP), 시드를 넣을 개발 PC의 공인 IP
   - Render: 무료 서비스는 고정 IP가 없습니다. Render 대시보드 → 서비스 → **Connect → Outbound** 탭의 IP 범위를 추가하거나, 학습용이면 전체 허용(TLS + 비밀번호로 보호)을 선택합니다.
4. **SQL Editor**(또는 아무 MySQL 클라이언트)에서 DB 생성 — 기본 DB는 `test`이므로 반드시 만듭니다.
   ```sql
   CREATE DATABASE buytiming;
   ```
   테이블은 API가 처음 기동할 때 자동 생성됩니다.

## 3. 접속 문자열 만들기

```
DATABASE_URL=mysql+pymysql://<USER>:<PASSWORD>@<HOST>:4000/buytiming?charset=utf8mb4
DB_SSL_CA=/etc/ssl/certs/ca-certificates.crt
```

- 예: `mysql+pymysql://abcd1234.root:p%40ss@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/buytiming?charset=utf8mb4`
- 비밀번호에 `@ : / ? # %` 같은 특수문자가 있으면 **URL 인코딩**합니다(`@` → `%40`). 확인 방법:
  `python -c "import urllib.parse;print(urllib.parse.quote('비밀번호', safe=''))"`
- `DB_SSL_CA=/etc/ssl/certs/ca-certificates.crt`는 Render·EC2의 Docker 이미지(Debian 기반) 안의 경로입니다. 두 곳 모두 이 값을 그대로 씁니다.
- 이 값은 Render 환경 변수와 EC2 `.env` **두 곳에 똑같이** 넣습니다. Git에는 절대 커밋하지 않습니다.

## 4. 시드 데이터 넣기 (최초 1회, 선택)

Render 무료 플랜은 셸 접속이 안 되므로 **둘 중 한 곳**에서 실행합니다. 데이터가 이미 있으면 자동으로 건너뜁니다.

- **EC2에서(권장, 08 문서 완료 후)**:
  ```bash
  cd ~/buytiming
  docker compose exec -e SEED_DEMO_PASSWORD='원하는값' -e SEED_ADMIN_PASSWORD='원하는값' api python -m app.seed
  ```
- **개발 PC(Windows)에서**:
  ```powershell
  cd backend
  $env:DATABASE_URL = "mysql+pymysql://<USER>:<PASSWORD>@<HOST>:4000/buytiming?charset=utf8mb4"
  $env:DB_SSL_CA = (python -c "import certifi; print(certifi.where())")   # Windows에는 /etc/ssl 경로가 없음
  python -m app.seed
  ```
  실행 후 PowerShell 창을 닫아 운영 DB 변수가 남지 않게 합니다.

> 금지: TiDB 주소로 `python -m app.seed --reset` 또는 `pytest`(`TEST_DATABASE_URL`) 실행 — 모든 테이블이 삭제됩니다.

## 5. MySQL 8 개발 환경 (로컬)

### 방법 A — Docker로 MySQL만 띄우기 (PC에 Docker Desktop이 있을 때)

`docker-compose.yml`의 `mysql` 서비스는 포트를 외부에 열지 않으므로, 로컬 uvicorn에서 쓰려면 별도로 띄웁니다.

```bash
docker run -d --name buytiming-mysql -p 3306:3306 \
  -e MYSQL_DATABASE=buytiming -e MYSQL_USER=buytiming -e MYSQL_PASSWORD=devpass -e MYSQL_ROOT_PASSWORD=devroot \
  mysql:8.0 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

### 방법 B — MySQL 8 설치 (MySQL Installer for Windows)

설치 후 `CREATE DATABASE buytiming CHARACTER SET utf8mb4;`와 사용자를 만듭니다.

### 로컬 `.env` (저장소 루트, Git 제외)

```
APP_ENV=development
DATABASE_URL=mysql+pymysql://buytiming:devpass@127.0.0.1:3306/buytiming?charset=utf8mb4
DB_SSL_CA=
JWT_SECRET=dev-only-secret
RPA_API_KEY=dev-only-rpa-key
RPA_TARGET_API=http://localhost:8000
```

```bash
cd backend && python -m app.seed && uvicorn app.main:app --reload     # http://localhost:8000/docs
# MySQL 8 통합 테스트 (CI와 동일) — 테스트 전용 DB를 따로 만들어 사용 (테스트가 DB를 초기화함)
docker exec buytiming-mysql mysql -uroot -pdevroot -e "CREATE DATABASE IF NOT EXISTS buytiming_test; GRANT ALL ON buytiming_test.* TO 'buytiming'@'%';"
TEST_DATABASE_URL="mysql+pymysql://buytiming:devpass@127.0.0.1:3306/buytiming_test?charset=utf8mb4" pytest -q
```

### 방법 C — 전체 스택을 로컬 Docker로 (EC2와 같은 구성)

`.env`에 `DATABASE_URL=mysql+pymysql://buytiming:<MYSQL_PASSWORD>@mysql:3306/buytiming?charset=utf8mb4`,
`MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `RPA_TARGET_API=http://api:8000`을 넣고 `docker compose --profile localdb up -d --build` → http://localhost

## 6. TiDB와 MySQL 8의 차이 (코드 작성 시 주의)

- CI가 SQLite와 MySQL 8 양쪽에서 테스트하므로, 두 곳에서 통과하는 SQL은 TiDB에서도 대부분 동작합니다.
- TiDB 한 행 최대 6 MiB(기본). 모델 바이너리는 약 0.24 MiB로 여유가 있습니다.
- TiDB 트랜잭션은 30분을 넘길 수 없습니다. 대량 작업은 나눠서 커밋합니다.
- TiDB의 `AUTO_INCREMENT` 값은 증가는 하지만 연속이 아닐 수 있습니다. ID가 1, 2, 3…으로 이어진다고 가정하지 않습니다.

다음 문서: [07. Render 배포](07-deploy-render.md)
