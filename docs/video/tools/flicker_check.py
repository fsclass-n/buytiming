"""영상의 깜박임을 측정한다: 프레임별 평균 밝기(YAVG) 급변과 프레임 시간 간격 이상을 찾는다."""
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
video = Path(sys.argv[1])
cmd = [FF, "-hide_banner", "-i", str(video), "-vf", "scale=320:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-an", "-f", "null", "-"]
out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
times = [float(t) for t in re.findall(r"pts_time:([\d.]+)", out)]
ys = [float(y) for y in re.findall(r"YAVG=([\d.]+)", out)]
n = min(len(times), len(ys))
times, ys = times[:n], ys[:n]
gaps = [b - a for a, b in zip(times, times[1:], strict=False)]
print(f"frames {n}, duration {times[-1]:.1f}s, gap min {min(gaps):.4f} max {max(gaps):.4f}")
# 깜박임: 짧은 시간 안에 밝기가 크게 오르내리는 패턴(위·아래로 4 이상 연속 변화)
events = []
for i in range(1, n - 1):
    up, down = ys[i] - ys[i - 1], ys[i + 1] - ys[i]
    if abs(up) > 4 and abs(down) > 4 and (up > 0) != (down > 0):
        events.append((times[i], ys[i - 1], ys[i], ys[i + 1]))
jumps = [(times[i], ys[i - 1], ys[i]) for i in range(1, n) if abs(ys[i] - ys[i - 1]) > 12]
print("one-frame spikes (flash):", len(events))
for e in events[:40]:
    print(f"  {e[0]:7.2f}s  {e[1]:.1f} -> {e[2]:.1f} -> {e[3]:.1f}")
print("large jumps (>12):", len(jumps))
for j in jumps[:40]:
    print(f"  {j[0]:7.2f}s  {j[1]:.1f} -> {j[2]:.1f}")
