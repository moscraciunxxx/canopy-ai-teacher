# Canopy · All-for-One AI Teacher

Canopy is an offline-first, multi-subject learning academy for the SPEED AI
Challenge. It turns one teacher into a coherent learning loop:

attempt → inspect a model → diagnose the reasoning → choose a nudge → practise
a remix → transfer → teach back

The app now contains two academies, nine course studios, 54 linked learning
nodes, 27 transfer missions, and nine course-native visual laboratories.
Progress, notes, recent learning signals, and mastery are preserved separately
for every course during a session.

**Watch the 1:41 demo:** https://youtu.be/VyyJqFhyBb4

## Twenty-language learning mode

Language is an independent learner preference: switching it does not reset the
academy, course, model state, notes, attempts, or mastery trail. The catalogue
uses Unicode/BCP 47 identifiers and includes English plus 19 widely used world
languages:

- English, Mandarin Chinese, Hindi, Spanish, Modern Standard Arabic, French,
  Bengali, Portuguese, Russian, and Indonesian.
- Urdu, German, Japanese, Nigerian Pidgin, Marathi, Vietnamese, Telugu,
  Turkish, Romanian, and Cantonese.

The selected language becomes primary across academy/course navigation,
course titles, the six-stage learning map, visual-lab framing, Coach, Learn,
Remix, Apply/Roleplay, reasoning feedback, and the teacher toolkit. Plot titles,
legends, controls, hover labels, axes, annotations, Sankey nodes, course models,
and source labels follow the same locale contract. Arabic and Urdu use
right-to-left layout while equations, scientific symbols, SVG paths, sliders,
and Plotly scenes remain directionally isolated. An optional English reference
exposes canonical prompts alongside—not in place of—the translated experience.

