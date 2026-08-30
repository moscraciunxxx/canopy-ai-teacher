"""Deterministic learning-studio primitives for an all-in-one AI teacher.

This module deliberately has no third-party dependencies and does not call a
model.  It supplies a stable, JSON-friendly experience layer that an app can
render immediately and that an optional model can enrich later.  The design is
centered on four teacher modes:

* Coach: diagnose the learner's thinking and give the smallest useful nudge.
* Explain: build a clear mental model with examples and counterexamples.
* Practice: remix the skill into varied, increasingly difficult questions.
* Reflect: turn a solved problem into metacognition and transfer.

All factories return fresh dictionaries/lists, so callers can safely mutate a
rendered snapshot without changing the next session.  The public functions
are intentionally small enough to import from ``app.py`` or a notebook.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Literal, Mapping, TypedDict, TypeAlias


LearningStatus: TypeAlias = Literal["mastered", "active", "available", "locked"]
TeacherMode: TypeAlias = Literal["coach", "explain", "practice", "reflect"]
PracticeKind: TypeAlias = Literal["equation", "concept", "transfer", "teach_back"]


class LearningEdge(TypedDict):
    """A directed prerequisite edge in the learning graph."""

    source: str
    target: str
    reason: str


class LearningNode(TypedDict):
    """A graph node with enough presentation metadata for a visual canvas."""

    id: str
    title: str
    subtitle: str
    concept: str
    status: LearningStatus
    order: int
    prerequisites: list[str]
    mastery: float
    accent: str
    icon: str
    estimated_minutes: int
    outcomes: list[str]


class LearningGraph(TypedDict):
    """A complete learner roadmap suitable for JSON serialization."""

    id: str
    title: str
    description: str
    nodes: list[LearningNode]
    edges: list[LearningEdge]
    active_node_id: str | None
    completion_percent: int


class _NodeSpec(TypedDict):
    """Internal immutable-ish template used to construct graph nodes."""

    id: str
    title: str
    subtitle: str
    concept: str
    prerequisites: list[str]
    accent: str
    icon: str
    estimated_minutes: int
    outcomes: list[str]


class PracticeMetadata(TypedDict):
    """Structured pedagogical metadata attached to one practice item."""

    skill: str
    cognitive_move: str
    success_signal: str
    common_traps: list[str]
    estimated_seconds: int
    transfer_target: str


class PracticeItem(TypedDict):
    """A remixable exercise with answer and scaffolding metadata."""

    id: str
    node_id: str
    kind: PracticeKind
    prompt: str
    equation: str
    answer: str
    answer_type: Literal["number", "text", "expression"]
    answer_explanation: str
    accepted_answers: list[str]
    difficulty: int
    misconception_tags: list[str]
    skills: list[str]
    hint_ladder: list[str]
    transfer_prompt: str
    metadata: PracticeMetadata


class TeacherModeSpec(TypedDict):
    """Presentation and orchestration contract for a teacher mode."""

    id: TeacherMode
    title: str
    tagline: str
    description: str
    icon: str
    accent: str
    interaction_label: str
    teacher_goal: str
    response_contract: list[str]
    best_for: list[str]


class TeacherTurn(TypedDict):
    """A deterministic mode brief that can seed a model or a local UI."""

    mode: TeacherMode
    mode_title: str
    node_id: str
    practice_id: str
    prompt: str
    learner_answer: str
    hint_level: int
    teacher_brief: str
    response_frame: list[str]
    next_actions: list[str]


class StudioStats(TypedDict):
    """Small progress summary for a dashboard header."""

    mastered_nodes: int
    total_nodes: int
    practice_items: int
    average_difficulty: float
    completion_percent: int


class StudioSnapshot(TypedDict):
    """One render-ready payload for a learning-studio screen."""

    learner_name: str
    graph: LearningGraph
    modes: list[TeacherModeSpec]
    recommended_practice: PracticeItem
    stats: StudioStats
    microcopy: list[str]


_NODE_SPECS: tuple[_NodeSpec, ...] = (
    {
        "id": "translate",
        "title": "See the structure",
        "subtitle": "Translate the story into an equation",
        "concept": "Represent a relationship before calculating",
        "prerequisites": [],
        "accent": "#78F0C3",
        "icon": "◈",
        "estimated_minutes": 6,
        "outcomes": ["Name the unknown", "Map words to operations"],
    },
    {
        "id": "balance",
        "title": "Balance the system",
        "subtitle": "Protect equality while transforming",
        "concept": "Apply the same inverse operation to both sides",
        "prerequisites": ["translate"],
        "accent": "#6CD9FF",
        "icon": "⇄",
        "estimated_minutes": 7,
        "outcomes": ["Explain why both sides change", "Track equivalent expressions"],
    },
    {
        "id": "isolate",
        "title": "Isolate the signal",
        "subtitle": "Undo operations in the right order",
        "concept": "Separate the coefficient from the variable",
        "prerequisites": ["balance"],
        "accent": "#B69CFF",
        "icon": "✦",
        "estimated_minutes": 8,
        "outcomes": ["Remove constants first", "Use the inverse coefficient"],
    },
    {
        "id": "verify",
        "title": "Verify with evidence",
        "subtitle": "Substitute and inspect the result",
        "concept": "Use verification as a reasoning tool, not a final ritual",
        "prerequisites": ["balance"],
        "accent": "#FFD166",
        "icon": "✓",
        "estimated_minutes": 6,
        "outcomes": ["Catch arithmetic slips", "Defend an answer with evidence"],
    },
    {
        "id": "transfer",
        "title": "Transfer the move",
        "subtitle": "Recognize the same idea in a new skin",
        "concept": "Generalize inverse operations across contexts",
        "prerequisites": ["verify"],
        "accent": "#FF8FB3",
        "icon": "↗",
        "estimated_minutes": 9,
        "outcomes": ["Solve a changed surface problem", "Choose a strategy independently"],
    },
    {
        "id": "teach_back",
        "title": "Teach it forward",
        "subtitle": "Make the invisible reasoning visible",
        "concept": "Explain, diagnose, and adapt a solution",
        "prerequisites": ["transfer"],
        "accent": "#FFB86B",
        "icon": "✺",
        "estimated_minutes": 8,
        "outcomes": ["Explain without answer dumping", "Predict a common misconception"],
    },
)


def _clamp_mastery(value: object) -> float:
    """Convert untrusted progress into a stable 0..1 float."""

    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        number = 0.0
    if number > 1.0 and number <= 100.0:
        number /= 100.0
    return round(min(1.0, max(0.0, number)), 3)


def _stable_rank(value: str, seed: int) -> str:
    """Return a process-independent sort key for deterministic remixing."""

    payload = f"{seed}:{value}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _copy(value: object) -> object:
    """Deep-copy a JSON-like object while keeping factory boundaries safe."""

    return copy.deepcopy(value)


def _default_progress() -> dict[str, float]:
    """Return a welcoming demo state with multiple visible graph statuses."""

    return {
        "translate": 0.92,
        "balance": 0.88,
        "isolate": 0.46,
        "verify": 0.08,
        "transfer": 0.0,
        "teach_back": 0.0,
    }


def build_learning_graph(progress: Mapping[str, object] | None = None) -> LearningGraph:
    """Build the six-node roadmap and infer statuses from mastery/prerequisites.

    ``progress`` accepts either 0..1 or percentage values such as ``72``.  The
    first eligible, unfinished node becomes active; later eligible nodes are
    available and prerequisite-blocked nodes are locked.  This makes the
    graph useful both as a static demo and as a deterministic state machine.
    """

    raw_progress = _default_progress()
    if progress is not None:
        raw_progress.update({key: _clamp_mastery(value) for key, value in progress.items()})
    mastery = {key: _clamp_mastery(value) for key, value in raw_progress.items()}
    mastered = {key for key, value in mastery.items() if value >= 0.85}

    eligible_ids: list[str] = []
    for spec in _NODE_SPECS:
        node_id = str(spec["id"])
        prerequisites = list(spec["prerequisites"])
        if mastery.get(node_id, 0.0) < 0.85 and all(item in mastered for item in prerequisites):
            eligible_ids.append(node_id)
    active_id = eligible_ids[0] if eligible_ids else None

    nodes: list[LearningNode] = []
    for order, spec in enumerate(_NODE_SPECS):
        node_id = str(spec["id"])
        prerequisites = list(spec["prerequisites"])
        value = mastery.get(node_id, 0.0)
        if value >= 0.85:
            status: LearningStatus = "mastered"
        elif node_id == active_id:
            status = "active"
        elif all(item in mastered for item in prerequisites):
            status = "available"
        else:
            status = "locked"
        nodes.append(
            {
                "id": node_id,
                "title": str(spec["title"]),
                "subtitle": str(spec["subtitle"]),
                "concept": str(spec["concept"]),
                "status": status,
                "order": order,
                "prerequisites": prerequisites,
                "mastery": value,
                "accent": str(spec["accent"]),
                "icon": str(spec["icon"]),
                "estimated_minutes": int(spec["estimated_minutes"]),
                "outcomes": list(spec["outcomes"]),
            }
        )

    edges: list[LearningEdge] = []
    for node in nodes:
        for prerequisite in node["prerequisites"]:
            edges.append(
                {
                    "source": prerequisite,
                    "target": node["id"],
                    "reason": "Unlocks after the prerequisite becomes reliable",
                }
            )
    completion = round(sum(node["mastery"] for node in nodes) / len(nodes) * 100)
    return {
        "id": "linear-reasoning-arc",
        "title": "The reasoning constellation",
        "description": "A visible route from noticing structure to teaching the idea forward.",
        "nodes": nodes,
        "edges": edges,
        "active_node_id": active_id,
        "completion_percent": completion,
    }


def recommend_next_node(graph: LearningGraph) -> LearningNode | None:
    """Return a fresh copy of the graph's active node, if one exists."""

    active_id = graph.get("active_node_id")
    for node in graph.get("nodes", []):
        if node["id"] == active_id:
            return _copy(node)  # type: ignore[return-value]
    return None


