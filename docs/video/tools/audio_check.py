"""완성 영상의 음성 트랙을 검사한다: 내레이션 장면마다 실제로 소리가 들리는지(평균 음량) 확인한다."""
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
from video_scenes import timeline

FF = imageio_ffmpeg.get_ffmpeg_exe()
final = Path(__file__).resolve().parents[1] / "3조_final.mp4"
head = subprocess.run([FF, "-i", str(final)], capture_output=True, text=True).stderr
print("\n".join(ln.strip() for ln in head.splitlines() if "Audio:" in ln))
silent = []
for s in timeline():
    if not s["say"]:
        continue
    out = subprocess.run([FF, "-hide_banner", "-ss", f"{s['start'] + .5:.2f}", "-t", f"{min(6, s['dur'] - 1):.2f}", "-i", str(final),
                          "-vn", "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    mean = float(re.search(r"mean_volume: (-?[\d.]+)", out).group(1))
    if mean < -35:
        silent.append((s["id"], mean))
print("voiced scenes checked:", sum(1 for s in timeline() if s["say"]), "| silent:", silent or "none")