The offline phrase packs are explicitly marked community-translation beta and
should receive native-speaker and subject-expert review before production use.
For open responses outside English, the deterministic teacher recognises
reasoning structure and language-native connectors without pretending to
verify semantic correctness; exact numeric and symbolic answers can still be
checked directly. Locale design follows [Unicode CLDR language identifiers](https://cldr.unicode.org/index/cldr-spec/picking-the-right-language-code)
and [W3C bidirectional text guidance](https://www.w3.org/TR/i18n-html-tech-bidi/).

## Two academies, nine studios

### STEM Studio

- Mathematics · Functions in Motion
- Physics · Motion in 3D
- Biology · DNA → Protein
- Earth & Climate Science · The Living Carbon Cycle
- Computer Science · Algorithms as Paths

### Human Worlds · Humanities & Society

- History · History as Evidence
- Literature · Narrative & Motif
- Civics & Media Literacy · Civic Claims Lab
- Philosophy & Ethics · Ethical Trade-offs

Every studio changes the full learning contract: the six-stage reasoning path,
diagnostic rubric, visual model, practice bank, transfer challenge, roleplay,
flashcards, teacher brief, and source shelf.

## Interactive visual laboratories

Plotly renders the visuals in the browser, keeping the local runtime light while
supporting rotate, zoom, pan, hover inspection, and responsive resizing.

- A 3D nonlinear function surface with amplitude, frequency, phase, and a
  highlighted cross-section.
- A three-component projectile simulator with a barrier, target zone, landing
  metrics, gravity, and crosswind.
- A manipulable DNA double helix with complementary pairing and a highlighted
  sequence variant.
- A carbon-cycle Sankey model showing reservoirs, transfers, human fossil flux,
  and land/ocean sensitivity.
- A 3D graph-search lab comparing breadth-first and depth-first traversal.
- A historical source constellation mapped across chronology, event proximity,
  and perspective.
- A 3D narrative arc that treats motif intensity as a debatable interpretation
  and keeps a counter-reading visible.
- A civic verification flow that distinguishes repeated posts from independent
  evidence and explicitly avoids pretending to be a truth machine.
- An ethical reasoning landscape that compares outcomes, rights, and uncertainty
  while explicitly refusing to output a moral verdict.

Each lab includes a predict → manipulate → explain inquiry cycle, dynamic
metrics, a live interpretation, and a reset control.

## More than a chat box

- One persistent teacher: Coach, Learn, Remix, and Apply/Roleplay share the
  current course trail and adapt to its disciplinary reasoning.
- A living learning map: six prerequisite-linked stages move from observation
  or sourcing to model testing and transfer.
- Inspectable diagnosis: the deterministic rubric shows which reasoning signals
  it heard instead of hiding judgment behind a generic score.
- Productive visualisation: every control changes a relationship the learner
  can predict and explain; no chart exists only as decoration.
- Transfer and roleplay: every course ends with a changed context and a bounded
  classmate-coaching challenge.
- Teacher toolkit: local notes, recent evidence, a single-session teacher brief,
  flashcards, exit tickets, and authoritative sources stay visible.
- Lightweight delivery: Streamlit, semantic HTML, accessible SVG, CSS motion
  with reduced-motion support, and browser-side Plotly require no front-end
  build and no high-end local GPU.

## Curriculum grounding

The curated studios use inspectable authoritative references and primary texts,
including OpenStax, NASA, the National Human Genome Research Institute, the
Library of Congress, UNESCO, the Stanford Encyclopedia of Philosophy, Project
Gutenberg, and Poetry Foundation. Conceptual models identify their boundaries:
the carbon diagram is not a climate forecast, narrative values are interpretive
claims, the civic index is not an automated truth score, and the ethics surface
is not a moral calculator.

## Run locally

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
~~~

Demo mode is the default and needs no API key or model download. The app opens
at http://localhost:8501.

## Two-minute judge path

1. Choose Spanish, Chinese, Arabic, or any of the 20 language options; show that
   Physics, the course trail, and the browser-rendered lab stay active.
2. Start in STEM → Physics. Move Launch speed twice and watch the 3D landing
   point, range, barrier clearance, and Canopy insight update together.
3. Switch to Biology and rotate the DNA helix; move the variant position and
   compare Original with Variant.
4. Switch to Human Worlds → History. Change Perspective set from Include
   disagreement to Only supportive and observe the source count and perspective
   diversity change.
5. Open Civics and remove the original source. The evidence pipeline shifts
   toward uncertainty while preserving the explicit not-a-truth-score boundary.
6. Open Ethics and change outcome, rights, and uncertainty weights. The surface
   reorganises reasons while the verdict remains open.
7. In Coach, submit a rough explanation. Then use Learn, Remix, and Apply to
   reveal a teaching layer, complete a subject-specific mission, and coach a
   sceptical classmate.
8. Open Teacher brief and Source shelf to show the inspectable learning signal,
   next intervention, exit ticket, and curriculum grounding.
9. Return to Physics and change language again to show that its mastery trail
   was preserved independently from both course and locale.

## Optional live mode

Live mode appears only when these provider-neutral variables are configured:

~~~bash
export MISCONCEPTION_LAB_API_KEY="your-key"
export MISCONCEPTION_LAB_API_BASE_URL="https://your-provider.example/v1"
export MISCONCEPTION_LAB_MODEL="your-model"
streamlit run app.py
~~~

The optional provider contract is retained for the original tutor service.
The nine academy studios remain fully usable through their deterministic,
inspectable subject rubrics without sending learner text to a network.

## Architecture

~~~text
Canopy Streamlit academy
    |
    +-- curriculum_atlas.py
    |     +-- two academies and nine course contracts
    |     +-- 54 reasoning nodes, 27 missions, flashcards, sources
    |
    +-- interactive_labs.py
    |     +-- six rotatable 3D scenes
    |     +-- carbon and civic Sankey flows
    |     +-- controls, metrics, dynamic insight boundaries
    |
    +-- localization.py
    |     +-- 20 BCP 47 locale packs and course labels
    |     +-- RTL metadata, script-aware effort signals, safe fallbacks
    |
    +-- app.py
    |     +-- course/language switching and per-course memory
    |     +-- Coach, Learn, Remix, Apply, toolkit, SVG map
    |
    +-- TutorService
          +-- local markdown retrieval and rubric guardrails
          +-- demo provider or optional compatible HTTP provider
~~~

## Tests and quality gate

Run from the repository root:

~~~bash
python -m pip install -r requirements-dev.txt
python -m compileall -q src app.py evals tests
python -m pytest -q
python evals/run_eval.py
~~~

The suite covers tutor contracts, retrieval, learning-experience contracts,
all nine course schemas, every visual-figure build, visual-form selection, and
control sensitivity, all 20 locale contracts, RTL metadata, script-aware
reasoning signals, language-neutral scientific notation, and preservation of
source URLs through localization. The current clean gate reports 26 passing
tests and 5/5 deterministic evaluation cases.

## Key files

- app.py — the complete Streamlit academy and interaction flow.
- src/curriculum_atlas.py — typed multi-subject curriculum catalogue.
- src/interactive_labs.py — deterministic Plotly figures, controls, metrics,
  and dynamic insights.
- src/localization.py — 20-language catalogue, UI phrase packs, course labels,
  RTL metadata, localized presentation copies, and safe reasoning signals.
- src/learning_studio.py — original graph and practice orchestration contracts.
- src/tutor.py, retrieval.py, rubric.py, provider.py, guardrails.py — grounded
  tutor service and optional provider boundary.
- content/ — local algebra lesson and rubric retained as a tutor-service sample.
- tests/ — contract, retrieval, experience, curriculum, and visual-lab tests.
- evals/ — deterministic golden cases and runner.

## Limitations and originality

Canopy is a curated competition demonstration, not a complete school
curriculum, psychometric assessment, climate forecast, historical database,
truth engine, or moral authority. Session progress is held in memory and there
is no multi-student account system. The curriculum contracts, visual models,
interaction design, reasoning rubrics, learning graph, orchestration,
guardrails, tests, and packaging are authored in this workspace. Claims about
learning impact are product hypotheses demonstrated through interaction, not
results from a controlled learning study.
