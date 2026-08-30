"""Interactive Plotly laboratories for the multi-subject Canopy academy.

Every course gets a visual model whose controls change an interpretable
relationship. Plotly renders the figures in the browser, so rotation, zoom,
hover inspection, and most animation work do not depend on a high-end local
GPU. The figures are deliberately deterministic so they are easy to test.
"""

from __future__ import annotations

from collections import deque
from math import cos, pi, radians, sin
from typing import Any, Literal, Mapping, NotRequired, TypedDict, cast

import plotly.graph_objects as go

from src.lab_localization import lab_option_label, lab_tr
from src.localization import get_language, get_stages, tr


ControlKind = Literal["slider", "select"]
LabValue = float | int | str


class ControlSpec(TypedDict):
    """One framework-agnostic control rendered by the Streamlit app."""

    key: str
    label: str
    kind: ControlKind
    default: LabValue
    help: str
    minimum: NotRequired[float]
    maximum: NotRequired[float]
    step: NotRequired[float]
    options: NotRequired[list[str]]
    format: NotRequired[str]


_MINT = "#76f2c0"
_BLUE = "#8edbff"
_CORAL = "#ff897a"
_VIOLET = "#a998ff"
_GOLD = "#ffd66e"
_INK = "#dcecf1"
_MUTED = "#86a1aa"
_GRID = "rgba(126, 175, 187, 0.16)"
_PAPER = "rgba(0,0,0,0)"


_CONTROLS: dict[str, tuple[ControlSpec, ...]] = {
    "surface": (
        {
            "key": "amplitude",
            "label": "Amplitude",
            "kind": "slider",
            "default": 1.8,
            "minimum": -3.0,
            "maximum": 3.0,
            "step": 0.1,
            "format": "%.1f",
            "help": "Vertical scale: the height and orientation of peaks.",
        },
        {
            "key": "frequency",
            "label": "Frequency",
            "kind": "slider",
            "default": 1.5,
            "minimum": 0.5,
            "maximum": 4.0,
            "step": 0.1,
            "format": "%.1f",
            "help": "How rapidly the pattern repeats across both inputs.",
        },
        {
            "key": "phase",
            "label": "Phase shift",
            "kind": "slider",
            "default": 0.0,
            "minimum": -3.14,
            "maximum": 3.14,
            "step": 0.1,
            "format": "%.1f",
            "help": "Slides the pattern without changing its shape.",
        },
    ),
    "projectile": (
        {
            "key": "speed",
            "label": "Launch speed · m/s",
            "kind": "slider",
            "default": 18.0,
            "minimum": 8.0,
            "maximum": 34.0,
            "step": 0.5,
            "format": "%.1f",
            "help": "Magnitude of the initial velocity vector.",
        },
        {
            "key": "angle",
            "label": "Launch angle · degrees",
            "kind": "slider",
            "default": 42.0,
            "minimum": 10.0,
            "maximum": 80.0,
            "step": 1.0,
            "format": "%.0f",
            "help": "Redistributes velocity between forward and vertical motion.",
        },
        {
            "key": "gravity",
            "label": "Gravity · m/s²",
            "kind": "slider",
            "default": 9.81,
            "minimum": 1.6,
            "maximum": 15.0,
            "step": 0.1,
            "format": "%.1f",
            "help": "Downward acceleration in the idealized model.",
        },
        {
            "key": "crosswind",
            "label": "Crosswind drift · m/s",
            "kind": "slider",
            "default": 0.8,
            "minimum": -4.0,
            "maximum": 4.0,
            "step": 0.2,
            "format": "%.1f",
            "help": "A simplified constant sideways velocity.",
        },
    ),
    "dna": (
        {
            "key": "turns",
            "label": "Helix turns",
            "kind": "slider",
            "default": 4,
            "minimum": 2,
            "maximum": 8,
            "step": 1,
            "format": "%.0f",
            "help": "Changes the twist while preserving complementary pairing.",
        },
        {
            "key": "variant_position",
            "label": "Variant position",
            "kind": "slider",
            "default": 9,
            "minimum": 0,
            "maximum": 23,
            "step": 1,
            "format": "%.0f",
            "help": "Highlights one base pair and its position within a codon.",
        },
        {
            "key": "view",
            "label": "Sequence view",
            "kind": "select",
            "default": "Variant",
            "options": ["Original", "Variant"],
            "help": "Compare the reference pair with a one-base substitution.",
        },
    ),
    "carbon": (
        {
            "key": "emissions",
            "label": "Fossil flux · baseline multiplier",
            "kind": "slider",
            "default": 1.0,
            "minimum": 0.0,
            "maximum": 2.0,
            "step": 0.1,
            "format": "%.1f×",
            "help": "Scales the modeled transfer from fossil stores to atmosphere.",
        },
        {
            "key": "land_uptake",
            "label": "Land uptake · baseline multiplier",
            "kind": "slider",
            "default": 1.0,
            "minimum": 0.5,
            "maximum": 1.5,
            "step": 0.05,
            "format": "%.2f×",
            "help": "Scales photosynthetic transfer into the land system.",
        },
        {
            "key": "ocean_uptake",
            "label": "Ocean uptake · baseline multiplier",
            "kind": "slider",
            "default": 1.0,
            "minimum": 0.5,
            "maximum": 1.5,
            "step": 0.05,
            "format": "%.2f×",
            "help": "Scales exchange from atmosphere into the surface ocean.",
        },
    ),
    "network": (
        {
            "key": "algorithm",
            "label": "Traversal strategy",
            "kind": "select",
            "default": "Breadth-first",
            "options": ["Breadth-first", "Depth-first"],
            "help": "A queue explores layers; a stack follows one branch deeply.",
        },
        {
            "key": "start",
            "label": "Start node",
            "kind": "select",
            "default": "A",
            "options": ["A", "B", "C", "D"],
            "help": "Changes the root of the search tree.",
        },
        {
            "key": "target",
            "label": "Target node",
            "kind": "select",
            "default": "H",
            "options": ["E", "F", "G", "H", "I"],
            "help": "Traversal stops when this node is discovered.",
        },
    ),
    "sources": (
        {
            "key": "lens",
            "label": "Evidence lens",
            "kind": "select",
            "default": "Corroboration",
            "options": ["Context", "Purpose", "Corroboration"],
            "help": "Changes which source relationship receives visual emphasis.",
        },
        {
            "key": "minimum_proximity",
            "label": "Minimum event proximity",
            "kind": "slider",
            "default": 0.0,
            "minimum": 0.0,
            "maximum": 0.8,
            "step": 0.1,
            "format": "%.1f",
            "help": "Filters sources by how directly they connect to the event or debate.",
        },
        {
            "key": "include_opposition",
            "label": "Perspective set",
            "kind": "select",
            "default": "Include disagreement",
            "options": ["Include disagreement", "Only supportive"],
            "help": "Tests what happens when inconvenient voices are removed.",
        },
    ),
    "narrative": (
        {
            "key": "motif",
            "label": "Motif lens",
            "kind": "select",
            "default": "Guilt",
            "options": ["Ambition", "Guilt", "Disorder"],
            "help": "Changes the recurring pattern traced across the acts.",
        },
        {
            "key": "perspective",
            "label": "Character perspective",
            "kind": "select",
            "default": "Macbeth",
            "options": ["Macbeth", "Lady Macbeth", "Banquo"],
            "help": "Changes which decisions anchor the interpretive path.",
        },
        {
            "key": "ambiguity",
            "label": "Counter-reading strength",
            "kind": "slider",
            "default": 0.45,
            "minimum": 0.0,
            "maximum": 1.0,
            "step": 0.05,
            "format": "%.2f",
            "help": "Makes the competing interpretation more or less prominent.",
        },
    ),
    "claims": (
        {
            "key": "independent_sources",
            "label": "Independent confirmations",
            "kind": "slider",
            "default": 1,
            "minimum": 0,
            "maximum": 3,
            "step": 1,
            "format": "%.0f",
            "help": "Counts independent evidence chains, not repeated posts.",
        },
        {
            "key": "context",
            "label": "Context recovered · %",
            "kind": "slider",
            "default": 55,
            "minimum": 0,
            "maximum": 100,
            "step": 5,
            "format": "%.0f%%",
            "help": "Represents method, denominator, timeframe, and surrounding material.",
        },
        {
            "key": "original_found",
            "label": "Original evidence",
            "kind": "select",
            "default": "Located",
            "options": ["Located", "Missing"],
            "help": "Whether the underlying report, dataset, recording, or document is available.",
        },
    ),
    "ethics": (
        {
            "key": "outcome_weight",
            "label": "Outcome lens",
            "kind": "slider",
            "default": 0.65,
            "minimum": 0.0,
            "maximum": 1.0,
            "step": 0.05,
            "format": "%.2f",
            "help": "How strongly the map foregrounds expected benefits and harms.",
        },
        {
            "key": "rights_weight",
            "label": "Rights & duties lens",
            "kind": "slider",
            "default": 0.75,
            "minimum": 0.0,
            "maximum": 1.0,
            "step": 0.05,
            "format": "%.2f",
            "help": "How strongly the map foregrounds constraints and consent.",
        },
        {
            "key": "uncertainty",
            "label": "Uncertainty",
            "kind": "slider",
            "default": 0.35,
            "minimum": 0.0,
            "maximum": 1.0,
            "step": 0.05,
            "format": "%.2f",
            "help": "Raises caution where evidence is incomplete or harm may be irreversible.",
        },
    ),
}


