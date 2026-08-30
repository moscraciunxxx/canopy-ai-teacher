"""Contracts for the multi-subject academy catalogue."""

from __future__ import annotations

from src.curriculum_atlas import (
    course_nodes,
    course_practice,
    default_course_id,
    get_academies,
    get_course,
    get_courses,
)


def test_academies_cover_stem_and_human_worlds() -> None:
    academies = get_academies()
    assert [academy["id"] for academy in academies] == ["stem", "human-worlds"]
    assert len(get_courses("stem")) == 5
    assert len(get_courses("human-worlds")) == 4
    assert default_course_id("stem") == "physics-flight"
    assert default_course_id("human-worlds") == "history-sources"


def test_every_course_has_a_complete_learning_contract() -> None:
    courses = get_courses()
    assert len(courses) == 9
    assert len({course["id"] for course in courses}) == len(courses)
    assert len({course["lab_kind"] for course in courses}) == len(courses)

    for course in courses:
        nodes = course_nodes(course)
        practice = course_practice(course)
        assert len(nodes) == 6
        assert len({node["id"] for node in nodes}) == 6
        assert all(len(node["explain_steps"]) == 3 for node in nodes)
        assert len(practice) == 3
        assert all(item["required_terms"] for item in practice)
        assert len(course["diagnostic_groups"]) == 4
        assert course["flashcards"]
        assert course["sources"]
        assert all(source["url"].startswith("https://") for source in course["sources"])


def test_catalogue_returns_independent_records() -> None:
    first = get_course("physics-flight")
    first["title"] = "mutated"
    first["path"][0]["label"] = "mutated"

    fresh = get_course("physics-flight")
    assert fresh["title"] == "Motion in 3D"
    assert fresh["path"][0]["label"] == "Read the flight"

