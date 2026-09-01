"""Export the canonical Canopy curriculum for the browser companion.

The Python curriculum remains the source of truth.  This script materializes a
versioned JSON snapshot with stable IDs and localized presentation overlays.
It intentionally omits learner state and provider credentials.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.curriculum_atlas import get_academies, get_courses
from src.localization import (
    academy_description,
    academy_label,
    get_languages,
    localize_course,
    message_keys,
    tr,
)

OUTPUT = ROOT / "canopy-web" / "data" / "catalog.json"


def _stage(item: dict[str, Any], order: int) -> dict[str, Any]:
    steps = []
    for raw in item.get("explain_steps", ()):
        title, model, body = raw
        steps.append({"title": title, "model": model, "body": body})
    return {
        "id": item["id"],
        "order": order,
        "shortLabel": item["short"],
        "label": item["label"],
        "icon": item["icon"],
        "color": item["color"],
        "model": item["equation"],
        "question": item["question"],
        "description": item["description"],
        "hint": item["hint"],
        "explainSteps": steps,
    }


def _practice(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "title": item["title"],
        "model": item["equation"],
        "question": item["question"],
        "answerType": item["answer_type"],
        "acceptedAnswers": item["accepted_answers"],
        "requiredTerms": item["required_terms"],
        "skill": item["skill"],
        "transfer": item["transfer"],
        "hints": item["hint_ladder"],
        "difficulty": item["difficulty"],
        "explanation": item["explanation"],
    }


def _course(course: dict[str, Any]) -> dict[str, Any]:
    sources = [
        {"id": f"{course['id']}:source:{index}", **source}
        for index, source in enumerate(course["sources"])
    ]
    return {
        "id": course["id"],
        "academyId": course["academy"],
        "subject": course["subject"],
        "title": course["title"],
        "subtitle": course["subtitle"],
        "icon": course["icon"],
        "accent": course["accent"],
        "ageBand": course["age_band"],
        "labKind": course["lab_kind"],
        "bigQuestion": course["big_question"],
        "misconception": course["misconception"],
        "transferPrompt": course["transfer_prompt"],
        "roleplayPrompt": course["roleplay_prompt"],
        "diagnosticGroups": course["diagnostic_groups"],
        "stages": [_stage(node, index) for index, node in enumerate(course["path"])],
        "practice": [_practice(item) for item in course["practice"]],
        "flashcards": course["flashcards"],
        "sources": sources,
    }


def build_catalog() -> dict[str, Any]:
    courses = [dict(course) for course in get_courses()]
    languages = get_languages()
    keys = message_keys()
    locales: dict[str, Any] = {}
    for language in languages:
        code = language["code"]
        locales[code] = {
            "meta": language,
            "messages": {key: tr(key, code) for key in keys},
            "academyLabels": {
                academy["id"]: academy_label(academy["id"], code)
                for academy in get_academies()
            },
            "academyDescriptions": {
                academy["id"]: academy_description(academy["id"], code)
                for academy in get_academies()
            },
            "courses": {
                course["id"]: _course(dict(localize_course(course, code)))
                for course in courses
            },
        }

    return {
        "schemaVersion": "canopy.content.v1",
        "defaultLocale": "en",
        "academies": [
            {
                "id": academy["id"],
                "label": academy["label"],
                "shortLabel": academy["short_label"],
                "icon": academy["icon"],
                "description": academy["description"],
            }
            for academy in get_academies()
        ],
        "courses": [_course(course) for course in courses],
        "locales": locales,
    }


def main() -> None:
    catalog = build_catalog()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Exported {len(catalog['courses'])} courses and "
        f"{len(catalog['locales'])} locales to {OUTPUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
