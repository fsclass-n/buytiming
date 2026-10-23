# BuyTiming 문서 모음 — 프로젝트 파악 → 배포까지

이 폴더는 바이타이밍 프로젝트 전체를 이해하고, **GitHub를 통해 Render와 AWS EC2에 각각 독립된 풀스택으로 배포**하기 위한 단계별 문서입니다.
번호 순서대로 읽고 진행하면 됩니다.

## 목표 구성 (확정)

| 구분 | 주소 | 역할 | 상태 |
|---|---|---|---|
| Netlify | https://buytiming.netlify.app | **프런트엔드 전용 — 데모 모드**(서버 없이 브라우저 목업 데이터) | 배포 완료, 추가 작업 없음 |
| Render | https://buytiming.onrender.com | **단독 풀스택**: FastAPI가 API + 프런트엔드를 같은 도메인으로 제공 (Docker, 무료 플랜) | 배포 예정 |
| AWS EC2 | http://buytiming.duckdns.org | **단독 풀스택**: nginx(프런트엔드) + FastAPI + RPA 수집기 (docker compose) | 배포 예정 |
| TiDB Cloud | (TiDB 접속 주소) | **운영 DB — Render와 EC2가 같은 DB를 공유** | DB 생성 완료 |
| MySQL 8 | 로컬 PC / GitHub Actions CI | **개발·테스트 전용 DB** | CI에 이미 구성됨 |
| GitHub Actions | — | CI/CD + **Render용 가격 수집(매시 예약 실행)** | 값 등록 예정 |

```
 사용자 ──▶ Netlify  (frontend only, 데모 모드 — API 호출 없음)

 사용자 ──▶ Render  https://buytiming.onrender.com          사용자 ──▶ EC2  http://buytiming.duckdns.org
            ┌──────────────────────────────┐                           ┌───────────────────────────────────┐
            │ FastAPI = API + 프런트엔드    │                           │ nginx(프런트) ─▶ api ◀─ rpa(매시) │
            └──────────────┬───────────────┘                           └─────────────────┬─────────────────┘
                 ▲         │                                                             │
 GitHub Actions  │         └───────────────▶  TiDB Cloud (운영 DB 하나를 공유)  ◀──────────┘
 collect-render  │                            같은 시간대 같은 판매처 가격은 한 번만 저장
 (매시 07분 수집) ─┘
```

- **독립 동작**: Render와 EC2는 서로를 호출하지 않습니다. 한쪽이 멈춰도 다른 쪽은 화면·API·가격 수집이 모두 동작합니다.
- **가격 수집 두 갈래**: EC2는 자체 `rpa` 컨테이너, Render는 GitHub Actions 예약 실행(`collect-render.yml`)이 수집기를 돌립니다.
  둘 다 같은 TiDB에 저장하므로, API가 **같은 판매처·같은 시간대(정시~59분)의 두 번째 가격은 건너뜁니다**(중복 저장 방지).
- **데이터 공유**: 회원·관심 상품·가격 이력이 공유되므로 어느 주소로 접속해도 같은 데이터가 보입니다.

## 문서 목록

### A. 프로젝트 파악

| 번호 | 문서 | 내용 |
|---|---|---|
| 01 | [프로젝트 개요와 구조](01-project-overview.md) | 서비스 흐름, 기술 스택, 폴더 구조, 환경별 차이 |
| 02 | [백엔드(FastAPI)](02-backend.md) | 설정(환경 변수), DB 테이블 12개, API 목록, 프런트엔드 서빙, AI·ML |
| 03 | [프런트엔드](03-frontend.md) | 화면 10개, 데모 모드와 같은 도메인 연동, `config.js` 동작 |
| 04 | [RPA 수집기](04-rpa.md) | 수집 작업 4종, EC2 컨테이너와 GitHub Actions 두 실행 경로 |
| 05 | [CI/CD 파이프라인](05-cicd.md) | `ci.yml`, `deploy.yml`, `collect-render.yml`, 바뀐 폴더별 배포 판별 |

### B. 배포 진행 (이 순서대로)

| 번호 | 문서 | 할 일 |
|---|---|---|
| 06 | [DB 준비: TiDB(운영) · MySQL 8(개발)](06-database.md) | TiDB 접속 문자열, 로컬 MySQL 8 |
| 07 | [Render 배포 (단독 풀스택)](07-deploy-render.md) | 서비스 설정·환경 변수·자동 배포 끄기·확인 |
| 08 | [EC2 배포 (단독 풀스택, DuckDNS)](08-deploy-ec2.md) | 인스턴스·고정 IP·DuckDNS·Docker·`.env`·시드 |
| 09 | [Netlify (데모 모드 유지)](09-netlify-connect.md) | 확인만 — 추가 작업 없음 |
| 10 | [GitHub Actions 등록 (자동 배포 + Render 수집)](10-github-actions-setup.md) | Secrets·Variables 등록, 첫 실행 확인 |
| 11 | [최종 점검과 문제 해결](11-checklist-troubleshooting.md) | 점검표, 자주 나는 오류와 해결법 |

## 이 프로젝트에서 특히 주의할 점 (요약)

1. **`main`에 push하면 운영 배포**가 일어납니다. 바뀐 폴더에 해당하는 대상만 배포됩니다(05 참고). `frontend/`를 바꾸면 Render와 EC2가 함께 배포됩니다.
2. **운영 DB는 하나(TiDB)** 입니다. 테스트(`pytest`)나 `python -m app.seed --reset`을 TiDB 주소로 실행하면 **운영 데이터가 모두 지워집니다**.
3. `.env`는 **로컬 PC와 EC2만** 읽습니다. Render는 대시보드 Environment, GitHub Actions는 Secrets/Variables를 씁니다.
   [`.env.example`](../../.env.example) 맨 위 **[필수] 6개**가 Render 환경 변수와 같은 이름이며, EC2에서는 이 6개만 운영 값으로 바꾸면 됩니다.
   - `RPA_TARGET_API`는 EC2 `.env`에 넣지 않습니다(`http://localhost:8000`을 넣으면 수집기가 API를 찾지 못함).
   - `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`는 예시 값을 그대로 둡니다(비어 있으면 `docker compose up` 자체가 실패).
4. Render 무료 플랜은 **셸(Shell) 접속이 안 됩니다**. 시드 데이터는 EC2나 로컬 PC에서 TiDB로 넣습니다.
5. GitHub Actions가 EC2에 SSH로 접속하므로 **보안 그룹 22번 포트를 GitHub 러너가 접근할 수 있게** 열어야 합니다(10 참고).
6. 공개 저장소의 예약 워크플로는 **저장소에 60일간 활동이 없으면 GitHub가 자동으로 멈춥니다**. 멈추면 Actions 화면에서 다시 켭니다.
