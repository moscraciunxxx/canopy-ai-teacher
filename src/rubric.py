"""Rubric loading and lightweight equation/misconception evaluation."""

from __future__ import annotations

import copy
import json
import math
import re
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from .config import DEMO_RUBRIC, DEFAULT_RUBRIC_PATH, candidate_paths
from .schemas import (
    MisconceptionRule,
    Rubric,
    RubricCriterion,
    RubricEvaluation,
)


_NUMBER_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)")
_ASSIGNMENT_RE = re.compile(
    r"(?:\bvalue\s+of\s+)?\b[a-zA-Z]\b\s*(?:is|=|:|equals)\s*"
    r"(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\s*/\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+))?)",
    re.IGNORECASE,
)
_EQUATION_RE = re.compile(
    r"(?P<left>[-+0-9a-zA-Z*./÷×·()\s]+)\s*=\s*(?P<right>[-+0-9a-zA-Z*./÷×·()\s]+)",
)
_EXPRESSION_CHARS_RE = re.compile(r"[-+0-9a-zA-Z*./÷×·()\s]+")


def _number_value(raw: str) -> float | None:
    raw = raw.strip().replace(" ", "")
    try:
        if "/" in raw:
            numerator, denominator = raw.split("/", 1)
            denominator_value = float(denominator)
            if denominator_value == 0:
                return None
            return float(Fraction(numerator) / Fraction(denominator))
        return float(raw)
    except (ValueError, ZeroDivisionError):
        return None


def _parse_linear_expression(expression: str) -> tuple[float, float] | None:
    """Return ``(coefficient_of_x, constant)`` for a simple linear expression."""

    cleaned = (
        expression.replace(" ", "")
        .replace("×", "*")
        .replace("·", "*")
        .replace("÷", "/")
    )
    if not cleaned:
        return None

    # Handle the compact parenthesized forms most often used in a learner's
    # work, such as 3(x+2), (x+2)/3, and -2(x-5)+1.  This remains a small
    # parser rather than evaluating arbitrary input.
    if "(" in cleaned or ")" in cleaned:
        if cleaned.startswith("(") and cleaned.endswith(")"):
            depth = 0
            closes_at_end = True
            for index, character in enumerate(cleaned):
                if character == "(":
                    depth += 1
                elif character == ")":
                    depth -= 1
                    if depth == 0 and index != len(cleaned) - 1:
                        closes_at_end = False
                        break
                if depth < 0:
                    closes_at_end = False
                    break
            if closes_at_end and depth == 0:
                return _parse_linear_expression(cleaned[1:-1])

        divided = re.fullmatch(r"\(([^()]*)\)/([+-]?(?:\d+(?:\.\d*)?|\.\d+))", cleaned)
        if divided:
            inner = _parse_linear_expression(divided.group(1))
            denominator = _number_value(divided.group(2))
            if inner is None or denominator is None or denominator == 0:
                return None
            return inner[0] / denominator, inner[1] / denominator

        parenthesized = re.fullmatch(
            r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)?)\*?\(([^()]*)\)(.*)",
            cleaned,
        )
        if parenthesized:
            factor_text, inner_text, suffix = parenthesized.groups()
            if factor_text in ("", "+"):
                factor = 1.0
            elif factor_text == "-":
                factor = -1.0
            else:
                try:
                    factor = float(factor_text)
                except ValueError:
                    return None
            inner = _parse_linear_expression(inner_text)
            if inner is None:
                return None
            if suffix:
                if suffix[0] not in "+-":
                    return None
                remainder = _parse_linear_expression(suffix)
                if remainder is None:
                    return None
            else:
                remainder = (0.0, 0.0)
            return factor * inner[0] + remainder[0], factor * inner[1] + remainder[1]
        return None

    cleaned = cleaned.replace("*", "")
    # A leading plus is harmless and makes term splitting uniform.
    if cleaned[0] not in "+-":
        cleaned = "+" + cleaned
    terms = re.findall(r"[+-][^+-]+", cleaned)
    coefficient = 0.0
    constant = 0.0
    if not terms:
        return None
    for term in terms:
        sign = -1.0 if term[0] == "-" else 1.0
        body = term[1:]
        variables = re.findall(r"[a-zA-Z]", body)
        if variables:
            if len(set(variables)) != 1:
                return None
            variable = variables[0]
            numerator, separator, denominator = body.partition("/")
            if separator:
                denominator_value = _number_value(denominator)
                if denominator_value is None or denominator_value == 0:
                    return None
                coefficient_text = numerator.replace(variable, "")
                numerator_value = float(coefficient_text) if coefficient_text else 1.0
                coefficient += sign * numerator_value / denominator_value
            else:
                coefficient_text = body.replace(variable, "")
                coefficient += sign * (float(coefficient_text) if coefficient_text else 1.0)
        else:
            numerator, separator, denominator = body.partition("/")
            value: float | None
            if separator:
                constant_numerator = _number_value(numerator)
                constant_denominator = _number_value(denominator)
                if (
                    constant_numerator is None
                    or constant_denominator is None
                    or constant_denominator == 0
                ):
                    return None
                value = constant_numerator / constant_denominator
            else:
                value = _number_value(body)
            if value is None:
                return None
            constant += sign * value
    return coefficient, constant


