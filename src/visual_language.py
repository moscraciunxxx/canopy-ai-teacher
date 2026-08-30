"""Dependency-free visual language primitives for the learning experience.

The module deliberately returns HTML strings so a host such as Streamlit can
embed the visual system with ``unsafe_allow_html=True``.  There is no runtime
JavaScript and no image/font dependency: motion is CSS-only, and the SVG map
remains useful when motion is disabled or scripts are unavailable.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from math import sin
from typing import Any


__all__ = [
    "VIBRANT_CSS_TOKENS",
    "REDUCED_MOTION_CSS",
    "VISUAL_SYSTEM_CSS",
    "visual_system_css",
    "learning_map_markup",
    "render_learning_map",
]


# Keep the palette in one place so a future app skin can consume the same
# values as the SVG renderer.  The contrast pair is intentionally dark/light;
# saturated colors are used as accents rather than long-form body text.
VIBRANT_CSS_TOKENS: Mapping[str, str] = {
    "--vl-ink": "#10233f",
    "--vl-ink-soft": "#35516b",
    "--vl-paper": "#f7fbf4",
    "--vl-foam": "#e7f7ef",
    "--vl-leaf": "#1f9d68",
    "--vl-leaf-dark": "#116345",
    "--vl-lake": "#168aad",
    "--vl-violet": "#7957d5",
    "--vl-sun": "#f7bd3f",
    "--vl-coral": "#ee6c5b",
    "--vl-line": "#b7d8c7",
    "--vl-focus": "#0b6e99",
    "--vl-shadow": "0 16px 40px rgba(16, 35, 63, .14)",
}


def _token_block() -> str:
    """Return scoped CSS variables, keeping host-page styles isolated."""

    values = "; ".join(f"{name}: {value}" for name, value in VIBRANT_CSS_TOKENS.items())
    return f".vl-visual-system {{ {values}; }}"


# The media query is public so hosts can include it alongside their own CSS.
# Every selector is scoped to this module's class to avoid unexpectedly
# changing the surrounding Streamlit page.
REDUCED_MOTION_CSS = """
@media (prefers-reduced-motion: reduce) {
  .vl-visual-system *,
  .vl-visual-system *::before,
  .vl-visual-system *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
  .vl-visual-system .vl-map-node:hover .vl-node-core,
  .vl-visual-system .vl-map-node:focus-visible .vl-node-core {
    transform: none !important;
  }
}
""".strip()


VISUAL_SYSTEM_CSS = f"""
{_token_block()}

