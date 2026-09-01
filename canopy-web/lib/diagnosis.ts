import type {
  Course,
  Diagnosis,
  EngineMode,
  RetrievedEvidence,
  Stage,
} from './canopy-types';

const CONNECTORS = [
  'because', 'since', 'therefore', 'evidence', 'model', 'change',
  'deoarece', 'pentru că', 'dovadă', 'porque', 'donc', 'car', 'weil',
  'لأن', 'دليل', 'क्योंकि', 'कारण', '因为', '證據', 'ので', 'доказ',
  'çünkü', 'bằng chứng', 'ఎందుకంటే', 'কারণ', 'کیونکہ',
];

export function unicodeTokens(text: string): string[] {
  const normalized = text.normalize('NFKC').toLocaleLowerCase();
  const words = normalized.match(/[\p{L}\p{M}\p{N}]+/gu) ?? [];
  const compact = normalized.replace(/[\s\p{P}\p{S}]+/gu, '');
  const cjk = /[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u.test(compact);
  if (!cjk) return words;
  const grams: string[] = [];
  const chars = Array.from(compact);
  for (let index = 0; index < chars.length - 1; index += 1) {
    grams.push(`${chars[index]}${chars[index + 1]}`);
  }
  return [...words, ...grams];
}

function overlap(query: string[], text: string): number {
  const target = new Set(unicodeTokens(text));
  if (!query.length || !target.size) return 0;
  const hits = query.filter((token) => target.has(token)).length;
  return hits / Math.sqrt(query.length * target.size);
}

function normalizeExact(value: string): string {
  return value.normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
}

export function buildEvidence(course: Course, stage: Stage): RetrievedEvidence[] {
  const records: RetrievedEvidence[] = [
    {
      id: `${stage.id}:concept`,
      title: stage.label,
      text: `${stage.description} ${stage.model}`,
      score: 0,
    },
    ...course.practice.map((item) => ({
      id: `${item.id}:explanation`,
      title: item.title,
      text: item.explanation,
      score: 0,
    })),
    {
      id: `${course.id}:boundary`,
      title: 'Misconception boundary',
      text: course.misconception,
      score: 0,
    },
    ...course.sources.map((source) => ({
      id: `${source.id}:support`,
      title: source.label,
      text: source.supports,
      sourceId: source.id,
      score: 0,
    })),
  ];
  return records;
}

export function diagnoseDeterministically(
  answer: string,
  course: Course,
  stage: Stage,
): Diagnosis {
  const tokens = unicodeTokens(answer);
  const lowered = answer.normalize('NFKC').toLocaleLowerCase();
  const exactPractice = course.practice.find((item) =>
    item.acceptedAnswers.some((expected) => normalizeExact(expected) === normalizeExact(answer)),
  );
  const rubricSignals = [
    ...new Set(
      course.diagnosticGroups
        .flat()
        .filter((signal) => lowered.includes(signal.toLocaleLowerCase())),
    ),
  ];
  const connectors = CONNECTORS.filter((marker) => lowered.includes(marker));
  const scored = buildEvidence(course, stage)
    .map((item) => ({ ...item, score: overlap(tokens, `${item.title} ${item.text}`) }))
    .sort((left, right) => right.score - left.score);
  const top = scored[0]?.score ?? 0;
  const second = scored[1]?.score ?? 0;
  const sufficient = tokens.length >= 7 || Array.from(answer.trim()).length >= 28;
  const misconceptionScore = overlap(tokens, course.misconception);

  let allowedClaim: Diagnosis['allowedClaim'] = 'uncertain';
  let mode: EngineMode = 'deterministic';
  if (exactPractice) {
    allowedClaim = 'correct';
    mode = 'exact-checker';
  } else if (sufficient && (top >= 0.14 || rubricSignals.length >= 2)) {
    allowedClaim = 'aligned';
  } else if (sufficient || rubricSignals.length > 0) {
    allowedClaim = 'partial';
  }

  const confidence: Diagnosis['confidence'] = exactPractice
    ? 'high'
    : allowedClaim === 'aligned' && connectors.length > 0 && top - second > 0.025
      ? 'medium'
      : 'low';
  const explanationScore = Math.min(
    100,
    Math.round(
      (sufficient ? 35 : 12) +
        Math.min(30, rubricSignals.length * 12) +
        Math.min(20, connectors.length * 10) +
        Math.min(15, top * 70),
    ),
  );
  const hypothesis = misconceptionScore > Math.max(0.13, top * 0.92)
    ? `Your explanation may be leaning toward this course misconception: ${course.misconception}`
    : allowedClaim === 'correct'
      ? 'The response matches a bounded answer checker for this practice item.'
      : allowedClaim === 'aligned'
        ? `Your explanation is aligned with ${scored[0]?.title ?? stage.label}.`
        : allowedClaim === 'partial'
          ? 'There is a useful reasoning trace, but the evidence relationship is incomplete.'
          : 'There is not enough evidence yet for a dependable course-level diagnosis.';

  return {
    mode,
    allowedClaim,
    hypothesis,
    confidence,
    confidenceReasons: [
      `${rubricSignals.length} visible course signal${rubricSignals.length === 1 ? '' : 's'}`,
      `${connectors.length} reasoning connector${connectors.length === 1 ? '' : 's'}`,
      exactPractice ? 'bounded answer match' : `top evidence alignment ${top.toFixed(2)}`,
    ],
    limitations: exactPractice
      ? ['Correctness is limited to the selected bounded practice checker.']
      : ['Similarity and vocabulary alignment do not prove factual correctness.'],
    rubricSignals: [...rubricSignals, ...connectors].slice(0, 8),
    evidence: scored.slice(0, 3),
    nextQuestion: stage.hint || course.transferPrompt,
    masterySignal: exactPractice
      ? 0.9
      : Math.min(0.82, Math.max(0.18, explanationScore / 115)),
    explanationScore,
  };
}

export function mergeSemantic(
  base: Diagnosis,
  semantic: { mode: 'semantic-webgpu' | 'semantic-wasm'; scores: Array<{ id: string; score: number }> },
): Diagnosis {
  const ranking = new Map(semantic.scores.map((item) => [item.id, item.score]));
  const evidence = [...base.evidence]
    .map((item) => ({ ...item, score: ranking.get(item.id) ?? item.score }))
    .sort((left, right) => right.score - left.score);
  const top = semantic.scores[0]?.score ?? 0;
  const runnerUp = semantic.scores[1]?.score ?? 0;
  const margin = top - runnerUp;
  const confidence = base.mode === 'exact-checker'
    ? base.confidence
    : base.allowedClaim === 'aligned' && top >= 0.55 && margin >= 0.04
      ? 'medium'
      : 'low';
  return {
    ...base,
    mode: base.mode === 'exact-checker' ? base.mode : semantic.mode,
    confidence,
    evidence,
    semantic: { topScore: top, runnerUpScore: runnerUp, margin },
    confidenceReasons: [
      ...base.confidenceReasons,
      `semantic margin ${margin.toFixed(2)}`,
    ],
    limitations: [
      ...base.limitations,
      'The multilingual embedding model is experimental for this course and language.',
    ],
  };
}
