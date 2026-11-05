"""원본 PPT 패키지를 바탕으로 10장 최종 발표본·발표자 노트·3분 대본을 생성한다."""
import io
import json
import re
import subprocess
import tempfile
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
CACHE = Path(tempfile.mkdtemp(prefix="picktiming-slides-"))
STORY = json.loads((WORK / "tools/story.json").read_text(encoding="utf-8"))
NAVY, CARD, PANEL, BLUE, CYAN, WHITE, GRAY = "0B1220", "111C33", "142744", "2563EB", "22D3EE", "F8FAFC", "CBD5E1"
MUTED, BORDER = "94A3B8", "263C5D"
FONT = "Noto Sans KR"
W, H = 13.333, 7.5
TOTAL = 10
ACCENT = re.compile(r"\[\[(.+?)\]\]")


def color(value):
    return RGBColor.from_string(value)


def box(slide, x, y, w, h, fill=CARD, stroke=None, radius=True, width=1.0):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        shape.adjustments[0] = min(0.12, 0.09 / max(min(w, h), 0.3))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color(fill)
    if stroke:
        shape.line.color.rgb = color(stroke)
        shape.line.width = Pt(width)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def text(slide, value, x, y, w, h, size=18, fill=WHITE, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.MIDDLE, accent=CYAN, spacing=1.15):
    """[[강조]] 표기는 포인트 컬러로 바꾼다. 줄바꿈은 문단으로 나눈다."""
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.clear()
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for i, line in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_before = Pt(0)
        p.space_after = Pt(3)
        p.line_spacing = spacing
        pos = 0
        parts = []
        for m in ACCENT.finditer(line):
            parts += [(line[pos:m.start()], fill), (m.group(1), accent)]
            pos = m.end()
        parts.append((line[pos:], fill))
        for chunk, tint in parts:
            if not chunk:
                continue
            r = p.add_run()
            r.text = chunk
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = color(tint)
            rpr = r._r.get_or_add_rPr()
            for tag in ("a:ea", "a:cs"):
                node = OxmlElement(tag)
                node.set("typeface", FONT)
                rpr.append(node)
    return shape


def line(slide, x1, y1, x2, y2, fill=CYAN, width=1.5, arrow=False, both=False):
    shape = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    shape.line.color.rgb = color(fill)
    shape.line.width = Pt(width)
    ln = shape.line._get_or_add_ln()
    for tag, on in (("a:headEnd", both), ("a:tailEnd", arrow or both)):
        if on:
            end = OxmlElement(tag)
            end.set("type", "triangle")
            ln.append(end)
    return shape


def circle(slide, x, y, d, fill=CYAN, stroke=None):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    s.fill.solid()
    s.fill.fore_color.rgb = color(fill)
    if stroke:
        s.line.color.rgb = color(stroke)
        s.line.width = Pt(1.4)
    else:
        s.line.fill.background()
    return s


def icon(slide, kind, x, y, s=0.44):
    """편집 가능한 기본 도형으로 만든 단순 라인 아이콘."""
    if kind == "search":
        circle(slide, x, y, s * .7, CARD, CYAN)
        line(slide, x + s * .6, y + s * .6, x + s, y + s, width=2.4)
    elif kind == "bars":
        for i, hh in enumerate([.45, .8, .62]):
            box(slide, x + i * s * .36, y + s * (1 - hh), s * .22, s * hh, CYAN, radius=False)
    elif kind == "chart":
        for a, b in pairwise([(0, .9), (.25, .5), (.5, .64), (.75, .18), (1, .33)]):
            line(slide, x + a[0] * s, y + a[1] * s, x + b[0] * s, y + b[1] * s, width=2.4)
    elif kind == "chat":
        box(slide, x, y, s, s * .72, CARD, CYAN, width=1.4)
        line(slide, x + s * .2, y + s * .28, x + s * .8, y + s * .28, width=1.2)
        line(slide, x + s * .2, y + s * .46, x + s * .6, y + s * .46, width=1.2)
        line(slide, x + s * .28, y + s * .72, x + s * .14, y + s * .96, width=1.4)
    elif kind == "bell":
        pts = [(.15, .74), (.26, .6), (.26, .3), (.5, .1), (.74, .3), (.74, .6), (.85, .74), (.15, .74)]
        for a, b in pairwise(pts):
            line(slide, x + a[0] * s, y + a[1] * s, x + b[0] * s, y + b[1] * s, width=1.6)
        circle(slide, x + s * .43, y + s * .82, s * .14, CYAN)
    elif kind == "robot":
        box(slide, x + s * .1, y + s * .25, s * .8, s * .62, CARD, CYAN, width=1.4)
        circle(slide, x + s * .28, y + s * .45, s * .14, CYAN)
        circle(slide, x + s * .58, y + s * .45, s * .14, CYAN)
        line(slide, x + s * .5, y + s * .05, x + s * .5, y + s * .25, width=1.4)


