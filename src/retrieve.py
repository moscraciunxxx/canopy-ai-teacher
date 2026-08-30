"""Deterministic lexical retrieval with a TF-IDF-like score."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Iterable

from .ingest import chunk_markdown
from .schemas import LessonChunk, RetrievedChunk


__all__ = ["LexicalRetriever", "Retriever", "chunk_markdown", "tokenize"]


_TOKEN_RE = re.compile(r"[a-zA-Z]+(?:'[a-zA-Z]+)?|\d+(?:\.\d+)?|x")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "be",
        "by",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "with",
    }
)


def tokenize(text: str) -> list[str]:
    """Tokenize words, numbers, and the algebra variable x."""

    if not isinstance(text, str):
        text = str(text)
    return [token.lower() for token in _TOKEN_RE.findall(text)]


class LexicalRetriever:
    """A tiny cosine retriever that does not need scikit-learn.

    Scores use sublinear term frequency and smoothed inverse document
    frequency.  An exact token overlap tie-breaker keeps results stable when
    cosine scores are equal.
    """

    def __init__(
        self,
        chunks: Sequence[LessonChunk | Mapping[str, Any]] | Iterable[LessonChunk | Mapping[str, Any]],
    ) -> None:
        self.chunks: tuple[LessonChunk, ...] = tuple(
            self._coerce_chunk(chunk, index) for index, chunk in enumerate(chunks)
        )
        self._documents: tuple[Counter[str], ...] = tuple(
            Counter(tokenize(f"{chunk.heading} {chunk.text}")) for chunk in self.chunks
        )
        document_frequency: Counter[str] = Counter()
        for document in self._documents:
            document_frequency.update(document.keys())
        self._idf: dict[str, float] = {
            term: math.log((len(self._documents) + 1) / (frequency + 1)) + 1.0
            for term, frequency in document_frequency.items()
        }
        self._vectors: tuple[dict[str, float], ...] = tuple(
            self._weighted_vector(document) for document in self._documents
        )
        self._norms: tuple[float, ...] = tuple(
            math.sqrt(sum(value * value for value in vector.values())) for vector in self._vectors
        )

    @staticmethod
    def _coerce_chunk(chunk: LessonChunk | Mapping[str, Any], index: int) -> LessonChunk:
        if isinstance(chunk, LessonChunk):
            return chunk
        if isinstance(chunk, Mapping):
            raw_id = chunk.get("chunk_id", chunk.get("id", f"chunk-{index + 1:03d}"))
            raw_text = chunk.get("text", "")
            raw_heading = chunk.get("heading", chunk.get("section", ""))
            raw_source = chunk.get("source", "lesson")
            raw_order = chunk.get("order", index)
            try:
                order = int(raw_order)
            except (TypeError, ValueError):
                order = index
            return LessonChunk(
                chunk_id=str(raw_id),
                text=str(raw_text),
                heading=str(raw_heading),
                source=str(raw_source),
                order=order,
            )
        raise TypeError("retriever chunks must be LessonChunk objects or mappings")

    def _weighted_vector(self, counts: Counter[str]) -> dict[str, float]:
        return {
            term: (1.0 + math.log(count)) * self._idf.get(term, 1.0)
            for term, count in counts.items()
            if count > 0
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        min_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        """Return the highest scoring chunks, with deterministic tie ordering."""

        if not self.chunks or not isinstance(query, str) or not query.strip():
            return []
        try:
            limit = max(0, int(top_k))
        except (TypeError, ValueError):
            limit = 4
        if limit == 0:
            return []

        raw_terms = tokenize(query)
        terms = [term for term in raw_terms if term not in _STOPWORDS]
        if not terms:
            terms = raw_terms
        query_counts = Counter(terms)
        query_vector = self._weighted_vector(query_counts)
        query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
        query_term_set = set(terms)

        scored: list[tuple[float, int, RetrievedChunk]] = []
        for index, (chunk, vector, norm) in enumerate(zip(self.chunks, self._vectors, self._norms)):
            if query_norm and norm:
                dot = sum(query_vector.get(term, 0.0) * value for term, value in vector.items())
                score = dot / (query_norm * norm)
            else:
                score = 0.0
            matched_terms = tuple(sorted(query_term_set.intersection(vector)))
            if score < min_score:
                continue
            retrieved = RetrievedChunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                heading=chunk.heading,
                source=chunk.source,
                score=float(score),
                matched_terms=matched_terms,
                order=chunk.order,
            )
            scored.append((score, index, retrieved))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [item[2] for item in scored[:limit]]

    def search(self, query: str, top_k: int = 4, min_score: float = 0.0) -> list[RetrievedChunk]:
        """Alias for :func:`retrieve`."""

        return self.retrieve(query, top_k=top_k, min_score=min_score)


Retriever = LexicalRetriever
