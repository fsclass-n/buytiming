"""녹화본에서 장면별 프레임을 뽑아 한 장의 확인용 이미지로 만든다."""
import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Users/pc06-00/AppData/Local/Temp/pt-video")
FF = imageio_ffmpeg.get_ffmpeg_exe()
info = json.loads((WORK / "demo_marks.json").read_text(encoding="utf-8"))
from video_scenes import timeline  # noqa: E402

dur = {s["id"]: s["dur"] for s in timeline()}
tiles = []
for sid, start in info["marks"].items():
    for frac in (.35, .85):
        out = WORK / f"frame_{sid}_{int(frac * 100)}.png"
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{start + dur[sid] * frac:.2f}", "-i", info["video"], "-frames:v", "1", str(out)], check=True)
        im = Image.open(out).convert("RGB")
        im.thumbnail((480, 270))
        ImageDraw.Draw(im).text((8, 8), f"{sid} {int(frac * 100)}%", fill=(255, 0, 0))
        tiles.append(im)
cols = 4
sheet = Image.new("RGB", (cols * 485, ((len(tiles) + cols - 1) // cols) * 275), "white")
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % cols) * 485, (i // cols) * 275))
sheet.save(WORK / "frames.png")
print(WORK / "frames.png", sheet.size)
