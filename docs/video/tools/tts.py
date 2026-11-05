"""장면별 내레이션 음성(남성 한국어 합성 음성)을 만들고 길이를 측정한다."""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from video_scenes import timeline

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Users/pc06-00/AppData/Local/Temp/pt-video")
VOICE, RATE = "ko-KR-InJoonNeural", "+0%"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def duration(path):
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = out.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


async def main():
    (WORK / "tts").mkdir(parents=True, exist_ok=True)
    report = []
    for s in timeline():
        if not s["say"]:
            continue
        path = WORK / "tts" / f"{s['id']}.mp3"
        if not path.exists():
            await edge_tts.Communicate(s["say"], VOICE, rate=RATE).save(str(path))
        d = duration(path)
        report.append({"id": s["id"], "budget": s["dur"], "speech": round(d, 2), "ok": d <= s["dur"] - .6})
    (WORK / "tts.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in report:
        if not r["ok"]:
            print("OVER", r)
    print("speech total", round(sum(r["speech"] for r in report), 1), "s /", len(report), "clips")


asyncio.run(main())
