import { describe, expect, it } from 'vitest';
import catalogJson from '../data/catalog.json';
import type { Catalog } from '../lib/canopy-types';
import { diagnoseDeterministically, mergeSemantic, unicodeTokens } from '../lib/diagnosis';

const catalog = catalogJson as Catalog;
const physics = catalog.courses.find((course) => course.id === 'physics-flight')!;

describe('diagnosis safety', () => {
  it('tokenizes unspaced and RTL scripts without throwing', () => {
    expect(unicodeTokens('因为证据改变模型').length).toBeGreaterThan(2);
    expect(unicodeTokens('لأن الدليل يغيّر النموذج').length).toBeGreaterThan(2);
    expect(unicodeTokens('pentru că dovezile schimbă modelul')).toContain('dovezile');
  });

  it('does not claim open semantic explanations are factually correct', () => {
    const base = diagnoseDeterministically(
      'Because horizontal velocity and vertical gravity are components, the model predicts a curved trajectory.',
      physics,
      physics.stages[1],
    );
    const semantic = mergeSemantic(base, {
      mode: 'semantic-wasm',
      scores: base.evidence.map((item, index) => ({ id: item.id, score: .92 - index * .1 })),
    });
    expect(semantic.allowedClaim).not.toBe('correct');
    expect(semantic.limitations.join(' ')).toMatch(/do not prove factual correctness/i);
  });

  it('keeps weak answers uncertain with a low confidence band', () => {
    const result = diagnoseDeterministically('maybe', physics, physics.stages[0]);
    expect(result.allowedClaim).toBe('uncertain');
    expect(result.confidence).toBe('low');
  });
});
