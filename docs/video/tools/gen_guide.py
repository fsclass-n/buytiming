"""장면 정의로 '대본·액션 가이드'와 README 템플릿을 만든다(영상과 같은 기준)."""
from pathlib import Path

from video_scenes import PARTS, stamp, timeline

OUT = Path(__file__).resolve().parents[1]
TAG = {"D01": "데모 데이터로 시연", "D07": "데모: 규칙 기반 / 운영: Gemini", "D11": "역할 기반 차단", "D13": "데모 수치 · 성과 아님",
       "D14": "데모 수치 · 성과 아님", "D15": "서버 권한 검사", "D16": "실제 운영 서버"}
MOUSE = {
    "D01": "화면 중앙 → 상단 데모 배너(1초 정지) → 검색창", "D02": "아래로 스크롤 → ‘오늘, 눈여겨볼 가격’ 제목 → 첫 추천 카드",
    "D03": "필수 약관 체크 2회 → ‘동의하고 계속’ → 단계 표시줄 → ‘디지털’ 칩", "D04": "‘일반 사용자 테스트’(1초 정지 후 클릭) → 상단 ‘로그아웃’ 버튼 확인",
    "D05": "검색창 입력 → 검색 버튼 → ‘디지털’ → ‘지금 구매 추천만’ → 첫 상품 카드",
    "D06": "상품명 클릭 → 실구매가 → ‘90일’·‘30일’·‘7일’ → 차트 위 좌→우 4지점 → 아래로 스크롤 → 판매처 비교 표",
    "D07": "위로 스크롤 → 신호등 카드 → ‘AI 구매 조언’ 탭 → ‘구매 조언 받기’ → 조언 카드", "D08": "‘AI와 상담하기’ → 추천 질문 ‘어느 쇼핑몰이 제일 싸?’ → 답변",
    "D09": "‘목표가 알림’ → 목표 가격 입력(115,000) → ‘알림 저장’ → 관심 상품 카드", "D10": "알림 목록 → ‘모두 읽음’",
    "D11": "주소 이동 /admin → ‘관리자 전용 화면입니다’", "D12": "‘로그아웃’ → ‘관리자 테스트’ → ‘관리자 센터’",
    "D13": "지표 카드 4개 → 7일 수집 차트 → 모델 버전 표 → 스크롤 → 작업 로그", "D14": "‘AI 사용량’ → 지표 카드 → ‘검증 실패율’ → 응답 시간 차트 → 최근 호출 표",
    "D15": "‘회원 관리’ → 검색 ‘demo’ → 권한 필터 ‘일반 사용자’ → 회원 표 → ‘관리자로’ → 거부 메시지",
    "D16": "API 묶음 첫 섹션 → 천천히 3회 스크롤 → ‘AI 판정·조언’ 묶음", "D17": "성공한 작업 목록 → 화면 중앙 정지",
}


