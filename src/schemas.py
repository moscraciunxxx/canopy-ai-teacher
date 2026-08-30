"""Typed, JSON-friendly data contracts used by the tutor core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence, TypeAlias


JSONScalar: TypeAlias = None | bool | int | float | str
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


@dataclass(frozen=True)
class LessonChunk:
    """A small source-grounded unit produced by the markdown ingester."""

    chunk_id: str
    text: str
    heading: str = ""
    source: str = "lesson"
    order: int = 0

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "heading": self.heading,
            "section": self.heading,
            "source": self.source,
            "order": self.order,
        }

    def __getitem__(self, key: str) -> JSONValue:
        """Allow lightweight mapping-style use alongside the typed object."""

        return self.to_dict()[key]


@dataclass(frozen=True)
class LessonDocument:
    """An ingested lesson and the source label used for citations."""

    source: str
    text: str
    chunks: tuple[LessonChunk, ...]


@dataclass(frozen=True)
class RetrievedChunk:
    """A lesson chunk with a deterministic lexical relevance score."""

    chunk_id: str
    text: str
    heading: str
    source: str
    score: float
    matched_terms: tuple[str, ...] = ()
    order: int = 0

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "heading": self.heading,
            "section": self.heading,
            "source": self.source,
            "score": float(self.score),
            "matched_terms": list(self.matched_terms),
            "order": self.order,
        }

    def __getitem__(self, key: str) -> JSONValue:
        """Allow callers to consume retrieval results as JSON-like mappings."""

        return self.to_dict()[key]


@dataclass(frozen=True)
class Citation:
    """A citation that must point at one of the retrieved lesson chunks."""

    chunk_id: str
    source: str = "lesson"
    heading: str = ""
    quote: str = ""

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "heading": self.heading,
            "quote": self.quote,
        }


@dataclass(frozen=True)
class RubricCriterion:
    criterion_id: str
    description: str
    weight: float = 1.0


@dataclass(frozen=True)
class MisconceptionRule:
    rule_id: str
    label: str
    patterns: tuple[str, ...] = ()
    feedback: str = ""
    hint: str = ""
    next_question: str = ""


@dataclass(frozen=True)
class Rubric:
    """Normalized rubric information needed by a provider or evaluator."""

    title: str
    primary_question: str
    equation: str
    expected_answer: str
    expected_value: float | None
    concept: str
    criteria: tuple[RubricCriterion, ...] = ()
    misconceptions: tuple[MisconceptionRule, ...] = ()

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "title": self.title,
            "primary_question": self.primary_question,
            "equation": self.equation,
            "expected_answer": self.expected_answer,
            "expected_value": self.expected_value,
            "concept": self.concept,
            "criteria": [
                {
                    "id": criterion.criterion_id,
                    "description": criterion.description,
                    "weight": criterion.weight,
                }
                for criterion in self.criteria
            ],
            "misconceptions": [
                {
                    "id": rule.rule_id,
                    "label": rule.label,
                    "patterns": list(rule.patterns),
                    "feedback": rule.feedback,
                    "hint": rule.hint,
                    "next_question": rule.next_question,
                }
                for rule in self.misconceptions
            ],
        }


@dataclass(frozen=True)
class RubricEvaluation:
    """Local assessment signal used by the deterministic provider."""

    diagnosis: str
    misconception: str
    feedback: str
    hint: str
    next_question: str
    mastery_score: float
    reveal_answer: bool = False
    expected_value: float | None = None
    candidate_value: float | None = None
    matched_rule_id: str | None = None


@dataclass(frozen=True)
class ProviderRequest:
    """Provider-neutral prompt data."""

    learner_answer: str
    stage: str
    question: str | None
    hint_level: int
    context: tuple[RetrievedChunk, ...] = ()
    rubric: Rubric | None = None


@dataclass
class ProviderResult:
    """Normalized provider output before tutor-level guardrails are applied."""

    diagnosis: str = "unknown"
    misconception: str = ""
    feedback: str = ""
    hint: str = ""
    next_question: str = ""
    mastery_score: float = 0.0
    reveal_answer: bool = False
    citations: list[Citation | Mapping[str, Any]] = field(default_factory=list)
    safety_flags: list[str] = field(default_factory=list)
    expected_value: float | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProviderResult":
        """Coerce a JSON-like provider response into the typed result shape."""

        def text(name: str, default: str = "") -> str:
            raw = value.get(name, default)
            return raw if isinstance(raw, str) else str(raw)

        raw_score = value.get("mastery_score", 0.0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0

        raw_citations = value.get("citations", [])
        citations: list[Citation | Mapping[str, Any]] = []
        if isinstance(raw_citations, Sequence) and not isinstance(raw_citations, (str, bytes)):
            citations.extend(item for item in raw_citations if isinstance(item, (Citation, Mapping)))

        raw_flags = value.get("safety_flags", [])
        flags: list[str] = []
        if isinstance(raw_flags, Sequence) and not isinstance(raw_flags, (str, bytes)):
            flags.extend(str(item) for item in raw_flags if str(item).strip())

        expected = value.get("expected_value")
        try:
            expected_value = float(expected) if expected is not None else None
        except (TypeError, ValueError):
            expected_value = None

        return cls(
            diagnosis=text("diagnosis", "unknown"),
            misconception=text("misconception"),
            feedback=text("feedback"),
            hint=text("hint"),
            next_question=text("next_question"),
            mastery_score=score,
            reveal_answer=bool(value.get("reveal_answer", False)),
            citations=citations,
            safety_flags=flags,
            expected_value=expected_value,
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "diagnosis": self.diagnosis,
            "misconception": self.misconception,
            "feedback": self.feedback,
            "hint": self.hint,
            "next_question": self.next_question,
            "mastery_score": float(self.mastery_score),
            "reveal_answer": bool(self.reveal_answer),
            "citations": [
                citation.to_dict() if isinstance(citation, Citation) else dict(citation)
                for citation in self.citations
            ],
            "safety_flags": list(self.safety_flags),
        }


@dataclass(frozen=True)
class TutorResponse:
    """The exact public response contract returned by TutorService.respond."""

    stage: str
    diagnosis: str
    misconception: str
    feedback: str
    hint: str
    next_question: str
    mastery_score: float
    reveal_answer: bool
    citations: tuple[dict[str, JSONValue], ...] = ()
    retrieved_chunks: tuple[dict[str, JSONValue], ...] = ()
    safety_flags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "stage": self.stage,
            "diagnosis": self.diagnosis,
            "misconception": self.misconception,
            "feedback": self.feedback,
            "hint": self.hint,
            "next_question": self.next_question,
            "mastery_score": float(self.mastery_score),
            "reveal_answer": bool(self.reveal_answer),
            "citations": [dict(item) for item in self.citations],
            "retrieved_chunks": [dict(item) for item in self.retrieved_chunks],
            "safety_flags": list(self.safety_flags),
        }