def image(slide, name, x, y, w, h, mode="cover", frame=True):
    """실제 캡처를 왜곡 없이 배치한다. cover는 위쪽 기준으로 잘라 카드 영역을 채운다."""
    src = Image.open(ASSETS / name).convert("RGB")
    iw, ih = src.size
    if frame:
        box(slide, x - .05, y - .05, w + .1, h + .1, "F8FAFC", BORDER)
    if mode == "cover":
        ratio = w / h
        if iw / ih > ratio:
            nw = int(ih * ratio)
            src = src.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
        else:
            src = src.crop((0, 0, iw, int(iw / ratio)))
        path = CACHE / f"{Path(name).stem}-{w:.2f}x{h:.2f}.png"
        src.save(path)
        slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    else:
        scale = min(w / iw, h / ih)
        pw, ph = iw * scale, ih * scale
        slide.shapes.add_picture(str(ASSETS / name), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))


def chip(slide, value, x, y, w, h=.46, fill=PANEL, stroke=BORDER, size=14, tint=WHITE, bold=False):
    box(slide, x, y, w, h, fill, stroke)
    text(slide, value, x + .1, y, w - .2, h, size, tint, bold, PP_ALIGN.CENTER)


def bullets(slide, items, x, y, w, row=.46, size=16, mark=CYAN, tint=GRAY):
    for i, item in enumerate(items):
        circle(slide, x, y + i * row + row / 2 - .045, .09, mark)
        text(slide, item, x + .24, y + i * row, w - .24, row, size, tint)


def base(slide, index, eyebrow, title=None, total=TOTAL, footer="PickTiming  ·  3조  ·  Final Project"):
    # 원본 PPT 패키지(판형·노트 구조)를 유지하고 슬라이드 도형만 새로 구성한다.
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color(NAVY)
    surface = box(slide, 0, 0, W, H, NAVY, radius=False)
    surface.fill.gradient()
    surface.fill.gradient_angle = 20
    surface.fill.gradient_stops[0].color.rgb = color(NAVY)
    surface.fill.gradient_stops[1].color.rgb = color("10203A")
    # 은은한 기술 라인: 오른쪽 위 네트워크 선과 노드 몇 개만 둔다.
    for i in range(4):
        line(slide, 9.9 + i * .5, 0, 12.9, 1.9 - i * .38, BORDER, .5)
    for nx, ny in [(11.35, .62), (12.2, .98), (12.62, .36)]:
        circle(slide, nx, ny, .07, "1E3A5F")
    text(slide, eyebrow, .6, .34, 9.5, .3, 12, CYAN, True)
    if title:
        text(slide, title, .6, .78, 12.1, .72, 30, WHITE, True)
    line(slide, .6, 7.0, 12.75, 7.0, BORDER, .7)
    line(slide, .6, 7.0, .6 + 12.15 * index / total, 7.0, CYAN, 1.8)
    text(slide, footer, .6, 7.1, 8, .26, 10, MUTED)
    text(slide, f"{index:02d} / {total:02d}", 11.6, 7.08, 1.15, .28, 12, GRAY, align=PP_ALIGN.RIGHT)