.vl-visual-system {{
  color: var(--vl-ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
.vl-learning-map-wrap {{
  background: linear-gradient(135deg, var(--vl-paper), #ffffff 54%, var(--vl-foam));
  border: 1px solid rgba(31, 157, 104, .20);
  border-radius: 24px;
  box-shadow: var(--vl-shadow);
  overflow: hidden;
  padding: .8rem;
}}
.vl-learning-map {{
  display: block;
  height: auto;
  max-width: 100%;
  width: 100%;
}}
.vl-map-title {{
  fill: var(--vl-ink);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -.02em;
}}
.vl-map-subtitle {{
  fill: var(--vl-ink-soft);
  font-size: 13px;
  font-weight: 600;
}}
.vl-map-edge {{
  fill: none;
  stroke: var(--vl-line);
  stroke-dasharray: 5 7;
  stroke-linecap: round;
  stroke-width: 4;
}}
.vl-map-edge.is-complete {{
  stroke: var(--vl-leaf);
  stroke-dasharray: none;
}}
.vl-map-node {{
  cursor: pointer;
  outline: none;
}}
.vl-map-node .vl-node-core {{
  transform-box: fill-box;
  transform-origin: center;
  transition: transform .22s ease, filter .22s ease;
}}
.vl-map-node:hover .vl-node-core,
.vl-map-node:focus-visible .vl-node-core {{
  filter: drop-shadow(0 6px 5px rgba(16, 35, 63, .20));
  transform: scale(1.07);
}}
.vl-map-node:focus-visible .vl-node-ring {{
  stroke: var(--vl-focus);
  stroke-width: 4;
}}
.vl-node-ring {{
  fill: #ffffff;
  stroke: rgba(16, 35, 63, .10);
  stroke-width: 2;
}}
.vl-node-badge {{
  fill: var(--vl-ink);
  font-size: 13px;
  font-weight: 850;
  text-anchor: middle;
}}
.vl-node-label {{
  fill: var(--vl-ink);
  font-size: 14px;
  font-weight: 800;
  text-anchor: middle;
}}
.vl-node-caption {{
  fill: var(--vl-ink-soft);
  font-size: 11px;
  font-weight: 600;
  text-anchor: middle;
}}
.vl-map-node[data-state="complete"] .vl-node-orb {{ fill: var(--vl-leaf); }}
.vl-map-node[data-state="active"] .vl-node-orb {{ fill: var(--vl-coral); }}
.vl-map-node[data-state="upcoming"] .vl-node-orb {{ fill: var(--vl-violet); opacity: .78; }}
.vl-map-node[data-state="locked"] {{ cursor: default; opacity: .62; }}
.vl-map-node[data-state="locked"] .vl-node-orb {{ fill: var(--vl-ink-soft); }}
.vl-map-node[data-state="complete"] .vl-node-check {{ display: inline; }}
.vl-node-check {{ display: none; fill: #ffffff; font-size: 12px; font-weight: 900; text-anchor: middle; }}
.vl-map-legend {{
  align-items: center;
  color: var(--vl-ink-soft);
  display: flex;
  flex-wrap: wrap;
  font-size: 12px;
  font-weight: 700;
  gap: .7rem 1rem;
  padding: 0 .65rem .45rem;
}}
.vl-legend-item {{ align-items: center; display: inline-flex; gap: .35rem; }}
.vl-legend-dot {{ border-radius: 50%; display: inline-block; height: .6rem; width: .6rem; }}
.vl-legend-dot.is-complete {{ background: var(--vl-leaf); }}
.vl-legend-dot.is-active {{ background: var(--vl-coral); }}
.vl-legend-dot.is-upcoming {{ background: var(--vl-violet); }}
{REDUCED_MOTION_CSS}
""".strip()


def visual_system_css() -> str:
    """Return the complete scoped style block for ``st.markdown``."""

    return f"<style>{VISUAL_SYSTEM_CSS}</style>"


def _safe_text(value: Any, *, limit: int = 48) -> str:
    """Normalize and escape short user/content labels for SVG text nodes."""

    text = " ".join(str(value or "").split())
    if len(text) > limit:
        text = text[: max(1, limit - 1)].rstrip() + "…"
    return escape(text)


def _safe_id(value: Any, fallback: str) -> str:
    """Create a stable fragment-safe identifier without trusting input HTML."""

    raw = "".join(character if character.isalnum() else "-" for character in str(value or ""))
    raw = raw.strip("-") or fallback
    return f"vl-node-{raw[:42]}"


def _state_for(node: Mapping[str, Any], active_id: str | None, completed: set[str]) -> str:
    node_id = str(node.get("id", ""))
    if node_id in completed:
        return "complete"
    if active_id is not None and node_id == active_id:
        return "active"
    state = str(node.get("state", "upcoming")).lower()
    return state if state in {"complete", "active", "upcoming", "locked"} else "upcoming"


def _position(index: int, count: int, node: Mapping[str, Any]) -> tuple[float, float]:
    """Use supplied coordinates or place nodes along a gentle vine-like arc."""

    try:
        x = float(node["x"])
        y = float(node["y"])
        return x, y
    except (KeyError, TypeError, ValueError):
        pass

    if count <= 1:
        return 480.0, 190.0
    progress = index / (count - 1)
    x = 92.0 + progress * 776.0
    y = 178.0 + sin(progress * 3.14159 * 2.0) * 34.0
    return x, y


def _curve(start: tuple[float, float], end: tuple[float, float]) -> str:
    """Return a soft cubic connector path between two learning nodes."""

    x1, y1 = start
    x2, y2 = end
    bend = max(34.0, abs(x2 - x1) * 0.34)
    return f"M {x1:.1f},{y1:.1f} C {x1 + bend:.1f},{y1:.1f} {x2 - bend:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"


def learning_map_markup(
    nodes: Iterable[Mapping[str, Any]],
    *,
    active_id: str | None = None,
    completed_ids: Iterable[str] = (),
    title: str = "Your learning trail",
    description: str = "A visual sequence of learning steps. Focus a step to inspect its status.",
) -> str:
    """Build an accessible, interactive SVG learning map.

    Each node accepts ``id``, ``label``, optional ``caption``, ``state``, and
    optional ``x``/``y`` coordinates in a 960 by 300 viewBox.  Nodes without
    coordinates are arranged automatically along a natural arc.  The returned
    markup is safe for content labels and can be embedded directly with
    ``st.markdown(learning_map_markup(...), unsafe_allow_html=True)``.
    """

    items = list(nodes)
    if not items:
        items = [{"id": "start", "label": "Start here", "caption": "Choose a first step", "state": "active"}]

    completed = {str(value) for value in completed_ids}
    positions = [_position(index, len(items), node) for index, node in enumerate(items)]
    map_title_id = "vl-learning-map-title"
    map_description_id = "vl-learning-map-description"

    edge_markup: list[str] = []
    for index in range(len(items) - 1):
        prior_state = _state_for(items[index], active_id, completed)
        next_state = _state_for(items[index + 1], active_id, completed)
        edge_state = " is-complete" if prior_state == "complete" or next_state == "complete" else ""
        edge_markup.append(f'<path class="vl-map-edge{edge_state}" d="{_curve(positions[index], positions[index + 1])}"/>')

    node_markup: list[str] = []
    for index, (node, (x, y)) in enumerate(zip(items, positions)):
        node_id = str(node.get("id", f"step-{index + 1}"))
        dom_id = _safe_id(node_id, f"step-{index + 1}")
        state = _state_for(node, active_id, completed)
        label = _safe_text(node.get("label", node_id), limit=28)
        caption = _safe_text(node.get("caption", ""), limit=34)
        aria = _safe_text(node.get("aria_label", f"{label}, {state}"), limit=90)
        caption_markup = f'<text class="vl-node-caption" x="{x:.1f}" y="{y + 67:.1f}">{caption}</text>' if caption else ""
        node_markup.append(
            f'''<g id="{dom_id}" class="vl-map-node" data-node-id="{_safe_text(node_id, limit=48)}" data-state="{state}" role="button" tabindex="0" aria-label="{aria}">
  <title>{aria}</title>
  <g class="vl-node-core">
    <circle class="vl-node-ring" cx="{x:.1f}" cy="{y:.1f}" r="37"/>
    <circle class="vl-node-orb" cx="{x:.1f}" cy="{y:.1f}" r="28"/>
    <text class="vl-node-badge" x="{x:.1f}" y="{y + 5:.1f}">{index + 1}</text>
    <text class="vl-node-check" x="{x:.1f}" y="{y + 5:.1f}">✓</text>
  </g>
  <text class="vl-node-label" x="{x:.1f}" y="{y + 53:.1f}">{label}</text>
  {caption_markup}
</g>'''
        )

    legend = """
<div class="vl-map-legend" aria-label="Learning map status legend">
  <span class="vl-legend-item"><span class="vl-legend-dot is-complete"></span>Completed</span>
  <span class="vl-legend-item"><span class="vl-legend-dot is-active"></span>Now</span>
  <span class="vl-legend-item"><span class="vl-legend-dot is-upcoming"></span>Next</span>
</div>
""".strip()

    return f'''<section class="vl-visual-system vl-learning-map-wrap" aria-labelledby="{map_title_id}">
  <svg class="vl-learning-map" viewBox="0 0 960 300" role="img" aria-labelledby="{map_title_id} {map_description_id}">
    <title id="{map_title_id}">{_safe_text(title, limit=90)}</title>
    <desc id="{map_description_id}">{_safe_text(description, limit=180)}</desc>
    <path d="M 40,245 C 200,272 285,232 420,247 S 700,272 920,232" fill="none" stroke="rgba(31,157,104,.12)" stroke-width="18" stroke-linecap="round"/>
    <path d="M 40,245 C 200,272 285,232 420,247 S 700,272 920,232" fill="none" stroke="rgba(22,138,173,.20)" stroke-width="2" stroke-linecap="round"/>
    <g class="vl-map-edges" aria-hidden="true">{''.join(edge_markup)}</g>
    <g class="vl-map-nodes">{''.join(node_markup)}</g>
  </svg>
  {legend}
</section>'''


def render_learning_map(
    nodes: Iterable[Mapping[str, Any]],
    *,
    active_id: str | None = None,
    completed_ids: Iterable[str] = (),
    title: str = "Your learning trail",
    description: str = "A visual sequence of learning steps. Focus a step to inspect its status.",
) -> str:
    """Alias with an app-friendly verb for the learning-map markup builder."""

    return learning_map_markup(
        nodes,
        active_id=active_id,
        completed_ids=completed_ids,
        title=title,
        description=description,
    )
