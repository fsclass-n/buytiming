"""장면별 내레이션을 사람이 말하듯 만든다.

- 자연스러운 남성 신경망 음성(ko-KR-HyunsuMultilingualNeural), 조금 차분한 속도·낮은 톤
- 문장마다 따로 합성하고 문장 사이에 숨 고르는 쉼(0.35초)을 넣는다
- 목소리 보정: 저역 잡음 제거, 부드러운 압축, 존재감 대역 보강
- 장면 시간을 넘으면 속도를 조금씩 올려 다시 만든다
"""
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from video_scenes import timeline

WORK = Path(next((a for a in sys.argv[1:] if not a.startswith("--")), "C:/Users/pc06-00/AppData/Local/Temp/pt-video"))
VOICE, PITCH, PAUSE = "ko-KR-HyunsuMultilingualNeural", "-2Hz", .35
RATES = ["-6%", "-3%", "+0%", "+4%", "+8%"]
FF = imageio_ffmpeg.get_ffmpeg_exe()
VOICE_FX = "highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,equalizer=f=3000:t=q:w=1.2:g=2.5,equalizer=f=200:t=q:w=1:g=1.5"


def duration(path):
    out = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = out.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


async def synth(sid, text, rate):
    parts = [p.strip() for p in re.split(r"(?<=[.?!])\s+", text) if p.strip()]
    files = []
    for i, p in enumerate(parts):
        f = WORK / "tts" / "parts" / f"{sid}_{i}.mp3"
        await edge_tts.Communicate(p, VOICE, rate=rate, pitch=PITCH).save(str(f))
        files.append(f)
    # 문장 사이 쉼을 넣어 이어 붙이고 목소리를 보정한다(48kHz 스테레오).
    inputs, chain = [], []
    for i, f in enumerate(files):
        inputs += ["-i", str(f)]
        chain.append(f"[{i}:a]aresample=48000,apad=pad_dur={PAUSE if i < len(files) - 1 else 0}[s{i}]")
    graph = ";".join(chain) + ";" + "".join(f"[s{i}]" for i in range(len(files))) + f"concat=n={len(files)}:v=0:a=1,{VOICE_FX}[out]"
    out = WORK / "tts" / f"{sid}.wav"
    subprocess.run([FF, "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[out]", "-ac", "2", str(out)], check=True)
    return out


async def main():
    (WORK / "tts" / "parts").mkdir(parents=True, exist_ok=True)
    report = []
    for s in timeline():
        if not s["say"]:
            continue
        for rate in RATES:
            out = await synth(s["id"], s["say"], rate)
            d = duration(out)
            if d <= s["dur"] - .6:
                break
        report.append({"id": s["id"], "budget": s["dur"], "speech": round(d, 2), "rate": rate, "ok": d <= s["dur"] - .6})
        print(s["id"], s["dur"], round(d, 2), rate)
    (WORK / "tts.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = [r for r in report if not r["ok"]]
    print("over budget:", bad)
    print("speech total", round(sum(r["speech"] for r in report), 1), "s /", len(report), "clips")


asyncio.run(main())