def _practice_bank() -> list[PracticeItem]:
    """Create the built-in bank; every call returns independent JSON data."""

    return [
        {
            "id": "balance-01",
            "node_id": "balance",
            "kind": "equation",
            "prompt": "A mystery number is multiplied by 4 and then increased by 3 to make 27. What equation represents the story?",
            "equation": "4x + 3 = 27",
            "answer": "4x + 3 = 27",
            "answer_type": "expression",
            "answer_explanation": "The multiplier stays attached to x, while the increase is added after multiplication.",
            "accepted_answers": ["4x + 3 = 27", "4*x+3=27", "4x+3=27"],
            "difficulty": 1,
            "misconception_tags": ["reverse-order", "story-to-symbol"],
            "skills": ["translate", "balance"],
            "hint_ladder": [
                "Which action happens first to the mystery number?",
                "Write the multiplication before the addition.",
                "The coefficient is 4 and the constant is +3.",
            ],
            "transfer_prompt": "Invent a story that could be represented by 4x + 3 = 27.",
            "metadata": {
                "skill": "Represent a two-step relationship",
                "cognitive_move": "Translate language into structure",
                "success_signal": "The order of operations matches the story",
                "common_traps": ["Writing 4(x+3)", "Subtracting before representing"],
                "estimated_seconds": 75,
                "transfer_target": "Word problems with a hidden linear structure",
            },
        },
        {
            "id": "isolate-01",
            "node_id": "isolate",
            "kind": "equation",
            "prompt": "Solve 3x + 5 = 20. Show the two inverse moves, not only the final number.",
            "equation": "3x + 5 = 20",
            "answer": "x = 5",
            "answer_type": "number",
            "answer_explanation": "Subtract 5 from both sides to get 3x = 15, then divide both sides by 3.",
            "accepted_answers": ["5", "x=5", "x = 5"],
            "difficulty": 2,
            "misconception_tags": ["stopped-early", "wrong-inverse"],
            "skills": ["balance", "isolate"],
            "hint_ladder": [
                "What is attached to 3x by addition? Undo that first.",
                "Subtract 5 from both sides. What equation remains?",
                "Now undo the coefficient by dividing both sides by 3.",
            ],
            "transfer_prompt": "How would the strategy change for 3x - 5 = 20?",
            "metadata": {
                "skill": "Solve a two-step linear equation",
                "cognitive_move": "Apply inverse operations in reverse order",
                "success_signal": "Each operation is performed on both sides",
                "common_traps": ["Stopping at 3x = 15", "Dividing before subtracting"],
                "estimated_seconds": 90,
                "transfer_target": "Any equation of the form ax + b = c",
            },
        },
        {
            "id": "isolate-02",
            "node_id": "isolate",
            "kind": "equation",
            "prompt": "Solve 6x - 8 = 22, then name the operation you use first and why.",
            "equation": "6x - 8 = 22",
            "answer": "x = 5",
            "answer_type": "number",
            "answer_explanation": "Add 8 to both sides to get 6x = 30, then divide by 6.",
            "accepted_answers": ["5", "x=5", "x = 5"],
            "difficulty": 2,
            "misconception_tags": ["sign-error", "wrong-order"],
            "skills": ["isolate", "explain"],
            "hint_ladder": [
                "What is the inverse of subtracting 8?",
                "Add 8 to both sides before touching the 6.",
                "After that move, divide the whole equation by 6.",
            ],
            "transfer_prompt": "Create a version whose solution is x = 5 but whose constant is positive.",
            "metadata": {
                "skill": "Handle a negative constant",
                "cognitive_move": "Justify operation order",
                "success_signal": "The sign change is explained rather than guessed",
                "common_traps": ["Subtracting 8 again", "Dropping the negative sign"],
                "estimated_seconds": 95,
                "transfer_target": "Signed quantities and inverse-operation reasoning",
            },
        },
        {
            "id": "verify-01",
            "node_id": "verify",
            "kind": "concept",
            "prompt": "A classmate says x = 4 solves 2x + 7 = 15. How can you test the claim in one line?",
            "equation": "2x + 7 = 15",
            "answer": "2(4) + 7 = 15, so the claim is true.",
            "answer_type": "text",
            "answer_explanation": "Substitution turns the claim into a check: 8 + 7 equals 15.",
            "accepted_answers": ["2(4)+7=15", "8+7=15", "true"],
            "difficulty": 1,
            "misconception_tags": ["no-verification", "arithmetic-slip"],
            "skills": ["verify", "evidence"],
            "hint_ladder": [
                "Replace x with the proposed value.",
                "Evaluate the left side.",
                "Compare the result with 15.",
            ],
            "transfer_prompt": "What would a failed substitution tell you about the claim?",
            "metadata": {
                "skill": "Verify by substitution",
                "cognitive_move": "Use evidence to evaluate a claim",
                "success_signal": "Both sides are compared after substitution",
                "common_traps": ["Checking only one operation", "Assuming a neat answer is correct"],
                "estimated_seconds": 60,
                "transfer_target": "Checking models, formulas, and predictions",
            },
        },
        {
            "id": "transfer-01",
            "node_id": "transfer",
            "kind": "transfer",
            "prompt": "A taxi charges $5 to start and $3 per mile. The ride costs $20. How many miles were traveled?",
            "equation": "3m + 5 = 20",
            "answer": "5 miles",
            "answer_type": "number",
            "answer_explanation": "The fixed fee is the constant; subtract it first, then divide the remaining cost by the per-mile rate.",
            "accepted_answers": ["5", "5 miles", "m=5", "m = 5"],
            "difficulty": 3,
            "misconception_tags": ["surface-feature", "fixed-vs-rate"],
            "skills": ["translate", "isolate", "transfer"],
            "hint_ladder": [
                "Which cost happens once, even at zero miles?",
                "Let m be miles and write the total-cost equation.",
                "Solve the equation using the same inverse moves.",
            ],
            "transfer_prompt": "Change the numbers so the ride is 7 miles, then write the new equation.",
            "metadata": {
                "skill": "Transfer algebra to a real context",
                "cognitive_move": "Separate fixed and variable quantities",
                "success_signal": "The equation preserves the context's roles",
                "common_traps": ["Treating 5 as the rate", "Dividing before removing the fee"],
                "estimated_seconds": 120,
                "transfer_target": "Rates, fees, and linear models",
            },
        },
        {
            "id": "transfer-02",
            "node_id": "transfer",
            "kind": "transfer",
            "prompt": "Which equation matches: 'The difference between twice a number and 9 is 17'? Explain the phrase difference between.",
            "equation": "2n - 9 = 17",
            "answer": "2n - 9 = 17",
            "answer_type": "expression",
            "answer_explanation": "The phrase means subtract 9 from twice the number; the result is 17.",
            "accepted_answers": ["2n-9=17", "2n - 9 = 17", "2*n-9=17"],
            "difficulty": 3,
            "misconception_tags": ["language-order", "difference-between"],
            "skills": ["translate", "transfer"],
            "hint_ladder": [
                "What expression represents twice a number?",
                "'The difference between A and 9' means A minus 9.",
                "Set that result equal to 17.",
            ],
            "transfer_prompt": "Write a sentence that could represent 9 - 2n = 17, and compare the meaning.",
            "metadata": {
                "skill": "Parse relational language",
                "cognitive_move": "Notice how wording controls order",
                "success_signal": "The learner can defend subtraction direction",
                "common_traps": ["Reversing the subtraction", "Confusing 2n with n²"],
                "estimated_seconds": 105,
                "transfer_target": "Natural-language precision in symbolic reasoning",
            },
        },
        {
            "id": "teach-back-01",
            "node_id": "teach_back",
            "kind": "teach_back",
            "prompt": "Teach a younger learner why solving 3x + 5 = 20 starts by subtracting 5 from both sides.",
            "equation": "3x + 5 = 20",
            "answer": "Remove the outside +5 equally from both sides, preserving equality; then 3x = 15.",
            "answer_type": "text",
            "answer_explanation": "A strong explanation connects the balance metaphor to the legal algebraic operation.",
            "accepted_answers": ["subtract 5 from both sides", "3x=15", "keep both sides equal"],
            "difficulty": 3,
            "misconception_tags": ["answer-dumping", "balance-metaphor"],
            "skills": ["explain", "teach-back", "balance"],
            "hint_ladder": [
                "What part is outside the 3x term?",
                "Use a balance metaphor: what must happen on both sides?",
                "State the new equation and why equality is preserved.",
            ],
            "transfer_prompt": "Name one likely mistake a beginner might make at this step.",
            "metadata": {
                "skill": "Explain a transformation causally",
                "cognitive_move": "Make a hidden invariant visible",
                "success_signal": "The explanation includes both action and reason",
                "common_traps": ["Saying 'move 5' without justification", "Giving only x = 5"],
                "estimated_seconds": 110,
                "transfer_target": "Peer teaching and misconception diagnosis",
            },
        },
        {
            "id": "teach-back-02",
            "node_id": "teach_back",
            "kind": "teach_back",
            "prompt": "A learner stops at 3x = 15 and says x = 15. Write one coaching question that helps without revealing x.",
            "equation": "3x = 15",
            "answer": "What operation is still attached to x, and what is its inverse?",
            "answer_type": "text",
            "answer_explanation": "The question directs attention to the remaining coefficient while preserving productive struggle.",
            "accepted_answers": ["what is attached to x", "inverse of 3", "divide by 3"],
            "difficulty": 4,
            "misconception_tags": ["premature-stop", "hint-too-large"],
            "skills": ["coach", "teach-back", "isolate"],
            "hint_ladder": [
                "Look at the operation still touching x.",
                "Ask about the inverse of that operation.",
                "A useful question mentions the coefficient without naming the result.",
            ],
            "transfer_prompt": "Write a less helpful hint and explain why yours is better.",
            "metadata": {
                "skill": "Design a productive hint",
                "cognitive_move": "Calibrate support to preserve agency",
                "success_signal": "The hint points, but does not solve",
                "common_traps": ["Revealing the answer", "Repeating the procedure mechanically"],
                "estimated_seconds": 100,
                "transfer_target": "Feedback design and adaptive tutoring",
            },
        },
    ]


