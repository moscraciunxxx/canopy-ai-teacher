"""Rendering contracts for every browser-side visual laboratory."""

from __future__ import annotations

from src.curriculum_atlas import get_courses
from src.interactive_labs import (
    build_lab_figure,
    default_lab_values,
    lab_control_specs,
    lab_insight,
    lab_metrics,
    lab_option_label,
)
from src.lab_localization import lab_message_keys, lab_tr
from src.localization import get_languages, localize_course, tr


def test_every_course_builds_an_interactive_figure() -> None:
    for course in get_courses():
        controls = lab_control_specs(course)
        values = default_lab_values(course)
        figure = build_lab_figure(course, values)

        assert controls
        assert set(values) == {control["key"] for control in controls}
        assert len(figure.data) >= 1
        assert figure.layout.title.text
        assert figure.layout.meta["course_id"] == course["id"]
        assert len(lab_metrics(course, values)) >= 3
        assert len(lab_insight(course, values)) > 80


def test_visual_forms_match_their_reasoning_jobs() -> None:
    traces_by_course = {
        course["id"]: {trace.type for trace in build_lab_figure(course).data}
        for course in get_courses()
    }

    assert "surface" in traces_by_course["math-patterns"]
    assert "scatter3d" in traces_by_course["physics-flight"]
    assert "scatter3d" in traces_by_course["biology-code"]
    assert traces_by_course["earth-carbon"] == {"sankey"}
    assert "scatter3d" in traces_by_course["cs-networks"]
    assert "scatter3d" in traces_by_course["history-sources"]
    assert "scatter3d" in traces_by_course["literature-motifs"]
    assert traces_by_course["civics-information"] == {"sankey"}
    assert {"surface", "scatter3d"}.issubset(traces_by_course["ethics-decisions"])


def test_controls_materially_change_models() -> None:
    low = build_lab_figure("projectile", {"speed": 12.0})
    high = build_lab_figure("projectile", {"speed": 26.0})
    assert float(low.data[0].x[-1]) < float(high.data[0].x[-1])

    bfs = lab_metrics("network", {"algorithm": "Breadth-first", "start": "A", "target": "H"})
    dfs = lab_metrics("network", {"algorithm": "Depth-first", "start": "A", "target": "H"})
    assert bfs[1][1] != dfs[1][1]

    with_opposition = lab_metrics("sources", {"include_opposition": "Include disagreement"})
    without_opposition = lab_metrics("sources", {"include_opposition": "Only supportive"})
    assert with_opposition[2][1] == "2"
    assert without_opposition[2][1] == "1"


def test_every_locale_fills_the_visual_vocabulary_contract() -> None:
    assert len(lab_message_keys()) == 42
    for language in get_languages():
        code = language["code"]
        assert all(lab_tr(key, code).strip() for key in lab_message_keys())

    assert lab_option_label("Variant", "ro") == "Variantă"
    assert lab_option_label("Breadth-first", "zh") == "广度优先"
    assert lab_option_label("Located", "ar") == "موجود"
    assert lab_option_label("A", "ro") == "A"


def test_every_non_english_course_figure_removes_canonical_english_chrome() -> None:
    leaked_phrases = (
        "Predicted path",
        "Landing point",
        "Barrier ·",
        "Target zone",
        "Function surface",
        "cross-section",
        "strand 1",
        "strand 2",
        "Selected base pair",
        "sequence position",
        "carbon reservoir",
        "conceptual flux index",
        "Graph edges",
        "Discovered route",
        "not visited",
        "Source constellation",
        "event proximity",
        "stance / perspective",
        "Act ",
        "narrative tension",
        "Counter-reading",
        "Public claim",
        "Repeated posts",
        "verification stage",
        "evidence-flow index",
        "Broad deployment",
        "Limited pilot",
        "Do not deploy",
        "Policy options",
        "outcome evidence",
        "rights compatibility",
    )
    languages = [language for language in get_languages() if language["code"] != "en"]
    for raw_course in get_courses():
        for language in languages:
            code = language["code"]
            course = localize_course(raw_course, code)
            figure = build_lab_figure(course, language_code=code)
            visible_copy = figure.to_json()
            leaks = [phrase for phrase in leaked_phrases if phrase in visible_copy]

            assert figure.layout.meta["language"] == code
            assert figure.layout.title.text == f"{course['title']} · {tr('experiment', code)}"
            if code != "pcm":  # Nigerian Pidgin legitimately shares English-derived vocabulary.
                assert not leaks, (course["id"], code, leaks)
