"""Public misconception-aware Socratic tutor service."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_MODE,
    DEFAULT_LESSON_PATH,
    DEFAULT_RUBRIC_PATH,
    DEFAULT_TOP_K,
    MAX_LEARNER_ANSWER_CHARS,
    MAX_QUESTION_CHARS,
    candidate_paths,
)
from .guardrails import (
    citation_for_chunk,
    clamp_score,
    detect_safety_flags,
    enforce_no_final_answer,
    normalize_flags,
    validate_citations,
)
from .ingest import load_lesson
from .provider import DemoProvider, OpenAICompatibleProvider, ProviderError, TutorProvider
from .retrieve import LexicalRetriever
from .rubric import evaluate_answer, load_rubric
from .schemas import (
    ProviderRequest,
    ProviderResult,
    TutorResponse,
)


_KNOWN_STAGES = frozenset({"diagnostic", "guided", "hint", "practice", "review", "synthesis", "mastery"})


def _normalize_stage(stage: str) -> str:
    value = stage if isinstance(stage, str) else str(stage)
    value = value.strip().lower()
    return value[:40] if value else "diagnostic"


def _normalize_hint_level(hint_level: int) -> int:
    try:
        value = int(hint_level)
    except (TypeError, ValueError):
        value = 1
    return min(3, max(0, value))


def _normalize_input(value: Any, max_chars: int) -> tuple[str, list[str]]:
    text = value if isinstance(value, str) else str(value or "")
    flags = detect_safety_flags(text, max_chars=max_chars)
    return text[:max_chars], flags


def _result_from_provider(raw: Any) -> ProviderResult:
    if isinstance(raw, ProviderResult):
        return raw
    if isinstance(raw, Mapping):
        return ProviderResult.from_mapping(raw)
    raise ProviderError("Provider returned an unsupported result type")


class TutorService:
    """Offline-first tutor orchestration service.

    ``lesson_path`` and ``rubric_path`` are optional; absent or unreadable
    paths use the embedded demo assets.  A caller-supplied provider is always
    honored.  In non-demo mode, a failed optional remote provider falls back
    to the deterministic evaluator and marks the response accordingly.
    """

    def __init__(
        self,
        lesson_path: str | Path | None = None,
        rubric_path: str | Path | None = None,
        provider: TutorProvider | Any | None = None,
        mode: str = DEFAULT_MODE,
    ) -> None:
        self.mode = (mode if isinstance(mode, str) else str(mode)).strip().lower() or DEFAULT_MODE
        self.lesson = load_lesson(lesson_path)
        self.rubric = load_rubric(rubric_path)
        self.lesson_path = self._resolved_path(lesson_path, DEFAULT_LESSON_PATH)
        self.rubric_path = self._resolved_path(rubric_path, DEFAULT_RUBRIC_PATH)
        self.retriever = LexicalRetriever(self.lesson.chunks)
        self.top_k = DEFAULT_TOP_K
        if provider is not None:
            self.provider = provider
        elif self.mode in {"demo", "offline", "local"}:
            self.provider = DemoProvider(self.rubric)
        else:
            self.provider = OpenAICompatibleProvider.from_environment()

    @staticmethod
    def _resolved_path(path: str | Path | None, default: Path) -> Path:
        if path is not None:
            return Path(path)
        for candidate in candidate_paths(default):
            if candidate.is_file():
                return candidate
        # This path is intentionally allowed not to exist: the ingestion
        # layer supplies embedded content when a bare checkout has no content/
        # directory, while callers can still inspect the conventional path.
        return next(candidate_paths(default))

    @property
    def lesson_chunks(self) -> tuple[Any, ...]:
        return self.lesson.chunks

    def _call_provider(self, request: ProviderRequest) -> ProviderResult:
        provider = self.provider
        generate = getattr(provider, "generate", None)
        if callable(generate):
            return _result_from_provider(generate(request))

        # Accept small application adapters that expose complete/respond while
        # retaining generate as the documented protocol.
        for method_name in ("complete", "respond", "analyze"):
            method = getattr(provider, method_name, None)
            if not callable(method):
                continue
            try:
                raw = method(request)
            except TypeError:
                raw = method(
                    learner_answer=request.learner_answer,
                    stage=request.stage,
                    question=request.question,
                    hint_level=request.hint_level,
                    context=request.context,
                )
            return _result_from_provider(raw)
        raise ProviderError("Provider must expose generate(request) or a compatible adapter method")

    @staticmethod
    def _fallback_result(request: ProviderRequest) -> ProviderResult:
        evaluation = evaluate_answer(
            request.learner_answer,
            request.rubric or load_rubric(),
            question=request.question,
            stage=request.stage,
            hint_level=request.hint_level,
        )
        return ProviderResult(
            diagnosis=evaluation.diagnosis,
            misconception=evaluation.misconception,
            feedback=evaluation.feedback,
            hint=evaluation.hint,
            next_question=evaluation.next_question,
            mastery_score=evaluation.mastery_score,
            reveal_answer=evaluation.reveal_answer,
            expected_value=evaluation.expected_value,
        )

    def respond(
        self,
        learner_answer: str,
        stage: str = "diagnostic",
        question: str | None = None,
        hint_level: int = 1,
    ) -> dict[str, Any]:
        """Return a JSON-serializable Socratic tutoring response."""

        response_stage = _normalize_stage(stage)
        answer, answer_flags = _normalize_input(learner_answer, MAX_LEARNER_ANSWER_CHARS)
        clean_question: str | None
        question_flags: list[str]
        if question is None:
            clean_question, question_flags = None, []
        else:
            clean_question, question_flags = _normalize_input(question, MAX_QUESTION_CHARS)
        level = _normalize_hint_level(hint_level)

        active_question = clean_question or self.rubric.primary_question
        query = f"{active_question}\n{answer}".strip()
        retrieved = self.retriever.retrieve(query, top_k=self.top_k, min_score=0.01)
        context = tuple(retrieved)
        request = ProviderRequest(
            learner_answer=answer,
            stage=response_stage,
            question=clean_question,
            hint_level=level,
            context=context,
            rubric=self.rubric,
        )

        local_evaluation = evaluate_answer(
            answer,
            self.rubric,
            question=clean_question,
            stage=response_stage,
            hint_level=level,
        )
        provider_flags: list[str] = []
        try:
            result = self._call_provider(request)
        except (ProviderError, OSError, ValueError, TypeError):
            # Provider errors never make demo tutoring unavailable.  The error
            # text is intentionally not sent to the learner.
            result = self._fallback_result(request)
            provider_flags.append("provider_unavailable")

        # Unknown and off-topic states are local safety boundaries.  A remote
        # model cannot turn either into a confident equation judgment.
        if local_evaluation.diagnosis in {"unknown", "off_topic", "scaffold"}:
            result = ProviderResult(
                diagnosis=local_evaluation.diagnosis,
                misconception=local_evaluation.misconception,
                feedback=local_evaluation.feedback,
                hint=local_evaluation.hint,
                next_question=local_evaluation.next_question,
                mastery_score=local_evaluation.mastery_score,
                reveal_answer=False,
                citations=result.citations,
                safety_flags=result.safety_flags,
                expected_value=local_evaluation.expected_value,
            )

        expected_value = result.expected_value
        if expected_value is None:
            expected_value = local_evaluation.expected_value
        hint = enforce_no_final_answer(result.hint, expected_value, hint_level=level)
        reveal_answer = bool(result.reveal_answer) and level >= 3

        # If a final reveal is explicitly requested, make it useful while
        # keeping the low-level path answer-free.
        feedback = result.feedback.strip()
        if reveal_answer and expected_value is not None and "x =" not in feedback.lower():
            formatted = str(int(expected_value)) if float(expected_value).is_integer() else f"{expected_value:.12g}"
            feedback = f"{feedback} The checked solution is x = {formatted}."

        citations = validate_citations(result.citations, context)
        if not citations and context:
            # Demo responses should be source-grounded even if a custom/API
            # provider omitted citations.  Every generated citation is valid.
            citations = [citation_for_chunk(chunk) for chunk in context[:2]]

        flags = normalize_flags(
            [
                *answer_flags,
                *question_flags,
                *provider_flags,
                *result.safety_flags,
                *( ["unknown_request"] if result.diagnosis == "unknown" else [] ),
                *( ["off_topic"] if result.diagnosis == "off_topic" else [] ),
            ]
        )
        response = TutorResponse(
            stage=response_stage,
            diagnosis=str(result.diagnosis or local_evaluation.diagnosis),
            misconception=str(result.misconception or ""),
            feedback=feedback,
            hint=hint,
            next_question=str(result.next_question or "What would you try next?"),
            mastery_score=clamp_score(result.mastery_score),
            reveal_answer=reveal_answer,
            citations=tuple(citations),
            retrieved_chunks=tuple(chunk.to_dict() for chunk in context),
            safety_flags=tuple(flags),
        )
        return response.to_dict()


__all__ = ["TutorService"]
