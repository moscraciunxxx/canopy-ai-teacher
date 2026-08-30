"""Provider abstraction, deterministic demo provider, and generic HTTP adapter."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from .config import DEFAULT_HTTP_TIMEOUT
from .rubric import evaluate_answer, load_rubric
from .schemas import Citation, ProviderRequest, ProviderResult, Rubric


class ProviderError(RuntimeError):
    """Base class for provider failures."""


class ProviderUnavailable(ProviderError):
    """Raised when an optional remote provider cannot be used."""


@runtime_checkable
class TutorProvider(Protocol):
    """Minimal interface accepted by TutorService."""

    def generate(self, request: ProviderRequest) -> ProviderResult | Mapping[str, Any]:
        ...


Provider = TutorProvider


class DemoProvider:
    """A deterministic local provider for the embedded equation lesson."""

    def __init__(self, rubric: Rubric | None = None) -> None:
        self.rubric = rubric or load_rubric()

    def generate(self, request: ProviderRequest) -> ProviderResult:
        rubric = request.rubric or self.rubric
        evaluation = evaluate_answer(
            request.learner_answer,
            rubric,
            question=request.question,
            stage=request.stage,
            hint_level=request.hint_level,
        )
        citations: list[Citation | Mapping[str, Any]] = [
            {
                "chunk_id": chunk.chunk_id,
                "source": chunk.source,
                "heading": chunk.heading,
                "quote": chunk.text[:320],
            }
            for chunk in request.context[:2]
        ]
        return ProviderResult(
            diagnosis=evaluation.diagnosis,
            misconception=evaluation.misconception,
            feedback=evaluation.feedback,
            hint=evaluation.hint,
            next_question=evaluation.next_question,
            mastery_score=evaluation.mastery_score,
            reveal_answer=evaluation.reveal_answer,
            citations=citations,
            expected_value=evaluation.expected_value,
        )

    def respond(
        self,
        learner_answer: str,
        stage: str = "diagnostic",
        question: str | None = None,
        hint_level: int = 1,
        context: Sequence[Any] = (),
    ) -> dict[str, Any]:
        """Convenience method for direct provider use outside TutorService."""

        request = ProviderRequest(
            learner_answer=learner_answer,
            stage=stage,
            question=question,
            hint_level=hint_level,
            context=tuple(context),
            rubric=self.rubric,
        )
        return self.generate(request).to_dict()

    analyze = generate


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, Sequence) and not isinstance(content, (str, bytes)):
        parts: list[str] = []
        for item in content:
            if isinstance(item, Mapping):
                text = item.get("text", item.get("content", ""))
                if text:
                    parts.append(str(text))
            elif item:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _parse_json_content(content: Any) -> Mapping[str, Any]:
    if isinstance(content, Mapping):
        return content
    text = _content_to_text(content).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError("The provider returned non-JSON tutor output") from exc
    if not isinstance(value, Mapping):
        raise ProviderError("The provider returned a JSON value instead of an object")
    return value


class OpenAICompatibleProvider:
    """Optional adapter for any endpoint supporting chat completions.

    The endpoint, model, and key are supplied by the caller or environment;
    no credential is embedded in this module.  Demo mode never instantiates
    this provider, so an offline demo does not make a network request.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
    ) -> None:
        self.endpoint = endpoint or os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_ENDPOINT")
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL") or "local-model"
        try:
            self.timeout = max(0.1, float(timeout))
        except (TypeError, ValueError):
            self.timeout = DEFAULT_HTTP_TIMEOUT

    @classmethod
    def from_environment(cls, **kwargs: Any) -> "OpenAICompatibleProvider":
        return cls(**kwargs)

    def _chat_url(self) -> str:
        if not self.endpoint:
            raise ProviderUnavailable(
                "No OpenAI-compatible endpoint configured; pass endpoint=... or set OPENAI_BASE_URL"
            )
        endpoint = self.endpoint.rstrip("/")
        if endpoint.endswith("/chat/completions"):
            return endpoint
        if endpoint.endswith("/v1"):
            return f"{endpoint}/chat/completions"
        return f"{endpoint}/v1/chat/completions"

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a misconception-aware Socratic tutor. Return only a JSON object with keys "
            "diagnosis, misconception, feedback, hint, next_question, mastery_score, reveal_answer, "
            "citations, and safety_flags. Keep low-level hints free of the final answer. "
            "Citations must use only supplied chunk_id values."
        )

    def _user_prompt(self, request: ProviderRequest) -> str:
        context = [
            {
                "chunk_id": chunk.chunk_id,
                "heading": chunk.heading,
                "text": chunk.text,
                "source": chunk.source,
            }
            for chunk in request.context
        ]
        rubric = request.rubric.to_dict() if request.rubric else {}
        payload = {
            "stage": request.stage,
            "question": request.question,
            "hint_level": request.hint_level,
            "learner_answer": request.learner_answer,
            "rubric": rubric,
            "retrieved_context": context,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def generate(self, request: ProviderRequest) -> ProviderResult:
        url = self._chat_url()
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": self._user_prompt(request)},
            ],
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        http_request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            raise ProviderUnavailable(f"OpenAI-compatible provider request failed: {exc}") from exc

        try:
            envelope = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError("OpenAI-compatible provider returned invalid JSON") from exc
        if not isinstance(envelope, Mapping):
            raise ProviderError("OpenAI-compatible provider returned an invalid response object")

        content: Any = envelope
        choices = envelope.get("choices")
        if isinstance(choices, Sequence) and choices:
            first = choices[0]
            if isinstance(first, Mapping):
                message = first.get("message", first)
                if isinstance(message, Mapping):
                    content = message.get("content", message)
                else:
                    content = message
        result = ProviderResult.from_mapping(_parse_json_content(content))
        return result


GenericOpenAIProvider = OpenAICompatibleProvider
