import { describe, expect, it } from 'vitest';
import { defaultProfile, parseProfile, profileCsv } from '../lib/learner-store';

describe('versioned learner profile', () => {
  it('round-trips a valid profile', () => {
    const profile = defaultProfile();
    const parsed = parseProfile(JSON.stringify(profile));
    expect(parsed.schemaVersion).toBe(1);
    expect(parsed.courseId).toBe('physics-flight');
  });

  it('rejects unknown versions and invalid learning history', () => {
    expect(() => parseProfile('{"schemaVersion":2,"events":[]}')).toThrow(/unsupported/i);
    expect(() => parseProfile('{"schemaVersion":1,"events":[{"mastery":9}]}')).toThrow(/invalid/i);
  });

  it('exports an honest empty evidence CSV with headers only', () => {
    expect(profileCsv(defaultProfile()).split('\n')).toHaveLength(1);
    expect(profileCsv(defaultProfile())).toContain('explanation_score');
  });
});