def solve_linear_equation(equation: str) -> float | None:
    """Solve a simple linear equation without evaluating arbitrary code."""

    if not isinstance(equation, str):
        return None
    parts = _equation_sides(equation)
    if parts is None:
        return None
    left = _parse_linear_expression(parts[0])
    right = _parse_linear_expression(parts[1])
    if left is None or right is None:
        return None
    left_coefficient, left_constant = left
    right_coefficient, right_constant = right
    coefficient = left_coefficient - right_coefficient
    constant = right_constant - left_constant
    if math.isclose(coefficient, 0.0, abs_tol=1e-12):
        return None
    return constant / coefficient


def extract_equation(text: str) -> str | None:
    """Extract the first simple equation containing x from prose."""

    if not isinstance(text, str):
        return None
    parts = _equation_sides(text)
    if parts is not None:
        return f"{parts[0]} = {parts[1]}"
    return None


def _equation_sides(text: str) -> tuple[str, str] | None:
    """Find parseable equation sides while ignoring prose around the equation."""

    if not isinstance(text, str) or "=" not in text:
        return None
    for equal_index, character in enumerate(text):
        if character != "=":
            continue
        left_raw = text[:equal_index]
        right_raw = text[equal_index + 1 :]
        # A sentence often continues after the right-hand side.  Keep decimal
        # points, but stop at punctuation that is not part of a number.
        punctuation = re.search(r"[.,;:?!](?!\s*\d)", right_raw)
        if punctuation:
            right_raw = right_raw[: punctuation.start()]
        left_candidates: list[str] = []
        right_candidates: list[str] = []
        # The equation may be introduced by words ("Solve ...") or followed
        # by prose ("... What is x?").  Validate each possible trim with the
        # safe linear parser rather than evaluating the original text.
        for start in range(len(left_raw)):
            candidate = left_raw[start:].strip(" \t\n\r.,;:?!")
            if candidate and _EXPRESSION_CHARS_RE.fullmatch(candidate):
                if _parse_linear_expression(candidate) is not None:
                    left_candidates.append(candidate)
        for end in range(len(right_raw), 0, -1):
            candidate = right_raw[:end].strip(" \t\n\r.,;:?!")
            if candidate and _EXPRESSION_CHARS_RE.fullmatch(candidate):
                if _parse_linear_expression(candidate) is not None:
                    right_candidates.append(candidate)
        if left_candidates and right_candidates:
            left = left_candidates[0]
            right = right_candidates[0]
            combined = f"{left} = {right}"
            if re.search(r"[a-zA-Z]", combined):
                return left, right
    return None


def extract_candidate_value(answer: str) -> float | None:
    """Extract a learner's proposed x value from common answer forms."""

    if not isinstance(answer, str):
        return None
    assignment = _ASSIGNMENT_RE.search(answer)
    if assignment:
        return _number_value(assignment.group("value"))

    # A bare numeric response is common in a one-variable exercise.  Avoid
    # treating a multi-number equation as a proposed answer.
    if "=" not in answer:
        numbers = _NUMBER_RE.findall(answer)
        if len(numbers) == 1:
            return _number_value(numbers[0])
    return None