def remix_practice_bank(
    node_id: str | None = None,
    difficulty: int | None = None,
    seed: int = 17,
    limit: int | None = None,
) -> list[PracticeItem]:
    """Return a deterministic, varied ordering of practice items.

    Filtering is optional.  The SHA-256 ordering avoids Python's randomized
    ``hash()`` seed, so the same ``seed`` produces the same remix across
    processes, machines, and demo recordings.
    """

    items = _practice_bank()
    if node_id is not None:
        items = [item for item in items if item["node_id"] == node_id]
    if difficulty is not None:
        items = [item for item in items if item["difficulty"] == difficulty]
    items.sort(key=lambda item: _stable_rank(item["id"], int(seed)))
    if limit is not None:
        items = items[: max(0, int(limit))]
    return _copy(items)  # type: ignore[return-value]


def get_practice_item(item_id: str | None = None, seed: int = 17) -> PracticeItem:
    """Get one named item, or the deterministic lead item for a seed."""

    items = remix_practice_bank(seed=seed)
    if not items:
        raise LookupError("The practice bank is empty")
    if item_id is None:
        return items[0]
    for item in items:
        if item["id"] == item_id:
            return item
    raise KeyError(f"Unknown practice item: {item_id}")


def get_teacher_modes() -> list[TeacherModeSpec]:
    """Return the four mode cards in a stable presentation order."""

    modes: list[TeacherModeSpec] = [
        {
            "id": "coach",
            "title": "Coach",
            "tagline": "Keep the insight yours",
            "description": "Diagnoses the move behind an answer and gives one calibrated nudge at a time.",
            "icon": "✦",
            "accent": "#78F0C3",
            "interaction_label": "Show my thinking",
            "teacher_goal": "Preserve productive struggle while making the next move unmistakable.",
            "response_contract": ["Name the evidence", "Identify one misconception", "Ask one next-step question", "Never dump the answer"],
            "best_for": ["Stuck moments", "Error diagnosis", "Confidence building"],
        },
        {
            "id": "explain",
            "title": "Explain",
            "tagline": "See the invisible structure",
            "description": "Builds a mental model with a visual metaphor, worked example, and a counterexample.",
            "icon": "◉",
            "accent": "#6CD9FF",
            "interaction_label": "Make it click",
            "teacher_goal": "Connect procedure to meaning so the learner can predict the next step.",
            "response_contract": ["Start with the why", "Use a concrete representation", "Contrast a common wrong move", "Check for understanding"],
            "best_for": ["New concepts", "Why questions", "Concept repair"],
        },
        {
            "id": "practice",
            "title": "Practice",
            "tagline": "Change the surface, keep the skill",
            "description": "Remixes difficulty, context, and representation so recognition becomes flexible knowledge.",
            "icon": "⟲",
            "accent": "#B69CFF",
            "interaction_label": "Remix this skill",
            "teacher_goal": "Create short deliberate reps with immediate, specific feedback.",
            "response_contract": ["Vary the context", "Preserve the target skill", "Escalate only after evidence", "Offer a transfer challenge"],
            "best_for": ["Fluency", "Exam preparation", "Transfer"],
        },
        {
            "id": "reflect",
            "title": "Reflect",
            "tagline": "Turn the win into a strategy",
            "description": "Prompts the learner to explain what changed, predict a trap, and choose a future strategy.",
            "icon": "✺",
            "accent": "#FFD166",
            "interaction_label": "Lock in the learning",
            "teacher_goal": "Convert a single solved item into reusable self-monitoring.",
            "response_contract": ["Ask what changed", "Surface the decision point", "Name a future trap", "Set a next experiment"],
            "best_for": ["After solving", "Metacognition", "Long-term retention"],
        },
    ]
    return _copy(modes)  # type: ignore[return-value]


