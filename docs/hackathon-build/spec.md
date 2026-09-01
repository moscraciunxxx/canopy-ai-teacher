# Canopy winning-release specification

## Outcome

Add an account-free browser companion without changing the proven Streamlit
academy. The companion must make private on-device AI inspectable, persist a
learner model, support teacher-authored courses, collect honest pilot evidence,
and satisfy accessible multimodal use.

## Uncontested-improvement boundaries

- No Streamlit Cloud account, provider key, or learner-text network request.
- Canonical curriculum is generated from `src/curriculum_atlas.py`; no second
  manually maintained catalogue.
- Semantic similarity may report alignment or a misconception hypothesis, but
  only an exact bounded checker may claim factual correctness.
- A model load failure must fall back to a Unicode-aware local rubric.
- Existing Python runtime and its evaluation contract remain unchanged.
- Impact screens show observed session metrics and explicitly distinguish them
  from controlled-study evidence.

## Acceptance

1. Nine courses and 20 locales are present with stable IDs and source URLs.
2. A learner answer yields visible mode, evidence, confidence reasons,
   misconception hypothesis, mastery update, and next action.
3. Course Forge turns pasted notes into a teacher-editable six-stage draft.
4. Local learner history includes mastery, misconception, review queue, next
   lesson, import/export, and aggregate teacher view.
5. Pre/post explanation scores, recovery time, and usability rating are
   recorded without fabricated claims.
6. Voice input/output, keyboard navigation, screen-reader announcements,
   high-contrast, dyslexia-friendly, and reduced-motion controls are available.
7. Python gates and browser lint/type/test/build gates pass.
