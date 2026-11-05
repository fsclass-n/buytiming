"""원본 PPT를 바탕으로 7장 발표본·발표자 노트·대본을 생성한다."""
import io
import json
import shutil
import subprocess
from itertools import pairwise
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs"
WORK = OUT / "발표자료"
ASSETS = WORK / "assets"
STORY = json.loads((WORK / "tools/story.json").read_text(encoding="utf-8"))
NAVY, CARD, BLUE, CYAN, WHITE, GRAY = "0B1220", "111C33", "2563EB", "22D3EE", "F8FAFC", "CBD5E1"
MUTED, BORDER = "94A3B8", "263C5D"
FONT = "Noto Sans KR"
W, H = 13.333, 7.5


def color(value):
    return RGBColor.from_string(value)


def box(slide, x, y, w, h, fill=CARD, stroke=None, radius=True):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h),
    )
    if radius:
        shape.adjustments[0] = 0.07
    shape.fill.solid()
    shape.fill.fore_color.rgb = color(fill)
    if stroke:
        shape.line.color.rgb = color(stroke)
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def text(slide, value, x, y, w, h, size=22, fill=WHITE, bold=False, align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, line in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(2)
        p.line_spacing = 1.13
        r = p.add_run()
        r.text = line
        r.font.name = FONT
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color(fill)
        for tag in ("a:ea", "a:cs"):
            node = OxmlElement(tag)
            node.set("typeface", FONT)
            r._r.get_or_add_rPr().append(node)
    return shape


def line(slide, x1, y1, x2, y2, fill=CYAN, width=1.5, arrow=False):
    shape = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    shape.line.color.rgb = color(fill)
    shape.line.width = Pt(width)
    if arrow:
        tail = OxmlElement("a:tailEnd")
        tail.set("type", "triangle")
        shape.line._get_or_add_ln().append(tail)
    return shape


def circle(slide, x, y, diameter, fill=CYAN, stroke=None):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(diameter), Inches(diameter))
    s.fill.solid()
    s.fill.fore_color.rgb = color(fill)
    if stroke:
        s.line.color.rgb = color(stroke)
        s.line.width = Pt(1.4)
    else:
        s.line.fill.background()
    return s


def icon(slide, kind, x, y, size=0.48):
    if kind == "clock":
        circle(slide, x, y, size, CARD, CYAN)
        line(slide, x + size / 2, y + size * .18, x + size / 2, y + size / 2)
        line(slide, x + size / 2, y + size / 2, x + size * .76, y + size * .60)
    elif kind == "chart":
        points = [(0, .9), (.25, .5), (.50, .64), (.75, .18), (1, .33)]
        for a, b in pairwise(points):
            line(slide, x + a[0] * size, y + a[1] * size, x + b[0] * size, y + b[1] * size, width=2.5)
    elif kind == "search":
        circle(slide, x, y, size * .72, CARD, CYAN)
        line(slide, x + size * .60, y + size * .60, x + size, y + size, width=2.5)
    elif kind == "chat":
        box(slide, x, y, size, size * .75, CARD, CYAN)
        line(slide, x + size * .2, y + size * .3, x + size * .8, y + size * .3)
        line(slide, x + size * .2, y + size * .50, x + size * .6, y + size * .50)
        line(slide, x + size * .25, y + size * .75, x + size * .1, y + size, width=1.5)
    elif kind == "bell":
        points = [(.15, .75), (.25, .60), (.25, .30), (.50, .10), (.75, .30), (.75, .60), (.85, .75), (.15, .75)]
        for a, b in pairwise(points):
            line(slide, x + a[0] * size, y + a[1] * size, x + b[0] * size, y + b[1] * size)
        circle(slide, x + size * .43, y + size * .88, size * .14, CYAN)
    else:
        for i, height in enumerate([.45, .8, .62]):
            box(slide, x + i * size * .35, y + size * (1 - height), size * .2, size * height, CYAN, radius=False)


def image(slide, name, x, y, w, h, caption=None):
    # 실제 화면을 잘라 왜곡하지 않고 원래 비율로 배치한다.
    path = ASSETS / name
    box(slide, x - .06, y - .06, w + .12, h + .12, "F8FAFC", BORDER)
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    slide.shapes.add_picture(str(path), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))
    if caption:
        text(slide, caption, x, y + h + .12, w, .28, 11, MUTED)


