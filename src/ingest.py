"""Small, dependency-free lesson ingestion helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .config import DEMO_LESSON, DEFAULT_LESSON_PATH, candidate_paths
from .schemas import LessonChunk, LessonDocument


_HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def _source_key(source: str) -> str:
    """Create a stable, readable prefix for generated chunk identifiers."""

    stem = Path(source).stem if source else "lesson"
    key = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower()
    return key or "lesson"


def chunk_markdown(markdown: str, source: str = "lesson") -> list[LessonChunk]:
    """Split markdown into heading-scoped paragraph chunks.

    Headings become metadata for following paragraphs.  Consecutive non-empty
    lines form one paragraph, which keeps lists and short equations together.
    Fenced code is treated as paragraph text so a hash inside code cannot
    accidentally become a heading.
    """

    if not isinstance(markdown, str):
        markdown = str(markdown)

    chunks: list[LessonChunk] = []
    paragraph: list[str] = []
    current_heading = ""
    in_fence = False
    prefix = _source_key(source)

    def flush() -> None:
        if not paragraph:
            return
        text = "\n".join(line.rstrip() for line in paragraph).strip()
        paragraph.clear()
        if not text:
            return
        chunks.append(
            LessonChunk(
                chunk_id=f"{prefix}-{len(chunks) + 1:03d}",
                text=text,
                heading=current_heading,
                source=source,
                order=len(chunks),
            )
        )

    for raw_line in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            in_fence = not in_fence
            paragraph.append(line)
            continue

        heading_match = None if in_fence else _HEADING_RE.match(line)
        if heading_match:
            flush()
            current_heading = heading_match.group(2).strip()
            continue

        if not line.strip():
            flush()
        else:
            paragraph.append(line)
    flush()

    # A document containing only headings is still useful to retrieval and
    # should not silently become an empty lesson.
    if not chunks and current_heading:
        chunks.append(
            LessonChunk(
                chunk_id=f"{prefix}-001",
                text=current_heading,
                heading=current_heading,
                source=source,
                order=0,
            )
        )
    return chunks


def _read_first_available(path: str | Path | None) -> tuple[str, str]:
    """Read an explicit or default path, returning embedded content on failure."""

    if path is not None:
        requested = Path(path)
        candidates: Iterable[Path] = (requested,)
        fallback_source = str(requested)
    else:
        candidates = candidate_paths(DEFAULT_LESSON_PATH)
        fallback_source = str(DEFAULT_LESSON_PATH)

    for candidate in candidates:
        try:
            if candidate.is_file():
                text = candidate.read_text(encoding="utf-8")
                if text.strip():
                    return text, str(candidate)
        except (OSError, UnicodeError):
            continue
    return DEMO_LESSON, f"{fallback_source} (embedded fallback)"


def load_lesson(path: str | Path | None = None) -> LessonDocument:
    """Load and chunk a lesson, gracefully falling back to the demo lesson."""

    text, source = _read_first_available(path)
    chunks = tuple(chunk_markdown(text, source=source))
    if not chunks:
        # The embedded lesson is known to chunk, but keep this guard for a
        # caller that supplies an unusual empty fallback in future.
        chunks = tuple(chunk_markdown(DEMO_LESSON, source=source))
    return LessonDocument(source=source, text=text, chunks=chunks)


def read_lesson(path: str | Path | None = None) -> LessonDocument:
    """Backward-friendly alias for :func:`load_lesson`."""

    return load_lesson(path)


def parse_markdown(markdown: str, source: str = "lesson") -> list[LessonChunk]:
    """Alias that makes the parser convenient to discover in small clients."""

    return chunk_markdown(markdown, source)
