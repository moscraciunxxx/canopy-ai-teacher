"""Configuration and embedded demo assets for the tutor core.

The core deliberately keeps its demo content in Python so that a checkout with
no surrounding files can still answer a learner.  If the conventional
``content/`` files are present, the ingestion helpers prefer those files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Iterator


DEFAULT_LESSON_PATH: Final[Path] = Path("content/demo_lesson.md")
DEFAULT_RUBRIC_PATH: Final[Path] = Path("content/demo_rubric.json")
DEFAULT_MODE: Final[str] = "demo"
DEFAULT_TOP_K: Final[int] = 4
DEFAULT_HTTP_TIMEOUT: Final[float] = 20.0
MAX_LEARNER_ANSWER_CHARS: Final[int] = 4_000
MAX_QUESTION_CHARS: Final[int] = 1_000


DEMO_LESSON: Final[str] = """# Solving a linear equation

An equation is balanced when both sides have the same value.  To solve for a
variable, use inverse operations and perform the same operation on both sides.

## Worked example

Consider **3x + 5 = 20**.  The constant is added to the x-term, so first undo
that addition on both sides.  Then undo the multiplication by 3.  Check a
solution by substituting it into the original equation and comparing both
sides.

## Common pitfalls

Subtracting or dividing on only one side breaks the balance.  Another common
mistake is to stop after removing the constant, leaving a coefficient attached
to x.  Keep asking which inverse operation removes the operation closest to
the variable.

## Self-check

After finding a value for x, substitute it into the original equation.  A
correct value makes the left-hand side and right-hand side equal.
"""


# This is intentionally ordinary JSON-shaped data: rubric.load_rubric can use
# it as a fallback without depending on a package-specific model format.
DEMO_RUBRIC: Final[dict[str, object]] = {
    "title": "Solving 3x + 5 = 20",
    "primary_question": "Solve 3x + 5 = 20. What is x?",
    "equation": "3x + 5 = 20",
    "expected_answer": "5",
    "concept": "Use inverse operations on both sides while preserving equality.",
    "criteria": [
        {
            "id": "correct",
            "description": "The learner gives a value that satisfies the equation.",
            "weight": 1.0,
        },
        {
            "id": "reasoning",
            "description": "The learner can describe undoing the addition and then the multiplication.",
            "weight": 0.5,
        },
    ],
    "misconceptions": [
        {
            "id": "forgot_division",
            "label": "Forgot to undo the coefficient",
            "patterns": ["9", "3x", "forgot.*divide", "stop.*constant"],
            "feedback": "You removed or noticed the constant, but the coefficient on x still needs attention.",
            "hint": "After undoing the addition, what inverse operation removes the coefficient attached to x?",
            "next_question": "Once the constant is gone, which operation is still acting directly on x?",
        },
        {
            "id": "one_side_only",
            "label": "Changed only one side",
            "patterns": ["one side", "only.*side", "just.*left", "just.*right"],
            "feedback": "An equation stays balanced only when the same operation is applied to both sides.",
            "hint": "Imagine a balance scale: if you undo an operation on one side, what must happen on the other side?",
            "next_question": "What would you do to the other side to keep the equality balanced?",
        },
        {
            "id": "sign_error",
            "label": "Sign error",
            "patterns": ["negative", "minus", "-3", "- 3"],
            "feedback": "Check the sign when you undo the addition, then verify by substitution.",
            "hint": "Use substitution to check the sign. What does the left side become with your value?",
            "next_question": "Does substituting your value make both sides equal, including their signs?",
        },
    ],
}


def candidate_paths(relative_path: Path) -> Iterator[Path]:
    """Yield sensible locations for a relative content path.

    The current working directory is useful for applications and tests.  The
    repository-root candidate makes the defaults work when the service is
    imported from another directory.  Duplicate paths are suppressed.
    """

    seen: set[Path] = set()
    candidates = (
        Path.cwd() / relative_path,
        Path(__file__).resolve().parent.parent / relative_path,
    )
    for candidate in candidates:
        resolved = candidate if candidate.is_absolute() else candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            yield resolved
