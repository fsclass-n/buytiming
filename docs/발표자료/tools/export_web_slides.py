"""현재 PPTX를 웹 발표용 WebP와 목록으로 내보낸다.

저장소 루트에서: python docs/발표자료/tools/export_web_slides.py
필요 도구: Windows PowerPoint, pywin32, python-pptx, Pillow.
원본은 읽기 전용으로 열며, 웹사이트 실행에는 이 도구가 필요하지 않다.
"""
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from win32com.client import dynamic

ROOT = Path(__file__).resolve().parents[3]
DECK = ROOT / "docs/프로젝트_발표자료.pptx"
DEST = ROOT / "docs/발표자료/slides"


def main():
    source_hash = hashlib.sha256(DECK.read_bytes()).hexdigest()
    deck = Presentation(DECK)
    titles = []
    for index, slide in enumerate(deck.slides):
        text = [shape.text for shape in slide.shapes if shape.has_text_frame and shape.text.strip()]
        title = "PickTiming · 팀 포트폴리오" if index == 0 else "마무리 · 감사합니다" if index == len(deck.slides) - 1 else text[1]
        titles.append(title.replace("\n", " "))
    DEST.mkdir(exist_ok=True)
    entries = []
    app = dynamic.Dispatch("PowerPoint.Application")
    presentation = None
    with tempfile.TemporaryDirectory(prefix="picktiming-web-slides-") as temporary:
        try:
            presentation = app.Presentations.Open(str(DECK), True, False, False)
            for number in range(1, presentation.Slides.Count + 1):
                png = Path(temporary) / f"slide-{number:02d}.png"
                presentation.Slides.Item(number).Export(str(png), "PNG", 1920, 1080)
                filename = f"slide-{number:02d}.webp"
                with Image.open(png) as image:
                    image.convert("RGB").save(DEST / filename, "WEBP", lossless=True, method=6)
                entries.append({"image": filename, "title": titles[number - 1]})
        finally:
            if presentation is not None:
                presentation.Close()
            if app.Presentations.Count == 0:
                app.Quit()
    assert hashlib.sha256(DECK.read_bytes()).hexdigest() == source_hash, "PPTX 원본이 변경되었습니다."
    manifest = {"source": "docs/프로젝트_발표자료.pptx", "sha256": source_hash, "width": 1920, "height": 1080, "slides": entries}
    (DEST / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(entries)} slides; source unchanged: {source_hash}")


if __name__ == "__main__":
    main()