def get_teacher_mode(mode: TeacherMode | str) -> TeacherModeSpec:
    """Return one mode specification with a friendly validation error."""

    normalized = str(mode).strip().lower()
    for spec in get_teacher_modes():
        if spec["id"] == normalized:
            return spec
    allowed = ", ".join(item["id"] for item in get_teacher_modes())
    raise ValueError(f"Unknown teacher mode {mode!r}; choose one of: {allowed}")


def build_teacher_turn(
    mode: TeacherMode | str,
    practice: PracticeItem,
    learner_answer: str = "",
    hint_level: int = 0,
    node_id: str | None = None,
) -> TeacherTurn:
    """Build a deterministic orchestration brief for one teacher interaction."""

    spec = get_teacher_mode(mode)
    selected_mode = spec["id"]
    bounded_hint = min(3, max(0, int(hint_level)))
    answer = str(learner_answer).strip()[:1000]
    target_node = node_id or practice["node_id"]
    item_context = f"Question: {practice['prompt']} Equation/context: {practice['equation']}"
    mode_guidance = {
        "coach": "Diagnose the learner's current move. Respond with evidence, one misconception label if needed, and one question that advances the work without revealing the answer.",
        "explain": "Explain the invariant behind the move. Use a concrete metaphor, one worked micro-step, and a quick check that asks the learner to predict what happens next.",
        "practice": "Give feedback on this attempt, then offer a nearby remix that changes the surface while preserving the target skill. Increase difficulty only when the reasoning is sound.",
        "reflect": "Ask the learner to reconstruct the decision point, name a likely future trap, and state a transferable strategy in their own words.",
    }[selected_mode]
    response_frame = {
        "coach": ["Evidence I notice", "The next useful question", "A hint only if requested"],
        "explain": ["The idea in plain language", "A visual or concrete analogy", "Try predicting the next step"],
        "practice": ["What was strong", "What to adjust", "A remixed follow-up"],
        "reflect": ["The decision that mattered", "A trap to watch for", "Your reusable strategy"],
    }[selected_mode]
    next_actions = {
        "coach": ["Answer the next-step question", "Request a stronger hint", "Switch to Explain"],
        "explain": ["Predict the next transformation", "Try the original item", "Switch to Practice"],
        "practice": ["Submit a worked attempt", "Try the transfer prompt", "Review the hint ladder"],
        "reflect": ["Write a one-sentence takeaway", "Teach the move back", "Choose the next graph node"],
    }[selected_mode]
    brief = f"{mode_guidance} {item_context} Skill tags: {', '.join(practice['skills'])}."
    return {
        "mode": selected_mode,
        "mode_title": spec["title"],
        "node_id": target_node,
        "practice_id": practice["id"],
        "prompt": practice["prompt"],
        "learner_answer": answer,
        "hint_level": bounded_hint,
        "teacher_brief": brief,
        "response_frame": list(response_frame),
        "next_actions": list(next_actions),
    }


