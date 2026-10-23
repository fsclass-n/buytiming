# BuyTiming 문서 모음 — 프로젝트 파악 → 배포까지

이 폴더는 바이타이밍 프로젝트 전체를 이해하고, **GitHub를 통해 Render와 AWS EC2에 배포**하기 위한 단계별 문서입니다.
번호 순서대로 읽고 진행하면 됩니다.

## 목표 구성 (확정)

| 구분 | 주소 | 역할 | 상태 |
|---|---|---|---|
| Netlify | https://buytiming.netlify.app | 프런트엔드(정적 사이트) → **Render API 호출** | 배포 완료 (API 연결 전: 데모 모드) |
| Render | https://buytiming.onrender.com | FastAPI 백엔드 (Docker, 무료 플랜) | 배포 예정 |
| AWS EC2 | http://buytiming.duckdns.org | nginx(프런트엔드) + FastAPI + RPA 수집기 (docker compose) | 배포 예정 |
| TiDB Cloud | (TiDB 접속 주소) | **운영 DB — Render와 EC2가 같은 DB를 공유** | 생성 예정 |
| MySQL 8 | 로컬 PC / GitHub Actions | **개발·테스트 전용 DB** | CI에 이미 구성됨 |

```
                         ┌───────────────────────────── GitHub (fsclass-n/buytiming) ─────────────────────────────┐
                         │  push → Actions: CI(ruff·pytest SQLite/MySQL8·Docker) → 바뀐 폴더만 배포                 │
                         └───────────────┬──────────────────────────────┬──────────────────────────────┬──────────┘
                                         │ Deploy Hook                  │ SSH(git pull + compose)      │ Git 연동
                                         ▼                              ▼                              ▼
사용자 브라우저 ──▶ Netlify (frontend) ──▶ Render API ◀─┐      EC2: nginx ─▶ api ◀─ rpa(매시 수집)     Netlify 빌드
                 buytiming.netlify.app   onrender.com  │      buytiming.duckdns.org
                                                       │              │
                                                       └──── TiDB Cloud (운영 DB 하나를 공유) ◀───┘
```

- RPA 수집기는 **EC2에서만** 돌고, EC2의 API를 통해 TiDB에 가격을 저장합니다. Render API는 같은 TiDB를 읽으므로 같은 데이터가 보입니다.
- 모델 재학습(매일 03:00)도 EC2에서 실행되어 TiDB에 저장되고, Render API가 활성 모델을 DB에서 읽어 씁니다.

## 문서 목록

### A. 프로젝트 파악

| 번호 | 문서 | 내용 |
|---|---|---|
| 01 | [프로젝트 개요와 구조](01-project-overview.md) | 서비스 흐름, 기술 스택, 폴더 구조, 데이터 흐름 |
| 02 | [백엔드(FastAPI)](02-backend.md) | 설정(환경 변수), DB 테이블 12개, API 목록, AI·ML, 보안 |
| 03 | [프런트엔드](03-frontend.md) | 화면 10개, 데모 모드와 실연동, `config.js` 동작 |
| 04 | [RPA 수집기](04-rpa.md) | 수집 작업 4종, 스케줄, API 인증, 수집 원칙 |
| 05 | [CI/CD 파이프라인](05-cicd.md) | `ci.yml`, `deploy.yml`, 바뀐 폴더별 배포 판별 |

### B. 배포 진행 (이 순서대로)

| 번호 | 문서 | 할 일 |
|---|---|---|
| 06 | [DB 준비: TiDB(운영) · MySQL 8(개발)](06-database.md) | TiDB 클러스터·DB 생성, 접속 문자열, 로컬 MySQL 8 |
| 07 | [Render 배포](07-deploy-render.md) | 서비스 생성·환경 변수·자동 배포 끄기·헬스 체크 |
| 08 | [EC2 배포 (DuckDNS)](08-deploy-ec2.md) | 인스턴스·고정 IP·DuckDNS·Docker·`.env`·시드 |
| 09 | [Netlify ↔ Render 연결](09-netlify-connect.md) | `API_BASE_URL` 설정, CORS, 재배포 |
| 10 | [GitHub Actions 자동 배포 등록](10-github-actions-setup.md) | Secrets·Variables 등록, 첫 자동 배포 확인 |
| 11 | [최종 점검과 문제 해결](11-checklist-troubleshooting.md) | 점검표, 자주 나는 오류와 해결법 |

## 이 프로젝트에서 특히 주의할 점 (요약)

1. **`main`에 push하면 운영 배포**가 일어납니다. 바뀐 폴더에 해당하는 대상만 배포됩니다(05 참고).
2. **운영 DB는 하나(TiDB)** 입니다. 테스트(`pytest`)나 `python -m app.seed --reset`을 TiDB 주소로 실행하면 **운영 데이터가 모두 지워집니다**.
3. EC2의 `.env`는 `.env.example`을 복사한 그대로 두면 **두 군데에서 실패**합니다(08 문서의 "반드시 고칠 값" 참고).
   - `RPA_TARGET_API=http://localhost:8000` → 수집기가 API를 찾지 못함 → `http://api:8000`으로 변경
   - `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`가 비어 있으면 `docker compose up` 자체가 실패 → 사용하지 않아도 아무 값이나 입력
4. Render 무료 플랜은 **셸(Shell) 접속이 안 됩니다**. 시드 데이터는 EC2나 로컬 PC에서 TiDB로 넣습니다.
5. GitHub Actions가 EC2에 SSH로 접속하므로 **보안 그룹 22번 포트를 GitHub 러너가 접근할 수 있게** 열어야 합니다(10 참고).
