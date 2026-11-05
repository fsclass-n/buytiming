"""기술 면접용 팀 포트폴리오 PPT(18장)를 만든다. 발표본과 같은 디자인 시스템을 사용한다.

모든 수치·코드는 저장소 기준(279a4ce)에서 확인한 값만 사용한다.
"""
from build_presentation import (
    BLUE,
    BORDER,
    CARD,
    CYAN,
    FONT,
    GRAY,
    MUTED,
    NAVY,
    OUT,
    PANEL,
    ROOT,
    WHITE,
    base,
    box,
    bullets,
    chip,
    circle,
    color,
    icon,
    image,
    line,
    text,
)
from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

TOTAL = 18
FOOTER = "PickTiming  ·  Team Portfolio  ·  3조"
NOTES = []


def frame(s, index, eyebrow, title):
    base(s, index, eyebrow, title, total=TOTAL, footer=FOOTER)


def code(s, source, x, y, w, h, size=11, label=None):
    """편집 가능한 코드 블록(Consolas). 저장소 코드에서 발췌하고 길이만 줄였다."""
    box(s, x, y, w, h, "0A1426", BORDER)
    if label:
        text(s, label, x + .2, y + .1, w - .4, .26, 10, MUTED)
    tb = s.shapes.add_textbox(Inches(x + .2), Inches(y + (.4 if label else .15)), Inches(w - .4), Inches(h - (.5 if label else .3)))
    tf = tb.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ln in enumerate(source.strip("\n").split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(0)
        p.line_spacing = 1.08
        r = p.add_run()
        r.text = ln if ln else " "
        r.font.name = "Consolas"
        r.font.size = Pt(size)
        r.font.color.rgb = color("7DD3FC" if ln.lstrip().startswith(("#", "//")) else "E2E8F0")
        rpr = r._r.get_or_add_rPr()
        for tag in ("a:ea", "a:cs"):
            node = OxmlElement(tag)
            node.set("typeface", FONT)
            rpr.append(node)


def card(s, x, y, w, h, title, items, stroke=BORDER, size=13, row=.36, tag=None, tint=CYAN):
    box(s, x, y, w, h, CARD, stroke, width=1.2)
    top = y + .18
    if tag:
        text(s, tag, x + .25, top, w - .5, .26, 11, tint, True)
        top += .3
    text(s, title, x + .25, top, w - .5, .42, 17, WHITE, True)
    bullets(s, items, x + .28, top + .5, w - .5, row, size, tint)


def note(talk, questions):
    NOTES.append(f"설명 포인트:\n{talk}\n\n예상 질문:\n" + "\n".join(f"- {q}" for q in questions))


# ------------------------------------------------------------------ 1 표지
def s01(s):
    frame(s, 1, "TEAM PORTFOLIO  |  FINAL PROJECT  ·  심화_생성형 AI와 AWS 클라우드를 활용한 풀스택 & 자동화 실무 개발", None)
    text(s, "PickTiming", .6, 1.2, 6.6, .95, 50, WHITE, True)
    text(s, "실시간 가격 비교 · 구매 타이밍 추천 플랫폼", .64, 2.15, 6.6, .45, 20, GRAY)
    text(s, "RPA로 가격을 모으고, ML로 구매 시점을 점수화하고,\n[[LLM 응답을 검증]]해 쉬운 말로 설명합니다.", .64, 2.85, 6.5, 1.0, 19, WHITE, True)
    roles = [("박미금", "조장·PM·데이터/AI"), ("김모란", "백엔드·배포"), ("이오리", "프런트엔드·UI/UX"), ("홍기흥", "RPA·데이터 수집")]
    for i, (n, r) in enumerate(roles):
        x, y = .64 + (i % 2) * 3.25, 4.25 + (i // 2) * .52
        chip(s, f"{n}  ·  {r}", x, y, 3.1, .42, PANEL, BLUE if i == 0 else BORDER, 13)
    text(s, "기간 2026.10.21 – 11.05 (저장소 커밋 기준)  ·  팀 4명", .64, 5.45, 6.6, .3, 13, GRAY)
    text(s, "github.com/fsclass-n/picktiming", .64, 5.85, 6.6, .3, 13, CYAN, True)
    text(s, "picktiming.onrender.com (운영)  ·  picktiming.netlify.app (데모)", .64, 6.2, 6.6, .3, 12, MUTED)
    box(s, 7.35, 1.2, 5.4, 5.2, CARD, BLUE)
    image(s, "product-chart.png", 7.6, 1.5, 4.9, 2.22, "contain")
    image(s, "admin-ai.png", 7.6, 3.95, 4.9, 1.95, "cover")
    text(s, "실제 UI · 상품 상세 / 관리자 AI 사용량 (데모 데이터)", 7.6, 6.0, 4.9, .28, 11, MUTED)
    note("서비스 한 줄 소개와 팀 구성, 링크를 먼저 보여 줍니다. 면접관이 바로 열어 볼 수 있도록 GitHub와 서비스 주소를 표지에 둡니다.",
         ["이 프로젝트에서 본인의 역할은 무엇이었나요?", "팀 규모와 기간은?"])


# ------------------------------------------------------------------ 2 한눈에 보기
def s02(s):
    frame(s, 2, "01  ·  OVERVIEW", "프로젝트 한눈에 보기")
    stats = [("4,133", "애플리케이션 코드(줄)", "백엔드 2,112 · 프런트 1,532 · RPA 489"), ("34", "REST API", "/api/v1 · 6개 라우터"),
             ("12", "DB 테이블", "TiDB · MySQL 호환"), ("71", "자동 검사", "백엔드 51 · RPA 11 · 브라우저 9")]
    for i, (num, label, sub) in enumerate(stats):
        x = .6 + i * 3.08
        box(s, x, 1.72, 2.92, 1.5, CARD, CYAN if i == 3 else BORDER)
        text(s, num, x + .25, 1.82, 2.5, .62, 32, CYAN, True)
        text(s, label, x + .25, 2.45, 2.5, .3, 14, WHITE, True)
        text(s, sub, x + .25, 2.78, 2.6, .3, 11, GRAY)
    card(s, .6, 3.42, 4.0, 3.3, "문제", ["판매처마다 다른 가격·배송비", "매일 바뀌는 가격", "현재 최저가만으로는\n구매 시점 판단이 어려움"], row=.62)
    card(s, 4.75, 3.42, 4.0, 3.3, "해결", ["1시간 주기 RPA 가격 수집", "실구매가 비교 + 90일 가격 흐름", "적기 점수(0~100) + LLM 설명", "목표가·판정 변화 알림"],
         stroke=BLUE, row=.55)
    card(s, 8.9, 3.42, 3.85, 3.3, "결과", ["Render 운영 배포·헬스 체크", "Netlify 데모(같은 API 계약)", "CI: SQLite·MySQL 8·Docker", "회원·관리자 권한 분리"],
         stroke=CYAN, row=.55)
    note("숫자로 규모를 먼저 보여 줍니다. 코드 줄 수는 git ls-files 기준 .py/.jsx/.css 합계이고, 자동 검사 수는 기준 커밋에서 실제 통과한 값입니다.",
         ["가장 어려웠던 부분은?", "테스트 71개는 어떤 범위를 검증하나요?"])


# ------------------------------------------------------------------ 3 팀 구성·역할
def s03(s):
    frame(s, 3, "02  ·  TEAM", "팀 구성과 역할 분담")
    team = [("박미금", "조장 · PM · 데이터/AI", BLUE,
             ["일정·위험 관리, 발표", "판정 피처 8종·모델·점수", "Gemini 프롬프트·응답 검증"], "backend/app/ml · services/timing.py · ai/gemini.py"),
            ("김모란", "백엔드 · 배포", BORDER,
             ["FastAPI API·인증·권한", "수집 수신 API·알림 생성", "Render·EC2·CI/CD"], "backend/app/routers · security.py · .github/"),
            ("이오리", "프런트엔드 · UI/UX", BORDER,
             ["React 통합 UI·차트·모달", "3단계 가입·관리자 화면", "접근성·반응형 브라우저 검사"], "frontend/src/App.jsx · pages/Admin* · tests/"),
            ("홍기흥", "RPA · 데이터 수집", BORDER,
             ["수집기·파서·네이버 API", "정제·이상치 제외", "스케줄 실행·주간 리포트"], "rpa/collector · jobs/weekly_report.py")]
    for i, (name, role, stroke, items, path) in enumerate(team):
        x = .6 + i * 3.08
        box(s, x, 1.72, 2.92, 4.45, CARD, stroke, width=1.3)
        circle(s, x + .25, 1.95, .62, PANEL, CYAN)
        text(s, name[0], x + .25, 1.95, .62, .62, 20, WHITE, True, PP_ALIGN.CENTER)
        text(s, name, x + 1.02, 1.92, 1.8, .38, 19, WHITE, True)
        text(s, role, x + 1.02, 2.3, 1.85, .3, 12, CYAN, True)
        line(s, x + .25, 2.8, x + 2.67, 2.8, BORDER, .8)
        bullets(s, items, x + .28, 2.95, 2.55, .52, 13)
        text(s, "주요 코드", x + .25, 4.65, 2.4, .26, 11, MUTED, True)
        text(s, path, x + .25, 4.92, 2.5, .95, 11, GRAY, anchor=MSO_ANCHOR.TOP)
    box(s, .6, 6.3, 12.15, .5, PANEL, BORDER)
    text(s, "협업: 통합 연계·테스트·오류 수정은 전원 참여  ·  main push = 운영 배포이므로 CI 통과 후 반영  ·  비밀값은 환경 변수·GitHub Secrets",
         .85, 6.3, 11.7, .5, 13, WHITE)
    note("역할은 담당 영역 기준입니다. 각자 자기 카드의 주요 코드 경로를 기준으로 '무엇을 왜 그렇게 만들었는지'를 설명합니다. 등장인물은 가상 인물입니다.",
         ["팀 내 의견 충돌은 어떻게 해결했나요?", "다른 팀원의 코드와 어떻게 통합했나요?"])


# ------------------------------------------------------------------ 4 문제·요구사항·제약
def s04(s):
    frame(s, 4, "03  ·  REQUIREMENTS", "문제 정의와 요구사항, 그리고 제약")
    card(s, .6, 1.72, 3.9, 4.95, "사용자 문제", ["같은 상품, 판매처별 가격·배송비 "
                                            "상이", "가격은 매일 변동", "‘지금 사도 될까?’ 판단 근거 부족", "가격 확인을 반복해야 함"], row=.6)
    card(s, 4.65, 1.72, 4.0, 4.95, "핵심 요구사항", ["기능 17건: "
                                               "비교·차트·판정·AI·알림·관리", "비기능 8건: 성능 목표·보안·비용·접근성", "이력 30일 미만은 ‘판단 보류’",
                                                "LLM 답변은 입력 수치만 사용", "관리자 권한은 서버에서 검사"], stroke=BLUE, row=.6)
    card(s, 8.8, 1.72, 3.95, 4.95, "제약 조건", ["약관·robots.txt 준수, 요청 간격 3초", "LLM 비용·환각 위험", "Render 무료 플랜: 상주 작업 불가·슬립",
                                             "로컬·Render·EC2가 운영 DB 공유"], stroke=CYAN, row=.6)
    note("요구사항보다 제약 조건이 설계를 결정했다는 점을 강조합니다. 예: 무료 플랜 제약 → 예약 수집 분리, 공유 DB → 테스트 격리.",
         ["제약 때문에 포기한 기능이 있나요?", "요구사항 우선순위는 어떻게 정했나요?"])


# ------------------------------------------------------------------ 5 아키텍처
def s05(s):
    frame(s, 5, "04  ·  ARCHITECTURE", "시스템 아키텍처와 배포 구성")
    nodes = [(.6, 2.3, "React SPA", "Vite · Tailwind v4"), (3.45, 3.0, "FastAPI /api/v1", "auth · products · ai\nuser_data · rpa · admin"),
             (7.0, 2.4, "TiDB Cloud", "12 tables · TLS")]
    for i, (x, w, head, sub) in enumerate(nodes):
        box(s, x, 1.85, w, 1.55, CARD, BLUE if i == 1 else BORDER, width=1.3)
        text(s, head, x + .1, 1.95, w - .2, .45, 17, WHITE, True, PP_ALIGN.CENTER)
        text(s, sub, x + .1, 2.42, w - .2, .85, 12, GRAY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP)
    line(s, 2.93, 2.62, 3.42, 2.62, CYAN, 1.6, both=True)
    text(s, "JWT", 2.85, 2.25, .65, .28, 11, CYAN, True, PP_ALIGN.CENTER)
    line(s, 6.48, 2.62, 6.97, 2.62, CYAN, 1.6, both=True)
    text(s, "SQLAlchemy", 6.3, 2.25, 1.0, .28, 10, CYAN, True, PP_ALIGN.CENTER)
    box(s, 9.75, 1.85, 3.0, .7, PANEL, BORDER)
    text(s, "Google Gemini", 9.9, 1.88, 2.7, .35, 14, WHITE, True)
    text(s, "서버에서만 호출 · 숫자 검증", 9.9, 2.2, 2.7, .3, 11, GRAY)
    box(s, 9.75, 2.7, 3.0, .7, PANEL, BORDER)
    text(s, "scikit-learn", 9.9, 2.73, 2.7, .35, 14, WHITE, True)
    text(s, "모델은 DB(model_versions)에 저장", 9.9, 3.05, 2.8, .3, 11, GRAY)
    line(s, 6.48, 2.0, 9.72, 2.0, BORDER, 1, True)
    box(s, 3.45, 3.75, 3.0, .75, PANEL, BORDER)
    icon(s, "robot", 3.6, 3.86, .4)
    text(s, "RPA 수집기", 4.12, 3.78, 2.2, .38, 14, WHITE, True)
    text(s, "X-RPA-KEY 인증", 4.12, 4.12, 2.2, .3, 11, GRAY)
    line(s, 4.95, 3.73, 4.95, 3.42, CYAN, 1.6, True)
    text(s, "배포 토폴로지 (서로 호출하지 않는 독립 구성)", .6, 4.75, 8, .3, 13, CYAN, True)
    deploys = [("Netlify", "React 빌드만 · 브라우저 목업 API", "데모"), ("Render", "루트 Dockerfile · React + FastAPI", "운영 확인"),
               ("AWS EC2", "compose: nginx + api + rpa", "구성 완료·운영 미확인"), ("GitHub Actions", "CI · 변경 경로별 배포 · 매시 07분 수집", "CI 통과")]
    for i, (head, sub, state) in enumerate(deploys):
        x = .6 + i * 3.07
        box(s, x, 5.12, 2.94, 1.55, CARD, BLUE if head == "Render" else BORDER)
        text(s, head, x + .2, 5.2, 2.6, .4, 16, WHITE, True)
        text(s, sub, x + .2, 5.62, 2.65, .55, 12, GRAY, anchor=MSO_ANCHOR.TOP)
        chip(s, state, x + .2, 6.18, 2.0, .36, PANEL, BORDER, 11, CYAN)
    note("요청 흐름(SPA → API → DB)과 수집 흐름(RPA → API)을 분리해 설명합니다. Render와 EC2는 같은 TiDB를 "
         "쓰는 독립 풀스택이며, EC2는 배포 코드까지 구현되어 있고 운영 확인은 남아 있습니다.",
         ["Render와 EC2를 둘 다 둔 이유는?", "공유 DB의 위험은 어떻게 관리했나요?", "모델을 왜 DB에 저장했나요?"])


# ------------------------------------------------------------------ 6 기술 선택
def s06(s):
    frame(s, 6, "05  ·  TECH DECISIONS", "기술 선택 이유와 트레이드오프")
    rows = [("API", "FastAPI", "Pydantic 입력 검증, 자동 /docs, 의존성 주입으로 권한 분리", "대규모 관리자 기능은 직접 구현"),
            ("DB", "TiDB + MySQL 8(CI) + SQLite", "MySQL 호환 무료 서버리스, 테스트는 빠른 SQLite + 호환성 MySQL", "공유 운영 DB → 초기화 금지 규칙"),
            ("화면", "React · Vite · Tailwind v4", "필터·모달·가입 단계 등 상태 관리, 관리자 화면 지연 로드", "Vanilla JS 대비 빌드 단계 추가"),
            ("ML", "RandomForest + TimeSeriesSplit", "표 형식 피처·적은 데이터에 적합, 시간 순서 분할로 미래 정보 누수 방지", "데이터 부족 시 규칙 확률로 대체"),
            ("LLM", "Gemini 구조화 출력", "JSON 스키마로 파싱 안정, temperature 0.3, 숫자 대조 검증", "실패 시 템플릿 → 표현 다양성 감소"),
            ("배포", "Render + EC2 + Actions", "무료 플랜은 상주 작업 불가 → 예약 수집 분리, 환경 독립", "콜드 스타트·중복 수집 → 시간대 중복 방지")]
    heads = [("영역", .6, 1.1), ("선택", 1.75, 2.55), ("이유", 4.35, 5.0), ("트레이드오프 · 보완", 9.4, 3.35)]
    for label, x, w in heads:
        text(s, label, x + .12, 1.72, w, .35, 13, CYAN, True)
    for i, row in enumerate(rows):
        y = 2.12 + i * .77
        box(s, .6, y, 12.15, .67, CARD, BLUE if i == 3 else BORDER)
        for (label, x, w), value in zip(heads, row, strict=True):
            text(s, value, x + .12, y, w - .1, .67, 13 if label != "영역" else 14, WHITE if label in ("영역", "선택") else GRAY,
                 label in ("영역", "선택"))
    note("모든 선택을 '왜'와 '대가'로 설명합니다. 특히 TimeSeriesSplit(미래 데이터 누수 방지)과 무료 플랜 제약에서 나온 배포 구조가 면접 단골 질문입니다.",
         ["왜 PostgreSQL이 아닌 TiDB인가요?", "RandomForest 대신 다른 모델을 검토했나요?", "Vanilla JS에서 React로 바꾼 이유는?"])


# ------------------------------------------------------------------ 7 데이터 파이프라인
def s07(s):
    frame(s, 7, "06  ·  DATA PIPELINE", "수집에서 알림까지, 한 번의 요청으로")
    steps = [("①", "대상 조회", "GET /rpa/listings"), ("②", "수집", "robots.txt · 3초 간격\n재시도 3·6·12초"), ("③", "정제", "중복 제거\n±50% 이상치 제외"),
             ("④", "적재", "POST /rpa/prices/bulk\n같은 시간대 중복 "
                         "skip"), ("⑤", "판정", "timing_predictions\n사전 계산"), ("⑥", "알림", "목표가·판정 변화\n24시간 중복 방지")]
    for i, (no, head, sub) in enumerate(steps):
        x = .6 + i * 2.05
        box(s, x, 1.85, 1.85, 2.1, CARD, BLUE if i in (3, 4) else BORDER)
        text(s, no, x + .18, 1.95, .5, .4, 18, CYAN, True)
        text(s, head, x + .18, 2.38, 1.6, .4, 17, WHITE, True)
        text(s, sub, x + .18, 2.85, 1.62, .9, 11, GRAY, anchor=MSO_ANCHOR.TOP)
        if i < 5:
            line(s, x + 1.87, 2.9, x + 2.03, 2.9, CYAN, 1.6, True)
    text(s, "스케줄 (EC2: 컨테이너 내장 스케줄러 / Render: GitHub Actions 예약)", .6, 4.2, 9, .3, 13, CYAN, True)
    sched = [("매시", "가격 수집 collect", "EC2 정각 · Actions 07분"), ("매일 03:00", "모델 재학습 train", "F1이 같거나 좋을 때만 교체"),
             ("매일 06:00", "참가격 public", "주소·키 없으면 건너뜀"), ("월 07:00", "주간 리포트 report", "엑셀 + 차트")]
    for i, (when, job, desc) in enumerate(sched):
        x = .6 + i * 3.07
        box(s, x, 4.6, 2.94, 1.35, CARD, BORDER)
        text(s, when, x + .2, 4.68, 2.6, .35, 14, CYAN, True)
        text(s, job, x + .2, 5.03, 2.6, .35, 14, WHITE, True)
        text(s, desc, x + .2, 5.4, 2.65, .35, 11, GRAY)
    box(s, .6, 6.12, 12.15, .62, PANEL, BORDER)
    text(s, "핵심: 가격 저장과 판정·알림을 [[같은 트랜잭션]]에서 처리해, 화면은 미리 계산된 점수를 바로 읽습니다(판정 캐시 2시간).",
         .85, 6.12, 11.7, .62, 14, WHITE)
    note("수집 요청 하나가 저장 → 판정 → 알림까지 처리하는 흐름입니다. 두 수집기가 같은 DB에 보내도 시간대 중복 방지로 행·알림이 중복되지 않습니다.",
         ["수집 실패 시 어떻게 되나요?", "판정을 미리 계산하는 이유는?"])


# ------------------------------------------------------------------ 8 심화: 판정 (박미금)
def s08(s):
    frame(s, 8, "07  ·  DEEP DIVE  —  데이터/AI  ·  박미금", "구매 시점을 점수로: 적기 판정 모델")
    box(s, .6, 1.72, 6.1, 1.1, CARD, BLUE)
    text(s, "적기 점수 = (1 − 7일 내 5% 하락 확률) × [[70]]\n                + (1 − 90일 가격 백분위) × [[30]]", .85, 1.75, 5.7, 1.05, 15, WHITE, True)
    text(s, "피처 8종", .6, 3.0, 3, .3, 13, CYAN, True)
    feats = ["90일 백분위", "최저가 대비", "7일 평균 괴리", "30일 평균 괴리", "30일 기울기", "30일 변동성", "하락 후 경과일", "월말 여부"]
    for i, f in enumerate(feats):
        chip(s, f, .6 + (i % 4) * 1.53, 3.35 + (i // 4) * .5, 1.43, .4, PANEL, BORDER, 11)
    bullets(s, ["라벨: 7일 안에 현재가 대비 5% 이상 하락하면 1", "RandomForest(150, depth 8, balanced) · TimeSeriesSplit(5)",
                "검증 F1이 운영 모델 이상일 때만 교체(100행 미만이면 생략)", "활성 모델이 없으면 규칙 확률, 이력 30일 미만은 판단 보류"], .6, 4.5, 6.1, .45, 13)
    code(s, """# backend/app/services/timing.py
model, mv = load_active(db)
if model is not None:
    prob = float(model.predict_proba(
        pd.DataFrame([row[FEATURES]]))[0, 1])
else:
    prob, version = heuristic_prob(row), "heuristic"
pct = float(row["percentile_90d"])
score = int(round((1 - prob) * 70 + (1 - pct) * 30))
label = label_for(score)  # BUY_NOW / WAIT_A_BIT / WAIT""", 6.95, 1.72, 5.8, 3.3, 11, "실제 코드 발췌")
    box(s, 6.95, 5.2, 5.8, 1.5, PANEL, BORDER)
    text(s, "한계와 다음 단계", 7.2, 5.28, 5, .32, 13, CYAN, True)
    text(s, "70/30 가중치는 기획 단계 정의값이며 실데이터 검증이 필요합니다.\n다음 단계: 판정 후 7일 실제 가격으로 적중률 집계·공개.",
         7.2, 5.62, 5.4, .95, 12, GRAY, anchor=MSO_ANCHOR.TOP)
    note("확률(미래)과 현재 가격 위치(과거)를 결합한 이유, 시계열 분할로 누수를 막은 점, 모델이 없을 때도 서비스가 멈추지 않는 대체 "
         "경로를 설명합니다. 운영 데이터 기준 F1은 아직 측정 보고서가 없다고 솔직히 말합니다.",
         ["왜 70/30인가요?", "클래스 불균형은 어떻게 처리했나요?", "데이터 누수를 어떻게 막았나요?"])


# ------------------------------------------------------------------ 9 심화: LLM 신뢰성 (박미금)
def s09(s):
    frame(s, 9, "08  ·  DEEP DIVE  —  데이터/AI  ·  박미금", "LLM 답변을 믿을 수 있게: 숫자 검증과 대체 경로")
    flow = [("분석 사실", "점수·가격·추세"), ("Gemini", "JSON 스키마\ntemperature 0.3"), ("숫자 대조", "입력에 없는 숫자?"),
            ("1회 재요청", "위반 숫자를 알려 줌"), ("대체 응답", "정해진 설명")]
    for i, (head, sub) in enumerate(flow):
        x = .6 + i * 2.45
        box(s, x, 1.8, 2.2, 1.35, CARD, BLUE if i == 2 else BORDER)
        text(s, head, x + .15, 1.88, 1.9, .4, 16, WHITE, True)
        text(s, sub, x + .15, 2.3, 1.95, .75, 12, GRAY, anchor=MSO_ANCHOR.TOP)
        if i < 4:
            line(s, x + 2.22, 2.47, x + 2.43, 2.47, CYAN, 1.6, True)
    code(s, """# backend/app/ai/gemini.py  (_generate 요약)
out, tok = _call(client, system, schema, payload)
bad = unknown_numbers(to_text(out), facts)
if bad:
    out, tok2 = _call(..., extra=f"... {', '.join(bad)} ...")
    meta["validation"] = "RETRY"
    if unknown_numbers(to_text(out), facts):
        out, meta["validation"] = None, "FALLBACK"
# except: 429 / network / schema -> "ERROR"
if result is None:
    result = fallback()        # template_advice / template_chat""", .6, 3.4, 6.5, 3.3, 11, "실제 코드 발췌")
    card(s, 7.3, 3.4, 5.45, 3.3, "운영 장치", ["검증 상태 기록: OK · RETRY · FALLBACK · ERROR", "조언 캐시: (상품·가격·판정·모델) SHA-256, 24시간",
                                            "사용자별 일일 한도(기본 20회), 초과 시 429", "키는 서버에만, 브라우저 직접 호출 금지",
                                            "가짜 클라이언트로 재요청·대체·오류 경로 테스트"], stroke=CYAN, size=12, row=.5)
    note("LLM을 그대로 신뢰하지 않고 '입력에 없는 숫자'를 기계적으로 걸러내는 구조입니다. 모든 오류를 없앤다고 하지 않고, "
         "검증 실패율을 관리자 화면에서 관찰할 수 있게 만든 점을 강조합니다.",
         ["숫자 외의 환각은 어떻게 다루나요?", "캐시 키에 모델 버전을 넣은 이유는?", "LLM 비용은 어떻게 통제하나요?"])


# ------------------------------------------------------------------ 10 심화: 백엔드 (김모란)
def s10(s):
    frame(s, 10, "09  ·  DEEP DIVE  —  백엔드  ·  김모란", "API 설계와 데이터 무결성")
    card(s, .6, 1.72, 5.9, 2.35, "인증 경계 분리", ["사용자: Authorization Bearer JWT", "수집기: X-RPA-KEY, hmac.compare_digest 비교", "관리자: ADMIN 역할 의존성",
                                               "운영에서 기본 비밀값이면 서버 기동 거부"], stroke=BLUE, size=13, row=.42)
    card(s, .6, 4.22, 5.9, 2.5, "관리자 권한 보호 규칙", ["본인 권한 변경 금지 "
                                                 "(SELF_ROLE_CHANGE)", "마지막 관리자 강등 금지 (LAST_ADMIN)", "테스트 관리자 조회 전용 (DEMO_READ_ONLY)",
                                                   "오류 응답 {code, message} 형식 통일"], size=13, row=.45)
    code(s, """# backend/app/routers/rpa.py  POST /rpa/prices/bulk
hour = at.replace(minute=0, second=0, microsecond=0)
seen = set(db.execute(select(PriceHistory.listing_id).where(
    PriceHistory.listing_id.in_(ids),
    PriceHistory.collected_at >= hour,
    PriceHistory.collected_at < hour + timedelta(hours=1))).scalars())
for i in body.items:
    if i.listing_id in seen:
        duplicate += 1; continue
    seen.add(i.listing_id)
    db.add(PriceHistory(..., total_price=i.price + i.shipping_fee))
db.flush()
alerts = sum(refresh_product(db, p) for p in touched)
db.commit()""", 6.7, 1.72, 6.05, 3.9, 10, "같은 시간대 중복 저장 방지 (멱등 적재)")
    box(s, 6.7, 5.8, 6.05, .92, PANEL, BORDER)
    text(s, "두 수집기(EC2·Actions)가 같은 DB에 보내도 행·알림이 중복되지 않습니다.\n검증: test_bulk_prices_skip_same_hour", 6.95, 5.8, 5.7, .92, 12, WHITE)
    note("인증 주체별로 경계를 나누고, 적재 API를 멱등하게 만든 이유를 설명합니다. 저장·판정·알림을 한 트랜잭션에서 처리해 부분 실패를 줄였습니다.",
         ["JWT를 어디에 저장하나요? 보안 위험은?", "멱등성을 DB 제약이 아닌 코드로 처리한 이유는?", "API 버전은 어떻게 관리하나요?"])


# ------------------------------------------------------------------ 11 심화: CI/CD (김모란)
def s11(s):
    frame(s, 11, "10  ·  DEEP DIVE  —  배포  ·  김모란", "CI/CD: 바뀐 폴더만 배포한다")
    jobs = [("backend", "Ruff · pytest (SQLite)"), ("backend-mysql", "pytest on MySQL 8"), ("rpa", "Ruff · pytest"), ("frontend", "npm ci · React 빌드"),
            ("docker", "이미지 빌드 · /health 확인")]
    text(s, "CI (push · PR)", .6, 1.72, 4, .3, 13, CYAN, True)
    for i, (job, desc) in enumerate(jobs):
        x = .6 + i * 2.45
        box(s, x, 2.08, 2.25, 1.0, CARD, BLUE if job == "backend-mysql" else BORDER)
        text(s, job, x + .15, 2.12, 2.0, .4, 14, WHITE, True)
        text(s, desc, x + .15, 2.5, 2.05, .45, 11, GRAY)
    text(s, "변경 경로 → 배포 대상 (detect-changes.sh)", .6, 3.35, 6, .3, 13, CYAN, True)
    rows = [("frontend/", "Netlify · Render · EC2(web)"), ("backend/ · requirements.txt", "Render · EC2(api)"), ("rpa/", "EC2(rpa)"),
            ("Dockerfile · render.yaml", "Render"), ("docs/ · .claude/", "배포 없음")]
    for i, (path, target) in enumerate(rows):
        y = 3.72 + i * .52
        box(s, .6, y, 6.0, .44, CARD, BORDER)
        text(s, path, .8, y, 2.8, .44, 12, WHITE, True)
        line(s, 3.6, y + .22, 4.0, y + .22, CYAN, 1.4, True)
        text(s, target, 4.1, y, 2.4, .44, 12, GRAY)
    card(s, 6.8, 3.35, 5.95, 3.38, "배포 방식", ["Render: Auto-Deploy ‘After CI Checks Pass’", "EC2: SSH → git pull → 바뀐 서비스만 compose 재빌드",
                                              "Netlify: Git 연동, React 빌드 결과만 게시", "Render 수집: Actions cron ‘7 * * * *’, /health로 깨운 뒤 실행",
                                              "MySQL 8 job이 SQLite에서 안 보이는 차이를 사전 발견"], stroke=CYAN, size=12, row=.52)
    note("문서만 바뀐 커밋이 운영 배포를 일으키지 않도록 경로 기반으로 대상을 고릅니다. MySQL 8 테스트 job은 TiDB 호환성 문제를 미리 잡는 장치입니다.",
         ["배포 실패 시 롤백은?", "왜 Render 배포 훅 대신 Auto-Deploy를 썼나요?", "비밀값은 어떻게 관리하나요?"])


# ------------------------------------------------------------------ 12 심화: 프런트엔드 (이오리)
def s12(s):
    frame(s, 12, "11  ·  DEEP DIVE  —  프런트엔드  ·  이오리", "하나의 화면 코드로 데모와 운영을 모두")
    image(s, "product-chart.png", .6, 1.75, 6.2, 2.8, "contain")
    text(s, "실제 UI · 7·30·90일 가격 흐름과 구매 타이밍 신호등 (데모 데이터)", .6, 4.68, 6.2, .28, 11, MUTED)
    code(s, """// frontend/src/lib/api.js
const BASE = (window.APP_CONFIG?.API_BASE_URL || '').trim();
// BASE == ''  -> handleMock(): same REST contract in browser

// frontend/src/App.jsx
const Admin = lazy(() => import('./pages/Admin.jsx'));
const AdminAI = lazy(() => import('./pages/AdminAI.jsx'));""", .6, 5.05, 6.2, 1.68, 11)
    card(s, 7.0, 1.75, 5.75, 2.55, "설계 포인트", ["데모 모드: 같은 API 계약을 브라우저 목업으로 처리", "Render: FastAPI가 SPA 제공, /js/config.js는 같은 도메인",
                                                "고객 차트는 가벼운 SVG, Plotly는 관리자에서만 지연 로드"], stroke=BLUE, size=12, row=.55)
    card(s, 7.0, 4.45, 5.75, 2.28, "접근성·반응형", ["모달 Tab 순환·Escape·포커스 복귀", "본문 바로가기, 화면 이동 시 본문 포커스", "375·768·1440px 가로 넘침 없음 "
                                                                                                     "검사"],
         stroke=CYAN, size=12, row=.5)
    note("API 응답 형식을 목업과 맞춰 데모 사이트와 운영 사이트가 같은 화면 코드를 공유합니다. 접근성은 자동 검사와 키보드 시나리오 테스트로 확인했습니다.",
         ["App.jsx를 하나로 합친 장단점은?", "상태 관리는 어떻게 했나요?", "번들 크기는 어떻게 줄였나요?"])


# ------------------------------------------------------------------ 13 심화: RPA (홍기흥)
def s13(s):
    frame(s, 13, "12  ·  DEEP DIVE  —  RPA  ·  홍기흥", "예의 있는 수집기: 허용된 만큼, 천천히, 다시")
    code(s, """# rpa/collector/http.py
def fetch(self, url, render=False, wait_for=None):
    if not self.allowed(url):          # robots.txt
        raise CollectError("robots.txt disallow: " + url)
    for attempt in range(self.retries):        # 3
        self.wait()                            # 3s interval
        try:
            if render:                         # Playwright
                return render_page(url, self.ua, ...)
            r = self.s.get(url, timeout=self.timeout)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception:
            time.sleep(3 * 2 ** attempt)      # 3, 6, 12s
    raise CollectError("request failed: " + url)""", .6, 1.72, 6.4, 4.1, 11, "실제 코드 발췌")
    box(s, .6, 5.98, 6.4, .74, PANEL, BORDER)
    text(s, "robots.txt를 확인할 수 없으면 [[수집하지 않음]](Disallow로 간주)", .85, 5.98, 6.0, .74, 13, WHITE)
    card(s, 7.2, 1.72, 5.55, 2.6, "수집·정제", ["등록 판매처(malls.json) · 네이버 쇼핑 API(키 설정 시)", "JavaScript 페이지는 Playwright로 렌더링",
                                             "직전 가격 대비 ±50% 초과는 이상치 제외", "시연 쇼핑몰은 실제 접속 없이 모의 가격"], stroke=BLUE, size=12, row=.5)
    card(s, 7.2, 4.47, 5.55, 2.25, "두 실행 경로", ["EC2: rpa 컨테이너 내장 스케줄러(정각)", "Render: GitHub Actions "
                                                                            "예약(07분)", "같은 코드 · 같은 API · 시간대 중복 방지"],
         stroke=CYAN, size=12, row=.5)
    note("수집 대상 서버에 부담을 주지 않는 원칙을 코드로 강제했습니다. 같은 수집기 코드를 두 실행 환경에서 재사용하고, 중복은 API에서 막습니다.",
         ["사이트 구조가 바뀌면 어떻게 대응하나요?", "법적·윤리적 문제는 어떻게 검토했나요?", "수집 실패를 어떻게 감지하나요?"])


# ------------------------------------------------------------------ 14 트러블슈팅
def s14(s):
    frame(s, 14, "13  ·  TROUBLESHOOTING", "문제 해결 사례")
    cases = [("무료 플랜에서 스케줄러를 돌릴 수 없음", "Render Free는 상주 작업 불가·15분 무요청 시 슬립",
              "GitHub Actions 매시 예약 + /health로 깨운 뒤 수집", "Render도 독립적으로 가격 갱신"),
             ("두 수집기가 같은 DB에 저장", "EC2·Actions가 같은 시간대에 같은 가격 전송 → 중복 행·알림",
              "판매처·시간대 기준 두 번째 가격 skip", "test_bulk_prices_skip_same_hour 통과"),
             ("LLM이 입력에 없는 숫자를 말함", "모델이 일반 지식으로 수치를 보충",
              "숫자 대조 → 1회 재요청 → 템플릿 대체, 상태 기록", "재요청·대체·오류 테스트 3건 통과"),
             ("SQLite에선 통과, MySQL에선 실패", "DB마다 행 선택 순서가 달라 가격 없는 판매 페이지가 선택됨",
              "CI MySQL 8 job으로 발견, 테스트 대상 선택 수정", "TiDB 호환성 문제를 배포 전 차단")]
    for i, (prob, cause, fix, result) in enumerate(cases):
        x, y = .6 + (i % 2) * 6.15, 1.72 + (i // 2) * 2.55
        box(s, x, y, 6.0, 2.4, CARD, BLUE if i == 1 else BORDER, width=1.2)
        text(s, prob, x + .25, y + .12, 5.5, .42, 16, WHITE, True)
        for j, (k, v) in enumerate([("원인", cause), ("해결", fix), ("결과", result)]):
            text(s, k, x + .25, y + .65 + j * .55, .7, .5, 12, CYAN, True)
            text(s, v, x + .95, y + .65 + j * .55, 4.9, .5, 12, GRAY)
    note("각 사례를 문제 → 원인 → 해결 → 검증 순서로 1분 안에 말할 수 있게 연습합니다. 결과에는 테스트 이름처럼 확인 가능한 근거를 붙였습니다.",
         ["가장 오래 걸린 문제는?", "같은 문제가 다시 생기지 않게 무엇을 했나요?"])


# ------------------------------------------------------------------ 15 테스트·품질
def s15(s):
    frame(s, 15, "14  ·  QUALITY", "테스트와 품질 관리")
    tiers = [("브라우저 E2E", "9개 시나리오", "Playwright · 핵심 사용자 흐름", 6.0),
             ("통합 (API)", "백엔드 51건", "API·인증·권한·AI 검증·수집 API·SPA 제공·DB TLS", 8.2),
             ("단위", "RPA 11건 + 피처·검증기", "파싱·정제·스케줄·네이버·S3, 피처·숫자 검증", 10.4)]
    for i, (name, count, desc, w) in enumerate(tiers):
        x = .6 + (10.4 - w) / 2
        y = 1.8 + i * 1.0
        box(s, x, y, w, .85, CARD, CYAN if i == 0 else BLUE if i == 1 else BORDER)
        text(s, f"{name}  ·  [[{count}]]", x + .25, y, 3.8, .85, 15, WHITE, True)
        text(s, desc, x + 4.0, y, w - 4.2, .85, 12, GRAY)
    card(s, 11.15 - .1, 1.8, 1.7, 2.85, "CI", ["Ruff", "SQLite", "MySQL 8", "Docker"], size=12, row=.48)
    card(s, .6, 5.0, 6.0, 1.75, "테스트 격리", ["conftest가 DATABASE_URL을 임시 SQLite로 덮어씀", "운영 TiDB 초기화 명령은 금지 규칙으로 관리"], size=12, row=.45)
    card(s, 6.75, 5.0, 6.0, 1.75, "외부 의존성 대체", ["Gemini: 가짜 클라이언트로 재요청·대체 검증", "OAuth: 토큰 교환을 가짜 응답으로 검증"], size=12, row=.45)
    note("테스트 수보다 '무엇을 막는 테스트인가'를 설명합니다. 운영 DB를 절대 쓰지 않도록 테스트 설정이 DB 주소를 덮어쓰는 점이 핵심입니다.",
         ["커버리지는 얼마인가요?", "E2E 테스트를 CI에 넣지 않은 이유는?", "외부 API는 어떻게 테스트했나요?"])


# ------------------------------------------------------------------ 16 결과 화면
def s16(s):
    frame(s, 16, "15  ·  RESULT", "실제 동작하는 서비스")
    shots = [("home.png", "홈 · 가격 탐색", "contain"), ("search.png", "검색·필터", "cover"), ("chat.png", "AI 상담", "cover"),
             ("watchlist.png", "관심 상품·목표가", "cover"), ("admin-dashboard.png", "관리자 수집·모델", "cover"), ("admin-users.png", "회원·권한 관리", "cover")]
    for i, (img, cap, mode) in enumerate(shots):
        x, y = .6 + (i % 3) * 4.1, 1.72 + (i // 3) * 2.45
        image(s, img, x, y, 3.9, 1.95, mode)
        text(s, cap, x, y + 2.0, 3.9, .3, 12, GRAY)
    text(s, "운영 picktiming.onrender.com  ·  데모 picktiming.netlify.app  ·  화면 데이터는 데모", .6, 6.65, 12, .3, 12, MUTED)
    note("면접 중 실제 사이트를 열 수 있다면 데모 사이트로 3분 안에 핵심 흐름을 보여 줍니다. 관리자 화면 숫자는 데모 데이터라고 먼저 말합니다.",
         ["실제 사용자는 있었나요?", "가장 자신 있는 화면은?"])


# ------------------------------------------------------------------ 17 회고
def s17(s):
    frame(s, 17, "16  ·  RETROSPECTIVE", "회고: 잘한 점, 한계, 다음 단계")
    card(s, .6, 1.72, 3.95, 5.0, "잘한 점", ["LLM 출력을 검증하는 구조", "제약에서 출발한 배포 설계", "운영 DB와 분리된 테스트", "데모·운영이 같은 API "
                                                                                                 "계약"], stroke=BLUE, row=.62)
    card(s, 4.7, 1.72, 3.95, 5.0, "한계 (솔직하게)", ["모델 F1·AI 품질 실데이터 "
                                                "미측정", "EC2 운영 연결 미확인", "토큰을 localStorage에 저장", "알림은 사이트 내 알림만",
                                                  "공유 DB 백업·복구 절차 미정"], row=.62)
    card(s, 8.8, 1.72, 3.95, 5.0, "다음 단계", ["판정 적중률 집계·공개", "응답 시간·부하 실측", "HttpOnly 쿠키 인증 검토", "모바일 푸시(PWA)", "카드·쿠폰 실결제가"],
         stroke=CYAN, row=.62)
    note("한계를 먼저 말하고 개선 계획으로 연결하면 신뢰를 얻습니다. 측정하지 않은 성능 수치는 말하지 않습니다.",
         ["다시 한다면 무엇을 바꾸겠나요?", "이 프로젝트에서 배운 가장 큰 것은?"])


# ------------------------------------------------------------------ 18 마무리
def s18(s):
    frame(s, 18, "THANK YOU", None)
    text(s, "가격 비교를 넘어,\n[[구매 타이밍]]까지.", .6, 1.2, 8.5, 1.95, 40, WHITE, True)
    text(s, "코드와 문서로 확인할 수 있습니다", .62, 3.3, 7, .5, 20, GRAY, True)
    logo = ROOT / "frontend/public/brand/picktiming-logo-140.png"
    if logo.exists():
        s.shapes.add_picture(str(logo), Inches(11.0), Inches(1.3), Inches(1.5), Inches(1.5))
    links = [("GitHub", "github.com/fsclass-n/picktiming"), ("운영", "picktiming.onrender.com"), ("데모", "picktiming.netlify.app"),
             ("문서", "docs/md · docs/산출물")]
    for i, (k, v) in enumerate(links):
        x, y = .6 + (i % 2) * 6.15, 4.15 + (i // 2) * .85
        box(s, x, y, 6.0, .7, CARD, BLUE if i == 0 else BORDER)
        text(s, k, x + .25, y, 1.2, .7, 14, CYAN, True)
        text(s, v, x + 1.45, y, 4.4, .7, 15, WHITE, True)
    text(s, "Q & A", 10.5, 6.05, 2.25, .5, 22, CYAN, True, PP_ALIGN.RIGHT)
    note("마지막에 링크를 다시 보여 주고 질문을 받습니다.", ["추가로 보여 줄 코드가 있나요?"])


BUILDERS = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13, s14, s15, s16, s17, s18]


def main():
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    blank = deck.slide_layouts[6]
    for builder in BUILDERS:
        slide = deck.slides.add_slide(blank)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = color(NAVY)
        builder(slide)
    for slide, talk in zip(deck.slides, NOTES, strict=True):
        slide.notes_slide.notes_text_frame.text = talk
    props = deck.core_properties
    props.title = "PickTiming · 팀 포트폴리오"
    props.subject = "기술 면접용 포트폴리오"
    props.author = "3조 · 박미금 · 김모란 · 이오리 · 홍기흥"
    props.keywords = "PickTiming, FastAPI, React, RPA, scikit-learn, Gemini, Portfolio"
    deck.save(OUT / "프로젝트_발표자료.pptx")  # 최종 발표·포트폴리오 PPT(18장)
    print("portfolio:", len(deck.slides), "slides")


if __name__ == "__main__":
    main()
