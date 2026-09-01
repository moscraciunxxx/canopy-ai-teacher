# Canopy · Devpost submission copy

## Project name

Canopy

## Tagline

One interactive, inspectable AI teacher across 9 school subjects and 20 languages.

## Inspiration

Most education assistants stop at a chat box. They answer a question, but they
do not give a learner a world to manipulate, a visible reasoning path, or a
teacher-readable explanation of what should happen next. Language access is
often bolted on after the learning experience is designed.

Canopy starts from a different premise: one teacher should follow the learner
across subjects, languages, models, evidence, practice, and transfer.

## What it does

Canopy is an all-for-one AI learning academy with two academies, nine course
studios, 54 connected reasoning nodes, 27 transfer missions, and nine
course-native visual laboratories.

Learners can rotate a projectile trajectory, edit a DNA helix, trace carbon
reservoirs, compare graph-search strategies, filter historical evidence,
inspect a narrative motif, audit a civic claim, and explore ethical trade-offs.
Every control changes evidence the learner can predict and explain.

The same teacher then carries that context through four modes:

- Coach asks for a prediction and diagnoses the learner's reasoning.
- Learn reveals an inspectable explanation one layer at a time.
- Remix moves the skill into a new representation or context.
- Apply transfers the idea and ends with bounded roleplay.

The entire experience—including charts, hover labels, diagrams, controls,
feedback, course models, and source shelves—works in 20 languages. Arabic and
Urdu receive right-to-left layout without reversing equations or scientific
visualizations. Language switching preserves the learner's course state.

## How we built it

Canopy combines a typed curriculum atlas, a six-stage learning graph, and an
inspectable reasoning engine. Course-specific evidence groups and
script-aware language signals update mastery, select the next useful action,
and preserve uncertainty instead of pretending every open response can be
graded automatically. A provider-neutral adapter can add a grounded live model
without changing the offline experience or sending text by default.

The visual layer uses Plotly in the browser for rotatable 3D scenes and Sankey
flows, keeping the Python runtime lightweight. Streamlit orchestrates the
stateful teacher, semantic HTML/CSS/SVG supplies the interaction design, and
Unicode BCP 47 locale packs provide deterministic multilingual presentation.
Docker packaging and a 26-test contract suite make the project reproducible.

The public judge companion adds a private on-device multilingual embedding
model with WebGPU and WASM execution, a deterministic Unicode fallback,
evidence-backed confidence disclosures, an editable six-stage Course Forge,
device-local learner history, spaced review, honest pre/post evidence, and
multimodal accessibility. It needs no Streamlit account, sign-in, or API key.

## Challenges we ran into

The hardest challenge was keeping nine subjects genuinely different while
maintaining one coherent teacher. A physics misconception, a historical source
problem, and an ethical disagreement cannot share the same rubric or visual
metaphor. We solved this with stable course contracts: each studio owns its
reasoning path, evidence vocabulary, model, practice bank, transfer task, and
sources while sharing one orchestration layer.

The second challenge was full-app localization. Translating navigation was not
enough; Plotly legends, hover cards, source labels, diagram nodes, model text,
and framework tooltips also had to stop leaking English. We created an explicit
20-locale visual vocabulary contract and regression-tested every course in
every locale.

## Accomplishments that we're proud of

- Nine interactive visual laboratories, including six 3D scenes and two
  evidence-flow Sankey models.
- Twenty end-to-end learning languages with RTL support.
- A teacher that preserves context across course, language, model, and mode.
- Inspectable feedback that names evidence signals and uncertainty.
- An account-free public judge app with private WebGPU/WASM semantic retrieval
  and a deterministic fallback.
- A teacher-reviewed Course Forge, persistent learner model, spaced review,
  honest evidence dashboard, voice, and accessibility modes.
- A clean quality gate: lint, static typing, 26 Python tests, 9 browser contract
  tests, and 5/5 evaluation cases.

## What we learned

Interactivity is educational only when every control changes a relationship a
learner can predict and defend. We also learned that multilingual access is an
architecture decision: every user-visible layer needs a locale contract, not
just the surrounding page.

Finally, transparent boundaries make an AI teacher more useful. The civic lab
is not a truth machine, the ethics surface is not a moral calculator, and open
multilingual answers are never labelled factually correct from shallow string
matching.

## What's next for Canopy

Next we would run native-speaker reviews and a real learner pilot, calibrate
semantic thresholds by language and subject, add opt-in school-managed sync,
and conduct controlled learning-impact and accessibility studies. The current
app deliberately reports only evidence observed on the learner's device.

## Built with

Python, Streamlit, Plotly, React, TypeScript, Transformers.js, ONNX, WebGPU,
WASM, HTML, CSS, SVG, Unicode BCP 47, localStorage, Docker, pytest, Vitest,
Ruff, and mypy.

## Links

- Account-free live app: https://canopy-ai-teacher.moscraciuncv.chatgpt.site
- Source code: https://github.com/moscraciunxxx/canopy-ai-teacher
- Two-minute demo: https://youtu.be/VyyJqFhyBb4