def _is_answer_request(answer: str) -> bool:
    """Detect a request for answer-only help before grading its number."""

    lowered = answer.lower()
    return bool(
        re.search(r"\b(?:just|only|simply)\s+(?:give|tell)\b.*\b(?:answer|solution)\b", lowered)
        or re.search(r"\b(?:give|tell)\s+me\s+the\s+(?:answer|solution)\b", lowered)
        or re.search(r"\bwithout\s+(?:the\s+)?(?:steps|explanation)\b", lowered)
    )


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _parse_expected_value(data: Mapping[str, Any]) -> float | None:
    direct = data.get("expected_value")
    if direct is not None:
        try:
            return float(direct)
        except (TypeError, ValueError):
            pass
    expected = data.get("expected_answer", data.get("answer", ""))
    if isinstance(expected, (int, float)):
        return float(expected)
    if isinstance(expected, str):
        return extract_candidate_value(f"x = {expected}") or _number_value(expected)
    return None


def _legacy_answer_key(data: Mapping[str, Any]) -> tuple[str, float | None] | None:
    """Extract a useful default example from the richer demo rubric format."""

    answer_keys = _as_mapping(data.get("answer_keys"))
    examples = _as_mapping(answer_keys.get("worked_examples"))
    candidates: list[tuple[int, str, float | None]] = []
    for index, raw in enumerate(examples.values()):
        example = _as_mapping(raw)
        equation = str(example.get("equation", "")).strip()
        if not equation:
            continue
        solution = _as_mapping(example.get("solution"))
        value = solution.get("value")
        try:
            numeric_value = float(value) if value is not None else solve_linear_equation(equation)
        except (TypeError, ValueError):
            numeric_value = solve_linear_equation(equation)
        # Prefer a two-step x example: it is the central demo case in the
        # supplied lesson, while still falling back sensibly for other files.
        score = index
        if re.search(r"x", equation, flags=re.IGNORECASE):
            score += 20
        elif re.search(r"[a-zA-Z]", equation):
            score += 5
        if re.search(r"[a-zA-Z]\s*[+-]", equation) or re.search(r"[+-]\s*[a-zA-Z]", equation):
            score += 10
        candidates.append((score, equation, numeric_value))
    if not candidates:
        return None
    _, equation, value = max(candidates, key=lambda item: item[0])
    return equation, value


