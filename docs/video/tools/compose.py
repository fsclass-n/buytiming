"""슬라이드·시연 녹화·내레이션·자막을 합쳐 3조_final.mp4, 자막, 하이라이트, 썸네일을 만든다."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from video_scenes import PARTS, timeline

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Users/pc06-00/AppData/Local/Temp/pt-video")
OUT = Path(__file__).resolve().parents[1]
FF = imageio_ffmpeg.get_ffmpeg_exe()
PX = 1920 / 13.333
LEAD = .3  # 장면 시작 후 내레이션 시작까지
BOLD = ["실구매가", "적기 점수", "권한 검사", "데모 데이터", "관리자 전용 화면", "조회만 가능", "숫자", "검증"]
TAGS = {"D01": "데모 데이터로 시연", "D07": "데모: 규칙 기반 / 운영: Gemini", "D11": "역할 기반 차단",
        "D13": "데모 수치 · 성과 아님", "D14": "데모 수치 · 성과 아님", "D15": "서버 권한 검사", "D16": "실제 운영 서버"}


def ff(*args, cwd=None):
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", *map(str, args)], check=True, cwd=cwd)


def speech_len(sid):
    out = subprocess.run([FF, "-i", str(WORK / "tts" / f"{sid}.mp3")], capture_output=True, text=True).stderr
    h, m, s = out.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def slide_clip(s, path):
    boxes = []
    n = len(s["hl"])
    if n:
        a, b = 1.0, s["dur"] - .6
        for i, (x, y, w, h) in enumerate(s["hl"]):
            t1, t2 = a + (b - a) * i / n, a + (b - a) * (i + 1) / n
            boxes.append(f"drawbox=x={x * PX:.0f}:y={y * PX:.0f}:w={w * PX:.0f}:h={h * PX:.0f}:color=0x22D3EE@0.95:t=5:"
                         f"enable='between(t,{t1:.2f},{t2:.2f})'")
    fades = []
    if s["id"] == "P16b":
        fades.append(f"fade=t=out:st={s['dur'] - .5}:d=0.5")
    if s["id"] == "C17":
        fades.append("fade=t=in:st=0:d=0.5")
    if s["id"] == "C18":
        fades.append(f"fade=t=out:st={s['dur'] - 1.5}:d=1.5")
    vf = ",".join(["scale=1920:1080", "fps=30", "format=yuv420p", *boxes, *fades])
    ff("-loop", 1, "-t", s["dur"], "-i", WORK / "slides" / f"slide{s['slide']:02d}.png", "-vf", vf,
       "-c:v", "libx264", "-preset", "medium", "-crf", 16, "-r", 30, path)


def demo_clip(s, video, mark, path):
    fades = ["fade=t=in:st=0:d=0.5"] if s["id"] == "D01" else []
    vf = ",".join(["scale=1920:1080", "fps=30", "format=yuv420p", *fades])
    ff("-ss", f"{mark:.3f}", "-t", s["dur"], "-i", video, "-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", 16, "-r", 30, path)


def chunks(text, limit=36):
    """문장·쉼표 기준으로 자막 단위를 나눈다(한 줄 18자 안팎, 최대 2줄)."""
    parts = [p.strip() for p in re.split(r"(?<=[.?!])\s+|(?<=,)\s+", text) if p.strip()]
    out = []
    for p in parts:
        while len(p) > limit:
            cut = p.rfind(" ", 0, limit)
            cut = cut if cut > 8 else limit
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if out and len(out[-1]) + len(p) + 1 <= limit and not out[-1].endswith((".", "?", "!")):
            out[-1] += " " + p
        else:
            out.append(p)
    return out


def two_lines(text):
    if len(text) <= 18:
        return [text]
    mid = len(text) // 2
    cut = min((i for i, c in enumerate(text) if c == " "), key=lambda i: abs(i - mid), default=mid)
    return [text[:cut].strip(), text[cut:].strip()]


def bold(text, ass):
    for k in BOLD:
        text = text.replace(k, ("{\\b1}" + k + "{\\b0}") if ass else f"<b>{k}</b>")
    return text


def ass_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def srt_time(t):
    m, s = divmod(t, 60)
    return f"00:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def subtitles(scenes):
    cues = []
    for s in scenes:
        if not s["say"]:
            continue
        pieces = chunks(s["say"])
        total = sum(len(p) for p in pieces)
        t = s["start"] + LEAD
        speech = speech_len(s["id"])
        for p in pieces:
            d = speech * len(p) / total
            cues.append((t, t + d - .05, two_lines(p)))
            t += d
    srt = []
    for i, (a, b, lines) in enumerate(cues, 1):
        srt += [str(i), f"{srt_time(a)} --> {srt_time(b)}", *[bold(ln, False) for ln in lines], ""]
    (OUT / "3조_final.srt").write_text("\n".join(srt), encoding="utf-8")
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, \
ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Malgun Gothic,46,&H00FFFFFF,&H00FFFFFF,&H00201B0B,&H9A201B0B,0,0,0,0,100,100,0,0,3,14,0,2,120,120,46,1
Style: LabelSlide,Malgun Gothic,28,&H00FFFFFF,&H00FFFFFF,&H00EB6325,&H00EB6325,1,0,0,0,100,100,0,0,3,10,0,9,40,40,24,1
Style: LabelDemo,Malgun Gothic,28,&H00FFFFFF,&H00FFFFFF,&H00EB6325,&H00EB6325,1,0,0,0,100,100,0,0,3,10,0,1,36,36,36,1
Style: Tag,Malgun Gothic,30,&H00201B0B,&H00201B0B,&H00EED322,&H00EED322,1,0,0,0,100,100,0,0,3,10,0,9,40,40,118,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    # 슬라이드는 비어 있는 오른쪽 위, 시연 화면은 로고·메뉴를 피해 왼쪽 아래에 구간 라벨을 둔다.
    spans = []
    for s in scenes:
        key = (s["part"], s["kind"])
        if spans and spans[-1][0] == key:
            spans[-1][2] = s["start"] + s["dur"]
        else:
            spans.append([key, s["start"], s["start"] + s["dur"]])
    for (part, kind), a, b in spans:
        style = "LabelSlide" if kind == "slide" else "LabelDemo"
        ev.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},{style},,0,0,0,,{PARTS[part]}")
    for s in scenes:
        if s["id"] in TAGS:
            ev.append(f"Dialogue: 1,{ass_time(s['start'] + .5)},{ass_time(s['start'] + s['dur'] - .3)},Tag,,0,0,0,,{TAGS[s['id']]}")
    newline = "\\N"
    for a, b, lines in cues:
        body = bold(newline.join(lines), True)
        ev.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Sub,,0,0,0,,{body}")
    (WORK / "subs.ass").write_text(head + "\n".join(ev) + "\n", encoding="utf-8-sig")
    return len(cues)


def main():
    scenes = timeline()
    info = json.loads((WORK / "demo_marks.json").read_text(encoding="utf-8"))
    clips = WORK / "clips"
    clips.mkdir(exist_ok=True)
    listing = []
    for s in scenes:
        path = clips / f"{s['id']}.mp4"
        if path.exists() and "--rebuild" not in sys.argv:
            pass
        elif s["kind"] == "slide":
            slide_clip(s, path)
        else:
            demo_clip(s, info["video"], info["marks"][s["id"]], path)
        listing.append(f"file '{path.as_posix()}'")
    (WORK / "list.txt").write_text("\n".join(listing), encoding="utf-8")
    ff("-f", "concat", "-safe", 0, "-i", WORK / "list.txt", "-c", "copy", WORK / "video_only.mp4")

    voiced = [s for s in scenes if s["say"]]
    inputs, delays = [], []
    for i, s in enumerate(voiced):
        inputs += ["-i", WORK / "tts" / f"{s['id']}.mp3"]
        ms = int((s["start"] + LEAD) * 1000)
        delays.append(f"[{i}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    mix = ";".join(delays) + ";" + "".join(f"[a{i}]" for i in range(len(voiced))) + \
        f"amix=inputs={len(voiced)}:normalize=0,apad=whole_dur=600,atrim=0:600,loudnorm=I=-16:TP=-1.5:LRA=11[out]"
    ff(*inputs, "-filter_complex", mix, "-map", "[out]", "-ac", 2, "-ar", 48000, "-c:a", "pcm_s16le", WORK / "narration.wav")

    n = subtitles(scenes)
    fonts = WORK / "fonts"
    fonts.mkdir(exist_ok=True)
    for f in ("malgun.ttf", "malgunbd.ttf"):
        shutil.copy(Path("C:/Windows/Fonts") / f, fonts / f)
    vf = "subtitles=subs.ass:fontsdir=fonts"
    common = ["-i", "video_only.mp4", "-i", "narration.wav", "-map", "0:v", "-map", "1:a", "-vf", vf,
              "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-b:v", "1100k", "-r", 30]
    ff(*common, "-pass", 1, "-passlogfile", "pass", "-an", "-f", "mp4", "NUL", cwd=WORK)
    final = OUT / "3조_final.mp4"
    ff(*common, "-pass", 2, "-passlogfile", "pass", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", final, cwd=WORK)
    ff("-ss", "00:04:25", "-t", 60, "-i", final, "-vf", "scale=1280:-2", "-c:v", "libx264", "-preset", "slow", "-b:v", "1000k",
       "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", OUT / "3조_highlight.mp4")
    ff("-ss", "00:04:40", "-i", final, "-frames:v", 1, OUT / "video-thumbnail.png")
    print("subtitle cues", n)
    for f in ("3조_final.mp4", "3조_highlight.mp4", "video-thumbnail.png", "3조_final.srt"):
        print(f, round((OUT / f).stat().st_size / 1024 / 1024, 2), "MB")


if __name__ == "__main__":
    main()