def build_teacher_prompt(turn: TeacherTurn, include_answer_key: bool = False) -> str:
    """Render a compact, provider-neutral prompt from a teacher turn.

    The answer key is excluded by default to preserve scaffolding.  A caller
    may include it for a private evaluator or a teacher dashboard.
    """

    lines = [
        f"You are in {turn['mode_title']} mode.",
        turn["teacher_brief"],
        f"Learner attempt: {turn['learner_answer'] or '[no attempt yet]'}",
        f"Hint level already used: {turn['hint_level']}/3",
        "Return exactly these sections: " + " | ".join(turn["response_frame"]),
    ]
    if include_answer_key:
        lines.append("Private answer-key access is enabled; do not reveal it unless explicitly requested.")
    return "\n".join(lines)


def build_studio_snapshot(
    learner_name: str = "Explorer",
    progress: Mapping[str, object] | None = None,
    seed: int = 17,
) -> StudioSnapshot:
    """Return one complete payload for a rich learning-studio landing view."""

    graph = build_learning_graph(progress)
    modes = get_teacher_modes()
    items = remix_practice_bank(seed=seed)
    if not items:
        raise LookupError("The practice bank is empty")
    mastered_count = sum(1 for node in graph["nodes"] if node["status"] == "mastered")
    average_difficulty = round(sum(item["difficulty"] for item in items) / len(items), 2)
    stats: StudioStats = {
        "mastered_nodes": mastered_count,
        "total_nodes": len(graph["nodes"]),
        "practice_items": len(items),
        "average_difficulty": average_difficulty,
        "completion_percent": graph["completion_percent"],
    }
    return {
        "learner_name": str(learner_name).strip() or "Explorer",
        "graph": graph,
        "modes": modes,
        "recommended_practice": items[0],
        "stats": stats,
        "microcopy": [
            "Your route adapts to the quality of the reasoning, not just the final answer.",
            "Every hint protects one piece of productive struggle.",
            "A changed surface is the fastest test of real understanding.",
        ],
    }


def json_dumps(value: object) -> str:
    """Serialize any public payload with stable key ordering for snapshots."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"))


__all__ = [
    "LearningEdge",
    "LearningGraph",
    "LearningNode",
    "LearningStatus",
    "PracticeItem",
    "PracticeKind",
    "PracticeMetadata",
    "StudioSnapshot",
    "StudioStats",
    "TeacherMode",
    "TeacherModeSpec",
    "TeacherTurn",
    "build_learning_graph",
    "build_studio_snapshot",
    "build_teacher_prompt",
    "build_teacher_turn",
    "get_practice_item",
    "get_teacher_mode",
    "get_teacher_modes",
    "json_dumps",
    "recommend_next_node",
    "remix_practice_bank",
]
