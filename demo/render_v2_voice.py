"""Render the upgraded Canopy demo with Vitalie's approved VoiceBank pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf

from synth import heard_text, synthesize


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "demo" / "v2-vo_script.txt"
OUT_DIR = ROOT / "demo" / "v2-renders"
CAPTIONS_PATH = ROOT / "demo" / "v2-captions.srt"
TIMING_PATH = ROOT / "demo" / "v2-timing.json"
NARRATION_PATH = OUT_DIR / "canopy-v2-narration.wav"
PAUSE_SECONDS = 0.24
TARGET_SAMPLE_RATE = 48_000


def srt_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{milliseconds:03}"


def normalized_words(text: str) -> set[str]:
    return {
        re.sub(r"[^a-z0-9]", "", token.lower())
        for token in re.findall(r"[A-Za-z0-9'-]+", text)
        if len(re.sub(r"[^a-z0-9]", "", token.lower())) >= 5
    }


def main() -> int:
    lines = [line.strip() for line in SCRIPT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 9:
        raise RuntimeError(f"Expected nine picture-first narration beats, found {len(lines)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timeline: list[dict[str, object]] = []
    chunks: list[np.ndarray] = []
    cursor = 0.0
    captions: list[str] = []
    caption_index = 1

    for index, line in enumerate(lines, start=1):
        destination = OUT_DIR / f"beat-{index:02}.wav"
        report_path = destination.with_suffix(".json")
        cached_report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else None
        if destination.is_file() and cached_report and cached_report.get("text") == line:
            report = cached_report
        else:
            report = synthesize(line, destination, verify=True, apply_adapter=True, listen_voice=True)
        audio, sample_rate = sf.read(destination, dtype="float32")
        if sample_rate != TARGET_SAMPLE_RATE:
            raise RuntimeError(f"Beat {index} rendered at {sample_rate} Hz, expected {TARGET_SAMPLE_RATE}")
        duration = len(audio) / sample_rate
        start = cursor
        end = start + duration
        heard = str(report.get("heard", ""))
        expected = normalized_words(line)
        recognized = normalized_words(heard)
        coverage = len(expected & recognized) / max(1, len(expected))
        timeline.append(
            {
                "beat": index,
                "line": line,
                "heard": heard,
                "coverage": round(coverage, 3),
                "duration": round(duration, 3),
                "start": round(start, 3),
                "end": round(end, 3),
                "sample_rate": sample_rate,
                "engine": report.get("engine"),
                "listen_voice": report.get("listen_voice"),
            }
        )
        if coverage < 0.68:
            raise RuntimeError(f"Beat {index} failed Whisper coverage: {coverage:.1%}; heard {heard!r}")
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", line) if part.strip()]
        weights = [max(1, len(re.findall(r"[A-Za-z0-9'-]+", sentence))) for sentence in sentences]
        caption_cursor = start
        for sentence_index, (sentence, weight) in enumerate(zip(sentences, weights, strict=True)):
            if sentence_index == len(sentences) - 1:
                caption_end = end
            else:
                caption_end = caption_cursor + duration * weight / sum(weights)
            captions.append(
                f"{caption_index}\n{srt_time(caption_cursor)} --> {srt_time(caption_end)}\n{sentence}\n"
            )
            caption_index += 1
            caption_cursor = caption_end
        chunks.append(np.asarray(audio, dtype=np.float32))
        if index < len(lines):
            silence = np.zeros(round(PAUSE_SECONDS * sample_rate), dtype=np.float32)
            chunks.append(silence)
            cursor = end + PAUSE_SECONDS
        else:
            cursor = end

    narration = np.concatenate(chunks)
    sf.write(NARRATION_PATH, narration, TARGET_SAMPLE_RATE, subtype="PCM_16")
    final_duration = len(narration) / TARGET_SAMPLE_RATE
    if final_duration >= 119:
        raise RuntimeError(f"Narration is {final_duration:.2f}s; it must stay below two minutes")

    CAPTIONS_PATH.write_text("\n".join(captions), encoding="utf-8")
    final_heard = heard_text(NARRATION_PATH)
    TIMING_PATH.write_text(
        json.dumps(
            {
                "duration": round(final_duration, 3),
                "pause_seconds": PAUSE_SECONDS,
                "narration": str(NARRATION_PATH),
                "final_heard": final_heard,
                "beats": timeline,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(TIMING_PATH)
    print(f"duration={final_duration:.3f}s")
    print(final_heard)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
