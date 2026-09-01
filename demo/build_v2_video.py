"""Assemble the verified VoiceBank narration with public Canopy capture frames."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "demo" / "v2-captures"
RENDER_DIR = ROOT / "demo" / "v2-renders"
OUTPUT_DIR = ROOT / "demo" / "v2-output"
TIMING_PATH = ROOT / "demo" / "v2-timing.json"
CAPTIONS_PATH = ROOT / "demo" / "v2-captions.srt"
FILTER_PATH = ROOT / "demo" / "v2-video-filter.txt"
OUTPUT_PATH = OUTPUT_DIR / "canopy-upgraded-devpost-demo.mp4"
THUMBNAIL_PATH = OUTPUT_DIR / "canopy-upgraded-thumbnail.jpg"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required")
    timing = json.loads(TIMING_PATH.read_text(encoding="utf-8"))
    beats = timing["beats"]
    pause = float(timing["pause_seconds"])

    beat_slots = [float(item["duration"]) + (pause if index < len(beats) - 1 else 0.0) for index, item in enumerate(beats)]
    shots: list[tuple[str, float]] = [
        ("01-physics-constellation.png", beat_slots[0]),
        ("09-transfer-stage.png", beat_slots[1]),
        ("02-romanian-physics.png", beat_slots[2] / 2),
        ("03-arabic-rtl.png", beat_slots[2] / 2),
        ("04-inspectable-diagnosis.png", beat_slots[3]),
        ("04-inspectable-diagnosis.png", beat_slots[4]),
        ("05-course-forge.png", beat_slots[5]),
        ("06-honest-evidence.png", beat_slots[6]),
        ("07-learner-toolkit.png", beat_slots[7] / 2),
        ("08-accessibility-contrast.png", beat_slots[7] / 2),
        ("09-transfer-stage.png", beat_slots[8]),
    ]
    for filename, _ in shots:
        if not (CAPTURE_DIR / filename).is_file():
            raise RuntimeError(f"Missing capture: {filename}")

    total_duration = sum(duration for _, duration in shots)
    if total_duration >= 119:
        raise RuntimeError(f"Video timeline is {total_duration:.3f}s; must remain below two minutes")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filters: list[str] = []
    for index, (_, duration) in enumerate(shots):
        x_motion = "+18*sin(t/4)" if index % 2 == 0 else "-18*sin(t/4)"
        y_motion = "+10*cos(t/5)" if index % 3 == 0 else "-10*cos(t/5)"
        filters.append(
            f"[{index}:v]scale=1980:1114:force_original_aspect_ratio=increase,"
            f"crop=1920:1080:x='(iw-ow)/2{x_motion}':y='(ih-oh)/2{y_motion}',"
            f"fps=30,trim=duration={duration:.3f},setpts=PTS-STARTPTS[v{index}]"
        )
    concat_inputs = "".join(f"[v{index}]" for index in range(len(shots)))
    caption_file = str(CAPTIONS_PATH.relative_to(ROOT)).replace("'", "\\'")
    filters.append(
        f"{concat_inputs}concat=n={len(shots)}:v=1:a=0,setsar=1,"
        f"fade=t=in:st=0:d=0.35,fade=t=out:st={max(0.0, total_duration - 0.35):.3f}:d=0.35,"
        f"subtitles='{caption_file}':force_style='FontName=Helvetica,FontSize=17,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H70101A21,BackColour=&H70101A21,"
        "BorderStyle=3,Outline=1,Shadow=0,MarginV=36,Alignment=2'[video]"
    )
    FILTER_PATH.write_text(";\n".join(filters) + "\n", encoding="utf-8")

    command = [ffmpeg, "-y"]
    for filename, duration in shots:
        command.extend(["-loop", "1", "-framerate", "30", "-t", f"{duration:.3f}", "-i", str(CAPTURE_DIR / filename)])
    command.extend(
        [
            "-i",
            str(RENDER_DIR / "canopy-v2-narration.wav"),
            "-filter_complex_script",
            str(FILTER_PATH),
            "-map",
            "[video]",
            "-map",
            f"{len(shots)}:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-t",
            f"{total_duration:.3f}",
            "-movflags",
            "+faststart",
            str(OUTPUT_PATH),
        ]
    )
    run(command)
    run(
        [
            ffmpeg,
            "-y",
            "-ss",
            "3",
            "-i",
            str(OUTPUT_PATH),
            "-frames:v",
            "1",
            "-update",
            "1",
            "-q:v",
            "2",
            str(THUMBNAIL_PATH),
        ]
    )
    print(f"video={OUTPUT_PATH}")
    print(f"thumbnail={THUMBNAIL_PATH}")
    print(f"duration={total_duration:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