def main():
    scenes = timeline()
    lines = ["# 3조 10분 발표·시연 영상 — 대본·액션 가이드", "",
             "`3조_final.mp4`는 이 문서와 같은 장면 정의(`tools/video_scenes.py`)로 자동 제작했습니다. 아래 표가 영상의 실제 시간표입니다.", "",
             "| 항목 | 내용 |", "|---|---|",
             "| 길이·형식 | 10:00, 1920×1080, 30fps, H.264 High + AAC |",
             "| 발표자 | 조장 박미금(내레이션은 남성 한국어 합성 음성 `ko-KR-InJoonNeural`, 실제 녹음으로 교체 가능) |",
             "| PPT | `docs/프로젝트_발표자료.pptx` 18장 — 1~16장(00:00–03:00), 17·18장(09:00–10:00) |",
             "| 시연 | Netlify 데모(운영 DB 변경 없음) → Render `/docs` → GitHub Actions |",
             "| 자막 | 화면에 한국어 자막을 넣었고, 별도 파일 `3조_final.srt`도 제공 |", "",
             "## 1. 10분 타임라인", "",
             "| 시간 | 구간 | 화면 | 클릭 동작 | 대본 (박미금) | 강조 연출 | 자막 태그 |", "|---|---|---|---|---|---|---|"]
    for s in scenes:
        a, b = s["start"], s["start"] + s["dur"]
        say = s["say"] or "(말 없이 전환)"
        lines.append(f"| {stamp(a)}–{stamp(b)} | {PARTS[s['part']]} | {s['screen']} | {s['action']} | {say} | {s['fx']} | {TAG.get(s['id'], '')} |")
    lines += ["", "## 2. 파트별 상세 대본", ""]
    for part, title in PARTS.items():
        group = [s for s in scenes if s["part"] == part]
        a, b = group[0]["start"], group[-1]["start"] + group[-1]["dur"]
        lines += [f"### {title} ({stamp(a)}–{stamp(b)})", ""]
        for s in group:
            if not s["say"]:
                lines += [f"- **{stamp(s['start'])} {s['screen']}** — 말 없이 0.5초 페이드로 브라우저 전환", ""]
                continue
            lines += [f"**{stamp(s['start'])} · {s['screen']}** ({s['dur']}초)", "", f"> {s['say']}", ""]
    lines += ["## 3. 마우스 동선·강조 연출", "",
              "| 원칙 | 영상 적용 |", "|---|---|",
              "| 커서 | 노란 원형 커서(지름 34px), 클릭 시 링 애니메이션 |",
              "| 이동 | 22단계로 부드럽게 이동, 도착 후 0.7~0.8초 정지 뒤 클릭 |",
              "| 강조 | 시안 테두리 상자 + 주변 살짝 어둡게(2~5초). 슬라이드는 같은 색 테두리를 순서대로 표시 |",
              "| 스크롤 | 8단계로 나눠 천천히, 스크롤 후 0.5초 정지 |",
              "| 입력 | 글자당 0.12~0.15초 타이핑, 비밀번호 입력 장면 없음 |",
              "| 라벨 | 슬라이드는 오른쪽 위, 시연은 왼쪽 아래에 현재 구간 라벨. 데모·권한 장면은 오른쪽 위 노란 태그 |",
              "| 노출 금지 | 토큰·비밀번호·환경 변수·개발자 도구 없음(Netlify 배지는 숨김) |", "",
              "| 장면 | 커서 경로 |", "|---|---|"]
    for s in scenes:
        if s["id"] in MOUSE:
            lines.append(f"| {stamp(s['start'])} {s['screen']} | {MOUSE[s['id']]} |")
    lines += ["", "## 4. 결과물", "",
              "| 파일 | 내용 |", "|---|---|",
              "| `3조_final.mp4` | 10분 본편(95MB 이하) |",
              "| `3조_final.srt` | 한국어 자막(핵심 용어 굵게) |",
              "| `3조_highlight.mp4` | 04:25부터 60초 하이라이트(10MB 이하, README 인라인 재생용) |",
              "| `video-thumbnail.png` | 04:40 상품 상세 화면 썸네일 |",
              "| `README_template.md` | GitHub README 템플릿 |",
              "| `tools/` | 재제작 도구: `tts.py` → `export_slides.ps1` → `record_demo.py` → `compose.py` |", "",
              "## 5. 다시 만들기", "",
              "```bash", "cd docs/video/tools",
              "python tts.py                 # 내레이션(장면별 길이 검사)",
              "# PowerShell: export_slides.ps1 <pptx 경로> <작업폴더>\\slides",
              "python record_demo.py         # 데모 녹화(공개 데모·API 문서·GitHub만 사용)",
              "python compose.py --rebuild   # 합성·자막·인코딩·하이라이트·썸네일",
              "python check_final.py         # 길이·스트림·주요 프레임 확인", "```", "",
              "대본을 바꾸면 `video_scenes.py`만 고치고 위 순서로 다시 만듭니다. 실제 목소리로 바꾸려면 `tts/장면ID.mp3`를 녹음 파일로 교체합니다.", ""]
    (OUT / "영상_대본_및_연출가이드.md").write_text("\n".join(lines), encoding="utf-8")

    chapters = [("00:00", "PPT 발표 — 팀 역할·아키텍처·기술 선택·역할별 심화·문제 해결·테스트"), ("03:00", "화면 전환 — 데모 사이트"),
                ("03:30", "일반 회원 — 가입·검색·실구매가·가격 흐름·AI 조언·목표가·알림·관리자 차단"),
                ("06:30", "관리자 — 수집 현황·AI 사용량·회원 관리(조회 전용)·API 문서·CI"), ("09:00", "클로징 — 회고(한계·다음 단계)·링크")]
    shots = [("홈", "home"), ("상품 탐색", "search"), ("가격 흐름·신호등", "product-chart"), ("AI 조언", "ai-advice"), ("AI 상담", "chat"),
             ("목표가 알림", "target-alert"), ("관리자 수집·모델", "admin-dashboard"), ("관리자 AI 사용량", "admin-ai"), ("회원 관리", "admin-users")]
    rows = []
    for i in range(0, 9, 3):
        trio = shots[i:i + 3]
        rows.append("| " + " | ".join(f"**{t}**" for t, _ in trio) + " |")
        rows.append("| " + " | ".join(f"![{t}](docs/발표자료/assets/{f}.png)" for t, f in trio) + " |")
    readme = ["# PickTiming (픽타이밍)", "",
              "> 가격 비교를 넘어, 구매 타이밍까지 — 생성형 AI & RPA 기반 실시간 가격 비교·구매 타이밍 추천 플랫폼", "",
              "[![CI](https://github.com/fsclass-n/picktiming/actions/workflows/deploy.yml/badge.svg)](https://github.com/fsclass-n/picktiming/actions)",
              "**데모** https://picktiming.netlify.app · **운영** https://picktiming.onrender.com · **API 문서** https://picktiming.onrender.com/docs", "",
              "## 🎬 발표·시연 영상 (10분)", "",
              "[![PickTiming 10분 발표·시연](docs/video/video-thumbnail.png)](https://github.com/fsclass-n/picktiming/releases/latest/download/3조_final.mp4)", "",
              "60초 하이라이트 (README에서 바로 재생 — GitHub 웹 편집기에 `docs/video/3조_highlight.mp4`를 끌어다 놓아 생긴 주소로 교체):", "",
              "https://github.com/user-attachments/assets/여기에-하이라이트-업로드-주소", "",
              "자막: [docs/video/3조_final.srt](docs/video/3조_final.srt)", "",
              "| 시간 | 내용 |", "|---|---|", *[f"| {t} | {c} |" for t, c in chapters], "",
              "## 📸 스크린샷", "", "| | | |", "|---|---|---|", *rows, "",
              "> 화면의 상품·가격·관리자 수치는 데모 데이터입니다.", "",
              "## 🏗 아키텍처", "",
              "- React(Vite·Tailwind) → FastAPI(`/api/v1`, API 34개) → TiDB(테이블 12개)",
              "- RPA 수집기(1시간) → 수집 API(X-RPA-KEY) → 판정·알림 / scikit-learn 적기 점수 / Gemini 설명(숫자 검증·대체)",
              "- 배포: Netlify(데모) · Render(풀스택 운영) · AWS EC2(compose 구성) · GitHub Actions(CI·변경 경로별 배포·예약 수집)", "",
              "## 🧰 기술 스택", "",
              "| 영역 | 기술 |", "|---|---|",
              "| 화면 | React 19 · Vite 8 · Tailwind CSS v4 |", "| 서버 | Python 3.11 · FastAPI · SQLAlchemy 2 · JWT |",
              "| 데이터 | TiDB Cloud · MySQL 8(CI) · SQLite(테스트) |", "| AI/ML | scikit-learn RandomForest · Google Gemini |",
              "| 수집 | Requests · BeautifulSoup4 · Playwright(선택) |", "| 배포 | Netlify · Render · AWS EC2 · GitHub Actions |", "",
              "## 👥 팀", "", "| 이름 | 역할 |", "|---|---|",
              "| 박미금 | 조장 · PM · 데이터/AI |", "| 김모란 | 백엔드 · 배포 |", "| 이오리 | 프런트엔드 · UI/UX |", "| 홍기흥 | RPA · 데이터 수집 |", "",
              "## ✅ 품질", "", "백엔드 테스트 51 · RPA 테스트 11 · 브라우저 시나리오 9 · CI(SQLite·MySQL 8·Docker)", "",
              "## 📂 문서", "",
              "발표·포트폴리오 PPT(18장) `docs/프로젝트_발표자료.pptx` · PDF `docs/pdf/프로젝트_발표자료.pdf` · 운영 문서 `docs/md/` · 영상 가이드 `docs/video/`", ""]
    body = "\n".join(readme)
    (OUT / "README_template.md").write_text(
        "# GitHub README 템플릿\n\n아래 코드 블록을 저장소 루트 `README.md`에 붙여 넣습니다. "
        "본편은 GitHub Release에 `3조_final.mp4`로 올리면 썸네일 링크가 바로 동작합니다.\n\n"
        "````markdown\n" + body + "````\n", encoding="utf-8")
    print("guide and README template written")


if __name__ == "__main__":
    main()