def base(slide, index, eyebrow, title):
    # 원본의 판형과 프레젠테이션 패키지는 유지하고 슬라이드 도형을 리디자인한다.
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color(NAVY)
    surface = box(slide, 0, 0, W, H, NAVY, radius=False)
    surface.fill.gradient()
    surface.fill.gradient_angle = 15
    surface.fill.gradient_stops[0].color.rgb = color(NAVY)
    surface.fill.gradient_stops[1].color.rgb = color("111D34")
    for i in range(3):
        line(slide, 10.2 + i * .45, .0, 12.8, 2.1 - i * .35, BORDER, .5)
    text(slide, "PICKTIMING  /  " + eyebrow, .55, .32, 10.5, .30, 12, CYAN, True)
    if title:
        text(slide, title, .55, .93, 12.1, .65, 31, WHITE, True)
    line(slide, .55, 7.02, 12.78, 7.02, BORDER, .7)
    line(slide, .55, 7.02, .55 + 12.23 * index / 7, 7.02, CYAN, 1.6)
    text(slide, "FINAL PROJECT  ·  3조  ·  PickTiming", .55, 7.13, 9, .2, 10, MUTED)
    text(slide, f"{index:02d} / 07", 11.8, 7.10, .98, .27, 12, GRAY, align=PP_ALIGN.RIGHT)


def slide_one(slide):
    base(slide, 1, "PRICE COMPARISON & PURCHASE TIMING", "")
    text(slide, "PickTiming", .58, 1.30, 6.8, .85, 47, WHITE, True)
    text(slide, "좋은 가격에,\n좋은 타이밍에.", .60, 2.43, 6, 1.60, 37, WHITE, True)
    text(slide, "온라인 쇼핑객이 가격을 비교하고\n구매 시점을 판단하도록 돕습니다.", .62, 4.20, 6.1, .86, 19, GRAY)
    line(slide, .62, 5.17, 1.55, 5.17, CYAN, 3)
    text(slide, "3조  |  발표자·조장 박미금", .62, 5.49, 6.2, .45, 21, WHITE, True)
    text(slide, "박미금 · 김길동 · 이오리 · 홍기흥", .62, 6.06, 6.2, .36, 15, GRAY)
    box(slide, 7.35, 1.55, 5.35, 4.75, CARD, BLUE)
    text(slide, "어디서 살까 → 언제 살까", 7.65, 1.88, 4.7, .5, 22, CYAN, True)
    image(slide, "home.png", 7.62, 2.65, 4.78, 2.72)
    text(slide, "실제 UI · Netlify 데모 화면", 7.65, 5.66, 4.7, .33, 13, GRAY)


def slide_two(slide):
    base(slide, 2, "WHY", "최저가를 찾아도, 살 시점은 남습니다")
    text(slide, "“지금 사도 될까요?”", .65, 2.15, 6.4, .8, 34, WHITE, True)
    text(slide, "현재 가격만으로는\n구매 시점을 판단하기 어렵습니다.", .68, 3.25, 6.0, 1.2, 23, GRAY)
    text(slide, "가격과 시간, 두 질문을 함께 다룹니다.", .68, 5.38, 6.0, .8, 22, CYAN, True)
    cards = [
        ("PROBLEM", "가격·배송비가 제각각", "비교하고도 남는 구매 시점의 고민"),
        ("SOLUTION", "가격 이력과 판단 근거", "실구매가 + 가격 추이 + 구매 적기"),
        ("VALUE", "근거를 보고 선택", "비교의 번거로움과 판단 부담 줄이기"),
    ]
    for i, (tag, title, body) in enumerate(cards):
        y = 1.95 + i * 1.50
        box(slide, 7.15, y, 5.5, 1.32, CARD, BORDER)
        text(slide, tag, 7.43, y + .12, 4.9, .25, 11, CYAN, True)
        text(slide, title, 7.43, y + .43, 4.9, .43, 23, WHITE, True)
        text(slide, body, 7.43, y + .93, 4.9, .24, 15, GRAY)


def slide_three(slide):
    base(slide, 3, "SERVICE FLOW", "비교에서 알림까지, 한 번의 흐름으로")
    steps = [
        ("수집", "상품 가격 모으기", "search"), ("비교", "배송비 포함 가격", "bars"),
        ("판단", "가격 차트·적기", "chart"), ("설명", "AI 조언·상담", "chat"), ("알림", "나의 목표 가격", "bell"),
    ]
    for i, (title, body, symbol) in enumerate(steps):
        x = .58 + i * 2.52
        box(slide, x, 2.40, 2.18, 2.38, CARD, BORDER)
        icon(slide, symbol, x + .83, 2.75, .44)
        text(slide, title, x + .10, 3.43, 1.98, .5, 27, WHITE, True, PP_ALIGN.CENTER)
        text(slide, body, x + .08, 4.13, 2.02, .35, 16, GRAY, align=PP_ALIGN.CENTER)
        if i < 4:
            line(slide, x + 2.20, 3.59, x + 2.47, 3.59, CYAN, 1.6, True)
    for x, title, body in [
        (.68, "같은 기준으로 비교", "판매가 + 배송비"),
        (4.90, "시간의 흐름을 확인", "7일 · 30일 · 90일"),
        (9.08, "기다리는 선택도 지원", "관심 상품 · 사이트 알림"),
    ]:
        text(slide, title, x, 5.45, 3.7, .42, 19, CYAN, True)
        text(slide, body, x, 6.03, 3.7, .35, 17, GRAY)


