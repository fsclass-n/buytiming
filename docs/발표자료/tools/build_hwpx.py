"""기존 HWPX의 서식·표 구조를 재사용해 단계별 산출물과 진행일지를 개정한다."""
import copy
import io
import itertools
import math
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from artifact_content import ARTIFACTS, BASELINE, COURSE, JOURNALS, NOTICE, PERIODS, SERVICE, TEAM
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
NS = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}
HP = "{" + NS["hp"] + "}"


def baseline(path):
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"279a4ce:{relative}"], cwd=ROOT)


def content(node):
    return " ".join(node.xpath(".//hp:t/text()", namespaces=NS))


def paragraph(value, style=0, title=False):
    p = E.Element(HP + "p", id="0", paraPrIDRef="0", styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
    if title:
        p.set("paraPrIDRef", "2")
    run = E.SubElement(p, HP + "run", charPrIDRef=str(style))
    E.SubElement(run, HP + "t").text = value
    return p


def replace_cell(cell, values):
    sub = cell.find(HP + "subList")
    sample = sub.find(HP + "p")
    char_id = sample.find(HP + "run").get("charPrIDRef", "0")
    for p in list(sub):
        if p.tag == HP + "p":
            sub.remove(p)
    for value in values if isinstance(values, list) else [values]:
        p = paragraph(value, char_id)
        p.set("paraPrIDRef", sample.get("paraPrIDRef", "0"))
        sub.append(p)


def save_package(source, target, section, title):
    text = "\n".join(section.xpath("//hp:t/text()", namespaces=NS))
    with ZipFile(io.BytesIO(source)) as old, ZipFile(target, "w") as new:
        for item in old.infolist():
            data = old.read(item.filename)
            if item.filename == "Contents/section0.xml":
                data = E.tostring(section, encoding="UTF-8", xml_declaration=True, standalone=True)
            elif item.filename == "Preview/PrvText.txt":
                data = text.encode("utf-8")
            elif item.filename in ("docProps/core.xml", "Contents/content.hpf"):
                # 본문 외 메타데이터에도 이전 서비스명·작성자명이 남지 않게 한다.
                raw = data.decode("utf-8")
                raw = raw.replace("BuyTiming", "PickTiming").replace("바이타이밍", "픽타이밍")
                raw = raw.replace("김길동", "김모란").replace("조휘일", "박미금")
                data = raw.encode("utf-8")
            elif item.filename == "Preview/PrvImage.png":
                # 오래된 본문의 썸네일을 남기지 않는다. 한글에서 저장 시 새로 생성된다.
                continue
            new.writestr(item, data, compress_type=item.compress_type if item.filename == "mimetype" else ZIP_DEFLATED)
    with ZipFile(target) as check:
        assert check.testzip() is None
        for name in check.namelist():
            if name.endswith(".xml"):
                E.fromstring(check.read(name))
    return text


class ArtifactWriter:
    def __init__(self, source):
        self.source = source
        with ZipFile(io.BytesIO(source)) as z:
            self.root = E.fromstring(z.read("Contents/section0.xml"))
        self.table_template = copy.deepcopy(self.root.xpath(".//hp:tbl[@colCnt='2']", namespaces=NS)[0])
        self.header_cell = copy.deepcopy(self.table_template.find(HP + "tr").find(HP + "tc"))
        self.body_cell = copy.deepcopy(self.table_template.findall(HP + "tr")[-1].findall(HP + "tc")[-1])
        self.ids = itertools.count(2000)
        # 원본의 용지·여백·단 설정을 보존한다.
        first = E.Element(HP + "p", id="0", paraPrIDRef="0", styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
        run = E.SubElement(first, HP + "run", charPrIDRef="0")
        for child in self.root[0].find(HP + "run"):
            if child.tag in (HP + "secPr", HP + "ctrl"):
                run.append(copy.deepcopy(child))
        for child in list(self.root):
            self.root.remove(child)
        self.root.append(first)

    def add_text(self, value, style=0):
        self.root.append(paragraph(value, style, title=style in (2, 3)))

    def add_table(self, rows):
        # 아주 긴 표는 쪽을 넘길 때 마지막 행이 잘릴 수 있어 머리행을 반복한 표로 나눈다.
        if len(rows) > 22:
            for start in range(1, len(rows), 16):
                self.add_table([rows[0], *rows[start:start + 16]])
            return
        table = copy.deepcopy(self.table_template)
        for tr in list(table.findall(HP + "tr")):
            table.remove(tr)
        columns = len(rows[0])
        table.set("id", str(next(self.ids)))
        table.set("rowCnt", str(len(rows)))
        table.set("colCnt", str(columns))
        table.set("repeatHeader", "1")
        width = int(table.find(HP + "sz").get("width"))
        # 열 너비는 내용 길이에 비례시키되 짧은 열도 읽을 수 있는 최소 폭을 둔다.
        weights = [min(max(len(str(r[j])) for r in rows), 48) + 6 for j in range(columns)]
        widths = [round(width * w / sum(weights)) for w in weights]
        widths[-1] = width - sum(widths[:-1])
        total_height = 0
        for row_number, values in enumerate(rows):
            tr = E.SubElement(table, HP + "tr")
            lines = max(math.ceil(len(str(value)) * 700 / max(1, widths[j] - 1000)) for j, value in enumerate(values))
            height = max(2300, lines * 1500 + 800)
            total_height += height
            for j, value in enumerate(values):
                cell = copy.deepcopy(self.header_cell if row_number == 0 else self.body_cell)
                cell.set("header", "1" if row_number == 0 else "0")
                cell.find(HP + "cellAddr").set("colAddr", str(j))
                cell.find(HP + "cellAddr").set("rowAddr", str(row_number))
                cell.find(HP + "cellSpan").set("colSpan", "1")
                cell.find(HP + "cellSpan").set("rowSpan", "1")
                cell.find(HP + "cellSz").set("width", str(widths[j]))
                cell.find(HP + "cellSz").set("height", str(height))
                replace_cell(cell, str(value))
                tr.append(cell)
        table.find(HP + "sz").set("height", str(total_height))
        p = paragraph("")
        run = p.find(HP + "run")
        run.remove(run.find(HP + "t"))
        run.append(table)
        self.root.append(p)
        self.add_text("")


def md_table(rows):
    return ["| " + " | ".join(str(c).replace("\n", " ") for c in row) + " |"
            for row in [rows[0], ["---"] * len(rows[0]), *rows[1:]]] + [""]


def write_artifact(index):
    short, label, period, hours = PERIODS[index]
    target = DOCS / "산출물" / f"{index + 1:02d}_{short}_산출물.hwpx"
    doc = ARTIFACTS[index]
    writer = ArtifactWriter(baseline(target))
    header = [["항목", "내용"], ["과정명", COURSE], ["프로젝트", SERVICE], ["조", TEAM],
              ["단계 / 기간", f"{label} / {period} ({hours}, 원본 계획)"], ["개정 기준", BASELINE]]
    writer.add_text(f"{label} 단계 산출물", 2)
    writer.add_table(header)
    writer.add_text(NOTICE)
    writer.add_text("수록 산출물", 3)
    writer.add_table(doc["toc"]["table"])
    md = [f"# {label} 단계 산출물", "", *md_table(header), NOTICE, "", "## 수록 산출물", "", *md_table(doc["toc"]["table"])]
    for section in doc["sections"]:
        writer.add_text(section["title"], 2)
        md += [f"## {section['title']}", ""]
        for block in section["blocks"]:
            if isinstance(block, str):
                writer.add_text(block)
                md += [block, ""]
            elif "h" in block:
                writer.add_text(block["h"], 3)
                md += [f"### {block['h']}", ""]
            elif "bullets" in block:
                for item in block["bullets"]:
                    writer.add_text("• " + item)
                md += [f"- {item}" for item in block["bullets"]] + [""]
            elif "note" in block:
                for part in block["note"].split("\n"):
                    writer.add_text(part, 4)
                md += ["> " + part for part in block["note"].split("\n")] + [""]
            else:
                writer.add_table(block["table"])
                md += md_table(block["table"])
    save_package(writer.source, target, writer.root, label)
    target.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print(target.name)


def write_journal(index):
    short, label, period, _ = PERIODS[index]
    target = DOCS / f"프로젝트_진행일지_{index + 1}단계_{short}.hwpx"
    source = baseline(target)
    with ZipFile(io.BytesIO(source)) as z:
        root = E.fromstring(z.read("Contents/section0.xml"))
    table = root.xpath(".//hp:tbl", namespaces=NS)[-1]
    for tr in table.findall(HP + "tr"):
        cells = tr.findall(HP + "tc")
        key = content(cells[0]).strip()
        if key.startswith(f"{index + 1} 단계"):
            replace_cell(cells[-1], content(cells[-1]) + " (원본 계획)")
        elif key == "3 조":
            replace_cell(cells[-1], SERVICE)
        elif key == "팀원":
            replace_cell(cells[-1], "박미금(조장), 김모란, 이오리, 홍기흥")
        elif key in JOURNALS[index]:
            replace_cell(cells[-1], JOURNALS[index][key])
        elif key == "마감회의":
            old = content(cells[-1])
            date = old.split("/ 참석:")[0].removeprefix("일시: ")
            replace_cell(cells[-1], [f"원본 계획: {date}", "실제 개최·참석자·회의록 확인 필요. 완료 기록으로 간주하지 않음."])
        elif key == "보 고 자":
            replace_cell(cells[-1], "박미금 (서명)")
    for t in root.xpath("//hp:t", namespaces=NS):
        if t.text:
            t.text = t.text.replace("발표 시간(15분)", "발표 시간(10분: PPT 3분·시연 7분)").replace("김길동", "김모란")
    # 변경 문구를 기준으로 한글이 줄 위치를 다시 계산하도록 기존 캐시를 제거한다.
    for cached in root.xpath("//hp:linesegarray", namespaces=NS):
        cached.getparent().remove(cached)
    save_package(source, target, root, label)
    print(target.name)


def main():
    for index in range(5):
        write_artifact(index)
        write_journal(index)


if __name__ == "__main__":
    main()
