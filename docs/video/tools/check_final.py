"""완성 영상의 길이·스트림을 확인하고 주요 시점 프레임을 한 장으로 모은다."""
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1]
WORK = Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Users/pc06-00/AppData/Local/Temp/pt-video")
FF = imageio_ffmpeg.get_ffmpeg_exe()
final = OUT / "3조_final.mp4"
info = subprocess.run([FF, "-i", str(final)], capture_output=True, text=True).stderr
print("\n".join(ln.strip() for ln in info.splitlines() if "Duration" in ln or "Stream" in ln))
times = ["00:00:05", "00:00:27", "00:01:25", "00:02:55", "00:03:05", "00:04:00", "00:04:40", "00:05:20",
         "00:06:25", "00:07:05", "00:08:20", "00:08:38", "00:08:52", "00:09:10", "00:09:55"]
tiles = []
for t in times:
    out = WORK / f"final_{t.replace(':', '')}.png"
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", t, "-i", str(final), "-frames:v", "1", str(out)], check=True)
    im = Image.open(out).convert("RGB")
    im.thumbnail((640, 360))
    ImageDraw.Draw(im).text((8, 340), t, fill=(255, 0, 0))
    tiles.append(im)
sheet = Image.new("RGB", (3 * 645, 5 * 365), "white")
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % 3) * 645, (i // 3) * 365))
sheet.save(WORK / "final_frames.png")
print(WORK / "final_frames.png")
