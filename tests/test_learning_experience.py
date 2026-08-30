from src.learning_studio import build_learning_graph, build_teacher_turn, remix_practice_bank
from src.visual_language import learning_map_markup


def test_learning_graph_exposes_prerequisites_and_unlocks() -> None:
    graph = build_learning_graph()

    assert len(graph["nodes"]) == 6
    assert graph["active_node_id"] == "isolate"
    assert any(edge["source"] == "balance" and edge["target"] == "isolate" for edge in graph["edges"])
    assert {node["status"] for node in graph["nodes"]} >= {"mastered", "active", "locked"}


def test_remix_bank_is_deterministic_and_varied() -> None:
    first = remix_practice_bank(seed=17)
    second = remix_practice_bank(seed=17)

    assert first == second
    assert len(first) == 8
    assert {item["kind"] for item in first} >= {"equation", "concept", "transfer", "teach_back"}
    assert len({item["difficulty"] for item in first}) >= 3


def test_teacher_turn_and_visual_map_are_safe_render_contracts() -> None:
    practice = remix_practice_bank(node_id="isolate", limit=1)[0]
    turn = build_teacher_turn("coach", practice, learner_answer="x = 15", hint_level=1)
    markup = learning_map_markup(
        [{"id": "isolate", "label": "<focus>", "caption": "active", "state": "active"}],
        active_id="isolate",
    )

    assert turn["mode"] == "coach"
    assert turn["learner_answer"] == "x = 15"
    assert "<focus>" not in markup
    assert "&lt;focus&gt;" in markup
    assert "aria-label" in markup
