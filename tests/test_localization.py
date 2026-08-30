"""Coverage and safety contracts for Canopy's multilingual academy."""

from __future__ import annotations

from app import multilingual_diagnose
from src.curriculum_atlas import get_courses
from src.localization import (
    answer_extent,
    course_label,
    get_language,
    get_languages,
    is_rtl,
    localize_course,
    message_keys,
    reasoning_signals,
    tr,
)


def test_catalogue_has_twenty_unique_bcp47_locales() -> None:
    languages = get_languages()
    codes = [language["code"] for language in languages]
    tags = [language["bcp47"] for language in languages]

    assert len(languages) == 20
    assert len(set(codes)) == 20
    assert len(set(tags)) == 20
    assert codes[0] == "en"
    assert "ro" in codes
    assert "ta" not in codes
    assert get_language("ro")["native_name"] == "Română"
    assert get_language("zh-Hans")["code"] == "zh"
    assert get_language("unknown")["code"] == "en"
    assert {language["code"] for language in languages if language["direction"] == "rtl"} == {"ar", "ur"}
    assert is_rtl("ar") and is_rtl("ur")
    assert not is_rtl("es")


def test_every_locale_fills_the_complete_message_and_course_contract() -> None:
    languages = get_languages()
    courses = get_courses()

    assert len(message_keys()) >= 40
    for language in languages:
        code = language["code"]
        assert all(tr(key, code).strip() for key in message_keys())
        for course in courses:
            subject, title = course_label(str(course["id"]), code)
            assert subject.strip()
            assert title.strip()


def test_localized_courses_preserve_ids_not_spoken_english_presentation_copy() -> None:
    courses = get_courses()
    for language in get_languages():
        code = language["code"]
        for course in courses:
            localized = localize_course(course, code)
            assert localized["id"] == course["id"]
            assert localized["academy"] == course["academy"]
            assert localized["lab_kind"] == course["lab_kind"]
            assert len(localized["path"]) == len(course["path"]) == 6
            assert len(localized["practice"]) == len(course["practice"]) == 3
            assert [node["id"] for node in localized["path"]] == [node["id"] for node in course["path"]]
            assert [source["url"] for source in localized["sources"]] == [source["url"] for source in course["sources"]]
            if code == "en":
                assert [node["equation"] for node in localized["path"]] == [node["equation"] for node in course["path"]]
                assert [source["label"] for source in localized["sources"]] == [source["label"] for source in course["sources"]]
            else:
                assert all(str(node["equation"]).strip() for node in localized["path"])
                assert all(str(item["equation"]).strip() for item in localized["practice"])
                assert all(
                    str(source["label"]).startswith(tr("sources", code))
                    for source in localized["sources"]
                )

    physics = next(course for course in courses if course["id"] == "physics-flight")
    assert localize_course(physics, "es")["title"] == "Movimiento en 3D"
    assert localize_course(physics, "ar")["subject"] == "الفيزياء"
    assert localize_course(physics, "ro")["title"] == "Mișcare în 3D"
    assert physics["title"] == "Motion in 3D"


def test_non_english_course_models_remove_canonical_english_prose() -> None:
    leaked_phrases = (
        "period =",
        "surface → model → prediction",
        "angle × speed × gravity",
        "air resistance",
        "constraint → model → test",
        "Earth g=",
        "Moon g=",
        "barrier=",
        "target=",
        "base change",
        "structure → information → function",
        "atmosphere ↔ land",
        "reservoir → flux",
        "sources − sinks",
        "millions of years",
        "ocean release",
        "impact × scale",
        "forest ↔ atmosphere",
        "respiration vs weathering",
        "emissions ↓",
        "frontier = candidates",
        "first in, first out",
        "last in, first out",
        "visited prevents cycles",
        "goal + constraints",
        "shortest route",
        "detail → question",
        "creator + audience",
        "automatic falsehood",
        "agreement + tension",
        "claim + evidence",
        "speech by movement organizer",
        "opposition pamphlet",
        "source set",
        "word/image/action",
        "motif across acts",
        "language ↔ choice",
        "same event, new lens",
        "blood imagery",
        "driven only by prophecy",
        "checkable evidence",
        "post → report → dataset",
        "who + when + method",
        "independent evidence",
        "supported / uncertain",
        "anonymous screenshot",
        "partial data",
        "decision → people → impacts",
        "probability × magnitude",
        "some actions may be impermissible",
        "consequence ↔ duty",
        "moral risk",
        "facial-recognition policy",
        "violates consent",
        "severe irreversible harm",
    )
    for language in get_languages():
        code = language["code"]
        if code == "en":
            continue
        for course in get_courses():
            localized = localize_course(course, code)
            visible_models = " ".join(
                [str(node["equation"]) for node in localized["path"]]
                + [str(item["equation"]) for item in localized["practice"]]
                + [str(source["label"]) for source in localized["sources"]]
            )
            leaks = [phrase for phrase in leaked_phrases if phrase in visible_models]
            assert not leaks, (course["id"], code, leaks)

    romanian_cs = localize_course(next(c for c in get_courses() if c["id"] == "cs-networks"), "ro")
    assert romanian_cs["path"][2]["equation"] == "Q = [v₁, v₂, …, vₙ] → v₁"
    assert tr("current_focus", "ro") == "OBIECTIV CURENT"
    assert tr("remix", "ro") == "Variații · Practică"


def test_reasoning_extent_and_markers_are_script_aware() -> None:
    assert answer_extent("uno dos tres cuatro", "es") == 4
    assert answer_extent("因为模型变化，所以证据也变化。", "zh") >= 10
    assert {"porque", "evidencia", "modelo"}.issubset(
        set(reasoning_signals("Porque la evidencia cambia cuando cambia el modelo.", "es"))
    )
    assert {"因为", "证据", "模型"}.issubset(set(reasoning_signals("因为模型变化，所以证据变化。", "zh")))
    assert {"لأن", "دليل", "نموذج"}.issubset(set(reasoning_signals("لأن هذا نموذج، فهناك دليل على التغير.", "ar")))
    assert {"deoarece", "dovezi", "model"}.issubset(
        set(reasoning_signals("Deoarece modelul se schimbă, dovezile susțin o altă sursă.", "ro"))
    )


def test_multilingual_feedback_never_fakes_semantic_correctness() -> None:
    feedback = multilingual_diagnose(
        "Porque la evidencia del modelo cambia, explico el resultado y comparo otra fuente antes de concluir.",
        "¿Qué muestra el modelo?",
        "Cambia una variable cada vez.",
        "es",
    )
    assert feedback["kind"] == "success"
    assert feedback["correct"] is False
    assert "multilingual_structure_only" in feedback["safety_flags"]
    assert len(feedback["signals"]) >= 2

    empty = multilingual_diagnose("", "问题", "提示", "zh")
    assert empty["kind"] == "warning"
    assert empty["correct"] is False