def slide_four(slide):
    base(slide, 4, "SYSTEM", "가격을 모으고, 분석하고, 설명합니다")
    blocks = [
        (.60, "사용자", "검색 · 확인 · 알림"),
        (3.78, "웹 브라우저", "React / Vite"),
        (6.96, "서버", "FastAPI · 권한 검사"),
        (10.14, "데이터베이스", "TiDB · 가격 이력"),
    ]
    for i, (x, title, sub) in enumerate(blocks):
        box(slide, x, 2.82, 2.58, 1.35, CARD, BORDER)
        text(slide, title, x + .12, 3.04, 2.34, .45, 22, WHITE, True, PP_ALIGN.CENTER)
        text(slide, sub, x + .08, 3.61, 2.42, .3, 15, GRAY, align=PP_ALIGN.CENTER)
        if i < 3:
            line(slide, x + 2.62, 3.50, x + 3.10, 3.50, CYAN, 1.6, True)
    box(slide, 6.96, 1.87, 5.76, .67, "142744", BORDER)
    text(slide, "RPA 수집  ·  등록 판매처 / 설정된 검색 API", 7.15, 2.04, 5.36, .30, 16, GRAY)
    line(slide, 8.23, 2.54, 8.23, 2.79, CYAN, 1.5, True)
    box(slide, 6.96, 4.61, 5.76, 1.15, "142744", BORDER)
    text(slide, "분석 모델·규칙 → Gemini 설명", 7.20, 4.79, 5.20, .38, 20, WHITE, True)
    text(slide, "수치 검증 · 실패 시 정해진 설명으로 대체", 7.20, 5.31, 5.20, .26, 15, GRAY)
    line(slide, 8.23, 4.20, 8.23, 4.58, CYAN, 1.5, True)
    text(slide, "자동 수집은 1시간 주기\n배포 환경에 따라 실행 위치를 분리", .65, 4.73, 5.8, .88, 20, GRAY)
    for x, value in [
        (.60, "Netlify  |  브라우저 데모"),
        (4.76, "Render  |  독립 풀스택 운영"),
        (8.92, "EC2  |  배포 구성·운영 확인 전"),
    ]:
        box(slide, x, 6.22, 3.82, .47, CARD)
        text(slide, value, x + .12, 6.31, 3.58, .24, 13, CYAN)


def slide_five(slide):
    base(slide, 5, "PRODUCT", "가격과 판단 근거를 한 화면에서")
    image(slide, "product-chart.png", .62, 2.05, 8.77, 4.33, "실제 웹사이트 캡처 · Netlify 데모 데이터")
    for i, (title, body) in enumerate([
        ("가격의 흐름", "7·30·90일\n판매처별 탐색"),
        ("구매 신호등", "점수와 근거 확인\n미래 가격 보장 아님"),
        ("내 목표가", "관심 상품 저장\n사이트에서 알림 확인"),
    ]):
        y = 2.05 + i * 1.49
        text(slide, f"0{i + 1}", 9.78, y, 2.75, .35, 16, CYAN, True)
        text(slide, title, 9.78, y + .40, 2.75, .47, 23, WHITE, True)
        text(slide, body, 9.78, y + .94, 2.75, .62, 16, GRAY)


def slide_six(slide):
    base(slide, 6, "ACCESS & OPERATIONS", "회원은 쇼핑을, 관리자는 운영을")
    for x in [.60, 6.90]:
        box(slide, x, 1.97, 5.83, 4.72, CARD, BORDER)
    text(slide, "일반 회원", .90, 2.24, 5.2, .48, 26, WHITE, True)
    text(slide, "상품 비교 · AI 상담\n관심 상품 · 목표가 알림", .90, 3.03, 5.2, 1.0, 21, GRAY)
    image(slide, "watchlist.png", .92, 4.43, 5.18, 1.78)
    text(slide, "관리자", 7.20, 2.24, 5.2, .48, 26, WHITE, True)
    text(slide, "회원·권한 관리\n수집·모델 · AI 사용량", 7.20, 3.03, 5.2, 1.0, 21, GRAY)
    image(slide, "admin-users.png", 7.22, 4.43, 5.18, 1.78)
    text(slide, "화면: Netlify 데모", .95, 6.38, 5.0, .22, 11, MUTED)
    text(slide, "테스트 관리자: 조회 전용", 7.25, 6.38, 5.0, .22, 12, CYAN)


