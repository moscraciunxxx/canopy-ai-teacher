"""Canopy: a multi-subject, visual AI-teacher studio for the SPEED challenge.

The product combines a structured STEM and Human Worlds academy, adaptive
coaching, practice and transfer loops, and browser-rendered 3D/flow labs. Demo
mode is deterministic and offline-first; an OpenAI-compatible provider remains
optional for the legacy algebra tutor contract.
"""

from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Any, Mapping

import streamlit as st

from src.curriculum_atlas import (
    course_nodes,
    course_practice,
    default_course_id,
    get_academies,
    get_course,
    get_courses,
)
from src.interactive_labs import (
    LabValue,
    build_lab_figure,
    default_lab_values,
    lab_control_specs,
    lab_insight,
    lab_metrics,
    lab_option_label,
)
from src.localization import (
    academy_description,
    academy_label,
    answer_extent,
    course_label,
    get_language,
    get_languages,
    get_stages,
    is_rtl,
    language_option,
    localize_course,
    reasoning_signals,
    tr,
)

try:
    from src.learning_studio import build_learning_graph, remix_practice_bank
except ImportError:  # The UI keeps a minimal fallback for a partial checkout.
    build_learning_graph = None  # type: ignore[assignment]
    remix_practice_bank = None  # type: ignore[assignment]


APP_TITLE = "Canopy"
DEFAULT_LESSON_PATH = Path(__file__).resolve().parent / "content" / "demo_lesson.md"
DEFAULT_MASTERY = 0.28


DEMO_LESSON: dict[str, Any] = {
    "title": "Solve a linear equation by keeping both sides balanced",
    "eyebrow": "CANOPY · ADAPTIVE AI TEACHER",
    "concept": "Inverse operations",
    "prompt": "Solve 3x + 5 = 20. What is x, and what should you do first?",
    "equation": "3x + 5 = 20",
    "objectives": [
        "Use inverse operations to isolate a variable.",
        "Apply the same operation to both sides of an equation.",
        "Explain why each step preserves equality.",
        "Verify a solution by substituting it back.",
    ],
    "misconception": "The teacher watches for skipped inverse operations, one-sided changes, and answers that are not checked.",
    "citations": [
        {
            "label": "OpenStax · Elementary Algebra 2e",
            "url": "https://openstax.org/books/elementary-algebra-2e/pages/2-1-use-a-general-strategy-to-solve-linear-equations",
            "supports": "Use inverse operations and a general strategy to solve linear equations.",
        },
        {
            "label": "Math is Fun · Solving Equations",
            "url": "https://www.mathsisfun.com/algebra/solve-equation.html",
            "supports": "Keep an equation balanced by doing the same thing to both sides.",
        },
    ],
}


NODES: tuple[dict[str, Any], ...] = (
    {
        "id": "translate",
        "short": "Translate",
        "label": "See the structure",
        "icon": "◈",
        "color": "mint",
        "mastery": 0.82,
        "equation": "4x + 3 = 27",
        "question": "A mystery number is multiplied by 4 and then increased by 3 to make 27. What equation represents the story?",
        "description": "Name the unknown and map the story into a symbolic relationship before calculating.",
        "hint": "Which action happens first to the mystery number: multiplying or increasing?",
        "explain_steps": (
            ("Name the unknown", "Let x = the mystery number", "Give the unknown a role before you manipulate it."),
            ("Preserve the story order", "4x + 3 = 27", "The multiplier acts first; the increase happens after it."),
            ("Predict the structure", "4(x + 3) ≠ 4x + 3", "A common trap is changing the order. Ask what happened first in the story."),
        ),
    },
    {
        "id": "balance",
        "short": "Balance",
        "label": "Balance the system",
        "icon": "⇄",
        "color": "gold",
        "mastery": 0.88,
        "equation": "x + 4 = 11",
        "question": "Solve x + 4 = 11. What should happen to both sides?",
        "description": "Understand equality as a relationship that must stay level.",
        "hint": "What operation would remove the +4 without tipping either side?",
        "explain_steps": (
            ("Name the promise", "x + 4 = 11", "Both sides have the same value. Every legal move must preserve that promise."),
            ("Undo the outside move", "x + 4 − 4 = 11 − 4", "Subtract 4 from both sides. The balance is still level."),
            ("Read the result", "x = 7", "The variable is alone, so check 7 + 4 = 11."),
        ),
    },
    {
        "id": "isolate",
        "short": "Isolate",
        "label": "Isolate the signal",
        "icon": "✦",
        "color": "coral",
        "mastery": 0.28,
        "equation": "3x + 5 = 20",
        "question": "Solve 3x + 5 = 20. What is x, and what should you do first?",
        "description": "Undo the outside operation first, then the coefficient, and explain why the order matters.",
        "hint": "What operation is farthest from x right now? Undo that operation on both sides.",
        "explain_steps": (
            ("Read outside-in", "3x + 5 = 20", "The +5 is the outside operation. Undo it before touching the coefficient 3."),
            ("Make the intermediate", "3x + 5 − 5 = 20 − 5  →  3x = 15", "One balanced move removes the constant and leaves the x-term visible."),
            ("Isolate and verify", "3x ÷ 3 = 15 ÷ 3  →  x = 5", "Divide both sides by 3, then substitute 5 into the original equation."),
        ),
    },
    {
        "id": "verify",
        "short": "Verify",
        "label": "Verify with evidence",
        "icon": "✓",
        "color": "violet",
        "mastery": 0.08,
        "equation": "2x + 7 = 15",
        "question": "A classmate says x = 4 solves 2x + 7 = 15. How can you test the claim in one line?",
        "description": "Use substitution as evidence, not as a ritual after the ‘real’ work is done.",
        "hint": "Replace x with 4, evaluate the left side, and compare it with 15.",
        "explain_steps": (
            ("Replace the unknown", "2(4) + 7 = 15?", "Substitution turns a proposed solution into a testable claim."),
            ("Evaluate one side", "8 + 7 = 15", "Compute the expression carefully, keeping the original relationship in view."),
            ("Decide with evidence", "15 = 15  ✓", "Both sides match, so the claim survives the check."),
        ),
    },
    {
        "id": "transfer",
        "short": "Transfer",
        "label": "Transfer the move",
        "icon": "↗",
        "color": "blue",
        "mastery": 0.0,
        "equation": "3m + 5 = 20",
        "question": "A taxi charges $5 to start and $3 per mile. The ride costs $20. How many miles were traveled?",
        "description": "Recognise the same structure in a real decision instead of memorising one equation.",
        "hint": "Which cost happens once, even at zero miles? Let m be miles and write the total-cost equation.",
        "explain_steps": (
            ("Separate the roles", "3m + 5 = 20", "The per-mile rate multiplies m; the fixed fee is the constant."),
            ("Undo the fixed fee", "3m = 15", "Remove the one-time cost before interpreting the rate."),
            ("Interpret the result", "m = 5 miles", "The number is meaningful because it answers the story, not only the algebra."),
        ),
    },
    {
        "id": "teach_back",
        "short": "Teach-back",
        "label": "Teach it forward",
        "icon": "✺",
        "color": "gold",
        "mastery": 0.0,
        "equation": "3x + 5 = 20",
        "question": "Teach a younger learner why solving 3x + 5 = 20 starts by subtracting 5 from both sides.",
        "description": "Make the invisible reasoning visible enough that someone else can use it.",
        "hint": "Use a balance metaphor, name the inverse operation, and state what equation remains.",
        "explain_steps": (
            ("Name the invariant", "Both sides stay equal", "A good explanation starts with the promise the algebra is protecting."),
            ("Connect action to reason", "Subtract 5 from both sides", "The same move on both sides preserves equality and exposes 3x."),
            ("Predict the trap", "Do not stop at 3x = 15", "Teaching includes noticing where another learner might stop or drift."),
        ),
    },
)


PRACTICE_BANK: tuple[dict[str, Any], ...] = (
    {
        "id": "remix_balance",
        "title": "Warm-up · balance",
        "equation": "2x + 3 = 11",
        "question": "Solve 2x + 3 = 11. Explain the first inverse operation.",
        "answer": "4",
        "skill": "same operation on both sides",
        "transfer": "If the constant were −3 instead, which inverse operation would change?",
    },
    {
        "id": "remix_signs",
        "title": "Stretch · signed coefficients",
        "equation": "−2m − 7 = 9",
        "question": "Solve −2m − 7 = 9. Track the sign in your explanation.",
        "answer": "-8",
        "skill": "sign-aware inverse operations",
        "transfer": "How would you verify a negative result without re-solving the equation?",
    },
    {
        "id": "remix_parentheses",
        "title": "Transfer · parentheses",
        "equation": "3(x + 2) = 15",
        "question": "Solve 3(x + 2) = 15. Name the outside operation first.",
        "answer": "3",
        "skill": "reverse order of operations",
        "transfer": "Why is dividing first safer here than subtracting 2 first?",
    },
    {
        "id": "remix_fraction",
        "title": "Challenge · division",
        "equation": "b ÷ 3 = −4",
        "question": "Solve b ÷ 3 = −4. Which inverse operation isolates b?",
        "answer": "-12",
        "skill": "inverse multiplication",
        "transfer": "What quick multiplication check confirms the result?",
    },
)


FLASHCARDS: tuple[dict[str, str], ...] = (
    {"front": "What does the equals sign promise?", "back": "Both expressions have the same value; a legal operation preserves that relationship."},
    {"front": "What is the inverse of adding 5?", "back": "Subtract 5 from both sides."},
    {"front": "Why undo +5 before ×3 in 3x + 5 = 20?", "back": "The +5 is the outside operation, so removing it exposes the x-term before division."},
    {"front": "What is the fastest final check?", "back": "Substitute the proposed value into the original equation and compare both sides."},
)


MODE_LABELS = (
    "Coach · Socratic",
    "Learn · Visual",
    "Remix · Practice",
    "Apply · Roleplay",
)


NUMBER_PATTERN = r"-?(?:\d+(?:\.\d*)?|\.\d+)"


def _first_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def live_settings() -> dict[str, str | bool]:
    api_key = _first_env("MISCONCEPTION_LAB_API_KEY")
    base_url = _first_env("MISCONCEPTION_LAB_API_BASE_URL")
    model = _first_env("MISCONCEPTION_LAB_MODEL")
    return {"api_key": api_key, "base_url": base_url, "model": model, "ready": bool(api_key and base_url)}


