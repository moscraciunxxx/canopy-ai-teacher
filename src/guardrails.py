"""Source, safety, and answer-reveal guardrails for tutor responses."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .schemas import Citation, RetrievedChunk


_INJECTION_PATTERNS = (
    r"ignore\s+(?:all\s+)?previous instructions",
    r"reveal\s+(?:the\s+)?system prompt",
    r"(?:api|secret|access)\s*key",
    r"password",
)


def clamp_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    if not math.isfinite(score):
        score = 0.0
    return min(1.0, max(0.0, score))


def detect_safety_flags(text: str, max_chars: int | None = None) -> list[str]:
    """Return stable, non-sensitive flags for input-level safety conditions."""

    value = text if isinstance(text, str) else str(text)
    flags: list[str] = []
    if max_chars is not None and len(value) > max_chars:
        flags.append("input_too_long")
    lowered = value.lower()
    if any(re.search(pattern, lowered) for pattern in _INJECTION_PATTERNS):
        flags.append("prompt_injection")
    return flags


def _chunk_mapping(chunk: RetrievedChunk | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(chunk, RetrievedChunk):
        return chunk.to_dict()
    return chunk


def _chunk_id(chunk: RetrievedChunk | Mapping[str, Any]) -> str:
    data = _chunk_mapping(chunk)
    return str(data.get("chunk_id", data.get("id", "")))


def _quote_from_chunk(chunk: RetrievedChunk | Mapping[str, Any], requested: str = "") -> str:
    data = _chunk_mapping(chunk)
    text = str(data.get("text", "")).strip()
    quote = requested.strip()
    if quote and text and quote in text:
        return quote[:320]
    return text[:320]


def citation_for_chunk(chunk: RetrievedChunk | Mapping[str, Any]) -> dict[str, Any]:
    """Build a citation whose fields are copied only from a retrieved chunk."""

    data = _chunk_mapping(chunk)
    return {
        "chunk_id": _chunk_id(chunk),
        "source": str(data.get("source", "lesson")),
        "heading": str(data.get("heading", "")),
        "quote": _quote_from_chunk(chunk),
    }


def validate_citations(
    citations: Sequence[Citation | Mapping[str, Any]] | None,
    retrieved_chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
    max_items: int = 4,
) -> list[dict[str, Any]]:
    """Keep only citations that refer to retrieved chunks.

    Invalid IDs, malformed values, and hallucinated quotes are dropped or
    replaced with the actual source text.  The returned dictionaries contain
    only JSON-friendly scalar/list values.
    """

    source_by_id = {_chunk_id(chunk): chunk for chunk in retrieved_chunks if _chunk_id(chunk)}
    if not source_by_id:
        return []
    try:
        limit = max(0, int(max_items))
    except (TypeError, ValueError):
        limit = 4
    if limit == 0 or not citations:
        return []

    valid: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in citations:
        if len(valid) >= limit:
            break
        if isinstance(raw, Citation):
            data: Mapping[str, Any] = raw.to_dict()
        elif isinstance(raw, Mapping):
            data = raw
        else:
            continue
        chunk_id = str(data.get("chunk_id", data.get("id", "")))
        if chunk_id not in source_by_id or chunk_id in seen:
            continue
        source_chunk = source_by_id[chunk_id]
        source_data = _chunk_mapping(source_chunk)
        valid.append(
            {
                "chunk_id": chunk_id,
                "source": str(source_data.get("source", "lesson")),
                "heading": str(source_data.get("heading", "")),
                "quote": _quote_from_chunk(source_chunk, str(data.get("quote", ""))),
            }
        )
        seen.add(chunk_id)
    return valid


def _format_number(value: float | int | None) -> str | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.12g}"


def _contains_answer(text: str, expected_value: float | None) -> bool:
    formatted = _format_number(expected_value)
    if not formatted or not isinstance(text, str):
        return False
    escaped = re.escape(formatted)
    # A standalone expected value is conservative: mentioning the coefficient
    # in a level-one clue is less important than never handing over the answer.
    return bool(
        re.search(rf"\bx\s*(?:is|=|equals)\s*{escaped}\b", text, re.IGNORECASE)
        or re.search(rf"\b(?:answer|solution|value)\s*(?:is|=|equals)\s*{escaped}\b", text, re.IGNORECASE)
        or re.search(rf"(?<![\w.]){escaped}(?![\w.])", text)
    )


def enforce_no_final_answer(
    hint: str,
    expected_value: float | None,
    hint_level: int = 1,
) -> str:
    """Guarantee that level-one (low-level) hints do not reveal the answer."""

    value = hint if isinstance(hint, str) else str(hint)
    try:
        level = int(hint_level)
    except (TypeError, ValueError):
        level = 1
    if level <= 1 and _contains_answer(value, expected_value):
        return "What inverse operation would help you undo the operation closest to x? Apply it to both sides."
    return value.strip()


# Descriptive aliases for callers that use different terminology.
sanitize_hint = enforce_no_final_answer
enforce_no_answer_in_hint = enforce_no_final_answer


def normalize_flags(flags: Sequence[Any] | None) -> list[str]:
    """Normalize and de-duplicate safety flags for JSON output."""

    result: list[str] = []
    seen: set[str] = set()
    if flags:
        for flag in flags:
            value = str(flag).strip()
            if value and value not in seen:
                result.append(value)
                seen.add(value)
    return result
