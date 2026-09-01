export type ConfidenceBand = 'high' | 'medium' | 'low';
export type AllowedClaim = 'correct' | 'aligned' | 'partial' | 'uncertain';
export type EngineMode =
  | 'semantic-webgpu'
  | 'semantic-wasm'
  | 'deterministic'
  | 'exact-checker';

export interface Stage {
  id: string;
  order: number;
  shortLabel: string;
  label: string;
  icon: string;
  color: string;
  model: string;
  question: string;
  description: string;
  hint: string;
  explainSteps: Array<{ title: string; model: string; body: string }>;
}

export interface Practice {
  id: string;
  title: string;
  model: string;
  question: string;
  answerType: string;
  acceptedAnswers: string[];
  requiredTerms: string[];
  skill: string;
  transfer: string;
  hints: string[];
  difficulty: number;
  explanation: string;
}

export interface Source {
  id: string;
  label: string;
  url: string;
  supports: string;
}

export interface Course {
  id: string;
  academyId: string;
  subject: string;
  title: string;
  subtitle: string;
  icon: string;
  accent: string;
  ageBand: string;
  labKind: string;
  bigQuestion: string;
  misconception: string;
  transferPrompt: string;
  roleplayPrompt: string;
  diagnosticGroups: string[][];
  stages: Stage[];
  practice: Practice[];
  flashcards: Array<{ front: string; back: string }>;
  sources: Source[];
}

export interface Locale {
  meta: {
    code: string;
    bcp47: string;
    english_name: string;
    native_name: string;
    direction: 'ltr' | 'rtl';
    script: string;
  };
  messages: Record<string, string>;
  academyLabels: Record<string, string>;
  academyDescriptions: Record<string, string>;
  courses: Record<string, Course>;
}

export interface Catalog {
  schemaVersion: string;
  defaultLocale: string;
  academies: Array<{
    id: string;
    label: string;
    shortLabel: string;
    icon: string;
    description: string;
  }>;
  courses: Course[];
  locales: Record<string, Locale>;
}

export interface RetrievedEvidence {
  id: string;
  title: string;
  text: string;
  score: number;
  sourceId?: string;
}

export interface Diagnosis {
  mode: EngineMode;
  allowedClaim: AllowedClaim;
  hypothesis: string;
  confidence: ConfidenceBand;
  confidenceReasons: string[];
  limitations: string[];
  rubricSignals: string[];
  evidence: RetrievedEvidence[];
  nextQuestion: string;
  masterySignal: number;
  explanationScore: number;
  semantic?: { topScore: number; runnerUpScore: number; margin: number };
}

export interface ForgeStage {
  id: string;
  label: string;
  concept: string;
  question: string;
  evidence: string;
}