def load_lesson(course: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Adapt a course into the inspectable lesson contract used by the UI."""

    if course is not None:
        nodes = course_nodes(course)
        return {
            "title": str(course["title"]),
            "eyebrow": f"CANOPY · {str(course['academy']).upper()} · {course['subject']}",
            "concept": str(course["subject"]),
            "prompt": str(course["big_question"]),
            "equation": str(nodes[2]["equation"] if len(nodes) > 2 else nodes[0]["equation"]),
            "objectives": [str(node["description"]) for node in nodes],
            "misconception": str(course["misconception"]),
            "citations": [dict(citation) for citation in course["sources"]],
            "optional_content_path": str(DEFAULT_LESSON_PATH),
        }
    lesson = dict(DEMO_LESSON)
    lesson["objectives"] = list(DEMO_LESSON["objectives"])
    lesson["citations"] = [dict(citation) for citation in DEMO_LESSON["citations"]]
    lesson["optional_content_path"] = str(DEFAULT_LESSON_PATH)
    return lesson


def available_practice(course: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], ...]:
    """Return a course-native deterministic bank, with the algebra fallback."""

    if course is not None:
        items = course_practice(course)
        if items:
            return items
    if callable(remix_practice_bank):
        try:
            remix_items = remix_practice_bank(seed=17)
            adapted: list[dict[str, Any]] = []
            for item in remix_items:
                metadata = item.get("metadata", {})
                adapted.append(
                    {
                        "id": str(item["id"]),
                        "title": f"Level {item['difficulty']} · {metadata.get('skill', item['node_id'])}",
                        "equation": str(item.get("equation", "")),
                        "question": str(item.get("prompt", "")),
                        "answer": str(item.get("answer", "")),
                        "answer_type": str(item.get("answer_type", "text")),
                        "accepted_answers": list(item.get("accepted_answers", [])),
                        "skill": str(metadata.get("cognitive_move", ", ".join(item.get("skills", [])))),
                        "transfer": str(item.get("transfer_prompt", "How would this idea change in a new context?")),
                        "hint_ladder": list(item.get("hint_ladder", [])),
                        "difficulty": int(item.get("difficulty", 1)),
                        "explanation": str(item.get("answer_explanation", "")),
                    }
                )
            if adapted:
                return tuple(adapted)
        except (KeyError, TypeError, ValueError):
            pass
    return PRACTICE_BANK


def learning_graph(
    mastery: float,
    nodes: tuple[dict[str, Any], ...] | None = None,
) -> Mapping[str, Any]:
    """Build a truthful six-stage graph for any course in the academy."""

    active_nodes = nodes or NODES
    bounded = max(0.0, min(0.98, mastery))
    progress = [0.92, 0.86, bounded, 0.52 if bounded >= 0.58 else 0.08, 0.24 if bounded >= 0.72 else 0.0, 0.18 if bounded >= 0.84 else 0.0]
    statuses = ["mastered", "mastered", "active", "available" if bounded >= 0.52 else "locked", "available" if bounded >= 0.72 else "locked", "available" if bounded >= 0.84 else "locked"]
    graph_nodes = [
        {
            "id": str(node["id"]),
            "status": statuses[min(index, len(statuses) - 1)],
            "mastery": progress[min(index, len(progress) - 1)],
        }
        for index, node in enumerate(active_nodes)
    ]
    edges = [
        {"source": str(active_nodes[index]["id"]), "target": str(active_nodes[index + 1]["id"])}
        for index in range(max(0, len(active_nodes) - 1))
    ]
    completion = round(100 * sum(progress[: len(active_nodes)]) / max(len(active_nodes), 1))
    return {"nodes": graph_nodes, "edges": edges, "completion_percent": completion}


def init_state() -> None:
    default_course = get_course(default_course_id("stem"))
    default_nodes = course_nodes(default_course)
    default_bank = available_practice(default_course)
    defaults: dict[str, Any] = {
        "ml_academy": "stem",
        "ml_course_id": str(default_course["id"]),
        "ml_course_progress": {},
        "ml_language": "en",
        "ml_last_language": "en",
        "ml_show_english": False,
        "ml_hint_level": 1,
        "ml_feedback": None,
        "ml_mastery": DEFAULT_MASTERY,
        "ml_attempts": 0,
        "ml_answer": "",
        "ml_mode": MODE_LABELS[0],
        "ml_last_mode": MODE_LABELS[0],
        "ml_selected_node": str(default_nodes[2]["id"]),
        "ml_practice_id": str(default_bank[0]["id"]),
        "ml_practice_answer": "",
        "ml_apply_answer": "",
        "ml_reflection": "",
        "ml_roleplay_answer": "",
        "ml_roleplay": False,
        "ml_explain_step": 0,
        "ml_lens": "Visual and patient",
        "ml_flashcard_index": 0,
        "ml_flashcard_flipped": False,
        "ml_notes": [],
        "ml_history": [],
        "ml_engine": "Demo · deterministic",
        "ml_builder_step": 0,
        "ml_builder_errors": 0,
        "ml_builder_signal": "",
        "ml_builder_recorded": False,
        "ml_explain_lens": "Balance scale",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_state() -> None:
    for key in list(st.session_state):
        if str(key).startswith("ml_"):
            st.session_state.pop(key, None)


def activate_course(course_id: str) -> Mapping[str, Any]:
    """Switch the whole teacher context while preserving each course's trail."""

    target = get_course(course_id)
    current_id = str(st.session_state.get("ml_course_id", ""))
    target_nodes = course_nodes(target)
    target_bank = available_practice(target)
    if current_id == course_id:
        node_ids = {str(node["id"]) for node in target_nodes}
        if str(st.session_state.get("ml_selected_node", "")) not in node_ids:
            st.session_state["ml_selected_node"] = str(target_nodes[2]["id"])
        return target

    progress_by_course = dict(st.session_state.get("ml_course_progress", {}))
    if current_id:
        progress_by_course[current_id] = {
            "mastery": float(st.session_state.get("ml_mastery", DEFAULT_MASTERY)),
            "attempts": int(st.session_state.get("ml_attempts", 0)),
            "history": list(st.session_state.get("ml_history", [])),
            "notes": list(st.session_state.get("ml_notes", [])),
        }
    restored = progress_by_course.get(course_id, {})
    st.session_state["ml_course_progress"] = progress_by_course
    st.session_state["ml_course_id"] = course_id
    st.session_state["ml_academy"] = str(target["academy"])
    st.session_state["ml_mastery"] = float(restored.get("mastery", DEFAULT_MASTERY))
    st.session_state["ml_attempts"] = int(restored.get("attempts", 0))
    st.session_state["ml_history"] = list(restored.get("history", []))
    st.session_state["ml_notes"] = list(restored.get("notes", []))
    st.session_state["ml_selected_node"] = str(target_nodes[2]["id"])
    st.session_state["ml_practice_id"] = str(target_bank[0]["id"])
    st.session_state["ml_feedback"] = None
    st.session_state["ml_answer"] = ""
    st.session_state["ml_practice_answer"] = ""
    st.session_state["ml_apply_answer"] = ""
    st.session_state["ml_reflection"] = ""
    st.session_state["ml_roleplay_answer"] = ""
    st.session_state["ml_roleplay"] = False
    st.session_state["ml_explain_step"] = 0
    st.session_state["ml_flashcard_index"] = 0
    st.session_state["ml_flashcard_flipped"] = False
    return target


def rerun() -> None:
    st.rerun()


def active_language_code() -> str:
    """Return the validated learner locale stored independently of progress."""

    return get_language(str(st.session_state.get("ml_language", "en")))["code"]


def reset_visual_lab(course_id: str, language_code: str = "en") -> None:
    """Restore one visual laboratory before its keyed controls render."""

    course = get_course(course_id)
    for key, value in default_lab_values(course).items():
        st.session_state[f"ml_lab_{course_id}_{key}_{language_code}"] = value


def extract_x_value(answer: str) -> float | None:
    text = answer.strip().lower().replace("−", "-")
    if not text:
        return None
    for pattern in (
        rf"\bx\s*(?:=|is|equals)\s*({NUMBER_PATTERN})",
        rf"\b(?:answer|value|solution)\s*(?:is|=|:)\s*({NUMBER_PATTERN})",
    ):
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    if re.fullmatch(rf"\s*{NUMBER_PATTERN}\s*", text):
        return float(text)
    numbers = re.findall(NUMBER_PATTERN, text)
    if len(numbers) == 1 and not any(operator in text for operator in ("+", "=", "*", "/")):
        return float(numbers[0])
    return None


def _expected_from_equation(equation: str) -> float | None:
    try:
        from src.rubric import solve_linear_equation

        return solve_linear_equation(equation)
    except (ImportError, TypeError, ValueError):
        return None


def _fallback_feedback(answer: str, question: str, hint_level: int) -> dict[str, Any]:
    expected = _expected_from_equation(question)
    value = extract_x_value(answer)
    if value is not None and expected is not None and abs(value - expected) < 1e-9:
        return {
            "kind": "success",
            "title": "Correct reasoning",
            "body": "Your value satisfies the equation. Explain the inverse operations and verify it by substitution.",
            "next_step": "Can you explain why the outside operation is undone first?",
            "correct": True,
            "mastery": 0.92,
            "citations": [],
            "safety_flags": [],
        }
    return {
        "kind": "warning",
        "title": "Let’s find the next move",
        "body": "Start with the operation farthest from the variable and apply its inverse to both sides.",
        "next_step": "What operation is acting on the variable term right now?",
        "correct": False,
        "mastery": 0.30 if hint_level < 3 else 0.42,
        "citations": [],
        "safety_flags": [],
    }


def build_tutor_service(settings: Mapping[str, str | bool], mode: str = "demo") -> Any:
    from src.tutor import TutorService

    if mode == "live":
        from src.provider import OpenAICompatibleProvider

        provider = OpenAICompatibleProvider(
            endpoint=str(settings.get("base_url", "")),
            api_key=str(settings.get("api_key", "")),
            model=str(settings.get("model", "")) or None,
        )
        return TutorService(mode="live", provider=provider)
    return TutorService(mode="demo")


def normalize_core_feedback(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return _fallback_feedback("", DEMO_LESSON["question"], 1)
    diagnosis = str(raw.get("diagnosis", "unknown")).strip().lower()
    titles = {
        "correct": "Correct reasoning",
        "misconception": str(raw.get("misconception") or "A useful misconception signal"),
        "scaffold": "Let’s build the next step",
        "off_topic": "Return to the learning path",
        "unknown": "Let’s find your starting point",
    }
    if diagnosis == "correct":
        kind = "success"
    elif diagnosis in {"misconception", "off_topic"}:
        kind = "warning"
    else:
        kind = "info"
    return {
        "kind": kind,
        "title": titles.get(diagnosis, "Learning signal"),
        "body": str(raw.get("feedback") or "The teacher is listening for your next step."),
        "next_step": str(raw.get("next_question") or "What would you try next?"),
        "correct": diagnosis == "correct",
        "mastery": max(0.0, min(1.0, float(raw.get("mastery_score", 0.0) or 0.0))),
        "diagnosis": diagnosis,
        "misconception": str(raw.get("misconception") or ""),
        "hint": str(raw.get("hint") or ""),
        "citations": list(raw.get("citations", [])) if isinstance(raw.get("citations", []), (list, tuple)) else [],
        "retrieved_chunks": list(raw.get("retrieved_chunks", [])) if isinstance(raw.get("retrieved_chunks", []), (list, tuple)) else [],
        "safety_flags": list(raw.get("safety_flags", [])) if isinstance(raw.get("safety_flags", []), (list, tuple)) else [],
    }


def core_diagnose(
    settings: Mapping[str, str | bool],
    answer: str,
    question: str,
    hint_level: int,
    mode: str = "demo",
    stage: str = "diagnostic",
) -> dict[str, Any]:
    try:
        service = build_tutor_service(settings, mode=mode)
        raw = service.respond(answer, stage=stage, question=question, hint_level=hint_level)
        return normalize_core_feedback(raw)
    except Exception as exc:
        fallback = _fallback_feedback(answer, question, hint_level)
        if mode == "live":
            fallback["title"] = "Live teacher unavailable"
            fallback["body"] = f"The optional live provider could not answer this turn ({type(exc).__name__}). Demo mode remains ready."
        fallback["safety_flags"] = ["provider_unavailable"] if mode == "live" else []
        return fallback


def reflect_diagnose(answer: str) -> dict[str, Any]:
    text = answer.lower().strip()
    if not text:
        return {
            "kind": "warning",
            "title": "Give the teacher something to listen for",
            "body": "Explain the move in your own words, as if you were helping a classmate.",
            "next_step": "Try starting with: “The equals sign means…”",
            "mastery": 0.28,
            "signals": [],
        }
    checks = (
        ("Balance", ("both sides", "same operation", "balanced", "equal")),
        ("Inverse", ("inverse", "undo", "subtract", "divide", "add", "multiply")),
        ("Order", ("first", "then", "constant", "coefficient", "outside")),
        ("Verify", ("check", "substitut", "verify", "original")),
    )
    signals = [label for label, cues in checks if any(cue in text for cue in cues)]
    score = len(signals) / len(checks)
    if score >= 0.75:
        return {
            "kind": "success",
            "title": "Teacher-level explanation",
            "body": "You connected the invariant, the inverse operations, the order of the moves, and verification. That is durable understanding—not just an answer.",
            "next_step": "Now transfer the explanation to a signed or parenthesized equation.",
            "mastery": 0.88,
            "signals": signals,
        }
    if score >= 0.5:
        return {
            "kind": "info",
            "title": "Strong start · add one missing link",
            "body": "Your explanation has a useful structure. Add why the operation happens on both sides, or how you would check the final value.",
            "next_step": "Which step would you show to prove the equation stayed balanced?",
            "mastery": 0.62,
            "signals": signals,
        }
    return {
        "kind": "warning",
        "title": "The teacher hears a partial model",
        "body": "Name the operation, its inverse, and the reason the same move belongs on both sides. A quick substitution check will close the loop.",
        "next_step": "Can you say what you undo first and why?",
        "mastery": 0.40,
        "signals": signals,
    }


def _term_present(text: str, term: str) -> bool:
    """Match rubric language without letting one-letter terms match anywhere."""

    normalized_text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    normalized_term = re.sub(r"[^a-z0-9]+", " ", term.lower()).strip()
    if not normalized_term:
        return False
    if " " in normalized_term:
        return normalized_term in normalized_text
    tokens = set(normalized_text.split())
    if len(normalized_term) <= 2:
        return normalized_term in tokens
    return any(token == normalized_term or token.startswith(normalized_term) for token in tokens)


def multilingual_diagnose(
    answer: str,
    question: str,
    hint: str,
    language_code: str,
) -> dict[str, Any]:
    """Assess visible reasoning structure without faking semantic certainty.

    The offline multilingual rubric can recognise effort and native-language
    reasoning connectors.  It intentionally never labels an open explanation
    factually correct; exact numeric or symbolic answers are checked separately.
    """

    text = answer.strip()
    if not text:
        return {
            "kind": "warning",
            "title": tr("feedback_start", language_code),
            "body": tr("node_hint", language_code),
            "next_step": hint or question,
            "correct": False,
            "mastery": DEFAULT_MASTERY,
            "signals": [],
            "citations": [],
            "safety_flags": ["multilingual_structure_only"],
        }
    signals = reasoning_signals(text, language_code)
    extent = answer_extent(text, language_code)
    compact_script = language_code in {"zh", "ja", "yue"}
    strong_extent = 24 if compact_script else 12
    developing_extent = 10 if compact_script else 6
    if extent >= strong_extent and len(signals) >= 2:
        return {
            "kind": "success",
            "title": tr("feedback_strong", language_code),
            "body": f"{tr('model', language_code)} · {tr('evidence', language_code)} · {tr('explanation', language_code)}",
            "next_step": question,
            "correct": False,
            "mastery": 0.68,
            "signals": signals,
            "citations": [],
            "safety_flags": ["multilingual_structure_only"],
        }
    if extent >= developing_extent or signals:
        return {
            "kind": "info",
            "title": tr("feedback_developing", language_code),
            "body": tr("node_hint", language_code),
            "next_step": question,
            "correct": False,
            "mastery": 0.58,
            "signals": signals,
            "citations": [],
            "safety_flags": ["multilingual_structure_only"],
        }
    return {
        "kind": "warning",
        "title": tr("feedback_start", language_code),
        "body": tr("node_hint", language_code),
        "next_step": hint or question,
        "correct": False,
        "mastery": 0.38,
        "signals": signals,
        "citations": [],
        "safety_flags": ["multilingual_structure_only"],
    }


def domain_diagnose(
    course: Mapping[str, Any],
    answer: str,
    node: Mapping[str, Any] | None = None,
    hint_level: int = 1,
    language_code: str = "en",
) -> dict[str, Any]:
    """Apply an inspectable, subject-specific reasoning rubric."""

    text = answer.strip()
    focus = node or course_nodes(course)[2]
    if get_language(language_code)["code"] != "en":
        hint = str(focus.get("hint") or course.get("big_question", ""))
        if hint_level >= 3:
            hint = f"{focus.get('equation', '')} · {hint}"
        return multilingual_diagnose(
            text,
            str(focus.get("question") or course.get("big_question", "")),
            hint,
            language_code,
        )
    groups = [list(group) for group in course.get("diagnostic_groups", [])]
    if not text:
        return {
            "kind": "warning",
            "title": "Give the teacher a trace of your thinking",
            "body": "A fragment, prediction, source observation, or uncertainty is enough for Canopy to choose the next useful move.",
            "next_step": str(focus.get("hint") or course["big_question"]),
            "correct": False,
            "mastery": DEFAULT_MASTERY,
            "signals": [],
            "misconception": str(course["misconception"]),
            "citations": [],
            "safety_flags": [],
        }
    matched_groups = [group for group in groups if any(_term_present(text, term) for term in group)]
    signals = [group[0].title() for group in matched_groups if group]
    missing_groups = [group for group in groups if group not in matched_groups]
    score = len(matched_groups) / max(len(groups), 1)
    heard = ", ".join(signals) if signals else "a first attempt"
    missing = ", ".join(group[0] for group in missing_groups[:2] if group)
    if score >= 0.75:
        return {
            "kind": "success",
            "title": "Integrated subject reasoning",
            "body": f"Canopy heard {heard}. You linked enough layers to make the explanation testable instead of merely naming a fact.",
            "next_step": str(course["transfer_prompt"]),
            "correct": True,
            "mastery": 0.88,
            "signals": signals,
            "misconception": "No dominant misconception signal in this response.",
            "citations": [],
            "safety_flags": [],
        }
    if score >= 0.5:
        return {
            "kind": "info",
            "title": "Strong structure · connect one more layer",
            "body": f"Canopy heard {heard}. Add explicit reasoning about {missing or 'the evidence boundary'} so another learner can follow the mechanism or argument.",
            "next_step": str(focus.get("question") or course["big_question"]),
            "correct": False,
            "mastery": 0.64,
            "signals": signals,
            "misconception": str(course["misconception"]),
            "citations": [],
            "safety_flags": [],
        }
    reveal = str(focus.get("hint") or course["big_question"])
    if hint_level >= 3:
        reveal = f"Use this model, then explain its limit: {focus.get('equation', '')}."
    return {
        "kind": "warning",
        "title": "The teacher hears a partial model",
        "body": f"Canopy heard {heard}. Name a relationship and point to evidence; then connect it to {missing or 'a prediction or claim'}.",
        "next_step": reveal,
        "correct": False,
        "mastery": 0.40 if hint_level < 3 else 0.48,
        "signals": signals,
        "misconception": str(course["misconception"]),
        "citations": [],
        "safety_flags": [],
    }


def record_progress(feedback: Mapping[str, Any], label: str) -> None:
    st.session_state["ml_attempts"] = int(st.session_state.get("ml_attempts", 0)) + 1
    previous = float(st.session_state.get("ml_mastery", DEFAULT_MASTERY))
    score = float(feedback.get("mastery", previous) or previous)
    st.session_state["ml_mastery"] = max(previous, min(0.98, score))
    history = list(st.session_state.get("ml_history", []))
    history.append(
        {
            "label": label,
            "diagnosis": str(feedback.get("title", "Learning signal")),
            "mastery": round(float(st.session_state["ml_mastery"]) * 100),
            "language": active_language_code(),
        }
    )
    st.session_state["ml_history"] = history[-8:]


def add_note(note: str) -> None:
    notes = list(st.session_state.get("ml_notes", []))
    if note and note not in notes:
        notes.append(note)
    st.session_state["ml_notes"] = notes[-8:]


def open_exit_ticket(course_id: str) -> None:
    """Route the teacher brief into Remix before widgets are instantiated."""

    course = get_course(course_id)
    options = [item["id"] for item in available_practice(course)]
    st.session_state["ml_mode"] = MODE_LABELS[2]
    st.session_state["ml_practice_id"] = options[-1]
    st.session_state["ml_feedback"] = None


def _node_by_id(node_id: str, nodes: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    fallback = nodes[min(2, len(nodes) - 1)]
    return next((node for node in nodes if node["id"] == node_id), fallback)


def _node_status(
    node: Mapping[str, Any],
    selected: str,
    mastery: float,
    graph: Mapping[str, Any] | None = None,
) -> str:
    """Return a visible status from the prerequisite graph, not decoration."""

    if node["id"] == selected:
        return "NOW"
    if graph:
        for graph_node in graph.get("nodes", []):
            if graph_node.get("id") == node["id"]:
                return {
                    "mastered": "READY",
                    "active": "NOW",
                    "available": "NEXT",
                    "locked": "LOCKED",
                }.get(str(graph_node.get("status")), "NEXT")
    return "NEXT" if mastery >= 0.5 else "LOCKED"


def render_styles(language_code: str = "en") -> None:
    st.markdown(
        """
        <style>
        :root {
          --canopy-night: #0b1f2a;
          --canopy-pine: #123642;
          --canopy-ink: #10242b;
          --canopy-muted: #6b7f82;
          --canopy-paper: #f7fbf4;
          --canopy-mint: #76f2c0;
          --canopy-coral: #ff897a;
          --canopy-gold: #ffd66e;
          --canopy-violet: #a998ff;
          --canopy-blue: #8edbff;
        }
        .stApp { background: radial-gradient(circle at 10% 0%, rgba(118,242,192,.12), transparent 28rem), radial-gradient(circle at 90% 12%, rgba(169,152,255,.13), transparent 32rem), var(--canopy-night); color: #f6fbf2; }
        [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu { display:none !important; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #102f38 0%, #0b202b 100%); border-right: 1px solid rgba(118,242,192,.18); }
        [data-testid="stSidebar"] * { color: #e8f4ee; }
        .block-container { max-width: 1360px; padding: 2.3rem 3rem 4rem; }
        .canopy-topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:1.1rem; }
        .canopy-brand { display:flex; align-items:center; gap:.65rem; color:#f6fbf2; font-size:1rem; font-weight:850; letter-spacing:-.02em; }
        .canopy-brand small { color:rgba(232,244,238,.6); font-size:.7rem; font-weight:650; letter-spacing:.12em; text-transform:uppercase; }
        .canopy-mark { width:2.25rem; height:2.25rem; display:grid; place-items:center; border-radius:14px 10px 14px 8px; background:linear-gradient(135deg,var(--canopy-mint),var(--canopy-gold)); color:var(--canopy-night); box-shadow:0 0 30px rgba(118,242,192,.22); }
        .canopy-status { border:1px solid rgba(118,242,192,.25); background:rgba(118,242,192,.08); border-radius:999px; padding:.35rem .7rem; color:var(--canopy-mint); font-size:.68rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
        .canopy-hero { position:relative; overflow:hidden; min-height:245px; padding:2rem 2.2rem; margin:.7rem 0 1.25rem; border:1px solid rgba(118,242,192,.23); border-radius:32px 24px 40px 20px; background:linear-gradient(120deg,rgba(21,70,76,.96),rgba(20,47,59,.92) 58%,rgba(40,38,80,.92)); box-shadow:0 22px 80px rgba(0,0,0,.18); }
        .canopy-hero:after { content:""; position:absolute; width:360px; height:360px; right:-90px; top:-150px; border-radius:50%; background:radial-gradient(circle,rgba(255,214,110,.33),rgba(255,137,122,.13) 38%,transparent 68%); filter:blur(8px); animation: canopyDrift 12s ease-in-out infinite alternate; }
        .canopy-hero:before { content:""; position:absolute; width:180px; height:180px; right:23%; bottom:-100px; border-radius:50%; background:rgba(118,242,192,.13); filter:blur(22px); }
        .canopy-hero-content { position:relative; z-index:1; max-width:760px; }
        .canopy-kicker { color:var(--canopy-mint); font-size:.72rem; font-weight:850; letter-spacing:.16em; text-transform:uppercase; }
        .canopy-hero h1 { margin:.45rem 0 .55rem; color:#f8fff7; font-size:clamp(2.4rem,5vw,4.8rem); line-height:.95; letter-spacing:-.07em; }
        .canopy-hero h1 span { color:var(--canopy-gold); }
        .canopy-hero p { max-width:660px; margin:0; color:rgba(238,251,243,.75); font-size:1.04rem; line-height:1.55; }
        .canopy-hero-meta { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.35rem; }
        .canopy-pill { display:inline-flex; align-items:center; gap:.35rem; border:1px solid rgba(255,255,255,.16); border-radius:999px; padding:.38rem .68rem; color:rgba(248,255,247,.84); background:rgba(255,255,255,.07); font-size:.72rem; font-weight:750; }
        .canopy-pill b { color:var(--canopy-gold); }
        .canopy-section-label { color:var(--canopy-mint); font-size:.7rem; font-weight:850; letter-spacing:.14em; text-transform:uppercase; margin:.2rem 0 .5rem; }
        .canopy-section-title { color:#f7fff5; font-size:1.35rem; font-weight:800; letter-spacing:-.035em; margin:0 0 .7rem; }
        .canopy-card { border:1px solid rgba(173,235,213,.17); border-radius:24px 18px 28px 16px; padding:1.2rem 1.3rem; background:rgba(20,54,64,.76); box-shadow:0 12px 40px rgba(0,0,0,.12); }
        .canopy-card.paper { background:var(--canopy-paper); color:var(--canopy-ink); border:0; box-shadow:0 18px 55px rgba(0,0,0,.17); }
        .canopy-card.paper h3, .canopy-card.paper p, .canopy-card.paper span { color:var(--canopy-ink); }
        .canopy-metric { min-height:106px; padding:1rem 1.05rem; border:1px solid rgba(173,235,213,.15); border-radius:18px 14px 22px 12px; background:rgba(19,56,66,.67); }
        .canopy-metric-label { color:rgba(232,244,238,.62); font-size:.7rem; font-weight:750; letter-spacing:.08em; text-transform:uppercase; }
        .canopy-metric-value { margin-top:.28rem; color:#f6fbf2; font-size:1.7rem; font-weight:850; letter-spacing:-.06em; }
        .canopy-metric-note { color:var(--canopy-mint); font-size:.72rem; font-weight:700; }
        .canopy-map { position:relative; overflow:hidden; min-height:230px; margin:.3rem 0 .65rem; padding:1rem; border:1px solid rgba(173,235,213,.16); border-radius:28px 18px 30px 16px; background:linear-gradient(145deg,rgba(18,55,66,.95),rgba(20,41,64,.85)); }
        .canopy-map svg { width:100%; height:auto; display:block; }
        .canopy-map-caption { display:flex; justify-content:space-between; gap:1rem; color:rgba(232,244,238,.6); font-size:.73rem; }
        .canopy-node-note { margin:.3rem 0 .65rem; color:rgba(232,244,238,.68); font-size:.76rem; }
        .canopy-node-status { display:block; margin-top:.2rem; color:rgba(232,244,238,.54); font-size:.63rem; font-weight:800; letter-spacing:.1em; }
        .canopy-focus { display:flex; gap:.8rem; align-items:flex-start; }
        .canopy-focus-icon { flex:0 0 2.5rem; display:grid; place-items:center; height:2.5rem; border-radius:16px 10px 14px 8px; background:linear-gradient(135deg,var(--canopy-coral),var(--canopy-gold)); color:var(--canopy-night); font-size:1.2rem; font-weight:900; }
        .canopy-focus h3 { margin:0; color:#f7fff5; font-size:1.08rem; }
        .canopy-focus p { margin:.2rem 0 0; color:rgba(232,244,238,.67); font-size:.82rem; line-height:1.45; }
        .canopy-teacher { position:relative; overflow:hidden; min-height:180px; border:1px solid rgba(255,214,110,.22); border-radius:24px 15px 28px 13px; padding:1.2rem; background:linear-gradient(145deg,rgba(72,57,88,.94),rgba(30,48,67,.95)); }
        .canopy-teacher:after { content:""; position:absolute; width:110px; height:110px; right:-30px; bottom:-35px; border-radius:50%; background:rgba(255,137,122,.18); filter:blur(12px); }
        .canopy-avatar { display:flex; align-items:center; gap:.55rem; color:#fff; font-weight:850; }
        .canopy-avatar-dot { width:1.7rem; height:1.7rem; display:grid; place-items:center; border-radius:11px 8px 11px 6px; background:var(--canopy-mint); color:var(--canopy-night); font-size:.72rem; }
        .canopy-teacher blockquote { position:relative; z-index:1; margin:1rem 0 0; color:rgba(255,255,255,.79); font-size:.9rem; line-height:1.5; }
        .canopy-equation { display:grid; place-items:center; min-height:72px; margin:.8rem 0; border:1px solid rgba(16,36,43,.08); border-radius:18px 12px 20px 10px; background:#edf6ee; color:var(--canopy-ink); font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:1.55rem; font-weight:850; letter-spacing:.02em; }
        .canopy-equation.dark { border-color:rgba(173,235,213,.15); background:rgba(7,27,35,.42); color:#f8fff7; }
        .canopy-prompt { color:var(--canopy-ink); font-size:.91rem; line-height:1.5; }
        .canopy-prompt.dark { color:rgba(232,244,238,.8); }
        .canopy-step { display:grid; grid-template-columns:2rem 1fr; gap:.75rem; align-items:start; margin:.65rem 0; padding:.8rem; border-left:2px solid rgba(118,242,192,.42); border-radius:0 16px 16px 0; background:rgba(118,242,192,.06); }
        .canopy-step-number { color:var(--canopy-gold); font-weight:900; }
        .canopy-step h4 { margin:0; color:#f7fff5; font-size:.83rem; }
        .canopy-step p { margin:.22rem 0 0; color:rgba(232,244,238,.7); font-size:.78rem; line-height:1.45; }
        .canopy-step-equation { margin-top:.28rem; color:var(--canopy-mint); font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.91rem; font-weight:800; }
        .canopy-feedback { border-radius:21px 14px 24px 12px; padding:1.1rem 1.2rem; border:1px solid rgba(118,242,192,.25); background:rgba(118,242,192,.09); }
        .canopy-feedback.warning { border-color:rgba(255,137,122,.28); background:rgba(255,137,122,.08); }
        .canopy-feedback.info { border-color:rgba(142,219,255,.26); background:rgba(142,219,255,.08); }
        .canopy-feedback h3 { margin:.25rem 0 .35rem; color:#f7fff5; font-size:1.05rem; }
        .canopy-feedback p { margin:0; color:rgba(240,250,243,.78); line-height:1.5; }
        .canopy-signal { color:var(--canopy-mint); font-size:.66rem; font-weight:850; letter-spacing:.12em; text-transform:uppercase; }
        .canopy-quote { margin:.55rem 0; padding:.7rem .85rem; border-left:2px solid var(--canopy-gold); color:rgba(232,244,238,.72); font-size:.78rem; line-height:1.45; }
        .canopy-tool-card { min-height:170px; padding:1.1rem; border:1px solid rgba(173,235,213,.17); border-radius:22px 14px 24px 12px; background:rgba(20,54,64,.64); }
        .canopy-tool-card h4 { margin:0 0 .4rem; color:#f7fff5; font-size:.92rem; }
        .canopy-tool-card p { margin:0; color:rgba(232,244,238,.68); font-size:.79rem; line-height:1.5; }
        .canopy-flashcard { display:grid; place-items:center; min-height:150px; padding:1.3rem; text-align:center; border:1px dashed rgba(255,214,110,.45); border-radius:22px 13px 24px 11px; background:linear-gradient(145deg,rgba(255,214,110,.13),rgba(169,152,255,.1)); }
        .canopy-flashcard strong { color:var(--canopy-gold); font-size:1.05rem; }
        .canopy-flashcard span { color:rgba(240,250,243,.8); font-size:.88rem; line-height:1.45; }
        .canopy-note { padding:.7rem .8rem; margin:.45rem 0; border-radius:13px 8px 14px 7px; background:rgba(255,214,110,.1); color:rgba(240,250,243,.77); font-size:.78rem; }
        .canopy-subject-rail { display:flex; flex-wrap:wrap; gap:.5rem; margin:-.35rem 0 1.3rem; }
        .canopy-subject-chip { display:inline-flex; align-items:center; gap:.38rem; padding:.43rem .72rem; border:1px solid rgba(142,219,255,.16); border-radius:999px; background:rgba(20,54,64,.5); color:rgba(232,244,238,.66); font-size:.72rem; font-weight:760; }
        .canopy-subject-chip.active { border-color:var(--canopy-gold); background:linear-gradient(110deg,rgba(255,214,110,.16),rgba(169,152,255,.13)); color:#fff7d7; box-shadow:0 6px 24px rgba(255,214,110,.08); }
        .canopy-lab-intro { display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; padding:1rem 1.1rem; margin:.3rem 0 .8rem; border:1px solid rgba(142,219,255,.2); border-radius:21px 14px 24px 12px; background:linear-gradient(120deg,rgba(26,73,80,.72),rgba(41,38,78,.62)); }
        .canopy-lab-intro h3 { margin:0; color:#f8fff7; font-size:1.05rem; }
        .canopy-lab-intro p { margin:.3rem 0 0; color:rgba(232,244,238,.7); font-size:.8rem; line-height:1.45; }
        .canopy-lab-badge { flex:0 0 auto; border:1px solid rgba(118,242,192,.3); border-radius:999px; padding:.38rem .62rem; color:var(--canopy-mint); background:rgba(118,242,192,.08); font-size:.65rem; font-weight:850; letter-spacing:.08em; text-transform:uppercase; }
        .canopy-lab-metric { min-height:88px; padding:.78rem .85rem; border:1px solid rgba(173,235,213,.13); border-radius:16px 10px 18px 9px; background:rgba(7,27,35,.42); }
        .canopy-lab-metric strong { display:block; color:#f6fbf2; font-size:1.25rem; letter-spacing:-.03em; }
        .canopy-lab-metric span { color:rgba(232,244,238,.55); font-size:.64rem; font-weight:780; letter-spacing:.08em; text-transform:uppercase; }
        .canopy-lab-metric small { display:block; margin-top:.18rem; color:var(--canopy-mint); font-size:.65rem; line-height:1.25; }
        [data-testid="stPlotlyChart"] { overflow:hidden; border:1px solid rgba(142,219,255,.2); border-radius:28px 17px 31px 14px; background:radial-gradient(circle at 30% 15%,rgba(118,242,192,.07),transparent 32rem),rgba(7,27,35,.48); box-shadow:0 18px 60px rgba(0,0,0,.16); }
        .stButton > button { min-height:2.55rem; border:1px solid rgba(173,235,213,.18); border-radius:13px 9px 14px 8px; background:rgba(31,75,80,.72); color:#f5fff7; font-weight:780; transition:transform .16s ease, border-color .16s ease, box-shadow .16s ease; }
        .stButton > button:hover { transform:translateY(-2px); border-color:var(--canopy-mint); color:#fff; box-shadow:0 8px 22px rgba(118,242,192,.15); }
        .stButton > button[kind="primary"] { border-color:rgba(118,242,192,.55); background:linear-gradient(100deg,#2a9f86,#4b7ed1); }
        div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input { border:1px solid rgba(173,235,213,.25); border-radius:14px 9px 15px 8px; background:rgba(7,27,35,.45); color:#f7fff5; }
        div[data-testid="stTextArea"] textarea:focus, div[data-testid="stTextInput"] input:focus { border-color:var(--canopy-mint); box-shadow:0 0 0 1px var(--canopy-mint); }
        div[data-testid="stRadio"] > div { gap:.45rem; }
        div[data-testid="stRadio"] label { border:1px solid rgba(173,235,213,.16); border-radius:999px; padding:.35rem .7rem; background:rgba(20,54,64,.55); }
        div[data-testid="stRadio"] label:has(input:checked) { border-color:var(--canopy-mint); background:rgba(118,242,192,.13); }
        div[data-testid="stMetric"] { border:0; }
        div[data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,var(--canopy-coral),var(--canopy-gold),var(--canopy-mint)); }
        [data-testid="stExpander"] { border-color:rgba(173,235,213,.18); border-radius:17px 10px 19px 9px; background:rgba(20,54,64,.4); }
        [data-testid="stTabs"] button { color:rgba(232,244,238,.68); }
        [data-testid="stTabs"] button[aria-selected="true"] { color:var(--canopy-mint); }
        @keyframes canopyDrift { from { transform:translate3d(0,0,0) scale(1); } to { transform:translate3d(-24px,22px,0) scale(1.09); } }
        @media (prefers-reduced-motion: reduce) { *, *:before, *:after { animation:none !important; transition:none !important; scroll-behavior:auto !important; } }
        @media (max-width: 900px) { .block-container { padding:1.4rem 1rem 3rem; } .canopy-hero { padding:1.5rem; } .canopy-hero h1 { font-size:2.7rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
    direction = "rtl" if is_rtl(language_code) else "ltr"
    text_align = "right" if direction == "rtl" else "left"
    directional_css = (
        "<style>"
        f".stApp, [data-testid='stSidebar'] {{ direction:{direction}; text-align:{text_align}; }}"
        ".stApp, .stApp button, .stApp input, .stApp textarea, .stApp select {"
        "font-family:Inter,'Noto Sans','Noto Sans Arabic','Noto Sans Devanagari',"
        "'Noto Sans Bengali','Noto Sans Telugu',system-ui,sans-serif;}"
        ".canopy-equation, .canopy-step-equation, [data-testid='stPlotlyChart'],"
        "[data-testid='stPlotlyChart'] *, input[type='range'], svg {"
        "direction:ltr !important; unicode-bidi:isolate; text-align:left;}"
        f"div[data-testid='stTextArea'] textarea, div[data-testid='stTextInput'] input {{direction:{direction}; text-align:{text_align};}}"
        "</style>"
    )
    st.markdown(directional_css, unsafe_allow_html=True)


def render_topbar(language_code: str = "en") -> None:
    st.markdown(
        f"""
        <div class="canopy-topbar">
          <div class="canopy-brand">
            <span class="canopy-mark">✦</span>
            <span>CANOPY <small>{html.escape(tr('language', language_code))} · AI</small></span>
          </div>
          <span class="canopy-status">● {html.escape(tr('teacher_ready', language_code))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(course: Mapping[str, Any], academy: Mapping[str, Any], language_code: str = "en") -> None:
    locale = get_language(language_code)
    st.markdown(
        f"""
        <section class="canopy-hero" lang="{html.escape(locale['bcp47'])}" dir="{locale['direction']}">
          <div class="canopy-hero-content">
            <div class="canopy-kicker">{html.escape(str(academy['label']))} · {html.escape(str(course['subject']))}</div>
            <h1>{html.escape(str(course['title']))} <span>✦</span></h1>
            <p>{html.escape(str(course['big_question']))}</p>
            <div class="canopy-hero-meta">
              <span class="canopy-pill"><b>{html.escape(str(course['icon']))}</b> {html.escape(str(course['age_band']).replace('Grades ', ''))}</span>
              <span class="canopy-pill"><b>3D</b> {html.escape(tr('interactive_lab', language_code))}</span>
              <span class="canopy-pill"><b>∞</b> {html.escape(tr('model', language_code))} → {html.escape(tr('evidence', language_code))} → {html.escape(get_stages(language_code)[-1])}</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_subject_rail(course: Mapping[str, Any], language_code: str = "en") -> None:
    chips = []
    for candidate in get_courses(str(course["academy"])):
        active = " active" if candidate["id"] == course["id"] else ""
        subject, _title = course_label(str(candidate["id"]), language_code)
        chips.append(
            f"<span class='canopy-subject-chip{active}'>{html.escape(str(candidate['icon']))} {html.escape(subject)}</span>"
        )
    st.markdown(f"<div class='canopy-subject-rail'>{''.join(chips)}</div>", unsafe_allow_html=True)


def render_sidebar(mode: str, settings: Mapping[str, str | bool], lens: str) -> Mapping[str, Any]:
    with st.sidebar:
        st.markdown("## ✦ Canopy")
        languages = get_languages()
        language_codes = [language["code"] for language in languages]
        language_options = [language_option(language) for language in languages]
        current_language = active_language_code()
        selected_language_option = st.selectbox(
            tr("choose_language", current_language),
            language_options,
            index=language_codes.index(current_language),
        )
        selected_language = language_codes[language_options.index(str(selected_language_option))]
        if selected_language != current_language:
            st.session_state["ml_language"] = selected_language
            st.session_state["ml_last_language"] = selected_language
            st.session_state["ml_feedback"] = None
            st.session_state["ml_explain_step"] = 0
            rerun()
        language_code = str(selected_language)
        if language_code != "en":
            st.toggle(tr("show_english", language_code), key="ml_show_english")
            st.caption(f"◌ {tr('translation_beta', language_code)}")
        st.caption(f"20× {tr('language', language_code)} · 2× {tr('academy', language_code)} · 9× {tr('course', language_code)}")
        st.markdown(f"### {tr('academy', language_code)}")
        academies = get_academies()
        academy_ids = [str(academy["id"]) for academy in academies]
        academy_lookup = {str(academy["id"]): academy for academy in academies}
        current_academy = str(st.session_state.get("ml_academy", "stem"))
        if current_academy not in academy_ids:
            current_academy = "stem"
        selected_academy = st.radio(
            tr("academy", language_code),
            academy_ids,
            index=academy_ids.index(current_academy),
            format_func=lambda value: f"{academy_lookup[value]['icon']} {academy_label(value, language_code)}",
            label_visibility="collapsed",
        )
        st.caption(academy_description(str(selected_academy), language_code))
        courses = get_courses(selected_academy)
        course_ids = [str(course["id"]) for course in courses]
        course_lookup = {str(candidate["id"]): candidate for candidate in courses}
        current_course = str(st.session_state.get("ml_course_id", ""))
        if current_course not in course_ids:
            current_course = default_course_id(selected_academy)
        selected_course = st.selectbox(
            f"{tr('course', language_code)} · {academy_label(str(selected_academy), language_code)}",
            course_ids,
            index=course_ids.index(current_course),
            format_func=lambda value: (
                f"{course_lookup[value]['icon']} {course_label(value, language_code)[0]} · "
                f"{course_label(value, language_code)[1]}"
            ),
        )
        st.session_state["ml_academy"] = selected_academy
        course = activate_course(str(selected_course))
        nodes = course_nodes(localize_course(course, language_code))
        st.divider()
        if mode == "demo":
            status_suffix = "offline" if language_code == "en" else "◌"
            st.success(f"{tr('teacher_ready', language_code)} · {status_suffix}")
            st.caption(tr("translation_beta", language_code) if language_code != "en" else "No key or model download · browser rendered")
        else:
            status_suffix = "live" if language_code == "en" else "●"
            st.info(f"{tr('teacher_ready', language_code)} · {status_suffix}")
        st.markdown(f"### {tr('teacher_read', language_code)}")
        lens_options = ("Visual and patient", "Challenge me", "Short and direct", "Ask me to teach it")
        lens_labels = {
            lens_options[0]: tr("learn", language_code),
            lens_options[1]: tr("experiment", language_code),
            lens_options[2]: tr("model", language_code),
            lens_options[3]: tr("explanation", language_code),
        }
        if lens not in lens_options:
            st.session_state["ml_lens"] = lens_options[0]
        st.selectbox(
            tr("teacher_read", language_code),
            lens_options,
            key="ml_lens",
            format_func=lambda value: lens_labels[value],
            label_visibility="collapsed",
        )
        st.markdown(f"### {tr('learning_signal', language_code)}")
        mastery = float(st.session_state.get("ml_mastery", DEFAULT_MASTERY))
        graph = learning_graph(mastery, nodes)
        st.progress(max(0.0, min(1.0, mastery)))
        st.caption(
            f"{round(mastery * 100):d}% {tr('teacher_ready', language_code)} · "
            f"{st.session_state.get('ml_attempts', 0)} {tr('learning_signal', language_code)}"
        )
        st.markdown(f"### {tr('learning_map', language_code)}")
        for node in nodes:
            status = _node_status(node, str(st.session_state.get("ml_selected_node", nodes[2]["id"])), mastery, graph)
            icon = "●" if status == "READY" else "◉" if status == "NOW" else "○"
            st.markdown(f"{icon} **{node['short']}**")
        st.divider()
        if bool(settings.get("ready")):
            engine_options = ("Demo · deterministic", "Live · optional")
            st.radio(
                tr("teacher_ready", language_code),
                engine_options,
                key="ml_engine",
                format_func=lambda value: (
                    value
                    if language_code == "en"
                    else f"{tr('model', language_code)} · {engine_options.index(value) + 1}"
                ),
            )
        else:
            status_prefix = "offline" if language_code == "en" else "◌"
            st.caption(f"{status_prefix} · {tr('teacher_ready', language_code)}")
        if st.button(f"↺ {tr('reset_model', language_code)}", width="stretch", key="ml_reset_sidebar"):
            reset_state()
            rerun()
    return course


def render_metrics(
    course: Mapping[str, Any],
    nodes: tuple[dict[str, Any], ...],
    language_code: str = "en",
) -> None:
    mastery = float(st.session_state.get("ml_mastery", DEFAULT_MASTERY))
    attempts = int(st.session_state.get("ml_attempts", 0))
    graph = learning_graph(mastery, nodes)
    ready_nodes = sum(1 for node in graph.get("nodes", []) if node.get("status") in {"mastered", "available"})
    streak = min(4, max(0, attempts))
    columns = st.columns(4)
    values = (
        (tr("teacher_ready", language_code), f"{round(mastery * 100):d}%", tr("learning_signal", language_code)),
        (tr("experiment", language_code), str(streak), tr("inquiry", language_code)),
        (tr("learning_map", language_code), f"{ready_nodes}/{len(nodes)}", get_stages(language_code)[-1]),
        (tr("course", language_code), str(course["subject"]), academy_label(str(course["academy"]), language_code)),
    )
    for column, (label, value, note) in zip(columns, values):
        with column:
            st.markdown(
                f"<div class='canopy-metric'><div class='canopy-metric-label'>{label}</div><div class='canopy-metric-value'>{value}</div><div class='canopy-metric-note'>{note}</div></div>",
                unsafe_allow_html=True,
            )


def render_interactive_lab(course: Mapping[str, Any], language_code: str = "en") -> None:
    """Render a course-native visual model and its investigation controls."""

    show_english = language_code != "en" and bool(st.session_state.get("ml_show_english", False))
    st.markdown(
        f"<div class='canopy-section-label' style='margin-top:1.6rem'>{html.escape(tr('interactive_lab', language_code))}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div class='canopy-section-title'>{html.escape(tr('lab_title', language_code))}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='canopy-lab-intro'><div><h3>{html.escape(str(course['subtitle']))}</h3><p>{html.escape(str(course['transfer_prompt']))}</p></div><span class='canopy-lab-badge'>3D · {html.escape(tr('experiment', language_code))} · {html.escape(tr('evidence', language_code))}</span></div>",
        unsafe_allow_html=True,
    )
    st.button(
        f"↺ {tr('reset_model', language_code)}",
        key=f"ml_reset_lab_{course['id']}",
        on_click=reset_visual_lab,
        args=(str(course["id"]), language_code),
    )
    specs = lab_control_specs(course)
    controls = st.columns(len(specs))
    values: dict[str, LabValue] = {}
    for index, (column, spec) in enumerate(zip(controls, specs), start=1):
        widget_key = f"ml_lab_{course['id']}_{spec['key']}_{language_code}"
        control_label = str(spec["label"])
        if language_code != "en":
            control_label = f"{tr('parameter', language_code)} {index}"
            if show_english:
                control_label += f" · {spec['label']}"
        control_help = str(spec["help"]) if language_code == "en" or show_english else tr("node_hint", language_code)
        with column:
            if spec["kind"] == "select":
                options = list(spec.get("options", []))
                if st.session_state.get(widget_key) not in options:
                    st.session_state[widget_key] = spec["default"]
                values[spec["key"]] = st.selectbox(
                    control_label,
                    options,
                    key=widget_key,
                    help=control_help,
                    format_func=lambda value: (
                        f"{lab_option_label(value, language_code)} · {value}"
                        if show_english
                        else lab_option_label(value, language_code)
                    ),
                )
            else:
                default = spec["default"]
                integral = isinstance(default, int) and not isinstance(default, bool)
                minimum = spec.get("minimum", 0.0)
                maximum = spec.get("maximum", 1.0)
                step = spec.get("step", 1.0 if integral else 0.1)
                if widget_key not in st.session_state:
                    st.session_state[widget_key] = int(default) if integral else float(default)
                values[spec["key"]] = st.slider(
                    control_label,
                    min_value=int(minimum) if integral else float(minimum),
                    max_value=int(maximum) if integral else float(maximum),
                    step=int(step) if integral else float(step),
                    key=widget_key,
                    help=control_help,
                    format=spec.get("format", "%d" if integral else "%.2f"),
                )
    figure = build_lab_figure(course, values, language_code)
    st.plotly_chart(
        figure,
        width="stretch",
        key=f"ml_plot_{course['id']}_{language_code}",
        config={
            "displaylogo": False,
            "displayModeBar": language_code == "en",
            "responsive": True,
            "scrollZoom": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        },
    )
    metrics = lab_metrics(course, values, language_code)
    metric_columns = st.columns(len(metrics))
    for index, (column, (label, value, help_text)) in enumerate(zip(metric_columns, metrics), start=1):
        metric_label = label if language_code == "en" else f"{tr('result', language_code)} {index}"
        metric_help = help_text if language_code == "en" or show_english else tr("evidence", language_code)
        with column:
            st.markdown(
                f"<div class='canopy-lab-metric'><span>{html.escape(metric_label)}</span><strong>{html.escape(value)}</strong><small>{html.escape(metric_help)}</small></div>",
                unsafe_allow_html=True,
            )
    insight = lab_insight(course, values, language_code)
    st.markdown(
        f"<div class='canopy-quote'><strong>{html.escape(tr('teacher_read', language_code))}:</strong> {html.escape(insight)}</div>",
        unsafe_allow_html=True,
    )
    if show_english:
        st.caption(f"EN · {lab_insight(course, values, 'en')}")
    with st.expander(f"{tr('inquiry', language_code)} · {tr('prediction', language_code)} → {tr('experiment', language_code)} → {tr('explanation', language_code)}", expanded=False):
        st.caption(tr("node_hint", language_code))
        hypothesis_key = f"ml_hypothesis_{course['id']}"
        st.text_input(tr("prediction", language_code), key=hypothesis_key, placeholder=f"{tr('prediction', language_code)}…")
        if st.button(f"＋ {tr('prediction', language_code)}", key=f"ml_pin_hypothesis_{course['id']}"):
            hypothesis = str(st.session_state.get(hypothesis_key, "")).strip()
            if hypothesis:
                add_note(f"{course['subject']} · {tr('prediction', language_code)}: {hypothesis}")
                st.toast(f"{tr('prediction', language_code)} · ✓")
            else:
                st.warning(tr("node_hint", language_code))


def render_learning_map(
    selected_id: str,
    mastery: float,
    nodes: tuple[dict[str, Any], ...],
    language_code: str = "en",
) -> None:
    """Render a lightweight visual graph with native keyboard-accessible controls."""

    graph = learning_graph(mastery, nodes)
    graph_nodes = {str(node.get("id")): node for node in graph.get("nodes", [])}
    y_positions = (104, 52, 124, 50, 122, 54)
    points = {
        str(node["id"]): (74 + index * 154, y_positions[index % len(y_positions)])
        for index, node in enumerate(nodes)
    }
    palette = {"mint": "#76f2c0", "gold": "#ffd66e", "coral": "#ff897a", "violet": "#a998ff", "blue": "#8edbff"}
    edge_specs = [
        (str(edge.get("source")), str(edge.get("target")))
        for edge in graph.get("edges", [])
        if str(edge.get("source")) in points and str(edge.get("target")) in points
    ]
    paths: list[str] = []
    for source, target in edge_specs:
        x1, y1 = points[source]
        x2, y2 = points[target]
        source_state = str(graph_nodes.get(source, {}).get("status", "locked"))
        edge_class = "canopy-edge-done" if source_state == "mastered" else "canopy-edge"
        paths.append(
            f"<path class='{edge_class}' d='M {x1} {y1} C {(x1 + x2) / 2:.0f} {y1 - 38:.0f}, {(x1 + x2) / 2:.0f} {y2 + 38:.0f}, {x2} {y2}' fill='none' stroke-width='2' stroke-dasharray='5 8'/>"
        )
    node_markup: list[str] = []
    for node in nodes:
        node_id = str(node["id"])
        x, y = points[node_id]
        status = str(graph_nodes.get(node_id, {}).get("status", "locked"))
        accent = palette.get(str(node["color"]), "#76f2c0")
        radius = 18 if node_id == selected_id else 14
        opacity = 1 if node_id == selected_id else .78 if status != "locked" else .48
        node_markup.append(
            f"<g><circle cx='{x}' cy='{y}' r='{radius}' fill='{accent}' opacity='{opacity}'/><circle cx='{x}' cy='{y}' r='{radius + 9}' fill='none' stroke='{accent}' opacity='.24' stroke-width='2'/><text x='{x}' y='{y + 5}' text-anchor='middle' font-size='12' font-weight='800' fill='#0b1f2a'>{html.escape(str(node['icon']))}</text><text x='{x}' y='{y + 42}' text-anchor='middle' font-size='10' font-weight='800' fill='#dcefe6'>{html.escape(str(node['short']))}</text></g>"
        )
    st.markdown(
        f"""
        <div class="canopy-map">
          <svg viewBox="0 0 900 175" role="img" aria-label="{html.escape(tr('learning_map', language_code))}">
            <defs><linearGradient id="canopyLine" x1="0" x2="1"><stop offset="0" stop-color="#76f2c0"/><stop offset="1" stop-color="#a998ff"/></linearGradient></defs>
            {''.join(paths).replace("class='canopy-edge'", "class='canopy-edge'").replace("stroke-width='2'", "stroke='url(#canopyLine)' stroke-width='2'")}
            {''.join(node_markup)}
          </svg>
          <div class="canopy-map-caption"><span>{html.escape(tr('learning_map', language_code))}</span><span>{round(float(graph.get('completion_percent', mastery * 100))):d}%</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    node_columns = st.columns(len(nodes))
    for column, node in zip(node_columns, nodes):
        with column:
            label = f"{node['icon']} {node['short']}"
            if st.button(label, width="stretch", key=f"ml_node_{node['id']}"):
                st.session_state["ml_selected_node"] = node["id"]
                st.session_state["ml_feedback"] = None
                st.session_state["ml_explain_step"] = 0
                rerun()
            node_status = _node_status(node, selected_id, mastery, graph)
            status_display = node_status if language_code == "en" else {
                "READY": "●",
                "NOW": "◉",
                "NEXT": "○",
                "LOCKED": "◇",
            }.get(node_status, "○")
            st.markdown(
                f"<span class='canopy-node-status'>{status_display}</span>",
                unsafe_allow_html=True,
            )


def render_focus_and_teacher(
    node: Mapping[str, Any],
    course: Mapping[str, Any],
    language_code: str = "en",
) -> None:
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown(f"<div class='canopy-section-label'>{html.escape(tr('current_focus', language_code))}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='canopy-card'><div class='canopy-focus'><div class='canopy-focus-icon'>{html.escape(str(node['icon']))}</div><div><h3>{html.escape(str(node['label']))}</h3><p>{html.escape(str(node['description']))}</p></div></div></div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(f"<div class='canopy-section-label'>{html.escape(tr('teacher_read', language_code))}</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='canopy-teacher'><div class='canopy-avatar'><span class='canopy-avatar-dot'>✦</span> Canopy · {html.escape(str(course['subject']))}</div><blockquote>{html.escape(str(course['misconception']))}<br><br>{html.escape(tr('node_hint', language_code))}</blockquote></div>",
            unsafe_allow_html=True,
        )


def render_feedback(feedback: Mapping[str, Any] | None, language_code: str = "en") -> None:
    if not feedback:
        st.markdown(
            f"<div class='canopy-feedback info'><div class='canopy-signal'>{html.escape(tr('learning_signal', language_code))} · {html.escape('READY' if language_code == 'en' else tr('teacher_ready', language_code))}</div><h3>{html.escape(tr('teacher_listening', language_code))}</h3><p>{html.escape(tr('feedback_start', language_code))}</p></div>",
            unsafe_allow_html=True,
        )
        return
    kind = str(feedback.get("kind", "info"))
    title = html.escape(str(feedback.get("title", "Learning signal")))
    body = str(feedback.get("body", ""))
    next_step = html.escape(str(feedback.get("next_step", "")))
    st.markdown(
        f"<div class='canopy-feedback {kind}'><div class='canopy-signal'>{html.escape(tr('learning_signal', language_code))}</div><h3>{title}</h3><p>{html.escape(body)}</p><div class='canopy-quote'><strong>{html.escape(tr('next_question', language_code))}:</strong> {next_step}</div></div>",
        unsafe_allow_html=True,
    )
    flags = feedback.get("safety_flags", [])
    if flags:
        visible_flags = [str(flag) for flag in flags if str(flag) != "multilingual_structure_only"]
        if visible_flags and language_code == "en":
            st.caption("Safety boundary: " + ", ".join(visible_flags))
        elif language_code != "en":
            st.caption(f"{tr('beta_short', language_code)} · {tr('learning_signal', language_code)}")


def render_sources(
    lesson: Mapping[str, Any],
    feedback: Mapping[str, Any] | None,
    language_code: str = "en",
) -> None:
    raw_citations = feedback.get("citations", []) if isinstance(feedback, Mapping) else []
    if isinstance(raw_citations, list) and raw_citations and all(isinstance(item, Mapping) for item in raw_citations):
        with st.expander(f"{tr('sources', language_code)} · {tr('evidence', language_code)}", expanded=False):
            st.caption(
                "Citations below are copied from the local lesson chunks used for this response."
                if language_code == "en"
                else f"{tr('sources', language_code)} · {tr('course', language_code)} · {tr('evidence', language_code)}"
            )
            for index, citation in enumerate(raw_citations, start=1):
                heading = citation.get("heading") or "Lesson passage"
                source = citation.get("source") or "local lesson"
                quote = citation.get("quote") or ""
                if language_code != "en" and not bool(st.session_state.get("ml_show_english", False)):
                    heading = f"{tr('sources', language_code)} {index}"
                    quote = tr("evidence", language_code)
                st.markdown(f"**{index}. {heading}**")
                st.caption(f"{source} · {quote}")
        return
    with st.expander(f"{tr('sources', language_code)} · {tr('evidence', language_code)}", expanded=False):
        st.caption(tr("translation_beta", language_code) if language_code != "en" else "Inspectable course evidence")
        for citation in lesson["citations"]:
            st.markdown(f"**{citation['label']}** — {citation['supports']} [↗]({citation['url']})")


def render_english_reference(
    raw_course: Mapping[str, Any],
    raw_node: Mapping[str, Any],
    language_code: str,
) -> None:
    """Expose canonical English alongside, never instead of, localised content."""

    if language_code == "en" or not bool(st.session_state.get("ml_show_english", False)):
        return
    with st.expander(f"EN · {tr('english_reference', language_code)}", expanded=False):
        st.markdown(f"**{raw_course['subject']} · {raw_course['title']}**")
        st.write(str(raw_course["big_question"]))
        st.markdown(f"**{raw_node['label']}**")
        st.write(str(raw_node["question"]))
        st.caption(str(raw_node["hint"]))


def render_balance_lab() -> None:
    """Make the core reasoning loop a real interaction, not only a text box."""

    st.markdown("### Interactive balance lab")
    st.caption("Choose the next legal move. The teacher reacts to the move itself.")
    step = int(st.session_state.get("ml_builder_step", 0))
    equations = ("3x + 5 = 20", "3x = 15", "x = 5")
    st.markdown(f"<div class='canopy-equation'>{equations[min(step, 2)]}</div>", unsafe_allow_html=True)
    if step == 0:
        st.markdown("<p class='canopy-prompt dark'>What should happen first to keep the equation level?</p>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            if st.button("Subtract 5 from both sides", type="primary", width="stretch", key="ml_move_subtract"):
                st.session_state["ml_builder_step"] = 1
                st.session_state["ml_builder_signal"] = "Exactly. The same subtraction reveals the x-term without changing the equality."
                rerun()
        with right:
            if st.button("Divide by 3 first", width="stretch", key="ml_move_divide_first"):
                st.session_state["ml_builder_errors"] = int(st.session_state.get("ml_builder_errors", 0)) + 1
                st.session_state["ml_builder_signal"] = "Not yet. The +5 is still attached to 3x, so dividing now mixes two operations."
                rerun()
    elif step == 1:
        st.markdown("<p class='canopy-prompt dark'>Now the constant is gone. What operation is still attached to x?</p>", unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            if st.button("Divide both sides by 3", type="primary", width="stretch", key="ml_move_divide"):
                st.session_state["ml_builder_step"] = 2
                st.session_state["ml_builder_signal"] = "Yes. Dividing both sides by 3 isolates x; now a substitution check can defend the result."
                rerun()
        with right:
            if st.button("Subtract 5 again", width="stretch", key="ml_move_subtract_again"):
                st.session_state["ml_builder_errors"] = int(st.session_state.get("ml_builder_errors", 0)) + 1
                st.session_state["ml_builder_signal"] = "The +5 has already been removed. Look for the operation that is still touching x."
                rerun()
    else:
        st.success("Balanced path complete · x is isolated")
        st.markdown("<p class='canopy-prompt dark'>You changed both sides twice and preserved the meaning of the equation. Try the same move on a remix.</p>", unsafe_allow_html=True)
        if not st.session_state.get("ml_builder_recorded"):
            record_progress({"mastery": 0.78, "title": "Interactive balance lab complete"}, "Interactive · balance lab")
            st.session_state["ml_builder_recorded"] = True
    signal = str(st.session_state.get("ml_builder_signal", ""))
    if signal:
        st.info(signal)
    error_count = int(st.session_state.get("ml_builder_errors", 0))
    if error_count:
        st.caption(f"Teacher memory · {error_count} move{'s' if error_count != 1 else ''} to revisit")
    if st.button("Reset move lab", width="content", key="ml_reset_builder"):
        st.session_state["ml_builder_step"] = 0
        st.session_state["ml_builder_errors"] = 0
        st.session_state["ml_builder_signal"] = ""
        st.session_state["ml_builder_recorded"] = False
        rerun()


def render_coach(
    node: Mapping[str, Any],
    course: Mapping[str, Any],
    _settings: Mapping[str, str | bool],
    _mode: str,
    language_code: str = "en",
) -> None:
    st.markdown(f"<div class='canopy-section-label'>01 · {html.escape(tr('coach', language_code))}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='canopy-section-title'>{html.escape(tr('course_invite', language_code).format(title=str(course['title'])))}</div>",
        unsafe_allow_html=True,
    )
    hint_columns = st.columns(3)
    hint_copy = (
        (1, f"1 · {tr('question', language_code)}", tr("prediction", language_code)),
        (2, f"2 · {tr('evidence', language_code)}", tr("node_hint", language_code)),
        (3, f"3 · {tr('model', language_code)}", tr("explanation", language_code)),
    )
    for column, (level, label, description) in zip(hint_columns, hint_copy):
        with column:
            if st.button(label, width="stretch", key=f"ml_hint_level_{level}"):
                st.session_state["ml_hint_level"] = level
            selected = st.session_state.get("ml_hint_level") == level
            st.caption(("● " if selected else "○ ") + description)
    with st.container(border=True):
        left, right = st.columns([1.2, .8], gap="large")
        with left:
            st.markdown(f"### {tr('question', language_code)}")
            st.markdown(f"<div class='canopy-equation'>{html.escape(str(node['equation']))}</div>", unsafe_allow_html=True)
            st.markdown(f"<p class='canopy-prompt dark'>{html.escape(str(node['question']))}</p>", unsafe_allow_html=True)
            st.caption(f"{tr('learning_signal', language_code)} · {st.session_state.get('ml_hint_level', 1)}")
        with right:
            st.markdown(f"### {tr('node_hint', language_code)}")
            st.markdown(f"<div class='canopy-card'><p class='canopy-prompt dark'>{html.escape(str(node['hint']))}</p></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='canopy-quote'>{html.escape(tr('node_hint', language_code))}</div>", unsafe_allow_html=True)
    quick_left, quick_mid, quick_right = st.columns(3)
    quick_actions = (
        (quick_left, tr("question", language_code), f"{tr('question', language_code)}: ", "ml_quick_unsure"),
        (quick_mid, tr("prediction", language_code), f"{tr('prediction', language_code)}: ", "ml_quick_first"),
        (quick_right, tr("model", language_code), f"{tr('model', language_code)}: ", "ml_quick_lens"),
    )
    for column, label, value, key in quick_actions:
        with column:
            if st.button(label, width="stretch", key=key):
                st.session_state["ml_answer"] = value
                rerun()
    with st.form("ml_coach_form", clear_on_submit=False):
        st.text_area(
            tr("your_thinking", language_code),
            key="ml_answer",
            height=130,
            placeholder=f"{tr('explanation', language_code)} · {course['subject']} · {tr('evidence', language_code)}…",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(f"{tr('check_reasoning', language_code)} ↗", type="primary", width="stretch")
    if submitted:
        diagnosis = domain_diagnose(
            course,
            str(st.session_state.get("ml_answer", "")),
            node,
            int(st.session_state.get("ml_hint_level", 1)),
            language_code,
        )
        st.session_state["ml_feedback"] = diagnosis
        record_progress(diagnosis, f"{tr('coach', language_code)} · {node['short']}")
        rerun()
    render_feedback(st.session_state.get("ml_feedback"), language_code)
    current_feedback = st.session_state.get("ml_feedback")
    if isinstance(current_feedback, Mapping) and current_feedback.get("signals"):
        st.caption(f"{tr('learning_signal', language_code)} · " + " · ".join(str(signal) for signal in current_feedback["signals"]))


def render_explain(node: Mapping[str, Any], course: Mapping[str, Any], language_code: str = "en") -> None:
    st.markdown(f"<div class='canopy-section-label'>02 · {html.escape(tr('learn', language_code))}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='canopy-section-title'>{html.escape(tr('explanation', language_code))} · {html.escape(str(course['title']))}</div>", unsafe_allow_html=True)
    lenses = (tr("model", language_code), tr("evidence", language_code), tr("explanation", language_code))
    lens = st.selectbox(
        tr("explanation", language_code),
        lenses,
        key=f"ml_explain_lens_{course['id']}",
        label_visibility="collapsed",
    )
    st.markdown(
        f"<div class='canopy-card'><div class='canopy-signal'>{html.escape(lens).upper()}</div><div class='canopy-equation dark'>{html.escape(str(node['equation']))}</div><p class='canopy-prompt dark'>{html.escape(str(node['description']))}</p></div>",
        unsafe_allow_html=True,
    )
    steps = node["explain_steps"]
    step_count = int(st.session_state.get("ml_explain_step", 0))
    reveal_col, save_col = st.columns([1, 1])
    with reveal_col:
        if st.button(f"{tr('explanation', language_code)} →", type="primary", width="stretch", key="ml_reveal_step"):
            st.session_state["ml_explain_step"] = min(len(steps), step_count + 1)
            rerun()
    with save_col:
        if st.button(f"＋ {tr('toolkit', language_code)}", width="stretch", key="ml_save_explanation"):
            add_note(f"{node['label']}: {steps[min(step_count, len(steps) - 1)][2]}")
            st.toast(f"{tr('toolkit', language_code)} · ✓")
    if step_count == 0:
        st.info(str(course["big_question"]))
    for index, (title, equation, body) in enumerate(steps[:step_count], start=1):
        st.markdown(
            f"<div class='canopy-step'><div class='canopy-step-number'>0{index}</div><div><h4>{html.escape(title)}</h4><div class='canopy-step-equation'>{html.escape(equation)}</div><p>{html.escape(body)}</p></div></div>",
            unsafe_allow_html=True,
        )
    if step_count >= len(steps):
        st.success(tr("transfer", language_code).format(title=str(course["title"])))


def _canonical_answer(value: object) -> str:
    """Normalize short practice answers without hiding meaningful operators."""

    return re.sub(r"\s+", "", str(value or "").lower().replace("−", "-").replace("×", "*"))


def practice_diagnose(
    answer: str,
    practice: Mapping[str, Any],
    settings: Mapping[str, str | bool],
    mode: str,
    language_code: str = "en",
) -> dict[str, Any]:
    """Grade mixed numeric, symbolic, and explanation remixes deterministically."""

    locale = get_language(language_code)["code"]
    normalized = _canonical_answer(answer)
    accepted = [_canonical_answer(item) for item in practice.get("accepted_answers", [])]
    if not accepted:
        accepted = [_canonical_answer(practice.get("answer", ""))]
    if normalized and any(candidate == normalized or candidate in normalized for candidate in accepted):
        return {
            "kind": "success",
            "title": tr("feedback_strong", locale),
            "body": str(practice.get("explanation") or "Your response matches the target structure. Explain why the move works, then try the transfer prompt."),
            "next_step": str(practice.get("transfer") or "How would this strategy change in a new context?"),
            "correct": True,
            "mastery": min(0.92, 0.48 + float(practice.get("difficulty", 1)) * 0.12),
            "citations": [],
            "safety_flags": [],
        }
    if locale != "en":
        hints = practice.get("hint_ladder", [])
        hint = str(hints[0]) if isinstance(hints, (list, tuple)) and hints else tr("node_hint", locale)
        return multilingual_diagnose(
            answer,
            str(practice.get("question", "")),
            hint,
            locale,
        )
    required_terms = [str(term) for term in practice.get("required_terms", []) if str(term).strip()]
    if required_terms:
        matched_terms = [term for term in required_terms if _term_present(answer, term)]
        missing_terms = [term for term in required_terms if term not in matched_terms]
        threshold = max(2, (len(required_terms) * 3 + 4) // 5)
        if len(matched_terms) >= threshold:
            return {
                "kind": "success",
                "title": "Transfer signal · the reasoning travelled",
                "body": f"Your response uses {', '.join(matched_terms)} to connect the prompt with a defensible model. {practice.get('explanation', '')}",
                "next_step": str(practice.get("transfer") or "What changes in a new context?"),
                "correct": True,
                "mastery": min(0.94, 0.54 + float(practice.get("difficulty", 1)) * 0.1),
                "signals": matched_terms,
                "citations": [],
                "safety_flags": [],
            }
        if matched_terms:
            return {
                "kind": "info",
                "title": "A useful bridge · make the link explicit",
                "body": f"Canopy heard {', '.join(matched_terms)}. Connect that evidence to {', '.join(missing_terms[:2])} so the conclusion follows rather than floats.",
                "next_step": str(practice.get("hint_ladder", ["What relationship does the evidence support?"])[0]),
                "correct": False,
                "mastery": 0.58,
                "signals": matched_terms,
                "citations": [],
                "safety_flags": [],
            }
        return {
            "kind": "warning",
            "title": "The response needs an evidence-bearing relationship",
            "body": "Name a mechanism, source feature, pattern, or constraint and explain how it supports the conclusion.",
            "next_step": str(practice.get("hint_ladder", ["What is the first relationship you can defend?"])[0]),
            "correct": False,
            "mastery": 0.34,
            "signals": [],
            "citations": [],
            "safety_flags": [],
        }
    equation = str(practice.get("equation", ""))
    if equation and "=" in equation:
        feedback = core_diagnose(settings, answer, str(practice.get("question", equation)), 2, mode=mode, stage="practice")
        if feedback.get("correct"):
            feedback["title"] = "Transfer signal · the idea travelled"
        return feedback
    return {
        "kind": "warning",
        "title": "The teacher sees a different structure",
        "body": "Try matching the operation order or explanation requested in the prompt. The goal is the reasoning pattern, not a lucky phrase.",
        "next_step": str(practice.get("hint_ladder", ["What happens first in the story?"])[0]),
        "correct": False,
        "mastery": 0.28,
        "citations": [],
        "safety_flags": [],
    }


def _practice_by_id(practice_id: str, course: Mapping[str, Any]) -> dict[str, Any]:
    bank = available_practice(course)
    return next((item for item in bank if item["id"] == practice_id), bank[0])


def render_remix(
    course: Mapping[str, Any],
    settings: Mapping[str, str | bool],
    mode: str,
    language_code: str = "en",
) -> None:
    st.markdown(f"<div class='canopy-section-label'>03 · {html.escape(tr('remix', language_code))}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='canopy-section-title'>{html.escape(tr('practice_question', language_code))} · {html.escape(str(course['subject']))}</div>", unsafe_allow_html=True)
    bank = available_practice(course)
    options = [item["id"] for item in bank]
    current_id = str(st.session_state.get("ml_practice_id", options[0]))
    if current_id not in options:
        st.session_state["ml_practice_id"] = options[0]
    left, right = st.columns([1.5, .5])
    with left:
        selected_id = st.selectbox(
            f"{tr('practice_question', language_code)} · {course['subject']}",
            options,
            index=options.index(current_id),
            format_func=lambda value: _practice_by_id(value, course)["title"],
            label_visibility="collapsed",
        )
        st.session_state["ml_practice_id"] = str(selected_id)
    with right:
        if st.button(f"✦ {tr('experiment', language_code)}", width="stretch", key="ml_surprise_practice"):
            next_index = (options.index(selected_id) + 1) % len(options)
            st.session_state["ml_practice_id"] = options[next_index]
            st.session_state["ml_practice_answer"] = ""
            st.session_state["ml_feedback"] = None
            rerun()
    practice = _practice_by_id(str(selected_id), course)
    with st.container(border=True):
        st.markdown(f"### {html.escape(str(practice['title']))}")
        st.markdown(f"<div class='canopy-equation'>{html.escape(str(practice['equation']))}</div>", unsafe_allow_html=True)
        st.markdown(f"<p class='canopy-prompt dark'>{html.escape(str(practice['question']))}</p>", unsafe_allow_html=True)
        st.caption(f"{tr('learning_signal', language_code)} · {practice['skill']}")
        with st.form(f"ml_remix_form_{course['id']}", clear_on_submit=False):
            st.text_area(
                tr("your_thinking", language_code),
                key="ml_practice_answer",
                height=120,
                placeholder=f"{tr('model', language_code)} · {tr('evidence', language_code)} · {tr('explanation', language_code)}…",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button(f"{tr('check_reasoning', language_code)} ↗", type="primary", width="stretch")
        if submitted:
            feedback = practice_diagnose(
                str(st.session_state.get("ml_practice_answer", "")),
                practice,
                settings,
                mode,
                language_code,
            )
            st.session_state["ml_feedback"] = feedback
            record_progress(feedback, f"{tr('remix', language_code)} · {practice['title']}")
            rerun()
        render_feedback(st.session_state.get("ml_feedback"), language_code)
        st.markdown(f"<div class='canopy-quote'><strong>{html.escape(get_stages(language_code)[-1])}:</strong> {html.escape(str(practice['transfer']))}</div>", unsafe_allow_html=True)


def render_teach_back(
    course: Mapping[str, Any],
    settings: Mapping[str, str | bool],
    mode: str,
    language_code: str = "en",
) -> None:
    st.markdown(f"<div class='canopy-section-label'>04 · {html.escape(tr('apply', language_code))}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='canopy-section-title'>{html.escape(tr('transfer', language_code).format(title=str(course['title'])))}</div>", unsafe_allow_html=True)
    transfer = available_practice(course)[-1]
    st.markdown(
        f"<div class='canopy-card'><div class='canopy-signal'>{html.escape(tr('apply', language_code))}</div><div class='canopy-equation dark'>{html.escape(str(transfer['equation']))}</div><p class='canopy-prompt dark'>{html.escape(str(transfer['question']))}</p><p class='canopy-prompt dark'>{html.escape(tr('node_hint', language_code))}</p></div>",
        unsafe_allow_html=True,
    )
    with st.form(f"ml_apply_form_{course['id']}", clear_on_submit=False):
        st.text_area(
            tr("apply", language_code),
            key="ml_apply_answer",
            height=115,
            placeholder=f"{tr('model', language_code)} · {tr('evidence', language_code)} · {tr('explanation', language_code)}…",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(f"{tr('check_reasoning', language_code)} ↗", type="primary", width="stretch")
    if submitted:
        feedback = practice_diagnose(
            str(st.session_state.get("ml_apply_answer", "")),
            transfer,
            settings,
            mode,
            language_code,
        )
        st.session_state["ml_feedback"] = feedback
        record_progress(feedback, f"{tr('apply', language_code)} · {course['subject']}")
        rerun()
    if st.session_state.get("ml_feedback"):
        render_feedback(st.session_state.get("ml_feedback"), language_code)
    st.markdown(f"<div class='canopy-quote'><strong>{html.escape(get_stages(language_code)[-1])}:</strong> {html.escape(str(transfer['transfer']))}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='canopy-card'><div class='canopy-signal'>{html.escape(tr('roleplay', language_code).format(title=str(course['title'])))}</div><div class='canopy-equation dark'>{html.escape(str(course['roleplay_prompt']))}</div><p class='canopy-prompt dark'>{html.escape(tr('node_hint', language_code))}</p></div>",
        unsafe_allow_html=True,
    )
    with st.form(f"ml_reflect_form_{course['id']}", clear_on_submit=False):
        st.text_area(tr("explanation", language_code), key="ml_reflection", height=150, placeholder=f"{tr('explanation', language_code)} · {tr('evidence', language_code)}…", label_visibility="collapsed")
        submitted = st.form_submit_button(f"{tr('check_reasoning', language_code)} ↗", type="primary", width="stretch")
    if submitted:
        diagnosis = domain_diagnose(
            course,
            str(st.session_state.get("ml_reflection", "")),
            course_nodes(course)[-1],
            2,
            language_code,
        )
        st.session_state["ml_feedback"] = diagnosis
        record_progress(diagnosis, f"{tr('apply', language_code)} · {course['subject']}")
        rerun()
    current_feedback = st.session_state.get("ml_feedback")
    render_feedback(current_feedback, language_code)
    if isinstance(current_feedback, Mapping) and current_feedback.get("signals"):
        st.caption(f"{tr('learning_signal', language_code)}: " + " · ".join(str(signal) for signal in current_feedback["signals"]))
    if st.button(tr("roleplay", language_code).format(title=str(course["title"])), width="stretch", key="ml_roleplay_start"):
        st.session_state["ml_roleplay"] = True
        st.session_state["ml_feedback"] = None
        rerun()
    if st.session_state.get("ml_roleplay"):
        st.markdown(
            f"<div class='canopy-teacher'><div class='canopy-avatar'><span class='canopy-avatar-dot'>✦</span> Canopy · {html.escape(str(course['subject']))}</div><blockquote>{html.escape(tr('node_question', language_code).format(stage=get_stages(language_code)[4], title=str(course['title'])))}</blockquote></div>",
            unsafe_allow_html=True,
        )
        with st.form(f"ml_roleplay_form_{course['id']}", clear_on_submit=False):
            st.text_area(tr("your_thinking", language_code), key="ml_roleplay_answer", height=100, placeholder=f"{tr('question', language_code)} · {tr('evidence', language_code)}…", label_visibility="collapsed")
            submitted = st.form_submit_button(f"{tr('check_reasoning', language_code)} ↗", width="stretch")
        if submitted:
            feedback = domain_diagnose(
                course,
                str(st.session_state.get("ml_roleplay_answer", "")),
                course_nodes(course)[-1],
                2,
                language_code,
            )
            st.session_state["ml_feedback"] = feedback
            record_progress(
                feedback,
                tr("roleplay", language_code).format(title=str(course["title"])),
            )
            rerun()


def render_toolkit(
    lesson: Mapping[str, Any],
    node: Mapping[str, Any],
    course: Mapping[str, Any],
    language_code: str = "en",
) -> None:
    st.divider()
    st.markdown(f"<div class='canopy-section-label'>{html.escape(tr('toolkit', language_code))}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='canopy-section-title'>{html.escape(tr('course_invite', language_code).format(title=str(course['title'])))}</div>", unsafe_allow_html=True)
    notes_tab, report_tab, flash_tab, sources_tab = st.tabs(
        [tr("your_thinking", language_code), tr("teacher_read", language_code), tr("practice_question", language_code), tr("sources", language_code)]
    )
    with notes_tab:
        left, right = st.columns([1.1, .9])
        with left:
            st.markdown(
                f"<div class='canopy-tool-card'><h4>{html.escape(tr('your_thinking', language_code))}</h4>"
                f"<p>{html.escape(tr('course_invite', language_code).format(title=str(course['title'])))}</p>",
                unsafe_allow_html=True,
            )
            notes = st.session_state.get("ml_notes", [])
            if not notes:
                st.markdown(
                    f"<div class='canopy-note'>{html.escape(tr('prediction', language_code))} · "
                    f"{html.escape(tr('explanation', language_code))}</div>",
                    unsafe_allow_html=True,
                )
            else:
                for note in notes:
                    st.markdown(f"<div class='canopy-note'>{html.escape(str(note))}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            history = st.session_state.get("ml_history", [])
            st.markdown(
                f"<div class='canopy-tool-card'><h4>{html.escape(tr('teacher_read', language_code))}</h4>"
                f"<p>{html.escape(tr('learning_signal', language_code))}</p>",
                unsafe_allow_html=True,
            )
            if not history:
                st.markdown(f"<div class='canopy-note'>{html.escape(tr('teacher_listening', language_code))}</div>", unsafe_allow_html=True)
            else:
                for index, item in enumerate(reversed(history[-4:]), start=1):
                    same_language = str(item.get("language", "en")) == language_code
                    display_label = str(item["label"]) if language_code == "en" or same_language else f"{tr('learning_signal', language_code)} {index}"
                    display_diagnosis = str(item["diagnosis"]) if language_code == "en" or same_language else tr("teacher_listening", language_code)
                    ready_label = "ready" if language_code == "en" else tr("teacher_ready", language_code)
                    st.markdown(
                        f"<div class='canopy-note'><strong>{html.escape(display_label)}</strong><br>{html.escape(display_diagnosis)} · {item['mastery']}% {html.escape(ready_label)}</div>",
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)
    with report_tab:
        feedback = st.session_state.get("ml_feedback")
        misconception = tr("teacher_listening", language_code)
        intervention = tr("node_hint", language_code)
        if isinstance(feedback, Mapping):
            misconception = str(feedback.get("misconception") or feedback.get("title") or misconception)
            intervention = str(feedback.get("next_step") or intervention)
        st.markdown(
            f"<div class='canopy-tool-card'><h4>{html.escape(tr('teacher_read', language_code))}</h4>"
            f"<p>{html.escape(tr('evidence', language_code))} · {html.escape(tr('learning_map', language_code))}</p>"
            f"<div class='canopy-note'><strong>{html.escape(tr('current_focus', language_code))}</strong><br>{html.escape(str(node['label']))} · {html.escape(str(node['description']))}</div>"
            f"<div class='canopy-note'><strong>{html.escape(tr('learning_signal', language_code))}</strong><br>{html.escape(misconception)}</div>"
            f"<div class='canopy-note'><strong>{html.escape(tr('next_question', language_code))}</strong><br>{html.escape(intervention)}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"#### {tr('practice_question', language_code)}")
        exit_ticket = available_practice(course)[-1]
        st.caption(str(course["transfer_prompt"]))
        st.markdown(f"<div class='canopy-equation dark'>{html.escape(str(exit_ticket['equation']))}</div>", unsafe_allow_html=True)
        st.button(
            tr("remix", language_code),
            width="stretch",
            key="ml_open_exit_ticket",
            on_click=open_exit_ticket,
            args=(str(course["id"]),),
        )
        summary_lines = [
            f"CANOPY · {str(course['subject']).upper()} · {tr('teacher_read', language_code)}",
            f"{tr('course', language_code)}: {course['title']}",
            f"{tr('current_focus', language_code)}: {node['label']}",
            f"{tr('learning_signal', language_code)}: {misconception}",
            f"{tr('next_question', language_code)}: {intervention}",
            f"{tr('experiment', language_code)}: {course['transfer_prompt']}",
        ]
        st.code("\n".join(summary_lines), language="text")
    with flash_tab:
        flashcards = list(course["flashcards"])
        card = flashcards[int(st.session_state.get("ml_flashcard_index", 0)) % len(flashcards)]
        content = card["back"] if st.session_state.get("ml_flashcard_flipped") else card["front"]
        card_face = tr("explanation", language_code) if st.session_state.get("ml_flashcard_flipped") else tr("question", language_code)
        st.markdown(f"<div class='canopy-flashcard'><strong>{html.escape(card_face)}</strong><span>{html.escape(content)}</span></div>", unsafe_allow_html=True)
        flip_left, flip_right = st.columns(2)
        with flip_left:
            if st.button(tr("explanation", language_code), width="stretch", key="ml_flip_card"):
                st.session_state["ml_flashcard_flipped"] = not bool(st.session_state.get("ml_flashcard_flipped"))
                rerun()
        with flip_right:
            if st.button(f"{tr('next_question', language_code)} →", width="stretch", key="ml_next_card"):
                st.session_state["ml_flashcard_index"] = (int(st.session_state.get("ml_flashcard_index", 0)) + 1) % len(flashcards)
                st.session_state["ml_flashcard_flipped"] = False
                rerun()
    with sources_tab:
        st.markdown(
            f"<div class='canopy-tool-card'><h4>{html.escape(tr('sources', language_code))}</h4>"
            f"<p>{html.escape(tr('evidence', language_code))} · {html.escape(str(course['title']))}</p>",
            unsafe_allow_html=True,
        )
        for citation in lesson["citations"]:
            st.markdown(
                f"<div class='canopy-note'><strong>{html.escape(str(citation['label']))}</strong><br>{html.escape(str(citation['supports']))}<br><a href='{html.escape(str(citation['url']))}' target='_blank'>{html.escape(tr('sources', language_code))} ↗</a></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="✦", layout="wide", initial_sidebar_state="expanded")
    init_state()
    language_code = active_language_code()
    render_styles(language_code)
    settings = live_settings()
    engine = str(st.session_state.get("ml_engine", "Demo · deterministic"))
    mode = "live" if engine.startswith("Live") and bool(settings.get("ready")) else "demo"
    lens = str(st.session_state.get("ml_lens", "Visual and patient"))
    raw_course = render_sidebar(mode, settings, lens)
    language_code = active_language_code()
    course = localize_course(raw_course, language_code)
    lesson = load_lesson(course)
    nodes = course_nodes(course)
    raw_nodes = course_nodes(raw_course)
    academies = {str(item["id"]): dict(item) for item in get_academies()}
    academy = academies[str(course["academy"])]
    academy["label"] = academy_label(str(course["academy"]), language_code)
    academy["description"] = academy_description(str(course["academy"]), language_code)
    render_topbar(language_code)
    render_hero(course, academy, language_code)
    render_subject_rail(course, language_code)
    render_metrics(course, nodes, language_code)
    render_interactive_lab(course, language_code)
    st.markdown(
        f"<div class='canopy-section-label' style='margin-top:1.5rem'>{html.escape(tr('learning_map', language_code))}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='canopy-section-title'>{html.escape(tr('course_invite', language_code).format(title=str(course['title'])))}</div>",
        unsafe_allow_html=True,
    )
    selected_id = str(st.session_state.get("ml_selected_node", nodes[2]["id"]))
    node = _node_by_id(selected_id, nodes)
    raw_node = _node_by_id(selected_id, raw_nodes)
    render_learning_map(selected_id, float(st.session_state.get("ml_mastery", DEFAULT_MASTERY)), nodes, language_code)
    render_focus_and_teacher(node, course, language_code)
    render_english_reference(raw_course, raw_node, language_code)
    st.markdown(
        f"<div class='canopy-section-label' style='margin-top:1.6rem'>CANOPY · {html.escape(tr('teacher_ready', language_code))}</div>",
        unsafe_allow_html=True,
    )
    mode_keys = {
        MODE_LABELS[0]: "coach",
        MODE_LABELS[1]: "learn",
        MODE_LABELS[2]: "remix",
        MODE_LABELS[3]: "apply",
    }
    selected_mode = st.radio(
        tr("teacher_ready", language_code),
        MODE_LABELS,
        key="ml_mode",
        horizontal=True,
        format_func=lambda value: tr(mode_keys[value], language_code),
        label_visibility="collapsed",
    )
    previous_mode = str(st.session_state.get("ml_last_mode", selected_mode))
    if selected_mode != previous_mode:
        # Keep the observation in Teacher memory, but do not show a stale
        # response as if it answered the newly selected mode's prompt.
        st.session_state["ml_feedback"] = None
    st.session_state["ml_last_mode"] = selected_mode
    if selected_mode == MODE_LABELS[0]:
        render_coach(node, course, settings, mode, language_code)
    elif selected_mode == MODE_LABELS[1]:
        render_explain(node, course, language_code)
    elif selected_mode == MODE_LABELS[2]:
        render_remix(course, settings, mode, language_code)
    else:
        render_teach_back(course, settings, mode, language_code)
    render_toolkit(lesson, node, course, language_code)
    render_sources(lesson, st.session_state.get("ml_feedback"), language_code)
    st.caption(f"Canopy · 20× {tr('language', language_code)} · 9× {tr('course', language_code)} · 3D · {tr('beta_short', language_code)}")


if __name__ == "__main__":
    main()