def slide_cover(s):
    base(s, 1, "FINAL PROJECT  |  심화_생성형 AI와 AWS 클라우드를 활용한 풀스택 & 자동화 실무 개발")
    text(s, "PickTiming", .6, 1.18, 6.5, .95, 50, WHITE, True)
    text(s, "픽타이밍", .64, 2.1, 4, .4, 20, GRAY)
    text(s, "좋은 가격에,\n[[좋은 타이밍]]에.", .6, 2.68, 6.4, 1.45, 34, WHITE, True)
    text(s, "생성형 AI & RPA 기반 실시간 가격 비교 · 구매 타이밍 추천", .64, 4.3, 6.5, .38, 16, GRAY)
    line(s, .64, 4.92, 1.55, 4.92, CYAN, 3)
    text(s, "3조   |   발표 · 조장 [[박미금]]", .64, 5.15, 6.4, .45, 21, WHITE, True)
    for i, (name, role) in enumerate([("박미금", "조장·PM·데이터/AI"), ("김모란", "백엔드·배포"),
                                      ("이오리", "프런트엔드·UI/UX"), ("홍기흥", "RPA·데이터 수집")]):
        x, y = .64 + (i % 2) * 3.25, 5.66 + (i // 2) * .34
        text(s, f"[[{name}]]  {role}", x, y, 3.2, .32, 13, GRAY, accent=WHITE)
    text(s, "2026-12-18  프로젝트 발표회", .64, 6.4, 6.4, .3, 12, MUTED)
    box(s, 7.3, 1.25, 5.45, 5.1, CARD, BLUE)
    text(s, "LIVE SERVICE", 7.58, 1.48, 3, .3, 12, CYAN, True)
    text(s, "어디서 살까 → [[언제 살까]]", 7.58, 1.82, 4.9, .45, 21, WHITE, True)
    image(s, "home.png", 7.58, 2.5, 4.89, 2.75, "contain")
    text(s, "실제 UI · 홈 화면 (데모 데이터)", 7.58, 5.42, 4.9, .3, 12, GRAY)
    text(s, "picktiming.onrender.com  ·  picktiming.netlify.app", 7.58, 5.78, 4.9, .3, 12, MUTED)


def slide_intro(s):
    base(s, 2, "01  ·  PROJECT", "가격 비교와 구매 타이밍을 한 화면에")
    box(s, .6, 1.72, 12.15, 1.25, CARD, BLUE)
    text(s, "온라인 쇼핑 소비자가 [[실구매가]]와 [[가격 흐름]]을 한눈에 비교하고,\n지금 살지 기다릴지 [[근거를 갖고 결정]]하도록 돕는 웹 서비스",
         .95, 1.8, 11.5, 1.1, 20, WHITE, True)
    cards = [("목적", "현명한 구매 시점 결정", "가격과 시점을 함께 판단"),
             ("서비스", "가격 비교 + 구매 타이밍", "PC·모바일 반응형 웹"),
             ("주요 사용자", "온라인 쇼핑 소비자", "가격 변화에 민감한 구매자"),
             ("핵심 가치", "시간 절약 · 근거 있는 결정", "비교부터 알림까지 한 번에")]
    for i, (k, v, sub) in enumerate(cards):
        x = .6 + i * 3.08
        box(s, x, 3.17, 2.92, 1.4, CARD, BORDER)
        text(s, k, x + .22, 3.27, 2.5, .3, 12, CYAN, True)
        text(s, v, x + .22, 3.6, 2.6, .45, 16, WHITE, True)
        text(s, sub, x + .22, 4.08, 2.55, .32, 13, GRAY)
    text(s, "SERVICE FLOW", .6, 4.78, 4, .3, 12, CYAN, True)
    flow = [("수집", "1시간 주기 자동", "robot"), ("비교", "배송비 포함 실구매가", "bars"), ("판단", "0~100 적기 점수", "chart"),
            ("설명", "AI 조언 · 상담", "chat"), ("알림", "목표가 · 판정 변화", "bell")]
    for i, (name, sub, ic) in enumerate(flow):
        x = .6 + i * 2.49
        box(s, x, 5.12, 2.18, 1.5, CARD, BLUE if i == 2 else BORDER)
        icon(s, ic, x + .2, 5.32, .42)
        text(s, name, x + .78, 5.27, 1.3, .5, 21, WHITE, True)
        text(s, sub, x + .2, 5.92, 1.9, .5, 13, GRAY)
        if i < 4:
            line(s, x + 2.2, 5.87, x + 2.47, 5.87, CYAN, 1.6, True)


def slide_background(s):
    base(s, 3, "02  ·  BACKGROUND", "최저가를 찾아도, ‘언제 살까’는 남습니다")
    box(s, .6, 1.72, 5.65, 4.95, CARD, BORDER)
    text(s, "“지금 사도 될까요?”", .9, 1.92, 5.1, .62, 28, WHITE, True)
    # 이해를 돕는 예시 그래프(실측 데이터 아님): 가격이 오르내리는 흐름만 표현한다.
    ox, oy, gw, gh = 1.05, 2.95, 4.75, 2.55
    line(s, ox, oy + gh, ox + gw, oy + gh, BORDER, 1)
    line(s, ox, oy, ox, oy + gh, BORDER, 1)
    pts = [(0, .35), (.12, .3), (.22, .55), (.34, .5), (.45, .78), (.56, .4), (.68, .45), (.8, .62), (.9, .25), (1, .35)]
    xy = [(ox + px * gw, oy + gh - py * gh) for px, py in pts]
    for a, b in pairwise(xy):
        line(s, a[0], a[1], b[0], b[1], CYAN, 2.4)
    hx, hy = xy[6]
    circle(s, hx - .09, hy - .09, .18, BLUE, WHITE)
    text(s, "오늘 최저가", hx - .75, hy + .14, 1.5, .3, 12, WHITE, True, PP_ALIGN.CENTER)
    line(s, xy[8][0], oy + .05, xy[8][0], oy + gh, MUTED, 1)
    text(s, "며칠 뒤에는?", xy[8][0] - .8, oy - .32, 1.6, .3, 12, GRAY, align=PP_ALIGN.CENTER)
    text(s, "가격은 매일 바뀝니다  ·  그래프는 이해를 돕기 위한 예시", .9, 5.85, 5.1, .5, 12, MUTED)
    rows = [("01", "판매처마다 다른 가격", "판매가·배송비·조건이 달라 직접 계산해야 합니다"),
            ("02", "매일 바뀌는 가격", "오늘의 최저가가 내일도 최저가인지 알기 어렵습니다"),
            ("03", "판단은 소비자의 몫", "현재 가격 중심 비교로는 살 시점의 근거가 부족합니다")]
    for i, (no, head, desc) in enumerate(rows):
        y = 1.72 + i * 1.5
        box(s, 6.5, y, 6.25, 1.35, CARD, BORDER)
        text(s, no, 6.75, y + .2, .6, .4, 18, CYAN, True)
        text(s, head, 7.4, y + .17, 5.1, .45, 20, WHITE, True)
        text(s, desc, 7.4, y + .7, 5.2, .4, 14, GRAY)
    text(s, "‘어디서 살까’에서 ‘[[언제 살까]]’까지", 6.5, 6.3, 6.25, .4, 18, WHITE, True, PP_ALIGN.RIGHT)


def slide_goal(s):
    base(s, 4, "03  ·  GOAL", "문제에서 해결, 그리고 가치로")
    cols = [("PROBLEM", "기존 문제점", BORDER, MUTED,
             ["여러 쇼핑몰을 하나씩 비교", "배송비는 따로 계산", "살 시점의 근거 부족", "가격 확인을 반복"]),
            ("SOLUTION", "해결 방법", BLUE, "60A5FA",
             ["1시간 주기 RPA 자동 수집", "배송비 포함 실구매가 비교", "가격 흐름 기반 적기 점수·AI 설명", "목표가 등록과 알림"]),
            ("VALUE", "기대 효과", CYAN, CYAN,
             ["비교 시간 절약", "같은 기준의 공정한 비교", "근거 있는 구매 결정", "기다리는 선택도 편하게"])]
    for i, (tag, head, stroke, tint, items) in enumerate(cols):
        x = .6 + i * 4.18
        box(s, x, 1.72, 3.8, 3.92, CARD, stroke, width=1.4)
        text(s, tag, x + .3, 1.92, 3, .32, 14, tint, True)
        text(s, head, x + .3, 2.3, 3.2, .5, 22, WHITE, True)
        line(s, x + .3, 2.95, x + 3.5, 2.95, BORDER, .8)
        bullets(s, items, x + .32, 3.12, 3.35, .58, 16, tint)
        if i < 2:
            line(s, x + 3.84, 3.68, x + 4.14, 3.68, CYAN, 2, True)
    text(s, "개발 목표", .6, 5.92, 1.3, .5, 15, CYAN, True)
    for i, goal in enumerate(["① 가격 수집 자동화", "② 실구매가 비교", "③ 구매 시점 판단", "④ 놓치지 않는 알림"]):
        chip(s, goal, 1.95 + i * 2.72, 5.9, 2.57, .55, PANEL, BLUE if i == 2 else BORDER, 15, WHITE, True)


def slide_system(s):
    base(s, 5, "04  ·  ARCHITECTURE", "모으고, 분석하고, 설명합니다")
    nodes = [(.6, 1.9, "사용자", "PC · 모바일 웹"), (3.05, 2.55, "프론트엔드", "React · Vite · Tailwind"),
             (6.15, 2.7, "백엔드 서버", "FastAPI · 로그인·권한"), (9.4, 3.35, "데이터베이스", "TiDB Cloud (MySQL 호환)")]
    for i, (x, w, head, sub) in enumerate(nodes):
        box(s, x, 2.45, w, 1.3, CARD, BLUE if i == 2 else BORDER, width=1.3)
        text(s, head, x + .1, 2.58, w - .2, .5, 19, WHITE, True, PP_ALIGN.CENTER)
        text(s, sub, x + .1, 3.1, w - .2, .4, 13, GRAY, align=PP_ALIGN.CENTER)
    for (x1, x2, label) in [(2.5, 3.05, "⑤ 화면"), (5.6, 6.15, "요청"), (8.85, 9.4, "② 저장")]:
        line(s, x1 + .04, 3.1, x2 - .04, 3.1, CYAN, 1.6, both=True)
        text(s, label, x1 - .2, 2.72, x2 - x1 + .4, .28, 11, CYAN, True, PP_ALIGN.CENTER)
    box(s, 6.15, 1.58, 2.7, .62, PANEL, BORDER)
    icon(s, "robot", 6.3, 1.68, .38)
    text(s, "RPA 수집 · 1시간", 6.78, 1.6, 2.0, .58, 14, WHITE, True)
    line(s, 7.5, 2.22, 7.5, 2.43, CYAN, 1.6, True)
    text(s, "① 수집", 7.62, 2.17, .9, .28, 11, CYAN, True)
    text(s, "robots.txt 확인 · 3초 간격\n이상치(±50%) 제외 · 재시도 3회", 9.4, 1.55, 3.35, .7, 12, GRAY)
    box(s, 6.15, 4.3, 2.7, 1.0, PANEL, BORDER)
    text(s, "분석 엔진", 6.3, 4.38, 2.4, .42, 16, WHITE, True, PP_ALIGN.CENTER)
    text(s, "모델 또는 규칙 · 적기 점수", 6.3, 4.8, 2.4, .35, 12, GRAY, align=PP_ALIGN.CENTER)
    line(s, 7.5, 3.77, 7.5, 4.28, CYAN, 1.6, True)
    text(s, "③ 분석", 7.62, 3.88, .9, .28, 11, CYAN, True)
    box(s, 9.4, 4.3, 3.35, 1.0, PANEL, BORDER)
    text(s, "Google Gemini", 9.55, 4.38, 3.05, .42, 16, WHITE, True, PP_ALIGN.CENTER)
    text(s, "근거 설명 · 숫자 검증 · 대체 응답", 9.55, 4.8, 3.05, .35, 12, GRAY, align=PP_ALIGN.CENTER)
    line(s, 8.87, 4.8, 9.38, 4.8, CYAN, 1.6, True)
    text(s, "④ 설명", 8.75, 4.42, .75, .28, 11, CYAN, True, PP_ALIGN.CENTER)
    box(s, .6, 4.3, 5.0, 1.0, CARD, BORDER)
    text(s, "데이터 흐름", .85, 4.38, 3, .3, 12, CYAN, True)
    text(s, "① 수집 → ② 저장 → ③ 분석\n→ ④ 설명 → ⑤ 화면·알림", .85, 4.64, 4.65, .62, 14, WHITE, True, spacing=1.05)
    text(s, "배포 환경", .6, 5.55, 3, .28, 12, CYAN, True)
    deploys = [("Netlify", "프론트엔드 데모"), ("Render", "풀스택 운영 (화면+API)"),
               ("AWS EC2", "nginx·API·RPA 배포 구성"), ("GitHub Actions", "CI · 자동 배포 · 예약 수집")]
    for i, (head, sub) in enumerate(deploys):
        x = .6 + i * 3.07
        box(s, x, 5.88, 2.94, .85, CARD, BLUE if head == "Render" else BORDER)
        text(s, head, x + .18, 5.93, 2.6, .38, 15, WHITE, True)
        text(s, sub, x + .18, 6.3, 2.7, .32, 12, GRAY)


def slide_features(s):
    base(s, 6, "05  ·  FEATURES", "구매 판단에 필요한 정보를 한 화면에")
    feats = [("01", "상품 검색·필터", "search.png", "cover", "카테고리·추천 필터\n가격·점수 순 정렬", BORDER),
             ("02", "실구매가·가격 흐름", "product-chart.png", "contain", "판매처별 배송비 포함\n7·30·90일 가격 차트", BLUE),
             ("03", "구매 타이밍·\nAI 조언", "ai-advice.png", "contain", "0~100 적기 점수\n쉬운 말 설명·상담", BLUE),
             ("04", "목표가·가격 알림", "alerts.png", "cover", "관심 상품 목표가\n도달·판정 변화 알림", BORDER)]
    for i, (no, name, img, mode, desc, stroke) in enumerate(feats):
        x, y = .6 + (i % 2) * 6.15, 1.72 + (i // 2) * 2.38
        box(s, x, y, 6.0, 2.25, CARD, stroke, width=1.3)
        image(s, img, x + .18, y + .18, 3.35, 1.89, mode)
        text(s, no, x + 3.8, y + .22, 1, .32, 14, CYAN, True)
        text(s, name, x + 3.8, y + .55, 2.1, .75, 18, WHITE, True, anchor=MSO_ANCHOR.TOP)
        text(s, desc, x + 3.8, y + 1.28, 2.1, .75, 13, GRAY, anchor=MSO_ANCHOR.TOP)
    text(s, "＋ 3단계 회원가입·관심 카테고리   ＋ 소셜 로그인 연동(키 설정 시)   ＋ 모바일 반응형·키보드 사용",
         .6, 6.5, 9.4, .34, 13, GRAY)
    text(s, "화면: 실제 UI · 데모 데이터", 10.0, 6.5, 2.75, .34, 11, MUTED, align=PP_ALIGN.RIGHT)


def slide_roles(s):
    base(s, 7, "06  ·  ACCOUNTS", "회원은 쇼핑을, 관리자는 운영을")
    cards = [(.6, "USER", "일반 회원", BLUE, "60A5FA",
              ["상품 검색·비교", "가격 흐름·적기 점수", "AI 조언·상담 (일일 한도)", "관심 상품·목표가", "가격 알림·읽음 관리", "가입 시 관심 카테고리"],
              "watchlist.png", "화면: 내 관심 상품 (데모)"),
             (6.75, "ADMIN", "관리자", CYAN, CYAN,
              ["회원 기능 전체 포함", "회원 검색·권한 변경", "수집 현황·작업 로그", "모델 버전·성능 확인", "AI 호출·응답·검증 현황", "운영 통계 차트"],
              "admin-dashboard.png", "화면: 관리자 수집·모델 (데모 수치)")]
    for x, tag, head, stroke, tint, items, img, cap in cards:
        box(s, x, 1.72, 6.0, 4.2, CARD, stroke, width=1.5)
        chip(s, tag, x + .25, 1.92, 1.05, .4, PANEL, stroke, 11, tint, True)
        text(s, head, x + 1.45, 1.86, 3, .5, 22, WHITE, True)
        for j, item in enumerate(items):
            cx, cy = x + .3 + (j % 2) * 2.85, 2.55 + (j // 2) * .42
            text(s, "✓", cx, cy, .25, .38, 14, tint, True)
            text(s, item, cx + .28, cy, 2.55, .38, 14, GRAY)
        image(s, img, x + .3, 3.95, 5.4, 1.55, "cover")
        text(s, cap, x + .3, 5.56, 5.4, .28, 11, MUTED)
    box(s, .6, 6.08, 12.15, .7, PANEL, BORDER)
    text(s, "권한 보호", .85, 6.08, 1.3, .7, 14, CYAN, True)
    text(s, "비회원: 홈·안내·가입만   |   서버에서 로그인·관리자 권한 검사   |   테스트 관리자 조회 전용   |   본인·마지막 관리자 권한 변경 불가",
         2.15, 6.08, 10.45, .7, 13, WHITE)


def slide_difference(s):
    base(s, 8, "07  ·  DIFFERENTIATION", "현재 최저가에서, 구매 시점까지")
    quads = [(.6, 1.72, "기존 방식 대비 개선", BORDER), (6.75, 1.72, "기술적 특징", BORDER),
             (.6, 4.2, "사용자 편의성", BORDER), (6.75, 4.2, "실제 구현 성과", CYAN)]
    for x, y, head, stroke in quads:
        box(s, x, y, 6.0, 2.35, CARD, stroke, width=1.3)
        text(s, head, x + .3, y + .15, 5, .42, 18, WHITE, True)
    chip(s, "기존 · 현재 최저가", .9, 2.45, 2.2, .55, PANEL, BORDER, 14, GRAY)
    line(s, 3.15, 2.72, 3.55, 2.72, CYAN, 2, True)
    chip(s, "실구매가 + 90일 흐름 + 구매 시점", 3.6, 2.45, 2.75, .55, PANEL, BLUE, 13, WHITE, True)
    text(s, "‘어디서’에 ‘[[언제]]’를 더해 구매 결정까지 돕습니다", .9, 3.25, 5.4, .5, 14, GRAY)
    bullets(s, ["RPA 자동 수집 · robots.txt·3초 간격·이상치 제외", "적기 점수 = 하락 가능성 70% + 90일 가격 위치 30%",
                "AI 답변 숫자 검증 → 재요청 → 정해진 설명 대체", "데모(Netlify)와 운영(Render) 환경 분리"], 7.05, 2.35, 5.6, .45, 13)
    bullets(s, ["신호등·점수로 한눈에 판단", "쉬운 말 설명 · 바로 질문하기", "목표가 등록 후 알림 확인", "모바일 반응형 · 키보드 사용"], .9, 4.83, 5.5, .4, 14)
    for i, (num, label) in enumerate([("51", "백엔드 테스트"), ("11", "RPA 테스트"), ("9", "화면 시나리오")]):
        x = 7.05 + i * 1.85
        text(s, num, x, 4.75, 1.7, .62, 32, CYAN, True)
        text(s, label, x, 5.38, 1.75, .3, 13, GRAY)
    text(s, "375·768·1440px 화면 확인 · CI(SQLite·MySQL 8·Docker) 통과 · Render 운영 배포", 7.05, 5.82, 5.55, .5, 12, WHITE)


def slide_impact(s):
    base(s, 9, "08  ·  IMPACT", "비교는 빠르게, 결정은 근거 있게")
    text(s, "BEFORE  ·  지금까지", .6, 1.75, 5, .35, 14, MUTED, True)
    text(s, "AFTER  ·  PickTiming", 7.2, 1.75, 5, .35, 14, CYAN, True)
    rows = [("여러 쇼핑몰을 하나씩 확인", "판매처별 [[실구매가]]를 한 화면에서"), ("배송비를 따로 계산", "[[배송비 포함]] 가격으로 바로 비교"),
            ("감으로 구매 시점 결정", "[[가격 흐름·점수·AI 설명]]으로 판단"), ("가격을 반복해서 확인", "[[목표가]] 등록 후 알림 확인")]
    for i, (before, after) in enumerate(rows):
        y = 2.2 + i * .82
        box(s, .6, y, 5.45, .68, CARD, BORDER)
        text(s, before, .9, y, 5.0, .68, 16, GRAY)
        line(s, 6.2, y + .34, 7.05, y + .34, CYAN, 2, True)
        box(s, 7.2, y, 5.55, .68, CARD, BLUE)
        text(s, after, 7.5, y, 5.1, .68, 16, WHITE, True)
    text(s, "향후 계획", .6, 5.78, 1.4, .55, 14, CYAN, True)
    for i, plan in enumerate(["카드·쿠폰 할인 반영", "판정 사후 적중률 공개", "공식 제휴 API 확대", "모바일 푸시 알림"]):
        chip(s, plan, 1.95 + i * 2.72, 5.78, 2.57, .55, PANEL, BORDER, 14)
    text(s, "※ 절약 시간·금액 등 정량 효과는 실사용 데이터 확보 후 측정 예정", .6, 6.5, 12, .3, 11, MUTED)


def slide_closing(s):
    base(s, 10, "THANK YOU")
    text(s, "가격 비교를 넘어,\n[[구매 타이밍]]까지.", .6, 1.1, 8.5, 1.95, 40, WHITE, True)
    text(s, "감사합니다", .62, 3.2, 5, .55, 26, GRAY, True)
    logo = ROOT / "frontend/public/brand/picktiming-logo-140.png"
    if logo.exists():
        s.shapes.add_picture(str(logo), Inches(11.0), Inches(1.3), Inches(1.5), Inches(1.5))
    box(s, .6, 4.05, 12.15, 1.75, CARD, BLUE)
    text(s, "NEXT  ·  7분 라이브 시연", .9, 4.18, 6, .4, 15, CYAN, True)
    for i, step in enumerate(["① 검색 · 비교", "② 가격 흐름 · AI 판단", "③ 목표가 · 알림", "④ 관리자 화면"]):
        x = .9 + i * 2.95
        chip(s, step, x, 4.78, 2.6, .66, PANEL, BORDER, 16, WHITE, True)
        if i < 3:
            line(s, x + 2.63, 5.11, x + 2.92, 5.11, CYAN, 1.6, True)
    text(s, "운영  picktiming.onrender.com     데모  picktiming.netlify.app", .6, 6.1, 9, .4, 14, GRAY)
    text(s, "Q & A", 10.5, 6.02, 2.25, .5, 22, CYAN, True, PP_ALIGN.RIGHT)


BUILDERS = [slide_cover, slide_intro, slide_background, slide_goal, slide_system,
            slide_features, slide_roles, slide_difference, slide_impact, slide_closing]


def stamp(seconds):
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def write_script():
    total = sum(s["seconds"] for s in STORY)
    lines = ["# 3분 발표 대본 · 3조 조장 박미금", "",
             f"PPT 10장 · 대본 시간 예산 {total}초 · 시연 화면 전환 여유 {180 - total}초 · 합계 3분.",
             "말투: 친근하고 차분하게, 문장 끝을 내려 신뢰감 있게. 화면의 작은 글씨는 읽지 않고 대본만 말합니다.", "",
             "## 타임라인", "", "| 장 | 시간 | 제목 | 핵심 메시지 |", "|---|---|---|---|"]
    t = 0
    for i, s in enumerate(STORY, 1):
        lines.append(f"| {i} | {stamp(t)}–{stamp(t + s['seconds'])} ({s['seconds']}초) | {s['title']} | {s['message']} |")
        t += s["seconds"]
    lines += [f"| — | {stamp(t)}–03:00 ({180 - t}초) | 시연 화면 전환 | 브라우저로 이동, 대본 없음 |", ""]
    t = 0
    for i, s in enumerate(STORY, 1):
        lines += [f"## 슬라이드 {i}. {s['title']}", "",
                  f"- 예상 시간: {s['seconds']}초 ({stamp(t)}–{stamp(t + s['seconds'])})",
                  f"- 핵심 메시지: {s['message']}", "",
                  f"**대본** {s['script']}", "", f"**전환 멘트** {s['transition']}", ""]
        t += s["seconds"]
    lines += ["## 발표 팁", "",
              "- 슬라이드 5(시스템)와 6(기능)이 가장 깁니다. 화살표 순서대로 손이나 포인터로 짚으며 말합니다.",
              "- 슬라이드 7·8의 관리자 화면 수치는 데모 데이터입니다. 화면 숫자를 성과로 읽지 않습니다.",
              "- 슬라이드 8의 51·11·9는 기능 검사 수입니다. 예측 정확도나 만족도로 표현하지 않습니다.",
              "- 마지막 전환 멘트 후 바로 브라우저를 띄웁니다. 시연 순서는 7분 시연 시나리오를 따릅니다.", ""]
    (WORK / "3분_발표대본.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    original = subprocess.check_output(["git", "show", "279a4ce:docs/프로젝트_발표자료.pptx"], cwd=ROOT)
    deck = Presentation(io.BytesIO(original))
    while len(deck.slides) > TOTAL:
        slide_id = deck.slides._sldIdLst[-1]
        deck.part.drop_rel(slide_id.rId)
        deck.slides._sldIdLst.remove(slide_id)
    t = 0
    for i, builder in enumerate(BUILDERS):
        builder(deck.slides[i])
        s = STORY[i]
        deck.slides[i].notes_slide.notes_text_frame.text = (
            f"슬라이드 {i + 1} · {s['seconds']}초 ({stamp(t)}–{stamp(t + s['seconds'])})\n"
            f"핵심 메시지: {s['message']}\n\n대본:\n{s['script']}\n\n전환:\n{s['transition']}\n\n"
            "화면 캡처는 공개 Netlify 데모의 실제 UI입니다. 상품·가격·관리자 수치는 데모 데이터이며 성과로 해석하지 않습니다."
        )
        t += s["seconds"]
    props = deck.core_properties
    props.title = "PickTiming · 3조 최종 발표"
    props.subject = "PPT 3분 + 웹 시연 7분"
    props.author = "3조 · 박미금 · 김모란 · 이오리 · 홍기흥"
    props.keywords = "PickTiming, 가격 비교, 구매 타이밍, Navy Tech"
    props.comments = "원본 13장을 10장으로 리디자인. 확인되지 않은 성과 수치는 제외."
    deck.save(OUT / "프로젝트_발표자료.pptx")
    write_script()
    print("PPT:", len(deck.slides), "slides; script:", sum(s["seconds"] for s in STORY), "seconds")


if __name__ == "__main__":
    main()
