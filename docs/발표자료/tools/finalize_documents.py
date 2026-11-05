"""발표 보조 PDF를 만들고 제출 문서의 내용·링크·영역을 검수한다."""
import json
import re
import tempfile
import unicodedata
from html import escape
from pathlib import Path
from urllib.parse import unquote
from zipfile import ZipFile

import fitz
from fontTools.ttLib import TTFont as SourceFont
from fontTools.varLib.instancer import instantiateVariableFont
from lxml import etree as E
from PIL import Image
from pptx import Presentation
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
WORK = DOCS / "발표자료"
NAVY, CYAN = colors.HexColor("#0B1220"), colors.HexColor("#2563EB")
WIDTH = A4[0] - 84


def fonts():
    source = Path("C:/Windows/Fonts/NotoSansKR-VF.ttf")
    if not source.exists():
        raise FileNotFoundError("Noto Sans KR 글꼴이 필요합니다: " + str(source))
    font_dir = Path(tempfile.mkdtemp(prefix="picktiming-pdf-fonts-"))
    for weight, name in [(400, "NotoKR"), (700, "NotoKRB")]:
        font = instantiateVariableFont(SourceFont(source), {"wght": weight}, inplace=False)
        path = font_dir / f"{name}.ttf"
        font.save(path)
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily("NotoKR", normal="NotoKR", bold="NotoKRB", italic="NotoKR", boldItalic="NotoKRB")


def markup(value):
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = escape(value).replace("`", "")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)


