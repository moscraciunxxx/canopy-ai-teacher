import type { AllowedClaim, ConfidenceBand } from './canopy-types';

export const PROFILE_KEY = 'canopy.learner.v1';
export const PROFILE_VERSION = 1;

export interface LearningEvent {
  id: string;
  at: string;
  courseId: string;
  stageId: string;
  claim: AllowedClaim;
  confidence: ConfidenceBand;
  mastery: number;
  explanationScore: number;
  misconception: string;
  elapsedSeconds: number;
}

export interface SavedForgeCourse {
  id: string;
  title: string;
  createdAt: string;
  stages: Array<{ id: string; label: string; concept: string; question: string; evidence: string }>;
}

export interface LearnerProfile {
  schemaVersion: 1;
  locale: string;
  courseId: string;
  startedAt: string;
  events: LearningEvent[];
  usabilityRating: number | null;
  preferences: { contrast: boolean; dyslexia: boolean; reduceMotion: boolean };
  forgedCourses: SavedForgeCourse[];
}

export function defaultProfile(): LearnerProfile {
  return {
    schemaVersion: PROFILE_VERSION,
    locale: 'en',
    courseId: 'physics-flight',
    startedAt: new Date().toISOString(),
    events: [],
    usabilityRating: null,
    preferences: { contrast: false, dyslexia: false, reduceMotion: false },
    forgedCourses: [],
  };
}

function validEvent(value: unknown): value is LearningEvent {
  if (!value || typeof value !== 'object') return false;
  const event = value as Partial<LearningEvent>;
  return typeof event.id === 'string' &&
    typeof event.at === 'string' &&
    typeof event.courseId === 'string' &&
    typeof event.stageId === 'string' &&
    typeof event.mastery === 'number' &&
    event.mastery >= 0 && event.mastery <= 1 &&
    typeof event.explanationScore === 'number';
}

export function parseProfile(raw: string): LearnerProfile {
  const value: unknown = JSON.parse(raw);
  if (!value || typeof value !== 'object') throw new Error('Profile must be a JSON object.');
  const candidate = value as Partial<LearnerProfile>;
  if (candidate.schemaVersion !== PROFILE_VERSION) {
    throw new Error(`Unsupported profile version: ${String(candidate.schemaVersion)}`);
  }
  if (!Array.isArray(candidate.events) || !candidate.events.every(validEvent)) {
    throw new Error('Profile learning history is invalid.');
  }
  const base = defaultProfile();
  return {
    ...base,
    locale: typeof candidate.locale === 'string' ? candidate.locale : base.locale,
    courseId: typeof candidate.courseId === 'string' ? candidate.courseId : base.courseId,
    startedAt: typeof candidate.startedAt === 'string' ? candidate.startedAt : base.startedAt,
    events: candidate.events.slice(-500),
    usabilityRating:
      typeof candidate.usabilityRating === 'number' && candidate.usabilityRating >= 1 && candidate.usabilityRating <= 5
        ? candidate.usabilityRating
        : null,
    preferences: {
      contrast: Boolean(candidate.preferences?.contrast),
      dyslexia: Boolean(candidate.preferences?.dyslexia),
      reduceMotion: Boolean(candidate.preferences?.reduceMotion),
    },
    forgedCourses: Array.isArray(candidate.forgedCourses)
      ? candidate.forgedCourses.filter((item): item is SavedForgeCourse =>
          Boolean(item) && typeof item.id === 'string' && typeof item.title === 'string' && Array.isArray(item.stages),
        ).slice(-20)
      : [],
  };
}

export function loadProfile(): LearnerProfile {
  if (typeof window === 'undefined') return defaultProfile();
  const raw = window.localStorage.getItem(PROFILE_KEY);
  if (!raw) return defaultProfile();
  try {
    return parseProfile(raw);
  } catch {
    return defaultProfile();
  }
}

export function saveProfile(profile: LearnerProfile): void {
  window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function masteryByCourse(profile: LearnerProfile): Record<string, number> {
  const grouped: Record<string, number[]> = {};
  profile.events.forEach((event) => {
    (grouped[event.courseId] ??= []).push(event.mastery);
  });
  return Object.fromEntries(
    Object.entries(grouped).map(([courseId, scores]) => {
      const recent = scores.slice(-6);
      return [courseId, recent.reduce((sum, score) => sum + score, 0) / recent.length];
    }),
  );
}

export function profileCsv(profile: LearnerProfile): string {
  const header = 'timestamp,course,stage,claim,confidence,mastery,explanation_score,misconception,elapsed_seconds';
  const rows = profile.events.map((event) => [
    event.at,
    event.courseId,
    event.stageId,
    event.claim,
    event.confidence,
    event.mastery.toFixed(3),
    event.explanationScore,
    JSON.stringify(event.misconception),
    event.elapsedSeconds,
  ].join(','));
  return [header, ...rows].join('\n');
}