def slide_seven(slide):
    base(slide, 7, "PROOF → LIVE DEMO", "이제, 직접 확인하겠습니다")
    text(slide, "비교 시간은 줄이고,\n구매 판단의 근거는 명확하게.", .65, 2.02, 8.8, 1.42, 32, WHITE, True)
    text(slide, "기대 효과", 10.40, 2.16, 2.1, .38, 17, CYAN, True)
    for x, num, label in [
        (.65, "51", "백엔드 테스트"),
        (3.70, "11", "RPA 테스트"),
        (6.75, "9", "브라우저 시나리오"),
    ]:
        box(slide, x, 3.93, 2.73, 1.24, CARD, BORDER)
        text(slide, num, x + .19, 4.05, 2.32, .54, 31, CYAN, True)
        text(slide, label, x + .19, 4.68, 2.32, .29, 15, GRAY)
    text(slide, "배포 검사 통과\n2026.11.05 확인", 10.0, 4.17, 2.6, .70, 16, GRAY)
    line(slide, .65, 5.57, 12.66, 5.57, BORDER, 1)
    text(slide, "7분 시연", .65, 5.91, 2.0, .47, 24, CYAN, True)
    text(slide, "찾기 → 비교·판단 → 알림·관리", 2.95, 5.96, 9.7, .43, 23, WHITE, True)
    text(slide, "감사합니다  ·  picktiming.netlify.app", .65, 6.55, 11.9, .28, 14, GRAY)


def write_script():
    def stamp(seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    lines = ["# 3분 발표 대본 · 조장 박미금", "",
             "본편 7장. 대본 예산 170초, 전환 여유 10초. 실제 낭독 속도는 리허설에서 확인합니다.",
             "화면의 작은 설명과 기술명은 모두 읽지 않습니다. 아래 대본과 연결 멘트만 읽습니다.", ""]
    elapsed = 0
    for i, s in enumerate(STORY, 1):
        end = elapsed + s["seconds"]
        lines.extend([f"## {i}. {s['title']} · {stamp(elapsed)}–{stamp(end)} ({s['seconds']}초)", "",
                      f"핵심 메시지: {s['message']}", "", s["script"], "",
                      f"전환 멘트: {s['transition']}", ""])
        elapsed = end
    lines += ["## 02:50–03:00 전환 여유", "", "웹사이트 탭으로 전환합니다. 발표 대본을 추가하지 않습니다.",
              "권한 변경·데이터 삭제 등 운영 상태를 바꾸는 시연은 하지 않습니다.", ""]
    (WORK / "3분_발표대본.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    original = subprocess.check_output(["git", "show", "279a4ce:docs/프로젝트_발표자료.pptx"], cwd=ROOT)
    deck = Presentation(io.BytesIO(original))
    while len(deck.slides) > 7:
        slide_id = deck.slides._sldIdLst[-1]
        deck.part.drop_rel(slide_id.rId)
        deck.slides._sldIdLst.remove(slide_id)
    for i, builder in enumerate([slide_one, slide_two, slide_three, slide_four, slide_five, slide_six, slide_seven]):
        builder(deck.slides[i])
        s = STORY[i]
        deck.slides[i].notes_slide.notes_text_frame.text = (
            f"슬라이드 {i + 1} · {s['seconds']}초\n핵심 메시지: {s['message']}\n\n"
            f"대본:\n{s['script']}\n\n전환:\n{s['transition']}\n\n"
            "화면 캡처: 공개 Netlify 데모. 수치·상품은 데모이며 운영 성과로 해석하지 않음."
        )
    deck.core_properties.title = "PickTiming · 3조 최종 발표"
    deck.core_properties.subject = "3분 PPT + 7분 시연"
    deck.core_properties.author = "3조 · 박미금 · 김길동 · 이오리 · 홍기흥"
    deck.core_properties.keywords = "PickTiming, 가격 비교, 구매 타이밍, Navy Tech"
    deck.core_properties.comments = "원본 13장 리디자인. 확인되지 않은 성과 수치는 제외."
    primary = OUT / "3조_최종발표_PPT.pptx"
    deck.save(primary)
    shutil.copyfile(primary, OUT / "프로젝트_발표자료.pptx")
    write_script()
    print("PPT:", len(deck.slides), "slides; script:", sum(s["seconds"] for s in STORY), "seconds")


if __name__ == "__main__":
    main()
