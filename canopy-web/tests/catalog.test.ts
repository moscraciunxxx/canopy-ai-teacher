import { describe, expect, it } from 'vitest';
import catalogJson from '../data/catalog.json';
import type { Catalog } from '../lib/canopy-types';

const catalog = catalogJson as Catalog;

describe('generated curriculum contract', () => {
  it('preserves nine courses, six stages, three practices, and twenty locales', () => {
    expect(catalog.schemaVersion).toBe('canopy.content.v1');
    expect(catalog.courses).toHaveLength(9);
    expect(Object.keys(catalog.locales)).toHaveLength(20);
    expect(catalog.courses.every((course) => course.stages.length === 6)).toBe(true);
    expect(catalog.courses.every((course) => course.practice.length === 3)).toBe(true);
  });

  it('keeps stable identifiers and secure source URLs in every locale', () => {
    const ids = catalog.courses.map((course) => course.id);
    for (const locale of Object.values(catalog.locales)) {
      expect(Object.keys(locale.courses)).toEqual(ids);
      for (const course of Object.values(locale.courses)) {
        expect(course.sources.every((source) => source.url.startsWith('https://'))).toBe(true);
      }
    }
  });

  it('includes Romanian, excludes Tamil, and retains RTL metadata', () => {
    expect(catalog.locales.ro.meta.native_name).toBe('Română');
    expect(catalog.locales.ta).toBeUndefined();
    expect(catalog.locales.ar.meta.direction).toBe('rtl');
    expect(catalog.locales.ur.meta.direction).toBe('rtl');
  });
});