def _linspace(start: float, stop: float, count: int) -> list[float]:
    if count <= 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + index * step for index in range(count)]


def _number(values: Mapping[str, LabValue], key: str, default: float) -> float:
    value = values.get(key, default)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(values: Mapping[str, LabValue], key: str, default: str) -> str:
    value = values.get(key, default)
    return str(value)


def _kind(course: Mapping[str, Any] | str) -> str:
    if isinstance(course, str):
        return course
    return str(course.get("lab_kind", "surface"))


def _course_id(course: Mapping[str, Any] | str) -> str:
    if isinstance(course, str):
        return course
    return str(course.get("id", course.get("lab_kind", "lab")))


def _course_title(course: Mapping[str, Any] | str) -> str:
    if isinstance(course, str):
        return ""
    return str(course.get("title", ""))


def _is_english(code: str) -> bool:
    return get_language(code)["code"] == "en"


def _copy(code: str, english: str, key: str) -> str:
    return english if _is_english(code) else lab_tr(key, code)


def _figure_title(code: str, course_title: str, english: str) -> str:
    if _is_english(code):
        return english
    title = course_title or tr("interactive_lab", code)
    return f"{title} · {tr('experiment', code)}"


def lab_control_specs(course: Mapping[str, Any] | str) -> tuple[ControlSpec, ...]:
    """Return independent control definitions for a course or lab kind."""

    kind = _kind(course)
    if kind not in _CONTROLS:
        raise KeyError(f"Unknown lab kind: {kind}")
    return tuple(cast(ControlSpec, dict(spec)) for spec in _CONTROLS[kind])


def default_lab_values(course: Mapping[str, Any] | str) -> dict[str, LabValue]:
    """Return stable default values for every control in a lab."""

    return {spec["key"]: spec["default"] for spec in lab_control_specs(course)}


def _base_layout(title: str) -> dict[str, Any]:
    return {
        "title": {"text": title, "x": 0.02, "xanchor": "left", "font": {"size": 17, "color": _INK}},
        "paper_bgcolor": _PAPER,
        "plot_bgcolor": _PAPER,
        "font": {"family": "Inter, ui-sans-serif, system-ui", "color": _INK},
        "margin": {"l": 12, "r": 12, "t": 58, "b": 12},
        "hoverlabel": {"bgcolor": "#10252d", "bordercolor": _MINT, "font": {"color": "#f4fbfc"}},
        "legend": {
            "bgcolor": "rgba(8, 26, 33, 0.7)",
            "bordercolor": "rgba(142, 219, 255, 0.15)",
            "font": {"size": 11},
        },
        "uirevision": "canopy-lab",
    }


def _scene(x_title: str, y_title: str, z_title: str) -> dict[str, Any]:
    axis = {
        "backgroundcolor": "rgba(8, 27, 34, 0.55)",
        "gridcolor": _GRID,
        "zerolinecolor": "rgba(255,255,255,0.2)",
        "showbackground": True,
        "tickfont": {"color": _MUTED, "size": 10},
    }
    return {
        "xaxis": {**axis, "title": {"text": x_title, "font": {"color": _INK, "size": 11}}},
        "yaxis": {**axis, "title": {"text": y_title, "font": {"color": _INK, "size": 11}}},
        "zaxis": {**axis, "title": {"text": z_title, "font": {"color": _INK, "size": 11}}},
        "camera": {"eye": {"x": 1.48, "y": 1.45, "z": 1.15}},
        "aspectmode": "auto",
    }


def _surface_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    amplitude = _number(values, "amplitude", 1.8)
    frequency = _number(values, "frequency", 1.5)
    phase = _number(values, "phase", 0.0)
    coordinates = _linspace(-pi, pi, 35)
    z_values = [
        [amplitude * sin(frequency * x + phase) * cos(frequency * y) for x in coordinates]
        for y in coordinates
    ]
    cross_section = [amplitude * sin(frequency * x + phase) for x in coordinates]

    figure = go.Figure()
    figure.add_trace(
        go.Surface(
            x=coordinates,
            y=coordinates,
            z=z_values,
            colorscale=[
                [0.0, "#4a3a9a"],
                [0.25, "#5278d5"],
                [0.5, "#163c43"],
                [0.72, "#40d9af"],
                [1.0, "#ffe06f"],
            ],
            colorbar={"title": "output z" if _is_english(language_code) else "z", "thickness": 10, "len": 0.65},
            contours={
                "z": {
                    "show": True,
                    "usecolormap": True,
                    "highlightcolor": _CORAL,
                    "project_z": True,
                }
            },
            hovertemplate=(
                "x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}"
                f"<extra>{'surface' if _is_english(language_code) else tr('model', language_code)}</extra>"
            ),
            opacity=0.92,
            name="Function surface" if _is_english(language_code) else tr("model", language_code),
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=coordinates,
            y=[0.0] * len(coordinates),
            z=cross_section,
            mode="lines",
            line={"color": _CORAL, "width": 7},
            name="y = 0 slice" if _is_english(language_code) else f"{tr('evidence', language_code)} · y=0",
            hovertemplate=(
                "x=%{x:.2f}<br>z=%{z:.2f}"
                f"<extra>{'cross-section' if _is_english(language_code) else tr('evidence', language_code)}</extra>"
            ),
        )
    )
    layout = _base_layout(
        _figure_title(
            language_code,
            course_title,
            "Parameter landscape · rotate, zoom, and inspect a cross-section",
        )
    )
    layout["scene"] = _scene("input x", "input y", "output z") if _is_english(language_code) else _scene("x", "y", "z")
    figure.update_layout(**layout)
    return figure