def page_footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(42, 36, A4[0] - 42, 36)
    canvas.setFont("NotoKR", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(42, 23, "PickTiming · 3조 최종 발표")
    canvas.drawRightString(A4[0] - 42, 23, str(doc.page))


def pdf_from_markdown(path):
    body = ParagraphStyle("Korean", fontName="NotoKR", fontSize=10, leading=16,
                          wordWrap="CJK", textColor=NAVY, spaceAfter=7, alignment=TA_LEFT)
    h1 = ParagraphStyle("TitleKR", parent=body, fontName="NotoKRB", fontSize=22, leading=31, spaceAfter=18)
    h2 = ParagraphStyle("HeadingKR", parent=body, fontName="NotoKRB", fontSize=13, leading=20,
                        spaceBefore=13, spaceAfter=8, keepWithNext=True)
    small = ParagraphStyle("TableKR", parent=body, fontSize=8.5, leading=13, spaceAfter=0)
    header = ParagraphStyle("TableHeaderKR", parent=small, fontName="NotoKRB", textColor=colors.white)
    story, group = [], []
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    keep_sections = path.stem == "3분_발표대본"

    def flush():
        if group:
            story.append(KeepTogether(group[:])) if keep_sections else story.extend(group)
            group.clear()

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(markup(line[2:]), h1))
        elif line.startswith("##"):
            flush()
            group.append(Paragraph(markup(line.lstrip("# ")), h2))
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            n = len(rows[0])
            weights = {2: [.28, .72], 3: [.24, .38, .38], 4: [.17, .17, .30, .36],
                       5: [.12, .12, .29, .29, .18]}.get(n, [1 / n] * n)
            data = [[Paragraph(markup(c), header if j == 0 else small) for c in row] for j, row in enumerate(rows)]
            table = Table(data, colWidths=[WIDTH * w for w in weights], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
                ("LINEBELOW", (0, 0), (-1, 0), .6, CYAN),
                ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            group.extend([table, Spacer(1, 8)])
            continue
        else:
            paragraph = line
            if line.startswith("- "):
                paragraph = "• " + line[2:]
            else:
                while i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith(("#", "|", "- ")):
                    i += 1
                    paragraph += " " + lines[i].strip()
            group.append(Paragraph(markup(paragraph), body))
        i += 1
    flush()
    SimpleDocTemplate(str(path.with_suffix(".pdf")), pagesize=A4, leftMargin=42, rightMargin=42,
                      topMargin=40, bottomMargin=52, title=path.stem, author="PickTiming · 3조").build(
                          story, onFirstPage=page_footer, onLaterPages=page_footer)


def normalized(value):
    return re.sub(r"\s|\u00ad|\u200b", "", unicodedata.normalize("NFKC", value))


def render_contact(name="프로젝트_발표자료", output="슬라이드_미리보기.png"):
    source = fitz.open(DOCS / f"pdf/{name}.pdf")
    canvas = Image.new("RGB", (1440, 420 * ((len(source) + 1) // 2)), "#07101e")
    for i, page in enumerate(source):
        pix = page.get_pixmap(matrix=fitz.Matrix(.72, .72))
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        image.thumbnail((700, 394))
        canvas.paste(image, ((i % 2) * 720 + 10, (i // 2) * 420 + 10))
    canvas.save(WORK / output)


def verify():
    report = {"pdfs": [], "broken_links": [], "ppt_shape_overflow": [], "hwpx_missing_text": []}
    for path in sorted(DOCS.rglob("*.pdf")):
        doc = fitz.open(path)
        outside = []
        for i, page in enumerate(doc):
            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    x0, y0, x1, y1 = line["bbox"]
                    if x0 < -1 or y0 < -1 or x1 > page.rect.width + 1 or y1 > page.rect.height + 1:
                        outside.append(i + 1)
        report["pdfs"].append({"file": path.relative_to(DOCS).as_posix(), "pages": len(doc),
                               "out_of_page_text": sorted(set(outside)),
                               "empty_pages": [i + 1 for i, p in enumerate(doc) if len(p.get_text().strip()) < 10]})
    deck = Presentation(DOCS / "프로젝트_발표자료.pptx")
    for i, slide in enumerate(deck.slides, 1):
        for shape in slide.shapes:
            if shape.left < 0 or shape.top < 0 or shape.left + shape.width > deck.slide_width + 100 \
                    or shape.top + shape.height > deck.slide_height + 100:
                report["ppt_shape_overflow"].append({"slide": i, "shape": shape.name})
    report["ppt_slides"] = len(deck.slides)
    report["ppt_notes_complete"] = all("예상 질문" in sl.notes_slide.notes_text_frame.text for sl in deck.slides)
    report["pdf_pages_match_slides"] = len(fitz.open(DOCS / "pdf/프로젝트_발표자료.pdf")) == len(deck.slides)
    for path in DOCS.rglob("*.md"):
        # 코드 블록 안의 예시(README 템플릿 등)는 다른 위치 기준 경로이므로 검사하지 않는다.
        body = re.sub(r"(?ms)^(`{3,}).*?^\1", "", path.read_text(encoding="utf-8"))
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
            if re.match(r"^[a-z]+:|^#", link):
                continue
            target = path.parent / unquote(link.split("#")[0])
            if not target.exists():
                report["broken_links"].append({"file": path.relative_to(DOCS).as_posix(), "target": link})
    for path in DOCS.rglob("*.hwpx"):
        pdf = DOCS / "pdf" / path.relative_to(DOCS).with_suffix(".pdf")
        with fitz.open(pdf) as doc:
            text = normalized("".join(page.get_text() for page in doc))
        with ZipFile(path) as z:
            assert z.testzip() is None
            root = E.fromstring(z.read("Contents/section0.xml"))
            for p in root.xpath('//*[local-name()="p"]'):
                if p.xpath('.//*[local-name()="tbl"]'):
                    continue
                value = "".join(p.xpath('.//*[local-name()="t"]/text()'))
                if len(value) > 3 and normalized(value) not in text:
                    report["hwpx_missing_text"].append({"file": path.name, "text": value})
    (WORK / "document-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    fonts()
    for name in ["3분_발표대본", "7분_시연시나리오", "수정사항_보고서"]:
        pdf_from_markdown(WORK / f"{name}.md")
    render_contact()
    report = verify()
    print(json.dumps({k: v for k, v in report.items() if k != "pdfs"}, ensure_ascii=False, indent=2))
    print("PDFs:", len(report["pdfs"]), "pages:", sum(p["pages"] for p in report["pdfs"]))
    assert not report["broken_links"], "문서 링크를 확인하세요."
    assert not report["ppt_shape_overflow"], "슬라이드 도형 영역을 확인하세요."
    assert not report["hwpx_missing_text"], "HWPX와 PDF의 내용 일치를 확인하세요."
    assert report["ppt_notes_complete"], "발표자 노트(설명 포인트·예상 질문)를 확인하세요."
    assert report["pdf_pages_match_slides"], "PPT와 PDF의 장 수를 확인하세요."
    assert all(not p["out_of_page_text"] and not p["empty_pages"] for p in report["pdfs"]), "PDF 페이지를 확인하세요."


if __name__ == "__main__":
    main()