def _legacy_misconceptions(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_patterns = data.get("misconception_patterns")
    if not isinstance(raw_patterns, Sequence) or isinstance(raw_patterns, (str, bytes)):
        return []
    converted: list[dict[str, Any]] = []
    for raw in raw_patterns:
        item = _as_mapping(raw)
        cues = item.get("detection_cues", ())
        patterns = list(cues) if isinstance(cues, Sequence) and not isinstance(cues, (str, bytes)) else []
        converted.append(
            {
                "id": item.get("id", "misconception"),
                "label": item.get("name", item.get("description", "Misconception")),
                "patterns": patterns,
                "feedback": item.get("description", ""),
                "hint": item.get("corrective_prompt", ""),
                "next_question": item.get("follow_up_check", ""),
            }
        )
    return converted


def _parse_rules(raw_rules: Any) -> tuple[MisconceptionRule, ...]:
    if not isinstance(raw_rules, Sequence) or isinstance(raw_rules, (str, bytes)):
        return ()
    parsed: list[MisconceptionRule] = []
    for index, raw in enumerate(raw_rules):
        data = _as_mapping(raw)
        patterns_raw = data.get("patterns", ())
        patterns: tuple[str, ...]
        if isinstance(patterns_raw, str):
            patterns = (patterns_raw,)
        elif isinstance(patterns_raw, Sequence):
            patterns = tuple(str(item) for item in patterns_raw)
        else:
            patterns = ()
        parsed.append(
            MisconceptionRule(
                rule_id=str(data.get("id", data.get("rule_id", f"rule_{index + 1}"))),
                label=str(data.get("label", data.get("name", "Unspecified misconception"))),
                patterns=patterns,
                feedback=str(data.get("feedback", "")),
                hint=str(data.get("hint", "")),
                next_question=str(data.get("next_question", "")),
            )
        )
    return tuple(parsed)


def _parse_criteria(raw_criteria: Any) -> tuple[RubricCriterion, ...]:
    if not isinstance(raw_criteria, Sequence) or isinstance(raw_criteria, (str, bytes)):
        return ()
    parsed: list[RubricCriterion] = []
    for index, raw in enumerate(raw_criteria):
        data = _as_mapping(raw)
        try:
            weight = float(data.get("weight", 1.0))
        except (TypeError, ValueError):
            weight = 1.0
        parsed.append(
            RubricCriterion(
                criterion_id=str(data.get("id", data.get("criterion_id", f"criterion_{index + 1}"))),
                description=str(data.get("description", "")),
                weight=weight,
            )
        )
    return tuple(parsed)


def rubric_from_mapping(data: Mapping[str, Any]) -> Rubric:
    """Normalize a JSON-like rubric mapping."""

    legacy_example = _legacy_answer_key(data)
    equation = str(data.get("equation", "")).strip()
    if not equation and legacy_example:
        equation = legacy_example[0]
    primary_question = str(
        data.get("primary_question", data.get("question", f"Solve {equation}. What is x?"))
    )
    expected_answer = str(data.get("expected_answer", data.get("answer", "")))
    expected_value = _parse_expected_value(data)
    if expected_value is None and legacy_example:
        expected_value = legacy_example[1]
    if not equation:
        equation = extract_equation(primary_question) or "3x + 5 = 20"
    if expected_value is None:
        expected_value = solve_linear_equation(equation)
    if not expected_answer and expected_value is not None:
        expected_answer = str(int(expected_value) if expected_value.is_integer() else expected_value)
    raw_criteria = data.get("criteria", ())
    if not raw_criteria:
        scoring = _as_mapping(data.get("scoring_rubric"))
        raw_criteria = scoring.get("dimensions", ())
    raw_misconceptions = data.get("misconceptions", data.get("misconception_rules", ()))
    if not raw_misconceptions:
        raw_misconceptions = _legacy_misconceptions(data)
    metadata = _as_mapping(data.get("lesson_metadata"))
    concept = str(data.get("concept", ""))
    if not concept:
        concept = str(metadata.get("topic", ""))
    return Rubric(
        title=str(data.get("title", metadata.get("title", "Lesson rubric"))),
        primary_question=primary_question,
        equation=equation,
        expected_answer=expected_answer,
        expected_value=expected_value,
        concept=concept,
        criteria=_parse_criteria(raw_criteria),
        misconceptions=_parse_rules(raw_misconceptions),
    )


def load_rubric(path: str | Path | None = None) -> Rubric:
    """Load a rubric file, using the embedded demo rubric if unavailable."""

    data: Mapping[str, Any] | None = None
    candidates: tuple[Path, ...]
    if path is not None:
        candidates = (Path(path),)
    else:
        candidates = tuple(candidate_paths(DEFAULT_RUBRIC_PATH))
    for candidate in candidates:
        try:
            if candidate.is_file():
                raw = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(raw, Mapping):
                    data = raw
                    break
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
    if data is None:
        data = copy.deepcopy(DEMO_RUBRIC)
    return rubric_from_mapping(data)


def _matches_rule(answer: str, rule: MisconceptionRule) -> bool:
    for pattern in rule.patterns:
        try:
            if re.search(pattern, answer, flags=re.IGNORECASE):
                return True
        except re.error:
            if pattern.lower() in answer.lower():
                return True
    return False


def _is_unknown(answer: str) -> bool:
    normalized = re.sub(r"[^a-z0-9']+", " ", answer.lower()).strip()
    if not normalized:
        return True
    return bool(
        re.fullmatch(
            r"(?:i do not know|i don't know|idk|not sure|no idea| unsure|unsure|help|i need help|can you help me)",
            normalized,
        )
    )


def _looks_math_related(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(r"[=+*/]|\b(?:x|equation|solve|solution|variable|answer|subtract|divide|multiply)\b", lowered)
        or _NUMBER_RE.search(lowered)
    )


def _question_is_off_topic(question: str | None) -> bool:
    if not question or not question.strip():
        return False
    return not _looks_math_related(question)


def _rule_by_id(rubric: Rubric, *rule_ids: str) -> MisconceptionRule | None:
    wanted = set(rule_ids)
    return next((rule for rule in rubric.misconceptions if rule.rule_id in wanted), None)


def _rule_by_label(rubric: Rubric, phrase: str) -> MisconceptionRule | None:
    lowered = phrase.lower()
    return next((rule for rule in rubric.misconceptions if lowered in rule.label.lower()), None)


def _wrong_inverse_rule() -> MisconceptionRule:
    return MisconceptionRule(
        rule_id="wrong_inverse",
        label="Used the wrong inverse operation",
        feedback="The equation has a number added to the variable term. Undo that addition instead of repeating it.",
        hint="What operation undoes the added number? Subtract it from both sides before dividing.",
        next_question="What should you subtract from both sides first, and why does that preserve the balance?",
    )


def _parenthesized_order_rule() -> MisconceptionRule:
    return MisconceptionRule(
        rule_id="parenthesized_order",
        label="Stopped before undoing the inside addition",
        feedback="Dividing by the outside coefficient leaves x + 2, so one inverse operation is still needed.",
        hint="After dividing, subtract 2 from both sides of x + 2 = 5. What value remains for x?",
        next_question="Which inverse operation removes the +2 from x + 2?",
    )


def _intermediate_result_rule() -> MisconceptionRule:
    return MisconceptionRule(
        rule_id="intermediate_result",
        label="Stopped after removing the constant",
        feedback="That value is the intermediate result after removing the constant. The coefficient is still attached to x.",
        hint="What inverse operation undoes the coefficient multiplying x? Apply it to both sides.",
        next_question="After the constant is gone, what should you divide both sides by?",
    )


def _close(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and math.isclose(left, right, rel_tol=1e-7, abs_tol=1e-7)


def _select_numeric_rule(
    answer: str,
    rubric: Rubric,
    expected_value: float | None,
    candidate_value: float | None,
    question: str | None = None,
) -> MisconceptionRule | None:
    lowered = answer.lower()

    # Learners often describe the error in prose instead of reproducing the
    # exact malformed equation.  Capture those explanations explicitly.
    if re.search(
        r"\b(?:add|added|adding|plus)\b.*\b(?:instead of|rather than)\b.*\b(?:subtract|subtracted|subtracting|minus)\b",
        lowered,
    ):
        return _wrong_inverse_rule()
    if re.search(r"\b(?:stopped|stop)\b.*\b(?:x\s*[+-]|x\s*equals)", lowered):
        if question and "(" in question:
            return _parenthesized_order_rule()
        return _rule_by_id(rubric, "M3") or _wrong_inverse_rule()
    if re.search(r"\b(?:only|just)\s+(?:the\s+)?(?:left|right)\s+side\b", lowered):
        return _rule_by_id(rubric, "M1")
    if re.search(r"\b3\s*(?:x|·x|\*x)\s*(?:means|is)\s*3\s*\+\s*x\b", lowered):
        return _rule_by_id(rubric, "M5")

    for rule in rubric.misconceptions:
        if _matches_rule(answer, rule):
            return rule

    equation = extract_equation(question or "") or extract_equation(answer) or rubric.equation
    equation_value = solve_linear_equation(equation)
    # For ax+b=c, c-b is the intermediate value after undoing the constant.
    match = _EQUATION_RE.search(equation)
    if match and candidate_value is not None:
        left = _parse_linear_expression(match.group("left"))
        right = _parse_linear_expression(match.group("right"))
        if left and right:
            coefficient = left[0] - right[0]
            intermediate = (right[1] - left[1])
            if not math.isclose(coefficient, 0.0, abs_tol=1e-12) and _close(candidate_value, intermediate):
                return _intermediate_result_rule()
            if _close(candidate_value, -expected_value if expected_value is not None else None):
                for rule in rubric.misconceptions:
                    if rule.rule_id == "sign_error":
                        return rule
        _ = equation_value  # keeps the intermediate calculation explicit and typed
    if question and re.search(r"[a-zA-Z]\s*[+-]|[+-]\s*[a-zA-Z]", question):
        return _rule_by_id(rubric, "M3") or _wrong_inverse_rule()
    return _wrong_inverse_rule()


def evaluate_answer(
    answer: str,
    rubric: Rubric,
    question: str | None = None,
    stage: str = "diagnostic",
    hint_level: int = 1,
) -> RubricEvaluation:
    """Classify an answer and produce a Socratic, non-revealing local response."""

    answer = answer if isinstance(answer, str) else str(answer)
    active_question = question or rubric.primary_question
    computed_value = solve_linear_equation(extract_equation(active_question) or "")
    expected_value = computed_value if computed_value is not None else rubric.expected_value
    if _is_unknown(answer):
        return RubricEvaluation(
            diagnosis="unknown",
            misconception="",
            feedback="It is okay to be unsure. Let us identify the first operation acting on the x-term.",
            hint="What inverse operation would undo the operation closest to x? Apply it to both sides.",
            next_question="What operation is applied to x after it is multiplied by the coefficient?",
            mastery_score=0.10,
            expected_value=expected_value,
        )

    if _is_answer_request(answer):
        return RubricEvaluation(
            diagnosis="scaffold",
            misconception="Answer-only request",
            feedback="I will help you reach the solution, but the useful next step is to reason through one operation first.",
            hint="Name the operation attached to the variable term and choose its inverse. Apply it to both sides.",
            next_question="Which operation should you undo first, and what will the equation look like afterward?",
            mastery_score=0.10,
            expected_value=expected_value,
        )

    answer_is_math_related = _looks_math_related(answer)
    if _question_is_off_topic(question) or (
        question and _looks_math_related(question) and not answer_is_math_related
    ) or (not answer_is_math_related and not question):
        return RubricEvaluation(
            diagnosis="off_topic",
            misconception="",
            feedback="That question is outside this lesson. Bring your response back to the equation and the value of x.",
            hint="Look at the equation and name the operation attached to the x-term.",
            next_question="Would you like to return to the lesson equation and identify the operation attached to x?",
            mastery_score=0.0,
            expected_value=expected_value,
        )

    candidate_value = extract_candidate_value(answer)
    if _close(candidate_value, expected_value):
        should_reveal = hint_level >= 3
        formatted_value = (
            str(int(candidate_value))
            if candidate_value is not None and candidate_value.is_integer()
            else f"{candidate_value:.12g}"
            if candidate_value is not None
            else "your value"
        )
        return RubricEvaluation(
            diagnosis="correct",
            misconception="",
            feedback=f"Good work: x = {formatted_value} is consistent with the equation. Explain which inverse operations you used.",
            hint="Substitute your value for x into the original equation. Do both sides match?",
            next_question="Can you explain why you undo the addition before the multiplication?",
            mastery_score=0.95,
            reveal_answer=should_reveal,
            expected_value=expected_value,
            candidate_value=candidate_value,
        )

    rule = _select_numeric_rule(answer, rubric, expected_value, candidate_value, question=active_question)
    if candidate_value is None and not answer_is_math_related:
        diagnosis = "off_topic"
        misconception = ""
        feedback = "That question is outside this lesson. Bring your response back to the equation and the value of x."
        hint = "Look at the equation and name the operation attached to the x-term."
        next_question = "Would you like to return to the lesson equation and identify the operation attached to x?"
        score = 0.0
    else:
        diagnosis = "misconception"
        misconception = rule.label if rule else "The variable is not isolated correctly."
        feedback = (
            rule.feedback
            if rule and rule.feedback
            else "Let us check the inverse operations one at a time. The variable is not isolated yet."
        )
        hint = (
            rule.hint
            if rule and rule.hint
            else "Which operation should you undo first, and how will you keep both sides balanced?"
        )
        next_question = (
            rule.next_question
            if rule and rule.next_question
            else "What should you undo first: the addition or the multiplication?"
        )
        score = 0.35 if candidate_value is not None else 0.25

    return RubricEvaluation(
        diagnosis=diagnosis,
        misconception=misconception,
        feedback=feedback,
        hint=hint,
        next_question=next_question,
        mastery_score=score,
        expected_value=expected_value,
        candidate_value=candidate_value,
        matched_rule_id=rule.rule_id if rule else None,
    )


RubricEvaluator = evaluate_answer