def _projectile_state(values: Mapping[str, LabValue]) -> dict[str, float]:
    speed = _number(values, "speed", 18.0)
    angle = radians(_number(values, "angle", 42.0))
    gravity = max(_number(values, "gravity", 9.81), 0.1)
    crosswind = _number(values, "crosswind", 0.8)
    vertical = speed * sin(angle)
    forward = speed * cos(angle)
    time_of_flight = max(2.0 * vertical / gravity, 0.01)
    return {
        "speed": speed,
        "angle": angle,
        "gravity": gravity,
        "crosswind": crosswind,
        "vertical": vertical,
        "forward": forward,
        "time": time_of_flight,
        "range": forward * time_of_flight,
        "drift": crosswind * time_of_flight,
        "height": vertical * vertical / (2.0 * gravity),
    }


def _projectile_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    state = _projectile_state(values)
    times = _linspace(0.0, state["time"], 65)
    x_values = [state["forward"] * time for time in times]
    y_values = [state["crosswind"] * time for time in times]
    z_values = [
        max(state["vertical"] * time - 0.5 * state["gravity"] * time * time, 0.0)
        for time in times
    ]
    custom = [
        [time, state["forward"], state["crosswind"], state["vertical"] - state["gravity"] * time]
        for time in times
    ]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter3d(
            x=x_values,
            y=y_values,
            z=z_values,
            mode="lines+markers",
            line={"color": _BLUE, "width": 8},
            marker={
                "size": 3,
                "color": times,
                "colorscale": [[0, _MINT], [0.55, _GOLD], [1, _CORAL]],
                "showscale": False,
            },
            customdata=custom,
            hovertemplate=(
                (
                    "t=%{customdata[0]:.2f} s<br>"
                    "position=(%{x:.1f}, %{y:.1f}, %{z:.1f}) m<br>"
                    "velocity=(%{customdata[1]:.1f}, %{customdata[2]:.1f}, %{customdata[3]:.1f}) m/s"
                    "<extra>trajectory</extra>"
                )
                if _is_english(language_code)
                else (
                    "t=%{customdata[0]:.2f} s<br>"
                    "(x, y, z)=(%{x:.1f}, %{y:.1f}, %{z:.1f}) m<br>"
                    "(vₓ, vᵧ, vᵤ)=(%{customdata[1]:.1f}, %{customdata[2]:.1f}, %{customdata[3]:.1f}) m/s"
                    f"<extra>{lab_tr('predicted_path', language_code)}</extra>"
                )
            ),
            name=_copy(language_code, "Predicted path", "predicted_path"),
        )
    )
    figure.add_trace(
        go.Surface(
            x=[[14.0, 14.0], [14.0, 14.0]],
            y=[[-3.0, 3.0], [-3.0, 3.0]],
            z=[[0.0, 0.0], [8.0, 8.0]],
            surfacecolor=[[0.0, 0.0], [1.0, 1.0]],
            colorscale=[[0, "rgba(255,137,122,0.25)"], [1, _CORAL]],
            showscale=False,
            opacity=0.48,
            hovertemplate=(
                "Barrier · 8 m high<extra></extra>"
                if _is_english(language_code)
                else f"{lab_tr('barrier', language_code)} · 8 m<extra></extra>"
            ),
            name="8 m barrier" if _is_english(language_code) else f"{lab_tr('barrier', language_code)} · 8 m",
        )
    )
    figure.add_trace(
        go.Mesh3d(
            x=[28, 34, 34, 28],
            y=[-3, -3, 3, 3],
            z=[0, 0, 0, 0],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color=_MINT,
            opacity=0.28,
            hovertemplate=(
                "Target zone · x=28–34 m<extra></extra>"
                if _is_english(language_code)
                else f"{lab_tr('target_zone', language_code)} · x=28–34 m<extra></extra>"
            ),
            name=_copy(language_code, "Target zone", "target_zone"),
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=[x_values[-1]],
            y=[y_values[-1]],
            z=[0],
            mode="markers+text",
            marker={"size": 8, "color": _GOLD, "symbol": "diamond"},
            text=["landing" if _is_english(language_code) else "◆"],
            textposition="top center",
            name=_copy(language_code, "Landing point", "landing_point"),
            hovertemplate=(
                "landing=(%{x:.1f}, %{y:.1f}) m<extra></extra>"
                if _is_english(language_code)
                else f"{lab_tr('landing_point', language_code)}=(%{{x:.1f}}, %{{y:.1f}}) m<extra></extra>"
            ),
        )
    )
    layout = _base_layout(
        _figure_title(language_code, course_title, "Trajectory laboratory · an idealized three-component launch")
    )
    layout["scene"] = {
        **(
            _scene("forward x · m", "sideways y · m", "height z · m")
            if _is_english(language_code)
            else _scene("x · m", "y · m", "z · m")
        ),
        "aspectratio": {"x": 1.8, "y": 0.65, "z": 0.8},
    }
    figure.update_layout(**layout)
    return figure


_BASE_SEQUENCE = ("A", "C", "T", "G", "G", "A", "T", "C") * 3
_COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C"}
_BASE_COLORS = {"A": _MINT, "T": _CORAL, "C": _BLUE, "G": _GOLD}


def _dna_state(values: Mapping[str, LabValue]) -> dict[str, Any]:
    turns = int(round(_number(values, "turns", 4)))
    position = int(round(_number(values, "variant_position", 9))) % len(_BASE_SEQUENCE)
    view = _text(values, "view", "Variant")
    first = list(_BASE_SEQUENCE)
    original = first[position]
    if view == "Variant":
        alternatives = [base for base in ("A", "C", "G", "T") if base != original]
        first[position] = alternatives[position % len(alternatives)]
    second = [_COMPLEMENT[base] for base in first]
    return {
        "turns": turns,
        "position": position,
        "view": view,
        "original": original,
        "first": first,
        "second": second,
    }


