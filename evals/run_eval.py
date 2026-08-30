"""Run the small deterministic golden suite used by the demo.

This is an internal quality gate for a judged product, not an official contest
score. It intentionally runs without a model API or network access.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.tutor import TutorService  # noqa: E402


def _contains_any(value: str, needles: list[str]) -> bool:
    lowered = value.lower()
    return any(needle.lower() in lowered for needle in needles)


def main() -> int:
    service = TutorService(mode="demo")
    cases_path = ROOT / "evals" / "cases.jsonl"
    failures: list[str] = []
    passed = 0

    for raw in cases_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        case = json.loads(raw)
        response = service.respond(
            case["learner_answer"],
            stage=case.get("stage", "diagnostic"),
            question=case.get("question"),
        )
        text = " ".join(
            str(response.get(field, ""))
            for field in ("diagnosis", "misconception", "feedback", "hint", "next_question")
        )
        expected = case.get("expected")
        expected_diagnoses = {
            "misconception": {"misconception"},
            "correct": {"correct"},
            "bounded": {"off_topic"},
            "scaffold": {"scaffold"},
        }
        diagnosis_ok = response.get("diagnosis") in expected_diagnoses.get(expected, {response.get("diagnosis")})
        missing = [item for item in case.get("must_include", []) if item.lower() not in text.lower()]
        forbidden = [item for item in case.get("must_not_include", []) if item.lower() in text.lower()]
        retrieved_ids = {
            str(chunk.get("chunk_id"))
            for chunk in response.get("retrieved_chunks", [])
            if isinstance(chunk, dict)
        }
        citation_ids = {
            str(citation.get("chunk_id"))
            for citation in response.get("citations", [])
            if isinstance(citation, dict)
        }
        hard_gate_errors = []
        if not response.get("citations"):
            hard_gate_errors.append("no citations")
        if not citation_ids.issubset(retrieved_ids):
            hard_gate_errors.append("citation outside retrieval set")
        if response.get("reveal_answer") is not False:
            hard_gate_errors.append("low-level reveal")
        if "x = 5" in str(response.get("hint", "")).lower():
            hard_gate_errors.append("answer leaked in hint")
        try:
            score = float(response.get("mastery_score"))
            if not 0.0 <= score <= 1.0:
                hard_gate_errors.append("score out of range")
        except (TypeError, ValueError):
            hard_gate_errors.append("invalid score")
        if not diagnosis_ok or missing or forbidden or hard_gate_errors:
            failures.append(
                f"{case['case_id']}: diagnosis={response.get('diagnosis')!r}, expected={expected!r}, "
                f"missing={missing}, forbidden={forbidden}, gates={hard_gate_errors}"
            )
        else:
            passed += 1

    total = passed + len(failures)
    print(json.dumps({"passed": passed, "total": total, "pass_rate": passed / total if total else 0.0, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