def _dna_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    state = _dna_state(values)
    count = len(_BASE_SEQUENCE)
    z_values = _linspace(-3.2, 3.2, count)
    angles = [2 * pi * state["turns"] * index / (count - 1) for index in range(count)]
    x_first = [cos(angle) for angle in angles]
    y_first = [sin(angle) for angle in angles]
    x_second = [-value for value in x_first]
    y_second = [-value for value in y_first]
    first = state["first"]
    second = state["second"]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter3d(
            x=x_first,
            y=y_first,
            z=z_values,
            mode="lines+markers",
            line={"color": _VIOLET, "width": 7},
            marker={"size": 5, "color": [_BASE_COLORS[base] for base in first]},
            customdata=[[index, base] for index, base in enumerate(first)],
            hovertemplate=(
                "strand 1 · position %{customdata[0]} · %{customdata[1]}<extra></extra>"
                if _is_english(language_code)
                else f"# %{{customdata[0]}} · %{{customdata[1]}}<extra>{lab_tr('strand_1', language_code)}</extra>"
            ),
            name=_copy(language_code, "Strand 1", "strand_1"),
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=x_second,
            y=y_second,
            z=z_values,
            mode="lines+markers",
            line={"color": _BLUE, "width": 7},
            marker={"size": 5, "color": [_BASE_COLORS[base] for base in second]},
            customdata=[[index, base] for index, base in enumerate(second)],
            hovertemplate=(
                "strand 2 · position %{customdata[0]} · %{customdata[1]}<extra></extra>"
                if _is_english(language_code)
                else f"# %{{customdata[0]}} · %{{customdata[1]}}<extra>{lab_tr('strand_2', language_code)}</extra>"
            ),
            name=_copy(language_code, "Complement", "complement"),
        )
    )
    for index in range(0, count, 2):
        is_variant = index == state["position"]
        figure.add_trace(
            go.Scatter3d(
                x=[x_first[index], x_second[index]],
                y=[y_first[index], y_second[index]],
                z=[z_values[index], z_values[index]],
                mode="lines",
                line={"color": _CORAL if is_variant else "rgba(220,236,241,0.34)", "width": 9 if is_variant else 3},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    position = state["position"]
    figure.add_trace(
        go.Scatter3d(
            x=[x_first[position], x_second[position]],
            y=[y_first[position], y_second[position]],
            z=[z_values[position], z_values[position]],
            mode="markers+lines+text",
            marker={"size": 9, "color": _CORAL, "line": {"color": "#ffffff", "width": 1}},
            line={"color": _CORAL, "width": 10},
            text=[f"{first[position]} · variant" if _is_english(language_code) else f"{first[position]} · Δ", second[position]],
            textposition="top center",
            customdata=[[position, first[position]], [position, second[position]]],
            hovertemplate=(
                "highlighted pair · %{customdata[1]} · position %{customdata[0]}<extra></extra>"
                if _is_english(language_code)
                else f"%{{customdata[1]}} · # %{{customdata[0]}}<extra>{lab_tr('selected_pair', language_code)}</extra>"
            ),
            name=_copy(language_code, "Selected base pair", "selected_pair"),
        )
    )
    layout = _base_layout(
        _figure_title(language_code, course_title, "Molecular information model · structure, pairing, and variation")
    )
    scene = _scene("helix x", "helix y", "sequence position") if _is_english(language_code) else _scene("x", "y", "#")
    scene["xaxis"]["showticklabels"] = False
    scene["yaxis"]["showticklabels"] = False
    layout["scene"] = {**scene, "aspectratio": {"x": 0.8, "y": 0.8, "z": 1.8}}
    figure.update_layout(**layout)
    return figure


def _carbon_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    emissions = _number(values, "emissions", 1.0)
    land = _number(values, "land_uptake", 1.0)
    ocean = _number(values, "ocean_uptake", 1.0)
    label_keys = (
        "atmosphere",
        "plants",
        "soils",
        "surface_ocean",
        "deep_ocean",
        "fossil_stores",
        "rocks_sediments",
    )
    labels = [lab_tr(key, language_code) for key in label_keys]
    sources = [0, 1, 1, 2, 0, 3, 3, 4, 5, 6]
    targets = [1, 0, 2, 0, 3, 0, 4, 3, 0, 0]
    flux = [
        120 * land,
        60,
        60,
        59,
        92 * ocean,
        90,
        2.5 * ocean,
        1.8,
        10 * emissions,
        0.2,
    ]
    link_labels = [
        "photosynthesis",
        "plant respiration",
        "litter & transfer",
        "soil respiration",
        "air–sea uptake",
        "ocean release",
        "deep-ocean transfer",
        "upwelling",
        "human fossil flux",
        "slow geologic flux",
    ]
    link_colors = [
        "rgba(118,242,192,.45)",
        "rgba(118,242,192,.24)",
        "rgba(255,214,110,.32)",
        "rgba(255,214,110,.24)",
        "rgba(142,219,255,.45)",
        "rgba(142,219,255,.22)",
        "rgba(169,152,255,.34)",
        "rgba(169,152,255,.2)",
        "rgba(255,137,122,.62)",
        "rgba(220,236,241,.18)",
    ]
    figure = go.Figure(
        go.Sankey(
            arrangement="snap",
            node={
                "pad": 20,
                "thickness": 19,
                "line": {"color": "rgba(255,255,255,.32)", "width": 1},
                "label": labels,
                "color": [_BLUE, _MINT, _GOLD, "#54c5dc", _VIOLET, _CORAL, "#b9c5c9"],
                "hovertemplate": (
                    "%{label}<extra>carbon reservoir</extra>"
                    if _is_english(language_code)
                    else f"%{{label}}<extra>{tr('model', language_code)}</extra>"
                ),
            },
            link={
                "source": sources,
                "target": targets,
                "value": flux,
                "label": link_labels if _is_english(language_code) else [""] * len(link_labels),
                "color": link_colors,
                "hovertemplate": (
                    "%{label}<br>conceptual flux index: %{value:.1f}<extra></extra>"
                    if _is_english(language_code)
                    else f"%{{source.label}} → %{{target.label}}<br>{tr('result', language_code)}: %{{value:.1f}}<extra></extra>"
                ),
            },
        )
    )
    layout = _base_layout(
        _figure_title(language_code, course_title, "Carbon pathways · reservoir-to-reservoir flow")
    )
    layout["height"] = 530
    figure.update_layout(**layout)
    return figure


_GRAPH_POSITIONS: dict[str, tuple[float, float, float]] = {
    "A": (0.0, 0.0, 0.0),
    "B": (1.0, 1.0, 0.5),
    "C": (1.0, -1.0, -0.3),
    "D": (2.0, 1.4, 1.2),
    "E": (2.2, 0.2, 0.15),
    "F": (2.0, -1.35, -0.9),
    "G": (3.2, 1.0, 0.3),
    "H": (3.4, -0.25, 1.05),
    "I": (3.15, -1.35, -0.25),
}
_GRAPH_EDGES: tuple[tuple[str, str], ...] = (
    ("A", "B"),
    ("A", "C"),
    ("B", "D"),
    ("B", "E"),
    ("C", "E"),
    ("C", "F"),
    ("D", "G"),
    ("E", "G"),
    ("E", "H"),
    ("F", "H"),
    ("F", "I"),
    ("G", "H"),
    ("H", "I"),
)


def _adjacency() -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {node: [] for node in _GRAPH_POSITIONS}
    for first, second in _GRAPH_EDGES:
        graph[first].append(second)
        graph[second].append(first)
    for neighbours in graph.values():
        neighbours.sort()
    return graph


def _traverse(start: str, target: str, algorithm: str) -> tuple[list[str], list[str]]:
    graph = _adjacency()
    start = start if start in graph else "A"
    target = target if target in graph else "H"
    frontier: deque[str] | list[str]
    frontier = deque([start]) if algorithm == "Breadth-first" else [start]
    discovered = {start}
    parents: dict[str, str] = {}
    order: list[str] = []
    while frontier:
        current = frontier.popleft() if isinstance(frontier, deque) else frontier.pop()
        order.append(current)
        if current == target:
            break
        neighbours = graph[current]
        if algorithm != "Breadth-first":
            neighbours = list(reversed(neighbours))
        for neighbour in neighbours:
            if neighbour in discovered:
                continue
            discovered.add(neighbour)
            parents[neighbour] = current
            frontier.append(neighbour)
    path = [target] if target in order else []
    while path and path[-1] != start:
        parent = parents.get(path[-1])
        if parent is None:
            return order, []
        path.append(parent)
    path.reverse()
    return order, path


def _network_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    algorithm = _text(values, "algorithm", "Breadth-first")
    start = _text(values, "start", "A")
    target = _text(values, "target", "H")
    order, path = _traverse(start, target, algorithm)
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_z: list[float | None] = []
    for first, second in _GRAPH_EDGES:
        first_point = _GRAPH_POSITIONS[first]
        second_point = _GRAPH_POSITIONS[second]
        edge_x.extend([first_point[0], second_point[0], None])
        edge_y.extend([first_point[1], second_point[1], None])
        edge_z.extend([first_point[2], second_point[2], None])

    figure = go.Figure()
    figure.add_trace(
        go.Scatter3d(
            x=edge_x,
            y=edge_y,
            z=edge_z,
            mode="lines",
            line={"color": "rgba(142,219,255,.24)", "width": 3},
            hoverinfo="skip",
            name="Graph edges" if _is_english(language_code) else tr("model", language_code),
        )
    )
    if len(path) > 1:
        path_points = [_GRAPH_POSITIONS[node] for node in path]
        figure.add_trace(
            go.Scatter3d(
                x=[point[0] for point in path_points],
                y=[point[1] for point in path_points],
                z=[point[2] for point in path_points],
                mode="lines",
                line={"color": _CORAL, "width": 10},
                hoverinfo="skip",
                name="Discovered route" if _is_english(language_code) else tr("result", language_code),
            )
        )
    nodes = list(_GRAPH_POSITIONS)
    visit_index = {node: index + 1 for index, node in enumerate(order)}
    node_colors = [
        _GOLD if node == target else _MINT if node == start else _VIOLET if node in visit_index else "#36515b"
        for node in nodes
    ]
    custom = [
        [visit_index.get(node, "not visited" if _is_english(language_code) else "—"), node == target]
        for node in nodes
    ]
    figure.add_trace(
        go.Scatter3d(
            x=[_GRAPH_POSITIONS[node][0] for node in nodes],
            y=[_GRAPH_POSITIONS[node][1] for node in nodes],
            z=[_GRAPH_POSITIONS[node][2] for node in nodes],
            mode="markers+text",
            text=nodes,
            textposition="top center",
            marker={
                "size": [12 if node in {start, target} else 9 for node in nodes],
                "color": node_colors,
                "line": {"color": "#effcff", "width": 1},
            },
            customdata=custom,
            hovertemplate=(
                "node %{text}<br>visit order: %{customdata[0]}<extra></extra>"
                if _is_english(language_code)
                else f"%{{text}} · # %{{customdata[0]}}<extra>{tr('model', language_code)}</extra>"
            ),
            name="Nodes" if _is_english(language_code) else tr("model", language_code),
        )
    )
    layout = _base_layout(
        f"{algorithm} traversal · {start} → {target}"
        if _is_english(language_code)
        else _figure_title(language_code, course_title, "")
    )
    scene = _scene("layer", "branch", "structure") if _is_english(language_code) else _scene("x", "y", "z")
    scene["xaxis"]["showticklabels"] = False
    scene["yaxis"]["showticklabels"] = False
    scene["zaxis"]["showticklabels"] = False
    layout["scene"] = scene
    figure.update_layout(**layout)
    return figure


_HISTORY_SOURCES: tuple[dict[str, Any], ...] = (
    {"year": 1848, "proximity": 0.95, "stance": 0.82, "kind": "Primary", "label": "Seneca Falls declaration", "voice": "organizers"},
    {"year": 1851, "proximity": 0.88, "stance": 0.65, "kind": "Primary", "label": "Convention speech", "voice": "activist"},
    {"year": 1869, "proximity": 0.72, "stance": 0.74, "kind": "Primary", "label": "Movement newspaper", "voice": "movement press"},
    {"year": 1913, "proximity": 0.8, "stance": -0.72, "kind": "Primary", "label": "Anti-suffrage petition", "voice": "opposition"},
    {"year": 1917, "proximity": 0.9, "stance": 0.9, "kind": "Primary", "label": "Picket photograph", "voice": "public protest"},
    {"year": 1920, "proximity": 1.0, "stance": 0.2, "kind": "Primary", "label": "19th Amendment text", "voice": "law"},
    {"year": 1975, "proximity": 0.35, "stance": 0.35, "kind": "Secondary", "label": "Later historical synthesis", "voice": "historian"},
)


def _visible_history_sources(values: Mapping[str, LabValue]) -> list[dict[str, Any]]:
    threshold = _number(values, "minimum_proximity", 0.0)
    include_opposition = _text(values, "include_opposition", "Include disagreement") == "Include disagreement"
    return [
        source
        for source in _HISTORY_SOURCES
        if float(source["proximity"]) >= threshold and (include_opposition or float(source["stance"]) >= 0)
    ]


def _sources_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    lens = _text(values, "lens", "Corroboration")
    sources = _visible_history_sources(values)
    figure = go.Figure()
    if sources:
        emphasis = {
            "Context": [11 + 5 * float(source["proximity"]) for source in sources],
            "Purpose": [15 if abs(float(source["stance"])) > 0.6 else 10 for source in sources],
            "Corroboration": [15 if 1840 <= int(source["year"]) <= 1920 else 9 for source in sources],
        }[lens]
        colors = [_CORAL if float(source["stance"]) < 0 else _MINT if source["kind"] == "Primary" else _VIOLET for source in sources]
        figure.add_trace(
            go.Scatter3d(
                x=[source["year"] for source in sources],
                y=[source["proximity"] for source in sources],
                z=[source["stance"] for source in sources],
                mode="markers+text",
                text=[source["label"] for source in sources]
                if _is_english(language_code)
                else [str(source["year"]) for source in sources],
                textposition="top center",
                marker={"size": emphasis, "color": colors, "opacity": 0.9, "line": {"color": "#ffffff", "width": 1}},
                customdata=[[source["kind"], source["voice"]] for source in sources]
                if _is_english(language_code)
                else [[tr("evidence", language_code), tr("sources", language_code)] for _source in sources],
                hovertemplate=(
                    (
                        "%{text}<br>year=%{x}<br>event proximity=%{y:.2f}<br>"
                        "stance=%{z:.2f}<br>%{customdata[0]} · voice: %{customdata[1]}<extra></extra>"
                    )
                    if _is_english(language_code)
                    else (
                        "# %{x}<br>y=%{y:.2f}<br>z=%{z:.2f}"
                        f"<extra>{tr('sources', language_code)}</extra>"
                    )
                ),
                name=tr("sources", language_code),
            )
        )
        for first_index, first in enumerate(sources):
            for second in sources[first_index + 1 :]:
                if abs(int(first["year"]) - int(second["year"])) <= 20:
                    figure.add_trace(
                        go.Scatter3d(
                            x=[first["year"], second["year"]],
                            y=[first["proximity"], second["proximity"]],
                            z=[first["stance"], second["stance"]],
                            mode="lines",
                            line={
                                "color": "rgba(255,214,110,.5)" if lens == "Corroboration" else "rgba(142,219,255,.16)",
                                "width": 5 if lens == "Corroboration" else 2,
                            },
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )
    layout = _base_layout(
        f"Source constellation · {lens.lower()} lens"
        if _is_english(language_code)
        else _figure_title(language_code, course_title, "")
    )
    layout["scene"] = {
        **(_scene("chronology", "event proximity", "stance / perspective") if _is_english(language_code) else _scene("x", "y", "z")),
        "zaxis": {
            **_scene("", "", "")["zaxis"],
            "range": [-1.1, 1.1],
            "tickvals": [-1, 0, 1],
            "ticktext": ["opposes", "institutional", "supports"] if _is_english(language_code) else ["−", "0", "+"],
        },
    }
    figure.update_layout(**layout)
    return figure


_MOTIF_ARCS: dict[str, list[float]] = {
    "Ambition": [6.0, 8.2, 9.0, 7.0, 3.5],
    "Guilt": [1.0, 5.0, 7.4, 8.8, 9.4],
    "Disorder": [2.0, 5.6, 8.6, 8.0, 6.2],
}
_PERSPECTIVE_TENSION: dict[str, list[float]] = {
    "Macbeth": [2.0, 6.2, 8.6, 9.4, 10.0],
    "Lady Macbeth": [2.8, 7.4, 8.3, 8.9, 9.7],
    "Banquo": [2.0, 3.8, 7.0, 6.0, 5.0],
}


def _narrative_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    motif = _text(values, "motif", "Guilt")
    perspective = _text(values, "perspective", "Macbeth")
    ambiguity = _number(values, "ambiguity", 0.45)
    acts = [1, 2, 3, 4, 5]
    tension = _PERSPECTIVE_TENSION.get(perspective, _PERSPECTIVE_TENSION["Macbeth"])
    motif_values = _MOTIF_ARCS.get(motif, _MOTIF_ARCS["Guilt"])
    counter = [
        max(0.0, min(10.0, motif_value * (1.0 - 0.55 * ambiguity) + (10.0 - tension_value) * 0.35 * ambiguity))
        for motif_value, tension_value in zip(motif_values, tension, strict=True)
    ]
    scenes = [
        "Prophecy and possibility",
        "Decision and rupture",
        "Power and instability",
        "Escalation and resistance",
        "Recognition and consequence",
    ]
    motif_key = {"Ambition": "ambition", "Guilt": "guilt", "Disorder": "disorder"}.get(motif, "guilt")
    localized_motif = lab_tr(motif_key, language_code)
    figure = go.Figure()
    figure.add_trace(
        go.Scatter3d(
            x=acts,
            y=tension,
            z=motif_values,
            mode="lines+markers+text",
            line={"color": _VIOLET, "width": 9},
            marker={"size": [8, 10, 12, 10, 9], "color": [_MINT, _BLUE, _GOLD, _CORAL, _VIOLET]},
            text=[f"Act {act}" for act in acts] if _is_english(language_code) else ["I", "II", "III", "IV", "V"],
            textposition="top center",
            customdata=scenes if _is_english(language_code) else list(get_stages(language_code)[:5]),
            hovertemplate=(
                "Act %{x}<br>narrative tension=%{y:.1f}<br>motif intensity=%{z:.1f}<br>%{customdata}<extra>main reading</extra>"
                if _is_english(language_code)
                else f"# %{{x}}<br>y=%{{y:.1f}}<br>z=%{{z:.1f}}<br>%{{customdata}}<extra>{tr('model', language_code)}</extra>"
            ),
            name=f"{perspective} · {localized_motif}",
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=acts,
            y=[max(0.0, value - ambiguity * 2.0) for value in tension],
            z=counter,
            mode="lines+markers",
            line={"color": _CORAL, "width": 5, "dash": "dash"},
            marker={"size": 5, "color": _CORAL},
            hovertemplate=(
                "Act %{x}<br>counter-reading strength=%{z:.1f}<extra>alternative interpretation</extra>"
                if _is_english(language_code)
                else f"# %{{x}}<br>z=%{{z:.1f}}<extra>{tr('explanation', language_code)}</extra>"
            ),
            name="Counter-reading" if _is_english(language_code) else tr("explanation", language_code),
        )
    )
    layout = _base_layout(
        _figure_title(language_code, course_title, "Interpretive arc · patterns are arguments, not objective measurements")
    )
    layout["scene"] = {
        **(_scene("act", "narrative tension", f"{motif.lower()} motif") if _is_english(language_code) else _scene("x", "y", "z")),
        "xaxis": {**_scene("", "", "")["xaxis"], "tickvals": acts, "range": [0.7, 5.3]},
        "yaxis": {**_scene("", "", "")["yaxis"], "range": [0, 10.5]},
        "zaxis": {**_scene("", "", "")["zaxis"], "range": [0, 10.5]},
    }
    figure.update_layout(**layout)
    return figure


def _claims_state(values: Mapping[str, LabValue]) -> dict[str, float | int | bool]:
    independent = max(0, min(3, int(round(_number(values, "independent_sources", 1)))))
    context = max(0.0, min(100.0, _number(values, "context", 55)))
    original = _text(values, "original_found", "Located") == "Located"
    support = 12 + independent * 16 + context * 0.22 + (18 if original else 0)
    uncertainty = 92 - support
    contradiction = max(5.0, 18.0 - independent * 2.0)
    total = support + uncertainty + contradiction
    return {
        "independent": independent,
        "context": context,
        "original": original,
        "support": 100 * support / total,
        "uncertainty": 100 * uncertainty / total,
        "contradiction": 100 * contradiction / total,
    }


def _claims_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    state = _claims_state(values)
    independent = int(state["independent"])
    repeated = max(1, 4 - independent)
    original_flow = 18 if bool(state["original"]) else 2
    independent_flow = 5 + 8 * independent
    context_flow = 4 + float(state["context"]) * 0.18
    label_keys = (
        "public_claim",
        "repeated_posts",
        "original_evidence",
        "independent_sources",
        "context_check",
        "corroboration",
        "supported",
        "uncertain",
        "contradicted",
    )
    labels = [lab_tr(key, language_code) for key in label_keys]
    figure = go.Figure(
        go.Sankey(
            arrangement="fixed",
            node={
                "label": labels,
                "color": [_BLUE, "#4f6570", _GOLD, _MINT, _VIOLET, "#45cdb3", _MINT, _GOLD, _CORAL],
                "pad": 17,
                "thickness": 18,
                "line": {"color": "rgba(255,255,255,.28)", "width": 1},
                "x": [0.01, 0.23, 0.23, 0.23, 0.47, 0.68, 0.96, 0.96, 0.96],
                "y": [0.42, 0.06, 0.38, 0.78, 0.25, 0.52, 0.1, 0.48, 0.86],
                "hovertemplate": (
                    "%{label}<extra>verification stage</extra>"
                    if _is_english(language_code)
                    else f"%{{label}}<extra>{lab_tr('verification_pipeline', language_code)}</extra>"
                ),
            },
            link={
                "source": [0, 0, 0, 1, 2, 3, 2, 4, 5, 5, 5],
                "target": [1, 2, 3, 5, 4, 5, 5, 5, 6, 7, 8],
                "value": [
                    repeated * 8,
                    original_flow,
                    independent_flow,
                    repeated * 2,
                    context_flow,
                    independent_flow,
                    original_flow,
                    context_flow,
                    state["support"],
                    state["uncertainty"],
                    state["contradiction"],
                ],
                "color": [
                    "rgba(93,114,123,.28)",
                    "rgba(255,214,110,.42)",
                    "rgba(118,242,192,.42)",
                    "rgba(93,114,123,.2)",
                    "rgba(169,152,255,.4)",
                    "rgba(118,242,192,.45)",
                    "rgba(255,214,110,.35)",
                    "rgba(169,152,255,.4)",
                    "rgba(118,242,192,.48)",
                    "rgba(255,214,110,.48)",
                    "rgba(255,137,122,.42)",
                ],
                "hovertemplate": (
                    "%{source.label} → %{target.label}<br>evidence-flow index=%{value:.1f}<extra></extra>"
                    if _is_english(language_code)
                    else f"%{{source.label}} → %{{target.label}}<br>{tr('evidence', language_code)}: %{{value:.1f}}<extra></extra>"
                ),
            },
        )
    )
    layout = _base_layout(
        _figure_title(language_code, course_title, "Verification pipeline · repetition is not independence")
    )
    layout["height"] = 530
    figure.update_layout(**layout)
    return figure


def _ethics_figure(
    values: Mapping[str, LabValue],
    language_code: str = "en",
    course_title: str = "",
) -> go.Figure:
    outcome = _number(values, "outcome_weight", 0.65)
    rights = _number(values, "rights_weight", 0.75)
    uncertainty = _number(values, "uncertainty", 0.35)
    coordinates = _linspace(0.0, 10.0, 27)
    support = [
        [
            outcome * x
            + rights * y
            - uncertainty * (2.0 + 0.09 * (x - y) ** 2)
            - 0.025 * x * y
            for x in coordinates
        ]
        for y in coordinates
    ]
    options = [
        (lab_tr("broad_deployment", language_code), 8.2, 2.4),
        (lab_tr("limited_pilot", language_code), 6.1, 7.0),
        (lab_tr("do_not_deploy", language_code), 2.8, 9.0),
    ]
    option_z = [
        outcome * x
        + rights * y
        - uncertainty * (2.0 + 0.09 * (x - y) ** 2)
        - 0.025 * x * y
        for _, x, y in options
    ]
    figure = go.Figure()
    figure.add_trace(
        go.Surface(
            x=coordinates,
            y=coordinates,
            z=support,
            colorscale=[[0, "#4a3a9a"], [0.45, "#2e7596"], [0.72, "#40d9af"], [1, "#ffe06f"]],
            colorbar={
                "title": "deliberative<br>support" if _is_english(language_code) else tr("result", language_code),
                "thickness": 10,
                "len": 0.62,
            },
            opacity=0.86,
            hovertemplate=(
                "outcome evidence=%{x:.1f}<br>rights compatibility=%{y:.1f}<br>reasoning support=%{z:.1f}<extra></extra>"
                if _is_english(language_code)
                else f"x=%{{x:.1f}}<br>y=%{{y:.1f}}<br>z=%{{z:.1f}}<extra>{tr('model', language_code)}</extra>"
            ),
            name="Reasoning landscape" if _is_english(language_code) else tr("model", language_code),
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=[option[1] for option in options],
            y=[option[2] for option in options],
            z=option_z,
            mode="markers+text",
            text=[option[0] for option in options],
            textposition="top center",
            marker={
                "size": [11, 13, 11],
                "color": [_CORAL, _MINT, _GOLD],
                "line": {"color": "#ffffff", "width": 1},
            },
            customdata=(
                [["high reach / weak consent"], ["bounded test / review"], ["strong constraint / forgone benefit"]]
                if _is_english(language_code)
                else [[tr("node_hint", language_code)]] * 3
            ),
            hovertemplate=(
                "%{text}<br>%{customdata[0]}<br>map support=%{z:.1f}<extra>scenario option</extra>"
                if _is_english(language_code)
                else f"%{{text}}<br>%{{customdata[0]}}<br>z=%{{z:.1f}}<extra>{lab_tr('policy_options', language_code)}</extra>"
            ),
            name=_copy(language_code, "Policy options", "policy_options"),
        )
    )
    layout = _base_layout(
        _figure_title(language_code, course_title, "Ethical reasoning landscape · a comparison aid, never a moral verdict")
    )
    layout["scene"] = {
        **(
            _scene("outcome evidence", "rights & duties compatibility", "deliberative support")
            if _is_english(language_code)
            else _scene("x", "y", "z")
        ),
        "xaxis": {**_scene("", "", "")["xaxis"], "range": [0, 10]},
        "yaxis": {**_scene("", "", "")["yaxis"], "range": [0, 10]},
    }
    figure.update_layout(**layout)
    return figure


_BUILDERS = {
    "surface": _surface_figure,
    "projectile": _projectile_figure,
    "dna": _dna_figure,
    "carbon": _carbon_figure,
    "network": _network_figure,
    "sources": _sources_figure,
    "narrative": _narrative_figure,
    "claims": _claims_figure,
    "ethics": _ethics_figure,
}


def build_lab_figure(
    course: Mapping[str, Any] | str,
    values: Mapping[str, LabValue] | None = None,
    language_code: str = "en",
) -> go.Figure:
    """Build the interactive figure for a course using supplied control values."""

    kind = _kind(course)
    builder = _BUILDERS.get(kind)
    if builder is None:
        raise KeyError(f"Unknown lab kind: {kind}")
    merged = default_lab_values(course)
    if values:
        merged.update(values)
    figure = builder(merged, language_code, _course_title(course))
    figure.update_layout(
        meta={
            "course_id": _course_id(course),
            "lab_kind": kind,
            "language": get_language(language_code)["code"],
        }
    )
    return figure


def lab_metrics(
    course: Mapping[str, Any] | str,
    values: Mapping[str, LabValue] | None = None,
    language_code: str = "en",
) -> tuple[tuple[str, str, str], ...]:
    """Return concise metric cards as (label, value, help) tuples."""

    merged = default_lab_values(course)
    if values:
        merged.update(values)
    kind = _kind(course)
    english = _is_english(language_code)
    if kind == "surface":
        amplitude = _number(merged, "amplitude", 1.8)
        frequency = _number(merged, "frequency", 1.5)
        period = 2 * pi / max(frequency, 0.01)
        return (
            ("Peak magnitude", f"{abs(amplitude):.1f}", "Maximum absolute output."),
            ("Period", f"{period:.2f}", "Distance between repeats along a principal axis."),
            ("Orientation", ("upright" if amplitude >= 0 else "inverted") if english else ("+" if amplitude >= 0 else "−"), "Sign of the amplitude."),
        )
    if kind == "projectile":
        state = _projectile_state(merged)
        clears = state["height"] >= 8
        in_target = 28 <= state["range"] <= 34 and abs(state["drift"]) <= 3
        return (
            ("Time aloft", f"{state['time']:.2f} s", "Idealized launch-to-landing time."),
            ("Max height", f"{state['height']:.1f} m", "Barrier clears" if clears else "Below 8 m barrier"),
            ("Landing", f"{state['range']:.1f} m", "Inside target" if in_target else "Tune toward 28–34 m"),
            ("Side drift", f"{state['drift']:.1f} m", "Simplified constant crosswind model."),
        )
    if kind == "dna":
        dna_state = _dna_state(merged)
        position = int(dna_state["position"])
        changed = dna_state["view"] == "Variant"
        return (
            ("Base pairs", str(len(_BASE_SEQUENCE)), "Displayed sequence length."),
            ("Selected pair", f"{dna_state['first'][position]}–{dna_state['second'][position]}", "Complementary partners."),
            ("Codon position", str(position % 3 + 1), "Position within a three-base reading frame."),
            (
                "Sequence",
                ("changed" if changed else "reference")
                if english
                else lab_tr("variant" if changed else "original", language_code),
                "Structural change does not by itself prove functional effect.",
            ),
        )
    if kind == "carbon":
        emissions = _number(merged, "emissions", 1.0)
        land = _number(merged, "land_uptake", 1.0)
        ocean = _number(merged, "ocean_uptake", 1.0)
        pressure = 10 * emissions - 4 * (land - 1) - 3 * (ocean - 1)
        return (
            ("Fossil transfer", f"{10 * emissions:.1f}", "Conceptual annual flux index."),
            ("Land response", f"{land:.2f}×", "Relative to the diagram baseline."),
            ("Ocean response", f"{ocean:.2f}×", "Relative to the diagram baseline."),
            ("Atmospheric pressure", f"{pressure:.1f}", "Sensitivity index, not a climate forecast."),
        )
    if kind == "network":
        algorithm = _text(merged, "algorithm", "Breadth-first")
        start = _text(merged, "start", "A")
        target = _text(merged, "target", "H")
        order, path = _traverse(start, target, algorithm)
        return (
            ("Visited", str(len(order)), "Nodes examined before stopping."),
            ("Visit order", " → ".join(order), "Deterministic neighbor ordering."),
            ("Route length", str(max(len(path) - 1, 0)), "Edges in the discovered route."),
        )
    if kind == "sources":
        sources = _visible_history_sources(merged)
        years = [int(source["year"]) for source in sources]
        perspectives = len({"opposes" if float(source["stance"]) < 0 else "supports" for source in sources})
        return (
            ("Sources visible", str(len(sources)), "After current filters."),
            (
                "Time span",
                (f"{max(years) - min(years)} years" if years else "none")
                if english
                else (str(max(years) - min(years)) if years else "—"),
                "Chronological breadth.",
            ),
            ("Perspective groups", str(perspectives), "Disagreement can be evidence."),
        )
    if kind == "narrative":
        motif = _text(merged, "motif", "Guilt")
        perspective = _text(merged, "perspective", "Macbeth")
        arc = _MOTIF_ARCS.get(motif, _MOTIF_ARCS["Guilt"])
        peak = arc.index(max(arc)) + 1
        return (
            ("Motif", motif if english else lab_option_label(motif, language_code), "Selected recurring pattern."),
            ("Perspective", perspective, "Current interpretive anchor."),
            ("Peak act", f"Act {peak}" if english else str(peak), "A debatable model, not an objective measurement."),
        )
    if kind == "claims":
        state = _claims_state(merged)
        return (
            ("Independent chains", str(state["independent"]), "Repeated posts do not increase this count."),
            ("Context recovered", f"{state['context']:.0f}%", "Method, timeframe, denominator, and surrounding material."),
            (
                "Evidence status",
                ("traceable" if state["original"] else "origin missing")
                if english
                else lab_tr("located" if state["original"] else "missing", language_code),
                "Availability of original evidence.",
            ),
            ("Support index", f"{state['support']:.0f}/100", "A learning-model signal, not an automated truth score."),
        )
    outcome = _number(merged, "outcome_weight", 0.65)
    rights = _number(merged, "rights_weight", 0.75)
    uncertainty = _number(merged, "uncertainty", 0.35)
    dominant = "rights & duties" if rights > outcome else "outcomes" if outcome > rights else "balanced"
    if not english:
        dominant = "R" if rights > outcome else "O" if outcome > rights else "="
    return (
        ("Foregrounded lens", dominant, "Reflects control weights, not moral correctness."),
        ("Uncertainty", f"{uncertainty:.2f}", "Raises the need for caution and reversibility."),
        ("Verdict", "open" if english else tr("question", language_code), "The map organizes reasons; learners must justify a choice."),
    )


def lab_insight(
    course: Mapping[str, Any] | str,
    values: Mapping[str, LabValue] | None = None,
    language_code: str = "en",
) -> str:
    """Return a dynamic, course-specific reasoning prompt."""

    merged = default_lab_values(course)
    if values:
        merged.update(values)
    kind = _kind(course)
    if not _is_english(language_code):
        title = _course_title(course) or tr("interactive_lab", language_code)
        return tr("node_description", language_code).format(
            stage=get_stages(language_code)[3],
            title=title,
        )
    if kind == "surface":
        amplitude = _number(merged, "amplitude", 1.8)
        frequency = _number(merged, "frequency", 1.5)
        phase = _number(merged, "phase", 0.0)
        return (
            f"At A={amplitude:.1f}, f={frequency:.1f}, and phase={phase:.1f}, the magnitude is set by A, "
            "the spacing by f, and the position by phase. Predict which visible feature remains invariant before moving another control."
        )
    if kind == "projectile":
        state = _projectile_state(merged)
        clearance = state["height"] - 8
        target_relation = "inside" if 28 <= state["range"] <= 34 else "beyond" if state["range"] > 34 else "short of"
        return (
            f"The ideal path peaks {abs(clearance):.1f} m {'above' if clearance >= 0 else 'below'} the barrier and lands "
            f"{target_relation} the target at x={state['range']:.1f} m. Change one component, predict first, then test."
        )
    if kind == "dna":
        dna_state = _dna_state(merged)
        position = int(dna_state["position"])
        if dna_state["view"] == "Original":
            return "The reference view preserves every complementary pair. Switch to Variant, then trace what must happen before a structural change could affect a protein."
        return (
            f"Position {position} changes from {dna_state['original']} to {dna_state['first'][position]} on strand 1 while complementarity is restored. "
            "This visual establishes a sequence difference—not whether transcription, translation, or function changes."
        )
    if kind == "carbon":
        emissions = _number(merged, "emissions", 1.0)
        land = _number(merged, "land_uptake", 1.0)
        ocean = _number(merged, "ocean_uptake", 1.0)
        return (
            f"The conceptual diagram now scales fossil transfer to {emissions:.1f}×, land uptake to {land:.2f}×, and ocean uptake to {ocean:.2f}×. "
            "Compare flow size with reservoir timescale; this sensitivity model is not a climate forecast."
        )
    if kind == "network":
        algorithm = _text(merged, "algorithm", "Breadth-first")
        start = _text(merged, "start", "A")
        target = _text(merged, "target", "H")
        order, path = _traverse(start, target, algorithm)
        return (
            f"{algorithm} visits {' → '.join(order)} and discovers route {' → '.join(path)}. "
            "Switch strategy and explain why the order changes even though the graph does not."
        )
    if kind == "sources":
        sources = _visible_history_sources(merged)
        opposition = any(float(source["stance"]) < 0 for source in sources)
        return (
            f"The current lens retains {len(sources)} sources and {'includes' if opposition else 'removes'} direct disagreement. "
            "Ask what claim becomes easier—and what historical question becomes impossible—under this filter."
        )
    if kind == "narrative":
        motif = _text(merged, "motif", "Guilt")
        perspective = _text(merged, "perspective", "Macbeth")
        ambiguity = _number(merged, "ambiguity", 0.45)
        return (
            f"The map traces {motif.lower()} through {perspective}'s perspective with a {ambiguity:.2f} counter-reading. "
            "Treat every plotted value as an interpretive claim that must be defended with language and scene-level evidence."
        )
    if kind == "claims":
        state = _claims_state(merged)
        return (
            f"The pipeline has {state['independent']} independent evidence chain(s), {state['context']:.0f}% contextual recovery, "
            f"and the original is {'available' if state['original'] else 'missing'}. The support index organizes verification work; it does not decide truth."
        )
    outcome = _number(merged, "outcome_weight", 0.65)
    rights = _number(merged, "rights_weight", 0.75)
    uncertainty = _number(merged, "uncertainty", 0.35)
    return (
        f"The landscape foregrounds outcomes at {outcome:.2f}, rights and duties at {rights:.2f}, and uncertainty at {uncertainty:.2f}. "
        "It compares reasons, not moral worth: defend an option to the stakeholder who bears its greatest cost."
    )


__all__ = [
    "ControlSpec",
    "LabValue",
    "build_lab_figure",
    "default_lab_values",
    "lab_control_specs",
    "lab_insight",
    "lab_metrics",
    "lab_option_label",
]
